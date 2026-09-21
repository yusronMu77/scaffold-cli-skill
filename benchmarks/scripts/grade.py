#!/usr/bin/env python3
"""Grade every trial under a benchmark iteration directory against its eval's assertions.

Usage:
    python grade.py <iteration-dir>

Scans <iteration-dir>/<eval-name>/{with_skill,without_skill}/<trial>/ for every eval that has an
eval_metadata.json, evaluates its assertions against <trial>/repo/<src_root>, and writes
<trial>/grading.json. See ../README.md for the eval_metadata.json and check-type schema.
"""
import argparse
import glob
import json
import os
import sys

CONFIGS = ("with_skill", "without_skill")


def check_file_exists(root, pattern):
    matches = glob.glob(os.path.join(root, pattern), recursive=True)
    return (len(matches) > 0, matches)


def check_file_absent(root, pattern):
    matches = glob.glob(os.path.join(root, pattern), recursive=True)
    passed = len(matches) == 0
    evidence = ["(correctly absent)"] if passed else matches
    return (passed, evidence)


def check_grep(root, pattern_and_needle):
    # Split on the FIRST colon only -- the needle itself may contain a colon
    # (e.g. "@scaffold:routes"), and splitting on the last colon silently
    # truncates it. This was a real grading bug in iteration-8.
    pattern, needle = pattern_and_needle.split(":", 1)
    matches = glob.glob(os.path.join(root, pattern), recursive=True)
    hits = []
    for m in matches:
        try:
            text = open(m, encoding="utf-8").read()
        except Exception:
            continue
        if needle in text:
            hits.append(m)
    return (len(hits) > 0, hits)


def run_assertion(root, assertion):
    check = assertion["check"]
    if check.startswith("file_exists_matching_glob:"):
        passed, evidence = check_file_exists(root, check.split(":", 1)[1])
    elif check.startswith("file_absent_matching_glob:"):
        passed, evidence = check_file_absent(root, check.split(":", 1)[1])
    elif check.startswith("grep_in_glob:"):
        passed, evidence = check_grep(root, check.split(":", 1)[1])
    else:
        passed, evidence = (False, [f"unknown check type: {check}"])
    return {
        "text": assertion["text"],
        "passed": passed,
        "evidence": ", ".join(evidence) if evidence else "no match found",
    }


def find_evals(iteration_dir):
    for name in sorted(os.listdir(iteration_dir)):
        meta_path = os.path.join(iteration_dir, name, "eval_metadata.json")
        if os.path.isfile(meta_path):
            yield name, meta_path


def find_trials(eval_dir, config):
    cfg_dir = os.path.join(eval_dir, config)
    if not os.path.isdir(cfg_dir):
        return
    for trial in sorted(os.listdir(cfg_dir)):
        trial_dir = os.path.join(cfg_dir, trial)
        if os.path.isdir(os.path.join(trial_dir, "repo")):
            yield trial, trial_dir


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("iteration_dir")
    args = ap.parse_args()

    for eval_name, meta_path in find_evals(args.iteration_dir):
        meta = json.load(open(meta_path, encoding="utf-8"))
        src_root_rel = meta.get("src_root", ".")
        eval_dir = os.path.join(args.iteration_dir, eval_name)
        for config in CONFIGS:
            for trial, trial_dir in find_trials(eval_dir, config):
                src_root = os.path.join(trial_dir, "repo", src_root_rel)
                expectations = [run_assertion(src_root, a) for a in meta["assertions"]]
                passed_count = sum(1 for e in expectations if e["passed"])
                grading = {
                    "eval_name": eval_name,
                    "config": config,
                    "trial": trial,
                    "pass_rate": passed_count / len(expectations) if expectations else 0,
                    "expectations": expectations,
                }
                out_path = os.path.join(trial_dir, "grading.json")
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(grading, f, indent=2)
                print(f"{eval_name}/{config}/{trial}: {passed_count}/{len(expectations)} passed -> {out_path}")


if __name__ == "__main__":
    sys.exit(main())
