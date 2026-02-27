#!/usr/bin/env python3
"""
Multi-LLM council for star-chamber skill.

Features:
- Fan out prompts to multiple LLM providers in parallel
- Fan in responses for aggregation
- Target specific files or recent changes
- Select providers or use default config

Note: Debate mode (multi-round deliberation) is orchestrated by Claude Code
in SKILL.md, not by this script. This script handles single-round parallel calls.
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, TypedDict


# API key patterns to redact from error messages.
API_KEY_PATTERNS = [
    r"sk-(?:proj-)?[a-zA-Z0-9]{20,}",  # OpenAI keys (classic and project-scoped).
    r"sk-ant-[a-zA-Z0-9-]{20,}",  # Anthropic keys.
    r"ANY\.v1\.[a-zA-Z0-9]+",  # any-llm.ai platform keys.
    r"AIza[a-zA-Z0-9_-]{35}",  # Google API keys.
    r"gsk_[a-zA-Z0-9]{20,}",  # Groq keys.
]


# Fallback when provider config omits max_tokens.
DEFAULT_MAX_TOKENS = 16384


class ProviderConfig(TypedDict, total=False):
    """Configuration for a single LLM provider."""

    provider: str
    model: str
    api_key: str
    max_tokens: int
    api_base: str


class ReviewResult(TypedDict, total=False):
    """Result from a single provider review."""

    provider: str
    model: str
    success: bool
    content: str
    parsed_json: dict[str, Any] | list[Any] | None
    error: str


def extract_json(content: str) -> dict[str, Any] | list[Any] | None:
    """Extract JSON from LLM response, handling markdown code blocks.

    LLMs often wrap JSON responses in markdown code blocks like:
        ```json
        {"key": "value"}
        ```

    This function tries to parse JSON directly first, then falls back to
    extracting from code blocks.
    """
    if not content:
        return None

    # Try direct parse first.
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` or ``` ... ``` blocks.
    # Patterns use \s* to handle optional whitespace/newlines.
    patterns = [
        r"```json\s*(.*?)\s*```",  # ```json ... ```
        r"```\s*([\{\[].*?[\}\]])\s*```",  # ``` {/[ ... ]/} ```
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

    print("[star-chamber] Could not extract JSON from response", file=sys.stderr)
    return None


def sanitize_error(message: str) -> str:
    """Redact API keys and sensitive patterns from error messages."""
    result = message
    for pattern in API_KEY_PATTERNS:
        result = re.sub(pattern, "[REDACTED]", result)
    return result


def load_sdk_map() -> dict[str, str | None]:
    """Load provider-to-SDK mapping."""
    sdk_map_path = Path(__file__).resolve().parent / "sdk_map.json"
    if not sdk_map_path.exists():
        print(
            json.dumps({
                "error": f"SDK map not found: {sdk_map_path}",
                "hint": "Ensure star-chamber skill is set up correctly.",
            }),
        )
        sys.exit(1)

    try:
        with open(sdk_map_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(
            json.dumps({
                "error": f"Invalid JSON in SDK map: {sdk_map_path}",
                "details": str(e),
                "hint": "Check the file for syntax errors.",
            }),
        )
        sys.exit(1)

    # Validate structure: should be dict with string keys and string/None values.
    if not isinstance(data, dict):
        print(
            json.dumps({
                "error": "SDK map must be a JSON object",
                "got": type(data).__name__,
            }),
        )
        sys.exit(1)

    data.pop("_comment", None)
    return data


def get_required_sdks(provider_names: list[str]) -> list[str]:
    """Return list of SDK packages needed for the given providers."""
    sdk_map = load_sdk_map()
    sdks = []
    for name in provider_names:
        sdk = sdk_map.get(name.lower())
        if sdk:
            sdks.append(sdk)
        elif name.lower() != "openai":  # openai is the base case, no SDK needed
            print(
                f"[star-chamber] Provider {name} not in sdk_map, assuming OpenAI-compatible",
                file=sys.stderr,
            )
    return sorted(set(sdks))


async def _get_review_internal(
    provider: str, model: str, prompt: str, api_key: str,
    max_tokens: int = DEFAULT_MAX_TOKENS, api_base: str = "",
) -> ReviewResult:
    """Send prompt to a single provider and return structured response.

    If api_key is empty and ANY_LLM_KEY is set, the SDK auto-detects platform mode.
    If api_base is set, it overrides the provider's default endpoint URL.
    """
    try:
        # Import here to allow uv run --with to install the dependency.
        from any_llm import acompletion

        kwargs: dict[str, Any] = {
            "model": model,
            "provider": provider,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }
        # OpenAI gpt-5.x and o-series models require max_completion_tokens
        # instead of max_tokens. any-llm-sdk doesn't map this automatically
        # (see https://github.com/mozilla-ai/any-llm/issues/862).
        if provider.lower() == "openai":
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = max_tokens
        if api_key:
            kwargs["api_key"] = api_key
        # If no api_key, SDK checks ANY_LLM_KEY and auto-routes through platform.
        if api_base:
            kwargs["api_base"] = api_base

        response = await acompletion(**kwargs)
        if not response.choices:
            return ReviewResult(
                provider=provider,
                model=model,
                success=False,
                error="No response choices returned from provider",
            )
        content = response.choices[0].message.content
        return ReviewResult(
            provider=provider,
            model=model,
            success=True,
            content=content,
            parsed_json=extract_json(content),
        )
    except ImportError:
        sdk_map = load_sdk_map()
        sdk = sdk_map.get(provider.lower())
        if sdk:
            hint = f"Install with: pip install {sdk} (or add '--with {sdk}' to uv run)"
        else:
            hint = "This provider may use the OpenAI-compatible API (no extra SDK needed)"
        return ReviewResult(
            provider=provider,
            model=model,
            success=False,
            error=f"Missing SDK for {provider}. {hint}",
        )
    except Exception as e:
        error_msg = str(e).lower()
        # Map providers to their env var names for helpful errors.
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "google": "GEMINI_API_KEY",
            "cohere": "COHERE_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "groq": "GROQ_API_KEY",
        }
        env_var = env_var_map.get(provider.lower(), f"{provider.upper()}_API_KEY")

        # Detect common API key issues.
        if "api_key" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
            return ReviewResult(
                provider=provider,
                model=model,
                success=False,
                error=f"Authentication failed for {provider}. Check {env_var} is set and valid.",
            )
        if "api key" in error_msg or "apikey" in error_msg:
            return ReviewResult(
                provider=provider,
                model=model,
                success=False,
                error=f"Missing API key for {provider}. Set {env_var} in your environment.",
            )
        return ReviewResult(
            provider=provider,
            model=model,
            success=False,
            error=sanitize_error(str(e)),
        )


async def get_review(
    provider: str, model: str, prompt: str, api_key: str,
    timeout: float | None = None, max_tokens: int = DEFAULT_MAX_TOKENS,
    api_base: str = "",
) -> ReviewResult:
    """Get review with optional timeout.

    Wraps _get_review_internal with asyncio.wait_for for timeout handling.
    """
    if timeout is None:
        return await _get_review_internal(
            provider, model, prompt, api_key, max_tokens=max_tokens, api_base=api_base,
        )

    try:
        return await asyncio.wait_for(
            _get_review_internal(
                provider, model, prompt, api_key, max_tokens=max_tokens, api_base=api_base,
            ),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        return ReviewResult(
            provider=provider,
            model=model,
            success=False,
            error=f"Request timed out after {timeout}s",
        )


def resolve_api_keys(
    providers: list[dict[str, Any]], use_platform: bool
) -> list[dict[str, Any]]:
    """Resolve API keys - from env vars or platform."""
    if use_platform:
        # Platform mode: ignore any api_key in config, platform provides keys.
        ignored = [p["provider"] for p in providers if p.get("api_key")]
        if ignored:
            print(
                f"[star-chamber] Using platform mode, ignoring api_key for: {', '.join(ignored)}",
                file=sys.stderr,
            )
        for p in providers:
            p["api_key"] = ""
        return providers

    # Direct mode: resolve from environment variables.
    for p in providers:
        api_key = p.get("api_key", "")
        if api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            p["api_key"] = os.environ.get(env_var, "")
    return providers


def get_changed_files() -> list[str]:
    """Fallback if no --file args provided: get recent changes."""
    try:
        output = subprocess.check_output(
            ["git", "diff", "HEAD~1", "--name-only", "--diff-filter=ACMRT"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return [f.strip() for f in output.splitlines() if f.strip()]
    except Exception:
        # Try staged files as fallback.
        try:
            output = subprocess.check_output(
                ["git", "diff", "--cached", "--name-only"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            return [f.strip() for f in output.splitlines() if f.strip()]
        except Exception:
            return []


async def run_council(
    prompt: str,
    providers: list[ProviderConfig],
    timeout: float | None = None,
) -> dict[str, Any]:
    """Run multi-LLM council review.

    Fans out the prompt to all providers in parallel and returns their responses.
    Debate mode (multi-round deliberation) is handled by Claude Code in SKILL.md.
    """
    tasks = [
        get_review(
            p["provider"], p["model"], prompt, p.get("api_key", ""),
            timeout=timeout, max_tokens=p.get("max_tokens", DEFAULT_MAX_TOKENS),
            api_base=p.get("api_base", ""),
        )
        for p in providers
    ]
    results = list(await asyncio.gather(*tasks))
    return {"reviews": results}


def main() -> None:
    """Entry point for the LLM council script."""
    parser = argparse.ArgumentParser(description="Star-Chamber Multi-LLM Review")
    parser.add_argument(
        "--file", "-f", action="append", help="Target file(s) to review"
    )
    parser.add_argument(
        "--provider", "-p", action="append", help="LLM providers to use"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        help="Timeout in seconds for each provider request (overrides config)",
    )
    parser.add_argument(
        "--list-sdks",
        action="store_true",
        help="Output required SDK packages for configured/specified providers and exit",
    )
    args = parser.parse_args()

    # Load provider config.
    config_path = os.environ.get(
        "STAR_CHAMBER_CONFIG",
        os.path.expanduser("~/.config/star-chamber/providers.json"),
    )

    if not os.path.exists(config_path):
        print(
            json.dumps(
                {
                    "error": f"Config file not found: {config_path}",
                    "hint": "Run /star-chamber to set up configuration, or create manually.",
                },
                indent=2,
            )
        )
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    platform = config.get("platform")

    # Validate platform mode prerequisites.
    if platform == "any-llm":
        any_llm_key = os.environ.get("ANY_LLM_KEY", "")
        if not any_llm_key:
            print(
                json.dumps(
                    {
                        "error": "Platform mode enabled but ANY_LLM_KEY not set",
                        "setup": {
                            "step1": "Create project at https://any-llm.ai",
                            "step2": "Add your provider API keys to the project",
                            "step3": "Copy your project key and set: export ANY_LLM_KEY='...'",
                        },
                        "docs": "https://any-llm.ai/docs",
                    },
                    indent=2,
                )
            )
            sys.exit(1)

    providers = config.get("providers", [])
    providers = resolve_api_keys(providers, platform == "any-llm")

    # Filter to requested providers if specified.
    if args.provider:
        requested = [x.lower() for x in args.provider]
        providers = [p for p in providers if p["provider"].lower() in requested]
        if not providers:
            print(
                json.dumps(
                    {
                        "error": "No matching providers found.",
                        "requested": args.provider,
                        "available": [p["provider"] for p in config.get("providers", [])],
                    },
                    indent=2,
                )
            )
            sys.exit(1)

    # Handle --list-sdks: output diagnostic info and exit.
    if args.list_sdks:
        provider_names = [p["provider"] for p in providers]
        sdks = get_required_sdks(provider_names)

        # In platform mode, add platform SDK.
        if platform == "any-llm":
            sdk_map = load_sdk_map()
            platform_sdk = sdk_map.get("platform")
            if platform_sdk:
                sdks = sorted(set(sdks + [platform_sdk]))

        # Check which providers have API keys set.
        ready = []
        missing_key = []
        platform_provided = []
        for p in providers:
            if platform == "any-llm":
                platform_provided.append(p["provider"])
            elif p.get("api_key"):
                ready.append(p["provider"])
            else:
                missing_key.append(p["provider"])

        output = {
            "providers_configured": provider_names,
            "providers_ready": ready,
            "providers_missing_key": missing_key,
            "required_sdks": sdks,
            "uv_with_flags": " ".join(f"--with {sdk}" for sdk in sdks),
            "platform": platform,
        }
        if platform == "any-llm":
            output["providers_platform_provided"] = platform_provided
            output["platform_key_set"] = bool(os.environ.get("ANY_LLM_KEY"))

        print(json.dumps(output, indent=2))
        sys.exit(0)

    # Read prompt from stdin.
    prompt = sys.stdin.read()

    # Determine files to review.
    files_to_review = args.file if args.file else get_changed_files()

    # Build combined prompt with file list.
    combined_prompt = prompt
    if files_to_review:
        combined_prompt += "\n\nFiles to review:\n" + "\n".join(
            f"- {f}" for f in files_to_review
        )

    # Determine timeout: CLI flag > config > None.
    timeout: float | None = args.timeout
    if timeout is None:
        raw_timeout = config.get("timeout_seconds")
        if raw_timeout is not None:
            try:
                timeout = float(raw_timeout)
                if timeout <= 0:
                    raise ValueError("must be positive")
            except (TypeError, ValueError):
                print(
                    json.dumps({
                        "error": "Invalid timeout_seconds in config",
                        "value": raw_timeout,
                        "hint": "timeout_seconds must be a positive number",
                    }),
                )
                sys.exit(1)

    # Run the council (single parallel round).
    result = asyncio.run(
        run_council(
            combined_prompt,
            providers,
            timeout=timeout,
        )
    )

    # Separate successful and failed reviews.
    all_reviews = result.get("reviews", [])
    successful = [r for r in all_reviews if r.get("success")]
    failed = [r for r in all_reviews if not r.get("success")]

    # Build final output.
    output: dict[str, Any] = {
        "reviews": successful,
        "files_reviewed": files_to_review,
        "providers_used": [p["provider"] for p in providers],
    }

    if failed:
        output["failed_reviews"] = failed

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
