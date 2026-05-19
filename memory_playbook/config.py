"""Selector configuration: SelectorConfig dataclass, TOML loader, env-var resolution."""
from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass
from typing import Optional

PROVIDER_DEFAULT_BASE_URL = {
    "sambanova":   "https://api.sambanova.ai/v1",
    "together":    "https://api.together.xyz/v1",
    "openai":      "https://api.openai.com/v1",
    "commonstack": "https://api.commonstack.ai/v1",
    "deepseek":    "https://api.deepseek.com",
    "qwen":        "https://dashscope.aliyuncs.com/compatible-mode/v1",
}

_VALID_PROVIDERS = set(PROVIDER_DEFAULT_BASE_URL) | {"custom"}

_ENV_REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def resolve_env_refs(value: str, *, where: str) -> str:
    """Replace every ``${VAR}`` in *value* with ``os.environ[VAR]``."""
    if not isinstance(value, str):
        return value

    missing: list[str] = []

    def _sub(m: re.Match[str]) -> str:
        var = m.group(1)
        v = os.environ.get(var, "")
        if not v:
            missing.append(var)
        return v

    out = _ENV_REF.sub(_sub, value)
    if missing:
        names = ", ".join(f"${{{n}}}" for n in missing)
        raise ValueError(f"{where} references {names} which is unset or empty")
    return out


@dataclass(frozen=True)
class SelectorConfig:
    provider: str
    api_key: str
    model: str
    base_url: Optional[str] = None
    max_tokens: int = 1024
    max_bullets: int = 8
    use_json_mode: bool = False

    def resolved_base_url(self) -> str:
        if self.base_url:
            return self.base_url
        if self.provider == "custom":
            raise ValueError("base_url is required when provider='custom'")
        url = PROVIDER_DEFAULT_BASE_URL.get(self.provider)
        if not url:
            raise ValueError(
                f"Unknown provider {self.provider!r}. "
                f"Valid: {sorted(_VALID_PROVIDERS)}. "
                f"Or set base_url explicitly."
            )
        return url


def load_selector_config(path: str) -> SelectorConfig:
    """Load a ``SelectorConfig`` from a TOML file's ``[selector]`` table."""
    with open(path, "rb") as f:
        data = tomllib.load(f)

    raw = data.get("selector")
    if not raw:
        raise ValueError(f"[selector] table missing in {path}")

    provider = raw.get("provider")
    if not provider or provider not in _VALID_PROVIDERS:
        raise ValueError(
            f"[selector].provider={provider!r} is not one of {sorted(_VALID_PROVIDERS)}"
        )

    api_key_raw = raw.get("api_key")
    if not api_key_raw:
        raise ValueError("[selector].api_key is required")
    api_key = resolve_env_refs(api_key_raw, where="[selector].api_key")

    model = raw.get("model")
    if not model:
        raise ValueError("[selector].model is required")

    base_url = raw.get("base_url")
    if base_url:
        base_url = resolve_env_refs(base_url, where="[selector].base_url")

    max_tokens = raw.get("max_tokens", 1024)
    max_bullets = raw.get("max_bullets", 8)
    use_json_mode = raw.get("use_json_mode", False)

    return SelectorConfig(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url,
        max_tokens=max_tokens,
        max_bullets=max_bullets,
        use_json_mode=use_json_mode,
    )
