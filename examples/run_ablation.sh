#!/usr/bin/env bash
# 全量 ToMBench 消融实验：8 种模块组合 (skill × rag × memory)
#
# 用法:
#   bash examples/run_ablation.sh                     # 全量数据
#   bash examples/run_ablation.sh --limit 5           # 每 task 5 条试跑
#   bash examples/run_ablation.sh --tasks "False Belief Task,Persuasion Story Task"
#
# 已完成的组合会自动跳过（检测 stats.json），删除对应目录可重跑。

set -euo pipefail

EXTRA_ARGS="${*}"
BASE_DIR="results/ablation_$(date +%m%d)"
RUNNER="python examples/run_tombench_harness.py"

# 如果未指定 --limit，默认全量
if [[ ! "$EXTRA_ARGS" =~ "--limit" ]]; then
    EXTRA_ARGS="--limit 0 $EXTRA_ARGS"
fi

mkdir -p "$BASE_DIR"

# 7 种组合：顺序固定，便于对比
NAMES=(
    "1_baseline"
    "2_skill"
    "3_rag"
    "4_memory"
    "5_skill_rag"
    "6_skill_memory"
    "7_rag_memory"
    "8_skill_rag_memory"
)
FLAGS=(
    ""
    "--skill"
    "--rag"
    "--memory"
    "--skill --rag"
    "--skill --memory"
    "--rag --memory"
    "--skill --rag --memory"
)

TOTAL=${#NAMES[@]}

for i in $(seq 0 $((TOTAL - 1))); do
    name="${NAMES[$i]}"
    flag="${FLAGS[$i]}"
    OUT_DIR="$BASE_DIR/$name"
    NUM=$((i + 1))

    echo ""
    echo "============================================================"
    echo "[$NUM/$TOTAL] $name"
    echo "  Flags: ${flag:-(none)}"
    echo "  Output: $OUT_DIR"
    echo "============================================================"

    if [ -f "$OUT_DIR/stats.json" ]; then
        echo "  → Already completed, skipping. Delete $OUT_DIR/stats.json to re-run."
        continue
    fi

    mkdir -p "$OUT_DIR"
    $RUNNER $EXTRA_ARGS $flag --out_dir "$OUT_DIR" 2>&1 | tee "$OUT_DIR/console.log"

    echo "  → Done."
done

# ── 汇总表 ──────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo " Ablation Summary — $(date)"
echo " Results dir: $BASE_DIR"
echo "============================================================"
echo ""

python3 - "$BASE_DIR" "${NAMES[@]}" << 'PYEOF'
import json, sys, os

base_dir = sys.argv[1]
names = sys.argv[2:]

header = f"{'Config':<25s} {'Total':>6s} {'Correct':>7s} {'Acc':>8s} {'Errors':>6s}"
sep    = f"{'-'*25} {'-'*6} {'-'*7} {'-'*8} {'-'*6}"
print(header)
print(sep)

for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        print(f"{name:<25s} {'(not run)':>6s}")
        continue
    with open(stats_path) as f:
        s = json.load(f)
    o = s["overall"]
    print(f"{name:<25s} {o['total']:6d} {o['correct']:7d} {o['accuracy']*100:7.2f}% {o['errors']:6d}")

# per-task 对比
print()
print("Per-task accuracy:")
print()

all_tasks = set()
config_stats = {}
for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        continue
    with open(stats_path) as f:
        s = json.load(f)
    config_stats[name] = s.get("per_task", {})
    all_tasks.update(s.get("per_task", {}).keys())

if all_tasks and config_stats:
    short_names = [n.split("_", 1)[1] if "_" in n else n for n in names if n in config_stats]
    col_w = max(8, max(len(sn) for sn in short_names) + 1)
    header2 = f"{'Task':<40s}" + "".join(f"{sn:>{col_w}s}" for sn in short_names)
    print(header2)
    print("-" * len(header2))

    for task in sorted(all_tasks):
        row = f"{task:<40s}"
        for name in names:
            if name not in config_stats:
                continue
            ts = config_stats[name].get(task)
            if ts:
                row += f"{ts['accuracy']*100:>{col_w}.1f}"
            else:
                row += f"{'—':>{col_w}s}"
        print(row)

PYEOF

echo ""
echo "Done. Full results in: $BASE_DIR/"
