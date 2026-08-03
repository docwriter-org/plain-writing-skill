"""Command line interface and cross-agent Stop hook adapter."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from .checker import Violation, check_text


TEXT_SUFFIXES = {".md", ".mdx", ".txt", ".rst", ".adoc"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plain-writing-check",
        description="Check prose against the deterministic plain-writing rules.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to check. Use - or omit paths to read stdin.",
    )
    parser.add_argument(
        "--hook",
        action="store_true",
        help="Read a Claude Code or Codex Stop event as JSON from stdin.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select the report format.",
    )
    return parser


def _iter_files(paths: Iterable[str]) -> Iterable[Path]:
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in TEXT_SUFFIXES:
                    yield child
        else:
            yield path


def _read_inputs(paths: list[str]) -> list[tuple[str, str]]:
    if not paths or paths == ["-"]:
        return [("<stdin>", sys.stdin.read())]

    inputs: list[tuple[str, str]] = []
    for path in _iter_files(paths):
        if str(path) == "-":
            inputs.append(("<stdin>", sys.stdin.read()))
            continue
        try:
            inputs.append((str(path), path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError) as error:
            raise ValueError(f"cannot read {path}: {error}") from error
    return inputs


def _text_report(results: list[tuple[str, list[Violation]]]) -> str:
    lines: list[str] = []
    for source, violations in results:
        for item in violations:
            lines.append(
                f"{source}:{item.line}:{item.column}: {item.rule} {item.message}"
            )
            if item.excerpt:
                lines.append(f"  {item.excerpt}")
    count = sum(len(items) for _, items in results)
    noun = "violation" if count == 1 else "violations"
    lines.append(f"{count} {noun}")
    return "\n".join(lines)


def _json_report(results: list[tuple[str, list[Violation]]]) -> str:
    payload = {
        "ok": not any(items for _, items in results),
        "files": [
            {
                "path": source,
                "violations": [item.to_dict() for item in violations],
            }
            for source, violations in results
        ],
    }
    return json.dumps(payload, indent=2)


def _hook_reason(violations: list[Violation]) -> str:
    details = []
    for item in violations[:12]:
        details.append(
            f"{item.rule} on line {item.line}. {item.message} "
            f"Matched text {item.excerpt!r}."
        )
    if len(violations) > len(details):
        details.append(f"{len(violations) - len(details)} more violations were found.")
    joined = "\n".join(details)
    return (
        "Rewrite the entire final response using the plain-writing rules. "
        "Return only the replacement response, with no critique or preface. "
        "Fix the programmatically detected violations below.\n"
        f"{joined}"
    )


def _run_hook() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as error:
        print(json.dumps({"systemMessage": f"Plain-writing hook input error: {error}"}))
        return 0

    if event.get("stop_hook_active"):
        print("{}")
        return 0

    text = event.get("last_assistant_message")
    if not isinstance(text, str) or not text.strip():
        print("{}")
        return 0

    violations = check_text(text)
    if violations:
        print(json.dumps({"decision": "block", "reason": _hook_reason(violations)}))
    else:
        print("{}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.hook:
        return _run_hook()

    try:
        inputs = _read_inputs(args.paths)
    except ValueError as error:
        print(f"plain-writing-check: {error}", file=sys.stderr)
        return 2

    results = [(source, check_text(text)) for source, text in inputs]
    if args.format == "json":
        print(_json_report(results))
    else:
        print(_text_report(results))
    return 1 if any(violations for _, violations in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
