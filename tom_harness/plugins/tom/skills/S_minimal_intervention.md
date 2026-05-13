---
skill_id: S_minimal_intervention
name: Minimal Intervention (Rubric + Aggregate)
description: Structured rubric version of S04. LLM scores options on {directness, minimality, politeness}; Python aggregates and picks. Prevents the LLM from talking itself into a worse option.
triggers:
  - "convince"
  - "persuade"
  - "说服"
  - "劝说"
---

## Why this exists

S04 declared "prefer the minimal intervention", but the LLM still tended
to pick sophisticated-sounding options because its free-form reasoning
rewarded vivid language. This procedural version pins the rubric:

- **directness** [0..3]: does it address the exact concern?
- **minimality** [0..3]: how little extra structure?
- **politeness** [0..2]: non-confrontational?

Python aggregates: `total = 2*direct + 2*minimal + polite`. Highest wins.

## Output

```json
{
  "totals": {"A": 6, "B": 8, "C": 6, "D": 14},
  "breakdown": {"D": {"direct": 3, "minimal": 3, "polite": 2}, ...},
  "recommendation": "D"
}
```
