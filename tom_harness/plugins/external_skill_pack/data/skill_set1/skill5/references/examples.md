# FB-03 Reference

## Decision Variable

- The key variable is whether the answer should follow appearance or reality from the requested perspective.

## Route Signal

- Use this skill when the story contrasts a container's label or expected content with what is actually inside.

## Hard Boundary

- If the story is about moving an object between locations, route to `skill3` or `skill4`.
- If there is no appearance-versus-reality split, do not use this skill.

## Shortcut To Avoid

- Do not swap expected content with real content.
- Do not let location-tracking habits override content reasoning.

## Common Failure Modes

- Forgetting who opened the container.
- Treating label-based expectation as if it were true knowledge.
- Mistaking content belief questions for location false-belief questions.

## Minimal Pair

- Case A: the target only sees the label, so the answer follows appearance.
- Case B: the target opened the container, so the answer follows reality.

## Boundary Stress Test

- `What should be in the backpack?` -> this skill.
- `Where will she look for the backpack?` -> not this skill.

## Generalization Note

- The transferable core is appearance-versus-reality reasoning about contents: separate label, true content, and target belief before answering from the requested perspective.
