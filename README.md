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
- `hooks/hooks.json` contains the Stop hook used by each supported agent.
- `.claude-plugin/plugin.json` packages the skill and hook as one Claude Code
  plugin.

## Run the checker with uvx

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run
the checker directly from this repository:

```sh
uvx --from git+https://github.com/docwriter-org/plain-writing-skill plain-writing-check README.md
```

You do not need to clone the repository or install the checker. `uvx` creates
the tool environment on the first run and reuses its cache on later runs.

The checker accepts standard input, files, and directories. Add `--format json`
for machine-readable output. It reports each rule, line, column, and matching
text, and it exits with status 1 when it finds a violation.

## Install the skill and hook in Claude Code

Install `uv`, then run these commands inside Claude Code:

```text
/plugin marketplace add docwriter-org/plain-writing-skill
/plugin install plain-writing@plain-writing
/reload-plugins
```

The plugin applies the skill when Claude writes prose. When Claude finishes a
response, the hook runs the checker through `uvx`.

The checker runs locally and does not send the response to another model. When
it finds a violation, Claude receives the rule identifiers and source text and
rewrites the whole response. The hook allows the second response without
another correction, so it cannot create a loop.

Run `/hooks` and open `Stop` to confirm that the plugin hook is active.

## Install the hook in Codex

Install `uv`. Copy `hooks/hooks.json` to `~/.codex/hooks.json`, or merge its
`Stop` entry with the hooks already in that file.

Start Codex and run `/hooks`. Review and trust the command before using it.
Codex records trust for the exact hook definition, so you must trust it again
after changing the command.

## Install the hook in Pi

Pi needs the `pi-hooks` adapter because its extension API does not read
Claude-style command hooks by itself. Install the adapter:

```sh
pi install npm:@hsingjui/pi-hooks
```

Install `uv`, then merge the `Stop` entry from `hooks/hooks.json` into the
`hooks` object in `~/.pi/agent/settings.json`. Run `/reload` in Pi after
changing the settings.

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

Install `uv`, then copy the `Stop` entry from `hooks/hooks.json` into the `hooks`
object in `~/.claude/settings.json`. Merge the entry with existing hooks instead
of replacing them. Start a new Claude Code session, then use `/hooks` to confirm
that the Stop hook is present.

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
