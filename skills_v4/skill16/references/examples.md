# SP-01 Reference

## Decision Variable

- The key variable is the axis-mapping rule applied from your grid to
  the target viewer's grid (opposite / left / right / same side).

## Route Signal

- Use this skill when the question asks what someone sees, draws, or
  describes from a specific vantage point.

## Hard Boundary

- If the perceiver has a sensory restriction (blind / deaf / behind
  glass), use `skill19` for the conclusion; this skill is only the
  geometry sub-step.
- If the task is about belief / intention / emotion, do not use this
  skill.

## Shortcut To Avoid

- Do not eyeball the rotation; apply the explicit axis-mapping rule.
- Do not treat "your right side" as just an LR flip.
- Do not assume a die's opposite faces are adjacent (they sum to 7).

## Common Failure Modes

- Confusing 90° (side) rotation with 180° (opposite) rotation.
- For dice, picking the option that pairs adjacent faces instead of
  opposite faces.
- Stopping the reasoning at the wrong viewer's perspective.

## Minimal Pair

- Case A: target on your opposite side → both axes reverse.
- Case B: target on your right side → cols become rows, read R→L.

## Boundary Stress Test

- `What did Wu Di see when he stood opposite you?` → this skill,
  opposite-side rule.
- `The blind student is in front of the water-phone. What does she
  think it sounds like?` → `skill19`, not this skill.

## Generalization Note

- The transferable core is explicit perspective transformation:
  precise axis algebra beats intuitive rotation, especially for the
  "target on your right" case.
