#!/usr/bin/env python3
"""Check that the plugin manifests and commands are in place."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REQUIRED_JSON = (
    ROOT / "package.json",
    ROOT / "plugin.json",
    ROOT / ".cursor-plugin" / "plugin.json",
    ROOT / ".cursor-plugin" / "marketplace.json",
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / ".claude-plugin" / "marketplace.json",
    ROOT / ".codex-plugin" / "plugin.json",
    ROOT / ".agents" / "plugins" / "marketplace.json",
    ROOT / "skills" / "plain-writing" / "hooks" / "cursor-hooks.json",
    ROOT / "skills" / "plain-writing" / "hooks" / "claude-hooks.json",
)
REQUIRED_FILES = (
    ROOT / "commands" / "review.md",
    ROOT / "commands" / "deslopify.md",
    ROOT / "extensions" / "plain-writing-review.js",
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

    codex_plugin = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
    if "claude-hooks.json" not in str(codex_plugin.get("hooks") or ""):
        errors.append("codex plugin does not point at the Stop hook file")
    if not str(codex_plugin.get("skills") or "").startswith("./skills"):
        errors.append("codex plugin is missing the skills path")

    review = (ROOT / "commands" / "review.md").read_text()
    if "four reviewer subagents" not in review:
        errors.append("commands/review.md is missing the four-subagent step")

    skill = (ROOT / "skills" / "plain-writing" / "SKILL.md").read_text()
    if "/plain-writing review" not in skill:
        errors.append("SKILL.md is missing /plain-writing review")

    package = json.loads((ROOT / "package.json").read_text())
    keywords = package.get("keywords") or []
    if "pi-package" not in keywords:
        errors.append("package.json is missing the pi-package keyword")
    pi_manifest = package.get("pi") or {}
    if "./skills" not in str(pi_manifest.get("skills") or ""):
        errors.append("package.json is missing pi.skills")
    if "./extensions" not in str(pi_manifest.get("extensions") or ""):
        errors.append("package.json is missing pi.extensions")
    if "./commands" not in str(pi_manifest.get("prompts") or ""):
        errors.append("package.json is missing pi.prompts")

    python_hook = (ROOT / "skills" / "plain-writing" / "hooks" / "review_followup.py").read_text()
    pi_hook = (ROOT / "extensions" / "plain-writing-review.js").read_text()
    python_followup = _quoted_followup(python_hook)
    js_followup = _quoted_followup(pi_hook)
    if not python_followup:
        errors.append("review_followup.py is missing FOLLOWUP")
    if not js_followup:
        errors.append("plain-writing-review.js is missing FOLLOWUP")
    if python_followup and js_followup and python_followup != js_followup:
        errors.append("FOLLOWUP text differs between the Python hook and the Pi extension")
    if "isWritingPass" not in pi_hook or "agent_settled" not in pi_hook:
        errors.append("Pi extension is missing the writing-pass hook")

    node = _run(["node", str(ROOT / "extensions" / "plain-writing-review.js"), "--self-test"])
    if node is not None and node.returncode != 0:
        errors.append(f"Pi extension self-test failed: {node.stderr or node.stdout}")

    if errors:
        print("plugin check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("plugin check passed")
    return 0


def _quoted_followup(source: str) -> str:
    match = re.search(r'FOLLOWUP\s*=\s*\((.*?)\)', source, re.DOTALL)
    if match:
        return "".join(re.findall(r'"([^"]*)"', match.group(1)))
    match = re.search(r'FOLLOWUP\s*=\s*\n?\s*"([^"]*(?:"\s*\+\s*\n\s*"[^"]*)*)"', source)
    if not match:
        return ""
    return re.sub(r'"\s*\+\s*\n\s*"', "", match.group(1))


def _run(command: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
