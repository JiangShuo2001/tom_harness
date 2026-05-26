---
name: macro-01
level: macro
layer: macro
family: "false-belief"
description: "Direct-route macro for predicting where or how a character will act from their own first-order false belief, especially after an object or situation changes while they are absent or unaware."
---

# Classic False-Belief Judgment

## Use When
- Use when the scene asks where a character will look, search, go, or act based on what they falsely believe.
- Use when a character had earlier access to a location or state, then the world changed without that character seeing or learning about the change.
- Use when the answer depends on the character's own belief rather than the real current state.
- Use when the case is a first-order mindreading problem: what X believes and does, not what X thinks Y believes.

## Do Not Use When
- Do not use when the main task is second-order belief, such as where A thinks B will look; route to macro-02.
- Do not use when the main conflict is appearance versus reality without action prediction from a false belief; route to macro-03.
- Do not use when the question asks what is actually true rather than what the character will believe or do.
- Do not use when the character witnessed the change, was told about it, or otherwise had evidence that updates their belief.

## Decision Variable
where or how a character will act based on a false belief

## Direct Route Rule
Route immediately when the case is a first-order search-location belief after an unseen move.

## Expand With Micro Units
- micro-05
- micro-08
- micro-09
- micro-11
- micro-12
- micro-23

## Trigger Checklist
- A target character previously observed or learned an initial location, container, owner, route, or state.
- The relevant object or situation changed after that observation.
- The target character did not see, hear, infer, or get told about the change.
- The question asks what the target character will do, where they will search, or what action they will take.
- Only the target character's first-order belief is needed to answer.
- The real current location or state conflicts with the target character's belief.

## Workflow
- Identify the target character whose action or search behavior is being predicted.
- Record what that character last saw, heard, or was told about the relevant object or situation.
- Check whether the later change was outside that character's perception or knowledge.
- If the character lacked access to the change, preserve their outdated belief.
- Predict the action from that belief: the character looks, goes, asks, reaches, or acts according to the old location or state.
- Answer in terms of the character's perspective, and explicitly separate belief-based action from actual reality when needed.
- If another person's belief about the target character is required, exit to macro-02; if the issue is what an object really is despite its appearance, exit to macro-03.

## Special Case
**Unseen transfer or relocation**: When an object is moved while the target character is absent or unable to observe, the target will search in the original place they last believed the object to be, unless the scene gives them later updating evidence.

Scene: Maya puts her keys in the blue bowl and leaves the room. While she is gone, Leo moves the keys to a drawer. Maya returns and wants her keys.
Question: Where will Maya look first?
Answer logic: Maya last saw the keys in the blue bowl and did not see Leo move them. Her belief is false but still guides her action, so she will look first in the blue bowl.

## Boundary Exit Rule
- Exit to macro-02 when the answer requires modeling what one character thinks another character believes, knows, or will do.
- Exit to macro-03 when the core question is about the difference between appearance and reality, object identity, or fenced-off world knowledge rather than belief-guided action.
- Add micro-05 or micro-11 when the failure risk is about who saw what or which perspective had perceptual access.
- Add micro-08 or micro-12 when the failure risk is about memory, updating, or preserving the last known belief.
- Add micro-23 when the action prediction requires connecting belief to goal-directed behavior rather than merely naming the believed location.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
A character will search or act according to an outdated belief because a relevant change happened outside their awareness.
