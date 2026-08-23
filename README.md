# Plain writing skill

This skill makes an AI agent write in a plain style. The full rules are in
`skills/plain-writing/SKILL.md`.

The rules are plain text, so any agent can use them.

The skill also checks its own writing and removes anything that does not add
something.

## What is in here

- `skills/plain-writing/SKILL.md`: the skill, with the rules, deslopify, and review.
- `skills/plain-writing/agents/`: reviewer instructions for the review command.
- `skills/plain-writing/scripts/`: builds the four reviewer prompts from the rules.
- `skills/plain-writing/hooks/`: optional stop hooks that start one review pass.
- `evals/`: optional. Only needed if you want to measure the skill.

## How to use it

`skills/plain-writing/SKILL.md` is a plain markdown file with the rules. Any
agent that can read a file can follow it. The simplest way is to give that
file to the agent as instructions, in a rules file or the system prompt.

The skill lives under `skills/` so `gh skill install` can find it:

```
gh skill install docwriter-org/plain-writing-skill plain-writing
```

Some tools have a set place for skills:

- Claude Code reads skills from `~/.claude/skills`. Copy the whole
  `skills/plain-writing` folder so the review command can find the
  reviewer file and scripts. You do not need the evals.

- Other agents, e.g., Codex or pi, can use the rules too. Paste the rules from
  `skills/plain-writing/SKILL.md` into whatever instructions that agent reads.

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

## Review existing writing

Use this command when an agent already wrote something and you want
independent reviewers to check the rules, then have the same agent fix
what they flag. Triggering the skill while the agent writes is often not
enough.

```
/plain-writing review
```

You can also write `/plain-writing eval`. Put a file path or the text after
the command when you do not want to review the previous response.

The agent launches four subagents in the same turn, one for each rule
group. Each subagent judges only its rules. The main agent reads those
findings and rewrites the text.

If you want that loop to start on its own after a writing turn, copy
`skills/plain-writing/hooks/cursor-hooks.json` to `.cursor/hooks.json`, or
copy `skills/plain-writing/hooks/claude-hooks.json` into a Claude Code
plugin hooks file. Point the command at
`skills/plain-writing/hooks/review_followup.py`. The hook asks the agent
to run `/plain-writing review` once. Set `PLAIN_WRITING_REVIEW_HOOK=always`
if you want that follow-up after every completed turn.

## Evals

A skill install does not need the evals. If you want to run them, clone the
repo and see `evals/README.md`.
