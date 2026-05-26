---
name: micro-31
level: micro
layer: L4
family: "emotion-appraisal"
description: "Diagnose regret, relief, disappointment, or pleasant surprise by comparing what happened with a salient alternative outcome."
---

# Counterfactual Emotion

## Use When
- Use when the question asks what emotion follows from comparing reality with a salient alternative outcome.
- Use when the answer depends on whether the actual outcome feels better or worse than what could have happened.
- Use when the scene is about regret, relief, disappointment, or pleasant surprise from a contrast case, not from responsibility or norm violation.

## Do Not Use When
- Do not use when the emotion is explained by blame, guilt, shame, pride, anger, or gratitude tied to responsibility or moral appraisal.
- Do not use when the issue is simple success, failure, happiness, or sadness with no explicit or implied alternative outcome.
- Do not use when the main question is outward display, suppression, empathy, or emotion regulation rather than the felt emotion itself.
- Do not use when the comparison is about probability, certainty, or evidence alone without an emotional counterfactual contrast.

## Decision Variable
actual outcome versus salient alternative outcome

## Trigger Checklist
- Is there a clear actual outcome?
- Is there a plausible alternative outcome that matters to the character?
- Is the emotion based on comparing those two outcomes?
- Is the alternative better or worse than reality from the character's point of view?
- Is the target emotion regret, relief, disappointment, or pleasant surprise?

## Workflow
- Identify the real outcome that occurred.
- Identify the salient alternative outcome that could have happened.
- Compare the two outcomes from the character's perspective.
- Infer the emotion from the direction of the comparison.
- If no contrast is doing the work, exit to a different emotion skill.

## Special Case
**Implied alternative, not stated alternative**: Use this unit even when the alternative is only implied, as long as the emotional answer depends on 'could have happened' contrast rather than on blame, norm, or display.

Scene: A driver narrowly avoids a crash and then goes quiet.
Question: What does the driver most likely feel?
Answer logic: The actual outcome is much better than the feared alternative of crashing, so the emotion is relief.

## Boundary Exit Rule
- Exit to micro-26 Basic Emotion Appraisal if the question can be answered without comparing reality to an alternative outcome.
- Exit to micro-30 Moral Emotion if responsibility, wrongdoing, or social norm is the main cause of the emotion.
- Exit to micro-28 Hidden Emotion or micro-29 Emotional Disguise if the task asks how the person shows, hides, or manages the emotion rather than what the emotion is.
- Exit to micro-33 Emotion Regulation if the question is about coping with or reframing the emotion after it arises.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Route here when the scene asks for regret, relief, disappointment, or pleasant surprise based on a better-or-worse alternative outcome.
