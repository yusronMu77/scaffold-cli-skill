# scaffold-cli-skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An [Agent Skill](https://www.anthropic.com/news/skills) that teaches an AI coding agent how to use
[scaffold-cli](https://github.com/yusronMu77/scaffold-cli) — discover what it can generate, preview
before writing, and run `scaffold create` with the right flags — instead of the agent hand-writing
boilerplate that scaffold-cli already generates deterministically.

The skill itself is [SKILL.md](SKILL.md).

## Use it

Copy this repo into your agent's skills folder, keeping the directory name so `name:` in the
frontmatter matches the folder:

```bash
git clone https://github.com/yusronMu77/scaffold-cli-skill.git .claude/skills/scaffold-cli
```

To pick up a later update, `git pull` inside that folder.

## Related

- [scaffold-cli](https://github.com/yusronMu77/scaffold-cli) — the engine this skill drives.
- [scaffold-templates](https://github.com/yusronMu77/scaffold-templates) — the scaffolds/templates
  scaffold-cli reads from.

## License

Distributed under the [MIT License](LICENSE).
