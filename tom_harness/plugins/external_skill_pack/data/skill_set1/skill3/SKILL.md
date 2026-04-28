---
name: skill3
description: Use for FB-01 first-order location false belief questions by tracking the original object location, the unseen move, and the target character's last known state.
---

# FB-01 First-Order Location False Belief

## Use When

- The question asks where one character will look for or search for a moved object.
- Only one mind needs to be modeled: the target character's own belief.
- The target character missed the move and still relies on the last location they saw.

## Do Not Use When

- The question asks what one character thinks another character believes. Use `skill4`.
- The task is about label-content mismatch inside a container. Use `skill5`.
- The question is about real current location instead of a character's belief.

## Trigger Checklist

- Is the question about one character's own future search location?
- Did that character last see the object in one place and miss a later move?
- Is there no extra outer thinker such as `X thinks Y will look`?
- If yes, use this skill. If a second mind is explicitly queried, route to `skill4` immediately.

## Workflow

1. Identify the target character, the object, and the original location the target last saw.
2. Record the later move and check whether the target witnessed it.
3. If the question introduces another thinker or asks what one person thinks another will do, stop and route to `skill4`.
4. Keep two columns explicit: `real current location` and `target's believed location`.
5. Answer with the target character's last known location, not the real current location.
6. If options are provided, choose the option whose wording exactly matches that believed location.

## Output Template

- `Task framing`: target character, object, and requested search action.
- `Belief evidence`: original seen location, move event, and whether the target saw the move.
- `Reasoning decision`: the target character's believed location.
- `Answer`: the believed search location, mapped to the exact option if needed.

## Failure Checks

- Keep original location and real location separate.
- Do not collapse second-order belief into first-order belief.
- Do not use recency as a shortcut to the real location.
- Match the exact option wording for similar containers.

## Boundary Exit Rule

- If the question contains two minds such as `X thinks Y`, stop and use `skill4` instead of continuing with first-order reasoning.
- If the task is about what should be inside a labeled container, stop and use `skill5`.
- If the task asks about current reality rather than the target's belief, do not use this skill.

## Answer Discipline

- In multiple-choice settings, compute the believed location first, then map it to the exact option text.
- Do not answer with a synonym if the benchmark expects a specific container label.

## References

- For compact boundaries, minimal pairs, and common confusions, read `references/examples.md`.
