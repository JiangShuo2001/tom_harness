---
name: micro-20
level: micro
layer: L3
family: "goal-action"
description: "Micro skill for judging whether a character represents another person's likes, wants, or taste."
---

# Other Preference

## Use When
- Use when the question asks whether a character knows what another person likes, wants, prefers, or would choose.
- Use when the answer depends on the character's model of someone else's preference, not their own.
- Use when the scene is about preference attribution across people, such as knowing what a friend, partner, customer, or child would want.

## Do Not Use When
- Do not use when the question is about the character's own preference.
- Do not use when the main issue is what action the person is trying to accomplish rather than what they like.
- Do not use when the question is about belief, intention, emotion, or source reliability instead of preference.

## Decision Variable
the character's representation of another person's preference

## Trigger Checklist
- A person other than the target character is the one whose likes or wants matter.
- The scene asks what the character thinks that other person prefers.
- The question can be answered by comparing the model of the other's preference against available cues or history.
- No action-purpose inference is required beyond identifying what the other person wants.

## Workflow
- Identify whose preference is being asked about.
- Check whether the character has a representation of that other person's likes or wants.
- Use explicit evidence, prior choices, stated likes, or stable taste to judge the character's model.
- Ignore the character's own preference unless it is directly relevant as a contrast.

## Special Case
**Preference versus intention**: If the cue shows why someone acted, choose intention recognition; if the cue shows what they like or want, choose other preference.

Scene: Alex remembers that Priya always chooses tea over coffee when offered both.
Question: Does Alex know what Priya prefers?
Answer logic: Yes. The key variable is Alex's representation of Priya's taste, not Alex's own choice and not Priya's immediate purpose for acting.

## Boundary Exit Rule
- Exit to micro-19 Self Preference if the question asks what the character themselves wants or likes.
- Exit to micro-22 Intention Recognition if the main task is to infer the purpose behind an action, gaze, gesture, or request.
- Exit to micro-23 Action Prediction if the answer required is the other person's next behavior rather than the character's representation of their taste.
- Exit to a belief, emotion, or source-credibility unit if the relevant cue is about trust, belief, emotion, or deception rather than preference.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use when the scene asks whether one person understands another person's likes, wants, or preferred option.
