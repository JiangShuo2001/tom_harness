"""Thin harness runner driven by SelectiveRouter (v0.4).

Uses the harness's component layer (SkillLib, adapters, SelectiveRouter,
signature extraction) but skips the multi-step Planner/Executor pipeline.
Per sample: one routing call (no LLM) + one inference LLM call.

Why thin: v0.4 selective is fundamentally about *gating* — once the
gate is decided, more LLM steps add noise. The full Plan/Execute
machinery is appropriate for tasks that need decomposition (e.g. our
StoryModel-based skills), not for simple prompt prepending.

Falls back to vanilla CoT when SelectiveRouter returns skill_id=None.
"""

from __future__ import annotations

import argparse, json, logging, os, random, re, sys, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "/home/coder/survey_1/symbolictom_repro")

from benchmark_adapters import load_tombench  # type: ignore  # noqa: E402
from tom_harness import LLMClient  # noqa: E402
from tom_harness.tools.skills import SkillLib  # noqa: E402
from tom_harness.plugins.external_skill_pack.selective_router import SelectiveRouter  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("selective"); logger.setLevel(logging.INFO)


MAIN_8 = {
    "Unexpected Outcome Test", "Scalar Implicature Test", "Persuasion Story Task",
    "False Belief Task", "Ambiguous Story Task", "Hinting Task Test",
    "Strange Story Task", "Faux-pas Recognition Test",
}

SYSTEM = (
    "You are a reading comprehension assistant. Read the story and answer "
    'the multiple-choice question. Reply with ONLY a JSON object: '
    '{"answer": "A" | "B" | "C" | "D"}'
)


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
    if m: return m.group(1)
    m = re.search(r"\b([A-D])\b", text[-200:])
    if m: return m.group(1)
    return ""


def process_one(sample, llm, router, skill_lib):
    t0 = time.time()
    rt = router.route(
        question=sample["question"], story=sample["story"],
        options=sample["options"], task_type=sample["metadata"].get("task", ""),
    )
    skill_body = None
    if rt.skill_id:
        rec = skill_lib.get(rt.skill_id)
        if rec:
            skill_body = rec.body
    user = build_user(sample, skill_body=skill_body)
    try:
        resp = llm.chat(SYSTEM, user, max_tokens=1024)
        pred = parse_letter(resp)
    except Exception as e:  # noqa: BLE001
        pred, resp = "", f"ERROR: {e}"
    return {
        "id": sample["id"], "task": sample["metadata"].get("task"),
        "answer": sample["answer"], "predicted": pred,
        "correct": pred == sample["answer"],
        "skill_id": rt.skill_id, "rationale": rt.rationale,
        "elapsed_sec": round(time.time() - t0, 2),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_task", type=int, default=20)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--tag", default="selective_thin")
    args = ap.parse_args()

    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY"); model = os.environ.get("TOM_MODEL", "qwen3.5-27b")
    if not api_key: raise SystemExit("set TOM_API_KEY")
    llm = LLMClient(api_base=api_base, api_key=api_key, model=model,
                    temperature=0.0, max_tokens=1024, timeout=120.0, max_retries=3)

    skill_lib = SkillLib()
    router = SelectiveRouter()
    n = router.load_into(skill_lib)
    info = router.metadata()
    logger.info(f"router loaded: {info.pack_name} v{info.pack_version}, {n} skills")

    samples = load_tombench()
    pool = stratified(samples, args.per_task)
    logger.info(f"pool: {len(pool)}")

    out_dir = Path("results"); out_dir.mkdir(exist_ok=True)
    results_path = out_dir / f"selective_thin_{args.tag}_results.jsonl"
    done = set()
    if results_path.exists():
        for ln in open(results_path, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try: done.add(json.loads(ln)["id"])
                except Exception: pass
    pending = [s for s in pool if s["id"] not in done]

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as exe:
        futs = {exe.submit(process_one, s, llm, router, skill_lib): s for s in pending}
        for i, f in enumerate(as_completed(futs), 1):
            rec = f.result()
            with open(results_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if i % 30 == 0:
                logger.info(f"  {i}/{len(pending)} elapsed={(time.time()-t0)/60:.1f}min")

    # Aggregate
    records = [json.loads(l) for l in open(results_path) if l.strip()]
    per_task = defaultdict(lambda: [0, 0])
    skill_use = defaultdict(int)
    no_skill = 0
    for r in records:
        per_task[r["task"]][0] += 1
        per_task[r["task"]][1] += int(bool(r["correct"]))
        if r.get("skill_id"):
            skill_use[r["skill_id"]] += 1
        else:
            no_skill += 1
    total = len(records); correct = sum(1 for r in records if r["correct"])
    print(f"\n========== Selective via thin harness ==========")
    print(f"{'task':<32}{'acc':>10}")
    for t in sorted(per_task):
        n_t, c_t = per_task[t]
        print(f"{t:<32}{c_t/n_t:>9.1%}")
    print(f"{'OVERALL':<32}{correct/total:>9.1%}")
    print(f"\nMode usage: raw={no_skill}, skills={dict(skill_use)}")


if __name__ == "__main__":
    main()
