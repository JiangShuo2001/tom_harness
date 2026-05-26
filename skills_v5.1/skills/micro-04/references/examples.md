# micro-04 Examples and Boundaries

## Decision Variable
whether the current judgment is being skewed by bias

## Route Signal
Use this unit when the question is whether a judgment, interpretation, or answer is being distorted by the solver's own perspective, hindsight, emotion, or moral intuition.

## Hard Boundary
- Does not identify what actually happened in the scene.
- Does not decide which explanation is true.
- Does not check perceptual access or viewpoint visibility.
- Does not infer belief, desire, or emotion as the primary task.

## Shortcut To Avoid
- Do not treat a strong moral feeling as proof.
- Do not let the known outcome make the earlier reasoning look easier than it was.
- Do not confuse bias checking with explanation generation.

## Common Failure Modes
- Outcome bias: judging the reasoning by how things ended.
- Perspective bias: assuming others should know what the solver knows.
- Moral-intuition shortcut: accepting blame or innocence before checking evidence.

## Minimal Pair
- Case: A solver says an actor must have been careless because the result was bad. | Why: This is a direct bias check: the question is whether the bad outcome is unfairly driving the judgment.
- Case: A solver notices that two explanations are both possible and asks which one best fits the clues. | Why: This is close but not the same; it is explanation comparison, not bias auditing.

## Boundary Stress Test
- If the answer becomes stronger only because you already know the ending, the unit applies.
- If the problem requires new evidence, new inference, or a new explanation, the unit does not apply.
- If the question is about visibility, knowledge access, or belief content, route elsewhere.

## Generalization Note
Use this only as a reasoning-quality filter. It should help detect distortions in judgment, not replace substantive social inference.
