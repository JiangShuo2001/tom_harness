"""Compute detailed stats by 8 task types and 6 ability dimensions.

Usage:
  python examples/compute_detailed_stats.py results/ablation_0507/2_skill
  python examples/compute_detailed_stats.py results/ablation_0507  # all subdirs

Outputs:
  - <out_dir>/stats_detailed.json   (per task type + per ability dimension)
  - Console summary table

Requires: benchmark data accessible via load_tombench()
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmark.load_tombench import load_tombench  # noqa: E402

EIGHT_TASKS = {
    "Ambiguous Story Task",
    "False Belief Task",
    "Faux-pas Recognition Test",
    "Hinting Task Test",
    "Persuasion Story Task",
    "Scalar Implicature Test",
    "Strange Story Task",
    "Unexpected Outcome Test",
}

SIX_ABILITIES = {
    "Belief",
    "Desire",
    "Emotion",
    "Intention",
    "Knowledge",
    "Non-Literal Communication",
}


def extract_ability(ability_raw: str) -> str:
    """Extract ability dimension from raw field (take content before colon)."""
    if ":" in ability_raw:
        dim = ability_raw.split(":")[0].strip()
    elif "：" in ability_raw:
        dim = ability_raw.split("：")[0].strip()
    else:
        dim = ability_raw.strip()
    # Normalize case: "Non-literal communication" -> "Non-Literal Communication"
    if dim.lower() == "non-literal communication":
        return "Non-Literal Communication"
    return dim


def load_ability_map(data_dir=None) -> dict[str, str]:
    """Build sample_id -> ability_dimension mapping from benchmark data."""
    samples = load_tombench(data_dir=data_dir)
    mapping = {}
    for s in samples:
        ability_raw = s["metadata"].get("ability", "")
        mapping[s["id"]] = extract_ability(ability_raw)
    return mapping


def compute_group_stats(records: list[dict], group_key: str, group_map: dict[str, str]) -> dict:
    """Compute accuracy per group, excluding errors from denominator."""
    groups = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0})

    for r in records:
        group = group_map.get(r["id"], "")
        if not group:
            continue
        groups[group]["total"] += 1
        is_error = bool(r.get("error") or not r.get("predicted"))
        if is_error:
            groups[group]["errors"] += 1
        elif r.get("correct"):
            groups[group]["correct"] += 1

    result = {}
    for g, d in sorted(groups.items()):
        valid_n = d["total"] - d["errors"]
        d["accuracy"] = round(d["correct"] / valid_n, 4) if valid_n > 0 else 0.0
        result[g] = dict(d)
    return result


def process_one_dir(out_dir: Path, ability_map: dict[str, str]):
    """Process a single result directory."""
    results_path = out_dir / "results.jsonl"
    if not results_path.exists():
        return None

    records = [json.loads(l) for l in open(results_path, encoding="utf-8") if l.strip()]
    if not records:
        return None

    # Task type map: id -> task
    task_map = {r["id"]: r.get("task", "") for r in records}

    # Filter to 8 core tasks
    task_stats = compute_group_stats(
        [r for r in records if task_map.get(r["id"], "") in EIGHT_TASKS],
        "task",
        task_map,
    )

    # Ability dimension stats
    ability_stats = compute_group_stats(records, "ability", ability_map)
    # Only keep the 6 target dimensions
    ability_stats = {k: v for k, v in ability_stats.items() if k in SIX_ABILITIES}

    # Overall (all records)
    total = len(records)
    correct = sum(1 for r in records if r.get("correct"))
    errors = sum(1 for r in records if r.get("error") or not r.get("predicted"))
    valid_total = total - errors

    stats = {
        "overall": {
            "total": total,
            "correct": correct,
            "errors": errors,
            "accuracy": round(correct / valid_total, 4) if valid_total else 0,
        },
        "per_task_8": task_stats,
        "per_ability_6": ability_stats,
    }

    stats_path = out_dir / "stats_detailed.json"
    stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    return stats


def print_summary(name: str, stats: dict):
    """Print a formatted summary table."""
    o = stats["overall"]
    print(f"\n{'='*60}")
    print(f" {name}")
    print(f" Overall: {o['correct']}/{o['total']-o['errors']} = {o['accuracy']*100:.2f}% (errors: {o['errors']})")
    print(f"{'='*60}")

    print(f"\n  {'Task Type':<30s} {'Correct':>7s} {'Valid':>6s} {'Acc':>8s} {'Err':>5s}")
    print(f"  {'-'*30} {'-'*7} {'-'*6} {'-'*8} {'-'*5}")
    for t in sorted(stats["per_task_8"]):
        d = stats["per_task_8"][t]
        valid = d["total"] - d["errors"]
        print(f"  {t:<30s} {d['correct']:7d} {valid:6d} {d['accuracy']*100:7.2f}% {d['errors']:5d}")

    print(f"\n  {'Ability Dimension':<30s} {'Correct':>7s} {'Valid':>6s} {'Acc':>8s} {'Err':>5s}")
    print(f"  {'-'*30} {'-'*7} {'-'*6} {'-'*8} {'-'*5}")
    for a in sorted(stats["per_ability_6"]):
        d = stats["per_ability_6"][a]
        valid = d["total"] - d["errors"]
        print(f"  {a:<30s} {d['correct']:7d} {valid:6d} {d['accuracy']*100:7.2f}% {d['errors']:5d}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python examples/compute_detailed_stats.py <result_dir_or_parent>")
        sys.exit(1)

    target = Path(sys.argv[1])
    data_dir = sys.argv[2] if len(sys.argv) > 2 else None

    print("Loading ability map from benchmark data...")
    ability_map = load_ability_map(data_dir=data_dir)
    print(f"  Loaded {len(ability_map)} sample -> ability mappings")

    # Check if target is a single result dir or parent of multiple
    if (target / "results.jsonl").exists():
        # Single dir
        stats = process_one_dir(target, ability_map)
        if stats:
            print_summary(target.name, stats)
    else:
        # Parent dir with subdirs
        for d in sorted(target.iterdir()):
            if d.is_dir() and (d / "results.jsonl").exists():
                stats = process_one_dir(d, ability_map)
                if stats:
                    print_summary(d.name, stats)


if __name__ == "__main__":
    main()
