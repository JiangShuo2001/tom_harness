# micro-01 Examples and Boundaries

## Decision Variable
the target psychological or social variable the question asks about

## Route Signal
Use when the question is about selecting the right social-cognitive lens or capability entry point, not solving the underlying scene.

## Hard Boundary
- No scene solving.
- No evidence ranking.
- No explanation comparison.
- No final belief, emotion, intention, or action inference.

## Shortcut To Avoid
- Do not jump straight to the story outcome.
- Do not confuse variable selection with answer generation.
- Do not overfit to a benchmark-style label when the prompt only asks for the relevant mental or social factor.

## Common Failure Modes
- Answering the substantive question instead of naming the variable.
- Picking too broad a label like social reasoning when the prompt asks for a specific mental-state type.
- Treating evidence evaluation as routing.
- Confusing this with explanation comparison.

## Minimal Pair
- Case: The prompt asks whether a story is about belief, desire, or intention. | Why: The task is to identify the variable being tested before any scene reasoning.
- Case: The prompt asks where a character will search after an object was moved. | Why: This is a substantive false-belief question, so the answer is not routing but direct scene solving.

## Boundary Stress Test
- If the prompt contains clear social content but asks only what kind of inference is needed, stay here.
- If the prompt asks who knows what, who wants what, or what happened, do not stay here.
- If two different skills seem plausible, identify the variable first and then exit.

## Generalization Note
This skill generalizes across benchmark items and real-world scenes by selecting the correct mental or social variable before any deeper inference.
