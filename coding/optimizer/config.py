"""Configuration helpers for the Harness Optimizer.

The optimizer prefers PyYAML when available, but degrades gracefully to
a small built-in YAML reader/writer that supports the subset of YAML the
default policy files actually use (mappings, sequences, scalars, simple
list-of-strings). This keeps the package importable in environments
where PyYAML is not installed yet.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────────────────────────────
#  YAML adapter
# ──────────────────────────────────────────────────────────────────────

try:  # pragma: no cover — exercised by import path
    import yaml as _yaml
    _HAS_PYYAML = True
except ImportError:  # pragma: no cover
    _yaml = None
    _HAS_PYYAML = False


def has_pyyaml() -> bool:
    return _HAS_PYYAML


def load_yaml(path: str | Path) -> Any:
    """Load a YAML document. Falls back to a minimal parser if PyYAML missing.

    The minimal parser is intentionally restrictive — it handles the
    subset of YAML used by ``policies/*.yaml``: nested mappings, lists
    of scalars, and inline lists. For anything richer, users should
    install PyYAML (``pip install pyyaml``).
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if _HAS_PYYAML:
        return _yaml.safe_load(text)
    return _MiniYamlParser(text).parse()


def dump_yaml(obj: Any, path: str | Path) -> None:
    """Write a Python object to YAML. Uses PyYAML if available, else
    a deterministic JSON-as-YAML fallback (still valid YAML)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if _HAS_PYYAML:
        text = _yaml.safe_dump(obj, sort_keys=False, allow_unicode=True)
    else:
        # JSON is a valid YAML subset; this guarantees round-trip even
        # without PyYAML, at the cost of human-readability.
        text = json.dumps(obj, indent=2, ensure_ascii=False)
    p.write_text(text, encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────
#  OptimizerConfig
# ──────────────────────────────────────────────────────────────────────

@dataclass
class OptimizerConfig:
    """Process-wide settings for an optimizer run.

    ``runs_dir`` is where ExperienceStore writes per-run artefacts.
    ``policies_dir`` is where default / search-output policies live.
    """

    package_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent
    )
    runs_dir: Path = field(default_factory=lambda: Path("optimizer_runs"))
    policies_dir: Path | None = None
    examples_dir: Path | None = None

    def __post_init__(self) -> None:
        if self.policies_dir is None:
            self.policies_dir = self.package_root / "policies"
        if self.examples_dir is None:
            self.examples_dir = self.package_root / "examples"
        self.runs_dir = Path(self.runs_dir)

    def default_policy_bundle_path(self) -> Path:
        return self.policies_dir / "default_policy_bundle.yaml"

    def default_route_gate_policy_path(self) -> Path:
        return self.policies_dir / "default_route_gate_policy.yaml"

    def default_prompt_compose_policy_path(self) -> Path:
        return self.policies_dir / "default_prompt_compose_policy.yaml"


# ──────────────────────────────────────────────────────────────────────
#  Minimal YAML parser (fallback)
# ──────────────────────────────────────────────────────────────────────

class _MiniYamlParser:
    """A tiny indentation-based YAML reader.

    Supported:
      - block mappings (``key: value`` / ``key:`` + indented block)
      - block sequences (``- item`` / ``- key: value``)
      - flow scalars (strings, ints, floats, bool, null)
      - flow sequences (``[a, b, c]``) — strings/numbers/bools only
      - comments (``# ...``)

    NOT supported: anchors, aliases, multiline scalars, complex flow
    mappings, tagged values. That is fine — our policies only use the
    supported subset, and PyYAML is the recommended path anyway.
    """

    def __init__(self, text: str) -> None:
        # Strip comment-only / blank lines but keep indentation of real lines.
        self.lines: list[tuple[int, str]] = []
        for raw in text.splitlines():
            stripped = raw.split("#", 1)[0].rstrip() if "#" in raw else raw.rstrip()
            if not stripped.strip():
                continue
            indent = len(stripped) - len(stripped.lstrip(" "))
            self.lines.append((indent, stripped.lstrip(" ")))
        self.pos = 0

    # ── public ────────────────────────────────────────────────────────
    def parse(self) -> Any:
        if not self.lines:
            return None
        return self._parse_block(self.lines[0][0])

    # ── internals ─────────────────────────────────────────────────────
    def _peek(self) -> tuple[int, str] | None:
        return self.lines[self.pos] if self.pos < len(self.lines) else None

    def _parse_block(self, indent: int) -> Any:
        peek = self._peek()
        if peek is None:
            return None
        if peek[1].startswith("- "):
            return self._parse_seq(indent)
        return self._parse_map(indent)

    def _parse_map(self, indent: int) -> dict:
        out: dict = {}
        while True:
            peek = self._peek()
            if peek is None or peek[0] < indent:
                return out
            if peek[0] > indent:  # shouldn't happen at this level
                return out
            line = peek[1]
            if ":" not in line:
                return out
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            self.pos += 1
            if rest:
                out[key] = self._parse_scalar_or_flow(rest)
            else:
                child = self._peek()
                if child is None or child[0] <= indent:
                    out[key] = None
                else:
                    out[key] = self._parse_block(child[0])
        return out

    def _parse_seq(self, indent: int) -> list:
        out: list = []
        while True:
            peek = self._peek()
            if peek is None or peek[0] < indent:
                return out
            if not peek[1].startswith("- "):
                return out
            tail = peek[1][2:].strip()
            self.pos += 1
            if ":" in tail and not tail.startswith("["):
                # ``- key: value`` → treat as inline-mapping start
                key, _, rest = tail.partition(":")
                key, rest = key.strip(), rest.strip()
                inline_map: dict = {}
                if rest:
                    inline_map[key] = self._parse_scalar_or_flow(rest)
                else:
                    child = self._peek()
                    if child is not None and child[0] > indent:
                        inline_map[key] = self._parse_block(child[0])
                    else:
                        inline_map[key] = None
                # Continue collecting same-indent siblings of this map.
                while True:
                    sib = self._peek()
                    if sib is None or sib[0] <= indent or sib[1].startswith("- "):
                        break
                    sib_line = sib[1]
                    if ":" not in sib_line:
                        break
                    sk, _, sv = sib_line.partition(":")
                    sk, sv = sk.strip(), sv.strip()
                    self.pos += 1
                    if sv:
                        inline_map[sk] = self._parse_scalar_or_flow(sv)
                    else:
                        sub = self._peek()
                        if sub is not None and sub[0] > sib[0]:
                            inline_map[sk] = self._parse_block(sub[0])
                        else:
                            inline_map[sk] = None
                out.append(inline_map)
            else:
                out.append(self._parse_scalar_or_flow(tail))

    def _parse_scalar_or_flow(self, s: str) -> Any:
        s = s.strip()
        if s.startswith("[") and s.endswith("]"):
            inner = s[1:-1].strip()
            if not inner:
                return []
            return [self._parse_scalar(p.strip()) for p in inner.split(",")]
        return self._parse_scalar(s)

    @staticmethod
    def _parse_scalar(s: str) -> Any:
        if (s.startswith('"') and s.endswith('"')) or (
            s.startswith("'") and s.endswith("'")
        ):
            return s[1:-1]
        if s in {"null", "Null", "NULL", "~", ""}:
            return None
        if s in {"true", "True", "TRUE"}:
            return True
        if s in {"false", "False", "FALSE"}:
            return False
        # int / float
        try:
            if "." in s or "e" in s or "E" in s:
                return float(s)
            return int(s)
        except ValueError:
            return s
