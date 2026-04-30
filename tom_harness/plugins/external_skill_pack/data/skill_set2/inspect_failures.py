"""Round-2 failure inspection: Spatial Construction, Discrepant intentions,
Scalar Implicature.  Re-run with full reasoning capture."""
import json
import os
import sys
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
from llm_router import build_router_prompt, parse_router_choice, get_skill_prompt

TASK_TO_SKILL = {tt: sid for sid, tts in SKILL_TARGETS.items() for tt in tts}

ERRORS = []
for ds in ("ToMBench", "CogToM"):
    for line in open(os.path.join(DATA, f"{ds}.jsonl")):
        ERRORS.append(json.loads(line))
ERR_BY_IDX = {e["global_idx"]: e for e in ERRORS}

ROUTED = json.load(open(os.path.join(RESULTS, "routed_results.json")))["raw"]

groups = {
    # 1) Spatial Construction Task — only 6.7% routed fix rate, all routed correctly
    "Spatial_unfixed": [r for r in ROUTED
                        if r["task_type"] == "Spatial Construction Task"
                        and not r["fixed"]][:8],
    # 2) Discrepant intentions — 33.3%
    "DiscrepantIntent_unfixed": [r for r in ROUTED
                                  if r["task_type"] == "Discrepant intentions"
                                  and not r["fixed"]][:6],
    # 3) Scalar Implicature Test (ToMBench) — 23.3%
    "ScalarTest_unfixed": [r for r in ROUTED
                           if r["task_type"] == "Scalar Implicature Test"
                           and not r["fixed"]][:8],
    # also CogToM Scalar
    "ScalarTask_unfixed": [r for r in ROUTED
                           if r["task_type"] == "Scalar Implicature Task"
                           and not r["fixed"]][:6],
}

print("Group sizes:")
for k, v in groups.items():
    print(f"  {k}: {len(v)}")

model = load_model("gpt-5.4-mini")
_lock = Lock()
_done = {"n": 0}


def rerun(rec):
    item = ERR_BY_IDX[rec["global_idx"]]
    out = {
        "group":        rec["__group"],
        "global_idx":   item["global_idx"],
        "task_type":    item["task_type"],
        "oracle_skill": rec["oracle_skill"],
        "router_pick":  rec["router_pick"],
        "story":        item["story"],
        "question":     item["question"],
        "options":      dict(zip(item["labels"], item["options"])),
        "gold":         item["gold_answer"],
        "vanilla_pred": item.get("gpt_5_4_mini", {}).get("predicted"),
    }
    # full router resp
    rp = build_router_prompt(item["story"], item["question"],
                             item["options"], item["labels"])
    try:
        rresp = model.interact(rp, max_tokens=256)
    except Exception as e:
        rresp = f"<err: {e}>"
    out["router_full_resp"] = rresp
    chosen = parse_router_choice(rresp) or "NONE"
    out["router_pick_now"] = chosen

    # full answer with router-chosen skill
    try:
        skill_text = get_skill_prompt(chosen)
        base = build_vanilla_prompt(item["story"], item["question"],
                                    item["options"], item["labels"])
        ap = base if not skill_text else (
            "You are answering a Theory-of-Mind multiple-choice question.\n"
            "Apply the following strategy carefully, then answer.\n\n"
            f"=== STRATEGY ===\n{skill_text}\n=== END STRATEGY ===\n\n"
            f"=== QUESTION ===\n{base}"
        )
        aresp = model.interact(ap, max_tokens=2048)
    except Exception as e:
        aresp = f"<err: {e}>"
    out["answer_full_resp"] = aresp
    out["pred_now"] = extract_answer_letter(aresp, item["labels"])
    out["fixed_now"] = (out["pred_now"] == out["gold"])

    # also try with oracle skill
    try:
        oskill = get_skill_prompt(rec["oracle_skill"])
        if oskill:
            ap2 = (
                "You are answering a Theory-of-Mind multiple-choice question.\n"
                "Apply the following strategy carefully, then answer.\n\n"
                f"=== STRATEGY ===\n{oskill}\n=== END STRATEGY ===\n\n"
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
        print(f"  [{_done['n']:2d}] {item['global_idx']:14s} {item['task_type'][:28]:28s} "
              f"router={chosen:18s} pred={out['pred_now']} (gold={out['gold']}) "
              f"oracle={out.get('pred_oracle','-')}", flush=True)
    return out


tasks = []
for g, recs in groups.items():
    for r in recs:
        r2 = dict(r); r2["__group"] = g
        tasks.append(r2)

print(f"\nRe-running {len(tasks)} cases...")
results = []
with ThreadPoolExecutor(max_workers=16) as ex:
    futs = [ex.submit(rerun, r) for r in tasks]
    for f in as_completed(futs):
        results.append(f.result())

results.sort(key=lambda r: (r["group"], r["global_idx"]))

md = ["# Round-2 Failure inspection\n"]
for g in groups:
    grp = [r for r in results if r["group"] == g]
    md.append(f"\n## Group: `{g}`  ({len(grp)} cases)\n")
    for r in grp:
        md.append(f"### {r['global_idx']}   `{r['task_type']}`")
        md.append(f"- oracle skill: **{r['oracle_skill']}**")
        md.append(f"- vanilla pred: {r['vanilla_pred']}")
        md.append(f"- router picked: **{r['router_pick_now']}** (prev: {r['router_pick']})")
        md.append(f"- answered: **{r['pred_now']}** (gold = **{r['gold']}**) "
                  f"{'✓ FIXED' if r['fixed_now'] else '✗ wrong'}")
        if "pred_oracle" in r:
            md.append(f"- with ORACLE skill: pred = **{r['pred_oracle']}** "
                      f"{'✓ would-fix' if r.get('fixed_oracle') else '✗ still wrong'}")
        md.append("\n**Story**\n")
        md.append("> " + r['story'].replace("\n", " "))
        md.append("\n**Question:** " + r['question'].replace("\n", " "))
        md.append("\n**Options:**")
        for l, o in r['options'].items():
            md.append(f"- {l}. {o}")
        md.append("")
        md.append("**Router's full response:**\n```\n" + r["router_full_resp"] + "\n```\n")
        md.append("**Answer reasoning (router skill):**\n```\n" + r["answer_full_resp"] + "\n```\n")
        if "oracle_full_resp" in r:
            md.append("**Answer reasoning (ORACLE skill):**\n```\n" + r["oracle_full_resp"] + "\n```\n")
        md.append("\n---\n")

out_path = os.path.join(INSPECT, "FAILURE_INSPECTION_R2.md")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print(f"\nSaved {out_path}")

raw_path = os.path.join(INSPECT, "failure_inspection_r2.json")
with open(raw_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"Saved {raw_path}")
