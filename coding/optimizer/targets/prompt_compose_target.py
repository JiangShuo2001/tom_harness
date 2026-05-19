"""Prompt-Composer optimizer target.

Turns ``(task, route_decision, [ModuleOutput, ...])`` into a final
``{system_prompt, user_prompt, debug}`` dictionary, governed entirely
by a YAML policy. The policy is responsible for:

  * **Ranking** module outputs by priority.
  * **Cropping** them to fit a global token budget.
  * **Filtering** low-relevance RAG and over-long memory.
  * **Formatting** the final messages — preserving story/options
    verbatim and adding anti-overmentalizing guidance when asked.

The composer is *purely* token-aware (a 4-chars-per-token estimator).
Real LLM tokenization is not required for the optimizer's structural
decisions; the runtime can apply its own tokenizer when actually
calling the LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import dump_yaml, load_yaml
from ..interfaces import (
    ModuleOutput,
    OptimizerTarget,
    RouteDecision,
    coerce_module_outputs,
    coerce_route_decision,
)


# Rough approximation: 1 token ≈ 4 characters of English-like text.
_CHARS_PER_TOKEN = 4


@dataclass
class PromptComposePolicy(OptimizerTarget):
    """Apply a prompt-compose policy to a single sample."""

    policy: dict
    name: str = "prompt_compose_policy"

    # ── factories ─────────────────────────────────────────────────────
    @classmethod
    def from_yaml(cls, path: str | Path) -> "PromptComposePolicy":
        raw = load_yaml(path) or {}
        if "prompt_compose_policy" in raw and isinstance(
            raw["prompt_compose_policy"], dict
        ):
            policy = raw["prompt_compose_policy"]
        else:
            policy = raw
        return cls(policy=policy)

    @classmethod
    def from_policy(cls, policy: dict) -> "PromptComposePolicy":
        return cls(policy=policy or {})

    # ── OptimizerTarget interface ─────────────────────────────────────
    def load_policy(self, path: str) -> dict:
        return PromptComposePolicy.from_yaml(path).policy

    def dump_policy(self, policy: dict, path: str) -> None:
        dump_yaml({"prompt_compose_policy": policy}, path)

    def apply(  # type: ignore[override]
        self,
        policy: dict | None = None,
        *,
        task: dict | None = None,
        route_decision: Any = None,
        module_outputs: list[Any] | None = None,
        **_: Any,
    ) -> dict:
        if policy is None:
            policy = self.policy
        return _compose(
            policy or {},
            task or {},
            coerce_route_decision(route_decision),
            coerce_module_outputs(module_outputs or []),
        )

    # ── public stages (also useful from notebooks) ────────────────────
    def rank(
        self,
        module_outputs: list[ModuleOutput],
        route_decision: Any = None,
    ) -> list[ModuleOutput]:
        return _rank(self.policy, coerce_module_outputs(module_outputs))

    def crop(
        self, ranked_outputs: list[ModuleOutput], token_budget: int
    ) -> list[ModuleOutput]:
        return _crop(self.policy, ranked_outputs, token_budget)

    def render(
        self,
        task: dict,
        route_decision: Any,
        module_outputs: list[ModuleOutput],
    ) -> dict:
        return _compose(
            self.policy,
            task or {},
            coerce_route_decision(route_decision),
            coerce_module_outputs(module_outputs),
        )

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not isinstance(self.policy, dict):
            return ["prompt_compose_policy must be a mapping"]
        budget = self.policy.get("global_token_budget")
        if budget is not None and not isinstance(budget, (int, float)):
            issues.append("global_token_budget must be a number")
        prio = self.policy.get("priority")
        if prio is not None and not isinstance(prio, dict):
            issues.append("priority must be a mapping")
        return issues


# ──────────────────────────────────────────────────────────────────────
#  Compose pipeline
# ──────────────────────────────────────────────────────────────────────

def _compose(
    policy: dict,
    task: dict,
    route: RouteDecision,
    outputs: list[ModuleOutput],
) -> dict:
    rules = policy.get("rules") or {}
    rag_min = float(rules.get("rag_min_relevance", 0.0))
    memory_top_k = int(rules.get("memory_top_k", 0) or 0)
    drop_low_rag = bool(rules.get("drop_low_relevance_rag", False))
    add_anti_om = bool(rules.get("add_anti_overmentalizing_instruction", False))
    skill_hard_thr = float(rules.get("skill_as_hard_constraint_threshold", 0.85))

    debug: dict = {"dropped": [], "kept": [], "warnings": []}

    # 1. Filter RAG by relevance.
    filtered: list[ModuleOutput] = []
    for mo in outputs:
        if drop_low_rag and mo.module_name == "rag" and mo.relevance < rag_min:
            debug["dropped"].append(
                {
                    "module": mo.module_name,
                    "reason": f"rag relevance {mo.relevance:.2f} < {rag_min:.2f}",
                }
            )
            continue
        filtered.append(mo)

    # 2. Limit memory to top-k by confidence.
    if memory_top_k > 0:
        memory_items = [m for m in filtered if m.module_name == "memory"]
        if len(memory_items) > memory_top_k:
            keep = sorted(memory_items, key=lambda m: m.confidence, reverse=True)[
                :memory_top_k
            ]
            keep_ids = {id(m) for m in keep}
            new_filtered: list[ModuleOutput] = []
            for m in filtered:
                if m.module_name == "memory" and id(m) not in keep_ids:
                    debug["dropped"].append(
                        {
                            "module": "memory",
                            "reason": f"top-{memory_top_k} memory cap",
                        }
                    )
                    continue
                new_filtered.append(m)
            filtered = new_filtered

    # 3. Rank.
    ranked = _rank(policy, filtered)

    # 4. Crop to global budget.
    budget = int(policy.get("global_token_budget", 3500) or 3500)
    cropped = _crop(policy, ranked, budget)

    debug["kept"] = [
        {
            "module": mo.module_name,
            "confidence": mo.confidence,
            "relevance": mo.relevance,
            "tokens": _approx_tokens(mo.content),
        }
        for mo in cropped
    ]

    # 5. Render messages.
    skill_mode = (
        "hard"
        if any(
            m.module_name == "skill" and m.confidence >= skill_hard_thr for m in cropped
        )
        else "soft"
    )

    system_prompt = _render_system_prompt(policy, route, add_anti_om, skill_mode)
    user_prompt = _render_user_prompt(task, cropped, skill_mode)

    # Token accounting.
    total_tokens = _approx_tokens(system_prompt) + _approx_tokens(user_prompt)
    debug["token_estimate"] = {
        "system": _approx_tokens(system_prompt),
        "user": _approx_tokens(user_prompt),
        "total": total_tokens,
        "budget": budget,
    }
    debug["skill_mode"] = skill_mode

    if total_tokens > budget:
        debug["warnings"].append(
            f"Final prompt {total_tokens} tokens exceeds budget {budget}; "
            "story/options were preserved per policy."
        )

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "debug": debug,
    }


def _rank(policy: dict, outputs: list[ModuleOutput]) -> list[ModuleOutput]:
    priority = policy.get("priority") or {}
    default_pri = float(priority.get("default", 0))
    return sorted(
        outputs,
        key=lambda mo: (
            -float(priority.get(mo.module_name, default_pri)),
            -float(mo.confidence),
            mo.module_name,
        ),
    )


def _crop(
    policy: dict, ranked: list[ModuleOutput], budget: int
) -> list[ModuleOutput]:
    """Greedy crop: keep modules in priority order, respecting per-module
    budgets. Preserves the story/options implicitly — they live in the
    task dict, not in module outputs.
    """
    module_budgets = dict(policy.get("module_budgets") or {})
    used = 0
    out: list[ModuleOutput] = []
    for mo in ranked:
        per_module = int(module_budgets.get(mo.module_name, budget))
        tokens = _approx_tokens(mo.content)
        if tokens > per_module:
            mo = ModuleOutput(
                module_name=mo.module_name,
                content=_truncate_to_tokens(mo.content, per_module),
                confidence=mo.confidence,
                relevance=mo.relevance,
                risk_flags=list(mo.risk_flags) + ["truncated_per_module"],
                metadata=dict(mo.metadata),
            )
            tokens = _approx_tokens(mo.content)
        if used + tokens > budget:
            remaining = max(0, budget - used)
            if remaining < 64:
                break
            mo = ModuleOutput(
                module_name=mo.module_name,
                content=_truncate_to_tokens(mo.content, remaining),
                confidence=mo.confidence,
                relevance=mo.relevance,
                risk_flags=list(mo.risk_flags) + ["truncated_global"],
                metadata=dict(mo.metadata),
            )
            tokens = _approx_tokens(mo.content)
        out.append(mo)
        used += tokens
    return out


# ──────────────────────────────────────────────────────────────────────
#  Rendering
# ──────────────────────────────────────────────────────────────────────

_SYSTEM_BASE = (
    "You are a careful reading-comprehension assistant for social-cognition "
    "questions. Read the story and answer the multiple-choice question. "
    "First give a brief reason (2-3 sentences), then output a JSON object "
    'on its own line: {"answer": "A" | "B" | "C" | "D"}'
)

_ANTI_OM = (
    " Do not over-mentalize: if the story already provides a direct causal "
    "or factual explanation, prefer it over speculative inferences about "
    "hidden motives."
)


def _render_system_prompt(
    policy: dict, route: RouteDecision, add_anti_om: bool, skill_mode: str
) -> str:
    parts = [_SYSTEM_BASE]
    if add_anti_om:
        parts.append(_ANTI_OM)
    if skill_mode == "soft":
        parts.append(
            " Treat any provided reasoning skill as a *hint*, not a rule — "
            "follow the story when they conflict."
        )
    return "".join(parts)


def _render_user_prompt(
    task: dict, kept: list[ModuleOutput], skill_mode: str
) -> str:
    by_module: dict[str, list[ModuleOutput]] = {}
    for mo in kept:
        by_module.setdefault(mo.module_name, []).append(mo)

    sections: list[str] = []

    if "skill" in by_module:
        header = (
            "## Reasoning Skill (apply BEFORE answering)"
            if skill_mode == "hard"
            else "## Reasoning Skill (hint, not a rule)"
        )
        body = "\n\n".join(m.content for m in by_module["skill"])
        sections.append(f"{header}\n{body}")

    if "memory" in by_module:
        body = "\n\n".join(m.content for m in by_module["memory"])
        sections.append(f"## Playbook (only when conditions match)\n{body}")

    if "rag" in by_module:
        body = "\n\n".join(m.content for m in by_module["rag"])
        sections.append(
            "## Background Knowledge (reference only; story takes precedence)"
            f"\n{body}"
        )

    if "validator_hint" in by_module:
        body = "\n\n".join(m.content for m in by_module["validator_hint"])
        sections.append(f"## Validator Hint\n{body}")

    story = task.get("story", "")
    question = task.get("question", "")
    options = task.get("options", {}) or {}
    sections.append(f"## Story\n{story}")
    sections.append(f"## Question\n{question}")
    if options:
        opts = "\n".join(f"{k}. {v}" for k, v in options.items() if v)
        sections.append(f"## Options\n{opts}")

    sections.append(
        "## Answer\n"
        "First state your reason in 2-3 sentences, then output a JSON "
        'object on its own line: {"answer": "A"|"B"|"C"|"D"}'
    )
    return "\n\n".join(sections)


# ──────────────────────────────────────────────────────────────────────
#  Token math
# ──────────────────────────────────────────────────────────────────────

def _approx_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // _CHARS_PER_TOKEN)


def _truncate_to_tokens(text: str, max_tokens: int) -> str:
    if max_tokens <= 0:
        return ""
    max_chars = max_tokens * _CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return text
    cut = text[: max_chars - 8]
    # Try not to break mid-sentence.
    m = re.search(r"^(.*[.!?])\s", cut[::-1])
    if m:
        cut = cut[: len(cut) - m.start()]
    return cut.rstrip() + " […]"
