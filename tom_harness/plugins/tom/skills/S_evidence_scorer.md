---
skill_id: S_evidence_scorer
name: Evidence Scorer (Structured)
description: Split the story into numbered sentences, have the LLM score each option against them on a rubric, aggregate in Python. Replaces S01 for most inferential questions.
triggers:
  - "why"
  - "feel"
  - "reason"
  - "为什么"
  - "情绪"
---

## Why this exists

S01 (declarative) gives the LLM a lecture about "ground your answer in
textual evidence". That rarely changes behavior. This procedural version
*forces* the LLM to:
  1. See sentences numbered `[s0]..[sN]`.
  2. Emit a strict JSON rubric per option.
  3. Cite supporting sentence ids.

Python then picks the highest-scoring option deterministically. The LLM
cannot "reason around" the evidence — it must produce a numeric score.

## Output

```json
{
  "n_sentences": 7,
  "scores": {"A": 2, "B": 0, "C": 1, "D": -1},
  "support": {"A": ["s2", "s5"], "C": ["s3"]},
  "recommendation": "A"
}
```

## When to use

Any inferential question where multiple options look plausible and the
discriminator is "which one the text actually supports". Especially
useful for Ambiguous Story, Unexpected Outcome, and Strange Story.
