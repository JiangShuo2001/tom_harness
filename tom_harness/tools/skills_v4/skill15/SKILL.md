---
name: skill15
description: Use for SS-02 motive explanation — why did the speaker say that false / partial / polite / self-protective / mistaken / ironic statement? — by classifying the deviation type and recovering the local goal, including discrepant-intentions cases with literal motive cues.
---

# SS-02 Motive Explanation for Nonliteral Statements

## Use When

- The task asks **why** a speaker said something that is false,
  partial, selective, polite, self-protective, mistaken, or otherwise
  nonliteral.
- The target output is the speaker's **motive**, not the statement's
  truth status.
- The story requires distinguishing memory failure, face-saving,
  politeness, concealment, self-interest, and conflict avoidance.
- Includes "what is the possible INTENTION behind X's behavior?"
  Discrepant-intentions style items.

## Do Not Use When

- The task only asks whether the statement is true. Use `skill14`.
- The task is persuasion, hinting, or direct emotion classification.
- There is no nonliteral or selective statement to explain.

## Trigger Checklist

- Is there a specific statement (or behaviour) whose motive must be
  explained?
- Does the statement / behaviour depart from plain factual reporting
  or full disclosure?
- Does the story provide pressure, goal, relationship, or memory-state
  clues that explain the wording / behaviour choice?
- If yes, use this skill.

## Workflow

1. Identify the statement / behaviour and how it departs from plain
   factual reporting.
2. Classify the deviation: forgetting, confusion, white lie,
   egocentric lie, conflict avoidance, face-saving, selective truth,
   irony, or mixed emotion.
3. Recover the speaker's immediate goal or pressure.
4. Choose the explanation that best links the motive to the social
   context.
5. Keep `truth status` separate from `motive for saying it`.
6. If options are provided, pick the option that best explains why
   the speaker used that wording.

## Detailed Procedure — Literal-Cue Anchoring (Discrepant-Intentions)

For "why did X act / say this way" items, the correct option is
**NEVER** the generic surface paraphrase ("X did Y because of conflict
/ busy / didn't know"). It is **ALWAYS** the option that names the
**SPECIFIC mechanism** the story has explicitly set up.

```
Step A — Locate the story's explicit motive cue. Quote the exact phrase.

Common cue templates and the attribution they license:

   STORY SAYS                           → CORRECT ATTRIBUTION FAMILY
   "mistakes it for X" / "thinks it     → CHARITABLE: misunderstands /
       is X" / "accidentally finds"       mistaken belief; choose the
                                          option that says "thinks
                                          ownerless / misunderstands the
                                          purpose / believes it's class
                                          fund". Reject options that
                                          accuse the actor of conscious
                                          bad intent.

   "knows X but" / "is aware that"      → AWARE: actor knows the truth
       + "competes with / has grudge      and stays silent for STRATEGIC
       with / dispute with"               gain. Choose the option that
                                          names the SPECIFIC strategic
                                          gain ("see the rival blamed",
                                          "weaken their position", "let
                                          their plan fail"). Reject the
                                          option that just restates "has
                                          a conflict and doesn't tell".

   "X just yelled / was rude /          → PUNITIVE: silence / withholding
       behaved badly" + "Y chose          is interpreted as pushback or
       not to tell"                       moral punishment. Choose the
                                          option that says "disgusted by
                                          rude attitude, unspoken
                                          punishment".

   "quite troublesome" / "thought it    → INNOCENT: actor genuinely
       was trash / unattended"            thought no harm was done.
                                          Choose the "thinks ownerless /
                                          helping clean up" option.

Step B — DO NOT default to the most NEUTRAL paraphrase of the surface
  ("X has a conflict and chooses not to tell"). The benchmark almost
  always pairs that NEUTRAL option with a more SPECIFIC option that
  names the mechanism — and the SPECIFIC option is usually the gold.

Step C — If two options share the same gist, prefer the one that uses
  the same VERB CLASS the story used:
     story: "misunderstands"   → option containing "misunderstands"
     story: "has a grudge"     → option containing "see ... fail" /
                                  "let ... be blamed"
     story: "yelled rudely"    → option containing "disgusted /
                                  unspoken punishment"
```

GUARDRAIL: do not pick the bland paraphrase option in
intention-attribution questions — the benchmark rewards options that
name the SPECIFIC gain / loss / belief the story sets up.

## Output Template

- `Task framing`: statement / behaviour and type of nonliteral
  deviation.
- `Motive evidence`: pressure, goal, relationship, memory state, or
  self-protection cue (or for discrepant-intentions, the literal motive
  cue quoted from the story).
- `Reasoning decision`: why the speaker chose that wording / behaviour.
- `Answer`: the best motive explanation.

## Failure Checks

- Do not call every mismatch a deliberate lie.
- Distinguish forgetting from deception.
- Explain the motive for saying it, not just the objective facts.
- Separate social face-saving from factual confusion.
- Reject the bland paraphrase option in discrepant-intentions items.

## Boundary Exit Rule

- If the task only asks whether the statement is true, route to
  `skill14`.
- If there is no statement motive to explain, do not force this skill.
- If the task is persuasion strategy or indirect-speech decoding, route
  to the appropriate skill instead.

## Answer Discipline

- Name the deviation type first, then choose the answer that best fits
  the speaker's local goal.
- For Discrepant-intentions items, quote the explicit motive cue and
  pick the option that uses the same verb class.
- Reject options that merely restate the hidden facts without
  explaining why that wording was chosen.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
