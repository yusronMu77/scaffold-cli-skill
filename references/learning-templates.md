# Growing and learning templates

This is authoring-time guidance — building or extending templates in a project's `scaffolding-code`
or in `scaffold-templates` itself — not the per-task generate workflow (see `SKILL.md` for that).
It's referenced from `SKILL.md`'s discovery step for the "no matching scaffold exists yet" branch:
write the first real instance by hand, then come back here once a genuine repeat exists.

## Grow and validate templates deliberately

Applies to a project-owned `scaffolding-code` (see `references/setup.md`) as much as to
`scaffold-templates` itself — growing it well is deliberate work, not passive drift:

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

## Learn a template from an existing example

Instead of hand-authoring a `jig.yaml` from scratch, point `learn` at one already-written example
(a real controller, a CDK stack, any single instance of a pattern the project repeats) and it
separates invariant structure from variable names/paths/fields — normally by calling an LLM once.

**Already have a Java entity/POJO to scaffold from, rather than a whole example to `learn`?**
`scaffold learn-fields <JavaFile.java>` extracts its field declarations with a regex heuristic —
name, type, and whatever validation annotations sit directly above each field — and prints them as
the `data.entity.fields` YAML a `-f` values file already supplies. No API key, no model call:

```bash
scaffold learn-fields src/main/java/com/example/Order.java > fields.yaml
scaffold create <scaffold> <template> <name> -f fields.yaml -f base.yaml
```

It's a complement to `learn`, not a replacement — a regex heuristic, not a Java parser, so it only
recognizes ordinary single-statement field declarations with at least one modifier. An irregular
class (fields split across multiple statements, unusual modifier order, generated code) is still
better served by `learn` itself.

**Before scanning or inferring anything, `learn` checks whether an already-registered template's
base shape (file names, directory structure) already matches the example folder.** On a confident
match it prints the `scaffold create ...` invocation that already covers it and exits immediately —
nothing scanned further, no provider call, no draft written — rather than growing a duplicate
template in the registry. Check that output before treating `learn` as necessary at all: the
pattern may already be covered. Pass `--skip-match` to force a fresh draft regardless (for a
genuinely new pattern that happens to resemble an existing one).

Short of a confident match, `learn` also surfaces an **uncertain** one: if an existing template
scores a high-but-not-confident shape overlap, it prints a one-time note with that template's
`scaffold create ...` invocation and still proceeds with `learn` (no exit). Check that suggestion
before promoting the freshly-learned draft — it may turn out to be the same pattern with just
enough variance to miss the confident-match bar.

When it does scan, `learn` automatically skips common build/dependency-artifact directories the
same way it already skips dot-directories — `node_modules`, `dist`, `build`, `target`, `bin`,
`obj`, `__pycache__` — since a real, working example regenerates these normally and they're never
part of the pattern being learned. Not configurable; rename a directory that should be scanned (or
copy the example elsewhere) if it happens to share one of these names.

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
`--response-format=tool|json_schema` additionally picks how the `openai` provider asks for
structured JSON back, only for a model that rejects forced tool_choice.

**Only that live-provider-call path redacts secrets before sending anything externally** — before
the scanned content reaches the model, `learn` replaces secret-shaped values (API keys, tokens,
private key blocks, credentials embedded in a URL, etc.) with placeholders and reports which rule
fired per file, never the secret text itself. This doesn't apply to `--draft`: when you supply a
draft directly, you already read the raw files yourself and nothing left the machine, so there's
nothing to redact against.

**Choosing a local model for the human-without-agent path.** These four (as of 2026-09) cover the
size/quality/license tradeoffs for `--provider=openai --base-url=http://localhost:11434/v1` (Ollama,
or any other OpenAI-compatible local endpoint) — this is only for a human running `learn` with no
agent involved; Claude Code and other agents already use `--draft` per the rule above.

- `devstral:24b` — Apache 2.0, the only one of these four with a published SWE-Bench Verified score
  (46.8%), the easiest one to justify to a team.
- `gpt-oss:20b` — Apache 2.0, OpenAI's own open-weight release, runs CPU-only on 16GB RAM with no
  GPU required.
- `qwen3-coder:30b` — strongest coding quality per VRAM of the four, but needs a 24GB+ GPU or a 32GB
  Mac.
- `granite4:8b` — IBM, trained specifically for tool-use and structured JSON output, fits on small
  machines.

This is documentation for filling in `--base-url`/`--model`, not new engine behavior — none of it
changes which flags exist.

**Vetting a new model or provider before adopting it as the team default.** A public benchmark like
HumanEval or SWE-Bench measures general coding ability, not the specific thing `learn` needs from a
model — reliably separating invariant structure from variable names/paths/fields in one pass. Keep
a small eval-set instead: 2-3 example folders with already-known-clean `learn-review` results, run
against any new model/provider candidate before trusting it as a default.

1. **A single-file pattern with one concept in several casings** — e.g. a small class whose name
   appears as PascalCase, kebab-case, and camelCase across its content and filename. Clean: the
   draft has exactly one `variables` entry for that concept (never a separate variable per casing —
   see "one variable per concept" above), and `learn-review` reports zero mismatches.
2. **A multi-file example with a value that must stay literal** — e.g. a fixed port number or a
   config key that happens to look variable-ish but is identical across every real instance. Clean:
   that value stays in the draft's file `content` unchanged rather than getting lifted into
   `variables`; an over-eager model fails this one by inventing a variable for it.
3. **An example with a file that must NOT be templated** — a `.gitignore`-style file, or one written
   in a foreign templating language (Jinja, ERB, Handlebars). Clean: the draft uses `target:` (for
   the reserved-filename case) or `"raw": true` (for the foreign-syntax case) instead of running the
   file through this engine's own `{{ }}` templating.

A candidate passes when `learn-review` reports clean against all 2-3 examples under the same rules
documented above, not just "didn't crash" — the byte-comparison is what catches a hallucinated or
dropped variable mechanically, no second model call needed to judge it.

**A draft's file `path`s are relative to the scanned example folder itself, not the destination the
template will eventually write to once registered.** Don't bake a real project's destination prefix
(e.g. a per-instance nested subdirectory) into a draft's own `path`s — `learn-review` compares the
draft's render byte-for-byte against that same example folder treated as the root, so a baked-in
prefix reports the entire draft as mismatched. Add that nesting as a `target:` override afterward,
once the draft is promoted and wired into the real templates tree.

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
    {"path": "gitignore.tpl", "content": "target/\n", "target": ".gitignore"},
    {"path": "playbook.yml", "content": "- hosts: {{ hosts }}\n", "raw": true}
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
- **Naming trap: `camelcase` yields PascalCase, not lowerCamelCase** (Sprig's `"order_status" |
  camelcase` → `"OrderStatus"`, capital `O`). For a single-word lowerCamelCase identifier, use
  `lower` instead (`EntityName="Order"` → `{{ .EntityName | lower }}` = `order`). For a
  multi-word lowerCamelCase identifier, compose the `lowerFirst` template function (lowercases
  only the first rune) after `camelcase`: `{{ .EntityName | camelcase | lowerFirst }}`
  (`"order_status"` → `"OrderStatus"` → `"orderStatus"`).
- **`plural` produces an English plural** (`{{ .EntityName | plural }}`: `"Order"` → `"Orders"`) for
  a plural REST path/table/collection name — covers common suffix rules (consonant+`y`→`ies`,
  `s`/`x`/`z`/`ch`/`sh`→`+es`, else `+s`) plus a small built-in irregular-word table (`child`→
  `children`, `person`→`people`, and similar). Like `lowerFirst`, it's a `scaffold-cli` function,
  not Sprig. It's a minimal table, not a full inflection engine — a word it gets wrong should be a
  `computed` entry instead, with the literal correct plural as its value.
- **`flag` is optional — omit it unless the kebab-case of `name` would make a poor CLI flag** (e.g.
  an abbreviation). Left unset, `learn` derives the flag automatically and writes it out explicitly
  in the generated `jig.yaml` either way, so a promoted draft needs no manual `flag:` edit to be
  usable via `--<flag>=value`.
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
- **`"raw": true` is only for a file already written in a foreign templating language** (Jinja,
  Ansible, ERB, Handlebars, ...) whose own `{{ }}`/`{% %}` must survive untouched. Its `content` is
  copied byte-for-byte with zero rendering — maps to `jig.yaml`'s `template: false`. Omit it
  entirely for every ordinary file (the default, and by far the common case, is to template
  normally through this engine's own `{{ }}` syntax).
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
`--force` only when you deliberately mean to overwrite what's already there — `--force` clears the
entire output dir first, so a stale file from a previous draft that no longer appears in the new
one is removed rather than left behind.

After it writes the draft, **review it like any other generated artifact before trusting it**:
read the draft `jig.yaml` and templated files, diff them against the original example, and check
for anything over-generalized (a value templated that should have stayed literal) or
under-generalized (a value left literal that should vary).

**Do that self-review with `scaffold learn-review`, not by eyeballing the draft alone.** Every
draft `learn` writes is marked a **candidate** in its `jig.yaml`
(`candidate: true`): `create` and `lint` both refuse it outright (non-zero exit) — even one already
sitting inside the real `scaffolding-code` tree — and `list` prints the same explanation in place
of the variables it would otherwise show, since it's a browsing command and doesn't hard-fail.
Either way, nothing renders a candidate until it's explicitly approved, so reviewing it in place is
safe:

```bash
scaffold learn-review <draft-dir> <path-to-example>
```

This renders the draft using only its own declared defaults (the same way `create` would) and
byte-compares the result against the original example folder — a correct draft's defaults must
reproduce the example exactly, so ANY difference reported (a missing file, an extra file, or
mismatched content) is a concrete, mechanically-found sign of over- or under-generalization, no
second model call needed. Exit code is non-zero if anything is flagged; fix the draft's
`jig.yaml`/files under `<draft-dir>` (or re-run `learn` on a cleaner example) and re-run
`learn-review` until it reports clean.

A mismatch reported as differing only by line ending (CRLF vs LF) is flagged explicitly as such —
the two printed blocks otherwise look byte-identical in a terminal since `\r` doesn't render
visibly, so without the explicit flag it's easy to mistake for a `learn-review` bug rather than a
real difference worth fixing (e.g. an example file saved with Windows line endings).

If any draft file's `path` or content references `.Name` (the `<name>` positional `create` supplies
at generation time), note `learn-review` has no such positional to draw from — it substitutes the
example directory's own basename instead. Declare an explicit variable with a real `default` for
anything that needs one during review.

Once it's clean — or you've hand-edited the draft in an editor and are satisfied with it — approve
it:

```bash
scaffold learn-promote <draft-dir>
```

This clears the `candidate:` flag (the only thing `create`/`list`/`lint` were refusing it for),
preserving any comments or edits already in the file rather than rewriting it from scratch — this
includes a note left directly on or above the `candidate:` line itself, the most natural place to
record a review. Only now does the draft become a normal template: move/copy it into the project's
real `scaffolding-code` tree (or `scaffold-templates`), same as if it had been hand-authored —
`learn` does not wire it in for you, and neither does `learn-promote`. From that point on,
regenerating instances goes through the ordinary `create` path (the Generate step in `SKILL.md`)
with zero further model calls.

**Two or more similar examples available? Generalize across all of them in one draft, not one at a
time.** When ≥2 existing instances of the same pattern are available, prefer this over running
`learn` separately on each one: a draft built from only a single instance risks hard-coding a value
that actually varies across the others, or the reverse.

If you're supplying `--draft` yourself (the common case, per the rule above — you're already an
LLM): read every example, not just the first, and write ONE draft JSON whose
`variables`/`computed`/`files` cover every instance you looked at — same schema, same rules, no
changes. The one thing this adds: each variable's `default` must be the literal value from the
**first** example path specifically (the one you'll pass first below), even though the variable
itself was generalized by comparing it against the others. This isn't something `learn` enforces —
it's what `learn-review` (below) actually checks against.

Calling a provider directly instead (no `--draft`) takes the extra examples as additional
positionals in the same invocation:

```bash
scaffold learn <path-1> <path-2> [<path-3> ...] --output=<scratch-dir> --provider=...
```

All instances are sent to the model in a single call so it can generalize across them — a single
`<path>` still behaves exactly as before, this is purely additive. The combined size of everything
scanned across every path still has to fit in one call's budget; if `learn` rejects it as too large,
trim the examples down to just the pattern itself or use fewer of them, same "extract, don't
anticipate" discipline as growing templates deliberately above.

Either way — `--draft` or a live provider call — pass `learn-review` every example directory in
the same order `learn` used, not just the first:

```bash
scaffold learn-review <draft-dir> <path-1> [<path-2> ...]
```

`<path-1>` is still checked byte-for-byte against the draft's rendered defaults (a variable's
`default` is always drawn from that first example specifically); every later `<path-N>` is now
also checked structurally — it must have the same set of files as the draft's render — instead of
being ignored.

`learn-promote` afterward is unchanged: `scaffold learn-promote <draft-dir>`.
