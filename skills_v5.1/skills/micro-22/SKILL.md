---
name: micro-22
level: micro
layer: L3
family: "goal-action"
description: "Infer the immediate purpose behind a current action, gaze, gesture, expression, or other observable cue without predicting the person's next action."
---

# Intention Recognition

## Use When
- Use when the question asks why a person is currently doing, looking at, pointing to, touching, signaling, or arranging something.
- Use when the answer is the immediate purpose or communicative function of an observable behavior.
- Use when a cue such as gaze, gesture, posture, wink, smile, nod, pause, or object handling must be interpreted as goal-directed.
- Use when the scene asks what the actor is trying to make someone notice, understand, avoid, approach, or do through the current behavior.

## Do Not Use When
- Do not use when the main answer is what the person will do next rather than why the present behavior is occurring; use action prediction instead.
- Do not use when the task is to rank long-term versus short-term goals; use goal hierarchy instead.
- Do not use when the key variable is another person's stable preference or desire; use other preference instead.
- Do not use when the issue is which prior commitment, obligation, or plan should take priority; use commitment priority instead.
- Do not use when the behavior is merely a physical event with no need to infer a mental purpose.

## Decision Variable
the immediate purpose behind the behavior

## Trigger Checklist
- There is a concrete observable behavior or cue.
- The question asks for purpose, meaning, motive, or what the actor is trying to accomplish now.
- The answer can be stated as an immediate aim, not a future action sequence.
- Relevant context indicates what the actor knows, wants noticed, or wants changed.
- Alternative explanations can be compared using the actor's perspective rather than the observer's hindsight.

## Workflow
- Identify the exact behavior to explain, including who performs it and who may notice it.
- List the immediate effects the behavior could plausibly have in the scene, such as attracting attention, hiding information, requesting help, warning, reassuring, teasing, or checking something.
- Use the actor's current knowledge, goal, audience, and constraints to eliminate purposes the actor could not reasonably intend.
- Choose the purpose that best explains the specific form, timing, direction, and target of the behavior.
- State the answer as an immediate intention, not as a full plan or prediction of later behavior.

## Special Case
**Nonverbal communicative cue**: When a gesture, gaze, or expression is directed toward another person, first test whether it is meant to change that person's attention, belief, emotion, or behavior.

Scene: Maya sees that Leo is about to mention a surprise party while the guest of honor is nearby. Maya catches Leo's eye and quickly puts a finger to her lips.
Question: Why does Maya make that gesture?
Answer logic: The behavior is a directed nonverbal cue. Its immediate purpose is to warn Leo to stop talking or stay quiet so the surprise is not revealed.

## Boundary Exit Rule
- If the answer must be a next step such as where the person will go, what they will choose, or what they will say next, exit to micro-23 Action Prediction.
- If the answer requires comparing a local action to a broader aim, exit to micro-21 Goal Hierarchy.
- If the answer depends on what one person believes another person likes or wants, exit to micro-20 Other Preference.
- If the answer depends on obligations, prior promises, scheduled plans, or task priority, exit to micro-24 Commitment Priority.
- If the scene can be solved from literal verbal meaning alone without inferring a behavioral purpose, do not use this unit.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when an observable behavior is the evidence and the diagnostic question is what purpose that behavior serves right now.
