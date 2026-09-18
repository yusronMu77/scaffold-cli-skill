---
name: scaffold-cli
description: Use scaffold-cli to browse and generate standardized projects (Spring Boot services/libs/parent-POMs today, more scaffolds later) from the scaffold-templates repo. Use whenever asked to scaffold, generate, or bootstrap a new service/library/project from these templates, or to add a route/insert into a file scaffold-cli already generated. Skip if there's no existing scaffold to draw from and the request is to generate a whole new app or architecture from scratch — however it's phrased, a full PRD, a short brief, or a one-line prompt — write the first real instance by hand instead, then use the `learn` flow (see `references/learning-templates.md`) once a genuine repeat exists.
---

# scaffold-cli

> Verified against `scaffold-cli` v0.7.0 (includes the anchor-based insert feature, #11, the
> `init` command, #15, `flat_output` to skip the `<name>/` nesting, #53, `--skip-existing`
> deep-merging a template's `merge:`-registered files instead of skipping them outright, #80, the
> `learn-fields` command for pulling `data.entity.fields` straight from an existing Java class, #71,
> the full `scaffold learn` family — single/multi-example inference, the
> `learn-review`/`learn-promote` gate, match-before-learn with an uncertain-match band, `raw`
> (unrendered) draft files, hardened secret redaction, and 2-positional `create` for a leaf-version
> scaffold — and, new in v0.7.0, `create --print-written` to write and echo every file's exact
> final content in one call, plus `list <scaffold> --full` to expand every template's tree and
> variables in one response, both from #91). See
> [Staying in sync](references/setup.md#staying-in-sync) if your installed version disagrees.

`scaffold-cli` is a dependency-free Go binary that renders projects from a separate templates
repo, [scaffold-templates](https://github.com/yusronMu77/scaffold-templates). Nothing is
hardcoded in the binary — which scaffolds/versions/dimensions/templates/variables exist, and even
the CLI flag names for them, all come from `jig.yaml` files inside scaffold-templates. Treat the
binary as a deterministic renderer and scaffold-templates as the source of truth for what it can
produce; don't hand-write what `create` can generate instead.

## 1. Check prerequisites

```bash
scaffold --version
```

If that fails, or `scaffolding-code` isn't reachable yet, see `references/setup.md` for the full
global-vs-project-scoped install and `scaffolding-code` setup instructions — most invocations in an
already-set-up project skip straight past that file to discovery below.

## 2. Discover before generating

Flags are fully dynamic — which ones are valid depends on the template selected, and an unknown
flag is a hard error, not a silent no-op. Always browse first instead of guessing flag names:

```bash
scaffold list                        # known scaffolds
scaffold list <scaffold>             # versions, templates, optional dimensions for it
scaffold list <scaffold> --full      # same, plus every template's own tree and variables
scaffold list <scaffold> <template>  # full selector tree + every variable the template declares
```

`scaffold list` is always the first move on any new request, however it's phrased — a full
requirement doc, a short brief, or just a one-line prompt — for both new and existing projects.
Use it to decide between `create` directly, when a matching scaffold already exists, or the
manual-first-then-`learn` path (`references/learning-templates.md`), when it doesn't. Reach for
`--full` over separate per-template `list` calls once more than one template is a real candidate
for the request — it collapses what would otherwise be one round trip per template into one.

## 3. Preview before writing anything

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

`--print-written` is a fourth option that behaves differently from the three above: it actually
writes the files (same as a plain `create`) and then echoes their exact final content in the same
response — one round trip that gets both the write and a verifiable transcript, instead of a
`--print` pass followed by a separate `create`. It cannot be combined with
`--dry-run`/`--print`/`--explain`.

## 4. Generate

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

**Don't set up a folder convention for values files preemptively** — same "extract, don't
anticipate" discipline that applies to templates themselves (`references/learning-templates.md`).
A throwaway, uncommitted values file (or plain `--flag=value` args) is fine until one of these
shows up: the same flag combination has been reused 2-3+ times against the same scaffold, two or
more repos need to generate the same recipe, or a composite feature spans multiple sequential
`create` calls whose values files together form a replayable "feature manifest." Once a trigger
hits, mirror `scaffold-templates`' own `values/<scaffold>/<name>.yaml` shape (see its README)
rather than inventing a new one, placed alongside `scaffolding-code/` — not inside it, since it's
project state describing invocations, not template source. Commit it like any other project source.

A values file isn't portable across repos whose `scaffolding-code` has diverged
(`references/setup.md`) — solve the sharing-model question first; values-file conventions only
layer on top of it.

If `scaffold list <scaffold>` reports "no templates dimension - this version is itself the
template; omit `<template>`", that scaffold's resolved version is a **leaf**: `create` takes
exactly 2 positionals for it, `scaffold create <scaffold> <name>`, not 3 — don't pass a dummy
`<template>` value to fill the slot.

If the target template declares an anchor-based insert (`insert_after`/`insert_before` in a
`jig.yaml` `files:` entry), `create` also splices into an already-existing file instead of only
writing new ones — the output reports `Spliced into N existing file(s)`. This only works for
anchors the template author already declared; `scaffold-cli` has no way to discover an arbitrary
insertion point in a file it doesn't know about, so don't assume it can add a route to a file with
no such rule — say so instead of hand-editing the file to compensate.

For a Java file that was never `create`-generated in the first place (so it has no scaffold-cli
anchor at all), `scaffold-cli` deliberately has no fallback of its own — adding one (e.g.
OpenRewrite's AST-based `JavaTemplate`/`Recipe` mechanism) would pull a JVM dependency into a
single-binary Go CLI. If the team already has OpenRewrite (or `rewrite-maven-plugin`) in their own
Java toolchain, that's a reasonable external tool to point them at for splicing scaffold-cli's
generated snippet into that file safely — not something `scaffold-cli` invokes or depends on
itself.

If the target template declares `flat_output: true` in its `jig.yaml`, `create` writes straight
into `--output` (default `.`) instead of nesting under `<output>/<name>/` — for a template whose
own `files:` `target`s are already fully-qualified relative to the project root (e.g. laying files
into an existing repo tree) rather than one that generates a new, self-contained `<name>` project
directory. Whether a given scaffold does this is up to the template author, not something you
choose per invocation.

Without `--force`/`--skip-existing`, `create` reports exactly which files under the target already
exist (`N file(s) already exist under <target>: ...`) rather than refusing the whole invocation
just because the target directory itself is already there — two templates that share one `<name>`
but write to non-overlapping paths no longer collide with each other's leftovers.

**`--skip-existing` treats a template's `merge:`-registered files differently from a plain one.**
A plain existing file is left untouched, matching the flag's name — but a file the template
declares under `merge:` in its `jig.yaml` (e.g. `application.yml`, `pom.xml`, `requirements.txt`)
is deep-merged with the copy already on disk instead of being skipped, so a second `create` against
the same `--output` can still add a new dependency/config key without `--force` clobbering
everything else already there. Merge format is inferred from the filename: `.yml`/`.yaml`/`.json`
merge as structured documents (maps merge recursively, arrays replace wholesale, an explicit `null`
deletes a key); `requirements.txt` merges by package name instead — a pinned version from the newer
source replaces the older one for the same package, the existing file keeps its own line order and
comments, and a package only the newer source lists is appended.

**`create --print-written` is the complete verification, in one call — nothing after it needs
re-checking.** Reach for it by default over the older `--dry-run`/`--print`-then-`create` two-step:
it writes the files for real and then echoes their exact final content, including a spliced file's
full post-splice content (the "Spliced into N existing file(s)" case) — the one thing a
write-nothing `--print` preview couldn't show on its own, and previously the one legitimate reason
to re-open a generated file afterward. Once its output looks right, the files are correct, full
stop; re-reading them confirms nothing it didn't already show.

A plain `--dry-run`/`--print` pass (no write) is still the right call when the invocation itself is
still uncertain — e.g. unsure which flags will resolve, and not ready to write yet. Once you are
ready, `--print-written` replaces both that preview and any post-write check in a single round
trip. If a requirement was ambiguous, resolve that ambiguity *before* generating (by reading the
relevant source files or asking), not by re-checking the output after the fact.

## Reference

- Setup, installation, and staying in sync: `references/setup.md`
- Growing templates deliberately and the full `learn`/`learn-review`/`learn-promote` workflow:
  `references/learning-templates.md`
- Full command reference: [scaffold-cli README](https://github.com/yusronMu77/scaffold-cli#readme)
- Template authoring contract (`jig.yaml`, the precedence rule, reserved names): [scaffold-templates README](https://github.com/yusronMu77/scaffold-templates#readme)
