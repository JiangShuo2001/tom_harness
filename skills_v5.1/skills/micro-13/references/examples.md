# micro-13 Examples and Boundaries

## Decision Variable
which belief is embedded inside which other belief

## Route Signal
Use this micro unit when the prompt contains recursive language such as thinks, believes, knows, expects, or assumes about another person's mental state.

## Hard Boundary
- The answer must depend on one mental model embedded inside another.
- The prompt must require attribution from one mind to another mind, not only from mind to world.
- If the inner belief is not part of the question, this unit does not apply.

## Shortcut To Avoid
- Do not answer from the real state of the world and skip the outer character's model.
- Do not reduce the problem to a simple false-belief lookup.
- Do not infer common knowledge unless the prompt explicitly asks about mutual awareness.

## Common Failure Modes
- Answering the factual state instead of the outer character's belief about the inner character's belief.
- Stopping at first-order belief and missing the recursive layer.
- Confusing second-order belief with evidence update after a reveal.
- Treating shared knowledge as equivalent to recursive belief.

## Minimal Pair
- Case: Sam thinks Priya believes the package is in the locker. | Why: This asks directly for Sam's model of Priya's belief.
- Case: Priya believes the package is in the locker. | Why: This is only a first-order belief about facts, not a belief about another belief.

## Boundary Stress Test
- If the prompt can be answered correctly by naming only the factual location, this is not the right unit.
- If the prompt changes from 'What does A think B believes?' to 'What does B believe?', switch out of this unit.
- If the scene involves shared knowledge but no recursive attribution, do not use this unit.

## Generalization Note
This unit generalizes to any recursive mental-state attribution, including think, believe, know, expect, assume, and imagine, as long as the key variable is one belief nested inside another.
