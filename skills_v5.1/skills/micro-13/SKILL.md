---
name: micro-13
level: micro
layer: L2
family: "belief-models"
description: "Diagnose what one person thinks another person believes, when the answer depends on an embedded mental model rather than on reality alone."
---

# Second-Order or Recursive Belief

## Use When
- Use when the question asks what X thinks Y believes.
- Use when the core task is tracking one belief nested inside another belief.
- Use when the answer depends on recursive attribution rather than on the actual facts.
- Use as a diagnostic substep inside a larger scene when the only uncertain part is one character's model of another character's mind.

## Do Not Use When
- Do not use when the question only asks what X believes about the facts; use first-order belief instead.
- Do not use when the main issue is whether X's belief matches reality; use false belief instead.
- Do not use when the task is appearance versus reality without a character modeling another mind; use appearance-reality instead.
- Do not use when the task is simply how new evidence changes belief; use evidence-update instead.
- Do not use when common knowledge or shared awareness is the main issue rather than recursive attribution.

## Decision Variable
which belief is embedded inside which other belief

## Trigger Checklist
- Does the prompt ask what one person thinks another person believes?
- Do you need to track a belief about a belief, not just a belief about the world?
- Is the key uncertainty about the outer mind's model of the inner mind?
- Would answering require saying what A thinks B expects, knows, or believes?

## Workflow
- Identify the outer thinker and the inner thinker.
- State the outer thinker’s model of the inner thinker’s belief.
- Ignore reality unless it is needed only to check whether the inner belief is false.
- Answer the nested belief directly, not the factual state of the world.

## Special Case
**Nested belief with a false inner belief**: If the question asks what X thinks Y believes, answer the nested belief even when Y is wrong about reality; do not collapse the task into a false-belief question.

Scene: Alice saw Ben leave his keys on the table. Ben did not see them moved to the drawer. Later, Clara asks what Alice thinks Ben believes about the keys.
Question: What does Alice think Ben believes about the keys?
Answer logic: This is second-order belief because the target is Alice's model of Ben's belief. Determine whether Alice thinks Ben still believes the keys are on the table, then answer that belief state, not where the keys really are.

## Boundary Exit Rule
- If the task asks what the character believes is true, exit to first-order belief.
- If the task asks whether the character's belief is wrong, exit to false belief.
- If the task asks what is actually true versus what it looks like, exit to appearance-reality.
- If the task asks how a new clue changes belief, exit to evidence-update.
- If the task does not require a belief about another belief, do not stay in this unit.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when the prompt contains recursive language such as thinks, believes, knows, expects, or assumes about another person's mental state.
