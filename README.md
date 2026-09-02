# scaffold-cli-skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An [Agent Skill](https://www.anthropic.com/news/skills) that teaches an AI coding agent how to use
[scaffold-cli](https://github.com/yusronMu77/scaffold-cli) — discover what it can generate, preview
before writing, and run `scaffold create` with the right flags — instead of the agent hand-writing
boilerplate that scaffold-cli already generates deterministically.

The skill itself is [SKILL.md](SKILL.md).

## Use it

Copy this skill into your agent's skills folder, keeping the directory name so `name:` in the
frontmatter matches the folder. Every tagged release publishes a `scaffold-cli-skill.zip` — the
`releases/latest/download/` link always resolves to the newest one:

```bash
mkdir -p .claude/skills/scaffold-cli
curl -fsSL https://github.com/yusronMu77/scaffold-cli-skill/releases/latest/download/scaffold-cli-skill.zip -o /tmp/scaffold-cli-skill.zip
unzip -o /tmp/scaffold-cli-skill.zip -d .claude/skills/scaffold-cli
```

```powershell
New-Item -ItemType Directory -Force .claude/skills/scaffold-cli | Out-Null
Invoke-WebRequest https://github.com/yusronMu77/scaffold-cli-skill/releases/latest/download/scaffold-cli-skill.zip -OutFile "$env:TEMP\scaffold-cli-skill.zip"
Expand-Archive "$env:TEMP\scaffold-cli-skill.zip" .claude/skills/scaffold-cli -Force
```

Or track `main` directly instead of a pinned release:

```bash
git clone https://github.com/yusronMu77/scaffold-cli-skill.git .claude/skills/scaffold-cli
```

## Related

- [scaffold-cli](https://github.com/yusronMu77/scaffold-cli) — the engine this skill drives.
- [scaffold-templates](https://github.com/yusronMu77/scaffold-templates) — the scaffolds/templates
  scaffold-cli reads from.

## License

Distributed under the [MIT License](LICENSE).
