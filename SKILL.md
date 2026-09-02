---
name: scaffold-cli
description: Use scaffold-cli to browse and generate standardized projects (Spring Boot services/libs/parent-POMs today, more scaffolds later) from the scaffold-templates repo. Use whenever asked to scaffold, generate, or bootstrap a new service/library/project from these templates, or to add a route/insert into a file scaffold-cli already generated.
---

# scaffold-cli

`scaffold-cli` is a dependency-free Go binary that renders projects from a separate templates
repo, [scaffold-templates](https://github.com/yusronMu77/scaffold-templates). Nothing is
hardcoded in the binary — which scaffolds/versions/dimensions/templates/variables exist, and even
the CLI flag names for them, all come from `jig.yaml` files inside scaffold-templates. Treat the
binary as a deterministic renderer and scaffold-templates as the source of truth for what it can
produce; don't hand-write what `create` can generate instead.

## 1. Check it's installed

```bash
scaffold --version
```

If that fails, install a prebuilt release binary rather than building from source:

```bash
# Linux / macOS
curl -fsSL https://raw.githubusercontent.com/yusronMu77/scaffold-cli/main/install.sh | sh
```

```powershell
# Windows
irm https://raw.githubusercontent.com/yusronMu77/scaffold-cli/main/install.ps1 | iex
```

Both scripts fetch the right binary for the platform, verify its checksum, and put it on PATH.
Pin a version with `SCAFFOLD_CLI_VERSION=v0.3.0` (env) / `-Version v0.3.0` (PowerShell) if the
task needs a specific release. Anything else (a manual archive from the
[Releases page](https://github.com/yusronMu77/scaffold-cli/releases), or building from source with
`go build -o scaffold .` inside a clone of the repo) only if the install scripts aren't usable in
the environment.

## 2. Make sure scaffold-templates is reachable

`scaffold` needs a checkout of scaffold-templates to read from. Resolution order (first match
wins): `--scaffolding-code=<path>` flag → `SCAFFOLD_CODE` env var → `.scaffold.yaml` in the cwd →
`.scaffold.yaml` in `$HOME` → a `scaffolding-code` folder next to the binary → `./scaffolding-code`
as a last resort. If none resolve, clone it:

```bash
git clone https://github.com/yusronMu77/scaffold-templates.git scaffolding-code
```

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

## Reference

- Full command reference: [scaffold-cli README](https://github.com/yusronMu77/scaffold-cli#readme)
- Template authoring contract (`jig.yaml`, the precedence rule, reserved names): [scaffold-templates README](https://github.com/yusronMu77/scaffold-templates#readme)
