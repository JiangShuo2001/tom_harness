---
name: skill18
description: Use for OP-01 other-preference-driven action — discrepant desires, multiple desires, prediction of actions — by classifying the case into one of four patterns (solo-for-other / shared-hybrid / explicit-flip / pursuing) and applying the matching rule.
---

# OP-01 Other-Preference-Driven Action (4-Pattern Decision Tree)

## Use When

- An actor must act / decide *for or with another party* (host,
  invite, give a gift, plan a weekend, manage a request).
- The actor's own preference differs from the target's preference, OR
  the actor faces a constraint (limited money, mixed motives,
  disrupted plan).
- The question asks "where will X take Y?", "what will X give Y?",
  "how will the parent respond to the child's wish?", "what will X do
  given competing desires?".

## Do Not Use When

- The task is "what should X *say* to convince Y" — that is speech
  strategy. Use `skill13`.
- The task is "what does X do NEXT given a fresh disruption" with
  multiple time-ordered commitments. Use `skill21`.
- The task is about belief, emotion, or hidden meaning rather than
  action selection.

## Trigger Checklist

- Is there an actor and a target with potentially diverging
  preferences (or shared preferences in a couple / common-memory
  setting)?
- Is the asked output a CONCRETE ACTION (gift, venue, plan, response),
  not a SPEECH (how to convince)?
- If yes, use this skill.

## Workflow

1. Identify role, target, and activity type.
2. Classify the case into Pattern A / B / C / D using the marker
   phrases below.
3. Apply that pattern's rule to filter the options.
4. Apply secondary guardrails (constraints, atmosphere, postponement)
   if relevant.
5. Pick the surviving option.

## Detailed Procedure — 4-Pattern Decision Tree

```
STEP 1 — IDENTIFY ROLE & ACTIVITY TYPE
Who must act? (the actor)
Who is the target?
What kind of activity / gift / outing is being chosen?
Which of the following 4 patterns does it fit?

PATTERN A — SOLO-FOR-OTHER
  (gift just for them, trip just for them, invitation with no
   shared-memory marker)
  Marker phrases: "X invites Y to travel together", "X gives Y a
                  gift" (no mention of common memory / couple /
                  shared theme).
  → Use the TARGET's preference. Reject the actor's own preference.

PATTERN B — SHARED / "COMMON MEMORY" / "COUPLE" / TWO-WORLD MIX
  Marker phrases: "common memory", "couple's clothing", "shared",
                  "for both of them", "wants to do TOGETHER",
                  "celebrate their anniversary", or any explicit
                  instruction to combine BOTH characters' identities.
  → Look for a HYBRID option that COMBINES TERMS from both worlds.
    Examples:
      pianist × athlete   → "music-themed sportswear"
      graffiti × ballet   → "street DANCE flash mob"
      outdoor-photo × indoor-design → "photography exhibition"
      fashion × programmer → "fashion-brand windbreaker" (functional
                            but stylish, not pure plaid shirt)
      fitness × foodie    → "city exploration" (both can enjoy
                            walking, no pure dessert tasting against
                            fitness)
  → REJECT pure single-world options.

PATTERN C — EXPLICIT FLIP ("this time I want what I want")
  Marker phrases: "X always gives way to Y, but tonight X says he
                  wants to watch what HE wants", "X has had enough",
                  "X insists this time".
  → The actor's own preference WINS. Reject the usual "yield to
    other" option.

PATTERN D — "PURSUING / COURTING" + "let target decide"
  Marker phrases: "X wants to pursue Y", "X is courting Y", "X lets
                  Y decide".
  → The target picks something COMPATIBLE-TOGETHER (a public /
    shared version of their preference), NOT the most private /
    solitary version. Library > playing games at home alone.

STEP 2 — APPLY THE PATTERN'S RULE TO FILTER OPTIONS
  Pattern A → keep only options matching target's preference
  Pattern B → keep only options that touch BOTH characters' worlds
  Pattern C → keep only options matching the actor's preference
  Pattern D → keep only options compatible with two people doing it
              together OUTSIDE the home

STEP 3 — SECONDARY GUARDRAILS
  • When the actor faces a CONSTRAINT (cannot afford, cannot openly
    admit a value clash), prefer a SUBSTITUTE that respects both
    target wish AND constraint (cheaper similar toy > pure false
    promise).
  • When the actor wants to ease an awkward atmosphere, the action
    is usually JOIN / DE-ESCALATE, not avoid / wait / withdraw.
  • Reject "pure verbal promise" options that postpone the issue
    without addressing it.

GUARDRAIL: never just say "actor follows target's preference" without
first classifying which pattern (A / B / C / D) the case is. Pattern
B (common memory / couple / shared) is the most under-recognised one
and demands a HYBRID option, not a single-world one.
```

## Output Template

- `Task framing`: actor, target, activity type, and pattern (A / B /
  C / D).
- `Pattern evidence`: the marker phrases that selected the pattern.
- `Reasoning decision`: the option that survives the pattern's rule
  and any secondary guardrail.
- `Answer`: the chosen action.

## Failure Checks

- Do not skip the pattern classification.
- For Pattern B, do NOT pick a pure single-world option.
- For Pattern C, do NOT default to "yield to the other".
- For Pattern D, do NOT pick a private / solitary version of the
  target's hobby.
- Reject pure-promise options that postpone without addressing.

## Boundary Exit Rule

- If the task is to choose what to *say* to convince the other, route
  to `skill13`.
- If the task is "what does X do NEXT" with several time-ordered
  commitments competing for the next action, route to `skill21`.
- If no preference divergence or shared/common-memory cue exists, do
  not force this skill.

## Answer Discipline

- Name the pattern (A / B / C / D) explicitly in your reasoning before
  selecting the option.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
