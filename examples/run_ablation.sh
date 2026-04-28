#!/usr/bin/env bash
# Ablation test: baseline / skill / rag / memory / all
# Usage: ./examples/run_ablation.sh "Persuasion Story Task"

set -euo pipefail

TASKS="${1:?Usage: $0 \"task name\"}"
OUT_ROOT="results/ablation_$(date +%m%d)_$(echo "$TASKS" | tr ' ' '_')"

python examples/run_tombench_harness.py --tasks "$TASKS" --out_dir "$OUT_ROOT/baseline"
python examples/run_tombench_harness.py --tasks "$TASKS" --out_dir "$OUT_ROOT/skill"   --skill --limit 0
python examples/run_tombench_harness.py --tasks "$TASKS" --out_dir "$OUT_ROOT/rag"     --rag --limit 0
python examples/run_tombench_harness.py --tasks "$TASKS" --out_dir "$OUT_ROOT/memory"  --memory --limit 0
python examples/run_tombench_harness.py --tasks "$TASKS" --out_dir "$OUT_ROOT/all"     --skill --rag --memory --limit 0

echo ""
echo "=== Results ==="
for mode in baseline skill rag memory all; do
    stats="$OUT_ROOT/$mode/stats.json"
    if [[ -f "$stats" ]]; then
        acc=$(python3 -c "import json; d=json.load(open('$stats')); print(f\"{d['overall']['correct']}/{d['overall']['total']} = {d['overall']['accuracy']:.1%}\")")
        printf "  %-10s %s\n" "$mode" "$acc"
    fi
done
