---
name: micro-19
level: micro
layer: L3
family: "goal-action"
description: "Use this unit to identify a character's own likes, wants, or preferences, without inferring another person's preference or higher-level goals."
---

# Self Preference

## Use When
- Use when the question asks what this character personally likes, wants, prefers, or would choose.
- Use when the answer depends on the character's own preference rather than on belief, knowledge, emotion, or social strategy.
- Use when the scene gives direct statements, repeated choices, or stable tastes that reveal the character's preference.

## Do Not Use When
- Do not use when the main issue is another person's preference, even if the character is trying to guess it.
- Do not use when the main issue is how sure the character is, how credible a source is, or what the character knows.
- Do not use when the question is really about a goal, plan, obligation, or next action rather than liking or wanting.
- Do not use when the question asks which option is best for the group, the listener, or the situation instead of what the character likes.

## Decision Variable
the character's own preference

## Trigger Checklist
- Ask: whose liking or wanting is being queried?
- Look for direct preference words such as like, want, prefer, choose, favorite, or would rather.
- Check whether the answer comes from the character's internal taste or desire, not from another person's mind.
- Ignore whether the character is correct, informed, polite, or strategic unless that changes the preference itself.

## Workflow
- Identify the character whose preference is queried.
- Extract the character's expressed or implied liking from the scene.
- If several options are mentioned, choose the one most aligned with that character's own stated desire or repeated choice.
- Do not switch to another unit unless the question becomes about another person's preference, certainty, credibility, or goal priority.

## Special Case
**Preference expressed through action**: If the character does not say what they like, infer preference from consistent voluntary choice only when the scene clearly shows that the choice reflects liking rather than convenience, duty, or pressure.

Scene: Mina is offered tea and coffee. She smiles and says she always picks tea when both are available.
Question: What does Mina prefer?
Answer logic: Her repeated voluntary choice identifies her own preference, so the answer is tea.

## Boundary Exit Rule
- Exit to micro-20 if the question changes from what the character likes to what another person likes.
- Exit to micro-17 or micro-18 if the question is about confidence, rumor, evidence, or source reliability.
- Exit to micro-21 or micro-24 if the answer depends on a goal hierarchy, plan, obligation, or next action rather than preference.
- Exit to micro-40 or micro-41 if the scene asks what is socially wise, polite, or persuasive instead of what the character personally wants.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Route here when the diagnostic question is the character's own liking, wanting, or choice preference.
