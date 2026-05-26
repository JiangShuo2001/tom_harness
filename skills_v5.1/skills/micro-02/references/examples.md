# micro-02 Examples and Boundaries

## Decision Variable
which evidence supports the conclusion

## Route Signal
Use this micro unit when the prompt asks what evidence supports a conclusion or requires sorting direct text, inference, and commonsense completion.

## Hard Boundary
- No explanation comparison.
- No bias checking.
- No task routing.
- No scene-level prediction unless it is explicitly framed as evidence support.

## Shortcut To Avoid
- Do not pick the most plausible story and call it evidence.
- Do not treat background knowledge as if it were stated support.
- Do not answer from intuition before separating what is written from what is inferred.

## Common Failure Modes
- Confusing a likely inference with direct evidence.
- Choosing a completion that fits the story but is not text-based.
- Sliding into best-explanation reasoning instead of support tracing.
- Overlooking the difference between what is said and what must be added.

## Minimal Pair
- Case: A passage states that the boy grabbed a coat before leaving because the weather app showed snow. | Why: The question asks which detail supports the conclusion, so the unit identifies the evidence chain behind the conclusion.
- Case: Two possible reasons are given for why the woman left early, and the task asks which reason is more convincing. | Why: This is explanation competition, not evidence-chain construction, so it belongs to micro-03.

## Boundary Stress Test
- If two explanations both fit, do not resolve the dispute here unless the question explicitly asks what supports the conclusion.
- If the support comes from a clue plus commonsense completion, keep the clue and the completion separate.
- If the prompt is mostly about whether the solver is biased, route away to micro-04.

## Generalization Note
This skill generalizes to any case where the main operation is tracing why an answer follows from evidence, especially when direct statements, inferences, and background knowledge are easy to blur.
