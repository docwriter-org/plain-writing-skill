# Plain writing

This repository provides plain-writing rules, a command line checker, and
automatic response hooks.

The skill teaches an AI agent how to write and revise prose. The checker finds
mechanical rule violations without calling a model. Claude Code, Codex, and Pi
can run the same checker when an agent finishes a response.

## What is included

- `SKILL.md` contains the full writing rules and the manual deslopify command.
- `plain_writing/` contains the dependency free Python checker.
- `CHECKS.md` lists the rules that the checker can and cannot enforce.
- `hooks/hooks.json` contains the bundled Claude Code Stop hook.
- `hooks/portable-hooks.json` contains a Stop hook for an installed checker.
- `.claude-plugin/plugin.json` packages the skill and hook as one Claude Code
  plugin.

## Use the checker

The checker requires Python 3.9 or later and has no runtime dependencies. Install
it with one of these commands:

```sh
pipx install git+https://github.com/docwriter-org/plain-writing-skill
uv tool install git+https://github.com/docwriter-org/plain-writing-skill
```

Check text from standard input, a file, or a directory:

```sh
echo "Text to check" | plain-writing-check
plain-writing-check README.md
plain-writing-check docs/
plain-writing-check --format json README.md
```

The command reports each rule, line, column, and matching text. It exits with
status 1 when it finds a violation, so it can also run in tests or a Git
pre-commit hook.

## Install the skill and hook in Claude Code

Run these commands inside Claude Code:

```text
/plugin marketplace add docwriter-org/plain-writing-skill
/plugin install plain-writing@plain-writing
/reload-plugins
```

The plugin applies the skill when Claude writes prose. It also runs the hook
when Claude finishes a response.

The hook runs the bundled checker locally. It does not send the response to
another model. When the checker finds a violation, Claude receives the rule
identifiers and source text and rewrites the whole response. The hook allows the
second response without another correction, so it cannot create a loop.

Run `/hooks` and open `Stop` to confirm that the plugin hook is active.

## Install the hook in Codex

First install `plain-writing-check` with `pipx` or `uv` as shown above. Copy
`hooks/portable-hooks.json` to `~/.codex/hooks.json`, or merge its `Stop` entry
with the hooks already in that file.

Start Codex and run `/hooks`. Review and trust the command before using it.
Codex records trust for the exact hook definition, so you must trust it again
after changing the command.

## Install the hook in Pi

Pi needs the `pi-hooks` adapter because its extension API does not read
Claude-style command hooks by itself. Install the adapter:

```sh
pi install npm:@hsingjui/pi-hooks
```

First install `plain-writing-check` with `pipx` or `uv`. Then merge the `Stop`
entry from `hooks/portable-hooks.json` into the `hooks` object in
`~/.pi/agent/settings.json`. Run `/reload` in Pi after changing the settings.

The adapter runs the same command and gives Pi the same rewrite instruction when
the checker finds a violation.

## Install only the skill

Claude Code reads personal skills from `~/.claude/skills`. Clone this repository
into a folder named `plain-writing`:

```sh
git clone https://github.com/docwriter-org/plain-writing-skill ~/.claude/skills/plain-writing
```

Other agents, including Codex and Pi, can use the rules too. Give `SKILL.md` to
the agent as an instruction file or include its contents in the agent's system
instructions.

## Install only the Claude Code hook

Clone the repository, then copy the `Stop` entry from `hooks/hooks.json` into the
`hooks` object in `~/.claude/settings.json`. Replace
`${CLAUDE_PLUGIN_ROOT}` in the command with the absolute path to the cloned
repository. Merge the entry with existing hooks instead of replacing them.
Start a new Claude Code session, then use `/hooks` to confirm that the Stop hook
is present.

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
