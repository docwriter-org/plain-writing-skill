#!/usr/bin/env python3
"""Check that the plugin manifests and commands are in place."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REQUIRED_JSON = (
    ROOT / "plugin.json",
    ROOT / ".cursor-plugin" / "plugin.json",
    ROOT / ".cursor-plugin" / "marketplace.json",
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / ".claude-plugin" / "marketplace.json",
    ROOT / "skills" / "plain-writing" / "hooks" / "cursor-hooks.json",
    ROOT / "skills" / "plain-writing" / "hooks" / "claude-hooks.json",
)
REQUIRED_FILES = (
    ROOT / "commands" / "review.md",
    ROOT / "commands" / "deslopify.md",
    ROOT / "skills" / "plain-writing" / "SKILL.md",
    ROOT / "skills" / "plain-writing" / "hooks" / "run-review-followup.sh",
    ROOT / "skills" / "plain-writing" / "hooks" / "review_followup.py",
)


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_JSON:
        if not path.is_file():
            errors.append(f"missing {path.relative_to(ROOT)}")
            continue
        try:
            json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")

    for path in REQUIRED_FILES:
        if not path.is_file():
            errors.append(f"missing {path.relative_to(ROOT)}")

    cursor_hooks = json.loads(
        (ROOT / "skills" / "plain-writing" / "hooks" / "cursor-hooks.json").read_text()
    )
    cursor_cmd = cursor_hooks["hooks"]["stop"][0]["command"]
    if "run-review-followup.sh" not in cursor_cmd:
        errors.append("cursor hook does not call run-review-followup.sh")

    claude_hooks = json.loads(
        (ROOT / "skills" / "plain-writing" / "hooks" / "claude-hooks.json").read_text()
    )
    claude_cmd = claude_hooks["hooks"]["Stop"][0]["hooks"][0]["command"]
    if "run-review-followup.sh" not in claude_cmd:
        errors.append("claude hook does not call run-review-followup.sh")

    review = (ROOT / "commands" / "review.md").read_text()
    if "four reviewer subagents" not in review:
        errors.append("commands/review.md is missing the four-subagent step")

    skill = (ROOT / "skills" / "plain-writing" / "SKILL.md").read_text()
    if "/plain-writing review" not in skill:
        errors.append("SKILL.md is missing /plain-writing review")

    if errors:
        print("plugin check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("plugin check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
