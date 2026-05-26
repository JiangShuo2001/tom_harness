"""SkillV5Router — 4-stage LLM-based router over 76 skills (56 micro + 20 macro).

Implements the skills_v5.1 routing pipeline:
  Stage 1 (route prep): micro-01 injected as router system prompt (always on)
  Stage 2 (route): pick 0+ skills based on route_mode
  get_skill_bodies(): render picked skills for injection into solver prompt

Route modes:
  baseline      — no routing, no skill
  macro_only    — pick from 20 macros
  micro_only    — pick from 52 non-L0 micros
  hierarchical  — step1: pick macros; step2: pick micros from their expandable
                  set. If step1 picks nothing, step2 falls back to all 52
                  non-L0 micros (degenerates to micro_only).
  flat_all      — pick from all 72 candidates (20 macros + 52 non-L0 micros)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from ..llm import LLMClient
from .base import Router, RouteDecision

logger = logging.getLogger(__name__)

_DEFAULT_SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills_v5.1" / "skills"

L0_MICROS = ["micro-01", "micro-02", "micro-03", "micro-04"]
L0_ROUTE = "micro-01"
L0_REVIEW = ["micro-02", "micro-03", "micro-04"]

ID_RE = re.compile(r"(?:macro|micro)-\d{2}")


# ─────────────────────────────────────────────────────────────────────────────
# Skill loading & rendering
# ─────────────────────────────────────────────────────────────────────────────

class _SkillCache:
    """Lazy-loaded cache for skill files."""

    def __init__(self, skills_dir: Path):
        self._dir = skills_dir
        self._md_cache: dict[str, str] = {}
        self._pack_cache: dict[str, dict] = {}

    def load_md(self, skill_id: str) -> str:
        if skill_id not in self._md_cache:
            path = self._dir / skill_id / "SKILL.md"
            self._md_cache[skill_id] = path.read_text(encoding="utf-8")
        return self._md_cache[skill_id]

    def load_pack(self, skill_id: str) -> dict:
        if skill_id not in self._pack_cache:
            path = self._dir / skill_id / "unit_pack.json"
            self._pack_cache[skill_id] = json.loads(path.read_text(encoding="utf-8"))
        return self._pack_cache[skill_id]

    def list_macros(self) -> list[str]:
        return sorted(
            d.name for d in self._dir.iterdir()
            if d.is_dir() and d.name.startswith("macro-")
        )

    def list_all_micros(self) -> list[str]:
        return sorted(
            d.name for d in self._dir.iterdir()
            if d.is_dir() and d.name.startswith("micro-")
        )

    def list_non_l0_micros(self) -> list[str]:
        l0_set = set(L0_MICROS)
        return [m for m in self.list_all_micros() if m not in l0_set]


def _router_summary(pack: dict, skill_id: str) -> str:
    parts = [f"[{skill_id}] {pack.get('title', '')}",
             f"  decision_variable: {pack.get('decision_variable', '')}"]
    if pack.get("direct_route_rule"):
        parts.append(f"  direct_route_rule: {pack['direct_route_rule']}")
    use_when = pack.get("use_when") or []
    if use_when:
        parts.append("  use_when: " + " | ".join(use_when))
    do_not = pack.get("do_not_use_when") or []
    if do_not:
        parts.append("  do_not_use_when: " + " | ".join(do_not))
    return "\n".join(parts)


_INTERNAL_ID_RE = re.compile(r"\b(?:micro|macro)-\d{2}\b")


def _scrub_internal_ids(text: str) -> str:
    """Replace micro-XX / macro-XX mentions with a generic label so internal
    naming does not leak when content is shown as a guide."""
    return _INTERNAL_ID_RE.sub("a neighboring skill", text)


def _render_full(md_text: str, *, strip_id: bool = False) -> str:
    md = md_text
    if strip_id and md.startswith("---"):
        end = md.find("\n---", 3)
        if end != -1:
            md = md[end + 4:].lstrip("\n")
    if strip_id:
        m = re.search(r"\n##\s+Boundary Exit Rule\s*\n", md)
        if m:
            start = m.start()
            tail = md[m.end():]
            next_h2 = re.search(r"\n##\s+", tail)
            if next_h2:
                md = md[:start] + "\n" + tail[next_h2.start():].lstrip("\n")
            else:
                md = md[:start].rstrip() + "\n"
        md = _scrub_internal_ids(md)
    return md


def _render_light(pack: dict, skill_id: str, *, strip_id: bool = False) -> str:
    parts = []
    if not strip_id:
        parts.append(f"### [{skill_id}] {pack.get('title', '')}")
    elif pack.get("title"):
        parts.append(f"### {pack.get('title')}")
    if pack.get("decision_variable"):
        parts.append(f"**Decision variable**: {pack['decision_variable']}")
    if pack.get("direct_route_rule"):
        parts.append(f"**Direct route rule**: {pack['direct_route_rule']}")
    wf = pack.get("workflow") or []
    if wf:
        parts.append("**Workflow**:\n" + "\n".join(f"- {s}" for s in wf))
    sc = pack.get("special_case") or {}
    if sc.get("rule"):
        block = [f"**Special case — {sc.get('title', '').strip()}**: {sc['rule']}"]
        we = sc.get("worked_example") or {}
        if we.get("scene"):
            block.append(f"  - Scene: {we.get('scene', '')}")
            block.append(f"  - Question: {we.get('question', '')}")
            block.append(f"  - Logic: {we.get('answer_logic', '')}")
        parts.append("\n".join(block))
    if not strip_id:
        bex = pack.get("boundary_exit_rule") or []
        if bex:
            parts.append("**Boundary exits**:\n" + "\n".join(f"- {s}" for s in bex))
    out = "\n\n".join(parts)
    if strip_id:
        out = _scrub_internal_ids(out)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Prompt building
# ─────────────────────────────────────────────────────────────────────────────

MULTI_RULES_EN = (
    "Output a JSON array of ids you want to use, e.g. [\"micro-12\", \"micro-23\"]. "
    "If none of the skills apply, output [\"none\"]. No explanation."
)
MULTI_RULES_ZH = (
    "输出一个 JSON 数组,内容是你想使用的 id,例如 [\"micro-12\", \"micro-23\"]。"
    "如果都不适用,输出 [\"none\"]。不要解释。"
)


def _build_router_system(l0_content: str, rules: str, lang: str) -> str:
    if lang == "zh":
        return (
            "你是一个社会认知技能路由器。先阅读下面的任务路由指南,"
            "然后从候选技能中选择最合适的。\n\n"
            "## 任务路由指南\n\n" + l0_content + "\n\n"
            "## 路由规则\n" + rules
        )
    return (
        "You are a social-cognition skill router. First read the task-"
        "routing playbook below, then select the best candidate skill(s).\n\n"
        "## Task Routing Playbook\n\n" + l0_content + "\n\n"
        "## Routing rules\n" + rules
    )


def _build_router_user(story: str, question: str, options: dict[str, str],
                       candidates_block: str, header: str, lang: str) -> str:
    opts = "\n".join(f"{k}. {v}" for k, v in options.items() if v)
    if lang == "zh":
        return (
            f"故事:\n{story}\n\n问题: {question}\n\n选项:\n{opts}\n\n"
            f"候选 {header}:\n{candidates_block}\n\n你的选择:"
        )
    return (
        f"Story:\n{story}\n\nQuestion: {question}\n\nOptions:\n{opts}\n\n"
        f"Candidate {header}:\n{candidates_block}\n\nYour choice:"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Parsing
# ─────────────────────────────────────────────────────────────────────────────

def _parse_multi_ids(text: str, valid: set[str]) -> list[str]:
    if not text:
        return []
    if re.search(r"\bnone\b", text, re.IGNORECASE):
        return []
    ids = ID_RE.findall(text)
    out = []
    seen: set[str] = set()
    for pid in ids:
        if pid in valid and pid not in seen:
            out.append(pid)
            seen.add(pid)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SkillV5Router(Router):
    """Routes a ToM question using the skills_v5.1 library (76 skills)."""

    llm: LLMClient
    skills_dir: Path = _DEFAULT_SKILLS_DIR
    route_mode: str = "hierarchical"
    inject_mode: str = "light"
    router_max_tokens: int = 128
    lang: str = "en"

    _cache: _SkillCache = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._cache = _SkillCache(self.skills_dir)

    def route(
        self,
        *,
        question: str,
        story: str = "",
        options: dict[str, str] | None = None,
        task_type: str | None = None,
    ) -> RouteDecision:
        opts = options or {}

        if self.route_mode == "baseline":
            return RouteDecision(skill_id=None, skill_ids=[], rationale="baseline: no routing")

        self._route_llm_calls = 0
        picked = self._do_route(story=story, question=question, options=opts)

        skill_id = picked[0] if picked else None
        return RouteDecision(skill_id=skill_id, skill_ids=picked,
                             rationale=f"v5/{self.route_mode}: {picked}",
                             n_llm_calls=self._route_llm_calls)

    def _do_route(self, *, story: str, question: str, options: dict[str, str]) -> list[str]:
        if self.route_mode == "macro_only":
            return self._route_from_pool(
                story, question, options,
                self._cache.list_macros(), "macros"
            )
        elif self.route_mode == "micro_only":
            return self._route_from_pool(
                story, question, options,
                self._cache.list_non_l0_micros(), "micros"
            )
        elif self.route_mode == "hierarchical":
            return self._route_hierarchical(story, question, options)
        elif self.route_mode == "flat_all":
            all_ids = self._cache.list_macros() + self._cache.list_non_l0_micros()
            return self._route_from_pool(
                story, question, options,
                all_ids, "skills (macros and micros)"
            )
        else:
            logger.warning("Unknown route_mode=%s, falling back to no-op", self.route_mode)
            return []

    def _route_from_pool(self, story: str, question: str, options: dict[str, str],
                         candidates: list[str], header: str) -> list[str]:
        blocks = "\n\n".join(
            _router_summary(self._cache.load_pack(c), c) for c in candidates
        )
        l0_content = self._render_skill(L0_ROUTE, strip_id=True)
        rules = MULTI_RULES_ZH if self.lang == "zh" else MULTI_RULES_EN

        sys_p = _build_router_system(l0_content, rules, self.lang)
        user_p = _build_router_user(story, question, options, blocks, header, self.lang)

        try:
            resp = self.llm.chat(sys_p, user_p, max_tokens=self.router_max_tokens)
            self._route_llm_calls += 1
        except Exception as e:
            logger.warning("[SkillV5Router] LLM call failed: %s", e)
            return []

        return _parse_multi_ids(resp, set(candidates))

    def _route_hierarchical(self, story: str, question: str, options: dict[str, str]) -> list[str]:
        macros = self._cache.list_macros()
        macro_picks = self._route_from_pool(story, question, options, macros, "macros")

        if macro_picks:
            expandable: list[str] = []
            seen: set[str] = set()
            l0_set = set(L0_MICROS)
            for m in macro_picks:
                pack = self._cache.load_pack(m)
                for mid in (pack.get("expandable_micro_ids") or []):
                    if mid not in seen and mid not in l0_set:
                        seen.add(mid)
                        expandable.append(mid)
            if not expandable:
                return list(macro_picks)
            step2_pool = expandable
            step2_header = "micros to expand the selected macro(s)"
        else:
            step2_pool = self._cache.list_non_l0_micros()
            step2_header = "micros (no macro was selected — pick directly from non-L0 micros)"

        micro_picks = self._route_from_pool(
            story, question, options, step2_pool,
            step2_header,
        )
        return list(macro_picks) + micro_picks

    # ── skill rendering ────────────────────────────────────────────────────

    def _render_skill(self, skill_id: str, strip_id: bool = False) -> str:
        if self.inject_mode == "full":
            return _render_full(self._cache.load_md(skill_id), strip_id=strip_id)
        return _render_light(self._cache.load_pack(skill_id), skill_id, strip_id=strip_id)

    def get_skill_body(self, skill_id: str | None) -> str | None:
        """Backward-compatible single skill body (for v4 interface)."""
        if not skill_id:
            return None
        try:
            return self._render_skill(skill_id)
        except (FileNotFoundError, KeyError):
            return None

    def get_skill_bodies(self, skill_ids: list[str]) -> str | None:
        """Render multiple skills joined by separator."""
        if not skill_ids:
            return None
        bodies = []
        for sid in skill_ids:
            try:
                bodies.append(self._render_skill(sid))
            except (FileNotFoundError, KeyError):
                logger.warning("Skill %s not found, skipping", sid)
        if not bodies:
            return None
        return "\n\n---\n\n".join(bodies)
