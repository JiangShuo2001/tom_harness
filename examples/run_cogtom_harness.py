"""Run the harness on CogToM.

Usage examples:
  # Run 10 samples per category
  python examples/run_cogtom_harness.py --limit 10

  # Run only "Belief" category, 5 samples starting from the 20th
  python examples/run_cogtom_harness.py --category "Belief" --limit 5 --offset 20

  # Run all samples
  python examples/run_cogtom_harness.py --limit 0

Outputs (saved to results/<tag>/):
  - results.jsonl        per-sample records
  - stats.json           per-category + overall accuracy
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

from benchmark.load_cogtom import load_cogtom  # noqa: E402

from tom_harness import (  # noqa: E402
    ContextManager, Executor, LLMClient, Planner, Scheduler, ToolRegistry,
)
from tom_harness.hooks import HookRegistry  # noqa: E402
from tom_harness.scheduler import SchedulerConfig  # noqa: E402
from tom_harness.tools import MemoryStore, RAGEngine, SkillLib, MemoryPlaybook  # noqa: E402


class _FrameworkConsoleFilter(logging.Filter):
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

from dotenv import load_dotenv
load_dotenv()


def build_harness(shared_rag: RAGEngine | None = None, shared_playbook: MemoryPlaybook | None = None, cache_dir: str | None = None):
    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key  = os.environ.get("TOM_API_KEY")
    model    = os.environ.get("TOM_MODEL",    "qwen3-32b")
    if not api_key:
        raise SystemExit("ERROR: set the TOM_API_KEY env var (see README > Configuration)")

    llm = LLMClient(
        api_base=api_base, api_key=api_key, model=model,
        temperature=0.0, max_tokens=2048, timeout=120.0, max_retries=3,
    )
    if cache_dir:
        llm.set_cache_dir(cache_dir)
    registry  = ToolRegistry()
    ctx       = ContextManager()
    hooks     = HookRegistry()
    memory    = MemoryStore()
    skill_lib = SkillLib()

    if shared_rag is not None and shared_rag.size() > 0:
        registry.register(shared_rag)

    if shared_playbook is not None and shared_playbook.ready:
        ctx.install_playbook(shared_playbook.content)

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
    categories: set[str] | None,
    offset: int,
    limit: int,
) -> list[dict]:
    if categories:
        samples = [s for s in samples if s["metadata"].get("category", "") in categories]

    buckets: dict[str, list[dict]] = defaultdict(list)
    for s in samples:
        buckets[s["metadata"].get("category", "")].append(s)

    pool: list[dict] = []
    for cat in sorted(buckets):
        bucket = buckets[cat]
        sliced = bucket[offset:]
        if limit > 0:
            sliced = sliced[:limit]
        pool.extend(sliced)

    return pool


def process_one(scheduler_factory, sample, timeout_sec: float = 180.0):
    buf_handler = logging.handlers.MemoryHandler(capacity=10000, flushLevel=logging.CRITICAL + 1)
    buf_handler.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    buf_handler.setFormatter(fmt)
    framework_logger = logging.getLogger("tom_harness")
    framework_logger.addHandler(buf_handler)

    t0 = time.time()
    rec = {
        "id": sample["id"],
        "category": sample["metadata"].get("category"),
        "subcategory": sample["metadata"].get("subcategory"),
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
            dataset="CogToM",
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

    log_lines = []
    for log_record in buf_handler.buffer:
        log_lines.append(fmt.format(log_record))
    framework_logger.removeHandler(buf_handler)
    buf_handler.close()

    return rec, log_lines


def main():
    ap = argparse.ArgumentParser(
        description="Run ToM harness on CogToM.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ── data selection ────────────────────────────────────────────────────
    data_grp = ap.add_argument_group("data selection")
    data_grp.add_argument(
        "--data_dir", type=str, default=None,
        help="Path to CogToM data directory (default: benchmark/cogtom/).",
    )
    data_grp.add_argument(
        "--category", type=str, default=None,
        help='Comma-separated category names, e.g. "Belief,Emotion". '
             "Default: all categories. "
             "Available: Belief, Comprehensive, Desire, Emotion, Intention, Knowledge, Non-literal, Percept.",
    )
    data_grp.add_argument(
        "--limit", type=int, default=20,
        help="Max samples PER CATEGORY (default: 20, 0 = no limit).",
    )
    data_grp.add_argument(
        "--offset", type=int, default=0,
        help="Skip the first N samples within each category (default: 0).",
    )

    # ── execution ─────────────────────────────────────────────────────────
    exec_grp = ap.add_argument_group("execution")
    exec_grp.add_argument("--workers", type=int, default=8, help="Parallel workers (default: 8).")
    exec_grp.add_argument("--verbose", "-v", action="store_true",
                          help="Show detailed plan/execute trace for each sample.")

    # ── output ────────────────────────────────────────────────────────────
    out_grp = ap.add_argument_group("output")
    out_grp.add_argument("--out_dir", default="results", help="Root output directory (default: results/).")
    out_grp.add_argument("--tag", default="cogtom", help="Run tag — results saved under <out_dir>/<tag>/ (default: cogtom).")

    # ── RAG ───────────────────────────────────────────────────────────────
    rag_grp = ap.add_argument_group("RAG retrieval")
    rag_grp.add_argument("--rag", action="store_true", help="Enable RAG retrieval (default: off).")
    rag_grp.add_argument("--rag_data_dir", type=str, default=None,
                         help="Path to ToMRAG JSONL data directory (default: tom_harness/tools/tomrag/data).")
    rag_grp.add_argument("--rag_index_dir", type=str, default=None,
                         help="Path to FAISS index cache directory (default: tom_harness/tools/tomrag/index).")
    rag_grp.add_argument("--rag_model", type=str, default="model/bge-m3",
                         help="Embedding model path or HuggingFace name (default: model/bge-m3).")

    # ── Memory Playbook ──────────────────────────────────────────────────
    mem_grp = ap.add_argument_group("Memory playbook")
    mem_grp.add_argument("--memory", action="store_true", help="Enable memory playbook injection into planner (default: off).")
    mem_grp.add_argument("--memory_dir", type=str, default="memory_playbook/",
                         help="Path to playbook directory (default: memory_playbook/).")

    args = ap.parse_args()

    # ── resolve output paths ──────────────────────────────────────────────
    out_dir = Path(args.out_dir) / args.tag
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.jsonl"
    stats_path   = out_dir / "stats.json"
    log_path     = out_dir / "run.log"

    # ── logging setup ───────────────────────────────���─────────────────────
    if args.verbose and _console_handler:
        _console_handler.removeFilter(_console_filter)

    _log_file_lock = threading.Lock()
    log_path.write_text("", encoding="utf-8")

    if results_path.exists():
        results_path.unlink()

    # ── load & select samples ─────────────────────────────────────────────
    samples = load_cogtom(data_dir=args.data_dir, lang="en")
    logger.info(f"Loaded {len(samples)} total CogToM samples")

    if args.category:
        cat_filter = {c.strip() for c in args.category.split(",")}
    else:
        cat_filter = None

    pool = select_samples(
        samples,
        categories=cat_filter,
        offset=args.offset,
        limit=args.limit,
    )

    cat_counts = defaultdict(int)
    for s in pool:
        cat_counts[s["metadata"]["category"]] += 1
    logger.info(f"Selected {len(pool)} samples across {len(cat_counts)} categories "
                f"(offset={args.offset}, limit={args.limit or 'all'} per category)")
    for c in sorted(cat_counts):
        logger.info(f"  {c:<40} {cat_counts[c]:>4}")

    if not pool:
        logger.info("Nothing to run.")
        return

    # ── RAG setup ─────────────────────────────────────────────────────────
    shared_rag: RAGEngine | None = None
    if args.rag:
        rag_kwargs: dict = {"model_name": args.rag_model}
        if args.rag_data_dir:
            rag_kwargs["data_dir"] = args.rag_data_dir
        if args.rag_index_dir:
            rag_kwargs["index_dir"] = args.rag_index_dir
        shared_rag = RAGEngine(**rag_kwargs)
        shared_rag.build_index()
        if shared_rag.size() > 0:
            logger.info(f"RAG enabled: {shared_rag.size()} documents indexed")
        else:
            logger.info("RAG data not found — running without RAG")
            shared_rag = None

    # ── Memory Playbook setup ─────────────────────────────────────────────
    shared_playbook: MemoryPlaybook | None = None
    if args.memory:
        pb_kwargs: dict = {}
        if args.memory_dir:
            pb_kwargs["playbook_dir"] = args.memory_dir
        shared_playbook = MemoryPlaybook(**pb_kwargs)
        shared_playbook.load()
        if shared_playbook.ready:
            logger.info(f"Memory playbook enabled: {shared_playbook.size()} chars loaded")
        else:
            logger.info("Memory playbook data not found — running without playbook")
            shared_playbook = None

    # ── run ────────────────────────────────────────────────────────────────
    llm_cache_dir = str(out_dir / "llm_cache")
    scheduler_factory = lambda: build_harness(shared_rag, shared_playbook, llm_cache_dir)  # noqa: E731
    t_start = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as exe:
        futs = {exe.submit(process_one, scheduler_factory, s): s for s in pool}
        for fut in as_completed(futs):
            s = futs[fut]
            try:
                rec, log_lines = fut.result(timeout=360)
            except Exception as e:  # noqa: BLE001
                rec = {"id": s["id"], "category": s["metadata"].get("category"),
                       "subcategory": s["metadata"].get("subcategory"),
                       "answer": s["answer"],
                       "predicted": "", "correct": False, "error": f"outer: {e}",
                       "num_phases": 0, "num_steps": 0, "replans": 0,
                       "elapsed_sec": 0.0, "plan_task_type": "", "phase_names": []}
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
                logger.info(f"progress={completed}/{len(pool)} elapsed={elapsed:.1f}min running_acc={acc_so_far:.3f}")

    # ── stats ──────────────────────────────────────────────────────────────
    _print_and_save_stats(results_path, stats_path, pool, args.tag)


def _print_and_save_stats(results_path: Path, stats_path: Path, pool: list, tag: str) -> None:
    all_records = _load_all(results_path)
    if not all_records:
        logger.info("No results to summarize.")
        return
    stats = _compute_stats(all_records)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    sep = "=" * 70
    logger.info(f"\n{sep}\nHarness [{tag}] results  →  {stats_path}\n{sep}")
    logger.info(f"Overall: {stats['overall']['correct']}/{stats['overall']['total']} "
                f"= {stats['overall']['accuracy']:.1%}  (errors: {stats['overall']['errors']})")
    logger.info(f"{'Category':<30} {'N':>4} {'Acc':>7}  {'Err':>4}")
    logger.info("-" * 50)
    for c in sorted(stats["per_category"]):
        cs = stats["per_category"][c]
        logger.info(f"  {c:<28} {cs['total']:>4} {cs['accuracy']:>7.1%}  {cs['errors']:>4}")
    if stats.get("per_subcategory"):
        logger.info("")
        logger.info(f"{'Subcategory':<55} {'N':>4} {'Acc':>7}  {'Err':>4}")
        logger.info("-" * 75)
        for sc in sorted(stats["per_subcategory"]):
            scs = stats["per_subcategory"][sc]
            logger.info(f"  {sc:<53} {scs['total']:>4} {scs['accuracy']:>7.1%}  {scs['errors']:>4}")
    logger.info(f"\nResults saved to: {results_path}")
    logger.info(f"Stats   saved to: {stats_path}")
    logger.info(f"Log     saved to: {results_path.parent / 'run.log'}")


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


def _compute_stats(records):
    total = len(records)
    correct = sum(1 for r in records if r.get("correct"))
    errors = sum(1 for r in records if r.get("error"))

    per_cat = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0})
    per_subcat = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0})

    for r in records:
        cat = r.get("category", "unknown")
        subcat = r.get("subcategory", "unknown")
        per_cat[cat]["total"] += 1
        per_cat[cat]["correct"] += int(bool(r.get("correct")))
        per_cat[cat]["errors"] += int(bool(r.get("error")))
        per_subcat[subcat]["total"] += 1
        per_subcat[subcat]["correct"] += int(bool(r.get("correct")))
        per_subcat[subcat]["errors"] += int(bool(r.get("error")))

    for d in list(per_cat.values()) + list(per_subcat.values()):
        n = d["total"] or 1
        d["accuracy"] = d["correct"] / n

    return {
        "overall": {
            "total": total, "correct": correct, "errors": errors,
            "accuracy": round(correct / total, 4) if total else 0,
        },
        "per_category": dict(per_cat),
        "per_subcategory": dict(per_subcat),
    }


if __name__ == "__main__":
    main()
