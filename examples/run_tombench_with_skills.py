"""Run the harness on ToMBench WITH tools + skills wired in.

v0.2 benchmark:
  - MemoryStore registered in ToolRegistry as `memory_retrieve`
  - SkillLib    registered in ToolRegistry as `execute_skill`
  - ToM plugin installed (failure handlers, memory enrichment, validators,
    plan templates, 8 reasoning skills, S02 procedural handler)

Same 160 stratified samples as run_tombench_harness.py (--per_task 20
on the 8 main tasks) so the comparison is apples-to-apples with v0.1.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "/home/coder/survey_1/symbolictom_repro")

from benchmark_adapters import load_tombench  # type: ignore  # noqa: E402

from tom_harness import (  # noqa: E402
    ContextManager, Executor, LLMClient, Planner, Scheduler, ToolRegistry,
)
from tom_harness.hooks import HookRegistry  # noqa: E402
from tom_harness.scheduler import SchedulerConfig  # noqa: E402
from tom_harness.tools import MemoryStore, SkillLib  # noqa: E402
from tom_harness.plugins.tom.install import install as install_tom_plugin  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("harness_bench_v02")
logger.setLevel(logging.INFO)


MAIN_8 = {
    "Unexpected Outcome Test", "Scalar Implicature Test", "Persuasion Story Task",
    "False Belief Task", "Ambiguous Story Task", "Hinting Task Test",
    "Strange Story Task", "Faux-pas Recognition Test",
}


def stratified_sample(samples, per_task=20, seed=42):
    rng = random.Random(seed)
    buckets = defaultdict(list)
    for s in samples:
        t = s["metadata"].get("task", "")
        if t in MAIN_8:
            buckets[t].append(s)
    out = []
    for t in sorted(buckets):
        b = buckets[t]; rng.shuffle(b); out.extend(b[:per_task])
    return out


def build_harness():
    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key  = os.environ.get("TOM_API_KEY")
    model    = os.environ.get("TOM_MODEL", "qwen3.5-27b")
    if not api_key:
        raise SystemExit("ERROR: set TOM_API_KEY env var")

    llm = LLMClient(api_base=api_base, api_key=api_key, model=model,
                    temperature=0.0, max_tokens=3072, timeout=180.0, max_retries=3)
    registry  = ToolRegistry()
    ctx       = ContextManager()
    hooks     = HookRegistry()
    memory    = MemoryStore()
    skill_lib = SkillLib()

    # Install the ToM plugin (hooks + skills + handlers)
    info = install_tom_plugin(hooks=hooks, skill_lib=skill_lib)

    # Register memory and skill_lib as tools so the Planner can reference them
    registry.register(memory)
    registry.register(skill_lib)

    # Build a skill-ID list so the Planner knows what to pass to execute_skill
    skill_listing = "\n".join(
        f"    - {s['skill_id']}: {s['description'][:120]}"
        for s in skill_lib.list_skills()
    )
    tool_schema = registry.schema_summary() + "\n\n  Available skill_ids for execute_skill:\n" + skill_listing

    ctx.install_fixed(
        system_identity=(
            "A ToM-focused reasoning agent answering multiple-choice questions. "
            "You have access to memory_retrieve (for similar past plans) and "
            "execute_skill (for targeted reasoning procedures). Use skills when "
            "their triggers match."
        ),
        tool_schema_summary=tool_schema,
        safety_policy="Base answers ONLY on story facts; never fabricate detail.",
    )

    planner = Planner(llm=llm, registry=registry, context=ctx, hooks=hooks, memory=memory)
    executor = Executor(llm=llm, registry=registry, context=ctx, hooks=hooks, skill_lib=skill_lib)
    scheduler = Scheduler(
        planner=planner, executor=executor, registry=registry, context=ctx,
        hooks=hooks, memory=memory,
        config=SchedulerConfig(max_replans=1, persist_memories_on_success=True),
    )
    return scheduler, info


def process_one(sample, timeout_sec: float = 300.0):
    t0 = time.time()
    rec = {
        "id": sample["id"], "task": sample["metadata"].get("task"),
        "answer": sample["answer"], "predicted": "", "correct": False,
        "num_phases": 0, "num_steps": 0, "replans": 0,
        "elapsed_sec": 0.0, "plan_task_type": "", "phase_names": [],
        "skills_called": [], "error": None,
    }
    try:
        scheduler, _ = build_harness()
        result = scheduler.run(
            task_id=sample["id"],
            question=f"{sample['story']}\n\nQuestion: {sample['question']}",
            options=sample["options"],
            dataset="ToMBench",
        )
        rec["predicted"]      = result.answer
        rec["correct"]        = (result.answer == sample["answer"])
        rec["num_phases"]     = len(result.plan.phases)
        rec["num_steps"]      = len(result.traces)
        rec["replans"]        = int(result.metadata.get("replans", 0))
        rec["plan_task_type"] = result.plan.task_type
        rec["phase_names"]    = [p.phase_name for p in result.plan.phases]
        # Extract which skills were actually called during execution
        skills_called = []
        for trace in result.traces:
            if trace.tool_call and trace.tool_call.tool_type == "skill":
                skills_called.append(trace.tool_call.params.get("skill_id", trace.tool_call.tool_name))
        rec["skills_called"] = skills_called
        rec["error"]          = result.error
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["elapsed_sec"] = round(time.time() - t0, 2)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_task", type=int, default=20)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--tag", default="v02_with_skills")
    args = ap.parse_args()

    out_dir = Path("results"); out_dir.mkdir(exist_ok=True)
    results_path = out_dir / f"harness_{args.tag}_results.jsonl"
    stats_path   = out_dir / f"harness_{args.tag}_stats.json"

    samples = load_tombench()
    pool = stratified_sample(samples, args.per_task)
    logger.info(f"stratified sample: {len(pool)} from {len(samples)} total")

    done_ids: set[str] = set()
    if results_path.exists():
        with open(results_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try: done_ids.add(json.loads(line)["id"])
                except Exception: pass
    pending = [s for s in pool if s["id"] not in done_ids]
    logger.info(f"resume: done={len(done_ids)} pending={len(pending)}")

    # Warm up: build once to emit install summary
    _, info = build_harness()
    logger.info(f"plugin installed: {info}")

    t_start = time.time(); completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as exe:
        futs = {exe.submit(process_one, s): s for s in pending}
        for fut in as_completed(futs):
            s = futs[fut]
            try:
                rec = fut.result(timeout=360)
            except Exception as e:
                rec = {"id": s["id"], "task": s["metadata"].get("task"), "answer": s["answer"],
                       "predicted": "", "correct": False, "error": f"outer: {e}",
                       "num_phases": 0, "num_steps": 0, "replans": 0,
                       "elapsed_sec": 0.0, "plan_task_type": "", "phase_names": [], "skills_called": []}
            with open(results_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            completed += 1
            if completed % 10 == 0:
                n_done = len(done_ids) + completed
                logger.info(f"progress={completed}/{len(pending)} elapsed={(time.time()-t_start)/60:.1f}min")

    # Final stats
    records = []
    with open(results_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line: records.append(json.loads(line))
    total = len(records); correct = sum(1 for r in records if r.get("correct"))
    per_task = defaultdict(lambda: {"total": 0, "correct": 0})
    skill_use = defaultdict(int)
    for r in records:
        per_task[r["task"]]["total"] += 1
        per_task[r["task"]]["correct"] += int(bool(r.get("correct")))
        for sk in r.get("skills_called", []):
            skill_use[sk] += 1
    stats = {
        "overall": {"total": total, "correct": correct,
                    "accuracy": round(correct/total, 4) if total else 0},
        "per_task": {t: {"total": d["total"], "correct": d["correct"],
                         "accuracy": round(d["correct"]/d["total"], 4)}
                     for t, d in per_task.items()},
        "skill_usage": dict(skill_use),
        "mode": "v02_with_skills",
    }
    json.dump(stats, open(stats_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    logger.info(f"\n{'='*60}")
    logger.info(f"Overall: {correct}/{total} = {correct/total:.1%}")
    for t in sorted(per_task):
        d = per_task[t]; logger.info(f"  {t:<35} {d['total']:>3} {d['correct']/d['total']:>7.1%}")
    logger.info(f"skill usage: {dict(skill_use)}")


if __name__ == "__main__":
    main()
