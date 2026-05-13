# FB-01 Reference

## Decision Variable

- The key variable is the target character's last seen location of the object.

## Route Signal

- Use this skill when one character missed a move and the question asks where that same character will look.

## Hard Boundary

- If the question contains `X thinks Y` or otherwise requires an outer thinker modeling another mind, route to `skill4`.
- If the task is about what should be inside a container, route to `skill5`.

## Shortcut To Avoid

- Do not answer with the real current location just because it is the latest event.
- Do not keep using first-order reasoning after a second-order cue appears.

## Common Failure Modes

- Collapsing second-order belief into first-order belief.
- Swapping believed location with real location.
- Missing option-level wording differences between similar containers.

## Minimal Pair

- Case A: the target misses the move, so they search the old location.
- Case B: the target sees the move, so they search the new location.

## Boundary Stress Test

- `Where will Youyou look?` -> this skill.
- `Where does Xiao Li think Youyou will look?` -> `skill4`, not this skill.

## Generalization Note

- The transferable core is first-order belief tracking: keep reality separate from the target character's last known state and answer from that belief alone.
