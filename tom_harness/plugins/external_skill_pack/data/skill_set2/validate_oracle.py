"""
Per-skill validation for the v2 skill set.
Each skill is evaluated ONLY on error cases from its own target task_types.
All (skill, case) pairs are flattened into ONE ThreadPoolExecutor for maximum
parallelism.
"""
import json
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RESULTS = os.path.join(DATA, "results")
PERCEP = os.path.abspath(os.path.join(HERE, "..", "PercepToM"))
sys.path.insert(0, HERE)
sys.path.insert(0, PERCEP)

from llm_agents import load_model                                 # noqa
from eval_new_benchmarks import build_vanilla_prompt, extract_answer_letter  # noqa
from skills import SKILLS, SKILL_TARGETS                          # noqa


MODEL_NAME = os.environ.get("V2_MODEL", "gpt-5.4-mini")
MAX_PER_TASK_TYPE = int(os.environ.get("V2_MAX_PER_TT", "30"))
N_WORKERS = int(os.environ.get("V2_WORKERS", "32"))
os.makedirs(RESULTS, exist_ok=True)
ERROR_FILES = {
    "ToMBench": os.path.join(DATA, "ToMBench.jsonl"),
    "CogToM":   os.path.join(DATA, "CogToM.jsonl"),
}
OUT_JSON = os.path.join(RESULTS, "oracle_results.json")
OUT_MD   = os.path.join(RESULTS, "ORACLE_RESULTS.md")


# ───────────────────────── Data ─────────────────────────
def load_targeted_errors(skill_id):
    targets = SKILL_TARGETS[skill_id]
    out = []
    for ds, path in ERROR_FILES.items():
        per_tt = defaultdict(list)
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                if r["task_type"] in targets:
                    per_tt[r["task_type"]].append(r)
        for tt, items in per_tt.items():
            out.extend(items[:MAX_PER_TASK_TYPE])
    return out


# ───────────────────────── Eval ─────────────────────────
_print_lock = Lock()
_progress = {"done": 0, "total": 0}


def build_skilled_prompt(item, skill_text):
    base = build_vanilla_prompt(
        item["story"], item["question"], item["options"], item["labels"]
    )
    return (
        f"You are answering a Theory-of-Mind multiple-choice question.\n"
        f"Apply the following strategy carefully, then answer.\n\n"
        f"=== STRATEGY ===\n{skill_text}\n=== END STRATEGY ===\n\n"
        f"=== QUESTION ===\n{base}"
    )


def eval_one(model, skill_id, skill_text, item, total):
    try:
        prompt = build_skilled_prompt(item, skill_text)
        resp = model.interact(prompt, max_tokens=2048)
        pred = extract_answer_letter(resp, item["labels"])
        fixed = pred == item["gold_answer"]
        result = {
            "skill_id": skill_id,
            "global_idx": item["global_idx"],
            "dataset": item["dataset"],
            "task_type": item["task_type"],
            "gold": item["gold_answer"],
            "vanilla_gpt_pred": item.get("gpt_5_4_mini", {}).get("predicted"),
            "skilled_pred": pred,
            "fixed": bool(fixed),
            "response_head": (resp or "")[-400:],
        }
    except Exception as e:
        result = {
            "skill_id": skill_id,
            "global_idx": item["global_idx"],
            "dataset": item["dataset"],
            "task_type": item["task_type"],
            "gold": item["gold_answer"],
            "vanilla_gpt_pred": item.get("gpt_5_4_mini", {}).get("predicted"),
            "skilled_pred": None,
            "fixed": False,
            "error": str(e),
        }
    with _print_lock:
        _progress["done"] += 1
        if _progress["done"] % 10 == 0 or _progress["done"] == total:
            print(f"  [{_progress['done']:4d}/{total}] {skill_id} {item['global_idx']}"
                  f" gold={item['gold_answer']}"
                  f" pred={result.get('skilled_pred')}"
                  f" {'FIX' if result['fixed'] else ''}",
                  flush=True)
    return result


# ───────────────────────── Driver ─────────────────────────
def main():
    model = load_model(MODEL_NAME)

    # Build flat (skill_id, item) job list
    jobs = []  # (skill_id, item)
    skill_targets = {}  # skill_id -> targeted error items
    for sid in SKILLS:
        items = load_targeted_errors(sid)
        skill_targets[sid] = items
        for it in items:
            jobs.append((sid, it))

    total = len(jobs)
    _progress["total"] = total
    print(f"[v2] model={MODEL_NAME}  workers={N_WORKERS}  jobs={total}", flush=True)
    for sid, items in skill_targets.items():
        per_tt = defaultdict(int)
        for it in items:
            per_tt[it["task_type"]] += 1
        print(f"  {sid:20s} {len(items):4d} cases  "
              + " | ".join(f"{tt}:{n}" for tt, n in per_tt.items()),
              flush=True)

    t0 = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futures = [
            ex.submit(eval_one, model, sid, SKILLS[sid], it, total)
            for (sid, it) in jobs
        ]
        for f in as_completed(futures):
            results.append(f.result())
    elapsed = time.time() - t0

    # ─── Aggregate ───
    agg = defaultdict(lambda: defaultdict(lambda: {"tested": 0, "fixed": 0}))
    for r in results:
        a = agg[r["skill_id"]][r["task_type"]]
        a["tested"] += 1
        a["fixed"] += int(r["fixed"])

    # ─── Print summary ───
    md = ["# SKILLS v2 — Per-Skill Validation Results",
          f"\nModel: `{MODEL_NAME}`  ·  Workers: {N_WORKERS}  ·  "
          f"Cases: {total}  ·  Time: {elapsed:.1f}s\n",
          "Each skill was tested ONLY on error cases from its own target "
          "task_types (cases where vanilla model was already wrong).\n",
          "**fix-rate** = fraction of previously-wrong cases that the skill "
          "now answers correctly.\n",
          "\n## Per-skill / per-task-type fix rates\n",
          "| Skill | Task Type | Tested | Fixed | Fix Rate |",
          "|---|---|---:|---:|---:|"]

    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    overall_t = overall_f = 0
    for sid in SKILLS:
        per_tt = agg[sid]
        sid_t = sum(v["tested"] for v in per_tt.values())
        sid_f = sum(v["fixed"]  for v in per_tt.values())
        overall_t += sid_t; overall_f += sid_f
        print(f"\n[{sid}]  total: fixed {sid_f}/{sid_t} "
              f"({sid_f/sid_t*100 if sid_t else 0:.1f}%)")
        for tt in sorted(per_tt):
            v = per_tt[tt]
            r = v["fixed"]/v["tested"]*100 if v["tested"] else 0
            print(f"  {tt:48s}  {v['fixed']:3d}/{v['tested']:3d}  ({r:5.1f}%)")
            md.append(f"| {sid} | {tt} | {v['tested']} | {v['fixed']} | "
                      f"{r:.1f}% |")
        md.append(f"| **{sid} TOTAL** | — | **{sid_t}** | **{sid_f}** | "
                  f"**{sid_f/sid_t*100 if sid_t else 0:.1f}%** |")

    print(f"\nOVERALL: fixed {overall_f}/{overall_t} "
          f"({overall_f/overall_t*100 if overall_t else 0:.1f}%)")
    md.append(f"\n## Overall: fixed **{overall_f}/{overall_t}** "
              f"({overall_f/overall_t*100 if overall_t else 0:.1f}%)\n")

    # Save raw + summary
    out = {
        "config": {
            "model": MODEL_NAME, "workers": N_WORKERS,
            "max_per_task_type": MAX_PER_TASK_TYPE,
            "elapsed_sec": elapsed,
        },
        "summary": {sid: dict(tt) for sid, tt in agg.items()},
        "raw": results,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"\nSaved: {OUT_JSON}\nSaved: {OUT_MD}")


if __name__ == "__main__":
    main()
