#!/usr/bin/env python3
"""Block Thai control text in storyboard/image-generation prompts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterator


THAI = re.compile(r"[\u0E00-\u0E7F]")
PROMPT_KEYS = {"prompt", "image_prompt", "storyboard_prompt"}


def prompt_values(value: object, location: str = "root") -> Iterator[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            if key in PROMPT_KEYS:
                if not isinstance(child, str):
                    raise ValueError(f"{child_location} must be a string")
                yield child_location, child
            else:
                yield from prompt_values(child, child_location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from prompt_values(child, f"{location}[{index}]")


def prompts_in(path: Path) -> list[tuple[str, str]]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        prompts = list(prompt_values(payload))
        if not prompts:
            raise ValueError("JSON contains no prompt, image_prompt, or storyboard_prompt field")
        return prompts
    if path.suffix.lower() in {".md", ".txt"}:
        return [("document", path.read_text(encoding="utf-8"))]
    raise ValueError("prompt file must be .json, .md, or .txt")


def allowed_languages(schema_path: Path) -> set[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    policy = schema.get("language_policy") or {}
    languages = policy.get("generation_prompt_languages")
    if not isinstance(languages, list) or not all(isinstance(language, str) for language in languages):
        raise ValueError("schema language_policy.generation_prompt_languages must be a string list")
    return set(languages)


def main() -> int:
    skill_dir = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt_file", type=Path)
    parser.add_argument("--language", required=True, choices=("en", "zh-CN"))
    parser.add_argument(
        "--schema",
        type=Path,
        default=skill_dir / "config" / "base-schema.json",
        help="base schema containing language_policy",
    )
    args = parser.parse_args()

    try:
        if args.language not in allowed_languages(args.schema):
            raise ValueError(f"{args.language!r} is not allowed by {args.schema}")
        prompts = prompts_in(args.prompt_file)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))

    errors = [
        f"{args.prompt_file}:{location}: Thai control text is not allowed in an image prompt"
        for location, prompt in prompts
        if THAI.search(prompt)
    ]
    if errors:
        print("\n".join(errors))
        return 1

    print(f"PASS {args.prompt_file}: {len(prompts)} image prompt(s), language={args.language}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
