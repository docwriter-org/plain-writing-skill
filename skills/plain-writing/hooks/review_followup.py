#!/usr/bin/env python3
"""Ask the agent to run /plain-writing review after a writing turn.

Cursor stop hooks can return followup_message. Claude Code Stop hooks can
block with a reason. Both paths tell the main agent to launch the four
reviewer subagents and then fix the writing.

The hook follows up at most once per conversation. Set
PLAIN_WRITING_REVIEW_HOOK=always to treat every completed turn as a
writing turn. The default is to follow up only when the latest user
message looks like a writing request.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

FOLLOWUP = (
    "Run /plain-writing review on your last response. Launch four reviewer "
    "subagents, one per rule group, in the same turn. Wait for their "
    "findings. Fix every fail. Then reply with only the rewrite."
)

WRITING_RE = re.compile(
    r"("
    r"/plain-writing|"
    r"\bdeslopify\b|"
    r"\brewrite\b|"
    r"\bdraft\b|"
    r"\bmemo\b|"
    r"\breadme\b|"
    r"\bsummary\b|"
    r"\breport\b|"
    r"plain writing|"
    r"review this writing|"
    r"write (?:a |an |the )?(?:doc|docs|readme|memo|email|summary|report|pr\b)"
    r")",
    re.IGNORECASE,
)

STATE_DIR = Path(os.environ.get("TMPDIR", "/tmp")) / "plain-writing-review"


def read_payload() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    return json.loads(raw)


def transcript_text(path_value: str | None) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.is_file():
        return ""
    try:
        return path.read_text(errors="ignore")
    except OSError:
        return ""


def latest_user_text(transcript: str) -> str:
    if not transcript:
        return ""
    try:
        payload = json.loads(transcript)
    except json.JSONDecodeError:
        return transcript[-4000:]

    messages = payload if isinstance(payload, list) else payload.get("messages") or []
    for message in reversed(messages):
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "").lower()
        if role not in {"user", "human"}:
            continue
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and item.get("type") in {"text", "input_text"}:
                    parts.append(str(item.get("text") or ""))
            return "\n".join(parts)
    return ""


def already_followed_up(conversation_id: str) -> bool:
    if not conversation_id:
        return False
    marker = STATE_DIR / f"{conversation_id}.done"
    return marker.is_file()


def mark_followed_up(conversation_id: str) -> None:
    if not conversation_id:
        return
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        (STATE_DIR / f"{conversation_id}.done").write_text("1\n")
    except OSError:
        return


def is_writing_turn(payload: dict) -> bool:
    if os.environ.get("PLAIN_WRITING_REVIEW_HOOK", "").lower() in {"1", "always", "true"}:
        return True
    transcript = transcript_text(payload.get("transcript_path"))
    user_text = latest_user_text(transcript)
    if not user_text:
        return False
    return bool(WRITING_RE.search(user_text))


def should_follow_up(payload: dict) -> bool:
    status = str(payload.get("status") or "completed").lower()
    if status not in {"completed", "success", ""}:
        return False
    loop_count = payload.get("loop_count")
    if isinstance(loop_count, int) and loop_count >= 1:
        return False
    conversation_id = str(payload.get("conversation_id") or payload.get("session_id") or "")
    if already_followed_up(conversation_id):
        return False
    return is_writing_turn(payload)


def emit(payload: dict) -> dict:
    if not should_follow_up(payload):
        return {}
    conversation_id = str(payload.get("conversation_id") or payload.get("session_id") or "")
    mark_followed_up(conversation_id)
    event = str(payload.get("hook_event_name") or "")
    # Claude Code uses Stop plus decision/reason. Cursor uses followup_message.
    if event == "Stop" or (event.lower() == "stop" and "loop_count" not in payload):
        return {"decision": "block", "reason": FOLLOWUP}
    return {"followup_message": FOLLOWUP}


def _with_env(name: str, value: str | None):
    previous = os.environ.get(name)
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value
    return previous


def _restore_env(name: str, previous: str | None) -> None:
    if previous is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = previous


def self_test() -> int:
    errors: list[str] = []
    previous = _with_env("PLAIN_WRITING_REVIEW_HOOK", "always")
    ids = (
        "test-cursor-hit",
        "test-cursor-loop",
        "test-claude-hit",
        "test-skip-nonwriting",
    )
    for conversation_id in ids:
        marker = STATE_DIR / f"{conversation_id}.done"
        if marker.exists():
            marker.unlink()
    try:
        cursor_hit = emit(
            {
                "hook_event_name": "stop",
                "status": "completed",
                "loop_count": 0,
                "conversation_id": "test-cursor-hit",
                "transcript_path": "",
            }
        )
        if cursor_hit.get("followup_message") != FOLLOWUP:
            errors.append(f"cursor writing turn should follow up, got {cursor_hit}")

        cursor_loop = emit(
            {
                "hook_event_name": "stop",
                "status": "completed",
                "loop_count": 1,
                "conversation_id": "test-cursor-loop",
            }
        )
        if cursor_loop:
            errors.append(f"cursor second loop should stay quiet, got {cursor_loop}")

        claude_hit = emit(
            {
                "hook_event_name": "Stop",
                "status": "completed",
                "session_id": "test-claude-hit",
            }
        )
        if claude_hit.get("decision") != "block" or claude_hit.get("reason") != FOLLOWUP:
            errors.append(
                f"claude writing turn should block with review reason, got {claude_hit}"
            )

        cursor_again = emit(
            {
                "hook_event_name": "stop",
                "status": "completed",
                "loop_count": 0,
                "conversation_id": "test-cursor-hit",
                "transcript_path": "",
            }
        )
        if cursor_again:
            errors.append(
                f"same conversation should follow up only once, got {cursor_again}"
            )
    finally:
        _restore_env("PLAIN_WRITING_REVIEW_HOOK", previous)
        for conversation_id in ids:
            marker = STATE_DIR / f"{conversation_id}.done"
            if marker.exists():
                marker.unlink()

    skipped = emit(
        {
            "hook_event_name": "stop",
            "status": "completed",
            "loop_count": 0,
            "conversation_id": "test-skip-nonwriting",
            "transcript_path": "",
        }
    )
    if skipped:
        errors.append(f"non-writing turn should stay quiet, got {skipped}")

    transcript = STATE_DIR / "test-transcript.json"
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        transcript.write_text(
            json.dumps(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Please rewrite this README in plain writing.",
                        }
                    ]
                }
            )
        )
        from_transcript = emit(
            {
                "hook_event_name": "stop",
                "status": "completed",
                "loop_count": 0,
                "conversation_id": "test-transcript-hit",
                "transcript_path": str(transcript),
            }
        )
        if from_transcript.get("followup_message") != FOLLOWUP:
            errors.append(
                f"writing transcript should follow up, got {from_transcript}"
            )
    finally:
        if transcript.exists():
            transcript.unlink()
        marker = STATE_DIR / "test-transcript-hit.done"
        if marker.exists():
            marker.unlink()

    if errors:
        print("self-test failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("self-test passed: review follow-up hook")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    try:
        payload = read_payload()
    except json.JSONDecodeError:
        print("{}")
        return 0
    print(json.dumps(emit(payload)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
