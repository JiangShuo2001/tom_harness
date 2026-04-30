"""Per-(dataset, model) skill-fix-rate experiment.

For each of the 4 (dataset, answerer-model) combinations:
  - filter error cases where the answerer model was originally wrong
  - LLM router (gpt-5.4-mini, fixed) chooses a skill from the raw input
  - Answerer (the model under test) re-answers with the chosen skill prompt
  - Report fix rates broken down by `ability` and `task_type`

Router decisions are cached per case (dataset-level) so glm-5 + gpt-5.4-mini
runs share the same router call set.

Outputs land under data/results/per_model/.
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
OUT = os.path.join(DATA, "results", "per_model")
PERCEP = os.path.abspath(os.path.join(HERE, "..", "PercepToM"))
sys.path.insert(0, HERE)
sys.path.insert(0, PERCEP)
os.makedirs(OUT, exist_ok=True)

from llm_agents import load_model, GPTAgent                          # noqa
from eval_new_benchmarks import build_vanilla_prompt, extract_answer_letter  # noqa
from skills import SKILLS, SKILL_TARGETS                              # noqa
from llm_router import (                                              # noqa
    build_router_prompt, parse_router_choice, get_skill_prompt, VALID_IDS,
)


# ─────────────────── Saner retry/timeout for big runs ───────────────────
# The shared GPTAgent does up to 30 retries × 300s timeout — a single
# pathological glm call can therefore stall a worker for ~2.5h. Override.
import requests as _requests   # noqa: E402

EXP_HTTP_TIMEOUT = int(os.environ.get("EXP_HTTP_TIMEOUT", "120"))
EXP_MAX_RETRIES  = int(os.environ.get("EXP_MAX_RETRIES",  "5"))


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
            if is_reasoning_model:
                data["reasoning"] = {"effort": "low"}
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
            # No point sleeping a long time before next try — short backoff.
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
DATASETS = ["ToMBench", "CogToM"]
N_WORKERS = int(os.environ.get("EXP_WORKERS", "32"))
# Big budget — glm-5 (reasoning model) routinely overruns 2048 / 4000 tokens
# mid-procedure and emits no final answer. 8192 covers ~99% of cases empirically.
ANSWER_MAX_TOKENS = int(os.environ.get("EXP_ANSWER_TOKENS", "8192"))

# Single instruction block injected into every (skill / vanilla) answer prompt.
# Two purposes:
#   1) Defends against truncation: if the model is cut off mid-reasoning we
#      still recover an answer letter from the FIRST line.
#   2) The downstream `extract_answer_letter` keeps the LAST match of
#      `answer (is|:) X`, so a deliberate `FINAL ANSWER: X` at the end
#      overrides the preliminary one when the model finishes cleanly.
ANSWER_FORMAT_GUARD = (
    "OUTPUT FORMAT (mandatory):\n"
    "1. Your VERY FIRST line must be exactly `ANSWER: <letter>` — your best\n"
    "   guess based on a fast read. This protects against truncation.\n"
    "2. Then perform the strategy/reasoning steps.\n"
    "3. End with exactly one line: `FINAL ANSWER: <letter>`.\n"
    "If steps 2-3 lead you to revise step 1, the FINAL ANSWER line wins.\n"
    "Use only one of the provided option letters."
)


EXP_LIMIT = int(os.environ.get("EXP_LIMIT", "0"))   # 0 = no cap (full run)


# ─────────────────────── Loading ───────────────────────
def load_dataset(ds):
    out = []
    with open(os.path.join(DATA, f"{ds}.jsonl")) as f:
        for line in f:
            out.append(json.loads(line))
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
    p = build_router_prompt(
        item["story"], item["question"],
        dict(zip(item["labels"], item["options"])), item["labels"]
    )
    try:
        resp = model.interact(p, max_tokens=256)
        choice = parse_router_choice(resp) or "NONE"
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


# Tight regexes for the answer-format-guard markers — checked BEFORE
# the more permissive extract_answer_letter() to defeat mid-reasoning noise
# like "the answer is C because…" inside a long glm trace.
_FINAL_ANSWER_RE = re.compile(r"FINAL\s*ANSWER\s*[:\-]\s*\(?([A-D])\)?", re.IGNORECASE)
_FIRST_ANSWER_RE = re.compile(r"^\s*ANSWER\s*[:\-]\s*\(?([A-D])\)?", re.IGNORECASE | re.MULTILINE)


def robust_extract(resp, labels):
    """Prefer explicit format-guard markers; fall back to the shared extractor."""
    if not resp:
        return None
    valid = set(labels)
    # 1) FINAL ANSWER wins if present (the model finished cleanly).
    matches = _FINAL_ANSWER_RE.findall(resp)
    if matches:
        letter = matches[-1].upper()
        if letter in valid:
            return letter
    # 2) Otherwise the first-line ANSWER guard (handles truncation).
    matches = _FIRST_ANSWER_RE.findall(resp)
    if matches:
        letter = matches[0].upper()
        if letter in valid:
            return letter
    # 3) Fall through to the shared (looser) extractor.
    return extract_answer_letter(resp, labels)


# ───────────────────── Answer pass ─────────────────────
def answer_one(model, item, skill_id):
    skill = get_skill_prompt(skill_id)
    base = build_vanilla_prompt(item["story"], item["question"],
                                 dict(zip(item["labels"], item["options"])),
                                 item["labels"])
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
    _bump(f"answer {item['global_idx']} {skill_id:18s} → {pred} (gold={item['gold_answer']}) {'FIX' if fixed else '-'}")
    return {
        "global_idx": item["global_idx"],
        "ability":    item["ability"],
        "task_type":  item["task_type"],
        "gold":       item["gold_answer"],
        "skill":      skill_id,
        "pred":       pred,
        "fixed":      fixed,
        "answer_response": resp,
    }


def run_answerer(items, model_name, skill_map, label):
    model = load_model(model_name)
    _progress["done"] = 0
    _progress["total"] = len(items)
    print(f"\n[{label}] answering {len(items)} cases with {model_name} ...")
    rows = []
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = [
            ex.submit(answer_one, model, it,
                      skill_map.get(it["global_idx"], "NONE"))
            for it in items
        ]
        for f in as_completed(futs):
            rows.append(f.result())
    return rows


# ───────────────────── Aggregation ─────────────────────
def summarise(rows, dim):
    bucket = defaultdict(lambda: {"n": 0, "fix": 0})
    for r in rows:
        b = bucket[r[dim]]
        b["n"] += 1
        if r["fixed"]:
            b["fix"] += 1
    out = []
    for k, v in bucket.items():
        out.append((k, v["n"], v["fix"], v["fix"] / v["n"] if v["n"] else 0.0))
    out.sort(key=lambda x: (-x[3], -x[1], x[0]))
    return out


def write_dataset_md(ds, results, router_acc_info):
    """results = {model_name: rows}"""
    md = [f"# Per-model fix rates on `{ds}`\n",
          f"- Router: `{ROUTER_MODEL}` (fixed across both answerers)",
          f"- Cases routed: {router_acc_info['n_routed']}",
          f"- Routed to NONE: {router_acc_info['n_none']} ({router_acc_info['n_none']/max(1,router_acc_info['n_routed']):.1%})\n"]

    md.append("## Overall\n")
    md.append("| Answerer | Cases | Fixed | Fix Rate |")
    md.append("|---|---:|---:|---:|")
    for m, rows in results.items():
        n = len(rows); fx = sum(r["fixed"] for r in rows)
        md.append(f"| `{m}` | {n} | {fx} | **{fx/max(1,n):.1%}** |")

    for dim in ("ability", "task_type"):
        md.append(f"\n## Per `{dim}` fix rates\n")
        all_keys = sorted({r[dim] for rows in results.values() for r in rows})
        head = "| " + dim + " | " + " | ".join(
            f"{m} cases | {m} fixed | {m} fix-rate" for m in results
        ) + " |"
        sep = "|---|" + ("---:|---:|---:|" * len(results))
        md.append(head); md.append(sep)
        # Pre-compute per (model, key)
        per = {m: {k: [0, 0] for k in all_keys} for m in results}
        for m, rows in results.items():
            for r in rows:
                per[m][r[dim]][0] += 1
                if r["fixed"]:
                    per[m][r[dim]][1] += 1
        for k in all_keys:
            cells = []
            for m in results:
                n, fx = per[m][k]
                rate = f"{fx/n:.1%}" if n else "—"
                cells += [str(n) if n else "0", str(fx) if n else "0", f"**{rate}**" if n else "—"]
            md.append(f"| {k} | " + " | ".join(cells) + " |")

    return "\n".join(md) + "\n"


# ───────────────────── Main ─────────────────────
def main():
    t0 = time.time()
    summary = {}  # dataset → {model → rows}
    skill_maps = {}
    router_raws = {}

    for ds in DATASETS:
        items = load_dataset(ds)
        # Route once per case (router doesn't depend on answerer model)
        skill_map, raw = run_router(items, label=f"{ds}/router")
        skill_maps[ds] = skill_map
        router_raws[ds] = raw

        n_none = sum(1 for v in skill_map.values() if v == "NONE")
        router_acc_info = {"n_routed": len(items), "n_none": n_none}

        per_model_rows = {}
        for mname in ANSWERER_MODELS:
            mname = mname.strip()
            wrong = [it for it in items if mname in it["wrong_by"]]
            print(f"\n=== {ds}  answerer={mname}  cases={len(wrong)} ===")
            rows = run_answerer(wrong, mname, skill_map, label=f"{ds}/{mname}")
            per_model_rows[mname] = rows

            json_path = os.path.join(OUT, f"{ds}__{mname.replace('.','_')}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({
                    "dataset": ds,
                    "answerer": mname,
                    "router": ROUTER_MODEL,
                    "n_cases": len(rows),
                    "n_fixed": sum(r["fixed"] for r in rows),
                    "by_ability":   summarise(rows, "ability"),
                    "by_task_type": summarise(rows, "task_type"),
                    "rows": rows,
                }, f, ensure_ascii=False, indent=2)
            print(f"Saved {json_path}")

        # Markdown for this dataset
        md = write_dataset_md(ds, per_model_rows, router_acc_info)
        md_path = os.path.join(OUT, f"{ds}__per_model.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Saved {md_path}")
        summary[ds] = per_model_rows

    # Combined headline summary
    head = ["# Skills v2 — per (dataset × model) fix rates\n",
            f"Router: `{ROUTER_MODEL}`  ·  Answerers: {ANSWERER_MODELS}",
            f"Total elapsed: {time.time()-t0:.1f}s\n",
            "## Headline\n",
            "| Dataset | Answerer | Cases (orig wrong) | Fixed by skills | Fix Rate |",
            "|---|---|---:|---:|---:|"]
    for ds in DATASETS:
        for m in ANSWERER_MODELS:
            m = m.strip()
            rows = summary[ds][m]
            n = len(rows); fx = sum(r["fixed"] for r in rows)
            head.append(f"| {ds} | `{m}` | {n} | {fx} | **{fx/max(1,n):.1%}** |")
    head.append("\nSee per-dataset breakdowns:\n")
    for ds in DATASETS:
        head.append(f"- [`{ds}__per_model.md`](./{ds}__per_model.md)")
    with open(os.path.join(OUT, "HEADLINE.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(head) + "\n")
    print(f"Saved {os.path.join(OUT, 'HEADLINE.md')}")
    print(f"\nDone in {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    main()
