#!/usr/bin/env python3
"""
Multi-LLM council for star-chamber skill.

Features:
- Target specific files or recent changes
- Select providers or use default config
- Manual-only flags:
    --deliberate N: sequential chaining of LLM responses
    --interject N: parallel advisory interjections
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def load_sdk_map() -> dict[str, str | None]:
    """Load provider-to-SDK mapping from reference file."""
    claude_config = os.environ.get("CLAUDE_CONFIG_PATH", "")
    sdk_map_path = Path(claude_config) / "reference/star-chamber/sdk_map.json"
    if sdk_map_path.exists():
        with open(sdk_map_path) as f:
            data = json.load(f)
            # Remove comment key.
            data.pop("_comment", None)
            return data
    # Fallback: common providers that need SDKs. If not listed, none needed.
    return {
        "anthropic": "anthropic",
        "gemini": "google-genai",
        "vertexai": "google-genai",
        "groq": "groq",
        "mistral": "mistralai",
        "cohere": "cohere",
        "bedrock": "boto3",
        "sagemaker": "boto3",
        "together": "together",
        "ollama": "ollama",
    }


def get_required_sdks(provider_names: list[str]) -> list[str]:
    """Return list of SDK packages needed for the given providers."""
    sdk_map = load_sdk_map()
    sdks = []
    for name in provider_names:
        sdk = sdk_map.get(name.lower())
        if sdk:
            sdks.append(sdk)
    return sorted(set(sdks))


async def get_review(
    provider: str, model: str, prompt: str, api_key: str
) -> dict[str, Any]:
    """Send prompt to a single provider and return structured response."""
    try:
        # Import here to allow uvx to install the dependency.
        from any_llm import acompletion

        response = await acompletion(
            model=model,
            provider=provider,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key,
            temperature=0.3,
        )
        return {
            "provider": provider,
            "model": model,
            "success": True,
            "content": response.choices[0].message.content,
        }
    except ImportError:
        sdk_map = load_sdk_map()
        sdk = sdk_map.get(provider.lower(), provider)
        hint = f"Add '--with {sdk}' to uvx command" if sdk else "Check provider name"
        return {
            "provider": provider,
            "model": model,
            "success": False,
            "error": f"Missing SDK for {provider}. {hint}",
        }
    except Exception as e:
        error_msg = str(e).lower()
        # Detect common API key issues.
        if "api_key" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
            return {
                "provider": provider,
                "model": model,
                "success": False,
                "error": f"Authentication failed for {provider}. Check API key is set and valid.",
            }
        if "api key" in error_msg or "apikey" in error_msg:
            return {
                "provider": provider,
                "model": model,
                "success": False,
                "error": f"Missing or invalid API key for {provider}.",
            }
        return {"provider": provider, "model": model, "success": False, "error": str(e)}


def resolve_api_keys(providers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve environment variable placeholders in API keys."""
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
    providers: list[dict[str, Any]],
    deliberate: int = 0,
    interject: int = 0,
) -> dict[str, Any]:
    """Run multi-LLM council review."""
    results: list[dict[str, Any]] = []

    if deliberate > 0:
        # Sequential chaining - feed each response to next LLM.
        current_prompt = prompt
        for _round_idx in range(deliberate):
            for p in providers:
                res = await get_review(
                    p["provider"], p["model"], current_prompt, p["api_key"]
                )
                results.append(res)
                if res.get("success"):
                    # Build on previous response for debate mode.
                    current_prompt = (
                        f"Previous reviewer said:\n{res['content']}\n\n"
                        f"Original review request:\n{prompt}\n\n"
                        f"Please provide your perspective, agreeing or disagreeing with specific points."
                    )
    elif interject > 0:
        # Parallel interjections with limited count.
        tasks = []
        for p in providers:
            for _ in range(interject):
                tasks.append(
                    get_review(p["provider"], p["model"], prompt, p["api_key"])
                )
        results = list(await asyncio.gather(*tasks))
    else:
        # Default: parallel independent.
        tasks = [
            get_review(p["provider"], p["model"], prompt, p["api_key"])
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
        "--deliberate", type=int, default=0, help="Sequential chaining rounds"
    )
    parser.add_argument(
        "--interject", type=int, default=0, help="Parallel interjections per provider"
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
        claude_config = os.environ.get("CLAUDE_CONFIG_PATH", "")
        reference_path = (
            f"{claude_config}/reference/star-chamber/providers.json"
            if claude_config
            else "~/.config/star-chamber/providers.json"
        )
        print(
            json.dumps(
                {
                    "error": f"Config file not found: {config_path}",
                    "setup": {
                        "step1": "mkdir -p ~/.config/star-chamber",
                        "step2": f"cp {reference_path} ~/.config/star-chamber/providers.json",
                        "step3": "Edit the file to configure your API keys",
                    },
                    "required_env_vars": [
                        "OPENAI_API_KEY",
                        "ANTHROPIC_API_KEY",
                        "GEMINI_API_KEY",
                    ],
                    "hint": "Remove providers from the config if you don't have their API keys.",
                },
                indent=2,
            )
        )
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    providers = config.get("providers", [])
    providers = resolve_api_keys(providers)

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

        # Check which providers have API keys set.
        ready = []
        missing_key = []
        for p in providers:
            if p.get("api_key"):
                ready.append(p["provider"])
            else:
                missing_key.append(p["provider"])

        print(
            json.dumps(
                {
                    "providers_configured": provider_names,
                    "providers_ready": ready,
                    "providers_missing_key": missing_key,
                    "required_sdks": sdks,
                    "uvx_with_flags": " ".join(f"--with {sdk}" for sdk in sdks),
                },
                indent=2,
            )
        )
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

    # Run the council.
    result = asyncio.run(
        run_council(combined_prompt, providers, args.deliberate, args.interject)
    )

    # Separate successful and failed reviews.
    all_reviews = result.get("reviews", [])
    successful = [r for r in all_reviews if r.get("success")]
    failed = [r for r in all_reviews if not r.get("success")]

    # Build final output.
    output = {
        "reviews": successful,
        "files_reviewed": files_to_review,
        "providers_used": [p["provider"] for p in providers],
        "mode": (
            "deliberate"
            if args.deliberate > 0
            else "interject" if args.interject > 0 else "parallel"
        ),
    }

    if failed:
        output["failed_reviews"] = failed

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
