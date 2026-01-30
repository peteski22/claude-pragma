#!/usr/bin/env python3
"""
Multi-LLM council for star-chamber skill.

Features:
- Target specific files or recent changes
- Select providers or use default config
- Debate mode: multiple rounds where each provider sees others' responses
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
    with open(sdk_map_path) as f:
        data: dict[str, str | None] = json.load(f)
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
    return sorted(set(sdks))


async def get_review(
    provider: str, model: str, prompt: str, api_key: str
) -> dict[str, Any]:
    """Send prompt to a single provider and return structured response.

    If api_key is empty and ANY_LLM_KEY is set, the SDK auto-detects platform mode.
    """
    try:
        # Import here to allow uvx to install the dependency.
        from any_llm import acompletion

        kwargs = {
            "model": model,
            "provider": provider,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }
        if api_key:
            kwargs["api_key"] = api_key
        # If no api_key, SDK checks ANY_LLM_KEY and auto-routes through platform.

        response = await acompletion(**kwargs)
        return {
            "provider": provider,
            "model": model,
            "success": True,
            "content": response.choices[0].message.content,
        }
    except ImportError:
        sdk_map = load_sdk_map()
        sdk = sdk_map.get(provider.lower())
        if sdk:
            hint = f"Install with: pip install {sdk} (or add '--with {sdk}' to uvx)"
        else:
            hint = "This provider may use the OpenAI-compatible API (no extra SDK needed)"
        return {
            "provider": provider,
            "model": model,
            "success": False,
            "error": f"Missing SDK for {provider}. {hint}",
        }
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
            return {
                "provider": provider,
                "model": model,
                "success": False,
                "error": f"Authentication failed for {provider}. Check {env_var} is set and valid.",
            }
        if "api key" in error_msg or "apikey" in error_msg:
            return {
                "provider": provider,
                "model": model,
                "success": False,
                "error": f"Missing API key for {provider}. Set {env_var} in your environment.",
            }
        return {"provider": provider, "model": model, "success": False, "error": str(e)}


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
    providers: list[dict[str, Any]],
    debate: bool = False,
    rounds: int = 2,
) -> dict[str, Any]:
    """Run multi-LLM council review.

    Default mode: All providers review in parallel independently.

    Debate mode: Multiple rounds where each provider sees others' responses.
      Round 1: All providers get original prompt (parallel)
      Round 2+: Each provider sees what the others said and responds (parallel)
    """
    all_results: list[dict[str, Any]] = []

    if debate:
        # Debate mode: parallel rounds with cross-pollination.
        # Track responses by provider for each round.
        previous_responses: dict[str, str] = {}

        for round_num in range(1, rounds + 1):
            round_results: list[dict[str, Any]] = []

            # Build tasks for this round.
            tasks = []
            for p in providers:
                provider_name = p["provider"]

                if round_num == 1:
                    # First round: everyone gets the original prompt.
                    round_prompt = prompt
                else:
                    # Subsequent rounds: include other providers' responses.
                    other_responses = []
                    for other_provider, response in previous_responses.items():
                        if other_provider != provider_name:
                            other_responses.append(
                                f"**{other_provider}** said:\n{response}"
                            )

                    round_prompt = (
                        f"{prompt}\n\n"
                        f"---\n"
                        f"## Other council members' responses (round {round_num - 1}):\n\n"
                        f"{chr(10).join(other_responses)}\n\n"
                        f"---\n"
                        f"Please provide your perspective, responding to the other members' points. "
                        f"Note areas of agreement and disagreement."
                    )

                tasks.append(
                    (provider_name, get_review(
                        p["provider"], p["model"], round_prompt, p["api_key"]
                    ))
                )

            # Execute round in parallel.
            results = await asyncio.gather(*[t[1] for t in tasks])

            # Process results and update previous_responses for next round.
            previous_responses = {}
            for i, res in enumerate(results):
                provider_name = tasks[i][0]
                res["round"] = round_num
                round_results.append(res)
                if res.get("success"):
                    previous_responses[provider_name] = res["content"]

            all_results.extend(round_results)

        return {"reviews": all_results, "rounds": rounds}
    else:
        # Default: parallel independent reviews.
        tasks = [
            get_review(p["provider"], p["model"], prompt, p["api_key"])
            for p in providers
        ]
        results = list(await asyncio.gather(*tasks))
        return {"reviews": results, "rounds": 1}


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
        "--debate",
        action="store_true",
        help="Enable debate mode: multiple rounds where each provider sees others' responses",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=2,
        help="Number of debate rounds (default: 2, requires --debate)",
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
            "uvx_with_flags": " ".join(f"--with {sdk}" for sdk in sdks),
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

    # Run the council.
    result = asyncio.run(
        run_council(combined_prompt, providers, args.debate, args.rounds)
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
        "mode": "debate" if args.debate else "parallel",
        "rounds": result.get("rounds", 1),
    }

    if failed:
        output["failed_reviews"] = failed

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
