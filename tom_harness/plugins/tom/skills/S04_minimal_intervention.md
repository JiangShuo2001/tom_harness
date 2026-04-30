---
skill_id: S04_minimal_intervention
name: Minimal-Intervention Ranking (Persuasion)
description: For persuasion/advice questions where multiple options are reasonable strategies, rank them by (1) directness to the stated concern, (2) minimality of structural change, (3) politeness. Pick the most direct, least-invasive option.
triggers:
  - "convince"
  - "persuade"
  - "说服"
  - "劝说"
  - "how does"
  - "如何"
---

## Problem this skill solves

Persuasion is the second-worst bucket (45%). Analysis of all 11 errors
reveals the same structural pattern: 3–4 options are all "plausible
persuasion strategies", but only one **directly addresses the stated
concern with minimal overhead**. Examples:

> Concern: "convince friends to respect cultural diversity"
> Options: A share travel experiences / B design cultural-difference questions
>          / C organize debate / D organize speech
> **Answer: A** — it directly exposes friends to diversity via first-person stories.
> Wrong pick: C (organize debate) — adds structure, doesn't address the concern as directly.

> Concern: "wants sister to stop borrowing clothes without asking"
> Options: A buy clothes together / B guilt-trip / C weekly exchange day / D ask first
> **Answer: D** — directly names the behavior + minimal fix (ask first).
> Wrong pick: C (exchange day) — adds structure unrelated to the concern.

The underlying principle is what economists call the **minimal effective
intervention**: when multiple interventions work, the one that's closest
to the problem surface and requires the least co-ordination is preferred.

## Workflow

1. **Extract the concern** from the story as a single predicate:
   `concern = "friends should respect cultural diversity"`.
2. **For each option**, score:
   - **Directness** [0..3]: how closely does the option address the
     exact concern? Direct address = 3, analogy = 2, indirect structural
     change = 1, orthogonal = 0.
   - **Minimality** [0..3]: how much extra structure must be added?
     No new structure = 3, light framing = 2, recurring event = 1,
     institutional = 0.
   - **Politeness** [0..2]: is the option non-confrontational?
     Light ask = 2, neutral = 1, accusatory = 0.
3. **Aggregate**: `total = 2 * direct + 2 * minimal + politeness`.
4. **Recommend** the highest-scoring option.

## Output shape

```json
{
  "concern": "sister borrows clothes without asking",
  "scores": [
    {"option": "A", "direct": 1, "minimal": 1, "polite": 2, "total": 6},
    {"option": "B", "direct": 2, "minimal": 2, "polite": 0, "total": 8},
    {"option": "C", "direct": 1, "minimal": 1, "polite": 2, "total": 6},
    {"option": "D", "direct": 3, "minimal": 3, "polite": 2, "total": 14}
  ],
  "recommendation": "D"
}
```

## Anti-patterns

- Do NOT prefer an option because it "sounds sophisticated" (debate,
  workshop, policy). Sophistication = more structure = lower minimality.
- Do NOT over-weight politeness; a direct ask (D) outranks a circuitous
  group activity (C) even if both are polite.
- Do NOT forget to re-read the concern literally; if the story says "stop
  X", a solution that doesn't mention X is failing directness.
