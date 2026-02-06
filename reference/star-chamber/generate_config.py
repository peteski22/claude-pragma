"""Generate star-chamber provider config from reference file."""

import argparse
import json
import pathlib
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate star-chamber config.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--platform", action="store_true", help="Platform mode (strips api_key fields).")
    group.add_argument("--direct", action="store_true", help="Direct keys mode (strips platform field).")
    args = parser.parse_args()

    ref_path = pathlib.Path(__file__).parent / "providers.json"
    if not ref_path.exists():
        print(f"Reference file not found: {ref_path}", file=sys.stderr)
        sys.exit(1)

    ref = json.loads(ref_path.read_text())

    if args.platform:
        ref["providers"] = [
            {k: v for k, v in p.items() if k != "api_key"} for p in ref["providers"]
        ]
    else:
        ref.pop("platform", None)

    dest = pathlib.Path.home() / ".config" / "star-chamber" / "providers.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(ref, indent=2) + "\n")
    print(f"Wrote {dest}")


if __name__ == "__main__":
    main()
