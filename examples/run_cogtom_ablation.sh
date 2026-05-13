#!/usr/bin/env bash
# CogToM 消融实验：8 种模块组合 (skill × rag × memory)
# 使用蒸馏后的英文数据集 (~2000 条)
#
# 用法:
#   bash examples/run_cogtom_ablation.sh                       # 全量蒸馏数据
#   bash examples/run_cogtom_ablation.sh --limit 5             # 每 category 5 条试跑
#   bash examples/run_cogtom_ablation.sh --category "Belief,Emotion"
#
# 已完成的组合会自动跳过（检测 stats.json），删除对应目录可重跑。

set -euo pipefail

EXTRA_ARGS="${*}"
BASE_DIR="results/cogtom_ablation_$(date +%m%d)"
RUNNER="python examples/run_cogtom_v2_harness.py"
DATA_FILE="benchmark/CogToM/CogToM-en-distilled.jsonl"

# 默认不限制数量（蒸馏数据已经是 ~2000 条）
if [[ ! "$EXTRA_ARGS" =~ "--limit" ]]; then
    EXTRA_ARGS="--limit 0 $EXTRA_ARGS"
fi

mkdir -p "$BASE_DIR"

# 8 种组合
NAMES=(
    "1_baseline"
    "2_skill"
    "3_rag"
    "4_memory"
    "8_skill_rag_memory"
)
FLAGS=(
    ""
    "--skill"
    "--rag"
    "--memory"
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
    echo "  Data:  $DATA_FILE"
    echo "  Output: $OUT_DIR"
    echo "============================================================"

    if [ -f "$OUT_DIR/stats.json" ]; then
        echo "  → Already completed, skipping. Delete $OUT_DIR/stats.json to re-run."
        continue
    fi

    mkdir -p "$OUT_DIR"
    $RUNNER --data_file "$DATA_FILE" $EXTRA_ARGS $flag --out_dir "$OUT_DIR" 2>&1 | tee "$OUT_DIR/console.log"

    echo "  → Done."
done

# ── 汇总表 ──────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo " CogToM Ablation Summary — $(date)"
echo " Data: $DATA_FILE"
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

# per-category 对比
print()
print("Per-category accuracy:")
print()

all_cats = set()
config_stats = {}
for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        continue
    with open(stats_path) as f:
        s = json.load(f)
    config_stats[name] = s.get("per_category", {})
    all_cats.update(s.get("per_category", {}).keys())

if all_cats and config_stats:
    short_names = [n.split("_", 1)[1] if "_" in n else n for n in names if n in config_stats]
    col_w = max(10, max(len(sn) for sn in short_names) + 1)
    header2 = f"{'Category':<20s}" + "".join(f"{sn:>{col_w}s}" for sn in short_names)
    print(header2)
    print("-" * len(header2))

    for cat in sorted(all_cats):
        row = f"{cat:<20s}"
        for name in names:
            if name not in config_stats:
                continue
            cs = config_stats[name].get(cat)
            if cs:
                row += f"{cs['accuracy']*100:>{col_w}.1f}"
            else:
                row += f"{'—':>{col_w}s}"
        print(row)

# per-subcategory 对比
print()
print("Per-subcategory accuracy:")
print()

all_subcats = set()
config_substats = {}
for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        continue
    with open(stats_path) as f:
        s = json.load(f)
    config_substats[name] = s.get("per_subcategory", {})
    all_subcats.update(s.get("per_subcategory", {}).keys())

if all_subcats and config_substats:
    short_names = [n.split("_", 1)[1] if "_" in n else n for n in names if n in config_substats]
    col_w = max(10, max(len(sn) for sn in short_names) + 1)
    header3 = f"{'Subcategory':<55s}" + "".join(f"{sn:>{col_w}s}" for sn in short_names)
    print(header3)
    print("-" * len(header3))

    for subcat in sorted(all_subcats):
        row = f"{subcat:<55s}"
        for name in names:
            if name not in config_substats:
                continue
            scs = config_substats[name].get(subcat)
            if scs:
                row += f"{scs['accuracy']*100:>{col_w}.1f}"
            else:
                row += f"{'—':>{col_w}s}"
        print(row)

PYEOF

echo ""
echo "Done. Full results in: $BASE_DIR/"
