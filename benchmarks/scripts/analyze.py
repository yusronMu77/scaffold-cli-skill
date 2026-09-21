#!/usr/bin/env python3
"""Power calculation + bootstrap CI for one or more with-skill vs without-skill comparisons.

Usage:
    python analyze.py <input.json> [--resamples 10000] [--alpha 0.05] [--power 0.80] [--out result.json]

See ../README.md for the input schema. Prints a human-readable report and (optionally) writes the
same data as JSON.
"""
import argparse
import json
import math
import random
import statistics
import sys

# Two-sided normal quantiles, precomputed for the two alpha/power values this script defaults to
# and exposed generically via a small inverse-normal-CDF approximation for other choices.
def _norm_ppf(p):
    # Acklam's algorithm (rational approximation), good to ~1e-9 -- plenty for sample-size planning.
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    p_low, p_high = 0.02425, 1 - 0.02425
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p <= p_high:
        q = p - 0.5
        r = q*q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


def mean(xs):
    return sum(xs) / len(xs)


def stdev(xs):
    return statistics.stdev(xs) if len(xs) > 1 else 0.0


def bootstrap_ci_delta(a, b, n_resamples, alpha, rng):
    deltas = []
    for _ in range(n_resamples):
        ra = [rng.choice(a) for _ in a]
        rb = [rng.choice(b) for _ in b]
        deltas.append(mean(ra) - mean(rb))
    deltas.sort()
    lo_idx = int((alpha / 2) * n_resamples)
    hi_idx = int((1 - alpha / 2) * n_resamples) - 1
    return deltas[lo_idx], deltas[hi_idx], mean(deltas)


def power_n_per_group(sigma, delta, alpha, power):
    """Two-sample t-test (equal variance, equal n), sample size per group."""
    if delta == 0:
        return float("inf")
    z_alpha2 = _norm_ppf(1 - alpha / 2)
    z_beta = _norm_ppf(power)
    n = 2 * (sigma ** 2) * (z_alpha2 + z_beta) ** 2 / (delta ** 2)
    return math.ceil(n)


def analyze_comparison(comp, resamples, alpha, power, rng):
    name = comp["name"]
    ws = comp["with_skill"]
    wos = comp["without_skill"]
    out = {"name": name, "metrics": {}}
    for metric in ws:
        if metric not in wos:
            continue
        a, b = ws[metric], wos[metric]
        delta = mean(a) - mean(b)
        pct = (delta / mean(b) * 100) if mean(b) else float("nan")
        lo, hi, boot_mean = bootstrap_ci_delta(a, b, resamples, alpha, rng)
        pooled_sigma = math.sqrt((stdev(a) ** 2 + stdev(b) ** 2) / 2)
        power_table = {}
        for target_pct in (5, 10, 15, 20):
            target_delta = mean(b) * target_pct / 100
            power_table[f"{target_pct}pct_shift"] = f"{power_n_per_group(pooled_sigma, target_delta, alpha, power)} runs/arm"
        out["metrics"][metric] = {
            "with_skill": {"n": len(a), "mean": mean(a), "stddev": stdev(a)},
            "without_skill": {"n": len(b), "mean": mean(b), "stddev": stdev(b)},
            "delta": delta,
            "delta_pct": pct,
            "bootstrap_ci95": [lo, hi],
            "pooled_stddev": pooled_sigma,
            "power_calc": power_table,
        }
    return out


def print_report(result):
    for comp in result["comparisons"]:
        print(f"\n=== {comp['name']} ===")
        for metric, m in comp["metrics"].items():
            ws, wos = m["with_skill"], m["without_skill"]
            print(f"  {metric}:")
            print(f"    with_skill    n={ws['n']}  mean={ws['mean']:.1f}  sd={ws['stddev']:.1f}")
            print(f"    without_skill n={wos['n']}  mean={wos['mean']:.1f}  sd={wos['stddev']:.1f}")
            print(f"    delta: {m['delta']:+.1f} ({m['delta_pct']:+.1f}%)")
            lo, hi = m["bootstrap_ci95"]
            crosses_zero = lo <= 0 <= hi
            print(f"    bootstrap 95% CI: [{lo:.1f}, {hi:.1f}]  crosses zero: {crosses_zero}")
            print(f"    power calc (pooled sd={m['pooled_stddev']:.1f}): " + ", ".join(
                f"{k.replace('pct_shift','%')}={v}" for k, v in m["power_calc"].items()))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input_json")
    ap.add_argument("--resamples", type=int, default=10000)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--power", type=float, default=0.80)
    ap.add_argument("--out", default=None, help="write the result as JSON to this path")
    ap.add_argument("--seed", type=int, default=42, help="RNG seed, for reproducible bootstrap CIs")
    args = ap.parse_args()

    data = json.load(open(args.input_json, encoding="utf-8"))
    rng = random.Random(args.seed)
    result = {"comparisons": [analyze_comparison(c, args.resamples, args.alpha, args.power, rng) for c in data["comparisons"]]}

    print_report(result)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\nwritten to {args.out}")


if __name__ == "__main__":
    sys.exit(main())
