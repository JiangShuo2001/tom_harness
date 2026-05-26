---
name: micro-26
level: micro
layer: L4
family: "emotion-appraisal"
description: "Infer a character's basic emotion by appraising whether an event helps or harms that character's goals, interests, safety, possessions, or social standing."
---

# Basic Emotion Appraisal

## Use When
- Use when the question asks what a character feels after a straightforward success, failure, gain, loss, threat, relief, or disappointment.
- Use when the needed inference is how the event affects the character's goals or interests.
- Use when the character's outward expression can be treated as sincere or irrelevant to the question.
- Use when the answer can be derived from ordinary appraisal patterns such as goal achieved implies happiness, goal blocked implies frustration or sadness, danger implies fear, loss implies sadness, and threat removed implies relief.

## Do Not Use When
- Do not use when the main question is what the character will choose or do next; route to goal-action units such as Commitment Priority or Goal-Conflict Arbitration.
- Do not use when the emotion is surprising specifically because the character has unusual values, preferences, or appraisals; route to Atypical Emotion.
- Do not use when the character feels one thing but displays another; route to Hidden Emotion.
- Do not use when the emotion depends on guilt, shame, blame, responsibility, wrongdoing, or moral evaluation rather than basic goal impact.
- Do not use when the emotion depends mainly on imagining an alternative outcome, regret, relief about what could have happened, or counterfactual comparison.

## Decision Variable
event impact on the character's goals or interests

## Trigger Checklist
- A character experiences or learns about an event.
- The question asks for an emotion, feeling, or likely affective reaction.
- The event has a clear positive, negative, threatening, or relieving consequence for that character.
- No hidden display, deception, moral blame, or unusual emotional preference is central.
- The answer can be explained by the character's own goals, not the narrator's or another person's goals.

## Workflow
- Identify the character whose emotion is being asked about.
- List that character's active goal, interest, possession, relationship, safety concern, or expectation in the scene.
- Classify the event's impact on that target: helps, blocks, threatens, removes threat, causes loss, or gives gain.
- Map the appraisal to a basic emotion: gain or success to happiness, blocked goal to frustration or disappointment, loss to sadness, danger to fear, insult or obstruction to anger, threat removed to relief.
- Check whether the character knows about the event; if not, appraise only what the character believes happened.
- Return the emotion with a brief causal explanation tied to the character's goal impact.

## Special Case
**Knowledge-gated appraisal**: Appraise the event as the character understands it, not as the reader knows it really is.

Scene: Maya wants her plant to survive. Her roommate secretly waters it after Maya leaves. Maya returns and sees the plant standing healthy, but she does not know her roommate helped.
Question: How does Maya feel when she sees the plant?
Answer logic: Maya sees evidence that her goal succeeded, so the basic appraisal is positive. She likely feels happy or relieved, even though the reader knows another person caused the success.

## Boundary Exit Rule
- If the task asks which action wins among competing plans, exit to micro-24 or micro-25 instead of inferring emotion.
- If the emotion is nonstandard because the character likes what most people dislike or dislikes what most people like, exit to micro-27.
- If facial expression, politeness, concealment, pretending, or private-versus-public feeling is central, exit to micro-28.
- If blame, guilt, shame, apology, deservedness, or moral responsibility determines the feeling, exit to a moral-emotion unit.
- If the answer depends on what might have happened but did not, exit to a counterfactual-emotion unit.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when an event's direct impact on a character's goal, interest, safety, or loss/gain is enough to infer the character's basic emotion.
