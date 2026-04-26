"""Test skill packs WITHOUT the harness.

For each of the 160 stratified samples:
  1. Route to a skill via the adapter.
  2. Build a single prompt: skill_body + story + question + options.
  3. One LLM call. Parse the answer letter.

Compares against:
  - raw_baseline   (no skill at all, just CoT)
  - set1_direct    (set1 SKILL.md body prepended)
  - set2_direct    (set2 prompt string prepended)

If set1_direct or set2_direct > raw_baseline → skills work; harness is
the bottleneck. If they ≈ raw_baseline → skills don't help on the
sample distribution (fix-rate-on-errors ≠ overall improvement). If
they < raw_baseline → skills net-hurt.
"""

from __future__ import annotations

import argparse, json, os, random, re, sys, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "/home/coder/survey_1/symbolictom_repro")

from benchmark_adapters import load_tombench  # type: ignore  # noqa: E402
from tom_harness import LLMClient  # noqa: E402
from tom_harness.tools.skills import SkillLib  # noqa: E402
from tom_harness.plugins.external_skill_pack.set1_adapter import Set1Adapter  # noqa: E402
from tom_harness.plugins.external_skill_pack.set2_adapter import Set2Adapter  # noqa: E402


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


def build_user_raw(s):
    opts = "\n".join(f"{k}. {v}" for k, v in s["options"].items() if v)
    return f"Story: {s['story']}\n\nQuestion: {s['question']}\n\nOptions:\n{opts}"


def build_user_with_skill(s, skill_body):
    """Skill body prepended; same JSON output contract."""
    opts = "\n".join(f"{k}. {v}" for k, v in s["options"].items() if v)
    return (
        f"## Reasoning Skill (apply before answering)\n{skill_body}\n\n"
        f"## Story\n{s['story']}\n\n"
        f"## Question\n{s['question']}\n\n"
        f"## Options\n{opts}\n\n"
        '## Answer\nAfter applying the skill above, reply with ONLY a JSON object: {"answer": "A"|"B"|"C"|"D"}'
    )


_LETTER = re.compile(r'"answer"\s*:\s*"([A-D])"')


def parse_letter(text: str) -> str:
    text = re.sub(r"<think>[\s\S]*?</think>", "", text or "").strip()
    try:
        d = json.loads(text)
        a = str(d.get("answer", "")).strip().upper()
        if a in {"A", "B", "C", "D"}: return a
    except Exception:
        pass
    m = _LETTER.search(text)
    if m: return m.group(1)
    m = re.search(r"\b([A-D])\b", text[-200:])  # last 200 chars to avoid skill body letters
    if m: return m.group(1)
    return ""


def run_one(sample, llm, mode, skill_lib, adapter):
    t0 = time.time()
    skill_id, skill_body = None, None
    if mode != "raw" and adapter is not None:
        rt = adapter.route(
            question=sample["question"], story=sample["story"],
            options=sample["options"],
            task_type=sample["metadata"].get("task", ""),
        )
        skill_id = rt.skill_id
        if skill_id and skill_lib.get(skill_id):
            skill_body = skill_lib.get(skill_id).body
    user = build_user_raw(sample) if not skill_body else build_user_with_skill(sample, skill_body)
    try:
        resp = llm.chat(SYSTEM_RAW, user, max_tokens=1024)
        pred = parse_letter(resp)
    except Exception as e:  # noqa: BLE001
        pred = ""
        resp = f"ERROR: {e}"
    return {
        "id": sample["id"], "task": sample["metadata"].get("task"),
        "answer": sample["answer"], "predicted": pred,
        "correct": pred == sample["answer"],
        "skill_id": skill_id, "skill_body_used": bool(skill_body),
        "elapsed_sec": round(time.time() - t0, 2),
        "raw_response_head": (resp or "")[:200],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_task", type=int, default=20)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--modes", nargs="+",
                    default=["raw", "set1_direct", "set2_direct"])
    args = ap.parse_args()

    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY")
    model = os.environ.get("TOM_MODEL", "qwen3.5-27b")
    if not api_key:
        raise SystemExit("set TOM_API_KEY")
    llm = LLMClient(api_base=api_base, api_key=api_key, model=model,
                    temperature=0.0, max_tokens=1024, timeout=120.0, max_retries=3)

    samples = load_tombench()
    pool = stratified(samples, args.per_task)
    print(f"pool: {len(pool)} samples")

    out_dir = Path("results"); out_dir.mkdir(exist_ok=True)
    summary = {}

    for mode in args.modes:
        print(f"\n========== mode = {mode} ==========")
        results_path = out_dir / f"direct_{mode}_results.jsonl"
        # Skip if already complete
        done = set()
        if results_path.exists():
            for ln in open(results_path, encoding="utf-8"):
                ln = ln.strip()
                if ln:
                    try: done.add(json.loads(ln)["id"])
                    except Exception: pass
        pending = [s for s in pool if s["id"] not in done]
        print(f"  resume: done={len(done)} pending={len(pending)}")

        skill_lib = SkillLib()
        adapter = None
        if mode == "set1_direct":
            adapter = Set1Adapter()
            adapter.load_into(skill_lib)
        elif mode == "set2_direct":
            adapter = Set2Adapter(routing_mode="signature")
            adapter.load_into(skill_lib)

        t0 = time.time()
        with ThreadPoolExecutor(max_workers=args.workers) as exe:
            futs = {exe.submit(run_one, s, llm, mode, skill_lib, adapter): s for s in pending}
            for i, f in enumerate(as_completed(futs), 1):
                rec = f.result()
                with open(results_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                if i % 30 == 0:
                    print(f"  {i}/{len(pending)} elapsed={(time.time()-t0)/60:.1f}min")

        # Summary
        records = [json.loads(ln) for ln in open(results_path) if ln.strip()]
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
        summary[mode] = {
            "overall": {"total": total, "correct": correct,
                        "accuracy": round(correct/total, 4) if total else 0},
            "per_task": {t: {"total": n, "correct": c, "accuracy": round(c/n, 4)}
                         for t, (n, c) in per_task.items()},
            "skill_usage": dict(skill_use),
            "no_skill_routed": no_skill,
        }
        print(f"  → {correct}/{total} = {correct/total:.1%}; "
              f"no-skill routed: {no_skill}")

    # Final table
    print("\n" + "="*70)
    tasks = sorted({t for m in summary.values() for t in m["per_task"]})
    header = f"{'task':<32}" + "".join(f"{c:<14}" for c in args.modes)
    print(header)
    print("-"*len(header))
    for t in tasks:
        row = f"{t:<32}"
        for c in args.modes:
            d = summary[c]["per_task"].get(t, {})
            row += f"{d.get('accuracy', 0):>11.1%}   "
        print(row)
    row = f"{'OVERALL':<32}"
    for c in args.modes:
        row += f"{summary[c]['overall']['accuracy']:>11.1%}   "
    print(row)
    json.dump(summary, open(out_dir / "direct_summary.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"\nsummary written to results/direct_summary.json")


if __name__ == "__main__":
    main()
