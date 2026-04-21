"""Run the harness on ToMBench — no-tools mode (plan + execute only).

Usage examples:
  # Run 10 samples per task from the main-8
  python examples/run_tombench_harness.py --limit 10

  # Run only "False Belief Task", 5 samples starting from the 20th
  python examples/run_tombench_harness.py --tasks "False Belief Task" --limit 5 --offset 20

  # Run ALL samples across all 20 tasks
  python examples/run_tombench_harness.py --all_tasks --limit 0

  # Specify a custom data directory
  python examples/run_tombench_harness.py --data_dir /path/to/ToMBench

Outputs (saved to results/<tag>/):
  - results.jsonl        per-sample records
  - stats.json           per-task + overall accuracy
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

from benchmark.load_tombench import load_tombench  # noqa: E402

from tom_harness import (  # noqa: E402
    ContextManager, Executor, LLMClient, Planner, Scheduler, ToolRegistry,
)
from tom_harness.hooks import HookRegistry  # noqa: E402
from tom_harness.scheduler import SchedulerConfig  # noqa: E402
from tom_harness.tools import MemoryStore, SkillLib  # noqa: E402


class _FrameworkConsoleFilter(logging.Filter):
    """Block tom_harness.* messages on console unless --verbose removes this filter."""
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.name.startswith("tom_harness")


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("harness_bench")

# Framework logger: level=DEBUG so file handler captures everything.
# Console suppression via filter (removed by --verbose).
_framework_logger = logging.getLogger("tom_harness")
_framework_logger.setLevel(logging.DEBUG)
_console_handler = logging.getLogger().handlers[0] if logging.getLogger().handlers else None
_console_filter = _FrameworkConsoleFilter()
if _console_handler:
    _console_handler.addFilter(_console_filter)

from dotenv import load_dotenv
load_dotenv()  # load env vars from .env file in project root


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
    memory    = MemoryStore()
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


def select_samples(
    samples: list[dict],
    *,
    tasks: set[str] | None,
    offset: int,
    limit: int,
) -> list[dict]:
    """Filter by task, then take up to `limit` samples per task starting from `offset`.

    Args:
        tasks: Set of task names to include. None = all tasks.
        offset: Skip the first N samples within each task.
        limit: Max samples per task after offset (0 = no limit).
    """
    # 1) Filter by task name
    if tasks:
        samples = [s for s in samples if s["metadata"].get("task", "") in tasks]

    # 2) Group by task, apply offset + limit per task
    buckets: dict[str, list[dict]] = defaultdict(list)
    for s in samples:
        buckets[s["metadata"].get("task", "")].append(s)

    pool: list[dict] = []
    for t in sorted(buckets):
        bucket = buckets[t]
        sliced = bucket[offset:]
        if limit > 0:
            sliced = sliced[:limit]
        pool.extend(sliced)

    return pool


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
        scheduler = scheduler_factory()
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
    ap = argparse.ArgumentParser(
        description="Run ToM harness on ToMBench (no-tools baseline).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ── data selection ────────────────────────────────────────────────────
    data_grp = ap.add_argument_group("data selection")
    data_grp.add_argument(
        "--data_dir", type=str, default=None,
        help="Path to ToMBench JSONL directory (default: benchmark/ToMBench/).",
    )
    data_grp.add_argument(
        "--tasks", type=str, default=None,
        help='Comma-separated task names, e.g. "False Belief Task,Hinting Task Test". '
             "Default: the 8 main tasks. Use --all_tasks to include every task.",
    )
    data_grp.add_argument(
        "--all_tasks", action="store_true",
        help="Include all 20 task types (overrides --tasks).",
    )
    data_grp.add_argument(
        "--limit", type=int, default=20,
        help="Max samples PER TASK (default: 20, 0 = no limit).",
    )
    data_grp.add_argument(
        "--offset", type=int, default=0,
        help="Skip the first N samples within each task (default: 0).",
    )

    # ── execution ─────────────────────────────────────────────────────────
    exec_grp = ap.add_argument_group("execution")
    exec_grp.add_argument("--workers", type=int, default=8, help="Parallel workers (default: 8).")
    exec_grp.add_argument("--no_resume", action="store_true", help="Ignore previous results and start fresh.")
    exec_grp.add_argument("--verbose", "-v", action="store_true",
                          help="Show detailed plan/execute trace for each sample.")

    # ── output ────────────────────────────────────────────────────────────
    out_grp = ap.add_argument_group("output")
    out_grp.add_argument("--out_dir", default="results", help="Root output directory (default: results/).")
    out_grp.add_argument("--tag", default="notools", help="Run tag — results saved under <out_dir>/<tag>/ (default: notools).")

    args = ap.parse_args()

    # ── resolve output paths ──────────────────────────────────────────────
    out_dir = Path(args.out_dir) / args.tag
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.jsonl"
    stats_path   = out_dir / "stats.json"
    log_path     = out_dir / "run.log"

    # ── logging setup ─────────────────────────────────────────────────────
    if args.verbose and _console_handler:
        _console_handler.removeFilter(_console_filter)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().addHandler(file_handler)

    if args.no_resume and results_path.exists():
        results_path.unlink()

    # ── load & select samples ─────────────────────────────────────────────
    samples = load_tombench(data_dir=args.data_dir)
    logger.info(f"Loaded {len(samples)} total ToMBench samples")

    if args.all_tasks:
        task_filter = None
    elif args.tasks:
        task_filter = {t.strip() for t in args.tasks.split(",")}
    else:
        task_filter = MAIN_8

    pool = select_samples(
        samples,
        tasks=task_filter,
        offset=args.offset,
        limit=args.limit,
    )

    task_counts = defaultdict(int)
    for s in pool:
        task_counts[s["metadata"]["task"]] += 1
    logger.info(f"Selected {len(pool)} samples across {len(task_counts)} tasks "
                f"(offset={args.offset}, limit={args.limit or 'all'} per task)")
    for t in sorted(task_counts):
        logger.info(f"  {t:<40} {task_counts[t]:>4}")

    # ── resume support ────────────────────────────────────────────────────
    done_ids: set[str] = set()
    if results_path.exists():
        with open(results_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    done_ids.add(json.loads(line)["id"])
                except Exception:  # noqa: BLE001
                    pass
    pending = [s for s in pool if s["id"] not in done_ids]
    if done_ids:
        logger.info(f"Resuming: {len(done_ids)} done, {len(pending)} pending")

    if not pending:
        logger.info("Nothing to run.")
        _print_and_save_stats(results_path, stats_path, pool, args.tag)
        return

    # ── run ────────────────────────────────────────────────────────────────
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

    # ── stats ──────────────────────────────────────────────────────────────
    _print_and_save_stats(results_path, stats_path, pool, args.tag)


def _print_and_save_stats(results_path: Path, stats_path: Path, pool: list, tag: str) -> None:
    all_records = _load_all(results_path)
    if not all_records:
        logger.info("No results to summarize.")
        return
    stats = _compute_stats(all_records, pool)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    sep = "=" * 60
    logger.info(f"\n{sep}\nHarness [{tag}] results  →  {stats_path}\n{sep}")
    logger.info(f"Overall: {stats['overall']['correct']}/{stats['overall']['total']} "
                f"= {stats['overall']['accuracy']:.1%}  (errors: {stats['overall']['errors']})")
    logger.info(f"{'Task':<40} {'N':>4} {'Acc':>7}  {'Err':>4}")
    logger.info("-" * 60)
    for t in sorted(stats["per_task"]):
        ts = stats["per_task"][t]
        logger.info(f"  {t:<38} {ts['total']:>4} {ts['accuracy']:>7.1%}  {ts['errors']:>4}")
    logger.info(f"\nResults saved to: {results_path}")
    logger.info(f"Stats   saved to: {stats_path}")
    logger.info(f"Log     saved to: {results_path.parent / 'run.log'}")


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
