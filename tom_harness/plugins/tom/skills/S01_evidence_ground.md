---
skill_id: S01_evidence_ground
name: Evidence-Grounded Option Scoring
description: For any inferential question, score each option by the amount of direct textual evidence in the story. Demote options that require adding narrative details not in the text.
triggers:
  - "why"
  - "为什么"
  - "feels"
  - "情绪"
  - "心情"
---

## Problem this skill solves

Model tends to fabricate plausible backstory ("narrative hallucination"):
it picks options that fit *a* coherent story rather than *the* story given.
The most dramatic regressions on Ambiguous Story / Unexpected Outcome are
of this form.

## Workflow (deterministic)

1. **Split** the story into numbered sentences `s1, s2, ...`.
2. **For each option** compute an evidence score:
   - +2 if some sentence **explicitly states** the option's claim
   - +1 if some sentence **implies** the option's claim via a single causal step
   -  0 if the option requires **adding** a fact not in the story
   - −1 if some sentence **contradicts** the option
3. **Report** per-option: `{option, score, supporting_sentence_ids, missing_facts}`.
4. **Recommend**: the option with the highest score; break ties by
   shortest chain of inference (Occam's razor applied to narrative).

## Output shape

```json
{
  "evidence_table": [
    {"option": "A", "score": 2, "support": ["s3"], "missing_facts": []},
    {"option": "B", "score": 0, "support": [], "missing_facts": ["X was jealous"]},
    ...
  ],
  "recommendation": "A",
  "confidence": 0.8
}
```

## Anti-patterns (do NOT do these)

- Do NOT pick the option that *makes the best story* — pick the one with
  the most textual support.
- Do NOT fabricate supporting sentences — if you cannot cite a sentence
  id, the score for that option is 0 or −1.
- Do NOT let emotional vividness influence the score; evidence is about
  whether the text says it, not how compelling it sounds.
