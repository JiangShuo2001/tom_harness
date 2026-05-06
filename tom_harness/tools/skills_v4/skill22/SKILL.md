---
name: skill22
description: Use for ME-01 belief-driven moral emotion — "what does X feel after their action possibly caused harm?" — by running the 5-CHECK ANTI-GUILT FILTER and resisting the intuitive guilt / panic answer when ANY check fires.
---

# ME-01 Belief-Driven Moral Emotion (5-Check Anti-Guilt Filter)

## Use When

- The question asks what the character feels after their action
  possibly caused harm to another character.
- The "easy" guilt / panic option is present in the choices.
- The story contains at least one of the 5 anti-guilt cues (young
  child / "MIGHT have" / self-justifying good-deed framing / external
  reassurance / explicit indifference).

Also use for general belief-driven emotion items where the character's
emotion follows from their BELIEVED situation rather than objective
reality (Yuki thinks she is safe; Roy thinks he is ignored).

## Do Not Use When

- The task asks which emotion fits with no anti-guilt cue and no
  belief-vs-reality split. Use `skill8`.
- The task asks WHY the surprising emotion occurs. Use `skill9`.
- The task is about truth status of a statement. Use `skill14`.

## Trigger Checklist

- Is there a "moral emotion" / "what does X feel after they possibly
  caused harm" framing?
- Or is the character's emotion clearly tied to their BELIEF (which
  may be partial or wrong) rather than to objective reality?
- Is there at least one anti-guilt cue in the story?
- If yes, use this skill.

## Workflow

1. Extract the character's belief state explicitly.
2. Map the belief to the appropriate emotion using the BELIEF →
   EMOTION taxonomy.
3. For moral-emotion items, run the **5-CHECK ANTI-GUILT FILTER**
   below. If ANY check fires, pick the warmer / neutral option.
4. Default to guilt / panic ONLY if all 5 checks fail AND the story
   explicitly shows the actor recognising their own causal role in a
   serious unambiguous harm.

## Detailed Procedure — Belief → Emotion + 5-Check Filter

```
STEP 1 — EXTRACT the character's BELIEF state explicitly:
  • What does the character think the situation is?
  • Is their belief possibly WRONG (based on partial info, biased
    assumption, self-justification)?
  E.g. Roy thinks he is "ignored" by the school. Yuki just got an
  invitation email so she thinks she is safe.

STEP 2 — The character's emotion follows from their BELIEF, not from
objective reality and not from what an outside observer (the reader)
would feel.

STEP 3 — EMOTION TAXONOMY for belief-driven cases:
  • Believes self is favoured / safe / chosen        → confident,
                                                       peaceful
  • Believes self is rejected / overlooked           → irritated, hurt
  • Believes self is unjustly accused / undervalued  → wronged,
                                                       indignant
  • Believes outcome is hopeless                     → depressed,
                                                       anxious

  Distinguish "wronged" (specific perceived unfairness) from
  "irritated" (general dissatisfaction).

──────────────────────────────────────────────────────────────────
SPECIAL CASE — "Moral emotions" / "What does X feel after their
                action possibly caused harm?"
──────────────────────────────────────────────────────────────────
The intuitive "guilty / panicked / anxious" answer is OFTEN WRONG in
these items. Before defaulting to guilt, run THIS 5-CHECK FILTER and
pick the WARMER / MORE NEUTRAL emotion if ANY check fires.

  CHECK 1 — AGE / COGNITIVE LIMIT
    Story says actor is a young child / 2-year-old / "doesn't
    understand the value" / unable to grasp the consequence?
    → Actor feels INDIFFERENT / continues their game. Young children
      do not experience adult-style moral guilt.

  CHECK 2 — UNCERTAINTY MARKERS
    Phrases like "REALIZES HE MIGHT have made a mistake", "is not
    sure if", "thinks he POSSIBLY did" → felt emotion is CONFUSION /
    UNCERTAINTY, not nervousness or guilt.

  CHECK 3 — SELF-JUSTIFYING NARRATIVE
    Actor's GOAL was to "do a good deed" (fed an animal, donated,
    helped) and the harm is INDIRECT or AMBIGUOUS (e.g. zookeeper
    said rabbits "ate too much", not "got sick from your carrots
    specifically")?
    → Actor maintains "I did good" → feels HAPPY / PROUD /
      SATISFIED. Actor does not spontaneously connect their action
      to the harm unless the story explicitly forces that
      connection.

  CHECK 4 — EXTERNAL REASSURANCE
    A third party tells the actor "it's not your fault" / "X did it"
    / explicitly absolves them?
    → Actor feels RELIEVED / SATISFIED, not guilty.

  CHECK 5 — EXPLICIT FACE-VALUE INDIFFERENCE
    Story literally says "too lazy to return" / "doesn't bother" /
    "doesn't think this is her responsibility"?
    → Take it LITERALLY → INDIFFERENT.

DECISION RULE for moral-emotion questions:
  • Run all 5 checks. If ANY fires → pick the warmer / neutral
    option (indifferent / happy / confused / satisfied) that matches
    the firing check.
  • ONLY default to guilt / panic if ALL 5 checks fail AND the story
    explicitly shows the actor recognising their own causal role in
    a serious unambiguous harm.

──────────────────────────────────────────────────────────────────
DECISION RULE (general belief-driven cases)
──────────────────────────────────────────────────────────────────
Pick the emotion that matches the character's CURRENT BELIEF, not
what an outsider would feel knowing all facts.

GUARDRAIL: even if the character's belief is FACTUALLY WRONG (Yuki
may still get laid off; Xiao Qiang's gift hurt the rabbits), the
character's emotion right now reflects the BELIEVED state, not future
or external reality. The "morally correct" feeling an outsider would
impose is USUALLY NOT the right answer.

WORKED EXAMPLE
Story: Yuki and Haru work in the same building. The company suddenly
notified us of layoffs today. Yuki just received a project invitation
email from her superiors and thinks she really needs it; Haru heard
that his group is a key target for layoffs.

Q: What is Yuki's mood at this moment?
  A. peace of mind ✅   B. flustered   C. pleasure   D. disdain

Without S11 / ME-01, a model may read "needs it" as anxiety and pick B
(flustered). With ME-01: Yuki's BELIEF is "I'm wanted by the
company → I'm safe from the layoff" — that maps to the
"favoured / safe" cell of the emotion taxonomy → A (peace of mind).
The fact that her belief might be factually wrong is irrelevant to
her current felt emotion.
```

## Output Template

- `Task framing`: character, action, possible-harm setup OR belief
  state.
- `Filter checks`: which of the 5 anti-guilt checks fire (if any).
- `Reasoning decision`: warmer / neutral option (if any check fires)
  or default guilt only when all 5 fail and explicit causal
  recognition exists.
- `Answer`: the emotion that matches the firing check or the
  belief state.

## Failure Checks

- Do not pick guilt / panic without running all 5 checks.
- Do not impose the reader's morally-correct outsider feeling on the
  character.
- Use the "wronged / irritated / depressed / peaceful" taxonomy for
  general belief-driven cases.

## Boundary Exit Rule

- If no anti-guilt cue and no belief-vs-reality split is present,
  route to `skill8`.
- If the question explicitly asks WHY a surprising emotion occurs,
  route to `skill9`.
- If the question is about truth status of a statement, route to
  `skill14`.

## Answer Discipline

- Quote the firing anti-guilt check (or the character's belief state)
  in your reasoning before selecting the option.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
