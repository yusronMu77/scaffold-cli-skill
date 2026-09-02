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
inside the cloned folder (see `SKILL.md`'s
[Staying in sync](SKILL.md#staying-in-sync) section for what else can go stale).

## Use it

You don't invoke this skill directly — your agent reads `SKILL.md`'s frontmatter `description`
and loads the full file itself whenever a task matches: scaffolding/generating a new
service/library/project from `scaffold-templates`, or inserting into a file `scaffold-cli` already
generated. Once loaded, it walks the agent through:

1. Checking/installing `scaffold-cli` itself
2. Resolving `scaffold-templates`
3. Discovering what's available (`scaffold list`)
4. Previewing before writing (`--dry-run` / `--print` / `--explain`)
5. Generating (`scaffold create`)

To confirm it's wired up, just ask the agent to scaffold something (e.g. "generate a new Spring
Boot service") and check that it reaches for `scaffold list`/`scaffold create` instead of writing
boilerplate by hand. The full instructions the agent follows are in [SKILL.md](SKILL.md).

## Related

- [scaffold-cli](https://github.com/yusronMu77/scaffold-cli) — the engine this skill drives.
- [scaffold-templates](https://github.com/yusronMu77/scaffold-templates) — the scaffolds/templates
  scaffold-cli reads from.

## License

Distributed under the [MIT License](LICENSE).
