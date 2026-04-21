"""Run the harness on ToMBench — no-tools mode (plan + execute only).

Per the senior's directive: "先不加任何工具，看看只用计划模块和执行模块能跑到啥程度".

Mode semantics:
  - MemoryStore exists (empty, so mandatory warm-start returns 0 hits)
  - No Memory/Skill/RAG tools registered → plans are all tool_type=none
  - ToM plugin NOT installed (generic behavior only)
  - Benchmark: stratified sample across the 8 main tasks

Outputs:
  - results/harness_notools_results.jsonl  (one record per sample)
  - results/harness_notools_stats.json     (per-task + overall accuracy)
  - results/harness_notools_plans/         (plan dumps for inspection)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "/home/coder/survey_1/symbolictom_repro")  # for benchmark_adapters

from benchmark_adapters import load_tombench  # type: ignore  # noqa: E402

from tom_harness import (  # noqa: E402
    ContextManager, Executor, LLMClient, Planner, Scheduler, ToolRegistry,
)
from tom_harness.hooks import HookRegistry  # noqa: E402
from tom_harness.scheduler import SchedulerConfig  # noqa: E402
from tom_harness.tools import MemoryStore, SkillLib  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("harness_bench")
logger.setLevel(logging.INFO)


MAIN_8 = {
    "Unexpected Outcome Test",
    "Scalar Implicature Test",
    "Persuasion Story Task",
    "False Belief Task",
    "Ambiguous Story Task",
    "Hinting Task Test",
    "Strange Story Task",
    "Faux-pas Recognition Test",
}


def build_harness():
    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key  = os.environ.get("TOM_API_KEY")
    model    = os.environ.get("TOM_MODEL",    "qwen3-32b")
    if not api_key:
        raise SystemExit("ERROR: set the TOM_API_KEY env var (see README > Configuration)")

    llm = LLMClient(
        api_base=api_base, api_key=api_key, model=model,
        temperature=0.0, max_tokens=2048, timeout=120.0, max_retries=3,
    )
    registry  = ToolRegistry()
    ctx       = ContextManager()
    hooks     = HookRegistry()
    memory    = MemoryStore()  # empty, but planner still queries it
    skill_lib = SkillLib()

    ctx.install_fixed(
        system_identity="A ToM-focused reasoning agent answering multiple-choice questions about characters' mental states.",
        tool_schema_summary=registry.schema_summary(),
        safety_policy="Base answers ONLY on story facts. Do not use outside knowledge. Pick exactly one option A/B/C/D.",
    )

    planner = Planner(llm=llm, registry=registry, context=ctx, hooks=hooks, memory=memory)
    executor = Executor(llm=llm, registry=registry, context=ctx, hooks=hooks, skill_lib=skill_lib)
    scheduler = Scheduler(
        planner=planner, executor=executor, registry=registry, context=ctx,
        hooks=hooks, memory=memory,
        config=SchedulerConfig(max_replans=1, persist_memories_on_success=False),
    )
    return scheduler


def stratified_sample(samples, per_task: int, tasks=MAIN_8, seed: int = 42):
    """Take up to per_task samples per main task (deterministic shuffle)."""
    import random
    rng = random.Random(seed)
    buckets = defaultdict(list)
    for s in samples:
        t = s["metadata"].get("task", "")
        if t in tasks:
            buckets[t].append(s)
    out = []
    for t in sorted(buckets):
        bucket = buckets[t]
        rng.shuffle(bucket)
        out.extend(bucket[:per_task])
    return out


def process_one(scheduler_factory, sample, timeout_sec: float = 180.0):
    t0 = time.time()
    rec = {
        "id": sample["id"],
        "task": sample["metadata"].get("task"),
        "answer": sample["answer"],
        "predicted": "",
        "correct": False,
        "num_phases": 0,
        "num_steps": 0,
        "replans": 0,
        "elapsed_sec": 0.0,
        "plan_task_type": "",
        "phase_names": [],
        "error": None,
    }
    try:
        scheduler = scheduler_factory()  # fresh scheduler per sample (isolated context)
        result = scheduler.run(
            task_id=sample["id"],
            question=f"{sample['story']}\n\nQuestion: {sample['question']}",
            options=sample["options"],
            dataset="ToMBench",
        )
        rec["predicted"] = result.answer
        rec["correct"] = (result.answer == sample["answer"])
        rec["num_phases"] = len(result.plan.phases)
        rec["num_steps"] = len(result.traces)
        rec["replans"] = int(result.metadata.get("replans", 0))
        rec["plan_task_type"] = result.plan.task_type
        rec["phase_names"] = [p.phase_name for p in result.plan.phases]
        rec["error"] = result.error
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["elapsed_sec"] = round(time.time() - t0, 2)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_task", type=int, default=20, help="Samples per main task (8 tasks × per_task)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out_dir", default="results")
    ap.add_argument("--tag", default="notools")
    ap.add_argument("--limit", type=int, default=0, help="Optional absolute cap")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / f"harness_{args.tag}_results.jsonl"
    stats_path   = out_dir / f"harness_{args.tag}_stats.json"

    samples = load_tombench()
    pool = stratified_sample(samples, args.per_task)
    if args.limit:
        pool = pool[:args.limit]
    logger.info(f"Loaded {len(samples)} total ToMBench samples; using {len(pool)} stratified")

    # Resume support
    done_ids: set[str] = set()
    if results_path.exists():
        with open(results_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    done_ids.add(r["id"])
                except Exception:  # noqa: BLE001
                    pass
    pending = [s for s in pool if s["id"] not in done_ids]
    logger.info(f"Resume: {len(done_ids)} done, {len(pending)} pending")

    t_start = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as exe:
        futs = {exe.submit(process_one, build_harness, s): s for s in pending}
        for fut in as_completed(futs):
            s = futs[fut]
            try:
                rec = fut.result(timeout=360)
            except Exception as e:  # noqa: BLE001
                rec = {"id": s["id"], "task": s["metadata"].get("task"), "answer": s["answer"],
                       "predicted": "", "correct": False, "error": f"outer: {e}",
                       "num_phases": 0, "num_steps": 0, "replans": 0,
                       "elapsed_sec": 0.0, "plan_task_type": "", "phase_names": []}
            with open(results_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            completed += 1
            if completed % 10 == 0:
                acc_so_far = _live_accuracy(results_path)
                elapsed = (time.time() - t_start) / 60
                logger.info(f"progress={completed}/{len(pending)} elapsed={elapsed:.1f}min running_acc={acc_so_far:.3f}")

    # Stats
    all_records = _load_all(results_path)
    stats = _compute_stats(all_records, pool)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    logger.info(f"\n{'='*60}\nHarness {args.tag} results\n{'='*60}")
    logger.info(f"Overall: {stats['overall']['correct']}/{stats['overall']['total']} = {stats['overall']['accuracy']:.1%}")
    for t in sorted(stats["per_task"]):
        ts = stats["per_task"][t]
        logger.info(f"  {t:<35} {ts['total']:>4} {ts['accuracy']:>7.1%}  (err {ts['errors']})")


def _live_accuracy(path: Path) -> float:
    n = 0
    c = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                n += 1
                c += int(bool(r.get("correct")))
            except Exception:  # noqa: BLE001
                pass
    return c / n if n else 0.0


def _load_all(path: Path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    return out


def _compute_stats(records, pool):
    total = len(records)
    correct = sum(1 for r in records if r.get("correct"))
    errors = sum(1 for r in records if r.get("error"))
    per_task = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0,
                                    "avg_phases": 0.0, "avg_steps": 0.0,
                                    "avg_elapsed": 0.0, "task_type_dist": {}})
    phases_sum = defaultdict(int); steps_sum = defaultdict(int); elapsed_sum = defaultdict(float)
    for r in records:
        t = r.get("task", "unknown")
        per_task[t]["total"] += 1
        per_task[t]["correct"] += int(bool(r.get("correct")))
        per_task[t]["errors"] += int(bool(r.get("error")))
        phases_sum[t] += int(r.get("num_phases", 0) or 0)
        steps_sum[t]  += int(r.get("num_steps", 0) or 0)
        elapsed_sum[t] += float(r.get("elapsed_sec", 0.0) or 0.0)
        tt = r.get("plan_task_type", "") or "unknown"
        per_task[t]["task_type_dist"][tt] = per_task[t]["task_type_dist"].get(tt, 0) + 1
    for t, d in per_task.items():
        n = d["total"] or 1
        d["accuracy"] = d["correct"] / n
        d["avg_phases"]  = round(phases_sum[t]  / n, 2)
        d["avg_steps"]   = round(steps_sum[t]   / n, 2)
        d["avg_elapsed"] = round(elapsed_sum[t] / n, 2)
    return {
        "overall": {
            "total": total, "correct": correct, "errors": errors,
            "accuracy": round(correct / total, 4) if total else 0,
        },
        "per_task": dict(per_task),
        "mode": "no_tools",
    }


if __name__ == "__main__":
    main()
