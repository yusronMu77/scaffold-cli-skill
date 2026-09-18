# Setup and staying in sync

Install `scaffold-cli`, point it at a `scaffolding-code` tree, and keep an installed copy of this
skill up to date. This is referenced from the main `SKILL.md`'s prerequisite check — an
already-set-up project skips straight past this file to discovery/generate.

## Check it's installed

First work out the scope from where the skill folder (the one containing `SKILL.md`) lives: if
its path resolves under your home directory's global skills folder (e.g.
`~/.claude/skills/scaffold-cli/`), this is a **global** install. If it resolves inside a specific
project instead (`<project-root>/.claude/skills/scaffold-cli/`), this is a **project-scoped**
install for that project. If you genuinely can't tell, default to project-scoped — it's the more
contained choice.

Many shells reset environment variables and PATH between commands but keep the working directory,
so exporting PATH once and expecting it to still apply on the next command doesn't work — invoke
the binary by a path that's still valid on its own instead.

On Windows specifically, a Bash tool and a PowerShell/pwsh tool available in the same agent session
don't necessarily share one PATH — a binary that resolves in one can come back "command not found"
in the other, even for something already installed (e.g. `git`), not just something this skill just
installed. If a command here fails in whichever shell tool you tried first, retry it in the other
before assuming the install itself failed or burning further attempts in the failing one.

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
`SCAFFOLD_CLI_VERSION=v0.7.0` (env) / `-Version v0.7.0` (PowerShell) if the task needs a specific
release. Anything else (a manual archive from the
[Releases page](https://github.com/yusronMu77/scaffold-cli/releases), or building from source with
`go build -o scaffold .` inside a clone of the repo) only if the install scripts aren't usable in
the environment.

## Make sure scaffold-templates is reachable

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
clone it next to the `scaffold-cli` binary from the install step above instead — same
disposable/re-fetchable reasoning as the binary itself, and one `.gitignore` entry (`.tools/`)
covers both:

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

## Staying in sync

This document can drift from what the installed `scaffold-cli` actually does. Check first:
`scaffold --version` against the "Verified against" line at the top of `SKILL.md`. If it differs,
don't trust an exact flag or output shape here over reality — run `scaffold --help`,
`scaffold create --help`, `scaffold list --help`, and `scaffold lint --help` and prefer their live
output. The engine's own flags (`--dry-run`/`--print`/`--explain`/`--output`/`--scaffolding-code`/
etc.) change rarely, but a mismatch is a reason to check, not to assume.

### Updating an installed copy

This repo has no release process of its own — `main` is always current, and updating means
fast-forwarding the installed folder to it:

1. Locate the installed copy — the same global-vs-project-scoped resolution as the install step
   above (e.g. `~/.claude/skills/scaffold-cli` or `<project>/.claude/skills/scaffold-cli`).
   Confirm it's really this skill: `git -C <skill-dir> remote get-url origin` should be
   `https://github.com/yusronMu77/scaffold-cli-skill(.git)`.
2. Refuse to touch it if it has local changes — `git -C <skill-dir> status --porcelain`. A modified
   installed copy is likely an intentional local override; stop and ask rather than overwriting it.
3. Record the current "Verified against" line and `git -C <skill-dir> rev-parse HEAD`, then:
   ```bash
   git -C <skill-dir> fetch origin
   git -C <skill-dir> merge --ff-only origin/main
   ```
   `--ff-only` fails loudly instead of creating a merge commit if the installed copy has diverged —
   don't force-resolve that; stop and tell the user instead.
4. Report what changed: `git -C <skill-dir> log <old-sha>..HEAD --oneline`, and the new "Verified
   against" line. If the pulled version now names a newer `scaffold-cli` than what's actually
   installed, point back at the install step above (the install script) to update the *binary*
   too — this only updates the skill's own files.

If you're maintaining this skill (not just using it) and `scaffold-cli`'s actual CLI surface has
drifted from what's documented in `SKILL.md`, edit that file directly, bump the "Verified against"
line, and open a PR — an update per the steps above is what carries the change to every install.
