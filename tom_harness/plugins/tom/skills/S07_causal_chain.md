---
skill_id: S07_causal_chain
name: Causal-Chain Tracker (Intention / Strange Story)
description: Build an explicit causal chain from the story's events to the queried behavior. Prefer the option whose causal path matches what the story actually provides, even when multiple options are individually plausible.
triggers:
  - "why"
  - "为什么"
  - "what makes"
  - "reason"
  - "intention"
---

## Problem this skill solves

Strange Story / Intention-explanation questions often have 2–3 options
that each describe *a* plausible reason; the discriminator is which
causal chain the story actually lays down. Example:

> "Li Lei plays football. After the game, he puts the ball in the locker
>  room, but he thinks he brings the ball home. In the evening dad asks
>  where the ball is. Li Lei says 'In my bag'."
>
> Options: A deliberately lies / B really thinks it's in his bag /
>          C wants to test dad / D forgets he put it in the locker room
>
> **Answer: D (forgets)**. Model picks B (really thinks) — both are valid
> mental states ("thinks in bag" ⊇ "forgot it's in locker"), but D is the
> narrower, causally-precise answer.

The story explicitly says "thinks he brings it home" — i.e., forgot the
locker. That's the causal *step* that produced the belief "in my bag".
Skipping the causal chain leads to accepting the vaguer B.

## Workflow

1. **Enumerate story events** as a DAG of `event_id → {cause: [...], effect: [...]}`.
2. **Identify the queried behavior**: the action/statement the question
   asks "why" about.
3. **Back-trace the chain**: from the behavior, follow cause edges
   backward, building `[cause_n ← ... ← cause_1 ← behavior]`.
4. **Match options** against the chain:
   - An option that names the **most proximal cause** (e.g. "forgets
     where he put it") scores +2.
   - An option that names a **non-causal state** that the proximal
     cause happens to entail (e.g. "thinks it's in the bag" — a
     *consequence* of forgetting) scores +1.
   - An option that **adds** a motive not in the chain (e.g. "tests
     dad") scores 0 or −1.

## Output shape

```json
{
  "queried_behavior": "Li Lei says ball is in bag",
  "causal_chain": [
    "put ball in locker (true fact)",
    "thinks he brought it home (false belief)",
    "infers ball is in bag (logical consequence)",
    "tells dad ball is in bag"
  ],
  "proximal_cause": "forgot location",
  "option_scores": {"A": -1, "B": 1, "C": 0, "D": 2},
  "recommendation": "D"
}
```

## Anti-patterns

- Do NOT prefer the most "psychologically interesting" motive (lie,
  test). Prefer what the story causally constructed.
- Do NOT accept a mental-state option (like "really thinks it's in bag")
  when the story supplies a mechanism (forgetting) for that mental state.
  Name the mechanism.
