# Plain writing

This repository provides the plain-writing rules in two forms.

The skill teaches an AI agent how to write and revise prose. The Claude Code
hook reviews every completed response and asks Claude to rewrite it when the
response has material style problems.

## What is included

- `SKILL.md` contains the full writing rules and the manual deslopify command.
- `hooks/hooks.json` contains the automatic Claude Code Stop hook.
- `.claude-plugin/plugin.json` packages the skill and hook as one Claude Code
  plugin.

## Install the skill and hook in Claude Code

Run these commands inside Claude Code:

```text
/plugin marketplace add docwriter-org/plain-writing-skill
/plugin install plain-writing@plain-writing
/reload-plugins
```

The plugin applies the skill when Claude writes prose. It also runs the hook
when Claude finishes a response.

The hook sends the completed response to a fast model for review. If the review
finds material problems, Claude receives a specific instruction to rewrite the
whole response. The hook allows the second response without another rewrite, so
it cannot keep Claude in a correction loop.

Run `/hooks` and open `Stop` to confirm that the plugin hook is active.

## Install only the skill

Claude Code reads personal skills from `~/.claude/skills`. Clone this repository
into a folder named `plain-writing`:

```sh
git clone https://github.com/docwriter-org/plain-writing-skill ~/.claude/skills/plain-writing
```

Other agents, including Codex and pi, can use the rules too. Give `SKILL.md` to
the agent as an instruction file or include its contents in the agent's system
instructions.

## Install only the hook

The hook format is specific to Claude Code. Copy the `Stop` entry from
`hooks/hooks.json` into the `hooks` object in `~/.claude/settings.json`. Merge it
with any existing hooks instead of replacing them. Restart Claude Code or run
`/reload-plugins`, then use `/hooks` to confirm that the Stop hook is present.

The hook uses an extra model request for every completed response. Install only
the skill if you do not want that automatic review.

Claude Code does not run the Stop hook when you interrupt a response or when an
API error ends the turn.

## Deslopify a response manually

Use the standalone skill command when a response assumes too much context, uses
unexplained technical terms, or hides the main point:

```text
/plain-writing deslopify
```

When the plugin is installed, the namespaced form is:

```text
/plain-writing:plain-writing deslopify
```

The skill rewrites the previous response for a sharp CEO or technical reader
who has no project context. You can put other text after the command when you
want to rewrite that text instead.
