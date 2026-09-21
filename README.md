# scaffold-cli-skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An [Agent Skill](https://www.anthropic.com/news/skills) that teaches an AI coding agent how to use
[scaffold-cli](https://github.com/yusronMu77/scaffold-cli) — discover what it can generate, preview
before writing, and run `scaffold create` with the right flags — instead of the agent hand-writing
boilerplate that scaffold-cli already generates deterministically.

The skill itself is [SKILL.md](SKILL.md).

## Install

Clone this repo into your agent's skills folder, naming the folder to match `name: scaffold-cli`
in `SKILL.md`'s frontmatter:

```bash
git clone https://github.com/yusronMu77/scaffold-cli-skill.git .claude/skills/scaffold-cli
```

That makes it available to one project. For every project on the machine instead, clone into your
agent's global skills folder the same way, e.g. `~/.claude/skills/scaffold-cli`.

There's no separate release to track — `main` is always current. To update later, `git pull`
inside the cloned folder, or point your agent at
[Updating an installed copy](references/setup.md#updating-an-installed-copy) to do that for you and
report what changed (see [Staying in sync](references/setup.md#staying-in-sync) for what else can
go stale).

## Use it

You don't invoke this skill directly — your agent reads `SKILL.md`'s frontmatter `description`
and loads the full file itself whenever a task matches: scaffolding/generating a new
service/library/project from `scaffold-templates`, or inserting into a file `scaffold-cli` already
generated. `SKILL.md` itself only covers the common per-task path, so an already-set-up project
doesn't load dead weight on every invocation:

1. Checking prerequisites (`scaffold --version`; full install/setup only on demand, from
   `references/setup.md`)
2. Discovering what's available (`scaffold list`)
3. Previewing before writing (`--dry-run` / `--print` / `--explain`)
4. Generating (`scaffold create`)

Two things are pushed into reference files, loaded only when actually needed:

- `references/setup.md` — installing `scaffold-cli`, resolving `scaffold-templates`, and staying in
  sync with a newer release
- `references/learning-templates.md` — growing templates deliberately (`scaffold lint [--build]`)
  and learning a template from an existing example (`scaffold learn` / `learn-review` /
  `learn-promote`; `scaffold learn-fields` for a Java entity's fields, no model call needed)

To confirm it's wired up, just ask the agent to scaffold something (e.g. "generate a new Spring
Boot service") and check that it reaches for `scaffold list`/`scaffold create` instead of writing
boilerplate by hand. The full instructions the agent follows are in [SKILL.md](SKILL.md).

## Benchmarking

[`benchmarks/`](benchmarks/) has the reproducible methodology and scripts for measuring this
skill's token/time/tool-call cost against a hand-written baseline (grading, sandboxing, power
calculation, bootstrap CI) — see issue [#30](https://github.com/yusronMu77/scaffold-cli-skill/issues/30)
for the history of re-benchmarks that led to formalizing it.

## Related

- [scaffold-cli](https://github.com/yusronMu77/scaffold-cli) — the engine this skill drives.
- [scaffold-templates](https://github.com/yusronMu77/scaffold-templates) — the scaffolds/templates
  scaffold-cli reads from.

## License

Distributed under the [MIT License](LICENSE).
