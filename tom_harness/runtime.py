"""HarnessRuntime — the canonical single-shot path.

This is the consolidated runtime, replacing the Plan/Execute multi-step
scheduler as the default. It implements:

    route(sample) -> skill_id
    build_prompt(sample, skill_id) -> messages
    LLM call
    for v in validators:
        result = v.validate(sample, current_answer)
        if not valid:
            apply v.suggested_answer  OR  retry LLM with v.feedback
    return final answer

Why this shape (vs Plan/Execute):
  - On qwen-plus, full Plan/Execute pipeline measured -7~9pp vs single-shot
    (see WEEKLY_REPORT_HARNESS_2026-04-29 §5 表 2a). Multi-step in a strong
    LLM regime is a net negative on this benchmark.
  - The remaining harness value (post-Plan/Execute) is exactly:
      adapter pattern + selective routing + procedural validators + retry
    All of which fit naturally in single-shot + checkpoint structure.

Plan/Execute (Scheduler/Planner/Executor) remains in the codebase for
multi-step research scenarios but is no longer the default.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from .llm import LLMClient
from .routing.base import Router, RouteDecision
from .tools.skills import SkillLib
from .validators.base import Validator, ValidationResult

logger = logging.getLogger(__name__)


SYSTEM_RAW = (
    "You are a reading comprehension assistant. Read the story and answer "
    "the multiple-choice question. Reply with ONLY a JSON object: "
    '{"answer": "A" | "B" | "C" | "D"}'
)

_LETTER_RE = re.compile(r'"answer"\s*:\s*"([A-D])"')


def _parse_letter(text: str) -> str:
    text = re.sub(r"<think>[\s\S]*?</think>", "", text or "").strip()
    try:
        d = json.loads(text)
        a = str(d.get("answer", "")).strip().upper()
        if a in {"A", "B", "C", "D"}:
            return a
    except Exception:  # noqa: BLE001
        pass
    m = _LETTER_RE.search(text)
    return m.group(1).upper() if m else ""


def _build_user_prompt(*, story: str, question: str, options: dict[str, str],
                       skill_body: str | None) -> str:
    opts = "\n".join(f"{k}. {v}" for k, v in options.items() if v)
    if skill_body:
        return (
            f"## Reasoning Skill (apply before answering)\n{skill_body}\n\n"
            f"## Story\n{story}\n\n"
            f"## Question\n{question}\n\n"
            f"## Options\n{opts}\n\n"
            '## Answer\nAfter applying the skill above, reply with ONLY a JSON object: {"answer": "A"|"B"|"C"|"D"}'
        )
    return f"Story: {story}\n\nQuestion: {question}\n\nOptions:\n{opts}"


def _build_retry_prompt(*, base_user: str, prior_answer: str, validator_feedback: str) -> str:
    return (
        f"{base_user}\n\n"
        f"## Validator Feedback (from a procedural check on your prior answer)\n"
        f"Your previous answer was {prior_answer}.\n"
        f"{validator_feedback}\n\n"
        '## Reconsider\nReply with ONLY a JSON object: {"answer": "A"|"B"|"C"|"D"}'
    )


@dataclass
class RuntimeResult:
    answer: str
    skill_id: str | None
    n_llm_calls: int
    validator_events: list[dict] = field(default_factory=list)


@dataclass
class HarnessRuntime:
    """Single-shot harness with optional validator-retry."""
    llm: LLMClient
    skill_lib: SkillLib
    router: Router
    validators: list[Validator] = field(default_factory=list)
    max_retries: int = 1                     # per-validator; 0 = no retry, just substitute

    def answer_one(
        self,
        *,
        question: str,
        story: str,
        options: dict[str, str],
        task_type: str | None = None,
    ) -> RuntimeResult:
        decision: RouteDecision = self.router.route(
            question=question, story=story, options=options, task_type=task_type
        )
        skill_id = decision.skill_id
        skill_body = None
        if skill_id:
            rec = self.skill_lib.get(skill_id)
            if rec is None:
                logger.warning(f"router picked unregistered skill_id={skill_id}; falling back to raw")
            else:
                skill_body = rec.body
        base_user = _build_user_prompt(
            story=story, question=question, options=options, skill_body=skill_body,
        )

        # ── 1. initial LLM call ───────────────────────────────────────────
        n_calls = 1
        try:
            text = self.llm.chat(SYSTEM_RAW, base_user, max_tokens=1024)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"initial LLM call failed: {e}")
            text = ""
        answer = _parse_letter(text)
        events: list[dict] = []

        # ── 2. validators ─────────────────────────────────────────────────
        for v in self.validators:
            if not v.applies(task_type):
                continue
            result: ValidationResult = v.validate(
                question=question, story=story, options=options,
                task_type=task_type, current_answer=answer,
            )
            events.append({
                "validator": v.__class__.__name__,
                "valid": result.valid,
                "rationale": result.rationale,
                "had_suggestion": bool(result.suggested_answer),
            })

            if result.valid:
                continue

            # 2a. direct substitute when validator is confident
            if result.suggested_answer:
                logger.info(
                    f"[{v.__class__.__name__}] substituting {answer} -> "
                    f"{result.suggested_answer} ({result.rationale})"
                )
                answer = result.suggested_answer
                continue

            # 2b. retry LLM with feedback
            for retry_idx in range(self.max_retries):
                retry_user = _build_retry_prompt(
                    base_user=base_user, prior_answer=answer,
                    validator_feedback=result.feedback,
                )
                n_calls += 1
                try:
                    text = self.llm.chat(SYSTEM_RAW, retry_user, max_tokens=1024)
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"retry LLM call failed: {e}")
                    break
                new_answer = _parse_letter(text)
                if new_answer:
                    answer = new_answer
                # re-run this validator to see if fixed
                result = v.validate(
                    question=question, story=story, options=options,
                    task_type=task_type, current_answer=answer,
                )
                events.append({
                    "validator": v.__class__.__name__,
                    "valid": result.valid,
                    "rationale": result.rationale,
                    "retry": retry_idx + 1,
                })
                if result.valid:
                    break

        return RuntimeResult(
            answer=answer, skill_id=skill_id, n_llm_calls=n_calls,
            validator_events=events,
        )


def build_default_runtime(
    *,
    llm: LLMClient,
    skill_lib: SkillLib,
    router: Router,
    enable_scalar_validator: bool = True,
) -> HarnessRuntime:
    """Convenience factory: wires the default validator stack."""
    validators: list[Validator] = []
    if enable_scalar_validator:
        from .validators.scalar_procedural import ScalarProceduralValidator
        validators.append(ScalarProceduralValidator())
    return HarnessRuntime(llm=llm, skill_lib=skill_lib, router=router, validators=validators)
