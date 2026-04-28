"""Inferred per-task best skill via LLM task classifier.

Re-uses cached per-skill predictions from results_matrix/per_skill_*.jsonl.
Only new LLM calls = 160 classifier calls (one per sample).

Pipeline per sample:
  1. classifier(question) -> predicted_task ∈ {MAIN_8}
  2. best_skill = per_task_best[predicted_task]   (from matrix_summary)
  3. inferred_pred = cached_pred[best_skill][sample_id]
  4. ok = (inferred_pred == answer)

Reports: classifier accuracy, per-task picks, inferred overall acc, gap to oracle.
"""
from __future__ import annotations
import argparse, json, os, random, re, sys, time
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "/home/coder/survey_1/symbolictom_repro")

from benchmark_adapters import load_tombench  # type: ignore  # noqa: E402
from tom_harness import LLMClient  # noqa: E402

MAIN_8 = [
    "Ambiguous Story Task", "False Belief Task", "Faux-pas Recognition Test",
    "Hinting Task Test", "Persuasion Story Task", "Scalar Implicature Test",
    "Strange Story Task", "Unexpected Outcome Test",
]
MAIN_8_SET = set(MAIN_8)


def stratified(samples, per_task=20, seed=42):
    rng = random.Random(seed)
    buckets = defaultdict(list)
    for s in samples:
        if s["metadata"].get("task", "") in MAIN_8_SET:
            buckets[s["metadata"]["task"]].append(s)
    out = []
    for t in sorted(buckets):
        b = buckets[t]; rng.shuffle(b); out.extend(b[:per_task])
    return out


CLASSIFIER_SYSTEM = """You are a task classifier. Given a Theory-of-Mind question and \
its multiple-choice options, classify which of the 8 task categories it belongs to. \
Reply with ONLY a JSON object: {"task": "<one of the 8 task names>"}.

The 8 task categories:
- "Ambiguous Story Task": story has socially ambiguous behavior, asks for likely intention/feeling.
- "False Belief Task": asks where a character will look / what they think, given the character missed an event.
- "Faux-pas Recognition Test": asks if someone said something inappropriate / hurtful unintentionally.
- "Hinting Task Test": asks what a speaker is hinting at indirectly (no literal request).
- "Persuasion Story Task": story has manipulation / persuasion attempt, asks about intent or response.
- "Scalar Implicature Test": question involves quantifiers (some/most/all/none/almost half), counting, or implicature.
- "Strange Story Task": story has unusual / odd behavior or speech (lie, irony, joke, double bluff, etc.).
- "Unexpected Outcome Test": asks how a character reacts to an unexpected event."""


def build_classifier_user(s):
    opts = "\n".join(f"{k}. {v}" for k, v in s["options"].items() if v)
    return f"Question: {s['question']}\n\nOptions:\n{opts}\n\nClassify."


_TASK_RE = re.compile(r'"task"\s*:\s*"([^"]+)"')


def parse_task(text: str) -> str:
    text = re.sub(r"<think>[\s\S]*?</think>", "", text or "").strip()
    try:
        d = json.loads(text); v = str(d.get("task", "")).strip()
        if v in MAIN_8_SET: return v
    except Exception:
        pass
    m = _TASK_RE.search(text)
    if m and m.group(1) in MAIN_8_SET: return m.group(1)
    return ""


def classify_one(llm: LLMClient, s: dict) -> dict:
    user = build_classifier_user(s)
    t0 = time.time()
    try:
        text = llm.chat(CLASSIFIER_SYSTEM, user, max_tokens=64)
    except Exception as e:  # noqa: BLE001
        return {"id": s["id"], "true_task": s["metadata"]["task"],
                "pred_task": "", "elapsed": time.time()-t0, "err": str(e)}
    return {"id": s["id"], "true_task": s["metadata"]["task"],
            "pred_task": parse_task(text), "elapsed": time.time()-t0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_task", type=int, default=20)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--matrix_dir", default="results_matrix")
    ap.add_argument("--out_dir", default="results_inferred")
    args = ap.parse_args()

    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY")
    model = os.environ.get("TOM_MODEL", "qwen-plus")
    if not api_key: raise SystemExit("ERROR: set TOM_API_KEY")
    llm = LLMClient(api_base=api_base, api_key=api_key, model=model,
                    temperature=0.0, max_tokens=128, timeout=60.0, max_retries=3)

    matrix_summary = json.loads(Path(args.matrix_dir, "matrix_summary.json").read_text(encoding="utf-8"))
    per_task_best = matrix_summary["oracle_per_task_picks"]
    print(f"per-task best skill (oracle):")
    for t, sid in per_task_best.items():
        print(f"  {t:<32} -> {sid}")

    samples = load_tombench()
    pool = stratified(samples, args.per_task)
    print(f"pool: {len(pool)} samples")

    # Load all skill cached predictions
    cached: dict[str, dict[str, str]] = {}
    for skill_id in set(per_task_best.values()):
        p = Path(args.matrix_dir, f"per_skill_{skill_id}.jsonl")
        if not p.exists():
            raise SystemExit(f"missing cached predictions for {skill_id}: {p}")
        cached[skill_id] = {}
        for ln in open(p, encoding="utf-8"):
            try:
                r = json.loads(ln); cached[skill_id][r["id"]] = r.get("pred", "")
            except Exception: pass
        print(f"  cached preds for {skill_id}: {len(cached[skill_id])} samples")

    # Run classifier
    out_dir = Path(args.out_dir); out_dir.mkdir(exist_ok=True)
    cls_path = out_dir / "classifier_results.jsonl"
    done = set()
    if cls_path.exists():
        for ln in open(cls_path, encoding="utf-8"):
            try: done.add(json.loads(ln)["id"])
            except Exception: pass
    pending = [s for s in pool if s["id"] not in done]
    print(f"classifier: {len(done)} done, {len(pending)} pending")

    results: list[dict] = []
    if cls_path.exists():
        for ln in open(cls_path, encoding="utf-8"):
            try: results.append(json.loads(ln))
            except Exception: pass

    f = open(cls_path, "a", encoding="utf-8")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(classify_one, llm, s): s for s in pending}
        for fut in as_completed(futs):
            r = fut.result()
            f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
            results.append(r)
    f.close()
    print(f"classifier done in {time.time()-t0:.1f}s")

    # Compute classifier accuracy
    cls_correct = sum(1 for r in results if r["pred_task"] == r["true_task"])
    cls_acc = cls_correct / len(results) if results else 0.0
    confusion = defaultdict(lambda: Counter())
    for r in results:
        confusion[r["true_task"]][r["pred_task"] or "<empty>"] += 1

    # Compute inferred-mode prediction
    pool_by_id = {s["id"]: s for s in pool}
    inferred_correct = 0; inferred_total = 0
    per_task_inferred: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0})
    fallback_count = 0
    for r in results:
        s = pool_by_id.get(r["id"])
        if not s: continue
        pred_task = r["pred_task"] or s["metadata"]["task"]  # fallback to true if classifier blank
        if not r["pred_task"]: fallback_count += 1
        skill = per_task_best.get(pred_task)
        if not skill:
            continue
        skill_pred = cached.get(skill, {}).get(s["id"], "")
        ok = (skill_pred == s["answer"])
        inferred_correct += int(ok); inferred_total += 1
        true_t = s["metadata"]["task"]
        per_task_inferred[true_t]["total"] += 1
        per_task_inferred[true_t]["correct"] += int(ok)
    inferred_acc = inferred_correct / inferred_total if inferred_total else 0.0
    for t, c in per_task_inferred.items():
        c["accuracy"] = round(c["correct"]/c["total"], 4) if c["total"] else 0.0

    # Print summary
    oracle_acc = matrix_summary["oracle_per_task_overall_acc"]
    print(f"\n{'='*70}")
    print(f"INFERRED PER-TASK BEST SKILL (via LLM classifier)")
    print(f"{'='*70}")
    print(f"classifier accuracy:           {cls_acc:.3f}  ({cls_correct}/{len(results)})")
    print(f"classifier blanks (fallback):  {fallback_count}")
    print(f"inferred per-task best acc:    {inferred_acc:.3f}  ({inferred_correct}/{inferred_total})")
    print(f"oracle per-task best acc:      {oracle_acc:.3f}")
    print(f"gap to oracle:                 {oracle_acc - inferred_acc:+.3f}")
    print(f"\nPer-task inferred:")
    for t in sorted(per_task_inferred):
        c = per_task_inferred[t]
        print(f"  {t:<32} {c['correct']:>2}/{c['total']:<2} = {c['accuracy']:.2f}")
    print(f"\nClassifier confusion (top errors):")
    err = []
    for true_t, preds in confusion.items():
        for pred_t, n in preds.items():
            if pred_t != true_t and pred_t != "<empty>":
                err.append((n, true_t, pred_t))
    err.sort(reverse=True)
    for n, tt, pt in err[:8]:
        print(f"  {tt:<28} -> {pt:<28} ×{n}")

    summary = {
        "classifier_accuracy": cls_acc,
        "classifier_blanks": fallback_count,
        "inferred_per_task_best_acc": inferred_acc,
        "oracle_per_task_best_acc": oracle_acc,
        "gap_to_oracle": oracle_acc - inferred_acc,
        "per_task_inferred": dict(per_task_inferred),
        "per_task_picks": per_task_best,
        "confusion": {t: dict(c) for t, c in confusion.items()},
    }
    (out_dir / "inferred_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
