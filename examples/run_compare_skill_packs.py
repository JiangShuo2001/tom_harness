"""Three-way benchmark: harness baseline / +set1 / +set2.

Runs the same 160 stratified ToMBench samples through:
  - "baseline": our harness, our own ToM skills only (status quo)
  - "set1":     our harness + Set1Adapter (15 SKILL.md from teammate-A)
  - "set2":     our harness + Set2Adapter (12 prompts + LLM router from teammate-B)

The only thing that differs across configs is the SkillLib contents and
the route() function picked by build_runtime_for_sample(). Everything
else (Scheduler / Planner / Executor / Memory / Finalize Short-Circuit)
is unchanged.

This is the intended "harness as a fair comparison platform" deliverable.
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
from tom_harness.plugins.tom.memory_index import extract_signature  # noqa: E402
from tom_harness.plugins.tom.router import select_skills  # noqa: E402
from tom_harness.plugins.external_skill_pack import SkillPackAdapter  # noqa: E402
from tom_harness.plugins.external_skill_pack.set1_adapter import Set1Adapter  # noqa: E402
from tom_harness.plugins.external_skill_pack.set2_adapter import Set2Adapter  # noqa: E402
from tom_harness.plugins.external_skill_pack.selective_router import SelectiveRouter  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("compare")
logger.setLevel(logging.INFO)


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


# ─────────────────────────────────────────────────────────────────────────────
# Build per-config harness state
# ─────────────────────────────────────────────────────────────────────────────

def build_state(config: str, llm: LLMClient):
    """config ∈ {'baseline', 'set1', 'set2_llm', 'set2_signature'}"""
    memory = MemoryStore()
    skill_lib = SkillLib()
    hooks = HookRegistry()

    if config == "baseline":
        info = install_tom_plugin(hooks=hooks, skill_lib=skill_lib)
        adapter: SkillPackAdapter | None = None
    elif config == "set1":
        adapter = Set1Adapter()
        adapter.load_into(skill_lib)
        info = adapter.metadata()
    elif config == "set2_llm":
        adapter = Set2Adapter(routing_mode="llm", router_llm_fn=llm.chat)
        adapter.load_into(skill_lib)
        info = adapter.metadata()
    elif config == "set2_signature":
        adapter = Set2Adapter(routing_mode="signature")
        adapter.load_into(skill_lib)
        info = adapter.metadata()
    elif config == "selective_v04":
        adapter = SelectiveRouter()
        adapter.load_into(skill_lib)
        info = adapter.metadata()
    else:
        raise ValueError(f"unknown config {config}")
    return llm, memory, skill_lib, hooks, adapter, info


def build_runtime_for_sample(
    state, *, sample, config: str,
):
    llm, shared_memory, shared_skill_lib, shared_hooks, adapter, _ = state
    registry = ToolRegistry()
    ctx = ContextManager()

    registry.register(shared_memory)
    registry.register(shared_skill_lib)

    story = sample["story"]
    question = sample["question"]
    options = sample["options"]
    task_type = sample["metadata"].get("task", "")

    # Decide which skills to surface to the Planner
    if config == "baseline":
        sig = extract_signature(question=question, story=story,
                                task_type=task_type, options=options)
        all_ids = {s["skill_id"] for s in shared_skill_lib.list_skills()}
        chosen = select_skills(sig, all_ids)
        rationale = f"signature router (kind={sig.question_kind})"
    else:
        rt = adapter.route(question=question, story=story,
                           options=options, task_type=task_type)
        chosen = [rt.skill_id] if rt.skill_id else []
        rationale = f"{config} router → {rt.skill_id} ({rt.rationale[:60]})"
        sig = None

    skill_listing = "\n".join(
        f"    - {sid}: {(_describe(shared_skill_lib, sid))[:140]}"
        for sid in chosen
    ) or "    (no skill suggested for this case)"

    tool_schema = (
        registry.schema_summary()
        + f"\n\n  Available skill_ids for execute_skill (filtered for this question):\n{skill_listing}"
        + f"\n  [routing rationale: {rationale}]"
    )
    ctx.install_fixed(
        system_identity=(
            "A ToM-focused reasoning agent. Use the filtered skill list "
            "below; calling an unlisted skill is an error."
        ),
        tool_schema_summary=tool_schema,
        safety_policy="Base answers ONLY on story facts.",
    )

    planner = Planner(llm=llm, registry=registry, context=ctx, hooks=shared_hooks, memory=shared_memory)
    executor = _AutoStoryExecutor(
        llm=llm, registry=registry, context=ctx, hooks=shared_hooks,
        skill_lib=shared_skill_lib, story_text=story,
    )
    scheduler = Scheduler(
        planner=planner, executor=executor, registry=registry, context=ctx,
        hooks=shared_hooks, memory=shared_memory,
        config=SchedulerConfig(max_replans=1, persist_memories_on_success=True),
    )
    return scheduler, chosen, rationale


def _describe(skill_lib: SkillLib, skill_id: str) -> str:
    rec = skill_lib.get(skill_id)
    return (rec.description or "(no description)") if rec else "(unknown)"


# Reuse the SignatureAwareExecutor pattern from run_tombench_v03.py: auto-inject
# story into skill input_context.
class _AutoStoryExecutor(Executor):
    story_text: str = ""

    def __init__(self, *args, story_text: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.story_text = story_text

    def _act(self, call, reasoning=None):
        from tom_harness.schemas import ToolType
        if call.tool_type == ToolType.SKILL:
            params = dict(call.tool_params)
            ic = params.get("input_context") or {}
            if isinstance(ic, dict) and "story" not in ic:
                ic = {**ic, "story": self.story_text}
            params["input_context"] = ic
            if "story" not in params:
                params["story"] = self.story_text
            call = call.model_copy(update={"tool_params": params})
        return super()._act(call, reasoning=reasoning)


# ─────────────────────────────────────────────────────────────────────────────
# Per-sample driver
# ─────────────────────────────────────────────────────────────────────────────

def process_one(sample, state, config):
    t0 = time.time()
    rec = {
        "id": sample["id"], "task": sample["metadata"].get("task"),
        "answer": sample["answer"], "predicted": "", "correct": False,
        "config": config, "chosen_skills_routed": [], "skills_called": [],
        "elapsed_sec": 0.0, "error": None,
    }
    try:
        scheduler, chosen, rationale = build_runtime_for_sample(
            state, sample=sample, config=config,
        )
        rec["chosen_skills_routed"] = chosen
        rec["routing_rationale"] = rationale
        result = scheduler.run(
            task_id=sample["id"],
            question=f"{sample['story']}\n\nQuestion: {sample['question']}",
            options=sample["options"], dataset="ToMBench",
        )
        rec["predicted"] = result.answer
        rec["correct"] = (result.answer == sample["answer"])
        called = []
        for tr in result.traces:
            if tr.tool_call and tr.tool_call.tool_type == "skill":
                called.append(tr.tool_call.params.get("skill_id", tr.tool_call.tool_name))
        rec["skills_called"] = called
        rec["error"] = result.error
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["elapsed_sec"] = round(time.time() - t0, 2)
    return rec


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_task", type=int, default=20)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--configs", nargs="+",
                    default=["baseline", "set1", "set2_signature"],
                    help="space-separated subset of: baseline set1 set2_llm set2_signature")
    ap.add_argument("--out_dir", default="results")
    args = ap.parse_args()

    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY")
    model = os.environ.get("TOM_MODEL", "qwen3.5-27b")
    if not api_key:
        raise SystemExit("ERROR: set TOM_API_KEY env var")
    llm = LLMClient(api_base=api_base, api_key=api_key, model=model,
                    temperature=0.0, max_tokens=3072, timeout=180.0, max_retries=3)

    samples = load_tombench()
    pool = stratified(samples, args.per_task)
    logger.info(f"pool: {len(pool)} samples")

    out_dir = Path(args.out_dir); out_dir.mkdir(exist_ok=True)
    summary = {}

    for config in args.configs:
        logger.info(f"\n========== config = {config} ==========")
        results_path = out_dir / f"compare_{config}_results.jsonl"
        # Resume support
        done = set()
        if results_path.exists():
            for ln in open(results_path, encoding="utf-8"):
                ln = ln.strip()
                if ln:
                    try: done.add(json.loads(ln)["id"])
                    except Exception: pass
        pending = [s for s in pool if s["id"] not in done]
        logger.info(f"  resume: done={len(done)} pending={len(pending)}")

        state = build_state(config, llm)
        info = state[5]
        logger.info(f"  pack info: {info}")

        t0 = time.time(); n = 0
        with ThreadPoolExecutor(max_workers=args.workers) as exe:
            futs = {exe.submit(process_one, s, state, config): s for s in pending}
            for f in as_completed(futs):
                rec = f.result()
                with open(results_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
                if n % 20 == 0:
                    logger.info(f"  progress {n}/{len(pending)} elapsed={(time.time()-t0)/60:.1f}min")

        # Summary
        records = [json.loads(ln) for ln in open(results_path) if ln.strip()]
        per_task = defaultdict(lambda: [0, 0])
        for r in records:
            per_task[r["task"]][0] += 1
            per_task[r["task"]][1] += int(bool(r["correct"]))
        total = len(records); correct = sum(1 for r in records if r["correct"])
        summary[config] = {
            "overall": {"total": total, "correct": correct,
                        "accuracy": round(correct/total, 4) if total else 0},
            "per_task": {t: {"total": n, "correct": c, "accuracy": round(c/n, 4)}
                         for t, (n, c) in per_task.items()},
        }
        logger.info(f"  → {correct}/{total} = {correct/total:.1%}")

    # Print final 3-way table
    logger.info("\n" + "="*70)
    tasks = sorted({t for s in summary.values() for t in s["per_task"]})
    header = f"{'task':<32}" + "".join(f"{c:<14}" for c in args.configs)
    logger.info(header)
    logger.info("-"*len(header))
    for t in tasks:
        row = f"{t:<32}"
        for c in args.configs:
            d = summary[c]["per_task"].get(t, {})
            row += f"{d.get('accuracy', 0):>11.1%}   "
        logger.info(row)
    row = f"{'OVERALL':<32}"
    for c in args.configs:
        row += f"{summary[c]['overall']['accuracy']:>11.1%}   "
    logger.info(row)

    json.dump(summary, open(out_dir / "compare_summary.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    logger.info(f"\nsummary written to {out_dir / 'compare_summary.json'}")


if __name__ == "__main__":
    main()
