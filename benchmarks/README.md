# Benchmark harness

Reproducible methodology + scripts for measuring this skill's actual token/time/tool-call cost
against a hand-written baseline, and for grading that a cheaper run didn't get there by producing
worse output. This exists because issue [#30](https://github.com/yusronMu77/scaffold-cli-skill/issues/30)
went through eight re-benchmarks (#26 through iteration-8) before the methodology itself was
formalized into scripts — every prior run re-derived the sandbox layout, grading conventions, and
statistics from scratch in an ad-hoc workspace. This directory is that formalization, so the next
re-run doesn't have to.

## Directory convention

A benchmark run lives in a workspace directory (not committed to this repo — it's disposable,
regenerate it per run) shaped like:

```
<workspace>/iteration-N/
  <eval-name>/
    eval_metadata.json          # {eval_id, eval_name, prompt, src_root, assertions[]}
    with_skill/
      trial-1/
        repo/                   # isolated sandbox copy of the target project + skill + tool
        timing.json             # {total_tokens, tool_calls, duration_ms, total_duration_seconds}
        grading.json            # written by grade.py
      trial-2/
        ...
    without_skill/
      trial-1/
      trial-2/
  agent_map.json                 # {agent_id: {path, output_file}} — bookkeeping for whoever ran the trials
  benchmark.json                 # written by analyze.py
  benchmark.md                   # human-readable summary, written by hand from benchmark.json
```

Every trial gets its **own isolated `repo/` directory** — a fresh copy of the target project, never
the live repo. This was a real gap in the very first benchmark (iteration-1's without-skill baseline
wrote into the live project and got caught/fixed manually); making the sandbox structural instead of
an instruction the agent has to remember closes that gap for good.

## `eval_metadata.json` schema

```json
{
  "eval_id": 0,
  "eval_name": "add-ping-endpoint",
  "prompt": "The exact task prompt given to every trial (with_skill and without_skill alike).",
  "src_root": "uid2-generator/src",
  "assertions": [
    { "text": "Human-readable description shown in reports", "check": "file_exists_matching_glob:**/api/ping/*Controller.java" },
    { "text": "...", "check": "file_absent_matching_glob:**/api/version/*Controller.java" },
    { "text": "...", "check": "grep_in_glob:**/api/ping/*Controller.java:@RestController" }
  ]
}
```

- `src_root` is the path (relative to each trial's `repo/`) that assertions search under. Keep it
  project-specific (e.g. `uid2-generator/src` for this repo's benchmark project) so `grade.py` stays
  generic across whatever target codebase a future benchmark uses.
- Three check types, each `type:pattern[:needle]`:
  - `file_exists_matching_glob:<glob>` — at least one match required.
  - `file_absent_matching_glob:<glob>` — zero matches required (use this for "did NOT create a
    stray extra file" assertions — see iteration-8's `add-route` family for why this matters: a
    splice-style scaffold should edit an existing file, not spawn a parallel one).
  - `grep_in_glob:<glob>:<needle>` — needle found in at least one matching file. The needle is
    everything after the *first* colon, so needles containing their own colon (e.g.
    `@scaffold:routes`) work correctly — this bit a genuine grading bug in iteration-8 that a
    naive "split on the last colon" implementation gets wrong.

The **same prompt** is used for both `with_skill` and `without_skill` trials of a given eval — the
differentiator is the instruction given to the trial agent at spawn time (see "Running trials"
below), not a different task description.

## Running trials

This harness doesn't spawn trial agents itself — that's orchestrated by whatever's running the
benchmark (a Claude Code session using its own subagent/task tooling, or an equivalent runner). What
this harness assumes from that orchestration:

1. **Sandboxing**: use `scripts/setup_sandbox.py` to materialize each trial's `repo/` from a
   template checkout (the target project + this skill + the `scaffold` binary already installed),
   optionally overlaying fixture files (see iteration-8's `add-route` family, which needed a
   pre-existing controller with the `// @scaffold:routes` anchor before the trial could start).
2. **Prompt**: give every trial the eval's `prompt` verbatim. For `without_skill` trials, append an
   explicit instruction to hand-write the change and not invoke the scaffold tool or its skill,
   even though both are present in the sandbox (this mirrors how a real "no skill installed" user
   would behave, without needing a second, skill-stripped template checkout).
3. **Shell**: on Windows, explicitly instruct every trial to use PowerShell, never Bash. Git Bash on
   Windows has repeatedly (iterations 1, 4, 5) hit a `command not found` failure for basic coreutils
   that inflates a trial's token/time numbers for reasons unrelated to the skill under test. If a
   trial's `timing.json` looks like an outlier, check whether it hit this before folding it into
   the mean.
4. **Capture `timing.json` immediately per trial** as soon as its usage is known (tokens, tool
   calls, duration) — this is usually a one-time notification from whatever spawned the trial, not
   something recoverable later.
5. **Do not require the target project's build/tests to run** — grading here is static
   (file/content checks), so trials don't need to compile or run anything, which keeps them fast
   and keeps "did it use the skill" the only thing under test.

## Grading

```
python scripts/grade.py <iteration-dir>
```

Scans every `<eval-name>/<config>/<trial>/` under the iteration directory, evaluates that eval's
assertions against `repo/<src_root>`, and writes `grading.json` next to each trial's `repo/`.

## Analysis (power calculation + bootstrap CI)

```
python scripts/analyze.py <input.json> [--resamples 10000] [--alpha 0.05] [--power 0.80]
```

Input schema — one or more named comparisons, each an independent-samples with-skill vs.
without-skill pair of raw per-trial token/time arrays (pull these from each trial's `timing.json`):

```json
{
  "comparisons": [
    {
      "name": "family-A",
      "with_skill": { "tokens": [63121, 64111, 66627, 66622, 65405], "time_seconds": [77.653, 97.902, 75.169, 75.203, 180.094] },
      "without_skill": { "tokens": [53728, 61309, 58330, 56499], "time_seconds": [73.1, 58.7, 63.0, 60.3] }
    }
  ]
}
```

For each comparison this reports: mean ± stddev per arm, the delta and its bootstrap CI (resample
both arms independently, 10,000 resamples by default), and a **power calculation table** — how many
runs per arm a two-sample t-test would need to detect a 5/10/15/20% shift at 80% power, given the
pooled stddev actually observed. Report the CI and the power table alongside the mean±stddev in any
write-up — a mean/stddev pair alone doesn't say whether an observed gap is distinguishable from
noise at the sample size used (see issue #30's 2026-09-21 methodology-review comment for why this
matters: at n=4, "the mean improved 23%" and "the mean didn't move" are not reliably
distinguishable without one).

## Known-anomaly convention

If a trial's outcome is corrupted by something outside what's under test — a shell/coreutils bug, a
CLI argument-parsing footgun the agent hit, a crashed subprocess — **flag it and exclude it from the
pooled mean, don't fold it in**. Document what happened and why it was excluded directly in
`benchmark.md`. Iterations 4-5's Bash/coreutils numbers and iteration-8's `--output` space-vs-`=`
CLI footgun are both examples already in this repo's history (see issue #30's comment history) —
folding either into a mean would have measured the environment/tooling bug's cost, not the skill's.

## Task diversity

A single task family tested repeatedly (e.g. only `/ping`/`/ready`-shaped REST endpoint additions)
risks measuring one task's idiosyncrasies rather than the skill generally — issue #30's methodology
review calls this out directly. When re-benchmarking, prefer adding a structurally different task
(a different scaffold, a different mechanic — e.g. splicing into an existing file vs. generating new
ones — or a different stack) over another variant of an already-measured family. Iteration-8's
`add-route` family (spliced into an existing controller) vs. the original `feature-module` family
(generates new files) is the first example of this in this repo's history, and it surfaced a
genuinely different result: the skill's overhead is roughly fixed per invocation, so it's a much
larger *percentage* of a small task's cost than a large one's.
