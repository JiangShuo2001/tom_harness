"""Full-dataset skill-routing evaluation.

Unlike `experiment_per_model.py`, which restricts to the error subset and
reports *fix rate on wrong cases*, this script runs the full pipeline
(router → skill-or-vanilla → answer) on the **entire 2860 ToMBench +
2112 CogToM pool** and reports **global accuracy + breakdowns by
`ability` and `task_type`**.

Key robustness features (lessons from the per-model run):
  - Incremental JSONL checkpoint: every completed case is flushed to disk
    **immediately**, so a hung worker or process crash cannot lose
    already-computed work.
  - Resumable: re-running the script skips cases whose `global_idx`
    already exists in the checkpoint.
  - Shorter HTTP timeout (monkey-patched `GPTAgent.interact`) so a single
    slow request can't stall a worker for >2 minutes.

Outputs land under `data/results/full_eval/`.
"""
import json
import os
import re
import sys
import time
import random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT  = os.path.join(DATA, "results", "full_eval")
PERCEP = os.path.abspath(os.path.join(HERE, "..", "PercepToM"))
sys.path.insert(0, HERE)
sys.path.insert(0, PERCEP)
os.makedirs(OUT, exist_ok=True)

from llm_agents import load_model, GPTAgent                                 # noqa
from eval_new_benchmarks import build_vanilla_prompt, extract_answer_letter # noqa
from skills import SKILLS                                                    # noqa
from llm_router import (                                                      # noqa
    build_router_prompt, parse_router_choice, get_skill_prompt, VALID_IDS,
)

# ─────────── Saner retry/timeout ───────────
import requests as _requests  # noqa: E402

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
            time.sleep(2)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            time.sleep(2)
    raise RuntimeError(f"GPT generation failed: {last_err}")


GPTAgent.interact = _patched_interact


# ─────────── Config ───────────
ROUTER_MODEL      = os.environ.get("EXP_ROUTER", "gpt-5.4-mini")
ANSWERER_MODELS   = os.environ.get("EXP_ANSWERERS", "gpt-5.4-mini,glm-5").split(",")
N_WORKERS         = int(os.environ.get("EXP_WORKERS", "32"))
ANSWER_MAX_TOKENS = int(os.environ.get("EXP_ANSWER_TOKENS", "8192"))
EXP_LIMIT         = int(os.environ.get("EXP_LIMIT", "0"))  # 0 = full

ANSWER_FORMAT_GUARD = (
    "OUTPUT FORMAT (mandatory):\n"
    "1. Your VERY FIRST line must be exactly `ANSWER: <letter>` — your best\n"
    "   guess based on a fast read. This protects against truncation.\n"
    "2. Then perform the strategy/reasoning steps.\n"
    "3. End with exactly one line: `FINAL ANSWER: <letter>`.\n"
    "If steps 2-3 lead you to revise step 1, the FINAL ANSWER line wins.\n"
    "Use only one of the provided option letters."
)


# ─────────── Dataset loaders (deterministic, identical to run_eval.py) ───────────
TOMBENCH_FULL = os.path.join(PERCEP, "dataset", "ToMBench", "tombench.jsonl")
COGTOM_FULL   = os.path.join(PERCEP, "dataset", "CogToM", "cogtom_full_en.jsonl")


def load_tombench_full():
    data = []
    with open(TOMBENCH_FULL, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f):
            item = json.loads(line)
            if not item.get("story") or not item.get("question"):
                continue
            options, labels = [], []
            for key, lab in [("option_a", "A"), ("option_b", "B"),
                             ("option_c", "C"), ("option_d", "D")]:
                val = item.get(key)
                if val and val != "None" and str(val).strip():
                    options.append(val)
                    labels.append(lab)
            if len(options) < 2:
                continue
            ans = str(item.get("answer", "")).strip()
            if ans.endswith("."):
                ans = ans[:-1].strip()
            data.append({
                "global_idx": f"tombench_{line_idx}",
                "dataset":    "ToMBench",
                "story":      item["story"],
                "question":   item["question"],
                "options":    options,
                "labels":     labels,
                "gold_answer": ans,
                "ability":     item.get("ability", ""),
                "task_type":   item.get("sheet_name", ""),
            })
    return data


def load_cogtom_stratified(ratio=0.25, seed=42):
    raw = []
    with open(COGTOM_FULL, "r", encoding="utf-8") as f:
        for line in f:
            raw.append(json.loads(line))

    by_sub = defaultdict(list)
    for item in raw:
        by_sub[item["subcategory"]].append(item)

    rng = random.Random(seed)
    sampled = []
    for sub, items in sorted(by_sub.items()):
        items_copy = list(items)
        rng.shuffle(items_copy)
        n = max(1, int(len(items_copy) * ratio))
        sampled.extend(items_copy[:n])

    data = []
    for item in sampled:
        opts = item["options"]
        if isinstance(opts, dict):
            options = list(opts.values())
            labels  = list(opts.keys())
        else:
            options = opts
            labels  = ["A", "B", "C", "D"][:len(opts)]
        data.append({
            "global_idx":  f"cogtom_{item['global_idx']}",
            "dataset":     "CogToM",
            "story":       item["scene"],
            "question":    item["question"],
            "options":     options,
            "labels":      labels,
            "gold_answer": item["answer"],
            "ability":     item.get("category", ""),
            "task_type":   item.get("subcategory", ""),
        })
    return data


# ─────────── Incremental JSONL checkpoint ───────────
class JsonlCheckpoint:
    """Line-by-line append-only store keyed by global_idx."""
    def __init__(self, path):
        self.path = path
        self.lock = Lock()
        self.done = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                        self.done[r["global_idx"]] = r
                    except Exception:
                        pass
        if self.done:
            print(f"  [resume] {path} already has {len(self.done)} rows", flush=True)

    def has(self, gid): return gid in self.done

    def get(self, gid): return self.done.get(gid)

    def append(self, row):
        gid = row["global_idx"]
        with self.lock:
            if gid in self.done:
                return
            self.done[gid] = row
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def rows(self):
        return list(self.done.values())


# ─────────── Router pass ───────────
_print_lock = Lock()
_progress = {"done": 0, "total": 0, "new": 0}


def _bump(label):
    with _print_lock:
        _progress["done"] += 1
        if _progress["done"] % 100 == 0 or _progress["done"] == _progress["total"]:
            print(f"  [{_progress['done']:5d}/{_progress['total']}] {label}", flush=True)


def route_one(model, item, ckpt):
    gid = item["global_idx"]
    if ckpt.has(gid):
        _bump(f"route skip {gid}")
        return
    p = build_router_prompt(
        item["story"], item["question"],
        dict(zip(item["labels"], item["options"])), item["labels"]
    )
    try:
        resp = model.interact(p, max_tokens=256)
        choice = parse_router_choice(resp) or "NONE"
    except Exception as e:
        choice, resp = "NONE", f"<route err: {e}>"
    row = {"global_idx": gid, "skill": choice, "router_response": resp}
    ckpt.append(row)
    _bump(f"route {gid} → {choice}")


def run_router(items, ds_label):
    ckpt_path = os.path.join(OUT, f"router_{ds_label}.jsonl")
    ckpt = JsonlCheckpoint(ckpt_path)
    model = load_model(ROUTER_MODEL)
    _progress["done"] = 0
    _progress["total"] = len(items)
    todo = [it for it in items if not ckpt.has(it["global_idx"])]
    print(f"\n[{ds_label}/router] {len(items)} cases ({len(todo)} pending) with {ROUTER_MODEL} ...",
          flush=True)
    for it in items:
        if ckpt.has(it["global_idx"]):
            _bump(f"route skip {it['global_idx']}")
    if todo:
        with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
            futs = [ex.submit(route_one, model, it, ckpt) for it in todo]
            for f in as_completed(futs):
                try:
                    f.result()
                except Exception as e:
                    print(f"  [router err] {e}", flush=True)
    return {r["global_idx"]: r["skill"] for r in ckpt.rows()}


# ─────────── Answer extraction ───────────
_FINAL_ANSWER_RE = re.compile(r"FINAL\s*ANSWER\s*[:\-]\s*\(?([A-D])\)?", re.IGNORECASE)
_FIRST_ANSWER_RE = re.compile(r"^\s*ANSWER\s*[:\-]\s*\(?([A-D])\)?", re.IGNORECASE | re.MULTILINE)


def robust_extract(resp, labels):
    if not resp:
        return None
    valid = set(labels)
    m = _FINAL_ANSWER_RE.findall(resp)
    if m and m[-1].upper() in valid:
        return m[-1].upper()
    m = _FIRST_ANSWER_RE.findall(resp)
    if m and m[0].upper() in valid:
        return m[0].upper()
    return extract_answer_letter(resp, labels)


def build_prompt(item, skill_id):
    skill = get_skill_prompt(skill_id)
    base = build_vanilla_prompt(item["story"], item["question"],
                                 dict(zip(item["labels"], item["options"])),
                                 item["labels"])
    if skill:
        return (
            "You are answering a Theory-of-Mind multiple-choice question.\n"
            "Apply the following strategy carefully, then answer.\n\n"
            f"=== STRATEGY ===\n{skill}\n=== END STRATEGY ===\n\n"
            f"=== QUESTION ===\n{base}\n\n"
            f"=== {ANSWER_FORMAT_GUARD}"
        )
    return f"{base}\n\n=== {ANSWER_FORMAT_GUARD}"


def answer_one(model, item, skill_id, ckpt):
    gid = item["global_idx"]
    if ckpt.has(gid):
        _bump(f"ans skip {gid}")
        return
    prompt = build_prompt(item, skill_id)
    try:
        resp = model.interact(prompt, max_tokens=ANSWER_MAX_TOKENS)
        pred = robust_extract(resp, item["labels"])
    except Exception as e:
        pred, resp = None, f"<answer err: {e}>"
    correct = (pred == item["gold_answer"])
    row = {
        "global_idx": gid,
        "dataset":    item["dataset"],
        "ability":    item["ability"],
        "task_type":  item["task_type"],
        "skill":      skill_id,
        "pred":       pred,
        "gold":       item["gold_answer"],
        "correct":    correct,
        "response":   resp[:4000] if isinstance(resp, str) else resp,
    }
    ckpt.append(row)
    _bump(f"ans {gid} {skill_id:18s} → {pred} (gold={item['gold_answer']}) {'OK' if correct else '-'}")


def run_answerer(items, skill_map, model_name, ds_label):
    ckpt_path = os.path.join(OUT, f"answers_{ds_label}_{model_name.replace('.', '_')}.jsonl")
    ckpt = JsonlCheckpoint(ckpt_path)
    model = load_model(model_name)
    _progress["done"] = 0
    _progress["total"] = len(items)
    todo = [it for it in items if not ckpt.has(it["global_idx"])]
    print(f"\n[{ds_label}/{model_name}] {len(items)} cases ({len(todo)} pending) ...",
          flush=True)
    for it in items:
        if ckpt.has(it["global_idx"]):
            _bump(f"ans skip {it['global_idx']}")
    if todo:
        with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
            futs = [ex.submit(answer_one, model, it,
                              skill_map.get(it["global_idx"], "NONE"), ckpt)
                    for it in todo]
            for f in as_completed(futs):
                try:
                    f.result()
                except Exception as e:
                    print(f"  [ans err] {e}", flush=True)
    return ckpt.rows()


# ─────────── Aggregation ───────────
def summarise(rows, dim):
    bucket = defaultdict(lambda: {"n": 0, "correct": 0})
    for r in rows:
        b = bucket[r[dim]]
        b["n"] += 1
        if r["correct"]:
            b["correct"] += 1
    out = []
    for k, v in bucket.items():
        out.append((k, v["n"], v["correct"], v["correct"] / v["n"] if v["n"] else 0.0))
    out.sort(key=lambda x: (-x[1], x[0]))
    return out


def write_dataset_md(ds, per_model_rows, skill_map, n_total):
    none_count = sum(1 for s in skill_map.values() if s == "NONE")
    lines = [
        f"# Full-dataset accuracy on `{ds}` (skill-routing pipeline)\n",
        f"- Router: `{ROUTER_MODEL}`",
        f"- Cases routed: {n_total}",
        f"- Routed to NONE: {none_count} ({none_count / max(1, n_total):.1%})",
        f"- Routed to a skill: {n_total - none_count} ({(n_total - none_count) / max(1, n_total):.1%})\n",
        "## Overall accuracy\n",
        "| Answerer | Cases | Correct | Accuracy |",
        "|---|---:|---:|---:|",
    ]
    for m, rows in per_model_rows.items():
        n = len(rows); c = sum(r["correct"] for r in rows)
        lines.append(f"| `{m}` | {n} | {c} | **{c / max(1, n):.1%}** |")

    for dim in ("ability", "task_type"):
        lines.append(f"\n## Accuracy by `{dim}`\n")
        models = list(per_model_rows.keys())
        header = "| " + dim + " | Cases | " + \
                 " | ".join(f"Correct ({m}) | Acc ({m})" for m in models) + " |"
        sep = "|---|---:|" + "|".join(["---:|---:"] * len(models)) + "|"
        lines.append(header); lines.append(sep)
        keys = sorted({r[dim] for rows in per_model_rows.values() for r in rows})
        for k in keys:
            cells = []
            total_n = None
            for m in models:
                rs = [r for r in per_model_rows[m] if r[dim] == k]
                n = len(rs); c = sum(r["correct"] for r in rs)
                if total_n is None:
                    total_n = n
                cells.append(f"{c} | {c / max(1, n):.1%}")
            lines.append(f"| {k} | {total_n} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


# ─────────── Main ───────────
def main():
    t0 = time.time()
    loaders = {
        "ToMBench": load_tombench_full,
        "CogToM":   load_cogtom_stratified,
    }
    summary = {}
    for ds, loader in loaders.items():
        items = loader()
        if EXP_LIMIT:
            items = items[:EXP_LIMIT]
        print(f"\n=== {ds} | {len(items)} cases ===", flush=True)

        skill_map = run_router(items, ds)

        per_model_rows = {}
        for m in ANSWERER_MODELS:
            m = m.strip()
            rows = run_answerer(items, skill_map, m, ds)
            per_model_rows[m] = rows

        md = write_dataset_md(ds, per_model_rows, skill_map, len(items))
        with open(os.path.join(OUT, f"{ds}__full.md"), "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Saved {os.path.join(OUT, f'{ds}__full.md')}", flush=True)
        summary[ds] = (per_model_rows, skill_map, len(items))

    # Combined headline
    head = [
        "# Skills v2 — FULL-dataset accuracy with skill routing\n",
        f"Router: `{ROUTER_MODEL}`  ·  Answerers: {ANSWERER_MODELS}",
        f"Total elapsed: {time.time()-t0:.1f}s\n",
        "## Headline\n",
        "| Dataset | Answerer | Cases | Correct | Accuracy |",
        "|---|---|---:|---:|---:|",
    ]
    for ds, (pm, _, _) in summary.items():
        for m in ANSWERER_MODELS:
            m = m.strip()
            rows = pm[m]
            n = len(rows); c = sum(r["correct"] for r in rows)
            head.append(f"| {ds} | `{m}` | {n} | {c} | **{c / max(1, n):.1%}** |")
    head.append("\nSee per-dataset breakdowns:\n")
    for ds in summary:
        head.append(f"- [`{ds}__full.md`](./{ds}__full.md)")
    with open(os.path.join(OUT, "HEADLINE.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(head) + "\n")
    print(f"Saved {os.path.join(OUT, 'HEADLINE.md')}", flush=True)
    print(f"\nDone in {time.time()-t0:.1f}s.", flush=True)


if __name__ == "__main__":
    main()
