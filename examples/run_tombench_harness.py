"""Run the harness on ToMBench — single-shot runtime with v2 skill/RAG/memory.

Usage examples:
  # Run 10 samples per task, no tools
  python examples/run_tombench_harness.py --limit 10

  # Run with skill routing + RAG + memory selector
  python examples/run_tombench_harness.py --limit 10 --skill --rag --memory

  # Run only "False Belief Task", 5 samples
  python examples/run_tombench_harness.py --tasks "False Belief Task" --limit 5 --skill

  # Run ALL samples across all tasks
  python examples/run_tombench_harness.py --all_tasks --limit 0

Env vars for test model:
  TOM_API_BASE, TOM_API_KEY, TOM_MODEL, TOM_TEMPERATURE

Env vars for helper model (selector/classifier, independent of test model):
  HELPER_API_BASE, HELPER_API_KEY, HELPER_MODEL

Outputs (saved to <out_dir>/):
  - results.jsonl        per-sample records
  - stats.json           per-task + overall accuracy
"""

from __future__ import annotations

import argparse
import json
import logging
import logging.handlers
import os
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmark.load_tombench import load_tombench  # noqa: E402

from tom_harness import LLMClient, build_default_runtime  # noqa: E402
from tom_harness.routing import SkillV4Router, NoOpRouter  # noqa: E402
from tom_harness.tools.rag_v2 import RAGv2Engine, CategoryClassifier  # noqa: E402


class _FrameworkConsoleFilter(logging.Filter):
    """Block tom_harness.* messages on console unless --verbose."""
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.name.startswith("tom_harness")


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("harness_bench")

_framework_logger = logging.getLogger("tom_harness")
_framework_logger.setLevel(logging.DEBUG)
_console_handler = logging.getLogger().handlers[0] if logging.getLogger().handlers else None
_console_filter = _FrameworkConsoleFilter()
if _console_handler:
    _console_handler.addFilter(_console_filter)

from dotenv import load_dotenv  # noqa: E402
load_dotenv()


def build_harness(
    *,
    shared_rag: RAGv2Engine | None = None,
    shared_memory=None,
    cache_dir: str | None = None,
    enable_skill: bool = False,
    enable_validator: bool = True,
):
    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY")
    model = os.environ.get("TOM_MODEL", "qwen3-32b")
    temperature = float(os.environ.get("TOM_TEMPERATURE", "0.0"))
    if not api_key:
        raise SystemExit("ERROR: set the TOM_API_KEY env var")

    llm = LLMClient(
        api_base=api_base, api_key=api_key, model=model,
        temperature=temperature, max_tokens=2048, timeout=120.0, max_retries=3,
    )
    if cache_dir:
        llm.set_cache_dir(cache_dir)

    router = SkillV4Router(llm=llm) if enable_skill else NoOpRouter()

    return build_default_runtime(
        llm=llm,
        router=router,
        rag_engine=shared_rag if (shared_rag is not None and shared_rag.size() > 0) else None,
        memory=shared_memory,
        enable_scalar_validator=enable_validator,
    )


def select_samples(
    samples: list[dict],
    *,
    tasks: set[str] | None,
    offset: int,
    limit: int,
) -> list[dict]:
    if tasks:
        samples = [s for s in samples if s["metadata"].get("task", "") in tasks]

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


def process_one(runtime_factory, sample, timeout_sec: float = 180.0):
    buf_handler = logging.handlers.MemoryHandler(capacity=10000, flushLevel=logging.CRITICAL + 1)
    buf_handler.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    buf_handler.setFormatter(fmt)
    framework_logger = logging.getLogger("tom_harness")
    framework_logger.addHandler(buf_handler)

    t0 = time.time()
    rec = {
        "id": sample["id"],
        "task": sample["metadata"].get("task"),
        "answer": sample["answer"],
        "predicted": "",
        "correct": False,
        "skill_id": None,
        "n_llm_calls": 0,
        "elapsed_sec": 0.0,
        "error": None,
    }
    try:
        runtime = runtime_factory()
        result = runtime.answer_one(
            question=sample["question"],
            story=sample["story"],
            options=sample["options"],
            task_type=sample["metadata"].get("task"),
        )
        rec["predicted"] = result.answer
        rec["correct"] = (result.answer == sample["answer"])
        rec["skill_id"] = result.skill_id
        rec["n_llm_calls"] = result.n_llm_calls
        if result.thinking:
            rec["thinking"] = result.thinking
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["elapsed_sec"] = round(time.time() - t0, 2)

    log_lines = []
    for log_record in buf_handler.buffer:
        log_lines.append(fmt.format(log_record))
    framework_logger.removeHandler(buf_handler)
    buf_handler.close()

    return rec, log_lines


def main():
    ap = argparse.ArgumentParser(
        description="Run ToM harness on ToMBench (single-shot runtime).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    data_grp = ap.add_argument_group("data selection")
    data_grp.add_argument("--data_dir", type=str, default=None)
    data_grp.add_argument("--tasks", type=str, default=None,
                          help='Comma-separated task names.')
    data_grp.add_argument("--limit", type=int, default=20,
                          help="Max samples PER TASK (default: 20, 0 = no limit).")
    data_grp.add_argument("--offset", type=int, default=0)

    exec_grp = ap.add_argument_group("execution")
    exec_grp.add_argument("--workers", type=int, default=8)
    exec_grp.add_argument("--verbose", "-v", action="store_true")

    out_grp = ap.add_argument_group("output")
    out_grp.add_argument("--out_dir", default="results")

    rag_grp = ap.add_argument_group("RAG retrieval (ToM rules)")
    rag_grp.add_argument("--rag", action="store_true", help="Enable RAG retrieval.")
    rag_grp.add_argument("--rag_data_dir", type=str, default="tom_harness/tools/rag_v2_data")
    rag_grp.add_argument("--rag_index_dir", type=str, default="tom_harness/tools/rag_v2_index")
    rag_grp.add_argument("--rag_model", type=str, default="model/bge-m3")
    rag_grp.add_argument("--rag_category_filter", action="store_true", default=False,
                         help="Enable category-based metadata filtering in RAG search.")

    mem_grp = ap.add_argument_group("Memory playbook (selector-based)")
    mem_grp.add_argument("--memory", action="store_true")
    mem_grp.add_argument("--memory_playbook", type=str,
                         default="memory_playbook/playbook/final_playbook.txt",
                         help="Path to the playbook .txt file.")

    helper_grp = ap.add_argument_group("Helper model (selector / classifier)")
    helper_grp.add_argument("--helper_api_base", type=str, default=None,
                            help="API base for helper model (default: HELPER_API_BASE env var).")
    helper_grp.add_argument("--helper_api_key", type=str, default=None,
                            help="API key for helper model (default: HELPER_API_KEY env var).")
    helper_grp.add_argument("--helper_model", type=str, default=None,
                            help="Model name for helper model (default: HELPER_MODEL env var).")

    skill_grp = ap.add_argument_group("Skill injection (v4)")
    skill_grp.add_argument("--skill", action="store_true",
                           help="Enable LLM-routed skill injection (22 skills).")

    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.jsonl"
    stats_path = out_dir / "stats.json"
    log_path = out_dir / "run.log"

    if args.verbose and _console_handler:
        _console_handler.removeFilter(_console_filter)

    _log_file_lock = threading.Lock()
    log_path.write_text("", encoding="utf-8")

    if results_path.exists():
        results_path.unlink()

    samples = load_tombench(data_dir=args.data_dir)
    logger.info("Loaded %d total ToMBench samples", len(samples))

    task_filter = {t.strip() for t in args.tasks.split(",")} if args.tasks else None

    pool = select_samples(samples, tasks=task_filter, offset=args.offset, limit=args.limit)

    task_counts = defaultdict(int)
    for s in pool:
        task_counts[s["metadata"]["task"]] += 1
    logger.info("Selected %d samples across %d tasks (offset=%d, limit=%s per task)",
                len(pool), len(task_counts), args.offset, args.limit or "all")
    for t in sorted(task_counts):
        logger.info("  %-40s %4d", t, task_counts[t])

    if not pool:
        logger.info("Nothing to run.")
        return

    # ── resolve helper model config ────────────────────────────────────
    helper_api_base = args.helper_api_base or os.environ.get("HELPER_API_BASE", "")
    helper_api_key = args.helper_api_key or os.environ.get("HELPER_API_KEY", "")
    helper_model = args.helper_model or os.environ.get("HELPER_MODEL", "")

    # ── RAG setup ────────────────────────────────────────────────────────
    shared_rag: RAGv2Engine | None = None
    if args.rag:
        classifier = None
        if helper_api_key and helper_model:
            classifier = CategoryClassifier(
                api_base=helper_api_base, api_key=helper_api_key, model=helper_model,
            )
        shared_rag = RAGv2Engine(
            data_dir=args.rag_data_dir,
            index_dir=args.rag_index_dir,
            model_name=args.rag_model,
            use_category_filter=args.rag_category_filter,
            classifier=classifier,
        )
        shared_rag.build_index()
        if shared_rag.size() > 0:
            logger.info("RAG enabled: %d rules indexed", shared_rag.size())
        else:
            logger.info("RAG data not found — running without RAG")
            shared_rag = None

    # ── Memory setup (selector-based) ───────────────────────────────────
    shared_memory = None
    if args.memory:
        if not helper_api_key or not helper_model:
            logger.warning("Memory requires HELPER_API_KEY and HELPER_MODEL — skipping")
        elif not Path(args.memory_playbook).exists():
            logger.warning("Playbook file %s not found — skipping memory", args.memory_playbook)
        else:
            from memory_playbook import Memory, SelectorConfig
            selector_cfg = SelectorConfig(
                provider="custom",
                api_key=helper_api_key,
                model=helper_model,
                base_url=helper_api_base or None,
            )
            shared_memory = Memory(args.memory_playbook, selector_cfg)
            logger.info("Memory enabled: playbook=%s, selector_model=%s",
                        args.memory_playbook, helper_model)

    if args.skill:
        logger.info("Skill injection enabled (v4: 22 LLM-routed skills)")

    # ── run ───────────────────────────────────────────────────────────────
    llm_cache_dir = str(out_dir / "llm_cache")
    runtime_factory = lambda: build_harness(  # noqa: E731
        shared_rag=shared_rag,
        shared_memory=shared_memory,
        cache_dir=llm_cache_dir,
        enable_skill=args.skill,
    )
    t_start = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as exe:
        futs = {exe.submit(process_one, runtime_factory, s): s for s in pool}
        for fut in as_completed(futs):
            s = futs[fut]
            try:
                rec, log_lines = fut.result(timeout=360)
            except Exception as e:
                rec = {"id": s["id"], "task": s["metadata"].get("task"), "answer": s["answer"],
                       "predicted": "", "correct": False, "error": f"outer: {e}",
                       "skill_id": None, "n_llm_calls": 0, "elapsed_sec": 0.0}
                log_lines = []
            with open(results_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if log_lines:
                with _log_file_lock:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write("\n".join(log_lines) + "\n")
            completed += 1
            if completed % 10 == 0:
                acc_so_far = _live_accuracy(results_path)
                elapsed = (time.time() - t_start) / 60
                logger.info("progress=%d/%d elapsed=%.1fmin running_acc=%.3f",
                            completed, len(pool), elapsed, acc_so_far)

    _print_and_save_stats(results_path, stats_path, pool)


def _print_and_save_stats(results_path: Path, stats_path: Path, pool: list) -> None:
    all_records = _load_all(results_path)
    if not all_records:
        logger.info("No results to summarize.")
        return
    stats = _compute_stats(all_records, pool)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    sep = "=" * 60
    logger.info("\n%s\nHarness results  →  %s\n%s", sep, stats_path, sep)
    logger.info("Overall: %d/%d = %.1f%%  (errors: %d)",
                stats["overall"]["correct"], stats["overall"]["total"],
                stats["overall"]["accuracy"] * 100, stats["overall"]["errors"])
    logger.info("%-40s %4s %7s  %4s", "Task", "N", "Acc", "Err")
    logger.info("-" * 60)
    for t in sorted(stats["per_task"]):
        ts = stats["per_task"][t]
        logger.info("  %-38s %4d %6.1f%%  %4d", t, ts["total"], ts["accuracy"] * 100, ts["errors"])
    logger.info("\nResults saved to: %s", results_path)
    logger.info("Stats   saved to: %s", stats_path)
    logger.info("Log     saved to: %s", results_path.parent / "run.log")


def _live_accuracy(path: Path) -> float:
    n = c = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                n += 1
                c += int(bool(r.get("correct")))
            except Exception:
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
            except Exception:
                pass
    return out


def _compute_stats(records, pool):
    total = len(records)
    correct = sum(1 for r in records if r.get("correct"))
    errors = sum(1 for r in records if r.get("error") or not r.get("predicted"))
    per_task = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0, "avg_elapsed": 0.0})
    elapsed_sum = defaultdict(float)
    for r in records:
        t = r.get("task", "unknown")
        per_task[t]["total"] += 1
        per_task[t]["correct"] += int(bool(r.get("correct")))
        per_task[t]["errors"] += int(bool(r.get("error") or not r.get("predicted")))
        elapsed_sum[t] += float(r.get("elapsed_sec", 0.0) or 0.0)
    for t, d in per_task.items():
        valid_n = d["total"] - d["errors"]
        d["accuracy"] = d["correct"] / valid_n if valid_n > 0 else 0.0
        d["avg_elapsed"] = round(elapsed_sum[t] / (d["total"] or 1), 2)
    valid_total = total - errors
    return {
        "overall": {
            "total": total, "correct": correct, "errors": errors,
            "accuracy": round(correct / valid_total, 4) if valid_total else 0,
        },
        "per_task": dict(per_task),
        "mode": "single_shot_v2",
    }


if __name__ == "__main__":
    main()
