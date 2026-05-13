"""Skill matrix sweep: every skill × every sample → per-(task, skill) accuracy.

Builds the upper-bound oracle ceiling under "single skill per sample, oracle
routing" by computing acc(task, skill) for all 27 skills on the 160-sample
stratified pool. Then post-processes:

  - raw            (no skill)
  - per_task_best  (oracle: pick winning skill per task)
  - top1_inferred  (use existing v0.4 selective router)
  - top3_vote_oracle  (top-3 skills per task by oracle acc; majority vote)
  - top3_vote_full    (apply best 3 skills uniformly to all samples; vote)

Output: results_matrix/per_skill_<sid>.jsonl + matrix_summary.json
"""

from __future__ import annotations

import argparse, json, os, random, re, sys, time, importlib.util
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "/home/coder/survey_1/symbolictom_repro")

from benchmark_adapters import load_tombench  # type: ignore  # noqa: E402
from tom_harness import LLMClient  # noqa: E402

import logging
logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("matrix"); logger.setLevel(logging.INFO)


MAIN_8 = {
    "Unexpected Outcome Test", "Scalar Implicature Test", "Persuasion Story Task",
    "False Belief Task", "Ambiguous Story Task", "Hinting Task Test",
    "Strange Story Task", "Faux-pas Recognition Test",
}


def stratified(samples, per_task=20, seed=42):
    rng = random.Random(seed)
    buckets = defaultdict(list)
    for s in samples:
        if s["metadata"].get("task", "") in MAIN_8:
            buckets[s["metadata"]["task"]].append(s)
    out = []
    for t in sorted(buckets):
        b = buckets[t]; rng.shuffle(b); out.extend(b[:per_task])
    return out


SYSTEM_RAW = (
    "You are a reading comprehension assistant. Read the story and answer "
    'the multiple-choice question. Reply with ONLY a JSON object: '
    '{"answer": "A" | "B" | "C" | "D"}'
)


def build_user(s, skill_body=None):
    opts = "\n".join(f"{k}. {v}" for k, v in s["options"].items() if v)
    if skill_body:
        return (
            f"## Reasoning Skill (apply before answering)\n{skill_body}\n\n"
            f"## Story\n{s['story']}\n\n"
            f"## Question\n{s['question']}\n\n"
            f"## Options\n{opts}\n\n"
            '## Answer\nAfter applying the skill above, reply with ONLY a JSON object: {"answer": "A"|"B"|"C"|"D"}'
        )
    return f"Story: {s['story']}\n\nQuestion: {s['question']}\n\nOptions:\n{opts}"


_LETTER = re.compile(r'"answer"\s*:\s*"([A-D])"')


def parse_letter(text: str) -> str:
    text = re.sub(r"<think>[\s\S]*?</think>", "", text or "").strip()
    try:
        d = json.loads(text); a = str(d.get("answer", "")).strip().upper()
        if a in {"A", "B", "C", "D"}: return a
    except Exception:
        pass
    m = _LETTER.search(text)
    return m.group(1).upper() if m else ""


# ─── Load skills ──────────────────────────────────────────────────────────────

def load_set1_skills() -> dict[str, str]:
    """15 SKILL.md files under /workspace/symbolictom_report/skill_set1/skill{1..15}/."""
    base = Path("/workspace/symbolictom_report/skill_set1")
    out = {}
    for i in range(1, 16):
        p = base / f"skill{i}" / "SKILL.md"
        if p.exists():
            out[f"cs1_skill{i}"] = p.read_text(encoding="utf-8")
    return out


def load_set2_skills() -> dict[str, str]:
    """SKILLS dict in /workspace/symbolictom_report/skill_set2/skill_v2/skills.py."""
    skills_path = "/workspace/symbolictom_report/skill_set2/skill_v2/skills.py"
    spec = importlib.util.spec_from_file_location("set2_skills_module", skills_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return {f"cs2_{k}": v for k, v in mod.SKILLS.items()}


# ─── Worker ───────────────────────────────────────────────────────────────────

def run_one(llm: LLMClient, s: dict, skill_id: str | None, skill_body: str | None) -> dict:
    sys_prompt = SYSTEM_RAW
    user = build_user(s, skill_body)
    t0 = time.time()
    try:
        text = llm.chat(sys_prompt, user, max_tokens=1024)
    except Exception as e:  # noqa: BLE001
        return {"id": s["id"], "task": s["metadata"]["task"], "gold": s["answer"],
                "skill_id": skill_id, "pred": "", "ok": False, "err": str(e),
                "elapsed": time.time() - t0}
    pred = parse_letter(text)
    return {"id": s["id"], "task": s["metadata"]["task"], "gold": s["answer"],
            "skill_id": skill_id, "pred": pred, "ok": pred == s["answer"],
            "elapsed": time.time() - t0}


def sweep_one_skill(llm: LLMClient, samples: list, skill_id: str | None,
                    skill_body: str | None, out_path: Path, workers: int) -> None:
    done = set()
    if out_path.exists():
        for ln in open(out_path, encoding="utf-8"):
            try: done.add(json.loads(ln)["id"])
            except Exception: pass
    pending = [s for s in samples if s["id"] not in done]
    if not pending:
        return
    f = open(out_path, "a", encoding="utf-8")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(run_one, llm, s, skill_id, skill_body): s for s in pending}
        for fut in as_completed(futures):
            r = fut.result()
            f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
    f.close()


# ─── Post-processing ──────────────────────────────────────────────────────────

def acc_table(per_skill: dict[str, list[dict]]) -> dict[str, dict[str, dict]]:
    """{skill_id -> {task -> {correct, total, accuracy}, overall: {...}}}"""
    out: dict[str, dict[str, dict]] = {}
    for sid, rows in per_skill.items():
        per_task: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0})
        for r in rows:
            t = r["task"]
            per_task[t]["total"] += 1
            if r["ok"]:
                per_task[t]["correct"] += 1
        for t, c in per_task.items():
            c["accuracy"] = round(c["correct"] / c["total"], 4) if c["total"] else 0.0
        total = sum(c["total"] for c in per_task.values())
        correct = sum(c["correct"] for c in per_task.values())
        out[sid] = {"per_task": dict(per_task),
                    "overall": {"total": total, "correct": correct,
                                "accuracy": round(correct / total, 4) if total else 0.0}}
    return out


def per_task_best(table: dict, raw_id: str = "raw") -> tuple[dict[str, str], float, dict]:
    """For each task, pick winning skill (or raw if no skill beats raw). Returns:
       (task -> skill_id, oracle_overall_acc, per_task_picks_with_acc)."""
    tasks = sorted({t for entry in table.values() for t in entry["per_task"].keys()})
    picks: dict[str, str] = {}
    detail: dict[str, dict] = {}
    total_correct = 0; total_total = 0
    for t in tasks:
        best_sid = raw_id
        best_acc = table[raw_id]["per_task"].get(t, {}).get("accuracy", 0.0)
        best_correct = table[raw_id]["per_task"].get(t, {}).get("correct", 0)
        for sid, entry in table.items():
            if sid == raw_id: continue
            c = entry["per_task"].get(t)
            if not c: continue
            if c["accuracy"] > best_acc or (c["accuracy"] == best_acc and sid < best_sid):
                best_acc = c["accuracy"]; best_sid = sid; best_correct = c["correct"]
        picks[t] = best_sid
        detail[t] = {"skill": best_sid, "acc": best_acc, "correct": best_correct,
                     "total": table[raw_id]["per_task"][t]["total"]}
        total_correct += best_correct
        total_total += table[raw_id]["per_task"][t]["total"]
    return picks, round(total_correct / total_total, 4) if total_total else 0.0, detail


def vote_topk(per_skill_pred: dict[str, dict[str, str]], samples: list,
              per_task_topk: dict[str, list[str]]) -> tuple[float, dict]:
    """For each sample, gather predictions from the top-k skills for that task,
       majority-vote. per_skill_pred[skill_id][sample_id] = letter."""
    correct = 0; total = 0
    per_task: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0})
    for s in samples:
        t = s["metadata"]["task"]
        topk = per_task_topk.get(t, [])
        votes: list[str] = []
        for sid in topk:
            p = per_skill_pred.get(sid, {}).get(s["id"], "")
            if p in {"A","B","C","D"}: votes.append(p)
        if not votes:
            continue
        winner = Counter(votes).most_common(1)[0][0]
        ok = (winner == s["answer"])
        correct += int(ok); total += 1
        per_task[t]["total"] += 1; per_task[t]["correct"] += int(ok)
    for t, c in per_task.items():
        c["accuracy"] = round(c["correct"] / c["total"], 4) if c["total"] else 0.0
    return (round(correct / total, 4) if total else 0.0), dict(per_task)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_task", type=int, default=20)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out_dir", default="results_matrix")
    ap.add_argument("--skip_run", action="store_true",
                    help="don't make LLM calls; just post-process existing jsonl")
    args = ap.parse_args()

    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY")
    model = os.environ.get("TOM_MODEL", "qwen-plus")
    if not api_key: raise SystemExit("ERROR: set TOM_API_KEY")
    llm = LLMClient(api_base=api_base, api_key=api_key, model=model,
                    temperature=0.0, max_tokens=1024, timeout=180.0, max_retries=3)

    samples = load_tombench()
    pool = stratified(samples, args.per_task)
    logger.info(f"pool: {len(pool)} samples")

    out_dir = Path(args.out_dir); out_dir.mkdir(exist_ok=True)
    skill_sources: dict[str, str | None] = {"raw": None}
    skill_sources.update(load_set1_skills())
    skill_sources.update(load_set2_skills())
    logger.info(f"skills: {len(skill_sources)} (incl. raw): {list(skill_sources.keys())}")

    if not args.skip_run:
        for i, (sid, body) in enumerate(skill_sources.items(), 1):
            t0 = time.time()
            out_path = out_dir / f"per_skill_{sid}.jsonl"
            sweep_one_skill(llm, pool, sid, body, out_path, args.workers)
            logger.info(f"[{i}/{len(skill_sources)}] {sid} done in {time.time()-t0:.1f}s")

    # Load all results
    per_skill_rows: dict[str, list[dict]] = {}
    per_skill_pred: dict[str, dict[str, str]] = {}
    for sid in skill_sources:
        p = out_dir / f"per_skill_{sid}.jsonl"
        if not p.exists():
            logger.warning(f"missing {p}"); continue
        rows = []
        for ln in open(p, encoding="utf-8"):
            try: rows.append(json.loads(ln))
            except Exception: pass
        per_skill_rows[sid] = rows
        per_skill_pred[sid] = {r["id"]: r.get("pred","") for r in rows}

    table = acc_table(per_skill_rows)

    # Oracle per-task best skill
    picks, oracle_acc, oracle_detail = per_task_best(table, raw_id="raw")
    # Top-3 per-task skills (for ensemble)
    per_task_topk: dict[str, list[str]] = {}
    tasks = sorted({t for entry in table.values() for t in entry["per_task"].keys()})
    for t in tasks:
        scored = []
        for sid, entry in table.items():
            c = entry["per_task"].get(t)
            if c: scored.append((c["accuracy"], sid))
        scored.sort(key=lambda x: (-x[0], x[1]))
        per_task_topk[t] = [sid for _, sid in scored[:3]]

    top3_acc, top3_per_task = vote_topk(per_skill_pred, pool, per_task_topk)

    # Per-skill overall ranking
    overall = sorted(((sid, e["overall"]["accuracy"]) for sid, e in table.items()),
                     key=lambda x: -x[1])

    summary = {
        "n_samples": len(pool),
        "n_skills": len(skill_sources),
        "per_skill_overall": [{"skill": sid, "acc": acc} for sid, acc in overall],
        "raw_acc": table.get("raw", {}).get("overall", {}).get("accuracy"),
        "best_single_skill_overall": overall[0] if overall else None,
        "oracle_per_task_picks": picks,
        "oracle_per_task_detail": oracle_detail,
        "oracle_per_task_overall_acc": oracle_acc,
        "top3_vote_per_task": per_task_topk,
        "top3_vote_overall_acc": top3_acc,
        "top3_vote_per_task_detail": top3_per_task,
        "table": table,
    }
    out_path = out_dir / "matrix_summary.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"summary -> {out_path}")

    # Console display
    print(f"\n{'='*70}\nSKILL MATRIX SUMMARY\n{'='*70}")
    print(f"raw                          : {summary['raw_acc']:.3f}")
    print(f"best_single_skill_overall    : {overall[0][0]:<22} {overall[0][1]:.3f}")
    print(f"oracle_per_task_best_skill   : {oracle_acc:.3f}")
    print(f"top3_vote_oracle             : {top3_acc:.3f}")
    print(f"\nPer-task oracle picks:")
    for t in tasks:
        d = oracle_detail[t]
        raw_t = table["raw"]["per_task"][t]["accuracy"]
        delta = d["acc"] - raw_t
        print(f"  {t:<32} pick={d['skill']:<22} acc={d['acc']:.2f} (raw={raw_t:.2f}, Δ={delta:+.2f})")
    print(f"\nTop-5 single skills overall:")
    for sid, acc in overall[:5]:
        print(f"  {sid:<24} {acc:.3f}")


if __name__ == "__main__":
    main()
