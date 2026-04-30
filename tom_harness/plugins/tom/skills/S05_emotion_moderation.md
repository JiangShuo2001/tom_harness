---
skill_id: S05_emotion_moderation
name: Emotion Moderation (Anti-Magnification)
description: When picking among emotion options, resist the pull toward the most emotionally charged option. Match the option whose intensity matches the surface behavior described in the story, not the one that makes the story most dramatic.
triggers:
  - "feel"
  - "mood"
  - "emotion"
  - "情绪"
  - "心情"
  - "感受"
---

## Problem this skill solves

Ambiguous Story (7 errors) and Unexpected Outcome (5 errors) share a
failure mode we call **emotional magnification**: given three or four
emotion options of varying intensity, model prefers the most intense
plausible one, when the correct answer is moderate.

Examples:

> Xiao Ming loses a chess game, has a conflict with opponent.
> Options: A guilty / B happy / C annoyed about losing / D very disappointed
> **Answer: C (annoyed)**. Model picks D (very disappointed) — adds intensity.

> Xiaofei is appointed volunteer after Ali walks over.
> Options: A happy and excited / B ashamed / C confused / D angry/betrayed
> **Answer: A (happy)**. Model picks B (ashamed) — adds negative inference.

The bug: the model's decoder has a pull toward vivid language, and
picks the more "interesting" emotion.

## Workflow

1. **Extract behavioral surface** from the story: what did the character
   actually **do** or **say**? (e.g. "sighs", "smiles", "walks away",
   "does not reply").
2. **Classify each option's intensity** on [−3..+3]:
   - −3 very negative (betrayed, devastated) / +3 very positive (thrilled)
3. **Identify the surface's implied intensity** from the behavior alone
   (ignore hypothesized internal state).
4. **Prefer the option whose intensity ±1 matches the surface**:
   - Behavior shows frustration → C "annoyed" (intensity −1), not D
     "very disappointed" (intensity −2).
5. **If the story explicitly signals a hidden emotion** (e.g. "smiles but
   inside ...", "outwardly ... but"), this skill does NOT apply — route
   to S09_hidden_emotion instead.

## Output shape

```json
{
  "surface_behavior": ["argues about chess", "loses match"],
  "implied_intensity": -1,
  "option_intensities": {"A": -2, "B": +2, "C": -1, "D": -2},
  "magnification_flag": ["B", "D"],
  "recommendation": "C"
}
```

## Anti-patterns

- Do NOT project "what I would feel in this situation" — stay with the
  surface described.
- Do NOT amplify negative inference just because the situation has
  conflict. Conflict can produce annoyance (mild) as easily as
  disappointment (strong).
- Do NOT ignore positive options just because the situation looks tense.
  The wedding-anniversary example shows the answer can be a completely
  unrelated factor (work stress) — but when no such signal exists, mild
  positive is often right.
