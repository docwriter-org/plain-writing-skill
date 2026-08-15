#!/usr/bin/env python3
"""Run a small before/after eval of the plain-writing skill.

Usage:
  cd evals
  uv sync
  uv run python run_eval.py
  uv run python run_eval.py --limit 5
  uv run python run_eval.py --category long_history --limit 1
  uv run python run_eval.py --category fable_coding
  uv run python run_eval.py --concurrency 64
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

ROOT = Path(__file__).resolve().parents[1]
EVALS = Path(__file__).resolve().parent
SOURCES = EVALS / "sources"
DATASET = EVALS / "dataset.jsonl"
SKILL = ROOT / "skills" / "plain-writing" / "SKILL.md"
DEFAULT_OUT = EVALS / "outputs"

DEFAULT_MODEL = "gpt-5.5"
DEFAULT_JUDGE_MODEL = "gpt-5.5"
DEFAULT_CONCURRENCY = 64

BASELINE_SYSTEM = (
    "You are a helpful writing assistant. Write a clear, complete response. "
    "Return only the requested writing."
)

JUDGE_SYSTEM_TEMPLATE = """You compare two texts against one writing rule.

Judge only this rule. Ignore every other writing preference. If both texts follow
the rule about equally, return "tie". If one text drops important task content so
badly that the comparison is unfair, still judge only the writing rule, and prefer
the text that follows the rule unless both break it equally.

Return ONLY valid JSON with these keys:
- winner: "a", "b", or "tie"
- reason: one short sentence
"""

CRITERION_RE = re.compile(
    r"^(\d+)\.\s+\*\*(.+?)\*\*\s*(.*?)(?=^\d+\.\s+\*\*|^## |\Z)",
    re.MULTILINE | re.DOTALL,
)


def parse_criteria(skill_text: str) -> list[dict]:
    criteria = []
    for match in CRITERION_RE.finditer(skill_text):
        number = int(match.group(1))
        title = re.sub(r"\s+", " ", match.group(2)).strip()
        body = re.sub(r"\s+", " ", match.group(3)).strip()
        # Drop before/after examples from the judge prompt to keep it focused.
        body = re.split(r"\bBefore:\b", body, maxsplit=1)[0].strip()
        criteria.append(
            {
                "id": number,
                "title": title,
                "text": f"{number}. **{title}** {body}".strip(),
            }
        )
    if len(criteria) < 10:
        raise RuntimeError(f"Expected many skill criteria, found {len(criteria)}")
    return criteria


def load_dataset(
    path: Path,
    limit: int | None = None,
    category: str | None = None,
    ids: set[str] | None = None,
) -> list[dict]:
    items = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if category and item.get("category") != category:
                continue
            if ids and item.get("id") not in ids:
                continue
            items.append(item)
            if limit is not None and len(items) >= limit:
                break
    return items


def load_history_messages(item: dict) -> list[dict]:
    history_file = item.get("history_file")
    if not history_file:
        return []
    path = SOURCES / history_file
    payload = json.loads(path.read_text())
    messages = payload.get("messages") or []
    cleaned = []
    for message in messages:
        role = message.get("role")
        content = message.get("content", "")
        if role not in ("user", "assistant"):
            continue
        if not isinstance(content, str) or not content.strip():
            continue
        cleaned.append({"role": role, "content": content})
    return cleaned


def build_messages(item: dict) -> list[dict]:
    history = load_history_messages(item)
    prompt = item["prompt"]
    if not history:
        return [{"role": "user", "content": prompt}]
    messages = list(history)
    if messages and messages[-1]["role"] == "user":
        messages[-1]["content"] += "\n\n" + prompt
    else:
        messages.append({"role": "user", "content": prompt})
    return messages


def parse_json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def complete(
    client: OpenAI,
    model: str,
    system: str,
    messages: list[dict],
    max_tokens: int = 1200,
    retries: int = 6,
    reasoning_effort: str = "low",
    api_slots: threading.Semaphore | None = None,
) -> str:
    payload = [{"role": "system", "content": system}, *messages]
    delay = 2.0
    last_exc: Exception | None = None
    token_budget = max_tokens
    for attempt in range(retries):
        try:
            if api_slots is not None:
                api_slots.acquire()
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=payload,
                    max_completion_tokens=token_budget,
                    reasoning_effort=reasoning_effort,
                )
            finally:
                if api_slots is not None:
                    api_slots.release()
            choice = response.choices[0]
            content = choice.message.content
            if not content:
                finish = choice.finish_reason
                details = getattr(response.usage, "completion_tokens_details", None)
                reasoning_tokens = getattr(details, "reasoning_tokens", None)
                if finish == "length" and attempt < retries - 1:
                    token_budget = min(token_budget * 2, 16000)
                    print(
                        f"retry {attempt + 1}/{retries} empty content "
                        f"(finish=length, reasoning_tokens={reasoning_tokens}); "
                        f"raising budget to {token_budget}",
                        flush=True,
                    )
                    continue
                raise RuntimeError(
                    f"Empty completion from {model} "
                    f"(finish={finish}, reasoning_tokens={reasoning_tokens})"
                )
            return content.strip()
        except (RateLimitError, APITimeoutError, APIConnectionError, APIStatusError) as exc:
            last_exc = exc
            status = getattr(exc, "status_code", None)
            message = str(exc)
            hit_token_cap = "max_tokens" in message or "output limit" in message
            retryable = (
                isinstance(exc, (RateLimitError, APITimeoutError, APIConnectionError))
                or (status is not None and status in {408, 409, 429, 500, 502, 503, 504})
                or hit_token_cap
            )
            if not retryable or attempt == retries - 1:
                raise
            if hit_token_cap:
                token_budget = min(max(token_budget * 2, 1200), 16000)
                print(
                    f"retry {attempt + 1}/{retries} after token-cap error; "
                    f"raising budget to {token_budget}",
                    flush=True,
                )
                continue
            print(
                f"retry {attempt + 1}/{retries} after {type(exc).__name__}: sleep {delay:.1f}s",
                flush=True,
            )
            time.sleep(delay)
            delay = min(delay * 2, 60.0)
    assert last_exc is not None
    raise last_exc


def judge_one_criterion(
    client: OpenAI,
    model: str,
    criterion: dict,
    prompt: str,
    text_a: str,
    text_b: str,
    api_slots: threading.Semaphore | None,
) -> dict:
    user = f"""Writing rule:
{criterion["text"]}

Task prompt:
{prompt}

Text A:
{text_a}

Text B:
{text_b}
"""
    raw = complete(
        client,
        model,
        JUDGE_SYSTEM_TEMPLATE,
        [{"role": "user", "content": user}],
        max_tokens=1200,
        reasoning_effort="low",
        api_slots=api_slots,
    )
    try:
        result = parse_json_object(raw)
    except json.JSONDecodeError:
        return {
            "winner": "tie",
            "reason": f"Judge returned non-JSON: {raw[:200]}",
        }
    winner = result.get("winner")
    if winner not in {"a", "b", "tie"}:
        winner = "tie"
    return {
        "winner": winner,
        "reason": str(result.get("reason") or "").strip(),
    }


def judge_pair(
    client: OpenAI,
    model: str,
    criteria: list[dict],
    prompt: str,
    baseline: str,
    with_skill: str,
    api_slots: threading.Semaphore | None,
    rng: random.Random,
) -> dict:
    def judge_criterion(criterion: dict) -> dict:
        # Blind the labels so the judge cannot prefer a "skill" condition.
        skill_is_a = rng.random() < 0.5
        if skill_is_a:
            text_a, text_b = with_skill, baseline
            a_is = "skill"
        else:
            text_a, text_b = baseline, with_skill
            a_is = "baseline"
        raw = judge_one_criterion(
            client, model, criterion, prompt, text_a, text_b, api_slots
        )
        winner = raw["winner"]
        if winner == "tie":
            skill_better = None
        elif (winner == "a" and a_is == "skill") or (winner == "b" and a_is == "baseline"):
            skill_better = True
        else:
            skill_better = False
        return {
            "id": criterion["id"],
            "title": criterion["title"],
            "a_is": a_is,
            "winner": winner,
            "skill_better": skill_better,
            "reason": raw["reason"],
        }

    criterion_results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, len(criteria))) as pool:
        futures = {pool.submit(judge_criterion, criterion): criterion for criterion in criteria}
        for future in as_completed(futures):
            criterion = futures[future]
            try:
                criterion_results.append(future.result())
            except Exception as exc:  # noqa: BLE001
                criterion_results.append(
                    {
                        "id": criterion["id"],
                        "title": criterion["title"],
                        "a_is": "unknown",
                        "winner": "tie",
                        "skill_better": None,
                        "reason": f"Judge error: {exc}",
                    }
                )

    criterion_results.sort(key=lambda row: row["id"])
    skill_wins = sum(1 for row in criterion_results if row["skill_better"] is True)
    baseline_wins = sum(1 for row in criterion_results if row["skill_better"] is False)
    ties = sum(1 for row in criterion_results if row["skill_better"] is None)

    if skill_wins > baseline_wins:
        overall = True
    elif baseline_wins > skill_wins:
        overall = False
    else:
        overall = None

    return {
        "skill_better": overall,
        "skill_criteria_wins": skill_wins,
        "baseline_criteria_wins": baseline_wins,
        "criteria_ties": ties,
        "criteria": criterion_results,
    }


def run_one_item(
    index: int,
    total: int,
    item: dict,
    client: OpenAI,
    model: str,
    judge_model: str,
    criteria: list[dict],
    skill_system: str,
    out_dir: Path,
    sleep_s: float,
    api_slots: threading.Semaphore | None,
) -> dict:
    item_id = item["id"]
    prompt = item["prompt"]
    category = item.get("category", "")
    messages = build_messages(item)
    history_chars = sum(len(m["content"]) for m in messages[:-1]) if len(messages) > 1 else 0
    print(
        f"[{index}/{total}] start {item_id} ({category}) history_chars={history_chars}",
        flush=True,
    )

    if category == "fable_coding":
        max_tokens = 2400
    elif category == "long_history":
        max_tokens = 1600
    else:
        max_tokens = 1200
    baseline = complete(
        client, model, BASELINE_SYSTEM, messages, max_tokens, api_slots=api_slots
    )
    time.sleep(sleep_s)
    with_skill = complete(
        client, model, skill_system, messages, max_tokens, api_slots=api_slots
    )
    time.sleep(sleep_s)
    judgment = judge_pair(
        client,
        judge_model,
        criteria,
        prompt,
        baseline,
        with_skill,
        api_slots,
        random.Random(f"{item_id}:{prompt[:80]}"),
    )

    row = {
        "id": item_id,
        "category": category,
        "prompt": prompt,
        "history_file": item.get("history_file"),
        "history_chars": history_chars,
        "baseline": baseline,
        "with_skill": with_skill,
        "judgment": judgment,
    }
    (out_dir / f"{item_id}.json").write_text(json.dumps(row, indent=2) + "\n")
    print(
        f"[{index}/{total}] done {item_id} "
        f"skill_better={judgment.get('skill_better')} "
        f"criteria={judgment.get('skill_criteria_wins')}-"
        f"{judgment.get('baseline_criteria_wins')}-"
        f"{judgment.get('criteria_ties')}",
        flush=True,
    )
    return row


def summarize_criteria(results: list[dict], criteria: list[dict]) -> dict:
    by_id: dict[int, dict] = {
        c["id"]: {
            "id": c["id"],
            "title": c["title"],
            "skill_wins": 0,
            "baseline_wins": 0,
            "ties": 0,
        }
        for c in criteria
    }
    for row in results:
        for crit in row.get("judgment", {}).get("criteria") or []:
            bucket = by_id.get(crit["id"])
            if not bucket:
                continue
            if crit.get("skill_better") is True:
                bucket["skill_wins"] += 1
            elif crit.get("skill_better") is False:
                bucket["baseline_wins"] += 1
            else:
                bucket["ties"] += 1
    return {
        str(cid): {
            **bucket,
            "skill_win_rate_among_decisive": (
                bucket["skill_wins"] / (bucket["skill_wins"] + bucket["baseline_wins"])
                if (bucket["skill_wins"] + bucket["baseline_wins"])
                else None
            ),
        }
        for cid, bucket in sorted(by_id.items())
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="Run only the first N matching items")
    parser.add_argument("--category", default=None, help="Only run this category")
    parser.add_argument(
        "--ids",
        default=None,
        help="Comma-separated item ids to run, e.g. 41,42",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Rewriter model")
    parser.add_argument(
        "--judge-model",
        default=DEFAULT_JUDGE_MODEL,
        help="Judge model",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--sleep", type=float, default=0.0, help="Pause between rewrite calls inside an item")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help="Max concurrent OpenAI API calls",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is missing. Put it in .env at the repo root.", file=sys.stderr)
        return 1

    skill_text = SKILL.read_text()
    criteria = parse_criteria(skill_text)
    ids = {part.strip() for part in args.ids.split(",")} if args.ids else None
    items = load_dataset(DATASET, args.limit, args.category, ids)
    if not items:
        print(f"No items found in {DATASET}", file=sys.stderr)
        return 1

    client = OpenAI(api_key=api_key)
    judge_model = args.judge_model
    args.out.mkdir(parents=True, exist_ok=True)

    skill_system = (
        "Follow the plain-writing skill below exactly when you write.\n\n"
        f"{skill_text}\n\n"
        "Return only the requested writing."
    )

    results_by_id: dict[str, dict] = {}
    concurrency = max(1, args.concurrency)
    api_slots = threading.Semaphore(concurrency)
    # Oversubscribe item workers; the semaphore caps actual API concurrency.
    item_workers = min(len(items), max(concurrency, 1))
    print(
        f"Running {len(items)} items with api_concurrency={concurrency} "
        f"item_workers={item_workers} criteria={len(criteria)} "
        f"model={args.model} judge={judge_model}",
        flush=True,
    )

    with ThreadPoolExecutor(max_workers=item_workers) as pool:
        futures = {
            pool.submit(
                run_one_item,
                index,
                len(items),
                item,
                client,
                args.model,
                judge_model,
                criteria,
                skill_system,
                args.out,
                args.sleep,
                api_slots,
            ): item["id"]
            for index, item in enumerate(items, start=1)
        }
        for future in as_completed(futures):
            item_id = futures[future]
            try:
                row = future.result()
                results_by_id[item_id] = row
            except Exception as exc:  # noqa: BLE001 - surface per-item failures
                print(f"ERROR {item_id}: {exc}", flush=True)
                results_by_id[item_id] = {
                    "id": item_id,
                    "error": str(exc),
                    "judgment": {
                        "skill_better": None,
                        "skill_criteria_wins": 0,
                        "baseline_criteria_wins": 0,
                        "criteria_ties": 0,
                        "criteria": [],
                        "reason": str(exc),
                    },
                }
                (args.out / f"{item_id}.json").write_text(
                    json.dumps(results_by_id[item_id], indent=2) + "\n"
                )

    results = [results_by_id[item["id"]] for item in items if item["id"] in results_by_id]
    wins = sum(1 for r in results if r.get("judgment", {}).get("skill_better") is True)
    losses = sum(1 for r in results if r.get("judgment", {}).get("skill_better") is False)
    ties = len(results) - wins - losses
    errors = sum(1 for r in results if "error" in r)
    criterion_skill_wins = sum(
        r.get("judgment", {}).get("skill_criteria_wins", 0) for r in results
    )
    criterion_baseline_wins = sum(
        r.get("judgment", {}).get("baseline_criteria_wins", 0) for r in results
    )
    criterion_ties = sum(r.get("judgment", {}).get("criteria_ties", 0) for r in results)

    summary = {
        "model": args.model,
        "judge_model": judge_model,
        "concurrency": concurrency,
        "n_criteria": len(criteria),
        "n": len(results),
        "skill_wins": wins,
        "baseline_wins": losses,
        "ties": ties,
        "errors": errors,
        "skill_win_rate_among_decisive": (
            wins / (wins + losses) if (wins + losses) else None
        ),
        "criterion_skill_wins": criterion_skill_wins,
        "criterion_baseline_wins": criterion_baseline_wins,
        "criterion_ties": criterion_ties,
        "criterion_skill_win_rate_among_decisive": (
            criterion_skill_wins / (criterion_skill_wins + criterion_baseline_wins)
            if (criterion_skill_wins + criterion_baseline_wins)
            else None
        ),
        "by_criterion": summarize_criteria(results, criteria),
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (args.out / "results.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in results)
    )

    print(json.dumps(summary, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
