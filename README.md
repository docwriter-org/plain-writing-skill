# Plain writing skill

This skill makes an agent write in a plain style: everyday words, complete
sentences, no dashes, and no jargon. The rules are in
`skills/plain-writing/SKILL.md`.

You can paste that file into any agent. If you install this repo as a
plugin, you also get two commands and a hook.

- `/plain-writing deslopify` rewrites a reply for a reader with no
  project context.
- `/plain-writing review` has four subagents check a draft against the
  rules, then the same agent fixes what they flag.
- After a long writing pass, the hook starts review on its own.

## Install

### Claude Code

```
/plugin marketplace add docwriter-org/plain-writing-skill
/plugin install plain-writing@plain-writing
```

Reload plugins if the install summary asks you to. The commands show up
as `/plain-writing:review` and `/plain-writing:deslopify`.

### Cursor

```
cursor-agent plugin marketplace add https://github.com/docwriter-org/plain-writing-skill
```

Then run `/plugin` and install `plain-writing`. You can also add that
GitHub URL as a team marketplace. The commands are `/review` and
`/deslopify`.

To try it on one machine without a marketplace:

```
ln -s /path/to/plain-writing-skill ~/.cursor/plugins/local/plain-writing
```

### Codex

```
codex plugin marketplace add docwriter-org/plain-writing-skill
codex plugin add plain-writing@plain-writing
```

Then run `/hooks` and trust the Stop hook.

### Pi

```
pi install git:github.com/docwriter-org/plain-writing-skill
```

### Other agents

If the agent loads Agent Plugins, point it at this repo. If it only
loads skills:

```
gh skill install docwriter-org/plain-writing-skill plain-writing
```

You can also copy `skills/plain-writing` into the agent's skills folder,
or paste `SKILL.md` into its instructions. The hook runs only when the
plugin is installed.

## Deslopify

Use this when a reply assumes too much context, uses unexplained terms,
or hides the main point.

```
/plain-writing deslopify
```

The skill rewrites the last agent reply for a sharp reader who has no
project context. Put text after the command if you want to rewrite
something else. It returns only the rewrite.

## Review

Use this when an agent already wrote something and you want a second
check before you keep it. Asking the skill to write plainly on the first
pass is often not enough.

```
/plain-writing review
```

It reviews the last agent reply. Put a file path or the text after the
command to review something else.

The agent launches four subagents in the same turn, one for each rule
group. Each subagent judges only its rules. The main agent reads those
findings and rewrites the text.

This is not the dataset evals in `evals/`. Those measure the skill on
saved writing tasks. `/plain-writing review` judges one live draft.

The hook starts this review after a writing pass: a long prose reply to
a writing request, or a long prose reply with almost no code. It stays
quiet after coding work, short status replies, and the review itself.

## Evals

You do not need the evals to use the skill. To run them, clone the repo
and see `evals/README.md`.
