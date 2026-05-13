"""Per-(dataset, model) skill-fix-rate experiment for SKILLS v4.

Runs the v4 router + the 22-skill SKILL.md library on benchmark cases
where an answerer model was originally wrong, then reports how often the
skill-guided retry fixes the answer.

For each configured (dataset, answerer-model) combination:
  - filter error cases where the answerer model was originally wrong
  - LLM router chooses a skill from the raw input
  - Answerer (the model under test) re-answers with the chosen skill prompt
  - Report fix rates broken down by `ability` and `task_type`

Configure with environment variables such as EXP_ROUTER,
EXP_ANSWERERS, EXP_DATASETS, and EXP_DATASET_FILES.

Outputs land under a new run directory inside
`skills_v4/data/results/per_model/` by default.
"""
import json
import os
import re
import sys
import time
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT_BASE = os.path.join(DATA, "results", "per_model")
RUN_ID = os.environ.get("EXP_RUN_ID", "").strip() or time.strftime("run_%Y%m%d_%H%M%S")
OUT = os.path.join(OUT_BASE, RUN_ID)
sys.path.insert(0, HERE)
os.makedirs(OUT, exist_ok=True)

from llm_agents import load_model, GPTAgent                          # noqa
from eval_new_benchmarks import build_vanilla_prompt, extract_answer_letter  # noqa
from llm_router import (                                              # noqa
    build_router_prompt, parse_router_choice, get_skill_prompt, VALID_IDS,
    ROUTER_GUIDE_MODE, ALLOW_NONE,
)


# ─────────────────── Saner retry/timeout for big runs ───────────────────
import requests as _requests   # noqa: E402

EXP_HTTP_TIMEOUT = int(os.environ.get("EXP_HTTP_TIMEOUT", "120"))
EXP_MAX_RETRIES  = int(os.environ.get("EXP_MAX_RETRIES",  "5"))
EXP_REASONING_EFFORT = os.environ.get("EXP_REASONING_EFFORT", "").strip()


def _patched_interact(self, prompt, max_tokens=2048):
    is_reasoning_model = any(t in self.model_name for t in ["glm-5", "o1", "o3", "o4"])
    eff = max(max_tokens, 4000) if is_reasoning_model else max_tokens
    last_err = None
    for attempt in range(EXP_MAX_RETRIES):
        try:
            data = {
                "model":    self.model_name,
                "stream":   False,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens":  eff,
                "top_p":       1.0,
                "temperature": 0.0,
            }
            if is_reasoning_model and EXP_REASONING_EFFORT and EXP_REASONING_EFFORT.lower() not in {"0", "false", "none", "off"}:
                data["reasoning"] = {"effort": EXP_REASONING_EFFORT}
            r = _requests.post(self.url, headers=self.headers, json=data,
                               timeout=EXP_HTTP_TIMEOUT)
            if r.status_code == 200:
                msg = r.json()["choices"][0]["message"]
                return (msg.get("content") or msg.get("reasoning") or "").strip()
            if r.status_code == 429:
                time.sleep(5 + 2 * attempt); last_err = f"429 try={attempt}"; continue
            last_err = f"HTTP {r.status_code}: {r.text[:120]}"
            time.sleep(2)
        except _requests.exceptions.Timeout:
            last_err = f"timeout after {EXP_HTTP_TIMEOUT}s try={attempt}"
            time.sleep(2)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            time.sleep(2)
    raise RuntimeError(f"GPT generation failed: {last_err}")


GPTAgent.interact = _patched_interact

ROUTER_MODEL = os.environ.get("EXP_ROUTER", "gpt-5.4-mini")
ANSWERER_MODELS = os.environ.get("EXP_ANSWERERS", "gpt-5.4-mini,glm-5").split(",")
DATASETS = [x.strip() for x in os.environ.get("EXP_DATASETS", "ToMBench,CogToM").split(",") if x.strip()]
DATASET_FILES = {}
for spec in os.environ.get("EXP_DATASET_FILES", "").split(","):
    spec = spec.strip()
    if not spec:
        continue
    if "=" not in spec:
        raise ValueError("EXP_DATASET_FILES entries must look like Dataset=file.jsonl")
    ds_name, filename = spec.split("=", 1)
    DATASET_FILES[ds_name.strip()] = filename.strip()
N_WORKERS = int(os.environ.get("EXP_WORKERS", "32"))
ANSWER_MAX_TOKENS = int(os.environ.get("EXP_ANSWER_TOKENS", "8192"))

# IDENTICAL to v2's guard so the comparison is apples-to-apples.
ANSWER_FORMAT_GUARD = (
    "OUTPUT FORMAT (mandatory):\n"
    "1. Your VERY FIRST line must be exactly `ANSWER: <letter>` — your best\n"
    "   guess based on a fast read. This protects against truncation.\n"
    "2. Then perform the strategy/reasoning steps.\n"
    "3. End with exactly one line: `FINAL ANSWER: <letter>`.\n"
    "If steps 2-3 lead you to revise step 1, the FINAL ANSWER line wins.\n"
    "Use only one of the provided option letters."
)


EXP_OFFSET = int(os.environ.get("EXP_OFFSET", "0"))
EXP_LIMIT = int(os.environ.get("EXP_LIMIT", "0"))   # 0 = no cap after offset


# ─────────────────────── Loading ───────────────────────
def load_dataset(ds):
    out = []
    filename = DATASET_FILES.get(ds, f"{ds}.jsonl")
    with open(os.path.join(DATA, filename), encoding="utf-8") as f:
        for line in f:
            out.append(json.loads(line))
    if EXP_OFFSET:
        out = out[EXP_OFFSET:]
    if EXP_LIMIT:
        out = out[:EXP_LIMIT]
    return out


# ───────────────────── Router pass ─────────────────────
_print_lock = Lock()
_progress = {"done": 0, "total": 0}


def _bump(label):
    with _print_lock:
        _progress["done"] += 1
        if _progress["done"] % 50 == 0 or _progress["done"] == _progress["total"]:
            print(f"  [{_progress['done']:5d}/{_progress['total']}] {label}", flush=True)


def route_one(model, item):
    # NOTE: pass options as a LIST aligned with labels (v4 router signature).
    # v2's experiment script accidentally passed a dict here; v4 fixes it.
    p = build_router_prompt(
        item["story"], item["question"], item["options"], item["labels"]
    )
    try:
        resp = model.interact(p, max_tokens=256)
        choice = parse_router_choice(resp)
        if choice is None:
            choice = "NONE"
    except Exception as e:
        choice, resp = "NONE", f"<route err: {e}>"
    _bump(f"route {item['global_idx']} → {choice}")
    return item["global_idx"], choice, resp


def run_router(items, label):
    model = load_model(ROUTER_MODEL)
    _progress["done"] = 0
    _progress["total"] = len(items)
    print(f"\n[{label}] routing {len(items)} cases with {ROUTER_MODEL} ...")
    out = {}
    raws = {}
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = [ex.submit(route_one, model, it) for it in items]
        for f in as_completed(futs):
            gid, choice, resp = f.result()
            out[gid] = choice
            raws[gid] = resp
    return out, raws


_FINAL_ANSWER_RE = re.compile(r"FINAL\s*ANSWER\s*[:\-]\s*\(?([A-Z])\)?", re.IGNORECASE)
_FIRST_ANSWER_RE = re.compile(r"^\s*ANSWER\s*[:\-]\s*\(?([A-Z])\)?", re.IGNORECASE | re.MULTILINE)


def robust_extract(resp, labels):
    if not resp:
        return None
    valid = set(labels)
    matches = _FINAL_ANSWER_RE.findall(resp)
    if matches:
        letter = matches[-1].upper()
        if letter in valid:
            return letter
    matches = _FIRST_ANSWER_RE.findall(resp)
    if matches:
        letter = matches[0].upper()
        if letter in valid:
            return letter
    return extract_answer_letter(resp, labels)


# ───────────────────── Answer pass ─────────────────────
def answer_one(model, item, skill_id):
    skill = get_skill_prompt(skill_id)
    base = build_vanilla_prompt(
        item["story"], item["question"], item["options"], item["labels"]
    )
    if skill:
        prompt = (
            "You are answering a Theory-of-Mind multiple-choice question.\n"
            "Apply the following strategy carefully, then answer.\n\n"
            f"=== STRATEGY ===\n{skill}\n=== END STRATEGY ===\n\n"
            f"=== QUESTION ===\n{base}\n\n"
            f"=== {ANSWER_FORMAT_GUARD}"
        )
    else:
        prompt = (
            f"{base}\n\n"
            f"=== {ANSWER_FORMAT_GUARD}"
        )
    try:
        resp = model.interact(prompt, max_tokens=ANSWER_MAX_TOKENS)
        pred = robust_extract(resp, item["labels"])
    except Exception as e:
        pred, resp = None, f"<answer err: {e}>"
    fixed = (pred == item["gold_answer"])
    _bump(f"answer {item['global_idx']} {skill_id:10s} → {pred} (gold={item['gold_answer']}) {'FIX' if fixed else '-'}")
    return {
        "global_idx":      item["global_idx"],
        "ability":         item["ability"],
        "task_type":       item["task_type"],
        "gold":            item["gold_answer"],
        "skill":           skill_id,
        "used_skill":      bool(skill),
        "skipped":         False,
        "pred":            pred,
        "fixed":           fixed,
        "answer_response": resp,
    }


def skipped_none_row(item):
    return {
        "global_idx":      item["global_idx"],
        "ability":         item["ability"],
        "task_type":       item["task_type"],
        "gold":            item["gold_answer"],
        "skill":           "NONE",
        "used_skill":      False,
        "skipped":         True,
        "pred":            None,
        "fixed":           False,
        "answer_response": "<skipped: router chose NONE; no skill prompt used>",
    }


def run_answerer(items, model_name, skill_map, label):
    todo = []
    rows = []
    for it in items:
        skill_id = skill_map.get(it["global_idx"], "NONE")
        if skill_id == "NONE":
            rows.append(skipped_none_row(it))
        else:
            todo.append((it, skill_id))

    _progress["done"] = 0
    _progress["total"] = len(todo)
    print(
        f"\n[{label}] answering {len(todo)} skill-routed cases with {model_name} "
        f"(skipping {len(rows)} NONE cases) ..."
    )
    if not todo:
        return rows

    model = load_model(model_name)
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = [
            ex.submit(answer_one, model, it, skill_id)
            for it, skill_id in todo
        ]
        for f in as_completed(futs):
            rows.append(f.result())
    return rows


# ───────────────────── Aggregation ─────────────────────
def summarise(rows, dim):
    bucket = defaultdict(lambda: {"n": 0, "answered": 0, "skipped": 0, "fix": 0})
    for r in rows:
        b = bucket[r[dim]]
        b["n"] += 1
        if r.get("skipped"):
            b["skipped"] += 1
        else:
            b["answered"] += 1
        if r["fixed"] and not r.get("skipped"):
            b["fix"] += 1
    out = []
    for k, v in bucket.items():
        rate = v["fix"] / v["answered"] if v["answered"] else 0.0
        coverage = v["answered"] / v["n"] if v["n"] else 0.0
        out.append((k, v["n"], v["answered"], v["skipped"], v["fix"], rate, coverage))
    out.sort(key=lambda x: (-x[5], -x[2], x[0]))
    return out


def write_dataset_md(ds, results, router_acc_info, skill_distribution):
    md = [f"# Skills v4 — per-model fix rates on `{ds}`\n",
          f"- Router: `{ROUTER_MODEL}` (fixed across both answerers)",
          f"- Cases routed: {router_acc_info['n_routed']}",
          f"- Routed to NONE: {router_acc_info['n_none']} "
          f"({router_acc_info['n_none']/max(1,router_acc_info['n_routed']):.1%})\n"]

    md.append("## Overall\n")
    md.append("| Answerer | Total Cases | Skill-Routed | Skipped NONE | Fixed | Skill Fix Rate | Coverage |")
    md.append("|---|---:|---:|---:|---:|---:|---:|")
    for m, rows in results.items():
        n = len(rows)
        answered = sum(1 for r in rows if not r.get("skipped"))
        skipped = sum(1 for r in rows if r.get("skipped"))
        fx = sum(r["fixed"] for r in rows if not r.get("skipped"))
        md.append(
            f"| `{m}` | {n} | {answered} | {skipped} | {fx} | "
            f"**{fx/max(1,answered):.1%}** | {answered/max(1,n):.1%} |"
        )

    md.append("\n## Router-pick distribution\n")
    md.append("| Skill | Picked | Share |")
    md.append("|---|---:|---:|")
    total_picks = sum(skill_distribution.values())
    for sid, cnt in sorted(skill_distribution.items(), key=lambda x: -x[1]):
        md.append(f"| {sid} | {cnt} | {cnt/max(1,total_picks):.1%} |")

    for dim in ("ability", "task_type"):
        md.append(f"\n## Per `{dim}` fix rates\n")
        all_keys = sorted({r[dim] for rows in results.values() for r in rows})
        head = "| " + dim + " | " + " | ".join(
            f"{m} total | {m} routed | {m} skipped | {m} fixed | {m} skill-fix-rate"
            for m in results
        ) + " |"
        sep = "|---|" + ("---:|---:|---:|---:|---:|" * len(results))
        md.append(head); md.append(sep)
        per = {m: {k: [0, 0, 0, 0] for k in all_keys} for m in results}
        for m, rows in results.items():
            for r in rows:
                per[m][r[dim]][0] += 1  # total
                if r.get("skipped"):
                    per[m][r[dim]][2] += 1
                else:
                    per[m][r[dim]][1] += 1
                    if r["fixed"]:
                        per[m][r[dim]][3] += 1
        for k in all_keys:
            cells = []
            for m in results:
                n, answered, skipped, fx = per[m][k]
                rate = f"{fx/answered:.1%}" if answered else "—"
                cells += [str(n), str(answered), str(skipped), str(fx), f"**{rate}**" if answered else "—"]
            md.append(f"| {k} | " + " | ".join(cells) + " |")

    return "\n".join(md) + "\n"


# Reference: v2 headline numbers (from
# `papers/skill_v2/data/results/per_model/HEADLINE.md`).
V2_BASELINE = {
    ("ToMBench", "gpt-5.4-mini"): (592, 180),
    ("ToMBench", "glm-5"):        (428, 152),
    ("CogToM",   "gpt-5.4-mini"): (444, 174),
    ("CogToM",   "glm-5"):        (207,  82),
}


def write_comparison_md(summary, t0):
    head = ["# Skills v4 — per (dataset × model) fix rates  ·  vs v2 baseline\n",
            f"Router: `{ROUTER_MODEL}`  ·  Answerers: {ANSWERER_MODELS}",
            f"Total elapsed: {time.time()-t0:.1f}s",
            f"v2 baseline source: `papers/skill_v2/data/results/per_model/HEADLINE.md`\n",
            "## Headline\n",
            "| Dataset | Answerer | Total Cases | Skill-Routed | Skipped NONE | v2 fixed | v2 fix-rate | v4 fixed | v4 skill-fix-rate | Coverage | Δ |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for ds in DATASETS:
        for m in ANSWERER_MODELS:
            m = m.strip()
            rows = summary[ds][m]
            n = len(rows)
            answered = sum(1 for r in rows if not r.get("skipped"))
            skipped = sum(1 for r in rows if r.get("skipped"))
            fx = sum(r["fixed"] for r in rows if not r.get("skipped"))
            v2_n, v2_fx = V2_BASELINE.get((ds, m), (0, 0))
            v4_rate = fx / max(1, answered)
            v2_rate = v2_fx / max(1, v2_n)
            delta_pp = (v4_rate - v2_rate) * 100
            sign = "+" if delta_pp >= 0 else ""
            head.append(
                f"| {ds} | `{m}` | {n} | {answered} | {skipped} | {v2_fx} | "
                f"**{v2_rate:.1%}** | {fx} | **{v4_rate:.1%}** | "
                f"{answered/max(1,n):.1%} | **{sign}{delta_pp:.1f}pp** |"
            )
    head.append("\nSee per-dataset breakdowns:\n")
    for ds in DATASETS:
        head.append(f"- [`{ds}__per_model.md`](./{ds}__per_model.md)")
    return "\n".join(head) + "\n"


# ───────────────────── Main ─────────────────────
def main():
    t0 = time.time()
    summary = {}
    skill_maps = {}
    router_raws = {}
    print(f"Writing results to {OUT}")
    print(f"Router guide mode: {ROUTER_GUIDE_MODE}; allow NONE: {ALLOW_NONE}")
    print(f"Dataset slice: offset={EXP_OFFSET}; limit={EXP_LIMIT or 'all'}")

    for ds in DATASETS:
        items = load_dataset(ds)
        skill_map, raw = run_router(items, label=f"{ds}/router")
        skill_maps[ds] = skill_map
        router_raws[ds] = raw

        n_none = sum(1 for v in skill_map.values() if v == "NONE")
        router_acc_info = {"n_routed": len(items), "n_none": n_none}
        skill_distribution = Counter(skill_map.values())
        print(f"\n[{ds}] router-pick distribution:")
        for sid, cnt in sorted(skill_distribution.items(), key=lambda x: -x[1]):
            print(f"   {cnt:4d}  {sid}")

        per_model_rows = {}
        for mname in ANSWERER_MODELS:
            mname = mname.strip()
            wrong = [it for it in items if mname in it["wrong_by"]]
            print(f"\n=== {ds}  answerer={mname}  cases={len(wrong)} ===")
            rows = run_answerer(wrong, mname, skill_map, label=f"{ds}/{mname}")
            per_model_rows[mname] = rows

            json_path = os.path.join(OUT, f"{ds}__{mname.replace('.','_')}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                n_answered = sum(1 for r in rows if not r.get("skipped"))
                n_skipped = sum(1 for r in rows if r.get("skipped"))
                n_fixed = sum(r["fixed"] for r in rows if not r.get("skipped"))
                json.dump({
                    "dataset": ds,
                    "answerer": mname,
                    "router": ROUTER_MODEL,
                    "router_guide_mode": ROUTER_GUIDE_MODE,
                    "allow_none": ALLOW_NONE,
                    "n_cases": len(rows),
                    "n_answered": n_answered,
                    "n_skipped_none": n_skipped,
                    "n_fixed": n_fixed,
                    "skill_fix_rate": n_fixed / max(1, n_answered),
                    "coverage": n_answered / max(1, len(rows)),
                    "by_ability":   summarise(rows, "ability"),
                    "by_task_type": summarise(rows, "task_type"),
                    "rows": rows,
                }, f, ensure_ascii=False, indent=2)
            print(f"Saved {json_path}")

        md = write_dataset_md(ds, per_model_rows, router_acc_info, skill_distribution)
        md_path = os.path.join(OUT, f"{ds}__per_model.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Saved {md_path}")
        summary[ds] = per_model_rows

    md = write_comparison_md(summary, t0)
    with open(os.path.join(OUT, "HEADLINE.md"), "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Saved {os.path.join(OUT, 'HEADLINE.md')}")
    print(f"\nDone in {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    main()
