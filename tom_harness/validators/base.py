"""Validator ABC."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ValidationResult:
    valid: bool
    feedback: str = ""                          # what to feed back to LLM if !valid
    suggested_answer: str | None = None         # if validator can substitute directly
    rationale: str = ""                         # short reason (for trace/debug)


class Validator(ABC):
    """A post-LLM validator. Cheap (no LLM by default) and task-scoped."""

    # Subclasses set this. Empty set = applies to every task.
    applies_to_tasks: set[str] = set()

    def applies(self, task_type: str | None) -> bool:
        if not self.applies_to_tasks:
            return True
        return task_type in self.applies_to_tasks

    @abstractmethod
    def validate(
        self,
        *,
        question: str,
        story: str,
        options: dict[str, str],
        task_type: str | None,
        current_answer: str,
    ) -> ValidationResult: ...
