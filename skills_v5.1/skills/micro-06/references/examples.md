# micro-06 Examples and Boundaries

## Decision Variable
the spatial relation visible from the target perspective

## Route Signal
Use this micro unit when the case asks what is visible, facing, left-right reversed, or blocked from another person's position.

## Hard Boundary
- Visibility from a viewpoint only.
- No belief inference.
- No attention or memory inference.
- No interpretation of intentions or emotions.

## Shortcut To Avoid
- Do not assume that seeing implies noticing.
- Do not convert viewpoint questions into belief questions.
- Do not use general world knowledge when simple spatial transformation is sufficient.

## Common Failure Modes
- Answering from the solver's own viewpoint instead of the target's viewpoint.
- Confusing visibility with attention or awareness.
- Treating occlusion as a belief problem.
- Adding mental-state inferences that are not asked for.

## Minimal Pair
- Case: A person stands on the left side of a sign and is asked which side of the sign appears closest. | Why: The answer depends on viewpoint transformation and spatial relation only.
- Case: A person walked past a painting and is asked whether they noticed a detail. | Why: This is about attention or noticing, not viewpoint visibility.

## Boundary Stress Test
- If the scene is fully visible but the person did not look, do not use this unit.
- If the person can see the object only by rotating mentally, this unit still applies.
- If the question asks what the person thinks is behind the object, this unit does not apply.

## Generalization Note
This unit covers viewpoint transformation across simple layouts, rotations, mirrors, and occlusion, but only as a visibility problem.
