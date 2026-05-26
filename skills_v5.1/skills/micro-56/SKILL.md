---
name: micro-56
level: micro
layer: L7
family: "quantity-probability"
description: "Identify the cause of an outcome without switching to blame, responsibility, or moral judgment."
---

# Causal Attribution

## Use When
- Use when the question asks what person, event, or condition caused an outcome.
- Use when the task is to identify the causal source of a result, change, or event.
- Use when the scene asks what led to, triggered, produced, or made something happen.
- Use when the answer should name the cause even if no one is being judged.

## Do Not Use When
- Do not use when the main issue is who is at fault, responsible, guilty, or deserving blame.
- Do not use when the question is about moral evaluation, apology, fault assignment, or deserved punishment.
- Do not use when the task is predicting beliefs, intentions, emotions, or actions rather than naming a cause.
- Do not use when the main issue is probability, typicality, quantity update, or evidence strength instead of causation.

## Decision Variable
the cause of the result

## Trigger Checklist
- Ask: what directly produced the outcome?
- Look for an explicit causal link such as because, due to, led to, caused by, or resulted from.
- Separate cause from blame: an accidental cause is still a cause.
- Prefer the stated causal factor in the scene over a moral or legal judgment.

## Workflow
- Identify the outcome that needs explanation.
- Find the person, event, or condition the scene links to that outcome.
- Return the causal factor, not the blamed person unless causation is the actual question.

## Special Case
**Accidental cause is still a cause**: If someone caused the outcome by accident, answer with the causal action or condition, not with blame language.

Scene: A vase falls after the shelf was loosened by a vibration from the washing machine.
Question: What caused the vase to fall?
Answer logic: The causal attribution is the loosened shelf and vibration, because the question asks for the cause of the outcome, not who should be blamed.

## Boundary Exit Rule
- Exit to micro-43 if the question asks who is responsible, at fault, guilty, or should apologize.
- Exit to micro-30 / macro-06 if the answer depends on moral blame, intention, negligence, or social judgment rather than cause.
- Exit to micro-22 if the scene asks the immediate purpose behind an act (intention), not the cause of an outcome.
- Exit to micro-54 / micro-55 if the main task is estimating likelihood or updating quantities instead of naming a cause.
- Exit to micro-15 if the focus is how new evidence updates a belief, rather than what produced the outcome.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when the prompt asks for the causal source of an outcome, change, or event.
