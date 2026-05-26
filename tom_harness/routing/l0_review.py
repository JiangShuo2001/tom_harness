"""L0 Review — Stage 4 of the skills_v5.1 pipeline.

v5.1 upgrade: the reviewer now receives the solver's full reasoning chain +
picked skill IDs and performs a structured chain-of-thought audit
(REASONING + ANSWER output) instead of a blind letter re-check.

Injects micro-02 (evidence chain) + micro-03 (explanation competition) +
micro-04 (anti-bias check) with strip_id=True to hide internal naming.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from ..llm import LLMClient

logger = logging.getLogger(__name__)

L0_REVIEW_IDS = ["micro-02", "micro-03", "micro-04"]

ANSWER_LINE_RE = re.compile(r"(?im)^\s*ANSWER\s*[:：]\s*([A-D])\b")
LETTER_RE = re.compile(r"\b([A-D])\b")


def _load_and_render(skills_dir: Path, skill_id: str, inject_mode: str) -> str:
    """Load a skill and render it with strip_id=True (hide internal IDs)."""
    import json

    _INTERNAL_ID_RE = re.compile(r"\b(?:micro|macro)-\d{2}\b")

    if inject_mode == "full":
        md = (skills_dir / skill_id / "SKILL.md").read_text(encoding="utf-8")
        if md.startswith("---"):
            end = md.find("\n---", 3)
            if end != -1:
                md = md[end + 4:].lstrip("\n")
        m = re.search(r"\n##\s+Boundary Exit Rule\s*\n", md)
        if m:
            start = m.start()
            tail = md[m.end():]
            next_h2 = re.search(r"\n##\s+", tail)
            if next_h2:
                md = md[:start] + "\n" + tail[next_h2.start():].lstrip("\n")
            else:
                md = md[:start].rstrip() + "\n"
        return _INTERNAL_ID_RE.sub("a neighboring skill", md)

    pack = json.loads((skills_dir / skill_id / "unit_pack.json").read_text(encoding="utf-8"))
    parts = []
    if pack.get("title"):
        parts.append(f"### {pack.get('title')}")
    if pack.get("decision_variable"):
        parts.append(f"**Decision variable**: {pack['decision_variable']}")
    wf = pack.get("workflow") or []
    if wf:
        parts.append("**Workflow**:\n" + "\n".join(f"- {s}" for s in wf))
    out = "\n\n".join(parts)
    return _INTERNAL_ID_RE.sub("a neighboring skill", out)


def build_review_prompts(
    *,
    skills_dir: Path,
    inject_mode: str,
    story: str,
    question: str,
    options: dict[str, str],
    draft_answer: str,
    draft_reasoning: str = "",
    picked_skills: list[str] | None = None,
    lang: str = "en",
) -> tuple[str, str]:
    """Build (system_prompt, user_prompt) for the v5.1 chain-of-thought review."""
    l0_block = "\n\n---\n\n".join(
        _load_and_render(skills_dir, mid, inject_mode) for mid in L0_REVIEW_IDS
    )
    opts_text = "\n".join(f"{k}. {v}" for k, v in options.items() if v)
    picks_str = ", ".join(picked_skills) if picked_skills else ("(none)" if lang == "en" else "(无)")

    if lang == "zh":
        sys_p = (
            "你的任务是审查另一个模型(下称 solver)对一道社会认知多选题给出的初稿推理与答案。"
            "下面提供三条审查指南供你使用:\n\n"
            + l0_block + "\n\n"
            "请按以下三个维度审查 solver 的链路:\n"
            "1) 证据链:solver 引用的证据是否真的出现在题面文本中?是否清楚区分了"
            "原文证据、推断和常识补全?\n"
            "2) 备择解释:对相同证据,是否还有 solver 没有考虑、但更合理的另一种解释?\n"
            "3) 偏误检查:solver 的推理是否被读者视角带入、结果偏差、或道德直觉抢答带偏?\n\n"
            "如果 solver 的链路扎实,沿用其答案;如发现关键漏洞,修正答案。\n\n"
            "输出格式必须严格遵守:\n"
            "REASONING: <2-10 句话,说明你为什么接受或修正,具体引用上述三个维度中你使用的那些>\n"
            "ANSWER: <A 或 B 或 C 或 D>\n"
            "不要在这两行之外输出任何其他内容。"
        )
        user_p = (
            f"故事:\n{story}\n\n问题: {question}\n\n"
            f"选项:\n{opts_text}\n\n"
            f"Solver 选用的辅助技能: {picks_str}\n\n"
            f"Solver 的初稿推理:\n{draft_reasoning or '(未给出)'}\n\n"
            f"Solver 的初稿答案: {draft_answer or '(未给出)'}\n\n"
            "请按格式输出你的 REASONING 与最终 ANSWER:"
        )
    else:
        sys_p = (
            "Your task is to audit another model's (the solver's) draft reasoning "
            "and answer for a social-cognition multiple-choice question. "
            "Three audit guides follow for you to use:\n\n"
            + l0_block + "\n\n"
            "Audit the solver's chain along these three dimensions:\n"
            "1) Evidence chain: do the cues the solver cites actually appear in "
            "the story text? Does the solver separate textual evidence from "
            "inference and from commonsense filling-in?\n"
            "2) Alternative explanations: is there a more plausible reading of "
            "the same evidence that the solver did not consider?\n"
            "3) Bias check: is the solver's chain distorted by reader-perspective "
            "leakage, outcome bias, or a moral-intuition shortcut?\n\n"
            "If the solver's chain is sound, keep its answer. If a key flaw is "
            "found, correct the answer.\n\n"
            "Output format MUST be exactly two lines:\n"
            "REASONING: <2-10 sentences explaining why you accept or revise, "
            "explicitly citing which of the three dimensions you used>\n"
            "ANSWER: <A or B or C or D>\n"
            "Do not output anything else."
        )
        user_p = (
            f"Story:\n{story}\n\nQuestion: {question}\n\n"
            f"Options:\n{opts_text}\n\n"
            f"Solver's selected helper skills: {picks_str}\n\n"
            f"Solver's draft reasoning:\n{draft_reasoning or '(none)'}\n\n"
            f"Solver's draft answer: {draft_answer or '(none)'}\n\n"
            "Output REASONING and the FINAL ANSWER per the format:"
        )
    return sys_p, user_p


def _extract_answer(text: str) -> str:
    """Extract answer letter from REASONING+ANSWER structured output."""
    if not text:
        return ""
    m = ANSWER_LINE_RE.search(text)
    if m:
        return m.group(1)
    tail = text.strip().splitlines()[-1] if text.strip() else ""
    m2 = LETTER_RE.search(tail.upper())
    if m2:
        return m2.group(1)
    m3 = LETTER_RE.search(text.upper())
    return m3.group(1) if m3 else ""


def run_review(
    *,
    llm: LLMClient,
    skills_dir: Path,
    inject_mode: str,
    story: str,
    question: str,
    options: dict[str, str],
    draft_answer: str,
    draft_reasoning: str = "",
    picked_skills: list[str] | None = None,
    lang: str = "en",
    max_tokens: int = 2048,
) -> str:
    """Run L0 review and return the final answer letter."""
    sys_p, user_p = build_review_prompts(
        skills_dir=skills_dir,
        inject_mode=inject_mode,
        story=story,
        question=question,
        options=options,
        draft_answer=draft_answer,
        draft_reasoning=draft_reasoning,
        picked_skills=picked_skills,
        lang=lang,
    )
    try:
        resp = llm.chat(sys_p, user_p, max_tokens=max_tokens)
    except Exception as e:
        logger.warning("[L0Review] LLM call failed: %s, keeping draft", e)
        return draft_answer

    letter = _extract_answer(resp)
    if letter:
        return letter
    logger.warning("[L0Review] Could not parse answer from review response, keeping draft")
    return draft_answer
