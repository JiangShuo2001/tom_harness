"""Selector agent — picks a relevant subset of playbook bullets for a question."""
from __future__ import annotations

from typing import List, Optional, Tuple

from .prompts import SELECTOR_PROMPT
from .llm import timed_llm_call
from .playbook import parse_playbook_line, extract_json_from_text


class Selector:
    def __init__(self, api_client, api_provider: str, model: str,
                 max_tokens: int = 1024, max_bullets: int = 8):
        self.api_client = api_client
        self.api_provider = api_provider
        self.model = model
        self.max_tokens = max_tokens
        self.max_bullets = max_bullets

    def select(
        self,
        question: str,
        playbook: str,
        *,
        context: str = "",
        known_subtasks: Optional[List[str]] = None,
        target_subtask: Optional[str] = None,
        use_json_mode: bool = False,
    ) -> Tuple[str, List[str], dict]:
        """Return (predicted_subtask, selected_bullet_ids, call_info).

        Returns ("unknown", [], {}) when the playbook has no bullets.
        """
        has_bullets = any(parse_playbook_line(l) for l in playbook.split('\n'))
        if not has_bullets:
            return "unknown", [], {}

        subtasks_str = ", ".join(known_subtasks) if known_subtasks else "(none yet)"
        if target_subtask:
            target_str = (f"{target_subtask} — prefer bullets whose bucket for this "
                          f"subtask shows helpful >= harmful and n >= 3")
        else:
            target_str = "(unknown — pick from the list above or output 'unknown')"

        prompt = SELECTOR_PROMPT.format(
            max_bullets=self.max_bullets,
            known_subtasks=subtasks_str,
            target_subtask=target_str,
            playbook=playbook,
            question=question,
            context=context or "",
        )

        response, call_info = timed_llm_call(
            self.api_client,
            self.api_provider,
            self.model,
            prompt,
            max_tokens=self.max_tokens,
            use_json_mode=use_json_mode,
        )

        predicted_subtask = "unknown"
        bullet_ids: List[str] = []

        try:
            parsed = extract_json_from_text(response)
            if parsed:
                predicted_subtask = str(parsed.get("predicted_subtask") or "unknown").strip()
                raw_ids = parsed.get("selected_bullet_ids") or []
                if isinstance(raw_ids, list):
                    bullet_ids = [str(b) for b in raw_ids if isinstance(b, (str, int))]
                bullet_ids = bullet_ids[: self.max_bullets]
        except Exception:
            pass

        return predicted_subtask, bullet_ids, call_info
