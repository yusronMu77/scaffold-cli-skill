#!/usr/bin/env python3
"""Materialize isolated trial sandboxes for a benchmark iteration from a config file.

Usage:
    python setup_sandbox.py <config.json>

Copies a template project checkout into <iteration_dir>/<eval_name>/<config>/<trial>/repo/ for
every trial listed, optionally overlaying fixture files on top (for evals that need pre-existing
state, e.g. iteration-8's add-route family needed a controller with a splice anchor already
present). See ../README.md for the directory convention this produces.

Config schema:
{
  "template_dir": "path/to/a/project checkout containing the skill + tool + target codebase",
  "iteration_dir": "path/to/workspace/iteration-N",
  "trials": [
    {
      "eval_name": "add-ping-endpoint",
      "configs": ["with_skill"],
      "trial_numbers": [3]
    },
    {
      "eval_name": "add-version-route",
      "configs": ["with_skill", "without_skill"],
      "trial_numbers": [1, 2],
      "fixture_dir": "path/to/files-to-overlay-onto-repo-after-copying"
    }
  ]
}

`fixture_dir`, if given, is copied on top of the freshly-copied template (recursive merge, fixture
files win on conflict) -- use it for state a trial needs to already exist before the task starts.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path


def copy_template(template_dir: Path, dest_repo: Path):
    dest_repo.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template_dir, dest_repo, dirs_exist_ok=True)


def overlay_fixture(fixture_dir: Path, dest_repo: Path):
    shutil.copytree(fixture_dir, dest_repo, dirs_exist_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config_json")
    args = ap.parse_args()

    cfg = json.load(open(args.config_json, encoding="utf-8"))
    template_dir = Path(cfg["template_dir"]).resolve()
    iteration_dir = Path(cfg["iteration_dir"]).resolve()
    if not template_dir.is_dir():
        print(f"template_dir does not exist: {template_dir}", file=sys.stderr)
        return 1

    for spec in cfg["trials"]:
        eval_name = spec["eval_name"]
        fixture_dir = Path(spec["fixture_dir"]).resolve() if spec.get("fixture_dir") else None
        for config in spec["configs"]:
            for n in spec["trial_numbers"]:
                dest_repo = iteration_dir / eval_name / config / f"trial-{n}" / "repo"
                copy_template(template_dir, dest_repo)
                if fixture_dir:
                    overlay_fixture(fixture_dir, dest_repo)
                print(f"{eval_name}/{config}/trial-{n} -> {dest_repo}" + (" (+ fixture)" if fixture_dir else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
