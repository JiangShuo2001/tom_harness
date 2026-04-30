"""Set1 adapter — wraps the 15-skill SKILL.md pack.

Pack origin: /workspace/symbolictom_report/skill_set1/
Layout    : skill1/, skill2/, …, skill15/, each with SKILL.md.
Routing   : encoded from ROUTING.md (static rules over question form).

This file does NOT modify the pack — it only reads SKILL.md files,
rewrites the frontmatter on the fly into our SkillLib's expected
{skill_id, name, description, triggers} schema, and translates the
ROUTING.md prose into a Python decision function.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ...tools.skills import SkillLib, SkillRecord, _parse_simple_yaml
from .adapter import RoutingResult, SkillPackAdapter, SkillPackInfo


# ─────────────────────────────────────────────────────────────────────────────
# Static routing — encoded from /workspace/.../skill_set1/ROUTING.md
# Each rule: (predicate_callable, skill_id, family, rationale)
# ─────────────────────────────────────────────────────────────────────────────

def _has_any(text: str, patterns: list[str]) -> bool:
    text = text.lower()
    return any(p.lower() in text for p in patterns)


def _has_re(text: str, regex: str) -> bool:
    return bool(re.search(regex, text, re.IGNORECASE))


def _route_set1(question: str, story: str, options: dict[str, str] | None) -> RoutingResult:
    q = question or ""
    s = story or ""
    qs = f"{q} {s}"

    # Family A — Faux pas vs Speaker knowledge ─────────────────────────────
    if _has_re(q, r"\b(does|did|do)\s+\w+\s+(know|knew|remember|remembers|aware|forget|forgot)\b") or \
       _has_any(q, ["know that", "did know", "知道", "记得", "意识到", "清楚"]):
        return RoutingResult(skill_id="cs1_skill2", confidence=0.85, rationale="A: knowledge/memory question")
    if _has_any(q, ["inappropriate", "rude", "awkward", "faux pas", "失礼", "不当", "失言"]) or \
       _has_re(q, r"which (sentence|line|remark)"):
        return RoutingResult(skill_id="cs1_skill1", confidence=0.85, rationale="A: faux-pas judgement")

    # Family B — Belief tracking ───────────────────────────────────────────
    # Second-order: "X thinks/believes Y will/looks/thinks"
    if _has_re(q, r"(does|will)\s+\w+\s+(think|believe|expect)\s+\w+\s+(will|would|look|thinks)") or \
       _has_re(q, r"(认为|觉得|以为).*(认为|觉得|以为|会|去)"):
        return RoutingResult(skill_id="cs1_skill4", confidence=0.85, rationale="B: 2nd-order belief")
    # Content-vs-label
    if _has_any(qs, ["label", "labelled", "container", "expect.*find inside", "what is in", "标签", "里面是什么", "以为是"]):
        return RoutingResult(skill_id="cs1_skill5", confidence=0.7, rationale="B: content/label belief")
    # First-order location belief — "where will X look"
    if _has_re(q, r"where\s+will\s+\w+\s+(look|search)") or _has_any(q, ["在哪里找", "去哪里找"]):
        return RoutingResult(skill_id="cs1_skill3", confidence=0.85, rationale="B: 1st-order belief")

    # Family E — Quantitative scalar ───────────────────────────────────────
    if _has_any(q, ["how many", "几", "多少"]) and _has_any(qs, ["most", "almost", "some", "几乎", "大多数", "一些", "部分"]):
        # Posterior if observation present
        if _has_any(qs, ["after", "counts", "observes", "saw", "已经看到", "数过", "数完", "观察"]) and \
           _has_re(qs, r"\b(\d+)\s+(are|is|wear|of)\b"):
            return RoutingResult(skill_id="cs1_skill11", confidence=0.85, rationale="E: scalar posterior")
        return RoutingResult(skill_id="cs1_skill10", confidence=0.85, rationale="E: scalar prior")

    # Family C — Social cue ────────────────────────────────────────────────
    if _has_re(q, r"why did \w+ smile") or _has_re(q, r"why did \w+ wink") or \
       _has_re(q, r"why did \w+ glance") or _has_any(q, ["为什么.*笑", "为什么.*眨眼"]):
        return RoutingResult(skill_id="cs1_skill7", confidence=0.7, rationale="C: cue intention")
    if _has_re(q, r"what does .* mean") or _has_any(q, ["really mean", "imply", "really want", "真正想", "言外之意", "暗示"]):
        return RoutingResult(skill_id="cs1_skill12", confidence=0.7, rationale="C: indirect speech")
    if _has_any(q, ["what does the observer", "after seeing", "look", "react", "感受", "觉得"]) and \
       _has_any(s, ["smile", "wink", "glance", "nod", "微笑", "眨眼", "点头"]):
        return RoutingResult(skill_id="cs1_skill6", confidence=0.6, rationale="C: belief-based reaction")

    # Family F — Persuasion ────────────────────────────────────────────────
    if _has_any(q, ["convince", "persuade", "说服", "劝说", "如何让"]):
        return RoutingResult(skill_id="cs1_skill13", confidence=0.85, rationale="F: persuasion")

    # Family G — Truth/motive ─────────────────────────────────────────────
    if _has_re(q, r"is \w+ true") or _has_any(q, ["is what", "said true", "yes or no", "属实", "是真的吗"]):
        return RoutingResult(skill_id="cs1_skill14", confidence=0.8, rationale="G: truth judgement")
    if _has_re(q, r"why does .+ say") or _has_any(q, ["为什么.*说", "为什么.*会说"]):
        return RoutingResult(skill_id="cs1_skill15", confidence=0.8, rationale="G: motive explanation")

    # Family D — Emotion ───────────────────────────────────────────────────
    if _has_re(q, r"why does \w+ feel") or _has_re(q, r"why .+ surprising") or \
       _has_any(q, ["为什么.*感到", "为什么.*惊讶"]):
        return RoutingResult(skill_id="cs1_skill9", confidence=0.7, rationale="D: emotion explanation")
    if _has_any(q, ["feel", "mood", "emotion", "情绪", "感受", "心情"]):
        return RoutingResult(skill_id="cs1_skill8", confidence=0.7, rationale="D: emotion attribution")

    return RoutingResult(skill_id=None, confidence=0.0, rationale="set1: no rule fired")


# ─────────────────────────────────────────────────────────────────────────────
# Adapter
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Set1Adapter(SkillPackAdapter):
    """Wraps skill_set1 pack."""

    pack_root: Path = Path(__file__).resolve().parent / "data" / "skill_set1"
    routing_mode: str = "static"           # only mode supported by set1
    _loaded_ids: list[str] = None

    def load_into(self, skill_lib: SkillLib) -> int:
        if self._loaded_ids is None:
            self._loaded_ids = []
        loaded = 0
        for d in sorted(self.pack_root.iterdir()):
            if not d.is_dir() or not d.name.startswith("skill"):
                continue
            md = d / "SKILL.md"
            if not md.exists():
                continue
            text = md.read_text(encoding="utf-8")
            m = re.match(r"^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$", text)
            if m:
                front_raw, body = m.group(1), m.group(2)
                front = _parse_simple_yaml(front_raw)
            else:
                front, body = {}, text
            external_name = front.get("name", d.name)            # "skill1"
            new_skill_id = f"cs1_{external_name}"                  # namespaced
            description = front.get("description", "")[:200]
            rec = SkillRecord(
                skill_id=new_skill_id,
                name=front.get("name", new_skill_id),
                description=description,
                triggers=[],
                body=body.strip(),
                metadata={"contributor_pack": "set1", "external_name": external_name,
                          "external_path": str(d)},
            )
            skill_lib._skills[new_skill_id] = rec
            self._loaded_ids.append(new_skill_id)
            loaded += 1
        return loaded

    def route(
        self, *, question: str, story: str = "",
        options: dict[str, str] | None = None, task_type: str | None = None,
    ) -> RoutingResult:
        return _route_set1(question, story, options)

    def metadata(self) -> SkillPackInfo:
        return SkillPackInfo(
            pack_name="set1",
            contributor="teammate-A",
            pack_version=str(self.pack_root.stat().st_mtime_ns) if self.pack_root.exists() else "missing",
            n_skills=len(self._loaded_ids or []),
            skill_ids=list(self._loaded_ids or []),
            routing_mode=self.routing_mode,
            extras={"pack_root": str(self.pack_root)},
        )
