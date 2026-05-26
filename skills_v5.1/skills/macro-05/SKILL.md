---
name: macro-05
level: macro
layer: macro
family: "emotion"
description: "Direct-route this macro when a scene asks for a character's true feeling from a mismatch between inner emotion and outward display or ordinary expectation."
---

# Hidden Emotion and Atypical Emotion

## Use When
- Use when the scene asks how a character truly feels rather than what they displayed or said.
- Use when a character's outward expression, behavior, or stated words conflict with their likely inner feeling.
- Use when the key task is to infer suppressed, masked, reversed, or unusually appraised emotion.
- Use when the appraised situation would ordinarily produce one emotion but the character shows another, and the question asks why.

## Do Not Use When
- Do not use when the main issue is responsibility, blame, guilt, shame, or moral evaluation rather than hidden feeling.
- Do not use when the scene is mainly about what someone saw, knew, or believed instead of what they felt.
- Do not use when the cue is primarily a nonverbal intention signal and the emotion itself is not the question.

## Decision Variable
why a character's true feeling differs from outward display or ordinary expectation

## Direct Route Rule
Route immediately when emotion must be inferred through suppression, reversal, or unusual appraisal.

## Expand With Micro Units
- micro-21
- micro-26
- micro-27
- micro-28
- micro-29
- micro-31
- micro-32

## Trigger Checklist
- The question asks what the person really feels, not what they did or said literally.
- The person shows one emotion outwardly but the context suggests a different inner state.
- The emotion may be hidden, restrained, inverted, mixed, or atypical for the situation.
- The answer depends on appraisal of a social or situational mismatch, not on factual memory or belief tracking.
- A direct feeling cue is absent, so the solver must infer the private emotion from behavior, context, and expectation.

## Workflow
- Identify the public display: words, facial expression, tone, or action.
- Identify the situational pressure that could mask or reverse the true feeling.
- Check whether the apparent emotion is a cover, a politeness display, a compensation, or an atypical reaction.
- Infer the private emotion that best explains the mismatch.
- If the case turns on guilt, blame, or norm violation, exit to the moral-emotion macro instead.

## Special Case
**Polite display versus private feeling**: When someone deliberately shows a socially acceptable emotion that differs from their real one, answer from the private feeling, not the display.

Scene: A person receives a gift they dislike, thanks the giver warmly, and later looks disappointed after the giver leaves.
Question: How do they really feel?
Answer logic: The warm thanks is a social display; the later reaction reveals the private feeling. The true emotion is disappointment, not gratitude.

## Boundary Exit Rule
- Exit to macro-06 if the question is really about guilt, shame, blame, or moral judgment after harm.
- Exit to macro-01 / macro-02 if the key challenge is what someone knows, saw, or falsely believes rather than what they feel.
- Exit to macro-04 if the problem is mainly cue interpretation or conversational intention rather than emotional inference.
- Add micro-26 when the basic appraisal of the situation drives the felt emotion.
- Add micro-27 when the puzzle is a genuinely unusual emotional reaction to a normal event.
- Add micro-28 when the inner-outer mismatch is descriptive (what is hidden) rather than explanatory.
- Add micro-29 when the mismatch is driven by a social display rule.
- Add micro-31 when the felt emotion compares actual to a salient counterfactual outcome.
- Add micro-21 when goal hierarchy (which goal is at stake) is needed to label the emotion.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
A mismatch between what a character shows and what they likely feel, especially when the feeling is concealed, reversed, or atypical for the situation.
