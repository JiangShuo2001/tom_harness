"""LLM client wrapper.

Thin adapter over an OpenAI-compatible Chat Completions endpoint. Supports:
  - JSON-mode parsing (extracts a top-level JSON object from response)
  - Optional think-mode (enable_thinking toggle)
  - Retry with exponential backoff
  - Stripping of <think>...</think> inline tags

Usage:
    client = LLMClient(api_base="...", api_key="...", model="Qwen3.5-27B")
    raw_text = client.chat(system="...", user="...")
    parsed   = client.chat_json(system="...", user="...")
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger(__name__)

_THINK_TAG = re.compile(r"<think>[\s\S]*?</think>", re.MULTILINE)
_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.MULTILINE)
_FIRST_JSON_OBJECT = re.compile(r"\{[\s\S]*\}", re.MULTILINE)


@dataclass
class LLMClient:
    """OpenAI-compatible chat client."""
    api_base: str
    api_key: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 4096
    enable_thinking: bool = False
    timeout: float = 180.0
    max_retries: int = 3

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        enable_thinking: bool | None = None,
    ) -> str:
        """Return the plain text response (reasoning stripped)."""
        think = self.enable_thinking if enable_thinking is None else enable_thinking
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
            # vLLM-style nested kwarg
            "chat_template_kwargs": {"enable_thinking": think},
            # DashScope-style top-level flag (ignored by vLLM)
            "enable_thinking": think,
        }
        last_err: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content") or ""
                # Some endpoints put thinking in a separate `reasoning` field — we ignore it
                return _THINK_TAG.sub("", content).strip()
            except Exception as e:  # noqa: BLE001
                last_err = e
                logger.warning(f"LLM chat attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"LLM chat failed after {self.max_retries} attempts: {last_err}")

    def chat_json(
        self,
        system: str,
        user: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Return a parsed JSON object. Falls back to extracting the first
        balanced {...} block if the response is not pure JSON."""
        text = self.chat(system, user, **kwargs)
        return self._parse_json(text)

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """Robust JSON extractor: direct parse → fenced block → first object."""
        text = text.strip()
        # Attempt 1: direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Attempt 2: fenced code block
        m = _JSON_FENCE.search(text)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        # Attempt 3: first balanced object
        m = _FIRST_JSON_OBJECT.search(text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Could not extract JSON from LLM response: {text[:300]!r}")
