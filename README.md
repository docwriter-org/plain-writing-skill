# Plain writing skill

This repo is a plugin. Install it once, and the agent gets the writing
rules, the `/review` and `/deslopify` commands, and a hook that starts
`/plain-writing review` after a writing pass.

The full rules are in `skills/plain-writing/SKILL.md`.

## What is in here

- `plugin.json`: Agent Plugins manifest, for clients that load that standard.
- `.cursor-plugin/`: Cursor plugin and marketplace files.
- `.codex-plugin/` and `.agents/plugins/`: Codex plugin and marketplace files.
- `.claude-plugin/`: Claude Code plugin and marketplace files.
- `commands/`: `/review` and `/deslopify` command files.
- `skills/plain-writing/SKILL.md`: the rules, deslopify, and review.
- `skills/plain-writing/hooks/`: writing-pass hooks that ship with the plugin.
- `evals/`: optional. Only needed if you want to measure the skill.

## Add it as a plugin

### Claude Code

```
/plugin marketplace add docwriter-org/plain-writing-skill
/plugin install plain-writing@plain-writing
```

Then run `/reload-plugins` if the install summary asks for it. The
namespaced commands are `/plain-writing:review` and
`/plain-writing:deslopify`.

### Cursor

From the Cursor CLI:

```
cursor-agent plugin marketplace add https://github.com/docwriter-org/plain-writing-skill
```

Then start `cursor-agent`, run `/plugin`, and install `plain-writing`.
You can also import the same GitHub URL under Dashboard, Plugins, Team
Marketplaces, then install it for the project or for your user.

To try it on one machine without a marketplace:

```
ln -s /path/to/plain-writing-skill ~/.cursor/plugins/local/plain-writing
```

Then reload the Cursor window. The commands are `/review` and
`/deslopify`. After a writing pass, the hook asks the agent to run
review.

### Codex

```
codex plugin marketplace add docwriter-org/plain-writing-skill
codex plugin add plain-writing@plain-writing
```

Then run `/hooks` and trust the Stop hook. Codex loads the skill from
this plugin. The same writing-pass Stop hook asks the agent to run
`/plain-writing review`.

### Other agents

If the agent loads Agent Plugins, point it at this repo. If it only
loads skills:

```
gh skill install docwriter-org/plain-writing-skill plain-writing
```

You can also copy `skills/plain-writing` into that agent's skills
folder, or paste `SKILL.md` into its instructions. The hook runs when
the plugin is installed in Cursor, Codex, or Claude Code.

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

Put a file path or the text after the command when you do not want to
review the previous response.

The agent launches four subagents in the same turn, one for each rule
group. Each subagent judges only its rules. The main agent reads those
findings and rewrites the text.

This is not the same as the dataset evals in `evals/`. Those measure
whether the skill beats a baseline on saved writing tasks. `/plain-writing
review` judges one live draft.

## Review hooks

The plugin turns the hook on for you. After a writing pass, it asks the
agent to run `/plain-writing review`. A writing pass is a long prose
reply to a writing request, or a long prose reply with almost no code.
The hook stays quiet after coding work, short status replies, and the
review pass itself.

You do not need to copy hook files into each project. In Codex, run
`/hooks` once and trust the Stop hook.

## Evals

A skill install does not need the evals. If you want to run them, clone the
repo and see `evals/README.md`.
