"""Memory — portable recall from a trained ACE playbook."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import openai

from .config import SelectorConfig, load_selector_config
from .playbook import (
    extract_known_subtasks,
    filter_playbook_to_bullets,
    parse_playbook_line,
)
from .selector import Selector


@dataclass(frozen=True)
class Bullet:
    id: str
    content: str
    section: Optional[str]
    helpful: int
    harmful: int
    buckets: dict
    raw_line: str


@dataclass
class RecallResult:
    bullets: list[Bullet]
    bullet_ids: list[str]
    predicted_subtask: str
    _playbook_text: str = field(repr=False)

    def as_text(self) -> str:
        if not self.bullet_ids:
            return ""
        return filter_playbook_to_bullets(self._playbook_text, self.bullet_ids)

    def __bool__(self) -> bool:
        return bool(self.bullets)


class Memory:
    """Load a trained playbook and recall relevant bullets via a selector LLM.

    Usage::

        memory = Memory("playbook/final_playbook.txt",
                         SelectorConfig(provider="openai",
                                        api_key="sk-...",
                                        model="gpt-4o-mini"))
        result = memory.recall("Where does Sally think the marble is?")
        result.bullets     # list[Bullet], may be []
        result.as_text()   # filtered playbook text, "" when empty
    """

    def __init__(self, playbook_path: str, selector: SelectorConfig):
        self.playbook = Path(playbook_path).read_text(encoding="utf-8")
        self._bullet_index = self._build_index(self.playbook)
        self.known_subtasks = extract_known_subtasks(self.playbook)

        client = openai.OpenAI(
            api_key=selector.api_key,
            base_url=selector.resolved_base_url(),
        )
        self._selector = Selector(
            client, selector.provider, selector.model,
            max_tokens=selector.max_tokens,
            max_bullets=selector.max_bullets,
        )
        self._use_json_mode = selector.use_json_mode

    @classmethod
    def from_toml(cls, playbook_path: str, config_path: str) -> Memory:
        return cls(playbook_path, load_selector_config(config_path))

    def recall(
        self,
        question: str,
        *,
        context: str = "",
        max_bullets: Optional[int] = None,
    ) -> RecallResult:
        """Retrieve relevant bullets from the playbook. May return zero bullets."""
        if max_bullets is not None:
            self._selector.max_bullets = max_bullets

        predicted, ids, _ = self._selector.select(
            question,
            self.playbook,
            context=context,
            known_subtasks=self.known_subtasks,
            use_json_mode=self._use_json_mode,
        )

        bullets = [self._bullet_index[bid] for bid in ids
                   if bid in self._bullet_index]
        resolved_ids = [b.id for b in bullets]

        return RecallResult(
            bullets=bullets,
            bullet_ids=resolved_ids,
            predicted_subtask=predicted,
            _playbook_text=self.playbook,
        )

    @staticmethod
    def _build_index(playbook_text: str) -> dict[str, Bullet]:
        index: dict[str, Bullet] = {}
        current_section: Optional[str] = None

        for line in playbook_text.split('\n'):
            stripped = line.strip()
            if stripped.startswith('##'):
                current_section = stripped.lstrip('#').strip()
                continue
            parsed = parse_playbook_line(line)
            if parsed:
                index[parsed['id']] = Bullet(
                    id=parsed['id'],
                    content=parsed['content'],
                    section=current_section,
                    helpful=parsed['helpful'],
                    harmful=parsed['harmful'],
                    buckets=parsed['buckets'],
                    raw_line=parsed['raw_line'],
                )

        return index
