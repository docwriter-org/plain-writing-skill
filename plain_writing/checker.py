"""Find plain-writing rule violations without calling a language model."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Iterable, Iterator, Pattern


@dataclass(frozen=True)
class Violation:
    rule: str
    message: str
    line: int
    column: int
    excerpt: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PatternRule:
    rule: str
    message: str
    pattern: Pattern[str]


def _rule(rule: str, message: str, pattern: str) -> PatternRule:
    return PatternRule(rule, message, re.compile(pattern, re.IGNORECASE | re.MULTILINE))


PATTERN_RULES = (
    _rule("PW001", "Replace the em dash with a period, comma, or connective word.", "—"),
    _rule("PW002", "Write the range or connection without an en dash.", "–"),
    _rule("PW003", "Replace the middle dot with a word, comma, or separate line.", "·"),
    _rule("PW004", "Use straight quotation marks.", "[“”‘’]"),
    _rule(
        "PW005",
        "Remove this banned or empty-emphasis word.",
        r"\b(?:delve|tapestry|robust|leverage|really|pivotal|renowned|quietly|boasts)\b"
        r"|\breach(?:es|ed|ing)? for\b|\bcarr(?:y|ies|ied|ying) weight\b"
        r"|\ba testament to\b",
    ),
    _rule(
        "PW006",
        "Remove the filler phrase and state the useful information directly.",
        r"\b(?:it is|it's) worth noting that\b|\bto be clear\b"
        r"|\bat the end of the day\b|\bneedless to say\b"
        r"|\bin today['’]s (?:world|landscape)\b|\bin a world where\b",
    ),
    _rule(
        "PW007",
        "State what the subject is without the negative parallel construction.",
        r"\b(?:it|this|that)\s+(?:is|'s)\s+not\s+(?:just|only|merely)\b"
        r"|\bnot\s+(?:just|only|merely)\b[^.!?\n]{0,120}\bbut\b",
    ),
    _rule(
        "PW008",
        "Name the source for the claim or remove the attribution.",
        r"\b(?:experts say|studies show|research (?:shows|suggests)|"
        r"it is widely (?:believed|accepted)|many believe)\b",
    ),
    _rule(
        "PW009",
        "Name the idea instead of opening a sentence with a demonstrative pronoun.",
        r"(?:(?<=^)|(?<=[.!?]\s))(?:This|That|These|Those)\b",
    ),
    _rule(
        "PW010",
        "Name the specific result, outcome, or point.",
        r"(?:(?<=^)|(?<=[.!?]\s))The (?:result|outcome|point)\b",
    ),
    _rule(
        "PW011",
        "Start with the first point instead of announcing a count.",
        r"(?:(?<=^)|(?<=[.!?]\s))(?:A few|Several|Two|Three|Four|\d+)"
        r"\s+(?:things|points|notes|reasons|ideas|cautions|considerations)\b",
    ),
    _rule(
        "PW012",
        "Describe the subject literally instead of using an analogy.",
        r"\b(?:is|are|was|were)\s+like\s+(?:a|an|the)\b|\bas if\b",
    ),
    _rule(
        "PW013",
        "State the full point directly instead of opening with a dramatic pivot.",
        r"(?:(?<=[.!?]\s)|(?<=^))(?:But|Yet|However),?\s",
    ),
    _rule(
        "PW014",
        "Replace the colon with a period and explain the relationship directly.",
        r":",
    ),
    _rule(
        "PW015",
        "Remove the vague opening and name the subject.",
        r"(?:(?<=^)|(?<=[.!?]\s))(?:Clearly|Obviously|Importantly|Interestingly),?\s",
    ),
    _rule(
        "PW021",
        "Replace the formatted list with connected paragraphs.",
        r"^\s*(?:[-+*]|\d+[.)])\s+",
    ),
    _rule(
        "PW022",
        "Replace the inline list with sentences that explain each relationship.",
        r"\b[A-Za-z][\w'-]*(?:\s+[A-Za-z][\w'-]*){0,3},\s+"
        r"[A-Za-z][\w'-]*(?:\s+[A-Za-z][\w'-]*){0,3},\s+"
        r"(?:and|or)\s+[A-Za-z][\w'-]*(?:\s+[A-Za-z][\w'-]*){0,3}\b",
    ),
    _rule(
        "PW023",
        'Introduce the example with "For example," or "e.g.,".',
        r"\b(?:for instance|such as)\b",
    ),
    _rule(
        "PW024",
        "Name the subject instead of referring back to it vaguely.",
        r"\b(?:both|these|those|such)\s+"
        r"(?:patterns|approaches|methods|ideas|things|cases)\b",
    ),
)


def _mask_ignored_text(text: str) -> str:
    """Mask code and URLs while preserving offsets and line breaks."""

    masked = list(text)
    patterns = (
        re.compile(r"```.*?```", re.DOTALL),
        re.compile(r"~~~.*?~~~", re.DOTALL),
        re.compile(r"`[^`\n]+`"),
        re.compile(r"https?://[^\s)>]+"),
    )
    for pattern in patterns:
        current = "".join(masked)
        for match in pattern.finditer(current):
            for index in range(match.start(), match.end()):
                if masked[index] != "\n":
                    masked[index] = " "
    return "".join(masked)


def _location(text: str, offset: int) -> tuple[int, int, str]:
    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset) + 1
    line_end = text.find("\n", offset)
    if line_end == -1:
        line_end = len(text)
    return line, offset - line_start + 1, text[line_start:line_end].strip()


def _pattern_violations(text: str, masked: str) -> Iterator[Violation]:
    for item in PATTERN_RULES:
        for match in item.pattern.finditer(masked):
            line, column, excerpt = _location(text, match.start())
            yield Violation(item.rule, item.message, line, column, excerpt)


def _heading_violations(text: str, masked: str) -> Iterator[Violation]:
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
    word_pattern = re.compile(r"[A-Za-z][A-Za-z']*")
    for match in heading_pattern.finditer(masked):
        words = word_pattern.findall(match.group(2))
        cased = [word for word in words if len(word) > 1 and not word.isupper()]
        title_cased = [word for word in cased if word[0].isupper()]
        if len(cased) >= 3 and len(title_cased) / len(cased) >= 0.75:
            line, column, excerpt = _location(text, match.start(2))
            yield Violation(
                "PW016",
                "Use sentence case in the heading.",
                line,
                column,
                excerpt,
            )


def _bold_heading_violations(text: str, masked: str) -> Iterator[Violation]:
    pattern = re.compile(r"^\s*\*\*[^*\n]+\*\*\s*:?\s*$", re.MULTILINE)
    for match in pattern.finditer(masked):
        line, column, excerpt = _location(text, match.start())
        yield Violation(
            "PW017",
            "Use a plain heading instead of a decorative bold line.",
            line,
            column,
            excerpt,
        )


def _sentence_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for match in re.finditer(r"(?:^|(?<=[.!?])\s+)([^.!?\n]+[.!?])", text):
        sentence = match.group(1).strip()
        start = match.start(1) + len(match.group(1)) - len(match.group(1).lstrip())
        spans.append((start, match.end(1), sentence))
    return spans


def _rhetorical_question_violations(text: str, masked: str) -> Iterator[Violation]:
    spans = _sentence_spans(masked)
    for first, second in zip(spans, spans[1:]):
        if first[2].endswith("?") and second[2].endswith("?"):
            line, column, excerpt = _location(text, first[0])
            yield Violation(
                "PW018",
                "Replace stacked rhetorical questions with a direct statement.",
                line,
                column,
                excerpt,
            )


def _short_sentence_violations(text: str, masked: str) -> Iterator[Violation]:
    spans = _sentence_spans(masked)
    word_pattern = re.compile(r"\b[\w']+\b")
    for index in range(len(spans) - 2):
        group = spans[index : index + 3]
        if "\n\n" in masked[group[0][0] : group[-1][1]]:
            continue
        lengths = [len(word_pattern.findall(sentence)) for _, _, sentence in group]
        if all(length <= 6 for length in lengths):
            line, column, excerpt = _location(text, group[0][0])
            yield Violation(
                "PW019",
                "Join related short sentences or explain the relationship between them.",
                line,
                column,
                excerpt,
            )


def _clause_violations(text: str, masked: str) -> Iterator[Violation]:
    signal = re.compile(r",\s+(?:and|but|or|so|because|while|although)\b", re.IGNORECASE)
    for start, _, sentence in _sentence_spans(masked):
        if len(signal.findall(sentence)) >= 2:
            line, column, excerpt = _location(text, start)
            yield Violation(
                "PW020",
                "Split the sentence because it contains three or more clauses.",
                line,
                column,
                excerpt,
            )


def check_text(text: str) -> list[Violation]:
    """Return stable, source-ordered violations for authored prose."""

    masked = _mask_ignored_text(text)
    checks: Iterable[Iterable[Violation]] = (
        _pattern_violations(text, masked),
        _heading_violations(text, masked),
        _bold_heading_violations(text, masked),
        _rhetorical_question_violations(text, masked),
        _short_sentence_violations(text, masked),
        _clause_violations(text, masked),
    )
    violations = [violation for results in checks for violation in results]
    unique: list[Violation] = []
    seen: set[tuple[str, int, str]] = set()
    for item in violations:
        key = (item.rule, item.line, item.excerpt)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return sorted(unique, key=lambda item: (item.line, item.column, item.rule))
