"""v0.3 benchmark: state-backed skills + signature-based routing + shared memory.

Key differences from v0.2:
  1. MemoryStore is shared across the whole batch (thread-safe via RLock),
     so warm-start actually has a chance to work.
  2. Skills exposed to the Planner are *filtered per-sample* via
     plugins/tom/router.select_skills(signature, available). The Planner
     only sees relevant skills, eliminating S03's 71% over-firing.
  3. Samples are processed **ordered by task**, so within a task-type
     group every sample can retrieve memories of previously-solved
     same-type samples.
  4. Executor auto-injects `story` into skill input_context so
     state-backed skills can parse the story without the Planner having
     to remember to pass it.
"""

from __future__ import annotations

import argparse
import copy
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
from tom_harness.plugins.tom.memory_index import extract_signature  # noqa: E402
from tom_harness.plugins.tom.router import select_skills  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bench_v03")
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
    # return samples GROUPED BY TASK so memory warm-start can benefit
    out = []
    for t in sorted(buckets):
        b = buckets[t]; rng.shuffle(b); out.extend(b[:per_task])
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Shared singletons (built once, used by all worker threads)
# ─────────────────────────────────────────────────────────────────────────────

def build_shared_state():
    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key  = os.environ.get("TOM_API_KEY")
    model    = os.environ.get("TOM_MODEL", "qwen3.5-27b")
    if not api_key:
        raise SystemExit("ERROR: set TOM_API_KEY env var")

    llm = LLMClient(api_base=api_base, api_key=api_key, model=model,
                    temperature=0.0, max_tokens=3072, timeout=180.0, max_retries=3)

    shared_memory = MemoryStore()        # shared across threads (thread-safe)
    shared_skill_lib = SkillLib()        # shared read-only after install
    shared_hooks = HookRegistry()
    info = install_tom_plugin(hooks=shared_hooks, skill_lib=shared_skill_lib)
    logger.info(f"plugin installed: {info}")

    return llm, shared_memory, shared_skill_lib, shared_hooks


def build_runtime_for_sample(llm, shared_memory, shared_skill_lib, shared_hooks,
                              question: str, story: str, options: dict, task_type: str):
    """Build per-sample runtime that reuses the shared singletons."""
    registry = ToolRegistry()
    ctx = ContextManager()
    # NB: hooks are shared across samples too — plugins may accumulate counters,
    # but nothing here mutates across calls beyond memory writes which we *want*.
    hooks = shared_hooks

    registry.register(shared_memory)
    registry.register(shared_skill_lib)

    # Signature-gated skill list
    sig = extract_signature(question=question, story=story,
                            task_type=task_type, options=options)
    all_skills = {s["skill_id"] for s in shared_skill_lib.list_skills()}
    chosen_skills = select_skills(sig, all_skills)
    skill_listing = "\n".join(
        f"    - {sid}: {_describe(shared_skill_lib, sid)}"
        for sid in chosen_skills
    )
    tool_schema = (
        registry.schema_summary()
        + f"\n\n  Available skill_ids for execute_skill (filtered for this question):\n{skill_listing}"
    )

    ctx.install_fixed(
        system_identity=(
            "A ToM-focused reasoning agent. Use the filtered skill list "
            "below; calling an unlisted skill is an error. Prefer the "
            "state-backed skills (S_build_story_model / S_belief_query / "
            "S_knowledge_query) over free-form reasoning when applicable."
        ),
        tool_schema_summary=tool_schema,
        safety_policy="Base answers ONLY on story facts.",
    )

    planner = Planner(llm=llm, registry=registry, context=ctx, hooks=hooks, memory=shared_memory)
    executor = SignatureAwareExecutor(
        llm=llm, registry=registry, context=ctx, hooks=hooks,
        skill_lib=shared_skill_lib, story_text=story,
    )
    scheduler = Scheduler(
        planner=planner, executor=executor, registry=registry, context=ctx,
        hooks=hooks, memory=shared_memory,
        config=SchedulerConfig(max_replans=1, persist_memories_on_success=True),
    )
    return scheduler, sig, chosen_skills


def _describe(skill_lib: SkillLib, skill_id: str) -> str:
    rec = skill_lib.get(skill_id)
    return (rec.description or "(no description)")[:140] if rec else "(unknown)"


# ─────────────────────────────────────────────────────────────────────────────
# Executor variant that auto-injects `story` into skill params
# ─────────────────────────────────────────────────────────────────────────────

class SignatureAwareExecutor(Executor):
    """Injects the story text into skill input_context when absent.

    Motivation: state-backed skills (S_build_story_model, S_evidence_scorer)
    always need the raw story. The Planner shouldn't have to remember to
    copy it into every tool call — just auto-inject.
    """
    story_text: str = ""

    def __init__(self, *args, story_text: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.story_text = story_text

    def _act(self, call):
        from tom_harness.schemas import ToolType
        if call.tool_type == ToolType.SKILL:
            params = dict(call.tool_params)
            # ensure input_context exists
            ic = params.get("input_context") or {}
            if isinstance(ic, dict) and "story" not in ic:
                ic = {**ic, "story": self.story_text}
            params["input_context"] = ic
            # Also promote story to a top-level alias for handlers that take it directly
            if "story" not in params:
                params["story"] = self.story_text
            # top-level convenience aliases — handlers accept **_
            call = call.model_copy(update={"tool_params": params})
        return super()._act(call)


# ─────────────────────────────────────────────────────────────────────────────
# Per-sample driver
# ─────────────────────────────────────────────────────────────────────────────

def process_one(sample, shared):
    llm, shared_memory, shared_skill_lib, shared_hooks = shared
    t0 = time.time()
    rec = {
        "id": sample["id"], "task": sample["metadata"].get("task"),
        "answer": sample["answer"], "predicted": "", "correct": False,
        "num_phases": 0, "num_steps": 0, "replans": 0,
        "elapsed_sec": 0.0, "plan_task_type": "", "phase_names": [],
        "skills_called": [], "gated_skills": [], "signature_kind": "",
        "memory_hit_count": 0, "error": None,
    }
    try:
        story = sample["story"]
        question = f"{story}\n\nQuestion: {sample['question']}"
        scheduler, sig, gated = build_runtime_for_sample(
            llm, shared_memory, shared_skill_lib, shared_hooks,
            question=sample["question"], story=story,
            options=sample["options"], task_type=sample["metadata"].get("task", ""),
        )
        rec["signature_kind"] = sig.question_kind
        rec["gated_skills"] = gated
        result = scheduler.run(
            task_id=sample["id"], question=question,
            options=sample["options"], dataset="ToMBench",
        )
        rec["predicted"] = result.answer
        rec["correct"] = (result.answer == sample["answer"])
        rec["num_phases"] = len(result.plan.phases)
        rec["num_steps"] = len(result.traces)
        rec["replans"] = int(result.metadata.get("replans", 0))
        rec["plan_task_type"] = result.plan.task_type
        rec["phase_names"] = [p.phase_name for p in result.plan.phases]
        rec["memory_hit_count"] = len(result.plan.memory_references)
        skills_called = []
        for trace in result.traces:
            if trace.tool_call and trace.tool_call.tool_type == "skill":
                skills_called.append(
                    trace.tool_call.params.get("skill_id", trace.tool_call.tool_name)
                )
        rec["skills_called"] = skills_called
        rec["error"] = result.error
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["elapsed_sec"] = round(time.time() - t0, 2)
    return rec


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_task", type=int, default=20)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--tag", default="v03")
    args = ap.parse_args()

    out_dir = Path("results"); out_dir.mkdir(exist_ok=True)
    results_path = out_dir / f"harness_{args.tag}_results.jsonl"
    stats_path   = out_dir / f"harness_{args.tag}_stats.json"

    samples = load_tombench()
    pool = stratified_sample(samples, args.per_task)
    logger.info(f"stratified pool: {len(pool)} samples")

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

    shared = build_shared_state()

    t_start = time.time(); completed = 0
    # Process per task-group sequentially; inside each group, use workers
    by_task = defaultdict(list)
    for s in pending:
        by_task[s["metadata"].get("task", "unknown")].append(s)

    for task_name in sorted(by_task.keys()):
        group = by_task[task_name]
        with ThreadPoolExecutor(max_workers=args.workers) as exe:
            futs = {exe.submit(process_one, s, shared): s for s in group}
            for fut in as_completed(futs):
                s = futs[fut]
                try:
                    rec = fut.result(timeout=360)
                except Exception as e:
                    rec = {"id": s["id"], "task": task_name, "answer": s["answer"],
                           "predicted": "", "correct": False, "error": f"outer: {e}",
                           "num_phases": 0, "num_steps": 0, "replans": 0,
                           "elapsed_sec": 0.0, "plan_task_type": "", "phase_names": [],
                           "skills_called": [], "gated_skills": [],
                           "signature_kind": "", "memory_hit_count": 0}
                with open(results_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                completed += 1
                if completed % 10 == 0:
                    shared_memory = shared[1]
                    logger.info(
                        f"progress={completed}/{len(pending)} "
                        f"elapsed={(time.time()-t_start)/60:.1f}min "
                        f"memory_size={shared_memory.size()}"
                    )

    # Stats
    records = []
    with open(results_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line: records.append(json.loads(line))
    total = len(records); correct = sum(1 for r in records if r.get("correct"))
    per_task = defaultdict(lambda: {"total": 0, "correct": 0})
    skill_use = defaultdict(int)
    mem_hits = 0
    for r in records:
        per_task[r["task"]]["total"] += 1
        per_task[r["task"]]["correct"] += int(bool(r.get("correct")))
        for sk in r.get("skills_called", []):
            skill_use[sk] += 1
        mem_hits += int(r.get("memory_hit_count", 0) or 0)
    stats = {
        "overall": {"total": total, "correct": correct,
                    "accuracy": round(correct/total, 4) if total else 0},
        "per_task": {t: {"total": d["total"], "correct": d["correct"],
                         "accuracy": round(d["correct"]/d["total"], 4)}
                     for t, d in per_task.items()},
        "skill_usage": dict(skill_use),
        "memory_hits_total": mem_hits,
        "final_memory_size": shared[1].size(),
        "mode": "v03_state_backed_skills",
    }
    json.dump(stats, open(stats_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    logger.info(f"\n{'='*60}")
    logger.info(f"Overall: {correct}/{total} = {correct/total:.1%}")
    for t in sorted(per_task):
        d = per_task[t]; logger.info(f"  {t:<35} {d['total']:>3} {d['correct']/d['total']:>7.1%}")
    logger.info(f"skill usage: {dict(skill_use)}")
    logger.info(f"memory hits: {mem_hits}; final memory size: {shared[1].size()}")


if __name__ == "__main__":
    main()
