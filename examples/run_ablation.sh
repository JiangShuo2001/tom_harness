#!/usr/bin/env bash
# Ablation test: baseline / skill / rag / memory / all
# Usage: ./examples/run_ablation.sh "Persuasion Story Task"

set -euo pipefail

TASKS="${1:?Usage: $0 \"task name\"}"
OUT_ROOT="results/ablation_$(date +%m%d)"

python examples/run_tombench_harness.py --tasks "$TASKS" --out_dir "$OUT_ROOT/baseline"
python examples/run_tombench_harness.py --tasks "$TASKS" --out_dir "$OUT_ROOT/skill"   --skill
python examples/run_tombench_harness.py --tasks "$TASKS" --out_dir "$OUT_ROOT/rag"     --rag
python examples/run_tombench_harness.py --tasks "$TASKS" --out_dir "$OUT_ROOT/memory"  --memory
python examples/run_tombench_harness.py --tasks "$TASKS" --out_dir "$OUT_ROOT/all"     --skill --rag --memory

echo ""
echo "=== Results ==="
for mode in baseline skill rag memory all; do
    stats="$OUT_ROOT/$mode/stats.json"
    if [[ -f "$stats" ]]; then
        acc=$(python3 -c "import json; d=json.load(open('$stats')); print(f\"{d['overall']['correct']}/{d['overall']['total']} = {d['overall']['accuracy']:.1%}\")")
        printf "  %-10s %s\n" "$mode" "$acc"
    fi
done
