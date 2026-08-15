#!/usr/bin/env python3
"""Write evals/README.md from the latest output summaries and samples."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset.jsonl"
README = ROOT / "README.md"
OUTPUTS = ROOT / "outputs"
RESULT_DIRS = (
    OUTPUTS / "core",
    OUTPUTS / "fable_coding",
    OUTPUTS / "new_rules",
    OUTPUTS / "all",
)
EXCERPT_CHARS = 900
# GitHub sizes HTML tables to the longest line. Long paragraphs in the
# baseline column then stretch the page. Wrap cells so each column stays
# about one third of the README width.
CELL_WRAP = 40
SAMPLES = (
    ("05", "Product launch copy"),
    ("08", "Slide script"),
    ("02", "Product memo"),
    ("59", "Fable wrap-up"),
    ("25", "Slide titles"),
    ("32", "Support reply"),
    ("67", "Engineering brief"),
)


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def load_dataset() -> dict[str, dict]:
    items = {}
    with DATASET.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            items[item["id"]] = item
    return items


def load_results() -> dict[str, dict]:
    """Load per-item result files. Later dirs override earlier ones."""
    results: dict[str, dict] = {}
    for out_dir in RESULT_DIRS:
        if not out_dir.is_dir():
            continue
        for path in sorted(out_dir.glob("[0-9][0-9].json")):
            row = load_json(path)
            if row and row.get("id"):
                results[row["id"]] = row
    return results


def raw_text(item: dict) -> str | None:
    prompt = item.get("prompt") or ""
    for marker in ("Wrap-up:\n", "Text:\n", "Excerpt:\n"):
        if marker in prompt:
            return prompt.split(marker, 1)[1].strip()
    return None


def excerpt(text: str, limit: int | None = EXCERPT_CHARS) -> str:
    text = (text or "").strip()
    if limit is None or len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n\n[...]"


def pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.0f}%"


def summarize(rows: list[dict]) -> dict:
    wins = sum(1 for r in rows if r.get("judgment", {}).get("skill_better") is True)
    losses = sum(1 for r in rows if r.get("judgment", {}).get("skill_better") is False)
    errors = sum(1 for r in rows if "error" in r)
    ties = len(rows) - wins - losses
    criterion_skill = sum(
        r.get("judgment", {}).get("skill_criteria_wins", 0) for r in rows
    )
    criterion_baseline = sum(
        r.get("judgment", {}).get("baseline_criteria_wins", 0) for r in rows
    )
    criterion_ties = sum(r.get("judgment", {}).get("criteria_ties", 0) for r in rows)
    models = {(r.get("model"), r.get("judge_model")) for r in rows}
    model = "?"
    judge = "?"
    if len(models) == 1:
        only = next(iter(models))
        model = only[0] or "?"
        judge = only[1] or "?"
    elif rows:
        # Item files do not store model; fall back to a sibling summary.
        model = rows[0].get("model") or "?"
        judge = rows[0].get("judge_model") or "?"
    return {
        "n": len(rows),
        "skill_wins": wins,
        "baseline_wins": losses,
        "ties": ties,
        "errors": errors,
        "skill_win_rate_among_decisive": (
            wins / (wins + losses) if (wins + losses) else None
        ),
        "criterion_skill_wins": criterion_skill,
        "criterion_baseline_wins": criterion_baseline,
        "criterion_ties": criterion_ties,
        "criterion_skill_win_rate_among_decisive": (
            criterion_skill / (criterion_skill + criterion_baseline)
            if (criterion_skill + criterion_baseline)
            else None
        ),
        "model": model,
        "judge_model": judge,
        "by_criterion": summarize_criteria(rows),
    }


def summarize_criteria(rows: list[dict]) -> dict:
    by_id: dict[int, dict] = {}
    for row in rows:
        for crit in row.get("judgment", {}).get("criteria") or []:
            cid = crit.get("id")
            if cid is None:
                continue
            bucket = by_id.setdefault(
                cid,
                {
                    "id": cid,
                    "title": crit.get("title") or str(cid),
                    "skill_wins": 0,
                    "baseline_wins": 0,
                    "ties": 0,
                },
            )
            if crit.get("title"):
                bucket["title"] = crit["title"]
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


def attach_models(summary: dict, result_dirs: tuple[Path, ...]) -> dict:
    if summary.get("model") not in (None, "?"):
        return summary
    for out_dir in reversed(result_dirs):
        sibling = load_json(out_dir / "summary.json")
        if sibling and sibling.get("model"):
            summary["model"] = sibling.get("model", "?")
            summary["judge_model"] = sibling.get("judge_model", "?")
            return summary
    return summary


def html_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["<table>", "<thead>", "<tr>"]
    lines.extend(f"<th>{html_escape(header)}</th>" for header in headers)
    lines.extend(["</tr>", "</thead>", "<tbody>"])
    for row in rows:
        lines.append("<tr>")
        lines.extend(f"<td>{html_escape(cell)}</td>" for cell in row)
        lines.append("</tr>")
    lines.extend(["</tbody>", "</table>"])
    return "\n".join(lines)


def summary_table(summary: dict) -> str:
    return html_table(
        ["Metric", "Result"],
        [
            ["Writing tasks", str(summary.get("n", 0))],
            [
                "Skill / baseline / tie",
                f"{summary.get('skill_wins', 0)} / {summary.get('baseline_wins', 0)} / {summary.get('ties', 0)}",
            ],
            [
                "Win rate among decisive tasks",
                pct(summary.get("skill_win_rate_among_decisive")),
            ],
            [
                "Rule skill / baseline / tie",
                f"{summary.get('criterion_skill_wins', 0)} / {summary.get('criterion_baseline_wins', 0)} / {summary.get('criterion_ties', 0)}",
            ],
            [
                "Rule win rate among decisive",
                pct(summary.get("criterion_skill_win_rate_among_decisive")),
            ],
            ["Errors", str(summary.get("errors", 0))],
            [
                "Rewriter / judge",
                f"{summary.get('model', '?')} / {summary.get('judge_model', '?')}",
            ],
        ],
    )


def criterion_rows(summary: dict, limit: int = 8) -> str:
    by_c = summary.get("by_criterion") or {}
    rows = []
    for bucket in by_c.values():
        decisive = bucket.get("skill_wins", 0) + bucket.get("baseline_wins", 0)
        if not decisive:
            continue
        rows.append(
            (
                bucket.get("skill_win_rate_among_decisive") or 0,
                bucket.get("id"),
                bucket.get("title"),
                bucket.get("skill_wins", 0),
                bucket.get("baseline_wins", 0),
                bucket.get("ties", 0),
            )
        )
    rows.sort(key=lambda r: (-(r[3] - r[4]), -r[3], r[1]))

    def rule_table(selected: list) -> str:
        return html_table(
            ["Rule", "Skill / baseline / tie"],
            [
                [
                    f"{cid}. {title}",
                    f"{sw} / {bw} / {ties} ({pct(rate)})",
                ]
                for rate, cid, title, sw, bw, ties in selected
            ],
        )

    parts = [rule_table(rows[:limit])]
    losses = [r for r in rows if r[4] > r[3]]
    if losses:
        parts.extend(
            ["", "Rules where the baseline won more often:", "", rule_table(losses[:5])]
        )
    return "\n".join(parts)


def html_escape(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def sample_title(item_id: str, item: dict) -> str:
    source = item.get("source") or {}
    return (
        source.get("task")
        or source.get("title")
        or item.get("source_key")
        or item.get("category")
        or item_id
    )


def wrap_lines(text: str, width: int = CELL_WRAP) -> str:
    """Break long lines on word boundaries so table columns stay narrow."""
    wrapped: list[str] = []
    for paragraph in (text or "").split("\n"):
        if not paragraph:
            wrapped.append("")
            continue
        current: list[str] = []
        current_len = 0
        for raw_word in paragraph.split():
            for word in _chunks(raw_word, width):
                extra = len(word) + (1 if current else 0)
                if current and current_len + extra > width:
                    wrapped.append(" ".join(current))
                    current = [word]
                    current_len = len(word)
                else:
                    current.append(word)
                    current_len += extra
        if current:
            wrapped.append(" ".join(current))
    return "\n".join(wrapped)


def _chunks(word: str, width: int) -> list[str]:
    if len(word) <= width:
        return [word]
    return [word[i : i + width] for i in range(0, len(word), width)]


def table_cell(text: str, limit: int | None = EXCERPT_CHARS) -> str:
    body = html_escape(wrap_lines(excerpt(text, limit))).replace("\n", "<br>")
    return f'<td valign="top" width="33%">{body}</td>'


def sample_input(item: dict, row: dict) -> tuple[str, str]:
    """Return (kind, text). kind is rewrite or draft."""
    source = raw_text(item)
    if source:
        return "rewrite", source
    return "draft", item.get("prompt") or row.get("prompt") or ""


def examples_group_table(
    samples: list[tuple[str, str]],
    dataset: dict[str, dict],
    results: dict[str, dict],
    first_header: str,
) -> str:
    lines = [
        "<table>",
        "<thead>",
        "<tr>",
        f'<th width="33%">{html_escape(first_header)}</th>',
        '<th width="33%">Baseline (no skill)</th>',
        '<th width="33%">Skill-based</th>',
        "</tr>",
        "</thead>",
        "<tbody>",
    ]
    for item_id, label in samples:
        row = results.get(item_id)
        if not row:
            continue
        item = dataset.get(item_id) or {}
        title = sample_title(item_id, item)
        judgment = row.get("judgment") or {}
        _kind, source = sample_input(item, row)
        lines.extend(
            [
                "<tr>",
                '<td colspan="3">',
                f"<strong>{html_escape(label)}</strong>, task {item_id}, ",
                f"<code>{html_escape(title)}</code>. ",
                f"The skill won {judgment.get('skill_criteria_wins')} rules, "
                f"the baseline won {judgment.get('baseline_criteria_wins')}, "
                f"and {judgment.get('criteria_ties')} were ties.",
                "</td>",
                "</tr>",
                "<tr>",
                table_cell(source),
                table_cell(row.get("baseline") or ""),
                table_cell(row.get("with_skill") or ""),
                "</tr>",
            ]
        )
    lines.extend(["</tbody>", "</table>"])
    return "\n".join(lines)


def examples_tables(dataset: dict[str, dict], results: dict[str, dict]) -> str:
    rewrite = []
    draft = []
    for item_id, label in SAMPLES:
        if item_id not in results:
            continue
        item = dataset.get(item_id) or {}
        kind, _text = sample_input(item, results[item_id])
        if kind == "rewrite":
            rewrite.append((item_id, label))
        else:
            draft.append((item_id, label))
    parts = []
    if rewrite:
        parts.extend(
            [
                "### Rewrite tasks",
                "",
                "These start from existing text. The first column is that original writing.",
                "",
                examples_group_table(rewrite, dataset, results, "Original writing"),
                "",
            ]
        )
    if draft:
        parts.extend(
            [
                "### Write-from-scratch tasks",
                "",
                "These start from a prompt. There is no original writing, so the first",
                "column is the prompt.",
                "",
                examples_group_table(draft, dataset, results, "Prompt"),
                "",
            ]
        )
    return "\n".join(parts).rstrip()


def main() -> None:
    dataset = load_dataset()
    results = load_results()
    rows = [results[i] for i in dataset if i in results]
    overall = attach_models(summarize(rows), RESULT_DIRS) if rows else None

    parts = [
        "# Plain-writing evals",
        "",
        "These evals ask whether giving `SKILL.md` to a writer produces text that",
        "follows the plain-writing rules better than a writer that does not see",
        "the skill.",
        "",
        "## Eval procedure",
        "",
        "### Dataset",
        "",
        f"`dataset.jsonl` has {len(dataset)} writing tasks.",
        "",
        "- `01`–`40`: short prompts, public-domain excerpts, and LLM slop.",
        "- `41`–`50`: long research and support-agent histories.",
        "- `51`–`65`: Claude Fable 5 coding-agent traces. The writer sees the",
        "  full trace and is asked to rewrite the longest wrap-up.",
        "- `66`–`67`: chat context and short-list checks.",
        "",
        "For a history task, we load a conversation from `sources/` and append",
        "the prompt as the last user turn. Fable traces are rebuilt with",
        "`uv run python build_fable_histories.py`.",
        "",
        "### Baseline",
        "",
        "The same user messages are sent to the writer with a short system prompt:",
        "write a clear, complete response, and return only the requested writing.",
        "The writer does not see `SKILL.md`.",
        "",
        "### Skill condition",
        "",
        "The same user messages are sent again, to the same model, with `SKILL.md`",
        "in the system prompt. The writer is told to follow those rules. It does",
        "not see the baseline output.",
        "",
        "### How it is judged",
        "",
        "For each writing task, we compare the two texts on every rule in",
        "`SKILL.md`. The judge does not know which text used the skill. The skill",
        "wins that task if it wins more rules. We also add up those rule wins",
        "across tasks.",
        "",
        "The default rewriter and judge are `gpt-5.5`. Override them with",
        "`--model` and `--judge-model`.",
        "",
        "## How to run",
        "",
        "```",
        "cd evals",
        "uv sync",
        "uv run python run_eval.py --out outputs/all",
        "uv run python run_eval.py --category fable_coding --out outputs/fable_coding",
        "uv run python run_eval.py --ids 66,67 --out outputs/new_rules",
        "uv run python write_readme.py",
        "```",
        "",
        "Put `OPENAI_API_KEY` in a `.env` file at the repo root. Outputs land in",
        "`outputs/` and are gitignored. `write_readme.py` combines the result",
        "files from those folders and writes this README.",
        "",
    ]

    if overall:
        missing = [i for i in dataset if i not in results]
        parts.extend(
            [
                "## Latest results",
                "",
                f"Combined from `{len(results)}` of `{len(dataset)}` writing tasks.",
                "",
                summary_table(overall),
                "",
                "### Rules with the largest gap",
                "",
                criterion_rows(overall),
                "",
            ]
        )
        if missing:
            parts.extend(
                [
                    f"Missing task results: {', '.join(missing)}.",
                    "",
                ]
            )
        if any(item_id in results for item_id, _label in SAMPLES):
            parts.extend(
                [
                    "## Examples",
                    "",
                    "Some tasks rewrite existing text. Some tasks write from scratch.",
                    "The first column is original writing for a rewrite, and the prompt",
                    "for a write-from-scratch task. Long texts are cut after about",
                    f"{EXCERPT_CHARS} characters.",
                    "",
                    examples_tables(dataset, results),
                    "",
                ]
            )
    else:
        parts.extend(
            [
                "## Latest results",
                "",
                "No task outputs yet. Run the commands in How to run, then",
                "`uv run python write_readme.py`.",
                "",
            ]
        )

    README.write_text("\n".join(parts).rstrip() + "\n")
    print(f"Wrote {README} from {len(results)} item results")


if __name__ == "__main__":
    main()
