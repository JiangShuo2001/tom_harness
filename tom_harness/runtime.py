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
from .validators.base import Validator, ValidationResult

logger = logging.getLogger(__name__)


SYSTEM_BASE = (
    "You are a reading comprehension assistant. Read the story and answer "
    "the multiple-choice question.\n"
)

SYSTEM_SKILL_HINT = (
    "A domain-specific reasoning skill is provided in the user message under "
    "\"## Reasoning Skill\". Follow its workflow step-by-step before choosing "
    "your answer.\n"
)

SYSTEM_RAG_HINT = (
    "Background knowledge retrieved from a commonsense knowledge base is "
    "provided under \"## Background Knowledge\". Use it as supplementary "
    "reference when it is relevant, but always prioritize evidence from the "
    "story itself.\n"
)

SYSTEM_PLAYBOOK_HINT = (
    "A strategy playbook is provided under \"## Playbook\". Apply its "
    "strategies and heuristics, and be mindful of the common mistakes it "
    "documents.\n"
)

SYSTEM_TAIL = (
    "First give a brief reason (2-3 sentences) for your choice, "
    "then output a JSON object on its own line: "
    '{"answer": "A" | "B" | "C" | "D"}'
)

# Keep backward-compat alias for any external code referencing SYSTEM_RAW
SYSTEM_RAW = SYSTEM_BASE + SYSTEM_TAIL


def _build_system_prompt(
    *,
    has_skill: bool = False,
    has_rag: bool = False,
    has_playbook: bool = False,
) -> str:
    parts = [SYSTEM_BASE]
    if has_skill:
        parts.append(SYSTEM_SKILL_HINT)
    if has_rag:
        parts.append(SYSTEM_RAG_HINT)
    if has_playbook:
        parts.append(SYSTEM_PLAYBOOK_HINT)
    parts.append(SYSTEM_TAIL)
    return "".join(parts)

_LETTER_RE = re.compile(r'"answer"\s*:\s*"([A-D])"')
_REASON_RE = re.compile(r'^([\s\S]*?)\s*(\{[\s\S]*"answer"[\s\S]*\})\s*$')
_BARE_LETTER_RE = re.compile(
    r'(?:答案|answer|选)\s*(?:[:：为]|is)?\s*\(?([A-D])\)?'
    r'|(?:^|\n)\s*\(?([A-D])\)?\s*[.。]?\s*$',
    re.IGNORECASE | re.MULTILINE
)


def _parse_response(text: str) -> tuple[str, str]:
    """Return (answer_letter, reasoning_text)."""
    raw = text or ""
    stripped = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
    # If stripping think tags leaves nothing, fall back to think content
    if not stripped:
        m_think = re.search(r"<think>([\s\S]*?)</think>", raw)
        stripped = m_think.group(1).strip() if m_think else ""
    text = stripped
    reasoning = ""
    m = _REASON_RE.match(text)
    if m:
        reasoning = m.group(1).strip()
        json_part = m.group(2).strip()
    else:
        json_part = text

    try:
        d = json.loads(json_part)
        a = str(d.get("answer", "")).strip().upper()
        if a in {"A", "B", "C", "D"}:
            return a, reasoning
    except Exception:  # noqa: BLE001
        pass
    m2 = _LETTER_RE.search(text)
    if m2:
        return m2.group(1).upper(), reasoning
    # Last resort: match bare letter patterns like "答案：B", "answer is C", or trailing letter
    m3 = _BARE_LETTER_RE.search(text)
    if m3:
        letter = (m3.group(1) or m3.group(2)).upper()
        return letter, reasoning
    logger.warning("_parse_response failed to extract answer from: %s", text)
    return ("", reasoning)


def _build_user_prompt(*, story: str, question: str, options: dict[str, str],
                       skill_body: str | None = None,
                       rag_context: str | None = None,
                       playbook: str | None = None) -> str:
    sections: list[str] = []
    if skill_body:
        sections.append(f"## Reasoning Skill (apply before answering)\n{skill_body}")
    if rag_context:
        sections.append(
            "## Background Knowledge\n"
            "The following information may be relevant to the current question and is for reference only:\n"
            f"{rag_context}"
        )
    if playbook:
        sections.append(f"## Playbook\n{playbook}")
    sections.append(f"## Story\n{story}")
    sections.append(f"## Question\n{question}")
    opts = "\n".join(f"{k}. {v}" for k, v in options.items() if v)
    sections.append(f"## Options\n{opts}")
    sections.append(
        '## Answer\n'
        'After applying any guidance above, first state your reason in 2-3 sentences, '
        'then output a JSON object on its own line: {"answer": "A"|"B"|"C"|"D"}'
    )
    return "\n\n".join(sections)


def _build_retry_prompt(*, base_user: str, prior_answer: str, validator_feedback: str) -> str:
    return (
        f"{base_user}\n\n"
        f"## Validator Feedback (from a procedural check on your prior answer)\n"
        f"Your previous answer was {prior_answer}.\n"
        f"{validator_feedback}\n\n"
        '## Reconsider\nState your reason in 2-3 sentences, then output a JSON object: {"answer": "A"|"B"|"C"|"D"}'
    )


@dataclass
class RuntimeResult:
    answer: str
    skill_id: str | None
    n_llm_calls: int
    thinking: str = ""
    rag_context: str = ""
    memory_bullets: list[str] = field(default_factory=list)
    memory_subtask: str = ""
    validator_events: list[dict] = field(default_factory=list)


@dataclass
class HarnessRuntime:
    """Single-shot harness with optional validator-retry."""
    llm: LLMClient
    router: "Router"
    validators: list["Validator"] = field(default_factory=list)
    rag_engine: Any = None
    playbook: str | None = None
    memory: Any = None
    max_retries: int = 1

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
        if skill_id and hasattr(self.router, 'get_skill_body'):
            skill_body = self.router.get_skill_body(skill_id)
            if skill_body is None:
                logger.warning("router picked skill_id=%s but get_skill_body returned None", skill_id)

        rag_context = None
        if self.rag_engine is not None:
            try:
                rag_context = self.rag_engine.retrieve(
                    query=question, category=task_type, story=story,
                )
            except Exception as e:
                logger.warning("RAG retrieve failed: %s", e)

        playbook_text = self.playbook
        memory_bullet_ids: list[str] = []
        memory_subtask = ""
        if self.memory is not None:
            try:
                recall_result = self.memory.recall(question, context=story)
                selected = recall_result.as_text()
                if selected:
                    playbook_text = selected
                    memory_bullet_ids = recall_result.bullet_ids
                    memory_subtask = recall_result.predicted_subtask
                    logger.info(
                        "[Memory] recall -> subtask=%s, %d bullets selected",
                        recall_result.predicted_subtask, len(recall_result.bullets),
                    )
                else:
                    logger.debug("[Memory] recall returned no relevant bullets")
            except Exception as e:
                logger.warning("Memory recall failed: %s", e)

        base_user = _build_user_prompt(
            story=story, question=question, options=options,
            skill_body=skill_body, rag_context=rag_context or None,
            playbook=playbook_text,
        )

        system_prompt = _build_system_prompt(
            has_skill=bool(skill_body),
            has_rag=bool(rag_context),
            has_playbook=bool(playbook_text),
        )

        # ── 1. initial LLM call ───────────────────────────────────────────
        n_calls = 1
        reasoning = ""
        try:
            text = self.llm.chat(system_prompt, base_user, max_tokens=4096)
        except Exception as e:
            logger.warning("initial LLM call failed: %s", e)
            text = ""
        answer, reasoning = _parse_response(text)
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

            if result.suggested_answer:
                logger.info(
                    "[%s] substituting %s -> %s (%s)",
                    v.__class__.__name__, answer, result.suggested_answer, result.rationale,
                )
                answer = result.suggested_answer
                continue

            for retry_idx in range(self.max_retries):
                retry_user = _build_retry_prompt(
                    base_user=base_user, prior_answer=answer,
                    validator_feedback=result.feedback,
                )
                n_calls += 1
                try:
                    text = self.llm.chat(system_prompt, retry_user, max_tokens=1024)
                except Exception as e:
                    logger.warning("retry LLM call failed: %s", e)
                    break
                new_answer, _ = _parse_response(text)
                if new_answer:
                    answer = new_answer
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
            thinking=reasoning,
            rag_context=rag_context or "",
            memory_bullets=memory_bullet_ids,
            memory_subtask=memory_subtask,
            validator_events=events,
        )


def build_default_runtime(
    *,
    llm: LLMClient,
    router: "Router",
    rag_engine: Any = None,
    playbook: str | None = None,
    memory: Any = None,
    enable_scalar_validator: bool = True,
) -> HarnessRuntime:
    """Convenience factory: wires the default validator stack."""
    validators: list["Validator"] = []
    if enable_scalar_validator:
        from .validators.scalar_procedural import ScalarProceduralValidator
        validators.append(ScalarProceduralValidator())
    return HarnessRuntime(
        llm=llm, router=router, validators=validators,
        rag_engine=rag_engine, playbook=playbook,
        memory=memory,
    )
