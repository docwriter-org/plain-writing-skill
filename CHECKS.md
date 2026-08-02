# Programmatic checks

The checker reports rules with stable identifiers, source lines, columns, and
the text that caused each report.

| Rule | Check |
| --- | --- |
| PW001 | Em dash |
| PW002 | En dash |
| PW003 | Middle dot |
| PW004 | Curly quotation mark |
| PW005 | Banned AI words and empty emphasis |
| PW006 | Common filler phrases |
| PW007 | Negative parallel constructions |
| PW008 | Claims attributed to vague sources |
| PW009 | Sentences that open with a demonstrative pronoun |
| PW010 | Sentences that open with a vague summary noun |
| PW011 | Sentences that announce a count of points |
| PW012 | Explicit comparison using "is like" or "as if" |
| PW013 | Sentences that open with a dramatic pivot |
| PW014 | A colon followed by prose instead of a list |
| PW015 | Empty sentence openers |
| PW016 | Markdown headings written in title case |
| PW017 | Standalone decorative bold lines |
| PW018 | Consecutive rhetorical questions |
| PW019 | Three consecutive short sentences |
| PW020 | A sentence with three or more coordinated clauses |

The checker ignores fenced code, inline code, and URLs because their spelling
often has to remain exact.

## Checks that still require the skill

A deterministic checker cannot reliably decide whether the reader knows a
technical term, whether an explanation includes enough context, or whether a
word is an invented label. It also cannot find every metaphor, decide whether
an inanimate subject has an appropriate verb, or tell whether two clauses
belong in the same sentence.

The hook therefore catches mechanical problems and sends exact findings back to
the agent. The skill remains responsible for meaning, organization, precision,
and reader context.

Some checks use narrow structural clues. For example, PW012 finds an explicit
"is like" comparison but cannot find every analogy. PW019 counts words in
consecutive sentences, and PW020 counts coordinated clauses. Review those
reports when the sentence structure is intentional.
