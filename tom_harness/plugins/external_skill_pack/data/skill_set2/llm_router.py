"""
LLM-based skill router for the v2 skill set.

Given a case (story + question + options), ask an LLM to choose ONE of the
seven skills (or NONE). No task_type metadata required at inference time.

Public API:
  ROUTER_CATALOG          — short id → 1-line description (used in router prompt)
  build_router_prompt()   — assemble the classification prompt
  parse_router_choice()   — extract the chosen skill id from the LLM response
  route(model, item)      — convenience wrapper, returns skill_id or None
"""
import re
from skills import SKILLS

# ─────────────────────────────────────────────────────────────────────────────
# Skill descriptions for the router (kept short; the FULL skill prompt is only
# injected after routing, not during routing).
# ─────────────────────────────────────────────────────────────────────────────
ROUTER_CATALOG = {
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
        "consciously masking / hiding / suppressing an emotion (good cards "
        "they hide, stomachache they hide, joke they don't get and hide). "
        "Typical question: 'what is X's real feeling?', 'what does X truly "
        "feel?', 'why does X react this way despite the surface event?'. "
        "Distinguish from S11: S5 fires when story explicitly mentions "
        "hiding / masking / suppressing; S11 fires when no hiding is "
        "involved and emotion just follows from the believed situation.",

    "S6_Spatial":
        "Story involves spatial layout, dice/cube faces, multiple viewers at "
        "different positions, or what someone sees/draws from a particular "
        "vantage point. Typical question: 'which face does X see?', 'what does "
        "the picture look like from X's side?'.",

    "S7_KnowledgeBound":
        "Story explicitly states a character has limited world knowledge "
        "(e.g. never seen animals, raised on a robot-only planet, no contact "
        "with X). Question asks about pretend play / imitation / inference "
        "under that knowledge limit.",

    "S8_OtherPreference":
        "An actor must act / decide for another party (host, invite, give a "
        "gift, manage a request) and the actor's own preference differs from "
        "the target's preference, or the actor faces a constraint (limited "
        "money, mixed motives). Typical question: 'where will X take Y for "
        "the weekend?', 'how will the parent respond to the child's wish?', "
        "'what will X do given competing desires?'.",

    "S9_SensoryChannel":
        "A perceiver has only a SUBSET of senses available (blind, deaf, "
        "blindfolded, behind glass) and the question asks what THAT perceiver "
        "concludes about the scene. The narrator describes multi-modal cues "
        "but the perceiver only experiences part. Typical question: 'what "
        "does the deaf student think you are doing?', 'what does the person "
        "relying on sound conclude?'.",

    "S10_AudienceCalib":
        "The speaker is sharing an experience involving a technical term and "
        "the LISTENER's expertise level on that term matters (expert vs "
        "novice). Question asks how the speaker should phrase / mention the "
        "term to that specific listener.",

    "S11_BeliefEmotion":
        "Asks about a character's emotion (NOT a hidden / real / suppressed "
        "feeling) that follows from the character's BELIEVED situation "
        "rather than objective reality. Often the belief is partial / "
        "wrong / self-justifying. Two sub-cases: (a) general belief→emotion: "
        "'what is X's mood after receiving this news?' where X believes "
        "themselves favoured / rejected / hopeless / wronged. (b) MORAL "
        "EMOTION items: 'what does X feel after their action possibly "
        "caused harm?' — the question tests whether the model resists the "
        "intuitive guilt answer when the actor is a young child / "
        "uncertain / self-justifying / externally reassured / explicitly "
        "indifferent.",

    "S12_CommitmentPrio":
        "Several competing draws on the next action — a recent verbal "
        "promise, an awaited appointment, an ongoing activity, and a fresh "
        "invitation. Question asks what the character will do NEXT. Often "
        "the original activity got disrupted (laptop dies, weather changes).",

    "NONE":
        "No strategy above clearly applies; the question is straightforward "
        "or doesn't match any of the seven patterns.",
}

VALID_IDS = list(ROUTER_CATALOG.keys())  # S1..S7 + NONE

# ─────────────────────────────────────────────────────────────────────────────
# Router prompt
# ─────────────────────────────────────────────────────────────────────────────
ROUTER_INSTRUCTION = """You are a skill router for Theory-of-Mind multiple-choice questions.
Read the story, question, and options below, then pick the ONE strategy that
best matches the case. Pick at most one.

Available strategies:

{catalog}

Decision rules:
- Look at WHAT THE QUESTION IS ASKING and WHAT KIND OF REASONING is required.
- Match to the strategy whose triggering pattern best fits.
- If no strategy clearly applies, choose NONE.

Reply with EXACTLY this format on a single line, with no additional text:
Skill: <ID>

where <ID> is one of: {ids}.
"""


def _format_catalog() -> str:
    return "\n".join(f"- {sid}: {desc}" for sid, desc in ROUTER_CATALOG.items())


def build_router_prompt(story: str, question: str,
                         options, labels) -> str:
    opts = "\n".join(f"{l}. {o}" for l, o in zip(labels, options))
    head = ROUTER_INSTRUCTION.format(
        catalog=_format_catalog(),
        ids=", ".join(VALID_IDS),
    )
    return (
        f"{head}\n"
        f"=== STORY ===\n{story}\n\n"
        f"=== QUESTION ===\n{question}\n\n"
        f"=== OPTIONS ===\n{opts}\n\n"
        f"Now output your choice:\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Parsing
# ─────────────────────────────────────────────────────────────────────────────
_SKILL_RE = re.compile(
    r"\b(S[1-7]_[A-Za-z]+|NONE)\b"
)


def parse_router_choice(response: str):
    """Return chosen skill_id (one of VALID_IDS) or None on failure."""
    if not response:
        return None
    # Prefer a 'Skill: X' line if present
    m = re.search(r"[Ss]kill\s*[:：]\s*([A-Za-z0-9_]+)", response)
    if m:
        cand = m.group(1)
        if cand in VALID_IDS:
            return cand
    # Otherwise, take the LAST matching token in the response
    matches = _SKILL_RE.findall(response)
    for tok in reversed(matches):
        if tok in VALID_IDS:
            return tok
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Convenience wrapper
# ─────────────────────────────────────────────────────────────────────────────
def route(model, item, max_tokens: int = 64):
    """Return (skill_id_or_None, raw_response). NONE → returns 'NONE'."""
    prompt = build_router_prompt(
        item["story"], item["question"], item["options"], item["labels"]
    )
    resp = model.interact(prompt, max_tokens=max_tokens)
    choice = parse_router_choice(resp)
    return choice, resp


def get_skill_prompt(skill_id: str):
    """Return the full skill prompt or None if skill_id is NONE / invalid."""
    if skill_id is None or skill_id == "NONE":
        return None
    return SKILLS.get(skill_id)
