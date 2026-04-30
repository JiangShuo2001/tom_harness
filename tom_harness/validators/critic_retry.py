"""LLMCriticValidator — critic LLM produces feedback text, runtime retries.

The single harness-native lever after stripping skills/memory/tools:

    detect signal -> critic produces text -> retry with text in prompt

Concrete instantiation: an LLM is asked, in a separate call, "is this
answer consistent with the story; if not, what's the contradiction?".
The critic's free-form critique is fed back into the original prompt
via the existing runtime retry path.

The validator itself just decides "is there an issue" and produces the
feedback text. The runtime does the actual re-prompting (it already
knows how to splice `feedback` into a retry prompt — see
`_build_retry_prompt` in tom_harness/runtime.py).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from ..llm import LLMClient
from .base import Validator, ValidationResult

logger = logging.getLogger(__name__)


CRITIC_SYSTEM = """You are a careful critic. You are given:
  - a short story
  - a multiple-choice question with options
  - a tentative answer letter from another reasoner

Your job: spot whether the tentative answer is inconsistent with what \
the story actually says. Look for factual contradictions, missed \
information, or unsupported assumptions. Do NOT just say "the answer is \
wrong" — name the specific story fact that conflicts.

Reply with ONLY a JSON object:
  {"issue": true/false, "critique": "<one sentence pointing to a specific \
story fact, or empty string if no issue>"}

Set "issue" to true ONLY if you can name a specific story fact that the \
answer contradicts. If you're unsure, set "issue" to false."""


def _parse_critic(text: str) -> tuple[bool, str]:
    text = re.sub(r"<think>[\s\S]*?</think>", "", text or "").strip()
    try:
        d = json.loads(text)
        issue = bool(d.get("issue", False))
        critique = str(d.get("critique", "")).strip()
        return issue, critique
    except Exception:
        # tolerant fallback: look for common "issue" boolean signal in raw text
        issue = bool(re.search(r'"issue"\s*:\s*true', text, re.IGNORECASE))
        m = re.search(r'"critique"\s*:\s*"([^"]+)"', text)
        critique = m.group(1) if m else ""
        return issue, critique


@dataclass
class LLMCriticValidator(Validator):
    """Critic-feedback retry. Configure which tasks it fires on; pass in the LLMClient."""
    llm: LLMClient
    target_tasks: set[str] = field(default_factory=set)
    max_critic_tokens: int = 256

    @property
    def applies_to_tasks(self) -> set[str]:  # type: ignore[override]
        return self.target_tasks

    def applies(self, task_type: str | None) -> bool:
        return task_type in self.target_tasks if self.target_tasks else True

    def validate(
        self,
        *,
        question: str,
        story: str,
        options: dict[str, str],
        task_type: str | None,
        current_answer: str,
    ) -> ValidationResult:
        if not current_answer:
            # nothing to critique
            return ValidationResult(valid=True, rationale="empty current_answer")

        opts = "\n".join(f"{k}. {v}" for k, v in options.items() if v)
        chosen_text = options.get(current_answer, "")
        user = (
            f"## Story\n{story}\n\n"
            f"## Question\n{question}\n\n"
            f"## Options\n{opts}\n\n"
            f"## Tentative answer\n{current_answer}. {chosen_text}\n\n"
            f"## Your critique"
        )
        try:
            text = self.llm.chat(CRITIC_SYSTEM, user, max_tokens=self.max_critic_tokens)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"critic LLM call failed: {e}")
            return ValidationResult(valid=True, rationale="critic call failed; passing")

        issue, critique = _parse_critic(text)
        if not issue or not critique:
            return ValidationResult(valid=True, rationale="critic found no issue")

        return ValidationResult(
            valid=False,
            feedback=f"A critic reviewing your prior answer noted: \"{critique}\" "
                     f"Reconsider in light of this. The story is the ground truth.",
            rationale=f"critic flagged: {critique[:120]}",
        )
