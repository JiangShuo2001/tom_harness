---
skill_id: S06_implicit_knowledge
name: Implicit Knowledge Inference (Faux-Pas)
description: Distinguish explicit knowledge (stated in story) from implicit knowledge (what an adult would reasonably conclude from context). Faux-pas questions hinge on this distinction.
triggers:
  - "does .+ know"
  - "知道"
  - "清楚"
  - "aware"
---

## Problem this skill solves

Faux-Pas errors (4/4) all stem from conflating two categories:

- **Explicit knowledge**: stated in the text ("Li Na greets her retired
  neighbor Uncle Liu" → Li Na knows Uncle Liu is retired).
- **Implicit knowledge**: NOT stated, but a reasonable person would know
  (Mr. Li is at Aunt Wang's buffet, tastes ribs, says "my wife's are
  better" → Mr. Li does NOT know these are Aunt Wang's; buffets don't
  announce cook per dish).

Getting this wrong creates the classic faux-pas failure: model labels an
innocent remark as "knowing insult" or vice versa.

## Workflow

1. **Identify the knowledge claim** the question is probing (e.g.
   "does Mr. Li know these ribs are Aunt Wang's?").
2. **Scan for explicit evidence** in the story:
   - Is the fact stated directly? → Mark as **explicit knowledge**.
   - Is the fact referred to in a way the character must have seen?
     → Mark as **observed explicit**.
3. **If not explicit, evaluate the implicit inference**:
   - What would an adult in this context reasonably know?
   - What affordances did the context provide for inference?
   - At a buffet, are dishes attributed to individual cooks? (No.)
   - When greeting "retired neighbor", does the adjective convey
     background knowledge? (Yes.)
4. **Output a three-level label**:
   - `explicit`: story directly states the character knows
   - `implicit-yes`: context strongly implies the character knows
   - `implicit-no`: context does not provide the inference; character
     plausibly does NOT know

## Output shape

```json
{
  "knowledge_claim": "Mr. Li knows ribs are Aunt Wang's cooking",
  "explicit_evidence": null,
  "contextual_clues": ["buffet-style gathering", "many dishes", "no attribution"],
  "adult_inference": "implicit-no",
  "final_label": "does not know",
  "answer_letter": "B"
}
```

## Anti-patterns

- Do NOT assume that being at someone's event implies knowing which food
  is theirs — buffets and potlucks break this.
- Do NOT assume that a character "must know" just because the reader
  knows. The reader is omniscient; the character is not.
- Do NOT use "ought to know" — use "reasonably infers from context". If
  the context doesn't provide an inference path, answer "does not know".
