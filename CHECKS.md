# Programmatic checks

The checker gives each rule a stable identifier and reports its source
location. Each report includes the matching text.

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
| PW014 | Colon |
| PW015 | Empty sentence openers |
| PW016 | Markdown headings written in title case |
| PW017 | Standalone decorative bold lines |
| PW018 | Consecutive rhetorical questions |
| PW019 | Three consecutive short sentences |
| PW020 | A sentence with three or more coordinated clauses |
| PW021 | Markdown bullet or numbered list |
| PW022 | Three or more items written as an inline list |
| PW023 | Example introduced with "for instance" or "such as" |

The checker ignores code because its spelling often has to remain exact. It also
ignores URLs.

## Checks that still require the skill

A deterministic checker cannot reliably decide whether the intended reader will
understand a technical term. It cannot tell whether an explanation supplies the
context that reader needs. Human judgment is also required to identify invented
labels and implicit metaphors. Sentence relationships require the same judgment.

The hook therefore catches mechanical problems and sends exact findings back to
the agent. The skill remains responsible for whether the prose conveys its exact
meaning in a form the intended reader can follow.

Some checks use narrow structural clues. PW012 finds an explicit "is like"
comparison but cannot find every analogy. PW019 counts words in consecutive
sentences. PW020 counts coordinated clauses. Review a report when the matched
sentence structure is intentional.
