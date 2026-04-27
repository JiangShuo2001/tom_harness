"""Skill Router — hardcoded skill injection for Plan A experiment.

Routes a ToM question to one of 12 skills (or NONE) via a single LLM call,
then returns the full skill prompt for injection into planner/executor context.

Skill content from skill_v2/skills.py; routing logic from skill_v2/llm_router.py.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from .llm import LLMClient

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Skill prompts (from skill_v2/skills.py)
# ─────────────────────────────────────────────────────────────────────────────

SKILL_S1_FAUX_PAS = """Before answering, perform PRAGMATIC FAUX-PAS DETECTION:

1. ENUMERATE every utterance / action in the story. For each one, identify
   (speaker, listener, content).
2. For EACH utterance, check three things:
   a. SPEAKER's intent: kind / neutral / strategic?
   b. SPEAKER's KNOWLEDGE GAP: does the speaker know about a listener-specific
      fact (preference, condition, recent event, identity) that would make
      this remark hurtful, embarrassing, or socially awkward? List that fact.
   c. LISTENER's likely reaction: would a reasonable listener feel
      hurt / awkward / patronised?
3. A FAUX PAS = (speaker is innocent / well-meaning) AND (speaker lacks
   knowledge of a listener-specific fact) AND (listener is uncomfortable).
   Politely-phrased remarks can still be faux pas.
4. FLATTERY check: a positive remark may be insincere when the speaker has
   a clear strategic incentive (negotiation, ingratiation, cover-up). Mark
   such utterances as strategically motivated, not literal compliments.

DECISION RULE:
• "Did anyone say something inappropriate?" → YES if any utterance passes
  the three-condition faux-pas check above (do NOT default to NO just
  because everyone is polite).
• Flattery question → identify the strategic goal, not the surface praise."""


SKILL_S2_SCALAR = """Before answering, perform SCALAR CALIBRATION using the
TIGHT ranges and HARD SUM-CONSTRAINT below.

STEP 1 — EXTRACT
• total N (e.g. "30 seats", "40 trees", "50 lunches").
• every explicit concrete sub-count from the story (e.g. "4 pears").
• every scalar quantifier the speaker uses, IN ORDER.

STEP 2 — TIGHT QUANTIFIER RANGES
  • "almost no X" / "hardly any" / "very few" → 1 to 3 items, NOT a percentage.
  • "a small part" / "a few" → 5–15% of N.
  • "some" → 15–30% of N.
  • "many" / "a lot" → 35–55% of N.
  • "most" / "the majority" → 60–85% of N. Lower bound is 60%, NOT 50%.
  • "almost all" / "nearly all" → 85–98% of N.

STEP 3 — HARD SUM CONSTRAINT
The named groups must SUM to N exactly.
  (a) Pin "almost no X" to 1 or 2.
  (b) Subtract every explicit sub-count and every "almost-no" pin from N.
  (c) Distribute the remainder preserving relative ranking.
  (d) If only "most" and "almost no", "most" ≈ N − explicit − 1.

STEP 4 — BEFORE vs AFTER COUNTING
  • BEFORE counting → quantifier range only; SUM-constraint unanchored.
  • AFTER counting → apply STEP 3 fully.

DECISION RULE: Pick the option satisfying BOTH quantifier-range AND SUM constraint.

GUARDRAIL 1: "almost no" → residual absorbed by LARGER groups.
GUARDRAIL 2: "most" with tight pin on "almost no" can reach 80%+ of N.
GUARDRAIL 3: Never pick option = N when another category has non-zero count."""


SKILL_S3_BELIEF_LEDGER = """Before answering, build a CHARACTER KNOWLEDGE LEDGER.

STEP 1 — TIMELINE
List every state change chronologically:
  t1: <event>  (witnesses: <character list>)

STEP 2 — PERCEPTION FILTER
For each character, mark which events they DIRECTLY witnessed vs MISSED.

STEP 3 — BELIEF = last state personally witnessed, NOT current world state.

STEP 4 — IDENTIFY QUESTION PERSPECTIVE
• "Where IS X?" → WORLD STATE
• "Where will C look?" / "What does C think?" → C's BELIEF
• "Does A know what B thinks?" → 2ND-ORDER: A had to see B's perception
• "Did C know that ...?" → did C witness the conveying event?

STEP 5 — DECISION
The correct answer is often the OLD / OUT-OF-DATE state held by a character
with limited view.

GUARDRAIL: never let "the story says X happened" leak into a character's
belief unless that character witnessed X."""


SKILL_S4_STRATEGIC = """Before answering, separate SURFACE from STRATEGY.

LAYER 1 — SURFACE: What is literally said / done? Quote it.

LAYER 2 — CONTEXT: List speaker's goals, incentives, social pressures, barriers.

LAYER 3 — STRATEGIC INTENT: Match to known pattern:
  • Lie: surface ≠ truth; intent = mislead, save face, gain edge.
  • Persuasion: surface = compliment / suggestion; intent = nudge past barrier.
  • Pretend: surface = fictional act; intent = play / symbolic communication.
  • Hint/Sarcasm: surface ≠ literal meaning; intent = indirect criticism / request.
  • Ambiguous: surface = neutral act; intent = signalling for hidden plan.

PERSUASION RULE: the BEST option DIRECTLY ADDRESSES Y's stated barrier,
not the one that praises X's own plan.

SPECIAL CASE — "What is the possible INTENTION behind X's behavior?"
Apply LITERAL-CUE ANCHORING:
  Step A — Locate story's explicit motive cue ("mistakes it for…", "knows X but…",
           "yelled rudely…"). Map to attribution family (charitable / aware / punitive / innocent).
  Step B — Do NOT default to the most NEUTRAL paraphrase.
  Step C — Prefer option using same VERB CLASS as the story.

DECISION RULE: Pick option matching STRATEGIC intent. Do not take statements at
face value when context shows incentive to misrepresent."""


SKILL_S5_EXPECTATION = """Before answering, perform EXPECTATION-DELTA ANALYSIS.

1. SURFACE EVENT: What visibly happened?
2. EXPECTED REACTION: What would be TYPICAL?
3. ACTUAL / ASKED REACTION: What reaction is the question pointing to?
4. HIDDEN CONTEXT SEARCH (if actual ≠ expected):
   (a) Additional constraint only this character faces
   (b) Competing second goal
   (c) External trigger known only to this character
   (d) Inside / outside asymmetry (SHOW vs FEEL)

5. DECISION: Pick option consistent with HIDDEN context.

SPECIAL CASE — "Real feeling" / "Hidden emotion":
  Step A — Identify SOURCE EVENT and valence:
    POSITIVE source (rewarded, good cards, secret advantage) → happy / excited
    NEGATIVE source (pain, excluded, disappointed) → sad / hurting
  Step B — Map valence to options. Do NOT add "secret-keeping anxiety" unless
    story explicitly shows struggle with the secret.

GUARDRAIL: the question asks precisely because the reaction is atypical."""


SKILL_S6_SPATIAL = """Before answering, perform SPATIAL MENTAL ROTATION.

STEP 1 — Build table grid from YOUR viewpoint: rows = near→far, cols = left→right.

STEP 2 — Apply EXACT axis mapping for target viewer:
  • OPPOSITE (180°): both axes reverse.
  • YOUR LEFT (90° CW): your COLS → target ROWS (same LR order).
  • YOUR RIGHT (90° CCW): your COLS → target ROWS (read RIGHT-TO-LEFT).
  • SAME SIDE (0°): identical mapping.

STEP 3 — Walk through worked example.
STEP 4 — Checklist: side identified? grid drawn? axis-rule applied? options re-checked?

DICE RULE: opposite faces sum to 7: 1↔6, 2↔5, 3↔4.

GUARDRAIL: RIGHT side is most confused — it is 90° rotation, not just LR flip."""


SKILL_S7_KNOWLEDGE_BOUNDARY = """Before answering, perform KNOWLEDGE-BOUNDARY FILTERING.

1. SCAN for sentences limiting character's world knowledge.
2. LIST concept domain the character DOES have access to.
3. Reader's pop-culture analogies are IRRELEVANT outside character's domain.
4. Re-frame behaviour using ONLY accessible concept set.

DECISION RULE: Pick option whose source domain is INSIDE character's knowledge boundary.

GUARDRAIL: the "obvious" real-world analogy is a TRAP when the story has
explicitly fenced off that knowledge."""


SKILL_S8_OTHER_PREFERENCE = """Before answering, perform OTHER-PARTY-FOCUSED ACTION INFERENCE.

STEP 1 — IDENTIFY ROLE & ACTIVITY TYPE (4 patterns):
  PATTERN A — SOLO-FOR-OTHER → use TARGET's preference.
  PATTERN B — SHARED / "COMMON MEMORY" / COUPLE → HYBRID option combining BOTH worlds.
  PATTERN C — EXPLICIT FLIP ("this time I want what I want") → ACTOR's preference wins.
  PATTERN D — PURSUING / COURTING + "let target decide" → compatible-together, non-private version.

STEP 2 — Apply the pattern's rule to filter options.

STEP 3 — SECONDARY GUARDRAILS:
  • Constraint → prefer SUBSTITUTE respecting both wish AND constraint.
  • Awkward atmosphere → JOIN / DE-ESCALATE, not avoid / withdraw.
  • Reject "pure verbal promise" options.

GUARDRAIL: classify pattern FIRST; Pattern B (common memory / couple) is most under-recognised."""


SKILL_S9_SENSORY_CHANNEL = """Before answering, perform SENSORY-CHANNEL FILTERING.

1. IDENTIFY perceiver's channels: blind=hearing+touch+smell; deaf=vision+touch+smell;
   blindfold=no vision; behind glass=vision only; distracted=no peripheral perception.
2. STRIP every detail the perceiver CANNOT access.
3. From REMAINING signals, reconstruct perceiver's conclusion.
4. If contrasting two perceivers, compute SEPARATELY.

DECISION RULE: Answer must be derivable from sensory data the perceiver actually has.

GUARDRAIL: deaf person won't think "whale song"; blind person won't think "chemistry lab"."""


SKILL_S10_AUDIENCE_CALIBRATION = """Before answering, calibrate to AUDIENCE EXPERTISE.

1. IDENTIFY listener's expertise level (expert / peer / novice).
2. EXPERT: Do NOT define the term. DO share SPECIFIC scene/observation/feeling
   using the term as shared vocabulary. Use vivid, sensory, personal language.
3. NOVICE: Define the term, give context, then share experience.

DECISION RULE: For expert audience → option that uses term as shared vocabulary
AND describes personal experience. Reject any option that defines term to expert.

GUARDRAIL: textbook definitions are WRONG when listener is domain expert."""


SKILL_S11_BELIEF_EMOTION = """Before answering, link BELIEF → EMOTION.

1. EXTRACT character's BELIEF state (what do they THINK the situation is?).
2. Emotion follows from BELIEF, not from objective reality or outsider's feeling.
3. EMOTION TAXONOMY:
   • Believes self favoured / safe → confident, peaceful
   • Believes self rejected / overlooked → irritated, hurt
   • Believes self unjustly accused → wronged, indignant
   • Believes outcome hopeless → depressed, anxious

SPECIAL CASE — Moral emotions ("what does X feel after possibly causing harm?"):
Run 5-CHECK FILTER — pick warmer/neutral option if ANY fires:
  (1) Age / cognitive limit → INDIFFERENT
  (2) Uncertainty markers ("might have") → CONFUSION
  (3) Self-justifying narrative ("did a good deed") → HAPPY / SATISFIED
  (4) External reassurance ("not your fault") → RELIEVED
  (5) Explicit indifference ("doesn't bother") → INDIFFERENT
Default to guilt/panic ONLY if all 5 fail.

DECISION RULE: Pick emotion matching character's CURRENT BELIEF.

GUARDRAIL: even if belief is factually WRONG, emotion reflects BELIEVED state."""


SKILL_S12_COMMITMENT_PRIORITY = """Before answering, perform COMMITMENT-PRIORITY ARBITRATION.

1. LIST competing draws:
   (a) PRIOR EXPLICIT COMMITMENT (promise, appointment, agreed plan)
   (b) ONGOING ACTIVITY (what they were doing before disruption)
   (c) NEW INVITATION (fresh option that just appeared)
   (d) BACKGROUND TASK (chores)

2. PRIORITY ORDER: (a) > (b) > (c) > (d)

3. FAILED-ACTION REPLACEMENT: if X became impossible, next action preserves
   SAME UNDERLYING GOAL. If reason was to wait for someone, keep waiting.

DECISION RULE: Next action satisfies PRIOR COMMITMENT, not newest alternative.

GUARDRAIL: do NOT over-weight freshest message / latest distraction."""


SKILLS: dict[str, str] = {
    "S1_FauxPas": SKILL_S1_FAUX_PAS,
    "S2_Scalar": SKILL_S2_SCALAR,
    "S3_BeliefLedger": SKILL_S3_BELIEF_LEDGER,
    "S4_Strategic": SKILL_S4_STRATEGIC,
    "S5_Expectation": SKILL_S5_EXPECTATION,
    "S6_Spatial": SKILL_S6_SPATIAL,
    "S7_KnowledgeBound": SKILL_S7_KNOWLEDGE_BOUNDARY,
    "S8_OtherPreference": SKILL_S8_OTHER_PREFERENCE,
    "S9_SensoryChannel": SKILL_S9_SENSORY_CHANNEL,
    "S10_AudienceCalib": SKILL_S10_AUDIENCE_CALIBRATION,
    "S11_BeliefEmotion": SKILL_S11_BELIEF_EMOTION,
    "S12_CommitmentPrio": SKILL_S12_COMMITMENT_PRIORITY,
}

# ─────────────────────────────────────────────────────────────────────────────
# Router catalog (short trigger-pattern descriptions for routing LLM call)
# ─────────────────────────────────────────────────────────────────────────────

ROUTER_CATALOG: dict[str, str] = {
    "S1_FauxPas":
        "Social interaction where someone may say something inappropriate, "
        "embarrassing, or insincerely flattering due to lack of awareness of "
        "the listener's situation/preference. Typical question: 'did anyone "
        "say something inappropriate?', 'what does this compliment really mean?'.",

    "S2_Scalar":
        "Story uses scalar quantifiers (most / some / a few / hardly any) "
        "together with an explicit total N and one or two concrete sub-counts. "
        "Typical question asks how many of a given category there are.",

    "S3_BeliefLedger":
        "Characters perceive or miss key events at different times (someone "
        "leaves the room, object is moved / swapped, container has misleading "
        "label). Typical question: 'where will X look for Y?', 'what does X "
        "think is in the box?', 'does X know that Z happened?', or nested "
        "'what does A think B believes?'.",

    "S4_Strategic":
        "There is a hidden strategic intent behind a polite or literal surface "
        "(lies, persuasion, hints, sarcasm, pretend play, or ambiguous "
        "behavior with an implied plan). Typical question: 'what does X "
        "really mean?', 'how should X persuade Y?', 'what is X's real intent?'.",

    "S5_Expectation":
        "A character's reaction seems mismatched with the visible event, OR "
        "asks for the REAL / HIDDEN / SUPPRESSED feeling of someone who is "
        "consciously masking / hiding / suppressing an emotion. "
        "Typical question: 'what is X's real feeling?', 'why does X react "
        "this way despite the surface event?'. "
        "Distinguish from S11: S5 fires when story explicitly mentions "
        "hiding / masking / suppressing; S11 fires when no hiding is "
        "involved and emotion just follows from the believed situation.",

    "S6_Spatial":
        "Story involves spatial layout, dice/cube faces, multiple viewers at "
        "different positions, or what someone sees/draws from a particular "
        "vantage point.",

    "S7_KnowledgeBound":
        "Story explicitly states a character has limited world knowledge "
        "(e.g. never seen animals, raised on a robot-only planet). Question "
        "asks about pretend play / imitation / inference under that limit.",

    "S8_OtherPreference":
        "An actor must act / decide for another party (host, invite, give a "
        "gift, manage a request) and the actor's own preference differs from "
        "the target's preference, or the actor faces a constraint.",

    "S9_SensoryChannel":
        "A perceiver has only a SUBSET of senses available (blind, deaf, "
        "blindfolded, behind glass) and the question asks what THAT perceiver "
        "concludes about the scene.",

    "S10_AudienceCalib":
        "The speaker is sharing an experience involving a technical term and "
        "the LISTENER's expertise level on that term matters (expert vs "
        "novice). Question asks how the speaker should phrase the term.",

    "S11_BeliefEmotion":
        "Asks about a character's emotion that follows from the character's "
        "BELIEVED situation rather than objective reality. No hiding / "
        "masking involved. Two sub-cases: (a) general belief→emotion; "
        "(b) MORAL EMOTION items (resist intuitive guilt when actor is "
        "young / uncertain / self-justifying / reassured / indifferent).",

    "S12_CommitmentPrio":
        "Several competing draws on the next action — a recent verbal "
        "promise, an awaited appointment, an ongoing activity, and a fresh "
        "invitation. Question asks what the character will do NEXT.",

    "NONE":
        "No strategy above clearly applies; the question is straightforward "
        "or doesn't match any of the twelve patterns.",
}

VALID_IDS = list(ROUTER_CATALOG.keys())

# ─────────────────────────────────────────────────────────────────────────────
# Router prompt template
# ─────────────────────────────────────────────────────────────────────────────

ROUTER_INSTRUCTION = """You are a skill router for Theory-of-Mind multiple-choice questions.
Read the story, question, and options below, then pick the ONE strategy that
best matches the case. Pick at most one.

Available strategies:

{catalog}

Decision rules:
1. First identify the ASKED OUTPUT — what the question literally wants.
2. Name the DECISION VARIABLE that determines the answer.
3. Match to the strategy whose triggering pattern best fits the decision variable.
4. Check the nearest neighboring strategy before committing — if two seem plausible,
   prefer the one keyed to the explicit question form.
5. If no strategy clearly applies, choose NONE.

Reply with EXACTLY this format on a single line, with no additional text:
Skill: <ID>

where <ID> is one of: {ids}.
"""

_SKILL_RE = re.compile(r"\b(S\d{1,2}_[A-Za-z]+|NONE)\b")


def _format_catalog() -> str:
    return "\n".join(f"- {sid}: {desc}" for sid, desc in ROUTER_CATALOG.items())


def _build_router_prompt(question: str, options: dict[str, str]) -> str:
    opts = "\n".join(f"{k}. {v}" for k, v in options.items() if v)
    head = ROUTER_INSTRUCTION.format(
        catalog=_format_catalog(),
        ids=", ".join(VALID_IDS),
    )
    return (
        f"{head}\n"
        f"=== QUESTION ===\n{question}\n\n"
        f"=== OPTIONS ===\n{opts}\n\n"
        f"Now output your choice:\n"
    )


def _parse_router_choice(response: str) -> str | None:
    if not response:
        return None
    m = re.search(r"[Ss]kill\s*[:：]\s*([A-Za-z0-9_]+)", response)
    if m:
        cand = m.group(1)
        if cand in VALID_IDS:
            return cand
    matches = _SKILL_RE.findall(response)
    for tok in reversed(matches):
        if tok in VALID_IDS:
            return tok
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SkillRouter:
    """Routes a ToM question to one of 12 skills via a single LLM call."""

    llm: LLMClient

    def route(self, question: str, options: dict[str, str]) -> str | None:
        """Return skill_id (e.g. 'S2_Scalar') or None if NONE / parse failure."""
        prompt = _build_router_prompt(question, options)
        try:
            resp = self.llm.chat(
                "You are a skill router. Output only the skill ID.",
                prompt,
                max_tokens=64,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("[SkillRouter] LLM call failed: %s", e)
            return None
        choice = _parse_router_choice(resp)
        if choice == "NONE":
            return None
        logger.info("[SkillRouter] Routed to: %s (raw: %s)", choice, resp.strip()[:80])
        return choice

    @staticmethod
    def get_skill_prompt(skill_id: str) -> str | None:
        """Return the full skill prompt text, or None if invalid."""
        return SKILLS.get(skill_id)
