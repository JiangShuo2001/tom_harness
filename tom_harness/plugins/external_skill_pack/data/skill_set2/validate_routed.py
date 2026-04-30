"""
End-to-end validation of LLM-routed skills.

For each error case (across all task_types covered by SKILL_TARGETS):
  call#1: LLM router  → predicted skill_id (no task_type given)
  call#2: model + chosen skill prompt → final answer

Both calls run inside one big ThreadPoolExecutor.

Reports:
  • routing accuracy : router pick == oracle skill (from SKILL_TARGETS)
  • final fix rate   : final answer == gold (the case was originally wrong)
  • per-task-type / per-router-choice breakdowns
  • confusion matrix : oracle_skill × router_pick

Comparable baseline: the static-routing run produced 248/534 = 46.4% fix-rate.
"""
import json
import os
import sys
import time
from collections import defaultdict, Counter
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
from llm_router import (                                          # noqa
    build_router_prompt, parse_router_choice, get_skill_prompt, VALID_IDS,
)


MODEL_NAME = os.environ.get("V2_MODEL", "gpt-5.4-mini")
ROUTER_MODEL_NAME = os.environ.get("V2_ROUTER_MODEL", MODEL_NAME)
MAX_PER_TASK_TYPE = int(os.environ.get("V2_MAX_PER_TT", "30"))
N_WORKERS = int(os.environ.get("V2_WORKERS", "32"))

os.makedirs(RESULTS, exist_ok=True)
ERROR_FILES = {
    "ToMBench": os.path.join(DATA, "ToMBench.jsonl"),
    "CogToM":   os.path.join(DATA, "CogToM.jsonl"),
}
OUT_JSON = os.path.join(RESULTS, "routed_results.json")
OUT_MD   = os.path.join(RESULTS, "ROUTED_RESULTS.md")


# Oracle: task_type → ground-truth skill_id (from SKILL_TARGETS)
TASK_TO_SKILL = {tt: sid for sid, tts in SKILL_TARGETS.items() for tt in tts}


# ───────────────────── Data loading ─────────────────────
def load_all_targeted_errors():
    """Collect error cases from every task_type covered by SKILL_TARGETS,
    capping per (dataset, task_type) at MAX_PER_TASK_TYPE.  Returns a flat list."""
    out = []
    for ds, path in ERROR_FILES.items():
        per_tt = defaultdict(list)
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                if r["task_type"] in TASK_TO_SKILL:
                    per_tt[r["task_type"]].append(r)
        for tt, items in per_tt.items():
            out.extend(items[:MAX_PER_TASK_TYPE])
    return out


# ───────────────────── Per-case pipeline ─────────────────────
_print_lock = Lock()
_progress = {"done": 0, "total": 0}


def build_skilled_prompt(item, skill_text):
    base = build_vanilla_prompt(
        item["story"], item["question"], item["options"], item["labels"]
    )
    if skill_text is None:
        return base
    return (
        f"You are answering a Theory-of-Mind multiple-choice question.\n"
        f"Apply the following strategy carefully, then answer.\n\n"
        f"=== STRATEGY ===\n{skill_text}\n=== END STRATEGY ===\n\n"
        f"=== QUESTION ===\n{base}"
    )


def run_one(router_model, ans_model, item, total):
    oracle = TASK_TO_SKILL[item["task_type"]]
    rec = {
        "global_idx":   item["global_idx"],
        "dataset":      item["dataset"],
        "task_type":    item["task_type"],
        "oracle_skill": oracle,
        "gold":         item["gold_answer"],
        "vanilla_pred": item.get("gpt_5_4_mini", {}).get("predicted"),
    }
    # ─── call#1: routing
    try:
        rprompt = build_router_prompt(
            item["story"], item["question"], item["options"], item["labels"]
        )
        rresp = router_model.interact(rprompt, max_tokens=64)
        chosen = parse_router_choice(rresp) or "NONE"
    except Exception as e:
        chosen = "NONE"
        rresp = f"<router-error: {e}>"
    rec["router_pick"]  = chosen
    rec["router_match"] = (chosen == oracle)
    rec["router_resp_head"] = (rresp or "")[:120]

    # ─── call#2: answering with chosen skill
    try:
        skill_text = get_skill_prompt(chosen)  # None if NONE
        prompt = build_skilled_prompt(item, skill_text)
        aresp = ans_model.interact(prompt, max_tokens=2048)
        pred = extract_answer_letter(aresp, item["labels"])
    except Exception as e:
        pred = None
        aresp = f"<answer-error: {e}>"
    rec["skilled_pred"] = pred
    rec["fixed"]        = (pred == item["gold_answer"])
    rec["answer_resp_tail"] = (aresp or "")[-200:]

    with _print_lock:
        _progress["done"] += 1
        if _progress["done"] % 20 == 0 or _progress["done"] == total:
            tag = "FIX" if rec["fixed"] else "   "
            ok  = "✓" if rec["router_match"] else "✗"
            print(f"  [{_progress['done']:4d}/{total}] "
                  f"router={chosen:18s} (oracle={oracle:18s} {ok}) "
                  f"gold={item['gold_answer']} pred={pred} {tag}",
                  flush=True)
    return rec


def main():
    items = load_all_targeted_errors()
    total = len(items)
    _progress["total"] = total

    print(f"[routed-v2] router_model={ROUTER_MODEL_NAME}  ans_model={MODEL_NAME}",
          flush=True)
    print(f"[routed-v2] workers={N_WORKERS}  cases={total}  "
          f"(2 LLM calls per case ⇒ {2*total} total)", flush=True)
    counts = Counter(it["task_type"] for it in items)
    for tt, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"   {n:4d}  {tt}  →  oracle: {TASK_TO_SKILL[tt]}",
              flush=True)

    router_model = load_model(ROUTER_MODEL_NAME)
    ans_model = load_model(MODEL_NAME) if MODEL_NAME != ROUTER_MODEL_NAME \
        else router_model

    t0 = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futures = [ex.submit(run_one, router_model, ans_model, it, total)
                   for it in items]
        for f in as_completed(futures):
            results.append(f.result())
    elapsed = time.time() - t0

    # ─── Aggregate ───
    n_routed_correct  = sum(r["router_match"] for r in results)
    n_routed_to_none  = sum(r["router_pick"] == "NONE" for r in results)
    n_fixed           = sum(r["fixed"] for r in results)

    # confusion: oracle × router_pick
    confusion = defaultdict(Counter)
    for r in results:
        confusion[r["oracle_skill"]][r["router_pick"]] += 1

    # per-task_type fix rate
    per_tt = defaultdict(lambda: {"tested": 0, "fixed": 0,
                                  "routed_correct": 0})
    for r in results:
        a = per_tt[r["task_type"]]
        a["tested"] += 1
        a["fixed"]  += int(r["fixed"])
        a["routed_correct"] += int(r["router_match"])

    # per-router-pick fix rate (how good is each chosen skill at fixing the case
    # the router routed to it? regardless of oracle)
    per_pick = defaultdict(lambda: {"picked": 0, "fixed": 0})
    for r in results:
        p = per_pick[r["router_pick"]]
        p["picked"] += 1
        p["fixed"]  += int(r["fixed"])

    # ─── Print summary ───
    print("\n" + "=" * 80)
    print(f"OVERALL  ({elapsed:.1f}s)")
    print("=" * 80)
    print(f"  Cases:                {total}")
    print(f"  Routing accuracy:     {n_routed_correct}/{total}  "
          f"({n_routed_correct/total*100:.1f}%)")
    print(f"  Routed to NONE:       {n_routed_to_none}/{total}  "
          f"({n_routed_to_none/total*100:.1f}%)")
    print(f"  Final fix rate:       {n_fixed}/{total}  "
          f"({n_fixed/total*100:.1f}%)")

    print("\n--- Per task_type ---")
    print(f"  {'Task type':46s} {'tested':>7} {'route✓':>7} {'fixed':>7} {'fix%':>7}")
    for tt in sorted(per_tt):
        v = per_tt[tt]
        rrate = v["routed_correct"]/v["tested"]*100
        frate = v["fixed"]/v["tested"]*100
        print(f"  {tt:46s} {v['tested']:7d} {v['routed_correct']:7d} "
              f"{v['fixed']:7d} {frate:6.1f}%   (route {rrate:.0f}%)")

    print("\n--- Per router-pick (how often picked, how often it then fixed) ---")
    for pick in VALID_IDS:
        v = per_pick.get(pick, {"picked": 0, "fixed": 0})
        if v["picked"] == 0:
            continue
        frate = v["fixed"]/v["picked"]*100
        print(f"  {pick:20s} picked {v['picked']:4d}  fixed {v['fixed']:4d}  "
              f"({frate:5.1f}%)")

    print("\n--- Confusion: oracle × router_pick ---")
    cols = VALID_IDS
    header = "  oracle\\router       " + " ".join(f"{c[:6]:>7}" for c in cols)
    print(header)
    for ora in [s for s in VALID_IDS if s != "NONE"]:
        row = " ".join(f"{confusion[ora].get(c, 0):>7d}" for c in cols)
        print(f"  {ora:20s}{row}")

    # ─── MD output ───
    md = []
    md.append("# SKILLS v2 — LLM-Routed End-to-End Validation\n")
    md.append(f"Router: `{ROUTER_MODEL_NAME}`  ·  Answerer: `{MODEL_NAME}`  "
              f"·  Cases: {total}  ·  Workers: {N_WORKERS}  ·  "
              f"Time: {elapsed:.1f}s\n")
    md.append(f"- **Routing accuracy:** {n_routed_correct}/{total} = "
              f"**{n_routed_correct/total*100:.1f}%**")
    md.append(f"- **Routed to NONE:**   {n_routed_to_none}/{total} = "
              f"{n_routed_to_none/total*100:.1f}%")
    md.append(f"- **End-to-end fix rate:** {n_fixed}/{total} = "
              f"**{n_fixed/total*100:.1f}%**\n")
    md.append("> Static-routing baseline (oracle): **248/534 = 46.4%**\n")

    md.append("## Per task_type")
    md.append("| Task Type | Oracle Skill | Tested | Router✓ | Route Acc | Fixed | Fix Rate |")
    md.append("|---|---|---:|---:|---:|---:|---:|")
    for tt in sorted(per_tt):
        v = per_tt[tt]
        md.append(f"| {tt} | {TASK_TO_SKILL[tt]} | {v['tested']} | "
                  f"{v['routed_correct']} | "
                  f"{v['routed_correct']/v['tested']*100:.1f}% | {v['fixed']} | "
                  f"{v['fixed']/v['tested']*100:.1f}% |")

    md.append("\n## Per router-pick")
    md.append("| Router Pick | Picked | Fixed | Fix Rate when picked |")
    md.append("|---|---:|---:|---:|")
    for pick in VALID_IDS:
        v = per_pick.get(pick, {"picked": 0, "fixed": 0})
        if v["picked"] == 0:
            continue
        md.append(f"| {pick} | {v['picked']} | {v['fixed']} | "
                  f"{v['fixed']/v['picked']*100:.1f}% |")

    md.append("\n## Confusion: oracle × router_pick")
    md.append("| oracle \\ router | " + " | ".join(VALID_IDS) + " |")
    md.append("|---" * (len(VALID_IDS) + 1) + "|")
    for ora in [s for s in VALID_IDS if s != "NONE"]:
        row = " | ".join(str(confusion[ora].get(c, 0)) for c in VALID_IDS)
        md.append(f"| {ora} | {row} |")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    out = {
        "config": {
            "router_model": ROUTER_MODEL_NAME,
            "answer_model": MODEL_NAME,
            "workers": N_WORKERS,
            "max_per_task_type": MAX_PER_TASK_TYPE,
            "elapsed_sec": elapsed,
        },
        "summary": {
            "total": total,
            "routing_accuracy": n_routed_correct,
            "routed_to_none":   n_routed_to_none,
            "fix_rate":         n_fixed,
        },
        "per_task_type": {tt: dict(v) for tt, v in per_tt.items()},
        "per_router_pick": {p: dict(v) for p, v in per_pick.items()},
        "confusion": {ora: dict(c) for ora, c in confusion.items()},
        "raw": results,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\nSaved: {OUT_JSON}\nSaved: {OUT_MD}")


if __name__ == "__main__":
    main()
