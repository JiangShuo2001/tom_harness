"""Single-question demo.

Runs one hand-crafted ToM question through the full harness (plan → execute
→ finalize), with verbose logging so every stage is inspectable.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tom_harness import (
    ContextManager, Executor, LLMClient, Planner, Scheduler, ToolRegistry,
)
from tom_harness.hooks import HookRegistry
from tom_harness.scheduler import SchedulerConfig
from tom_harness.tools import MemoryStore, RAGEngine, SkillLib, MemoryPlaybook

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from dotenv import load_dotenv
load_dotenv()  # load env vars from .env file in project root

def main() -> None:
    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key  = os.environ.get("TOM_API_KEY")
    model    = os.environ.get("TOM_MODEL",    "qwen3-32b")
    if not api_key:
        raise SystemExit("ERROR: set the TOM_API_KEY env var (see README > Configuration)")

    llm = LLMClient(api_base=api_base, api_key=api_key, model=model, temperature=0.0, max_tokens=2048)
    llm.set_cache_dir("results/demo/llm_cache")

    registry  = ToolRegistry()
    ctx       = ContextManager()
    hooks     = HookRegistry()
    memory    = MemoryStore()
    skill_lib = SkillLib()
    rag       = RAGEngine(model_name="model/bge-m3")
    rag.build_index()

    if rag.size() > 0:
        registry.register(rag)

    playbook = MemoryPlaybook()
    playbook.load()
    if playbook.ready:
        ctx.install_playbook(playbook.content)

    ctx.install_fixed(
        system_identity="A ToM-focused reasoning agent.",
        tool_schema_summary=registry.schema_summary(),
        safety_policy="Always base answers strictly on story facts; never use outside knowledge.",
    )

    planner   = Planner(llm=llm, registry=registry, context=ctx, hooks=hooks, memory=memory)
    executor  = Executor(llm=llm, registry=registry, context=ctx, hooks=hooks, skill_lib=skill_lib)
    scheduler = Scheduler(
        planner=planner, executor=executor, registry=registry,
        context=ctx, hooks=hooks, memory=memory,
        config=SchedulerConfig(max_replans=1, persist_memories_on_success=True),
    )

    # A minimal ToM question (classic Sally-Anne)
    question = (
        "Sally and Anne are in a room. Sally puts a marble in the basket, then leaves. "
        "While Sally is gone, Anne moves the marble to the box. Sally returns. "
        "Where will Sally look for the marble first?"
    )
    options = {"A": "The basket", "B": "The box", "C": "The floor", "D": "Anne's pocket"}

    result = scheduler.run(task_id="demo_sally_anne", question=question, options=options, dataset="demo")
    print("\n========== FINAL ==========")
    print(f"answer:  {result.answer}")
    print(f"success: {result.success}")
    print(f"plan.task_type: {result.plan.task_type}")
    print(f"phases: {[p.phase_name for p in result.plan.phases]}")
    print(f"num_steps: {len(result.traces)}")
    print(f"elapsed: {result.elapsed_sec:.2f}s")
    print(f"memories now: {memory.size()}")


if __name__ == "__main__":
    main()
