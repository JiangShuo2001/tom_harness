"""Minimal OpenAI-compatible model loader for skills_v4 experiments.

The experiment script monkey-patches ``GPTAgent.interact`` and uses only
``model_name``, ``url``, and ``headers`` from this class.
"""
from __future__ import annotations

import os


class GPTAgent:
    def __init__(self, model_name: str):
        self.model_name = model_name
        base_url = (
            os.environ.get(f"{_env_prefix(model_name)}_BASE_URL")
            or os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("BASE_URL")
            or "https://api.openai.com/v1"
        ).rstrip("/")
        api_key = (
            os.environ.get(f"{_env_prefix(model_name)}_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("API_KEY")
        )
        if not api_key:
            raise RuntimeError(
                "Missing API key. Set GLM_API_KEY for glm-* models, or OPENAI_API_KEY."
            )
        self.url = f"{base_url}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }


def _env_prefix(model_name: str) -> str:
    if model_name.lower().startswith("glm"):
        return "GLM"
    return "OPENAI"


def load_model(model_name: str):
    return GPTAgent(model_name)
