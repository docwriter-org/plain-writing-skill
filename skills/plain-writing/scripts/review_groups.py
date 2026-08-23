#!/usr/bin/env python3
"""Build reviewer-subagent prompts from the plain-writing skill.

Usage:
  python review_groups.py --list
  python review_groups.py --prompts
  python review_groups.py --writing draft.md --prompts
  python review_groups.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = SKILL_DIR / "SKILL.md"
REVIEWER = SKILL_DIR / "agents" / "reviewer.md"

CRITERION_RE = re.compile(
    r"^(\d+)\.\s+\*\*(.+?)\*\*\s*(.*?)(?=^\d+\.\s+\*\*|^## |\Z)",
    re.MULTILINE | re.DOTALL,
)

GROUPS = (
    {
        "id": "word-choice",
        "title": "Word choice and tone",
        "start": 1,
        "end": 7,
    },
    {
        "id": "sentences",
        "title": "Sentences and paragraphs",
        "start": 8,
        "end": 14,
    },
    {
        "id": "punctuation",
        "title": "Punctuation and formatting",
        "start": 15,
        "end": 19,
    },
    {
        "id": "patterns",
        "title": "Patterns to avoid",
        "start": 20,
        "end": 25,
    },
)

REVIEW_MARKERS = (
    "/plain-writing review",
)


def parse_criteria(skill_text: str) -> list[dict]:
    criteria = []
    for match in CRITERION_RE.finditer(skill_text):
        number = int(match.group(1))
        title = re.sub(r"\s+", " ", match.group(2)).strip()
        body = re.sub(r"\s+", " ", match.group(3)).strip()
        criteria.append(
            {
                "id": number,
                "title": title,
                "text": f"{number}. **{title}** {body}".strip(),
            }
        )
    return criteria


def grouped_criteria(criteria: list[dict]) -> list[dict]:
    by_id = {item["id"]: item for item in criteria}
    groups = []
    for group in GROUPS:
        rules = [by_id[n] for n in range(group["start"], group["end"] + 1) if n in by_id]
        groups.append({**group, "rules": rules})
    return groups


def build_prompt(group: dict, writing: str, reviewer_text: str) -> str:
    rule_block = "\n\n".join(rule["text"] for rule in group["rules"])
    writing_block = writing.strip() if writing.strip() else "[PASTE THE WRITING HERE]"
    return (
        f"{reviewer_text.strip()}\n\n"
        f"## Your group\n\n"
        f"{group['title']} (`{group['id']}`). Judge only rules "
        f"{group['start']} to {group['end']}.\n\n"
        f"## Rules\n\n"
        f"{rule_block}\n\n"
        f"## Writing\n\n"
        f"{writing_block}\n"
    )


def load_writing(path: Path | None) -> str:
    if path is None:
        return ""
    return path.read_text()


def self_test() -> int:
    skill_text = SKILL.read_text()
    criteria = parse_criteria(skill_text)
    groups = grouped_criteria(criteria)
    errors: list[str] = []

    if len(criteria) != 25:
        errors.append(f"expected 25 rules, found {len(criteria)}")

    covered = [rule["id"] for group in groups for rule in group["rules"]]
    if covered != list(range(1, 26)):
        errors.append(f"groups do not cover rules 1 to 25 exactly: {covered}")

    if not REVIEWER.is_file():
        errors.append(f"missing reviewer file: {REVIEWER}")

    for marker in REVIEW_MARKERS:
        if marker not in skill_text:
            errors.append(f"SKILL.md does not mention {marker}")

    if "Launch four reviewer subagents" not in skill_text:
        errors.append("SKILL.md is missing the four-subagent review step")
    if "code fence" not in skill_text:
        errors.append("SKILL.md does not tell the agent to read fenced JSON")

    if "agents/reviewer.md" not in skill_text:
        errors.append("SKILL.md does not point at agents/reviewer.md")

    prompts = [build_prompt(group, "Sample writing.", REVIEWER.read_text()) for group in groups]
    if len(prompts) != 4:
        errors.append(f"expected 4 prompts, built {len(prompts)}")
    for prompt, group in zip(prompts, groups):
        if group["id"] not in prompt:
            errors.append(f"prompt missing group id {group['id']}")
        if "Sample writing." not in prompt:
            errors.append(f"prompt for {group['id']} is missing the writing")

    if errors:
        print("self-test failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("self-test passed: 25 rules in 4 review groups")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="Print rule groups as JSON")
    parser.add_argument("--prompts", action="store_true", help="Print subagent prompts")
    parser.add_argument("--writing", type=Path, default=None, help="Writing file to embed")
    parser.add_argument("--self-test", action="store_true", help="Check rule grouping")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    skill_text = SKILL.read_text()
    criteria = parse_criteria(skill_text)
    if len(criteria) < 10:
        print(f"Expected many skill criteria, found {len(criteria)}", file=sys.stderr)
        return 1
    groups = grouped_criteria(criteria)
    writing = load_writing(args.writing)
    reviewer_text = REVIEWER.read_text()

    if args.list:
        payload = [
            {
                "id": group["id"],
                "title": group["title"],
                "start": group["start"],
                "end": group["end"],
                "rule_ids": [rule["id"] for rule in group["rules"]],
                "titles": [rule["title"] for rule in group["rules"]],
            }
            for group in groups
        ]
        print(json.dumps(payload, indent=2))
        return 0

    if args.prompts:
        output = [
            {
                "id": group["id"],
                "title": group["title"],
                "prompt": build_prompt(group, writing, reviewer_text),
            }
            for group in groups
        ]
        print(json.dumps(output, indent=2))
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
