#!/usr/bin/env python3
"""Start /plain-writing review after a writing pass, not after coding.

afterAgentResponse stores the last assistant reply. stop / Stop then
decides whether that reply was a writing pass. If it was, Cursor gets a
followup_message and Claude Code gets a blocked Stop. Both tell the main
agent to launch the four reviewer subagents and fix the writing.

The hook follows up at most once per conversation. It stays quiet on
code-heavy turns, short status replies, and the review pass itself.
Set PLAIN_WRITING_REVIEW_HOOK=always only if you want every completed
turn treated as writing.

Keep FOLLOWUP and is_writing_pass in sync with
extensions/plain-writing-review.js, which is the same check for Pi.
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
    r"\bsummary\b|"
    r"\breport\b|"
    r"plain writing|"
    r"review this writing|"
    r"write (?:a |an |the )?(?:doc|docs|readme|memo|email|summary|report|"
    r"update|post|essay|letter)\b"
    r")",
    re.IGNORECASE,
)

CODING_RE = re.compile(
    r"("
    r"\b(implement|refactor|debug|compile|lint|typecheck)\b|"
    r"\bfix (the )?(bug|error|test|regex|hook|script|function|parser|build)\b|"
    r"\b(git commit|git push|merge conflict|stack trace|unit test)\b"
    r")",
    re.IGNORECASE,
)

CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
MIN_WRITING_CHARS = 240

STATE_DIR = Path(os.environ.get("TMPDIR", "/tmp")) / "plain-writing-review"


def read_payload() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    return json.loads(raw)


def conversation_id(payload: dict) -> str:
    return str(payload.get("conversation_id") or payload.get("session_id") or "")


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


def _message_text(message: dict) -> str:
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


def _latest_role_text(transcript: str, roles: set[str]) -> str:
    if not transcript:
        return ""
    try:
        payload = json.loads(transcript)
    except json.JSONDecodeError:
        return ""

    messages = payload if isinstance(payload, list) else payload.get("messages") or []
    for message in reversed(messages):
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "").lower()
        if role not in roles:
            continue
        text = _message_text(message)
        if text.strip():
            return text
    return ""


def latest_user_text(transcript: str) -> str:
    return _latest_role_text(transcript, {"user", "human"})


def latest_assistant_text(transcript: str) -> str:
    return _latest_role_text(transcript, {"assistant", "model"})


def response_path(cid: str) -> Path:
    return STATE_DIR / f"{cid}.response.json"


def save_response(payload: dict) -> None:
    cid = conversation_id(payload)
    text = str(payload.get("text") or "")
    if not cid or not text.strip():
        return
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        response_path(cid).write_text(json.dumps({"text": text}))
    except OSError:
        return


def load_saved_response(cid: str) -> str:
    if not cid:
        return ""
    path = response_path(cid)
    if not path.is_file():
        return ""
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return ""
    return str(payload.get("text") or "")


def already_followed_up(cid: str) -> bool:
    if not cid:
        return False
    return (STATE_DIR / f"{cid}.done").is_file()


def mark_followed_up(cid: str) -> None:
    if not cid:
        return
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        (STATE_DIR / f"{cid}.done").write_text("1\n")
    except OSError:
        return


def code_fraction(text: str) -> float:
    fenced = sum(len(block) for block in CODE_FENCE_RE.findall(text))
    return fenced / max(len(text), 1)


def is_writing_pass(user_text: str, assistant_text: str) -> bool:
    if os.environ.get("PLAIN_WRITING_REVIEW_HOOK", "").lower() in {"1", "always", "true"}:
        return True
    assistant = (assistant_text or "").strip()
    user = (user_text or "").strip()
    if len(assistant) < MIN_WRITING_CHARS:
        return False
    if user == FOLLOWUP or "/plain-writing review" in user:
        return False
    if code_fraction(assistant) >= 0.35:
        return False
    user_wants_writing = bool(WRITING_RE.search(user))
    user_wants_coding = bool(CODING_RE.search(user))
    if user_wants_coding and not user_wants_writing:
        return False
    if user_wants_writing:
        return True
    if code_fraction(assistant) == 0 and len(assistant) >= 500:
        if re.search(r"\b(committed|pushed|pull request|diff|tests pass)\b", assistant, re.I):
            return False
        return True
    return False


def turn_texts(payload: dict) -> tuple[str, str]:
    transcript = transcript_text(payload.get("transcript_path"))
    user_text = latest_user_text(transcript)
    assistant_text = (
        str(payload.get("text") or "").strip()
        or latest_assistant_text(transcript)
        or load_saved_response(conversation_id(payload))
    )
    return user_text, assistant_text


def should_follow_up(payload: dict) -> bool:
    status = str(payload.get("status") or "completed").lower()
    if status not in {"completed", "success", ""}:
        return False
    loop_count = payload.get("loop_count")
    if isinstance(loop_count, int) and loop_count >= 1:
        return False
    cid = conversation_id(payload)
    if already_followed_up(cid):
        return False
    user_text, assistant_text = turn_texts(payload)
    return is_writing_pass(user_text, assistant_text)


def emit(payload: dict) -> dict:
    event = str(payload.get("hook_event_name") or "")
    if event in {"afterAgentResponse", "AgentResponse"}:
        save_response(payload)
        return {}
    if not should_follow_up(payload):
        return {}
    mark_followed_up(conversation_id(payload))
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


def _clear_markers(*ids: str) -> None:
    for cid in ids:
        for suffix in (".done", ".response.json"):
            path = STATE_DIR / f"{cid}{suffix}"
            if path.exists():
                path.unlink()


def self_test() -> int:
    errors: list[str] = []

    def check(name: str, ok: bool) -> None:
        if not ok:
            errors.append(name)

    writing_sample = (
        "Search ranking now uses a scored model instead of heuristics, and p95 "
        "latency fell from 900 ms to 220 ms. The old heuristic path is still in "
        "the repo as a fallback. To do: test recall on long queries. Dark mode "
        "shipped, and the invite link bug is fixed. Analytics export is still "
        "blocked on a schema mismatch."
    )
    check(
        "draft request is a writing pass",
        is_writing_pass("Draft a project update for engineering.", writing_sample),
    )
    check(
        "bug fix is not a writing pass",
        not is_writing_pass(
            "Fix the bug in parse_criteria.",
            "The parser skipped extra headings. I changed the regex and added a test.\n\n"
            "```python\nCRITERION_RE = re.compile('x')\n```\n",
        ),
    )
    check(
        "code-heavy reply is not a writing pass",
        not is_writing_pass(
            "Show me the new hook.",
            "Here is the script.\n\n```python\n"
            + ("print('x')\n" * 40)
            + "```\n\n```python\n"
            + ("print('y')\n" * 40)
            + "```\n",
        ),
    )
    check(
        "short status is not a writing pass",
        not is_writing_pass("Write a memo.", "Done."),
    )
    check(
        "review follow-up is not a writing pass",
        not is_writing_pass(FOLLOWUP, "A" * 300),
    )

    previous = _with_env("PLAIN_WRITING_REVIEW_HOOK", "always")
    ids = ("test-cursor-hit", "test-cursor-loop", "test-claude-hit", "test-skip-nonwriting")
    _clear_markers(*ids)
    try:
        cursor_hit = emit(
            {
                "hook_event_name": "stop",
                "status": "completed",
                "loop_count": 0,
                "conversation_id": "test-cursor-hit",
            }
        )
        check("always mode still follows up", cursor_hit.get("followup_message") == FOLLOWUP)

        cursor_loop = emit(
            {
                "hook_event_name": "stop",
                "status": "completed",
                "loop_count": 1,
                "conversation_id": "test-cursor-loop",
            }
        )
        check("second loop stays quiet", not cursor_loop)

        claude_hit = emit(
            {
                "hook_event_name": "Stop",
                "status": "completed",
                "session_id": "test-claude-hit",
            }
        )
        check(
            "claude writing turn blocks",
            claude_hit.get("decision") == "block" and claude_hit.get("reason") == FOLLOWUP,
        )
    finally:
        _restore_env("PLAIN_WRITING_REVIEW_HOOK", previous)
        _clear_markers(*ids)

    skipped = emit(
        {
            "hook_event_name": "stop",
            "status": "completed",
            "loop_count": 0,
            "conversation_id": "test-skip-nonwriting",
        }
    )
    check("no transcript stays quiet", not skipped)

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    recorded = emit(
        {
            "hook_event_name": "afterAgentResponse",
            "conversation_id": "test-saved-response",
            "text": (
                "Search ranking now uses a scored model, and p95 latency fell from 900 ms "
                "to 220 ms. The old heuristic path is still in the repo as a fallback."
            ),
        }
    )
    check("afterAgentResponse only records", recorded == {})

    transcript = STATE_DIR / "test-transcript.json"
    transcript.write_text(
        json.dumps(
            {
                "messages": [
                    {"role": "user", "content": "Draft a project update for engineering."},
                    {
                        "role": "assistant",
                        "content": writing_sample,
                    },
                ]
            }
        )
    )
    try:
        writing_turn = emit(
            {
                "hook_event_name": "stop",
                "status": "completed",
                "loop_count": 0,
                "conversation_id": "test-transcript-hit",
                "transcript_path": str(transcript),
            }
        )
        check("writing transcript follows up", writing_turn.get("followup_message") == FOLLOWUP)

        coding_transcript = STATE_DIR / "test-coding-transcript.json"
        coding_transcript.write_text(
            json.dumps(
                {
                    "messages": [
                        {"role": "user", "content": "Implement the hook script and add tests."},
                        {
                            "role": "assistant",
                            "content": (
                                "I added review_followup.py and a self-test.\n\n"
                                "```python\ndef emit(payload):\n    return {}\n```\n"
                            ),
                        },
                    ]
                }
            )
        )
        coding_turn = emit(
            {
                "hook_event_name": "stop",
                "status": "completed",
                "loop_count": 0,
                "conversation_id": "test-coding-hit",
                "transcript_path": str(coding_transcript),
            }
        )
        check("coding transcript stays quiet", not coding_turn)
    finally:
        for path in (transcript, STATE_DIR / "test-coding-transcript.json"):
            if path.exists():
                path.unlink()
        _clear_markers("test-transcript-hit", "test-coding-hit", "test-saved-response")

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
