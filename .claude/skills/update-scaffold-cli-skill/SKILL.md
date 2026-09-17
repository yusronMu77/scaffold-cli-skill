---
name: update-scaffold-cli-skill
description: Update an already-installed scaffold-cli-skill to the latest version published on GitHub (yusronMu77/scaffold-cli-skill) — locate the installed copy, git pull it, and report what changed, including whether the scaffold-cli binary itself now needs updating too. Use whenever asked to update/upgrade this skill, or when SKILL.md's "Verified against" line looks like it could be behind what's on GitHub.
---

# update-scaffold-cli-skill

Updates an **already-installed** copy of the `scaffold-cli-skill` skill in place, by pulling
straight from its GitHub remote (`https://github.com/yusronMu77/scaffold-cli-skill`) — this is
purely a remote-vs-local-install operation. It never looks at, builds, or depends on a local
checkout of `scaffold-cli`'s own source; whichever machine or project this runs in, the only thing
that matters is the installed skill folder and its `origin` remote.

Skip this entirely if you're working inside the `scaffold-cli-skill` source repo itself (its own
`git remote -v` points at `scaffold-cli-skill.git` and there's no `SKILL.md` frontmatter oddity) —
that's the source, not an install; use ordinary `git`/PR workflow there instead of "updating" it.

## 1. Locate the installed copy

Same detection `SKILL.md` step 1 already uses: a **global** install resolves under the user's home
directory skills folder (e.g. `~/.claude/skills/scaffold-cli`), a **project-scoped** one resolves
inside a specific project (`<project-root>/.claude/skills/scaffold-cli`). If more than one install
exists on the machine and it's unclear which one prompted this, ask which to update rather than
guessing.

Confirm it really is a clone of this skill, not something else with the same folder name:

```bash
git -C <skill-dir> remote get-url origin
# expect: https://github.com/yusronMu77/scaffold-cli-skill(.git)
```

## 2. Refuse to clobber local changes

```bash
git -C <skill-dir> status --porcelain
```

If that prints anything, stop and tell the user — don't discard or stash it yourself. A modified
installed copy is very likely an intentional local override (a team's own tweak to the "Verified
against" pin, an added note), not stray drift to blow away.

## 3. Record the before-state, then pull

```bash
git -C <skill-dir> rev-parse HEAD                              # before
grep -m1 "Verified against" <skill-dir>/SKILL.md                # before

git -C <skill-dir> fetch origin
git -C <skill-dir> merge --ff-only origin/main                 # fails loudly instead of creating
                                                                 # a merge commit if history diverged
```

If the fast-forward merge fails, the local branch has diverged from `origin/main` (shouldn't happen
on an untouched install per step 2, but don't force it) — stop and tell the user rather than
rebasing or resetting on their behalf.

## 4. Report what changed

```bash
git -C <skill-dir> log <old-sha>..HEAD --oneline                # commits just pulled in
grep -m1 "Verified against" <skill-dir>/SKILL.md                # after
```

Summarize: old "Verified against" version → new one, and the commit list. If nothing was ahead,
say the skill was already current — that's a normal, complete outcome, not a failure.

## 5. Flag if the `scaffold-cli` binary itself is now behind

This skill only updates `scaffold-cli-skill`'s own files, never the `scaffold-cli` binary. If the
newly-pulled "Verified against" version differs from what's actually installed
(`scaffold --version`), say so and point at `SKILL.md`'s own step 1 (the install script, optionally
pinned with `SCAFFOLD_CLI_VERSION=<version>` / `-Version <version>`) for updating the binary to
match — don't run that yourself as part of this skill unless asked.

## Don't

- Don't treat this as a maintainer/release skill — it has nothing to do with cutting a
  `scaffold-cli` release or editing `SKILL.md`'s prose; it only fast-forwards an install to
  whatever's already on `origin/main`.
- Don't force-pull, reset, or rebase over local modifications or a diverged branch — stop and ask.
- Don't assume a single well-known install path — always resolve it first (step 1).
