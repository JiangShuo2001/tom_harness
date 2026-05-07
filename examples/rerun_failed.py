"""Rerun only failed (predicted="") samples and patch results in-place.

Usage:
  python examples/rerun_failed.py results/ablation_0507/1_baseline
  python examples/rerun_failed.py results/ablation_0507/1_baseline --skill
  python examples/rerun_failed.py results/ablation_0507/1_baseline --skill --rag --memory

Reads results.jsonl, finds records with predicted="", reruns them,
updates results.jsonl in-place, and regenerates stats.json.
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
from tom_harness import LLMClient, build_default_runtime  # noqa: E402
from tom_harness.routing import SkillV4Router, NoOpRouter  # noqa: E402
from tom_harness.tools.rag_v2 import RAGv2Engine  # noqa: E402
from tom_harness.tools.playbook import MemoryPlaybook  # noqa: E402

from dotenv import load_dotenv  # noqa: E402
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("rerun_failed")


def build_harness(*, shared_rag=None, shared_playbook=None, enable_skill=False):
    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY")
    model = os.environ.get("TOM_MODEL", "qwen3-32b")
    if not api_key:
        raise SystemExit("ERROR: set the TOM_API_KEY env var")

    llm = LLMClient(
        api_base=api_base, api_key=api_key, model=model,
        temperature=0.0, max_tokens=2048, timeout=120.0, max_retries=3,
    )
    router = SkillV4Router(llm=llm) if enable_skill else NoOpRouter()

    playbook_text = None
    if shared_playbook is not None and shared_playbook.ready:
        playbook_text = shared_playbook.content

    return build_default_runtime(
        llm=llm, router=router,
        rag_engine=shared_rag if (shared_rag is not None and shared_rag.size() > 0) else None,
        playbook=playbook_text,
    )


def process_one(runtime_factory, sample):
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
    return rec


def compute_stats(records):
    total = len(records)
    correct = sum(1 for r in records if r.get("correct"))
    # Count as error: explicit error OR empty prediction (parse failure)
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
        # Accuracy denominator excludes errors
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


def main():
    ap = argparse.ArgumentParser(description="Rerun failed (empty predicted) samples or resume interrupted runs.")
    ap.add_argument("out_dir", type=str, help="Path to result directory (e.g. results/ablation_0507/1_baseline)")
    ap.add_argument("--skill", action="store_true")
    ap.add_argument("--rag", action="store_true")
    ap.add_argument("--rag_data_dir", type=str, default="tom_harness/tools/rag_v2_data")
    ap.add_argument("--rag_index_dir", type=str, default="tom_harness/tools/rag_v2_index")
    ap.add_argument("--rag_model", type=str, default="model/bge-m3")
    ap.add_argument("--memory", action="store_true")
    ap.add_argument("--memory_dir", type=str, default="memory_playbook/")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--data_dir", type=str, default=None)
    ap.add_argument("--resume", action="store_true",
                    help="Resume interrupted run: skip already-completed samples, run missing ones.")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    results_path = out_dir / "results.jsonl"
    stats_path = out_dir / "stats.json"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load existing results (if any)
    all_records = []
    if results_path.exists():
        with open(results_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    all_records.append(json.loads(line))

    # Load benchmark data
    samples = load_tombench(data_dir=args.data_dir)
    sample_map = {s["id"]: s for s in samples}

    if args.resume:
        # Resume mode: find samples not yet in results
        existing_ids = {r["id"] for r in all_records}
        all_ids = set(sample_map.keys())
        missing_ids = all_ids - existing_ids
        # Also rerun empty predictions
        failed_ids = {r["id"] for r in all_records if not r.get("predicted")}
        to_rerun_ids = missing_ids | failed_ids
        if not to_rerun_ids:
            logger.info("All samples completed. Nothing to do.")
            _save_stats(all_records, results_path, stats_path)
            return
        logger.info("Resume mode: %d missing + %d failed = %d to run",
                    len(missing_ids), len(failed_ids), len(to_rerun_ids))
        to_rerun = [sample_map[sid] for sid in to_rerun_ids if sid in sample_map]
    else:
        # Normal mode: only rerun empty predictions
        if not results_path.exists():
            raise SystemExit(f"ERROR: {results_path} not found")
        failed_ids = {r["id"] for r in all_records if not r.get("predicted")}
        if not failed_ids:
            logger.info("No failed records found. Nothing to rerun.")
            return
        logger.info("Found %d failed records to rerun", len(failed_ids))
        to_rerun = [sample_map[fid] for fid in failed_ids if fid in sample_map]

    # Setup modules
    shared_rag = None
    if args.rag:
        shared_rag = RAGv2Engine(
            data_dir=args.rag_data_dir, index_dir=args.rag_index_dir,
            model_name=args.rag_model, use_rewritten=True,
        )
        shared_rag.build_index()
        if shared_rag.size() == 0:
            shared_rag = None

    shared_playbook = None
    if args.memory:
        shared_playbook = MemoryPlaybook(playbook_dir=args.memory_dir)
        shared_playbook.load()
        if not shared_playbook.ready:
            shared_playbook = None

    runtime_factory = lambda: build_harness(  # noqa: E731
        shared_rag=shared_rag, shared_playbook=shared_playbook, enable_skill=args.skill,
    )

    # Run samples
    logger.info("Running %d samples with %d workers...", len(to_rerun), args.workers)
    new_results = {}
    t_start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as exe:
        futs = {exe.submit(process_one, runtime_factory, s): s for s in to_rerun}
        done = 0
        for fut in as_completed(futs):
            s = futs[fut]
            try:
                rec = fut.result(timeout=360)
            except Exception as e:
                rec = {"id": s["id"], "task": s["metadata"].get("task"), "answer": s["answer"],
                       "predicted": "", "correct": False, "error": f"outer: {e}",
                       "skill_id": None, "n_llm_calls": 0, "elapsed_sec": 0.0}
            new_results[rec["id"]] = rec
            done += 1
            if done % 10 == 0:
                elapsed = (time.time() - t_start) / 60
                logger.info("  progress: %d/%d (%.1f min)", done, len(to_rerun), elapsed)

    # Merge: update existing records + append new ones
    existing_id_set = {r["id"] for r in all_records}
    for i, r in enumerate(all_records):
        if r["id"] in new_results:
            all_records[i] = new_results[r["id"]]
    for rid, rec in new_results.items():
        if rid not in existing_id_set:
            all_records.append(rec)

    _save_stats(all_records, results_path, stats_path)

    patched = sum(1 for rid, rec in new_results.items() if rec.get("predicted"))
    still_empty = sum(1 for rid, rec in new_results.items() if not rec.get("predicted"))
    logger.info("Done. Patched/added %d records, %d still empty.", patched, still_empty)


def _save_stats(all_records, results_path, stats_path):
    with open(results_path, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    stats = compute_stats(all_records)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    logger.info("Overall: %d/%d = %.1f%%",
                stats["overall"]["correct"], stats["overall"]["total"],
                stats["overall"]["accuracy"] * 100)


if __name__ == "__main__":
    main()
