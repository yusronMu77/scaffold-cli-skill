---
name: scaffold-cli
description: Use scaffold-cli to browse and generate standardized projects (Spring Boot services/libs/parent-POMs today, more scaffolds later) from the scaffold-templates repo. Use whenever asked to scaffold, generate, or bootstrap a new service/library/project from these templates, or to add a route/insert into a file scaffold-cli already generated.
---

# scaffold-cli

> Verified against `scaffold-cli` v0.2.0 (includes the anchor-based insert feature, #11). See
> [Staying in sync](#staying-in-sync) below if your installed version disagrees.

`scaffold-cli` is a dependency-free Go binary that renders projects from a separate templates
repo, [scaffold-templates](https://github.com/yusronMu77/scaffold-templates). Nothing is
hardcoded in the binary — which scaffolds/versions/dimensions/templates/variables exist, and even
the CLI flag names for them, all come from `jig.yaml` files inside scaffold-templates. Treat the
binary as a deterministic renderer and scaffold-templates as the source of truth for what it can
produce; don't hand-write what `create` can generate instead.

## 1. Check it's installed

First work out the scope from where *this file* lives: if its path resolves under your home
directory's global skills folder (e.g. `~/.claude/skills/scaffold-cli/SKILL.md`), this is a
**global** install. If it resolves inside a specific project instead
(`<project-root>/.claude/skills/scaffold-cli/SKILL.md`), this is a **project-scoped** install for
that project. If you genuinely can't tell, default to project-scoped — it's the more contained
choice.

Many shells reset environment variables and PATH between commands but keep the working directory,
so exporting PATH once and expecting it to still apply on the next command doesn't work — invoke
the binary by a path that's still valid on its own instead.

**Global:**

```bash
scaffold --version || curl -fsSL https://raw.githubusercontent.com/yusronMu77/scaffold-cli/main/install.sh | sh
```

```powershell
scaffold --version; if (-not $?) { irm https://raw.githubusercontent.com/yusronMu77/scaffold-cli/main/install.ps1 | iex }
```

**Project-scoped** — install into the project instead of system-wide, so it doesn't leak into
other projects (run from the project root):

```bash
test -x .tools/scaffold-cli/scaffold || (
  export SCAFFOLD_CLI_INSTALL_DIR="$PWD/.tools/scaffold-cli"
  curl -fsSL https://raw.githubusercontent.com/yusronMu77/scaffold-cli/main/install.sh | sh
)
```

```powershell
if (-not (Test-Path .tools\scaffold-cli\scaffold.exe)) {
  $env:SCAFFOLD_CLI_INSTALL_DIR = "$PWD\.tools\scaffold-cli"
  irm https://raw.githubusercontent.com/yusronMu77/scaffold-cli/main/install.ps1 | iex
}
```

Add `.tools/` to the project's `.gitignore` if it isn't already. (On Windows the install script
also permanently adds that folder to the user's PATH as a side effect — harmless, but it isn't
undone by deleting the folder later.)

**For the rest of this skill, `scaffold` means whichever binary you resolved above** — bare
`scaffold` for a global install, or `.tools/scaffold-cli/scaffold` (`.tools\scaffold-cli\scaffold.exe`
on Windows) for a project-scoped one. Substitute accordingly in every command below.

Both scripts fetch the right binary for the platform and verify its checksum; the global variant
also puts it on PATH (the project-scoped one deliberately doesn't — see above). Pin a version with
`SCAFFOLD_CLI_VERSION=v0.3.0` (env) / `-Version v0.3.0` (PowerShell) if the task needs a specific
release. Anything else (a manual archive from the
[Releases page](https://github.com/yusronMu77/scaffold-cli/releases), or building from source with
`go build -o scaffold .` inside a clone of the repo) only if the install scripts aren't usable in
the environment.

## 2. Make sure scaffold-templates is reachable

`scaffold` needs a checkout of `scaffold-templates` to read from. Where to put it follows the same
scope as step 1 — don't just clone it to some arbitrary path and hope the resolution order finds
it; pick one of these two deliberately:

**Project-scoped:** clone it *next to the `scaffold-cli` binary itself* — `.tools/scaffold-cli/scaffolding-code`,
sibling to `.tools/scaffold-cli/scaffold` from step 1 — not the project root. The engine already
looks in the executable's own directory for a `scaffolding-code` folder before falling back to the
current directory, so this resolves automatically regardless of where `scaffold` is invoked from,
with no flag/env var/config file needed. It also means one `.gitignore` entry (`.tools/`) covers
both the binary and the templates checkout:

```bash
git clone https://github.com/yusronMu77/scaffold-templates.git .tools/scaffold-cli/scaffolding-code
```

```powershell
git clone https://github.com/yusronMu77/scaffold-templates.git .tools\scaffold-cli\scaffolding-code
```

**Global:** don't re-clone it per project — clone one shared copy once, then point every future
invocation at it permanently with a config file. A file persists across shells; an exported env
var doesn't survive to the next command, so don't use `SCAFFOLD_CODE` for this. Write the
*absolute* path — `.scaffold.yaml` does not expand `~`:

```bash
git clone https://github.com/yusronMu77/scaffold-templates.git "$HOME/scaffold-templates"
printf 'scaffolding_code: %s/scaffold-templates\n' "$HOME" > "$HOME/.scaffold.yaml"
```

```powershell
git clone https://github.com/yusronMu77/scaffold-templates.git "$HOME\scaffold-templates"
"scaffolding_code: $HOME\scaffold-templates" | Out-File "$HOME\.scaffold.yaml" -Encoding utf8
```

Full resolution order, if you need to override either default for a single invocation:
`--scaffolding-code=<path>` flag → `SCAFFOLD_CODE` env var → `.scaffold.yaml` in the cwd →
`.scaffold.yaml` in `$HOME` → a `scaffolding-code` folder next to the binary → `./scaffolding-code`
as a last resort.

## 3. Discover before generating

Flags are fully dynamic — which ones are valid depends on the template selected, and an unknown
flag is a hard error, not a silent no-op. Always browse first instead of guessing flag names:

```bash
scaffold list                        # known scaffolds
scaffold list <scaffold>             # versions, templates, optional dimensions for it
scaffold list <scaffold> <template>  # full selector tree + every variable the template declares
```

## 4. Preview before writing anything

All three run the full resolution with nothing touching disk — use them before `create` whenever
the outcome isn't already obvious from `list`:

| Flag | Answers |
|---|---|
| `--dry-run` | Which files would be produced |
| `--print` | What is actually in them |
| `--explain` | Which level of the inheritance chain contributed each file (and what it overrode) |

```bash
scaffold create <scaffold> <template> <name> --dry-run [--flag=value ...]
```

## 5. Generate

```bash
scaffold create <scaffold> <template> <name> [--flag=value ...]
```

`<scaffold>`, `<template>`, and `<name>` may also come from a values file — the flag namespace
without the dashes (`--package=x` becomes `package: x`):

```bash
scaffold create -f values.yaml
scaffold create -f base.yaml -f prod.yaml --name=payment-canary   # -f repeats, later wins
```

A command-line flag always beats a values file. Prefer a values file over a long flag list once
there are more than two or three variables to set.

If the target template declares an anchor-based insert (`insert_after`/`insert_before` in a
`jig.yaml` `files:` entry), `create` also splices into an already-existing file instead of only
writing new ones — the output reports `Spliced into N existing file(s)`. This only works for
anchors the template author already declared; `scaffold-cli` has no way to discover an arbitrary
insertion point in a file it doesn't know about, so don't assume it can add a route to a file with
no such rule — say so instead of hand-editing the file to compensate.

## 6. Check health of a templates change

If asked to validate a scaffold-templates change (not just consume it):

```bash
scaffold lint [<scaffold>] [--build]
```

`--build` additionally runs each combination's own `verify:` command against a real scratch build
— slower, but the only way to confirm generated output actually compiles/tests, not just that
templates parse.

## Staying in sync

This document can drift from what the installed `scaffold-cli` actually does. Check first:
`scaffold --version` against the "Verified against" line at the top of this file. If it differs,
don't trust an exact flag or output shape here over reality — run `scaffold --help`,
`scaffold create --help`, `scaffold list --help`, and `scaffold lint --help` and prefer their live
output. The engine's own flags (`--dry-run`/`--print`/`--explain`/`--output`/`--scaffolding-code`/
etc.) change rarely, but a mismatch is a reason to check, not to assume.

If you're maintaining this skill (not just using it) and `scaffold-cli`'s actual CLI surface has
drifted from what's documented above, edit this file directly, bump the "Verified against" line,
and `git push` — `git pull` in an existing install picks it up, no release process needed.

## Reference

- Full command reference: [scaffold-cli README](https://github.com/yusronMu77/scaffold-cli#readme)
- Template authoring contract (`jig.yaml`, the precedence rule, reserved names): [scaffold-templates README](https://github.com/yusronMu77/scaffold-templates#readme)
