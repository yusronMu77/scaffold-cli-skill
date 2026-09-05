---
name: scaffold-cli
description: Use scaffold-cli to browse and generate standardized projects (Spring Boot services/libs/parent-POMs today, more scaffolds later) from the scaffold-templates repo. Use whenever asked to scaffold, generate, or bootstrap a new service/library/project from these templates, or to add a route/insert into a file scaffold-cli already generated.
---

# scaffold-cli

> Verified against `scaffold-cli` v0.3.0 (includes the anchor-based insert feature, #11, and the
> `init` command, #15). See [Staying in sync](#staying-in-sync) below if your installed version
> disagrees.

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
  # install.ps1 unconditionally adds $env:SCAFFOLD_CLI_INSTALL_DIR to the user's PATH permanently -
  # undo that so a project-scoped install doesn't leak into the global environment.
  $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
  $kept = ($userPath -split ";" | Where-Object { $_ -and $_ -ne $env:SCAFFOLD_CLI_INSTALL_DIR }) -join ";"
  [Environment]::SetEnvironmentVariable("Path", $kept, "User")
}
```

Add `.tools/` to the project's `.gitignore` if it isn't already.

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

`scaffold` needs a `scaffolding-code` tree to read from — either the shared
[scaffold-templates](https://github.com/yusronMu77/scaffold-templates) library, or one the project
authors and owns itself. Which one depends on scope:

**Global install → the shared library, always.** Don't re-clone it per project — clone one shared
copy once, then point every future invocation at it permanently with a config file. A file
persists across shells; an exported env var doesn't survive to the next command, so don't use
`SCAFFOLD_CODE` for this. Write the *absolute* path — `.scaffold.yaml` does not expand `~`:

```bash
git clone https://github.com/yusronMu77/scaffold-templates.git "$HOME/scaffold-templates"
printf 'scaffolding_code: %s/scaffold-templates\n' "$HOME" > "$HOME/.scaffold.yaml"
```

```powershell
git clone https://github.com/yusronMu77/scaffold-templates.git "$HOME\scaffold-templates"
"scaffolding_code: $HOME\scaffold-templates" | Out-File "$HOME\.scaffold.yaml" -Encoding utf8
```

**Project-scoped install → default to the project owning its own templates**, not a read-only
clone of the shared library. A project's own conventions (its base POM tweaks, its house auth
middleware, its own file layout) naturally diverge from the generic shared templates as the
project matures, and a plain clone can't carry that divergence — the next `git pull` just
overwrites it. (Same reasoning Nx gives for "local generators" living in the workspace instead of
a consumed package.)

Bootstrap it with `scaffold init` (a pure local file write — no network calls, no `git init`)
rather than hand-authoring a root `jig.yaml` from scratch. This is project source, not disposable
tooling — commit it, don't put it under `.tools/` or `.gitignore` it:

```bash
scaffold init scaffolding-code
```

This writes a starter `jig.yaml` with an intentionally empty `values: []` — `scaffold list`/
`scaffold create` against it correctly refuse to do anything ("registers no scaffolds") until a
scaffold is actually registered. Edit it to add the project's first real one as templates are
needed; the starter file's own comments link to `scaffold-templates`' README for the format.
`scaffold init` refuses to clobber an existing `jig.yaml` unless `--force` is passed.

This resolves automatically (`./scaffolding-code` is the engine's last-resort default) as long as
`scaffold` runs from the project root; commit a `.scaffold.yaml` there too
(`scaffolding_code: ./scaffolding-code`) if it also needs to work from subdirectories.

If the project genuinely has no customization needs yet and just wants the shared library as-is,
clone it next to the `scaffold-cli` binary from step 1 instead — same disposable/re-fetchable
reasoning as the binary itself, and one `.gitignore` entry (`.tools/`) covers both:

```bash
git clone https://github.com/yusronMu77/scaffold-templates.git .tools/scaffold-cli/scaffolding-code
```

```powershell
git clone https://github.com/yusronMu77/scaffold-templates.git .tools\scaffold-cli\scaffolding-code
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

## 6. Grow and validate templates deliberately

Applies to a project-owned `scaffolding-code` (step 2) as much as to `scaffold-templates` itself —
growing it well is deliberate work, not passive drift:

- **Extract, don't anticipate.** Add or update a template when the same manual pattern has shown
  up for the second or third time in this project, not before a real repeat exists — a template
  for a hypothetical future need is speculative complexity with nothing yet to check it against.
- **Validate every change before considering it done**, the same way `scaffold-templates` does in
  its own CI:
  ```bash
  scaffold lint [<scaffold>] [--build]
  ```
  `--build` additionally runs each combination's own `verify:` command against a real scratch
  build — slower, but the only way to confirm generated output actually compiles/tests, not just
  that templates parse.
- **It's just a commit.** A project-owned `scaffolding-code` has no release process to go through
  (unlike the shared library) — a change ships the moment it's committed, and the very next
  `scaffold create` in this project already uses it.

## 7. Learn a template from an existing example

Requires whatever `scaffold-cli` release includes issue #17 — check `scaffold learn --help`
exists before relying on this section; if it doesn't, the installed version predates it.

Instead of hand-authoring a `jig.yaml` from scratch, point `learn` at one already-written example
(a real controller, a CDK stack, any single instance of a pattern the project repeats) and it
separates invariant structure from variable names/paths/fields — normally by calling an LLM once.

**You are already an LLM. Do the reasoning yourself and use `--draft`, not a provider call.**
`learn` also accepts an already-reasoned draft directly, skipping any provider/API key entirely:

```bash
scaffold learn <path-to-example> --output=<scratch-dir> --draft=- <<'JSON'
{"name": "...", "variables": [...], "files": [...]}
JSON
```

`--draft=-` reads the whole draft from stdin in one shot before `learn` does anything else, so the
JSON has to be attached to the same invocation (a heredoc as above, or an equivalent pipe) — running
the bare command first and trying to supply the JSON afterward doesn't work, since there's no
process left listening for it by then. Prefer writing the draft to a file and passing
`--draft=<path>` instead of `-` if the JSON is large or awkward to inline in a heredoc. Making
`learn` call Anthropic/OpenAI itself when you're the one invoking it would be a
second, separately-billed model call to do reasoning you can already do inline as part of this
session — prefer `--draft` every time you're the caller. Reserve the plain
`scaffold learn <path> --output=<dir>` form (which requires `ANTHROPIC_API_KEY` or
`OPENAI_API_KEY`, auto-detected, `--provider=anthropic|openai` to disambiguate) for when a human
runs it directly with no agent involved. `--draft` and `--provider`/`--model`/`--base-url` are
mutually exclusive — `learn` rejects combining them rather than silently ignoring one.

**The draft JSON schema** (`{}` = required unless noted):

```json
{
  "name": "kebab-case-template-name",
  "description": "One sentence describing what this template produces (optional)",
  "variables": [
    {"name": "ClassName", "prompt": "help text (optional)", "default": "Widget", "required": true}
  ],
  "computed": [
    {"name": "ClassNameKebab", "value": "{{ .ClassName | kebabcase }}"}
  ],
  "files": [
    {"path": "{{ .ClassName }}Controller.java", "content": "class {{ .ClassName }}Controller {}\n"},
    {"path": "gitignore.tpl", "content": "target/\n", "target": ".gitignore"}
  ]
}
```

`variables` and `files` are required (`computed` is not — omit it entirely unless some file `path`
needs a casing other than a variable's own canonical form; see below).

Rules for filling it in, same ones a provider call is instructed with:

- **One variable per concept**, named in its most natural canonical form as it appears in the
  example (e.g. a Java class name in PascalCase: `Order`). Every other casing of that same concept
  found in the example (kebab-case, camelCase, snake_case, UPPER_CASE, plural forms) is the *same*
  variable piped through a filter in file **content** — `kebabcase`, `camelcase`, `snakecase`,
  `upper`, `lower`, `title` are available (Sprig, already used everywhere else `scaffold-cli`
  renders). Never declare a second variable for a different casing of the same concept.
- **A file `path` may only use plain `{{ .Name }}`, never a piped filter** — Windows forbids `|` in
  filenames, so `{{ .Name | kebabcase }}` cannot appear in a path. If a path needs a casing other
  than a variable's own canonical form, declare a `computed` entry (`name` + a `value` template
  expression building on a variable) and reference it as plain `{{ .ComputedName }}` in the path.
  Piped filters are fine in file `content`, only paths forbid them.
- **A `computed` entry's `name` must be distinct from every variable name** — it's a separate
  identifier added alongside the variables, not a way to override one. A colliding name would
  silently shadow the variable's value during rendering, so `learn` rejects it outright.
- **Never name a variable `Name`, `Scaffold`, `Template` or `Data`.** Those four are reserved by
  the engine (they're the values-file keys), and a variable using one would make every later
  `scaffold create` fail. Use something specific: `EntityName`, `ClassName`, `ServiceName`.
  `learn` rejects these, so a draft that uses one fails at write time rather than at generation
  time.
- **`target` is only for a file whose real name would be acted on inside the templates repo
  itself.** `.gitignore` is the standard case: store it as `"path": "gitignore.tpl"` with
  `"target": ".gitignore"`, so git doesn't apply it to the templates repository. Same for
  `.dockerignore`. Every other file omits `target` entirely.
- **`jig.yaml` and `_*.tpl` are reserved as `path` values** — the first is the manifest the draft
  itself generates, the second holds shared template definitions that are never emitted as output.
  `learn` rejects both.
- `default` must be the literal value found in the example, so the draft, used unmodified,
  reproduces the example exactly.
- Every file that should be part of the template needs an entry; don't invent files that weren't
  in the example, don't omit files that should regenerate with the instance.

`--output` is required and must be a scratch location, never `scaffolding-code` directly — the
result is a **draft**, not yet a live template. It must also be empty (or not exist yet); pass
`--force` only when you deliberately mean to overwrite what's already there.

After it writes the draft, **review it like any other generated artifact before trusting it**:
read the draft `jig.yaml` and templated files, diff them against the original example, and check
for anything over-generalized (a value templated that should have stayed literal) or
under-generalized (a value left literal that should vary). Only once it looks right, move it into
the project's real `scaffolding-code` tree (or `scaffold-templates`) as a normal template addition,
same as if it had been hand-authored — `learn` does not wire it in for you. From that point on,
regenerating instances goes through the ordinary `create` path (step 5) with zero further AI calls.

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
