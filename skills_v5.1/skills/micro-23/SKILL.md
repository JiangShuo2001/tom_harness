---
name: micro-23
level: micro
layer: L3
family: "goal-action"
description: "Predicts the character's next likely behavior by combining their current belief state with their active goal."
---

# Action Prediction

## Use When
- Use when the question asks what a character will most likely do next.
- Use when the answer depends on the character's belief about the situation, not only on the real situation.
- Use when the character has an identifiable goal and the task is to predict the next outward behavior that would serve that goal.
- Use inside larger false-belief, social-cue, preference, or commitment scenes when the final diagnostic variable is the next action.

## Do Not Use When
- Do not use when the question asks why the character is currently acting, looking, gesturing, or speaking; use intention recognition instead.
- Do not use when the main task is to rank commitments, obligations, or prior plans; use commitment priority instead.
- Do not use when the main task is to explain the hierarchy among long-term, short-term, and local goals; use goal hierarchy instead.
- Do not use when the key problem is how the character weighs competing goals in general rather than which concrete next action follows from one active goal.
- Do not use when the answer is about what the character knows, believes, wants, or feels without predicting an observable next behavior.

## Decision Variable
the character's next likely action

## Trigger Checklist
- The prompt asks what the character will do, where they will go, what they will choose, or what they will try next.
- A current belief state can be identified for the character.
- An active goal, desire, or task can be identified.
- The predicted action should be from the character's perspective, even if their belief is false.
- The output is an observable behavior, not an internal motive or emotion.

## Workflow
- Identify the target character whose next action must be predicted.
- Separate reality from the character's belief state, including what they saw, missed, misunderstood, or falsely believe.
- Identify the active goal the character is trying to satisfy at this moment.
- List the available actions the character could take in the scene.
- Select the action that best advances the active goal given the character's own belief state.
- If several actions are plausible, prefer the most immediate, low-friction action unless the prompt gives a stronger constraint.
- State the predicted action and, if needed, briefly justify it using belief plus goal.

## Special Case
**False-belief action**: When the character has a false belief, predict the action that would make sense if that false belief were true, not the action that would work in reality.

Scene: Maya puts her keys in the blue bowl and leaves. While she is away, Leo moves the keys to the drawer. Maya returns wanting to drive home.
Question: Where will Maya look first?
Answer logic: Maya wants her keys and believes they are still in the blue bowl, so her next likely action is to look in the blue bowl first.

## Boundary Exit Rule
- Exit to micro-22 if the prompt asks for the purpose behind a current action or cue rather than the next action.
- Exit to micro-24 if the prompt requires deciding whether an existing commitment, deadline, promise, or scheduled plan overrides a new option.
- Exit to micro-25 if the prompt focuses on how conflicting goals are weighted, not on the immediate behavior that follows.
- Exit to micro-21 if the prompt asks how local actions relate to broader goals rather than what action happens next.
- Exit to belief-focused units if the only required answer is what the character thinks or knows, with no behavioral prediction.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when the answer must be an observable next behavior derived from the character's belief state and active goal.
