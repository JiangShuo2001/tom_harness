---
name: macro-13
level: macro
layer: macro
family: "spatial-social-perspective-judgment"
description: "Direct-route macro for judging what a target character can see or how spatial relations appear from that character's viewpoint."
---

# Spatial Social Perspective Judgment

## Use When
- Use when the answer depends on what a specific character can see from their physical position.
- Use when left-right, front-back, rotation, facing direction, occlusion, mirror-like viewpoint, picture orientation, dice/cube faces, or object layout from another person's perspective is central.
- Use when the scene asks how a character would describe, identify, point to, search within view, or interpret a spatial relation based on their viewpoint.
- Use when the task can be solved by placing the target character in the scene and transforming the layout into that character's visual frame.

## Do Not Use When
- Do not use when the key issue is what the character believes after missing an event rather than what they can currently see; route to a belief macro such as classic false belief if search after an unseen move is central.
- Do not use when the key issue is what action the character will choose under competing commitments; route to macro-11.
- Do not use when the key issue is whether a remark or disclosure is socially inappropriate; route to macro-12.
- Do not use when the key issue is estimating quantities, probabilities, or samples rather than spatial viewpoint; route to macro-14.
- Do not use when the key issue is trust, reputation, or relationship history; route to macro-15.

## Decision Variable
what a target character can see or how they understand spatial relations from their viewpoint

## Direct Route Rule
Route immediately when left-right, rotation, viewpoint, or cube/dice/picture perspective is central.

## Expand With Micro Units
- micro-05
- micro-06
- micro-07
- micro-11

## Trigger Checklist
- A target viewer or perspective holder is specified.
- The question asks what that target sees, points to, reads, describes, or considers left/right/front/back.
- The scene includes spatial layout, orientation, facing direction, line of sight, obstruction, rotation, or object faces.
- The correct answer changes if solved from the reader's viewpoint instead of the character's viewpoint.
- No deeper belief, deception, relationship, or moral judgment is required to answer the core question.

## Workflow
- Identify the target character whose viewpoint controls the answer.
- Anchor the target's body orientation: facing direction, left/right, front/back, height, and position.
- Map visible objects from that viewpoint, excluding objects blocked by walls, containers, screens, distance, darkness, or other occluders.
- If orientation matters, rotate the spatial frame into the target's perspective before assigning left, right, near, far, front, or behind.
- If a cube, die, picture, sign, or screen is involved, determine which face or side is visible to the target, not which is visible to the reader.
- Answer only the spatial-visibility question unless the prompt explicitly adds belief, memory, social norm, or relationship reasoning.
- If the spatial computation becomes ambiguous, state the dependency on facing direction, obstruction, or layout and use the relevant micro expansion for repair.

## Special Case
**Reader-viewpoint trap**: When the target faces the reader or stands on the opposite side of an object, reverse egocentric directions as needed; the target's left is not automatically the reader's left.

Scene: Maya stands across a table facing Noah. A red cup is on Noah's left side of the table and a blue cup is on Noah's right side. Maya is asked to pick the cup on her left.
Question: Which cup is on Maya's left?
Answer logic: Because Maya faces Noah from the opposite side, her left corresponds to Noah's right side of the table. The blue cup is on Maya's left.

## Boundary Exit Rule
- Exit to a belief-focused macro if the character's outdated or mistaken belief, rather than their current visual access, determines the answer.
- Exit to macro-11 if the spatial scene only sets up a choice among competing commitments or next actions.
- Exit to macro-12 if the central question is whether someone caused embarrassment, offense, or a faux pas.
- Exit to macro-14 if the spatial information is only evidence for estimating a number, probability, or base rate.
- Exit to macro-15 if the scene asks how relationship history, loyalty, trust, or reputation changes interpretation.
- Add micro-05, micro-06, micro-07, or micro-11 when the route is correct but the answer requires finer diagnosis of visibility, attention, spatial cue use, or viewpoint transformation.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
A scene asks for another person's visual or spatial perspective, especially what they can see or which side/object/location is left, right, front, behind, visible, hidden, or facing them.
