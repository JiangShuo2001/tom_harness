"""Reference runner for the consolidated harness.

Uses:
  - HarnessRuntime (canonical single-shot path)
  - OraclePicksRouter (per-task best skill from full-benchmark eval)
  - ScalarProceduralValidator (procedural arithmetic check + retry/substitute)

Wires Set1Adapter + Set2Adapter into a SkillLib, runs full ToMBench
main-8 (or a stratified subset), and reports per-task accuracy + how
often the validator fired / corrected.

Usage:
    TOM_API_KEY=... TOM_MODEL=qwen-plus python examples/run_consolidated.py --per_task 20
    TOM_API_KEY=... TOM_MODEL=qwen-plus python examples/run_consolidated.py --full
"""

from __future__ import annotations

import argparse, json, logging, os, random, sys, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "/home/coder/survey_1/symbolictom_repro")

from benchmark_adapters import load_tombench  # type: ignore  # noqa: E402

from tom_harness import LLMClient  # noqa: E402
from tom_harness.runtime import HarnessRuntime, build_default_runtime  # noqa: E402
from tom_harness.routing import OraclePicksRouter  # noqa: E402
from tom_harness.tools.skills import SkillLib  # noqa: E402
from tom_harness.plugins.external_skill_pack.set1_adapter import Set1Adapter  # noqa: E402
from tom_harness.plugins.external_skill_pack.set2_adapter import Set2Adapter  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("consolidated"); logger.setLevel(logging.INFO)


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


def build_runtime(api_base: str, api_key: str, model: str,
                  enable_validator: bool = True) -> HarnessRuntime:
    llm = LLMClient(
        api_base=api_base, api_key=api_key, model=model,
        temperature=0.0, max_tokens=1024, timeout=180.0, max_retries=3,
    )
    skill_lib = SkillLib()
    Set1Adapter(pack_root=Path("/workspace/symbolictom_report/skill_set1")).load_into(skill_lib)
    Set2Adapter(pack_root=Path("/workspace/symbolictom_report/skill_set2/skill_v2"),
                routing_mode="signature").load_into(skill_lib)
    logger.info(f"loaded {len(skill_lib.list_skills())} skills into SkillLib")

    router = OraclePicksRouter()
    return build_default_runtime(
        llm=llm, skill_lib=skill_lib, router=router,
        enable_scalar_validator=enable_validator,
    )


def run_one(runtime: HarnessRuntime, s: dict) -> dict:
    t0 = time.time()
    result = runtime.answer_one(
        question=s["question"], story=s["story"],
        options=s["options"], task_type=s["metadata"]["task"],
    )
    return {
        "id": s["id"], "task": s["metadata"]["task"], "gold": s["answer"],
        "skill_id": result.skill_id, "pred": result.answer,
        "ok": result.answer == s["answer"], "n_llm_calls": result.n_llm_calls,
        "validator_events": result.validator_events, "elapsed": time.time() - t0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_task", type=int, default=20)
    ap.add_argument("--full", action="store_true", help="run full ToMBench main-8")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--no_validator", action="store_true",
                    help="disable validator stack (A/B comparison)")
    ap.add_argument("--out_dir", default="results_consolidated")
    args = ap.parse_args()

    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY")
    model = os.environ.get("TOM_MODEL", "qwen-plus")
    if not api_key:
        raise SystemExit("ERROR: set TOM_API_KEY env var")

    runtime = build_runtime(api_base, api_key, model,
                            enable_validator=not args.no_validator)
    logger.info(f"validators: {[v.__class__.__name__ for v in runtime.validators]}")

    samples = [s for s in load_tombench() if s["metadata"].get("task") in MAIN_8]
    if not args.full:
        samples = stratified(samples, args.per_task)
    logger.info(f"pool: {len(samples)} samples (full={args.full})")

    out_dir = Path(args.out_dir); out_dir.mkdir(exist_ok=True)
    suffix = "novalidator" if args.no_validator else "validator"
    out_path = out_dir / f"consolidated_{suffix}_{'full' if args.full else f'pt{args.per_task}'}.jsonl"
    done = set()
    if out_path.exists():
        for ln in open(out_path, encoding="utf-8"):
            try: done.add(json.loads(ln)["id"])
            except Exception: pass
    pending = [s for s in samples if s["id"] not in done]
    logger.info(f"resume: done={len(done)} pending={len(pending)}")

    f = open(out_path, "a", encoding="utf-8")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_one, runtime, s): s for s in pending}
        n_done = 0
        for fut in as_completed(futs):
            r = fut.result()
            f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
            n_done += 1
            if n_done % 200 == 0:
                logger.info(f"  progress: {n_done}/{len(pending)} ({time.time()-t0:.1f}s)")
    f.close()
    logger.info(f"done in {time.time()-t0:.1f}s")

    # Reload & summarize
    rows = []
    for ln in open(out_path, encoding="utf-8"):
        try: rows.append(json.loads(ln))
        except Exception: pass

    per_task = defaultdict(lambda: {"correct": 0, "total": 0,
                                    "validator_fires": 0, "validator_substitutes": 0})
    for r in rows:
        c = per_task[r["task"]]
        c["total"] += 1
        if r["ok"]: c["correct"] += 1
        for ev in r.get("validator_events", []):
            if not ev.get("valid", True):
                c["validator_fires"] += 1
                if ev.get("had_suggestion"):
                    c["validator_substitutes"] += 1
    for c in per_task.values():
        c["accuracy"] = round(c["correct"] / c["total"], 4) if c["total"] else 0.0

    total_correct = sum(c["correct"] for c in per_task.values())
    total_total = sum(c["total"] for c in per_task.values())
    overall = round(total_correct / total_total, 4) if total_total else 0.0

    print(f"\n{'='*78}")
    print(f"CONSOLIDATED RUNTIME — {model}, validator={'ON' if not args.no_validator else 'OFF'}")
    print(f"{'='*78}")
    print(f"{'task':<32} {'acc':<8} {'fires':<8} {'subst':<8}")
    for t in sorted(per_task):
        c = per_task[t]
        print(f"  {t:<30} {c['accuracy']:.3f}    {c['validator_fires']:<6}  {c['validator_substitutes']:<6}")
    print(f"  {'OVERALL':<30} {overall:.3f}    n={total_total}")

    summary = {"overall": overall, "n": total_total, "per_task": dict(per_task),
               "model": model, "validator": not args.no_validator}
    (out_dir / f"summary_{suffix}_{'full' if args.full else f'pt{args.per_task}'}.json"
     ).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
