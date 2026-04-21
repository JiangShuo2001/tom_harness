"""ToM-aware memory enrichment.

When the Scheduler persists a successful (task, plan) pair into memory,
this hook enriches the Memory.metadata with ToM-relevant index fields.
The MemoryStore's `metadata_filter` retrieval parameter can then do
structured pre-filtering on future queries.

Indexed fields:
  - belief_order         : 0 | 1 | 2    (heuristic from plan phase names)
  - character_count      : int          (regex over original question)
  - has_knowledge_gap    : bool         (presence of "never seen" phrasing)
  - plan_phase_signature : str          (concatenated phase_name hashes)
  - num_phases           : int
"""

from __future__ import annotations

import re
from typing import Any

from ...schemas import Memory


_NEVER_SEEN = re.compile(r"never (seen|heard|encountered|met)|一无所知|从未见过")
_CAPITAL_NAME = re.compile(r"\b([A-Z][a-z]{2,})\b")


def enrich_memory(memory: Memory) -> Memory:
    metadata: dict[str, Any] = dict(memory.metadata)
    q = memory.task.question or ""
    metadata["has_knowledge_gap"] = bool(_NEVER_SEEN.search(q))
    metadata["character_count"] = len(set(_CAPITAL_NAME.findall(q)))
    metadata["belief_order"] = _infer_belief_order(memory)
    metadata["num_phases"] = len(memory.plan.phases)
    metadata["plan_phase_signature"] = "|".join(p.phase_name.lower()[:16] for p in memory.plan.phases)
    return memory.model_copy(update={"metadata": metadata})


def _infer_belief_order(memory: Memory) -> int:
    """Guess belief order from plan phase names and task_type."""
    names = " ".join(p.phase_name.lower() for p in memory.plan.phases)
    if "second" in names or "2nd" in names or "二阶" in names:
        return 2
    tt = memory.task.task_type.lower()
    if "second" in tt or "2nd" in tt:
        return 2
    if "false_belief" in tt or "belief" in names:
        return 1
    return 0
