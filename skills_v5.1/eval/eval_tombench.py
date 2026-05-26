"""
ToMBench evaluation runner for skills_v5.

## Pipeline

  Stage 1 (route prep) : micro-01 (task routing) is injected as the router's
                         system prompt. Always on.
  Stage 2 (route)      : One of 5 modes (see below) picks 0+ skills.
  Stage 3 (solve)      : Picked skills are injected as the solver's system
                         prompt. The solver returns a draft answer letter.
  Stage 4 (review)     : If --review-mode on, micro-02 + micro-03 + micro-04
                         are injected together along with the draft answer,
                         and the LLM is asked to confirm or revise. The final
                         letter is the one the reviewer outputs.

  When --review-mode is on, BOTH the draft and the final answer are recorded,
  so the lift from review can be measured without a second run.

## Routing modes (--route-mode)

  baseline      : Stage 2 picks no skill. Stages 1 and 4 still run if review
                  is on. 1 (or 2 if review on) LLM calls.
  macro_only    : LLM picks 0+ macros from 20.
  micro_only    : LLM picks 0+ non-L0 micros from the 52 (micro-05..56).
                  L0 micros (01..04) are never candidates — they have their
                  own stages.
  hierarchical  : Step 2a picks 0+ macros. Step 2b picks 0+ micros. The
                  step 2b candidate pool depends on step 2a:
                    - if step 2a picked 1+ macros: pool = UNION of their
                      expandable_micro_ids (always L0-free);
                    - if step 2a picked NONE: pool = all 52 non-L0 micros
                      (degenerates to micro_only-style selection).
  flat_all      : LLM sees all 72 candidates (20 macros + 52 non-L0 micros).

Every routing step explicitly allows the LLM to answer "none" (meaning the
question does not need any skill from the library).

## Injection mode (--inject-mode)

  Controls how ALL skill content (L0 stages 1 & 4 + the routed skills in
  stage 3) is rendered.

  full   : Selected skills are injected as full SKILL.md text.
  light  : Selected skills are injected as a compact slice (title +
           decision_variable + direct_route_rule [macro] + workflow +
           special_case.worked_example + boundary_exit_rule). References,
           notes, validation_seed, hard_boundary, etc. are dropped.

## Combinations

  4 routing modes (excluding baseline) × 2 injection modes = 8 experimental
  conditions. Plus baseline = 9 runs to fully compare.

## Per-item output

  Each row in results.jsonl has: idx, task, ability, lang, gold, pred,
  correct, picked_skills (list), latency_s, error.

## API

  OpenAI-compatible client.chat.completions.create with the same env vars as
  the rest of skills_v5:
    SKILL_V5_API_KEY / OPENAI_API_KEY  (required)
    SKILL_V5_BASE_URL                  (default: https://api.openai.com/v1)
    SKILL_V5_MODEL                     (default: gpt-4o-mini)

## Usage

  python eval_tombench.py --route-mode baseline      --lang en --limit 100
  python eval_tombench.py --route-mode macro_only    --inject-mode light --lang en --workers 8
  python eval_tombench.py --route-mode hierarchical  --inject-mode full  --lang zh --workers 8

Outputs land in eval/runs/<auto_run_id>/.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

try:
    from openai import OpenAI
except ImportError:
    print("Install: pip install openai", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parent.parent  # skills_v5/
SKILLS_DIR = ROOT / "skills"
DATA_DIR = ROOT / "data"
EVAL_DIR = ROOT / "eval"
RUNS_DIR = EVAL_DIR / "runs"

DEFAULT_MODEL = os.environ.get("SKILL_V5_MODEL", "gpt-4o-mini")
DEFAULT_BASE_URL = os.environ.get(
    "SKILL_V5_BASE_URL", os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
)


# --------------------------------------------------------------------------
# Skill loading
# --------------------------------------------------------------------------
_SKILL_MD_CACHE: dict[str, str] = {}
_SKILL_PACK_CACHE: dict[str, dict] = {}


def load_skill_md(skill_id: str) -> str:
    if skill_id not in _SKILL_MD_CACHE:
        _SKILL_MD_CACHE[skill_id] = (SKILLS_DIR / skill_id / "SKILL.md").read_text(encoding="utf-8")
    return _SKILL_MD_CACHE[skill_id]


def load_skill_pack(skill_id: str) -> dict:
    if skill_id not in _SKILL_PACK_CACHE:
        _SKILL_PACK_CACHE[skill_id] = json.loads(
            (SKILLS_DIR / skill_id / "unit_pack.json").read_text(encoding="utf-8")
        )
    return _SKILL_PACK_CACHE[skill_id]


def list_macros() -> list[str]:
    return sorted(d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and d.name.startswith("macro-"))


def list_all_micros() -> list[str]:
    return sorted(d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and d.name.startswith("micro-"))


L0_MICROS = ["micro-01", "micro-02", "micro-03", "micro-04"]
L0_ROUTE = "micro-01"                                  # injected at stage 1
L0_REVIEW = ["micro-02", "micro-03", "micro-04"]       # injected at stage 4


def list_non_l0_micros() -> list[str]:
    """All micros except L0 (meta-control). 52 candidates."""
    return [m for m in list_all_micros() if m not in set(L0_MICROS)]


# --------------------------------------------------------------------------
# Skill summary / rendering
# --------------------------------------------------------------------------
def router_summary(skill_id: str) -> str:
    """Compact one-block summary used in router prompts. ~5-8 lines."""
    pack = load_skill_pack(skill_id)
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
    """Replace any `micro-XX` / `macro-XX` mention with a generic label so
    internal naming does not leak when content is shown as a guide rather
    than as a labelled candidate."""
    return _INTERNAL_ID_RE.sub("a neighboring skill", text)


def render_skill_full(skill_id: str, strip_id: bool = False) -> str:
    """Full SKILL.md text. If strip_id:
      - drop the YAML frontmatter (id / level / layer / family),
      - drop the `## Boundary Exit Rule` section,
      - replace any remaining `micro-XX`/`macro-XX` with `a neighboring skill`.
    """
    md = load_skill_md(skill_id)
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


def render_skill_light(skill_id: str, strip_id: bool = False) -> str:
    """Lightweight: only the highest-value action-oriented fields. If
    strip_id, omit the leading `### [skill-id] Title` line, drop the
    boundary_exits section (which references other skill ids), and scrub
    any other internal ids that appear in retained fields."""
    pack = load_skill_pack(skill_id)
    parts = []
    if not strip_id:
        parts.append(f"### [{skill_id}] {pack.get('title', '')}")
    elif pack.get("title"):
        parts.append(f"### {pack.get('title')}")
    if pack.get("decision_variable"):
        parts.append(f"**Decision variable**: {pack['decision_variable']}")
    if pack.get("direct_route_rule"):  # macros only
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


def render_skill(skill_id: str, inject_mode: str, strip_id: bool = False) -> str:
    if inject_mode == "full":
        return render_skill_full(skill_id, strip_id=strip_id)
    if inject_mode == "light":
        return render_skill_light(skill_id, strip_id=strip_id)
    raise ValueError(f"unknown inject_mode={inject_mode}")


# --------------------------------------------------------------------------
# LLM client
# --------------------------------------------------------------------------
class LLMClient:
    def __init__(self, model: str, base_url: str, api_key: str,
                 timeout: int = 120, temperature: float = 0.0,
                 max_attempts: int = 3, retry_backoff_cap: int = 8):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.temperature = temperature
        self.max_attempts = max(1, int(max_attempts))
        self.retry_backoff_cap = max(0, int(retry_backoff_cap))
        self.client = OpenAI(api_key=api_key, base_url=self.base_url, timeout=timeout)

    def chat(self, system: str, user: str, max_tokens: int) -> str:
        for attempt in range(1, self.max_attempts + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": system},
                              {"role": "user", "content": user}],
                    temperature=self.temperature,
                    max_completion_tokens=max_tokens,
                )
                msg = resp.choices[0].message
                content = msg.content
                if isinstance(content, list):
                    content = "\n".join(
                        (p.text if hasattr(p, "text") else p.get("text", "")) for p in content
                    )
                return (content or "").strip()
            except Exception:
                if attempt >= self.max_attempts:
                    raise
                if self.retry_backoff_cap > 0:
                    time.sleep(min(2 ** attempt, self.retry_backoff_cap))
        return ""


# --------------------------------------------------------------------------
# Prompt builders — router
# --------------------------------------------------------------------------
def format_options(options: dict) -> str:
    return "\n".join(f"{k}. {v}" for k, v in sorted(options.items()))


def _scene_block(item: dict) -> str:
    lang = item["lang"]
    if lang == "zh":
        return f"故事:\n{item['story']}\n\n问题:{item['question']}"
    return f"Story:\n{item['story']}\n\nQuestion: {item['question']}"


SINGLE_RULES_EN = (
    "Output ONLY one id like macro-XX, OR the literal word `none` if no skill "
    "in the list fits this scene. No explanation, no quotes."
)
SINGLE_RULES_ZH = (
    "只输出一个 id (形如 macro-XX),或者字面量 `none`(如果列表里没有匹配)。"
    "不要解释,不要引号。"
)
MULTI_RULES_EN = (
    "Output a JSON array of ids you want to use, e.g. [\"micro-12\", \"micro-23\"]. "
    "If none of the skills apply, output [\"none\"]. No explanation."
)
MULTI_RULES_ZH = (
    "输出一个 JSON 数组,内容是你想使用的 id,例如 [\"micro-12\", \"micro-23\"]。"
    "如果都不适用,输出 [\"none\"]。不要解释。"
)


def build_router_prompt(item: dict, candidates: list[str], multi: bool,
                        header: str, inject_mode: str) -> tuple[str, str]:
    """Generic router prompt. micro-01 (task routing) is injected as the
    system prompt prefix (rendered per --inject-mode), so the router sees the
    L0 routing playbook in addition to the candidate summaries."""
    lang = item["lang"]
    blocks = "\n\n".join(router_summary(c) for c in candidates)
    rules = (MULTI_RULES_ZH if multi else SINGLE_RULES_ZH) if lang == "zh" \
            else (MULTI_RULES_EN if multi else SINGLE_RULES_EN)
    l0_block = render_skill(L0_ROUTE, inject_mode, strip_id=True)
    if lang == "zh":
        sys_p = (
            "你是一个社会认知技能路由器。先阅读下面的任务路由指南,"
            "然后从候选技能中选择最合适的。\n\n"
            "## 任务路由指南\n\n" + l0_block + "\n\n"
            "## 路由规则\n" + rules
        )
        user = f"{_scene_block(item)}\n\n候选 {header}:\n{blocks}\n\n你的选择:"
    else:
        sys_p = (
            "You are a social-cognition skill router. First read the task-"
            "routing playbook below, then select the best candidate skill(s).\n\n"
            "## Task Routing Playbook\n\n" + l0_block + "\n\n"
            "## Routing rules\n" + rules
        )
        user = f"{_scene_block(item)}\n\nCandidate {header}:\n{blocks}\n\nYour choice:"
    return sys_p, user


# --------------------------------------------------------------------------
# Prompt builders — solver
# --------------------------------------------------------------------------
def build_solver_prompt(item: dict, picked: list[str], inject_mode: str,
                        with_reasoning: bool) -> tuple[str, str]:
    """If with_reasoning is False, the solver is told to output ONLY a letter.
    If True, the solver must output a structured response of REASONING + ANSWER
    so a downstream reviewer can audit the chain rather than just the letter."""
    lang = item["lang"]
    if picked:
        rendered = "\n\n---\n\n".join(render_skill(s, inject_mode) for s in picked)
        if lang == "zh":
            base = (
                "你正在使用一套社会心智 skill 库求解题目。下面是被选中的 skill:\n\n"
                + rendered + "\n\n严格按照所选 skill 的 workflow / boundary 推理。"
            )
        else:
            base = (
                "You are solving a social-cognition problem with a skill library. "
                "Selected skills:\n\n" + rendered +
                "\n\nReason strictly using the selected skill's workflow / boundary."
            )
    else:
        if lang == "zh":
            base = "你是一个谨慎的选择题解题器。"
        else:
            base = "You are a careful multiple-choice solver."

    if with_reasoning:
        if lang == "zh":
            sys_p = base + (
                "\n\n输出格式必须严格遵守:\n"
                "REASONING: <2-10 句话,说明你应用所选 skill 推出该答案的关键证据与推断>\n"
                "ANSWER: <A 或 B 或 C 或 D>\n"
                "不要在这两行之外输出任何其他内容。"
            )
            user_tail = "请按格式输出 REASONING 与 ANSWER:"
        else:
            sys_p = base + (
                "\n\nOutput format MUST be exactly two lines:\n"
                "REASONING: <2-10 sentences citing the textual evidence and the "
                "step in the selected skill that yields the answer>\n"
                "ANSWER: <A or B or C or D>\n"
                "Do not output anything else."
            )
            user_tail = "Output REASONING and ANSWER per the format:"
    else:
        if lang == "zh":
            sys_p = base + "\n\n最后只输出一个字母 (A/B/C/D),不要解释。"
            user_tail = "请只输出一个字母:"
        else:
            sys_p = base + "\n\nEnd with ONLY one letter (A/B/C/D). No explanation."
            user_tail = "Output only one letter:"

    if lang == "zh":
        user = f"{_scene_block(item)}\n\n选项:\n{format_options(item['options'])}\n\n{user_tail}"
    else:
        user = f"{_scene_block(item)}\n\nOptions:\n{format_options(item['options'])}\n\n{user_tail}"
    return sys_p, user


def build_review_prompt(item: dict, picked: list[str], draft_reasoning: str,
                        draft_letter: str, inject_mode: str
                        ) -> tuple[str, str]:
    """Stage 4 review. The reviewer sees:
      - micro-02/03/04 (the L0 audit playbook),
      - which skills the solver chose,
      - the solver's full reasoning,
      - the solver's draft letter.

    The reviewer audits the solver's chain (not the question from scratch)
    and outputs REASONING (its critique) + ANSWER (final letter)."""
    lang = item["lang"]
    l0_block = "\n\n---\n\n".join(render_skill(m, inject_mode, strip_id=True) for m in L0_REVIEW)
    picks_str = ", ".join(picked) if picked else ("(none)" if lang == "en" else "(无)")
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
        user = (
            f"{_scene_block(item)}\n\n"
            f"选项:\n{format_options(item['options'])}\n\n"
            f"Solver 选用的辅助技能: {picks_str}\n\n"
            f"Solver 的初稿推理:\n{draft_reasoning or '(未给出)'}\n\n"
            f"Solver 的初稿答案: {draft_letter or '(未给出)'}\n\n"
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
        user = (
            f"{_scene_block(item)}\n\n"
            f"Options:\n{format_options(item['options'])}\n\n"
            f"Solver's selected helper skills: {picks_str}\n\n"
            f"Solver's draft reasoning:\n{draft_reasoning or '(none)'}\n\n"
            f"Solver's draft answer: {draft_letter or '(none)'}\n\n"
            "Output REASONING and the FINAL ANSWER per the format:"
        )
    return sys_p, user


# --------------------------------------------------------------------------
# Output parsing
# --------------------------------------------------------------------------
LETTER_RE = re.compile(r"\b([A-D])\b")
ID_RE = re.compile(r"(?:macro|micro)-\d{2}")
ANSWER_LINE_RE = re.compile(r"(?im)^\s*ANSWER\s*[:：]\s*([A-D])\b")
REASONING_LINE_RE = re.compile(r"(?ims)^\s*REASONING\s*[:：]\s*(.+?)(?=^\s*ANSWER\s*[:：]|\Z)")


def extract_letter(text: str) -> str:
    if not text:
        return ""
    tail = text.strip().splitlines()[-1] if text.strip() else ""
    m = LETTER_RE.search(tail.upper())
    if m:
        return m.group(1)
    m = LETTER_RE.search(text.upper())
    return m.group(1) if m else ""


def extract_reasoning_and_letter(text: str) -> tuple[str, str]:
    """Parse a structured `REASONING: ...\\nANSWER: X` reply.

    Falls back to: (full text without an ANSWER line, last A-D letter found)
    if the strict format is not followed."""
    if not text:
        return "", ""
    rm = ANSWER_LINE_RE.search(text)
    am = REASONING_LINE_RE.search(text)
    letter = rm.group(1) if rm else extract_letter(text)
    reasoning = am.group(1).strip() if am else (
        # No explicit REASONING marker: use the body up to the answer line, or
        # the whole text if no answer line either.
        text[:rm.start()].strip() if rm else text.strip()
    )
    return reasoning, letter


def parse_single_id(text: str, valid: set[str]) -> str:
    """Returns the picked id or '' if none/invalid."""
    if not text:
        return ""
    if re.search(r"\bnone\b", text, re.IGNORECASE):
        return ""
    m = ID_RE.search(text)
    if not m:
        return ""
    pid = m.group(0)
    return pid if pid in valid else ""


def parse_multi_ids(text: str, valid: set[str]) -> list[str]:
    """Returns the list of picked ids, or [] if none/empty."""
    if not text:
        return []
    if re.search(r"\bnone\b", text, re.IGNORECASE):
        return []
    ids = ID_RE.findall(text)
    out = []
    seen = set()
    for pid in ids:
        if pid in valid and pid not in seen:
            out.append(pid)
            seen.add(pid)
    return out


# --------------------------------------------------------------------------
# Routing strategies
# --------------------------------------------------------------------------
@dataclass
class TokenBudget:
    router: int = 128
    solver: int = 2048
    reviewer: int = 2048


def route_macro_only(item: dict, client: LLMClient, inject_mode: str,
                     tb: TokenBudget) -> list[str]:
    macros = list_macros()
    sys_p, user = build_router_prompt(item, macros, multi=True, header="macros", inject_mode=inject_mode)
    out = client.chat(sys_p, user, max_tokens=tb.router)
    return parse_multi_ids(out, set(macros))


def route_micro_only(item: dict, client: LLMClient, inject_mode: str,
                     tb: TokenBudget) -> list[str]:
    """Candidates are the 52 non-L0 micros."""
    micros = list_non_l0_micros()
    sys_p, user = build_router_prompt(item, micros, multi=True, header="micros", inject_mode=inject_mode)
    out = client.chat(sys_p, user, max_tokens=tb.router)
    return parse_multi_ids(out, set(micros))


def route_hierarchical(item: dict, client: LLMClient, inject_mode: str,
                       tb: TokenBudget) -> list[str]:
    """Step 1: pick 0+ macros from 20.
    Step 2: pick 0+ micros from a candidate pool that depends on step 1.
      - If step 1 picked 1+ macros: pool = UNION of their expandable_micro_ids
        (defensively filtered to exclude L0).
      - If step 1 picked NONE: pool = all 52 non-L0 micros (degenerates to
        micro_only-style selection so the LLM still gets a chance to pick
        diagnostic micros even when no scene-prototype macro fits)."""
    macros = list_macros()
    sys_p, user = build_router_prompt(item, macros, multi=True, header="macros", inject_mode=inject_mode)
    out = client.chat(sys_p, user, max_tokens=tb.router)
    macro_picks = parse_multi_ids(out, set(macros))
    if macro_picks:
        expandable: list[str] = []
        seen: set[str] = set()
        for m in macro_picks:
            for mid in (load_skill_pack(m).get("expandable_micro_ids") or []):
                if mid not in seen and mid not in set(L0_MICROS):
                    seen.add(mid)
                    expandable.append(mid)
        if not expandable:
            return list(macro_picks)
        step2_pool = expandable
        step2_header = "micros to expand the selected macro(s)"
    else:
        # No macro fit: fall back to letting the LLM pick from all non-L0 micros.
        step2_pool = list_non_l0_micros()
        step2_header = "micros (no macro was selected — pick directly from non-L0 micros)"

    sys_p2, user2 = build_router_prompt(
        item, step2_pool, multi=True,
        header=step2_header,
        inject_mode=inject_mode,
    )
    out2 = client.chat(sys_p2, user2, max_tokens=tb.router)
    micro_picks = parse_multi_ids(out2, set(step2_pool))
    return list(macro_picks) + micro_picks


def route_flat_all(item: dict, client: LLMClient, inject_mode: str,
                   tb: TokenBudget) -> list[str]:
    """Candidates are 20 macros + 52 non-L0 micros = 72."""
    all_ids = list_macros() + list_non_l0_micros()
    sys_p, user = build_router_prompt(item, all_ids, multi=True, header="skills (macros and micros)", inject_mode=inject_mode)
    out = client.chat(sys_p, user, max_tokens=tb.router)
    return parse_multi_ids(out, set(all_ids))


ROUTERS = {
    "macro_only": route_macro_only,
    "micro_only": route_micro_only,
    "hierarchical": route_hierarchical,
    "flat_all": route_flat_all,
}


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------
@dataclass
class ItemResult:
    idx: int
    task: str
    ability: str
    lang: str
    gold: str
    draft_pred: str               # answer after stage 3 (no review)
    pred: str                     # final answer (= draft_pred if review off)
    correct: bool                 # final correctness
    draft_correct: bool           # correctness of the draft
    review_changed: bool          # whether review changed the letter
    picked_skills: list[str] = field(default_factory=list)
    draft_reasoning: str = ""     # only populated when review_mode=on
    review_reasoning: str = ""    # only populated when review_mode=on
    latency_s: float = 0.0
    error: str = ""


def load_items(path: Path, limit: int | None) -> list[dict]:
    items = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            rec["_id"] = i
            items.append(rec)
            if limit and len(items) >= limit:
                break
    return items


def load_done_ids(path: Path) -> set[int]:
    if not path.exists():
        return set()
    done = set()
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line).get("idx"))
            except json.JSONDecodeError:
                continue
    return done


def solve_item(item: dict, route_mode: str, inject_mode: str,
               review_mode: str, client: LLMClient,
               tb: TokenBudget) -> ItemResult:
    t0 = time.time()
    picked: list[str] = []
    draft_letter = ""
    final_letter = ""
    draft_reasoning = ""
    review_reasoning = ""
    review_on = (review_mode == "on")
    try:
        # Stage 2: route (skip for baseline)
        if route_mode == "baseline":
            picked = []
        else:
            picked = ROUTERS[route_mode](item, client, inject_mode, tb)
        # Stage 3: solve -> draft. Ask for reasoning ONLY when reviewer needs it.
        sys_p, user = build_solver_prompt(item, picked, inject_mode,
                                          with_reasoning=review_on)
        draft_out = client.chat(sys_p, user, max_tokens=tb.solver)
        if review_on:
            draft_reasoning, draft_letter = extract_reasoning_and_letter(draft_out)
        else:
            draft_letter = extract_letter(draft_out)
        # Stage 4: review (optional)
        if review_on:
            rs, ru = build_review_prompt(
                item, picked, draft_reasoning, draft_letter, inject_mode,
            )
            rev_out = client.chat(rs, ru, max_tokens=tb.reviewer)
            review_reasoning, rev_letter = extract_reasoning_and_letter(rev_out)
            final_letter = rev_letter or draft_letter
        else:
            final_letter = draft_letter
        return ItemResult(
            idx=item["_id"], task=item["task"], ability=item.get("ability", ""),
            lang=item["lang"], gold=item["gold"],
            draft_pred=draft_letter, pred=final_letter,
            correct=(final_letter == item["gold"]),
            draft_correct=(draft_letter == item["gold"]),
            review_changed=(review_on and draft_letter != final_letter),
            picked_skills=picked,
            draft_reasoning=draft_reasoning, review_reasoning=review_reasoning,
            latency_s=time.time() - t0,
        )
    except Exception as exc:
        return ItemResult(
            idx=item["_id"], task=item["task"], ability=item.get("ability", ""),
            lang=item["lang"], gold=item["gold"],
            draft_pred=draft_letter, pred=final_letter,
            correct=False, draft_correct=(draft_letter == item["gold"]),
            review_changed=False, picked_skills=picked,
            draft_reasoning=draft_reasoning, review_reasoning=review_reasoning,
            latency_s=time.time() - t0, error=f"{type(exc).__name__}: {exc}",
        )


def run(args: argparse.Namespace) -> None:
    api_key = (
        os.environ.get("SKILL_V5_API_KEY") or os.environ.get("OPENAI_API_KEY") or args.api_key
    )
    if not api_key:
        sys.exit("Missing API key. Set SKILL_V5_API_KEY or OPENAI_API_KEY.")
    client = LLMClient(
        model=args.model, base_url=args.base_url, api_key=api_key,
        timeout=args.timeout, temperature=args.temperature,
        max_attempts=args.max_attempts, retry_backoff_cap=args.retry_backoff_cap,
    )
    tb = TokenBudget(
        router=args.router_max_tokens,
        solver=args.solver_max_tokens,
        reviewer=args.reviewer_max_tokens,
    )

    data_path = DATA_DIR / f"ToMBench_{args.lang}.jsonl"
    items = load_items(data_path, args.limit)
    print(f"Loaded {len(items)} items from {data_path.name}")

    if args.route_mode == "baseline":
        run_id = args.run_id or (
            f"baseline_{args.lang}_review-{args.review_mode}_"
            f"{args.model.replace('/', '_')}_{int(time.time())}"
        )
    else:
        run_id = args.run_id or (
            f"{args.route_mode}_{args.inject_mode}_review-{args.review_mode}_"
            f"{args.lang}_{args.model.replace('/', '_')}_{int(time.time())}"
        )
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    results_path = run_dir / "results.jsonl"
    done_ids = load_done_ids(results_path) if args.resume else set()
    if done_ids:
        print(f"Resuming: {len(done_ids)} items already done, skipping.")
    items_todo = [it for it in items if it["_id"] not in done_ids]

    # Initial counters reflect prior run if resuming
    file_lock = threading.Lock()
    n_done = len(done_ids)
    n_correct = 0
    if results_path.exists() and args.resume:
        for line in results_path.read_text(encoding="utf-8-sig").splitlines():
            try:
                if json.loads(line).get("correct"):
                    n_correct += 1
            except json.JSONDecodeError:
                pass

    config = {
        "run_id": run_id,
        "route_mode": args.route_mode,
        "inject_mode": args.inject_mode if args.route_mode != "baseline" else "n/a",
        "review_mode": args.review_mode,
        "lang": args.lang,
        "model": args.model,
        "limit": args.limit,
        "workers": args.workers,
        "temperature": args.temperature,
        "timeout": args.timeout,
        "max_attempts": args.max_attempts,
        "retry_backoff_cap": args.retry_backoff_cap,
        "router_max_tokens": args.router_max_tokens,
        "solver_max_tokens": args.solver_max_tokens,
        "reviewer_max_tokens": args.reviewer_max_tokens,
    }
    (run_dir / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    def write_result(r: ItemResult):
        nonlocal n_done, n_correct
        row = asdict(r)
        if args.review_mode != "on":
            # Drop review-only / draft-vs-final columns when review is off,
            # so the file matches the simpler schema:
            #   idx, task, ability, lang, gold, pred, correct,
            #   picked_skills, latency_s, error
            for k in ("draft_pred", "draft_correct", "review_changed",
                      "draft_reasoning", "review_reasoning"):
                row.pop(k, None)
            ordered_keys = ["idx", "task", "ability", "lang", "gold",
                            "pred", "correct", "picked_skills",
                            "latency_s", "error"]
            row = {k: row[k] for k in ordered_keys if k in row}
        with file_lock:
            with open(results_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            n_done += 1
            if r.correct:
                n_correct += 1
            if n_done % 25 == 0 or n_done == len(items):
                acc = n_correct / max(1, n_done)
                print(f"[{n_done}/{len(items)}] acc={acc:.3f}")

    print(f"Running route={args.route_mode} inject={args.inject_mode} "
          f"model={args.model} workers={args.workers}")
    print(f"Output: {results_path}")
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [
            ex.submit(solve_item, it, args.route_mode, args.inject_mode,
                      args.review_mode, client, tb)
            for it in items_todo
        ]
        for fut in as_completed(futures):
            try:
                write_result(fut.result())
            except Exception as exc:
                print(f"  worker error: {exc}", file=sys.stderr)

    summarize(run_dir)


def summarize(run_dir: Path) -> None:
    results_path = run_dir / "results.jsonl"
    if not results_path.exists():
        return
    rows = []
    bad_rows = []
    for line_no, line in enumerate(results_path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            bad_rows.append((line_no, exc))
    if not rows:
        print("No rows to summarize.")
        return
    if bad_rows:
        print(f"Skipped {len(bad_rows)} malformed result row(s) while summarizing.")

    by_task: dict[str, list[bool]] = {}
    by_ability: dict[str, list[bool]] = {}
    by_first_pick: dict[str, list[bool]] = {}
    by_n_picked: dict[int, list[bool]] = {}
    pick_freq: dict[str, int] = {}
    n_none = 0
    n_err = 0
    has_draft_metrics = any("draft_correct" in r for r in rows)
    draft_correct = 0
    draft_total = 0
    review_changed = 0
    review_flips_correct = 0       # draft wrong, final right
    review_flips_wrong = 0         # draft right, final wrong
    for r in rows:
        by_task.setdefault(r["task"], []).append(r["correct"])
        if r.get("ability"):
            by_ability.setdefault(r["ability"], []).append(r["correct"])
        picks = r.get("picked_skills") or []
        first = picks[0] if picks else "<none>"
        by_first_pick.setdefault(first, []).append(r["correct"])
        by_n_picked.setdefault(len(picks), []).append(r["correct"])
        for p in picks:
            pick_freq[p] = pick_freq.get(p, 0) + 1
        if not picks:
            n_none += 1
        if r.get("error"):
            n_err += 1
        if "draft_correct" in r:
            draft_total += 1
            if r.get("draft_correct"):
                draft_correct += 1
        if r.get("review_changed"):
            review_changed += 1
            if not r.get("draft_correct") and r.get("correct"):
                review_flips_correct += 1
            elif r.get("draft_correct") and not r.get("correct"):
                review_flips_wrong += 1

    overall_correct = sum(1 for r in rows if r["correct"])
    summary = {
        "n": len(rows),
        "overall_acc": overall_correct / len(rows),
        "review_changed": review_changed,
        "review_flips_correct": review_flips_correct,   # draft wrong -> final right
        "review_flips_wrong": review_flips_wrong,       # draft right -> final wrong
        "errors": n_err,
        "malformed_rows": len(bad_rows),
        "n_routed_to_none": n_none,
        "by_task": {k: {"n": len(v), "acc": sum(v) / len(v)} for k, v in sorted(by_task.items())},
        "by_ability": {k: {"n": len(v), "acc": sum(v) / len(v)} for k, v in sorted(by_ability.items())},
        "by_first_pick": {k: {"n": len(v), "acc": sum(v) / len(v)} for k, v in sorted(by_first_pick.items())},
        "by_n_picked": {str(k): {"n": len(v), "acc": sum(v) / len(v)} for k, v in sorted(by_n_picked.items())},
        "pick_frequency": dict(sorted(pick_freq.items(), key=lambda kv: -kv[1])),
    }
    if has_draft_metrics:
        summary["draft_acc"] = draft_correct / max(1, draft_total)
    out = run_dir / "summary.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")
    overall_parts = [
        f"n={summary['n']}",
        f"final_acc={summary['overall_acc']:.4f}",
    ]
    if has_draft_metrics:
        overall_parts.append(f"draft_acc={summary['draft_acc']:.4f}")
    overall_parts.extend([
        f"review_changed={review_changed}",
        f"flips(wrong->right)={review_flips_correct}",
        f"flips(right->wrong)={review_flips_wrong}",
        f"errors={summary['errors']}",
        f"routed_to_none={summary['n_routed_to_none']}",
    ])
    print("Overall: " + " ".join(overall_parts))
    print("\nBy task:")
    for k, v in summary["by_task"].items():
        print(f"  {k:40s} n={v['n']:4d}  acc={v['acc']:.3f}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--route-mode",
        choices=["baseline", "macro_only", "micro_only", "hierarchical", "flat_all"],
        default="hierarchical",
    )
    p.add_argument("--inject-mode", choices=["full", "light"], default="light")
    p.add_argument("--review-mode", choices=["on", "off"], default="on",
                   help="If 'on', run an L0 review stage after the draft "
                        "answer; both draft and final letters are recorded.")
    p.add_argument("--lang", choices=["en", "zh"], default="en")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--api-key", default="")
    p.add_argument("--limit", type=int, default=0, help="0 = all 2860")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--timeout", type=int, default=120,
                   help="Per-request timeout in seconds (passed to the OpenAI client).")
    p.add_argument("--max-attempts", type=int, default=3,
                   help="Maximum LLM attempts per call (1 = no retry).")
    p.add_argument("--retry-backoff-cap", type=int, default=8,
                   help="Cap (seconds) for exponential backoff between retries. "
                        "Set 0 to retry without sleeping.")
    p.add_argument("--router-max-tokens", type=int, default=128,
                   help="max_completion_tokens for each router call.")
    p.add_argument("--solver-max-tokens", type=int, default=2048,
                   help="max_completion_tokens for the solver. Default 2048 "
                        "leaves headroom for the reasoning block when "
                        "--review-mode on; you can lower it to ~256 for "
                        "letter-only solving with --review-mode off.")
    p.add_argument("--reviewer-max-tokens", type=int, default=2048,
                   help="max_completion_tokens for the L0 reviewer (which "
                        "also outputs reasoning + letter).")
    p.add_argument("--run-id", default="")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--summarize-only", action="store_true",
                   help="Re-summarize an existing run dir given by --run-id.")
    args = p.parse_args()
    if args.limit == 0:
        args.limit = None

    if args.summarize_only:
        if not args.run_id:
            sys.exit("--summarize-only requires --run-id")
        summarize(RUNS_DIR / args.run_id)
        return
    run(args)


if __name__ == "__main__":
    main()
