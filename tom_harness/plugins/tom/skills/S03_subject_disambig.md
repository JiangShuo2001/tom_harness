---
skill_id: S03_subject_disambig
name: Belief-Subject Disambiguator
description: Before any belief inference, explicitly identify whose mental state the question asks about. Parse the question grammatically and tag the subject with [SUBJECT=X]. This prevents "self-belief vs other-belief" confusion.
triggers:
  - "think"
  - "believe"
  - "expect"
  - "认为"
  - "以为"
  - "觉得"
---

## Problem this skill solves

A concrete class of false-belief failures on our dataset: the question
asks what **the knowing-agent** expects, not what **the uninformed-agent**
expects. Model conflates the two because the question surface looks like
a Sally-Anne. Example from a real failure:

> "Youyou finds a box labeled 'ring'. Youyou opens it, sees a carrot,
>  closes the box. Lilei enters the garden and sees the box.
>  **After Li Lei opens the box, what does Youyou expect to find in the box?**"

Here Youyou is the knowing agent — she already saw the carrot. The
question asks *her* expectation, which is CARROT (A). Model picks RING (D)
because it applies the Sally-Anne template to the wrong subject.

## Workflow

1. **Identify all agents** mentioned in the story: `A = {Youyou, Lilei}`.
2. **Parse the question** to find the mental-state **subject**:
   - "**X** thinks/believes/expects/will look" → subject = X
   - "What does **X** think **Y** will do" → subject = X (outer); object-of-belief = Y (inner)
3. **Tag**: emit `[SUBJECT=X, PERSPECTIVE_ORDER=1|2]`.
4. **Identify X's epistemic state**:
   - What has X observed?
   - What has X NOT observed?
5. **Route to the correct downstream skill**:
   - If X observed the key fact → apply S04_first_order_truth (X knows reality).
   - If X did not observe → apply S05_first_order_false_belief (X is mistaken).
   - If the question is about X's belief about Y's belief → S06_second_order_belief.

## Output shape

```json
{
  "subject": "Youyou",
  "perspective_order": 1,
  "subject_observed": ["opened the box", "saw carrot"],
  "subject_did_not_observe": [],
  "is_knowing_agent": true,
  "route": "S04_first_order_truth"
}
```

## Anti-patterns

- Do NOT apply the Sally-Anne template mechanically when the question is
  about the knowing agent. The surface "what does X expect?" can ask
  either — check whose observations are listed.
- Do NOT confuse outer and inner subjects in second-order questions.
