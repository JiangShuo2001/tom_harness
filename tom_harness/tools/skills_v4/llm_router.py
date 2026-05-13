"""
LLM-based skill router for the v4 skill set (22 skills).

Given a case (story + question + options), ask an LLM to choose ONE of the
22 skills (or ``NONE``). No ``task_type`` metadata is required at inference
time.

Public API (mirrors ``papers/skill_v2/llm_router.py``):
  ROUTER_CATALOG          — short id → 1-line description (used in router
                            prompt; built automatically from each
                            ``skill*/SKILL.md`` frontmatter ``description``).
  build_router_prompt()   — assemble the classification prompt.
  parse_router_choice()   — extract the chosen skill id from the LLM
                            response.
  route(model, item)      — convenience wrapper, returns
                            (skill_id_or_None, raw_response).
  get_skill_prompt(id)    — return the full ``SKILL.md`` body of the
                            chosen skill, or ``None`` for ``NONE`` /
                            invalid IDs.

The catalog is built lazily on first import. To refresh after editing
SKILL.md files in the same Python process, call ``rebuild_catalog()``.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
SKILL_IDS: list[str] = [f"skill{i}" for i in range(1, 23)]  # skill1 .. skill22


# ─────────────────────────────────────────────────────────────────────────────
# Catalog construction — read each skill's SKILL.md frontmatter `description`.
# ─────────────────────────────────────────────────────────────────────────────
_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(?P<body>.*?)\n---\s*\n", re.DOTALL,
)
_FIELD_RE = re.compile(r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?P<value>.*)$")


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Tiny YAML-frontmatter parser that handles the simple key: value
    layout used by every SKILL.md in this directory. We deliberately do
    NOT depend on PyYAML."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    out: dict[str, str] = {}
    for line in match.group("body").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _FIELD_RE.match(line)
        if not m:
            continue
        out[m.group("key").strip()] = m.group("value").strip().strip("\"'")
    return out


def _read_skill_md(skill_id: str) -> str:
    return (ROOT / skill_id / "SKILL.md").read_text(encoding="utf-8")


def _strip_frontmatter(text: str) -> str:
    return _FRONTMATTER_RE.sub("", text, count=1).lstrip()


def _build_catalog() -> dict[str, str]:
    catalog: dict[str, str] = {}
    for sid in SKILL_IDS:
        try:
            text = _read_skill_md(sid)
        except FileNotFoundError:
            continue
        meta = _parse_frontmatter(text)
        desc = meta.get("description", "").strip()
        if not desc:
            # Fallback: take the first non-empty paragraph after the H1.
            stripped = _strip_frontmatter(text)
            paragraphs = [p.strip() for p in stripped.split("\n\n") if p.strip()]
            desc = paragraphs[1] if len(paragraphs) > 1 else (paragraphs[0] if paragraphs else sid)
        catalog[sid] = desc
    catalog["NONE"] = (
        "No skill above clearly applies; the question is straightforward "
        "or doesn't match any of the 22 patterns."
    )
    return catalog


ROUTER_CATALOG: dict[str, str] = _build_catalog()
VALID_IDS: list[str] = list(ROUTER_CATALOG.keys())


def rebuild_catalog() -> dict[str, str]:
    """Re-read every SKILL.md from disk and refresh the in-process
    catalog. Useful if SKILL.md files change inside a long-running
    process (notebook, training loop)."""
    global ROUTER_CATALOG, VALID_IDS
    ROUTER_CATALOG = _build_catalog()
    VALID_IDS = list(ROUTER_CATALOG.keys())
    _get_skill_body.cache_clear()
    return ROUTER_CATALOG


# ─────────────────────────────────────────────────────────────────────────────
# Router prompt
# ─────────────────────────────────────────────────────────────────────────────
ROUTER_GUIDE_MODE = os.environ.get("EXP_ROUTER_GUIDE", "compact").strip().lower()
ALLOW_NONE = os.environ.get("EXP_ALLOW_NONE", "true").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}


def _extract_markdown_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ms)^## {re.escape(heading)}\s*\n(?P<body>.*?)(?=^## |\Z)"
    )
    match = pattern.search(text)
    return match.group("body").strip() if match else ""


@lru_cache(maxsize=4)
def _read_routing_guide(mode: str) -> str:
    """Return optional routing context from ROUTING.md.

    Modes:
      - none/catalog: use only SKILL.md descriptions.
      - compact: include workflow + boundary/disambiguation sections.
      - full: include the whole ROUTING.md.
    """
    mode = (mode or "compact").strip().lower()
    if mode in {"none", "catalog", "off", "0", "false"}:
        return ""

    path = ROOT / "ROUTING.md"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

    if mode == "full":
        return text.strip()

    sections = [
        "Router First Principle",
        "Machine Router Contract",
        "Fast Routing Workflow",
        "High-Value Boundary Checks",
        "Disambiguation Cues for the Most Confused Pairs",
        "General Rule",
    ]
    chunks = []
    for section in sections:
        body = _extract_markdown_section(text, section)
        if body:
            chunks.append(f"## {section}\n{body}")
    return "\n\n".join(chunks).strip()


ROUTER_INSTRUCTION = """You are a skill router for Theory-of-Mind
multiple-choice questions. Read the story, question, and options below,
then pick the ONE strategy that best matches the case. Pick at most one.

Available strategies:

{catalog}

Routing guide context:

{routing_guide}

NONE policy for this run:

{none_policy}

Decision rules:
- Look at WHAT THE QUESTION IS ASKING and WHAT KIND OF REASONING is required.
- Match to the strategy whose triggering pattern best fits.
- Prefer the NARROWEST skill that directly matches the asked output.
- If the question changes from `what` to `why`, or from `truth` to
  `motive`, route to the why/motive skill instead of the what/truth one.
- Prefer choosing the closest skill among skill1-skill22 when the case
  involves social reasoning, belief tracking, emotion, intention, indirect
  speech, knowledge, perception, preference, quantity, spatial perspective,
  or action choice.
- Choose NONE only when the question is outside these Theory-of-Mind skill
  areas. Do not choose NONE merely because the match is imperfect.

Reply with EXACTLY this format on a single line, with no additional text:
Skill: <ID>

where <ID> is one of: {ids}.
"""


def _format_catalog(catalog: dict[str, str] | None = None) -> str:
    cat = catalog or ROUTER_CATALOG
    return "\n".join(
        f"- {sid}: {desc}" for sid, desc in cat.items() if sid != "NONE"
    )


def _valid_output_ids() -> list[str]:
    if ALLOW_NONE:
        return VALID_IDS
    return [sid for sid in VALID_IDS if sid != "NONE"]


def _format_none_policy() -> str:
    if ALLOW_NONE:
        return (
            "NONE is allowed, but it is a last resort. Use NONE only when "
            "the question is outside the 22 Theory-of-Mind skill areas."
        )
    return (
        "NONE is disabled. You must choose the closest skill from skill1 "
        "through skill22, even if the match is imperfect."
    )


def build_router_prompt(
    story: str,
    question: str,
    options: Iterable[str],
    labels: Iterable[str],
) -> str:
    opts = "\n".join(f"{l}. {o}" for l, o in zip(labels, options))
    head = ROUTER_INSTRUCTION.format(
        catalog=_format_catalog(),
        routing_guide=_read_routing_guide(ROUTER_GUIDE_MODE) or "(not provided)",
        none_policy=_format_none_policy(),
        ids=", ".join(_valid_output_ids()),
    )
    return (
        f"{head}\n"
        f"=== STORY ===\n{story}\n\n"
        f"=== QUESTION ===\n{question}\n\n"
        f"=== OPTIONS ===\n{opts}\n\n"
        f"Now output your choice:\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Parsing — robust to noisy LLM responses.
# ─────────────────────────────────────────────────────────────────────────────
_SKILL_TOKEN_RE = re.compile(r"\b(skill(?:1[0-9]|2[0-2]|[1-9])|NONE)\b", re.IGNORECASE)


def parse_router_choice(response: str) -> str | None:
    """Return the chosen skill_id (one of ``VALID_IDS``) or ``None`` on
    failure."""
    if not response:
        return None

    # Preferred: explicit `Skill: <ID>` (or Chinese full-width colon).
    m = re.search(r"[Ss]kill\s*[:：]\s*([A-Za-z0-9_]+)", response)
    if m:
        cand = m.group(1).strip()
        cand_norm = _normalize_id(cand)
        if cand_norm in _valid_output_ids():
            return cand_norm

    # Fallback: scan for any token matching the skill regex; take the LAST.
    matches = _SKILL_TOKEN_RE.findall(response)
    for tok in reversed(matches):
        norm = _normalize_id(tok)
        if norm in _valid_output_ids():
            return norm
    return None


def _normalize_id(token: str) -> str:
    """Accept ``Skill1``, ``SKILL1``, ``skill_1``, ``S1`` (legacy) etc.
    and map to the canonical ``skillN`` form used in this directory."""
    if not token:
        return ""
    raw = token.strip().replace("_", "").replace("-", "")
    if raw.upper() == "NONE":
        return "NONE"
    # legacy v2 form: S1_FauxPas / S11_BeliefEmotion → not a v4 id; refuse
    if re.match(r"^S\d+([A-Za-z]+)?$", raw):
        return ""
    m = re.match(r"^skill(\d{1,2})$", raw, re.IGNORECASE)
    if not m:
        return ""
    n = int(m.group(1))
    if 1 <= n <= 22:
        return f"skill{n}"
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Skill prompt retrieval
# ─────────────────────────────────────────────────────────────────────────────
@lru_cache(maxsize=64)
def _get_skill_body(skill_id: str) -> str:
    text = _read_skill_md(skill_id)
    return _strip_frontmatter(text).strip()


def get_skill_prompt(skill_id: str | None) -> str | None:
    """Return the full ``SKILL.md`` body (without the YAML frontmatter)
    for the chosen skill. Returns ``None`` for ``NONE`` / invalid IDs."""
    if not skill_id or skill_id == "NONE":
        return None
    canonical = _normalize_id(skill_id)
    if not canonical:
        return None
    try:
        return _get_skill_body(canonical)
    except FileNotFoundError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Convenience wrapper
# ─────────────────────────────────────────────────────────────────────────────
def route(model, item, max_tokens: int = 64):
    """Run the router LLM call once and return ``(skill_id_or_None,
    raw_response)``.

    ``item`` is a dict with ``story``, ``question``, ``options``, and
    ``labels`` keys, exactly as accepted by
    ``papers/skill_v2/llm_router.py::route``.

    The returned ``skill_id`` is either ``"skillN"`` (1 ≤ N ≤ 22),
    ``"NONE"``, or ``None`` (parsing failed; treat as ``NONE`` and use the
    vanilla prompt path).
    """
    prompt = build_router_prompt(
        item["story"], item["question"], item["options"], item["labels"],
    )
    resp = model.interact(prompt, max_tokens=max_tokens)
    return parse_router_choice(resp), resp


__all__ = [
    "ROUTER_CATALOG",
    "VALID_IDS",
    "ALLOW_NONE",
    "ROUTER_GUIDE_MODE",
    "SKILL_IDS",
    "rebuild_catalog",
    "build_router_prompt",
    "parse_router_choice",
    "get_skill_prompt",
    "route",
]
