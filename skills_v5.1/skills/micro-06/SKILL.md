---
name: micro-06
level: micro
layer: L1
family: "perception-memory-knowledge"
description: "Diagnose what is visible from another person's spatial viewpoint, without inferring belief, attention, or sensory access."
---

# Spatial Perspective Transformation

## Use When
- Use when the question asks what a target person can see from their position.
- Use when you must transform the scene into the target person's left-right, front-back, or occlusion viewpoint.
- Use when the answer depends on the spatial relation visible from the target perspective.

## Do Not Use When
- Do not use when the main issue is whether the person noticed, remembered, believed, or inferred anything.
- Do not use when the question is about whether information was perceptually available at all; that is sensory access.
- Do not use when attention, salience, or event order changes the mental state; those are different units.
- Do not use when the task asks what the solver sees from their own viewpoint or asks for a non-spatial judgment.

## Decision Variable
the spatial relation visible from the target perspective

## Trigger Checklist
- A person's physical position is given.
- The scene contains an object, sign, image, or layout with directional structure.
- The question asks what that person would see, face, or identify from that viewpoint.
- The answer changes if the scene is mentally rotated or mirrored into the target person's perspective.

## Workflow
- Identify the target viewer's exact position and facing direction.
- Map the scene from that viewpoint, keeping only visibility and orientation.
- Check whether any object is blocked, reversed, or on the left/right side from that viewpoint.
- Answer only the visible spatial relation, not beliefs or interpretations.

## Special Case
**Occlusion versus perspective**: If an object is hidden by blocking, answer only what is visible after the perspective transform; do not mix in what the person knows is behind the blocker unless the question explicitly asks about knowledge.

Scene: Alice stands to the right of a table. A cup is behind a box from Alice's side.
Question: What can Alice see?
Answer logic: Transform the table into Alice's viewpoint. The box blocks the cup, so Alice cannot see the cup even if the cup exists in the scene.

## Boundary Exit Rule
- If the question shifts from visible layout to what the person noticed, believed, or remembered, exit immediately.
- If the question asks whether the person had sensory access in general rather than viewpoint-specific visibility, exit to Sensory Access.
- If the question requires reasoning about another mind, common knowledge, or interpretation of a cue, exit to the relevant social-cognitive unit.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when the case asks what is visible, facing, left-right reversed, or blocked from another person's position.
