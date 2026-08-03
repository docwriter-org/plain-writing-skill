# Plain writing skill

This skill makes an AI agent write in a plain style. The full rules are in
`SKILL.md`.

The rules are plain text, so any agent can use them.

The skill also checks its own writing and removes any clause or sentence that
adds nothing the reader needs.

## Where the rules come from

The skill adapts useful ideas from
[ASD-STE100 Simplified Technical English](https://en.wikipedia.org/wiki/Simplified_Technical_English).
It tells the agent to use simple words, keep one meaning for each word, use the
same term for the same thing, name the actor, and keep each sentence about one
topic.

The skill is not a full implementation of ASD-STE100. The standard uses a
controlled dictionary and strict grammar for technical maintenance documents.
This skill applies selected principles to technical and general prose, and it
keeps the user's preference for complete explanations.

## What is in here

- `SKILL.md`: the skill, with the rules and the revision steps.

## How to use it

`SKILL.md` is a plain markdown file with the rules. Any agent that can read a
file can follow it. The simplest way is to give `SKILL.md` to the agent as
instructions, in a rules file or the system prompt.

Some tools have a set place for skills:

- Claude Code reads skills from `~/.claude/skills`. Clone the repo into a folder
  named `plain-writing`:

```
git clone https://github.com/shreyashankar/plain-writing-skill ~/.claude/skills/plain-writing
```

- Other agents, e.g., Codex or pi, can use the rules too. Paste the rules from
  `SKILL.md` into whatever instructions that agent reads.

Then ask the agent to write or revise some text. It applies the rules on its
own.

## Deslopify an agent response

Use the command below when an agent response assumes too much context, uses
unexplained technical terms, or does not make the main point clear.

```
/plain-writing deslopify
```

The skill rewrites the agent's previous response in a clear structure for a
sharp CEO or technical reader who has no project context and needs to understand
all relevant details. The rewrite follows the plain-writing guidelines in the
skill.

You can also put text after the command when you want to rewrite text other than
the previous response.
