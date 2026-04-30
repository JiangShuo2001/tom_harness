"""Pull actual failing cases for the four highest-ROI failure modes,
including full router & answer reasoning, so we can do targeted fixes."""
import json
import os
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RESULTS = os.path.join(DATA, "results")
INSPECT = os.path.join(DATA, "inspections")
PERCEP = os.path.abspath(os.path.join(HERE, "..", "PercepToM"))
sys.path.insert(0, HERE)
sys.path.insert(0, PERCEP)
os.makedirs(INSPECT, exist_ok=True)

from llm_agents import load_model
from eval_new_benchmarks import build_vanilla_prompt, extract_answer_letter
from skills import SKILLS, SKILL_TARGETS
from llm_router import (
    build_router_prompt, parse_router_choice, get_skill_prompt,
)

TASK_TO_SKILL = {tt: sid for sid, tts in SKILL_TARGETS.items() for tt in tts}

ERRORS = []
for ds in ("ToMBench", "CogToM"):
    for line in open(os.path.join(DATA, f"{ds}.jsonl")):
        ERRORS.append(json.loads(line))
ERR_BY_IDX = {e["global_idx"]: e for e in ERRORS}

# Load previous routed results to find which were wrong
ROUTED = json.load(open(os.path.join(RESULTS, "routed_results.json")))["raw"]
ROUTED_BY_IDX = {r["global_idx"]: r for r in ROUTED}


# ─── Pick failure groups ───
def in_oracle(skill):  # all cases whose oracle == skill
    return [r for r in ROUTED if r["oracle_skill"] == skill]


groups = {
    # 1) S5 cases routed to S11 (50 cases, biggest confusion)
    "S5→S11_confusion": [r for r in ROUTED
                          if r["oracle_skill"] == "S5_Expectation"
                          and r["router_pick"] == "S11_BeliefEmotion"][:8],
    # 2) Discrepant desires NOT fixed (S8 selected but failed)
    "S8_DiscrepantDesires_unfixed": [r for r in ROUTED
                                     if r["task_type"] == "Discrepant desires"
                                     and not r["fixed"]][:8],
    # 3) Moral emotions all 10 unfixed
    "S11_MoralEmotions_unfixed":   [r for r in ROUTED
                                    if r["task_type"] == "Moral emotions"
                                    and not r["fixed"]][:8],
    # 4) ToMBench False Belief 0/12
    "S3_FBT_TomBench_unfixed":     [r for r in ROUTED
                                    if r["task_type"] == "False Belief Task"
                                    and not r["fixed"]][:8],
}

print("Group sizes:")
for k, v in groups.items():
    print(f"  {k}: {len(v)}")

# For each failing case, RE-RUN with FULL reasoning captured (no truncation)
model = load_model("gpt-5.4-mini")
_lock = Lock()
_done = {"n": 0}


def rerun_one(rec):
    item = ERR_BY_IDX[rec["global_idx"]]
    out = {
        "group": rec["__group"],
        "global_idx": item["global_idx"],
        "task_type": item["task_type"],
        "oracle_skill": rec["oracle_skill"],
        "router_pick": rec["router_pick"],
        "story": item["story"],
        "question": item["question"],
        "options": dict(zip(item["labels"], item["options"])),
        "gold": item["gold_answer"],
        "vanilla_pred": item.get("gpt_5_4_mini", {}).get("predicted"),
    }

    # 1) full router response
    rp = build_router_prompt(item["story"], item["question"],
                             item["options"], item["labels"])
    try:
        rresp = model.interact(rp, max_tokens=256)
    except Exception as e:
        rresp = f"<err: {e}>"
    out["router_full_resp"] = rresp
    chosen = parse_router_choice(rresp) or "NONE"
    out["router_pick_now"] = chosen

    # 2) full answer with the skill the LLM actually picked
    try:
        skill_text = get_skill_prompt(chosen)
        base = build_vanilla_prompt(item["story"], item["question"],
                                    item["options"], item["labels"])
        if skill_text:
            ap = (
                "You are answering a Theory-of-Mind multiple-choice question.\n"
                "Apply the following strategy carefully, then answer.\n\n"
                f"=== STRATEGY ===\n{skill_text}\n=== END STRATEGY ===\n\n"
                f"=== QUESTION ===\n{base}"
            )
        else:
            ap = base
        aresp = model.interact(ap, max_tokens=2048)
    except Exception as e:
        aresp = f"<err: {e}>"
    out["answer_full_resp"] = aresp
    out["pred_now"] = extract_answer_letter(aresp, item["labels"])
    out["fixed_now"] = (out["pred_now"] == out["gold"])

    # 3) ALSO try with ORACLE skill (so we can see if oracle would have helped)
    try:
        oracle_skill = get_skill_prompt(rec["oracle_skill"])
        if oracle_skill:
            ap2 = (
                "You are answering a Theory-of-Mind multiple-choice question.\n"
                "Apply the following strategy carefully, then answer.\n\n"
                f"=== STRATEGY ===\n{oracle_skill}\n=== END STRATEGY ===\n\n"
                f"=== QUESTION ===\n{base}"
            )
            aresp2 = model.interact(ap2, max_tokens=2048)
            out["oracle_full_resp"] = aresp2
            out["pred_oracle"] = extract_answer_letter(aresp2, item["labels"])
            out["fixed_oracle"] = (out["pred_oracle"] == out["gold"])
    except Exception as e:
        out["oracle_full_resp"] = f"<err: {e}>"

    with _lock:
        _done["n"] += 1
        print(f"  [{_done['n']}] {item['global_idx']} {item['task_type'][:30]}  "
              f"router_now={chosen}  pred_now={out['pred_now']} (gold={out['gold']})  "
              f"oracle_pred={out.get('pred_oracle','-')}",
              flush=True)
    return out


tasks = []
for g, recs in groups.items():
    for r in recs:
        r2 = dict(r); r2["__group"] = g
        tasks.append(r2)

print(f"\nRe-running {len(tasks)} cases with full reasoning capture...")
results = []
with ThreadPoolExecutor(max_workers=16) as ex:
    futs = [ex.submit(rerun_one, r) for r in tasks]
    for f in as_completed(futs):
        results.append(f.result())

# Group & write to MD for inspection
results.sort(key=lambda r: (r["group"], r["global_idx"]))
md = ["# Failure-mode inspection\n"]
for g in groups:
    grp = [r for r in results if r["group"] == g]
    md.append(f"\n## Group: `{g}`  ({len(grp)} cases)\n")
    for r in grp:
        md.append(f"### {r['global_idx']}   task_type=`{r['task_type']}`")
        md.append(f"- oracle skill : **{r['oracle_skill']}**")
        md.append(f"- vanilla pred : {r['vanilla_pred']}")
        md.append(f"- router picked: **{r['router_pick_now']}** "
                  f"(prev run: {r['router_pick']})")
        md.append(f"- answered     : **{r['pred_now']}**  "
                  f"(gold = **{r['gold']}**)  "
                  f"{'✓ FIXED' if r['fixed_now'] else '✗ wrong'}")
        if "pred_oracle" in r:
            md.append(f"- with ORACLE skill: pred = **{r['pred_oracle']}**  "
                      f"{'✓ would-fix' if r.get('fixed_oracle') else '✗ still wrong'}")
        md.append("")
        md.append("**Story**\n")
        md.append("> " + r['story'].replace("\n", " "))
        md.append("\n**Question:** " + r['question'].replace("\n", " "))
        md.append("\n**Options:**")
        for l, o in r["options"].items():
            md.append(f"- {l}. {o}")
        md.append("")
        md.append("**Router's full response (after seeing case):**\n")
        md.append("```\n" + r["router_full_resp"] + "\n```\n")
        md.append("**Answerer's reasoning (with router's chosen skill):**\n")
        md.append("```\n" + r["answer_full_resp"] + "\n```\n")
        if "oracle_full_resp" in r:
            md.append("**Answerer's reasoning (with ORACLE skill):**\n")
            md.append("```\n" + r["oracle_full_resp"] + "\n```\n")
        md.append("\n---\n")

out_path = os.path.join(INSPECT, "FAILURE_INSPECTION.md")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print(f"\nSaved {out_path}")

raw_path = os.path.join(INSPECT, "failure_inspection_raw.json")
with open(raw_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"Saved {raw_path}")
