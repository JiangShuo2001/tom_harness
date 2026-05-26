# macro-14 Examples and Boundaries

## Decision Variable
how to estimate under vague quantities, samples, and base rates

## Route Signal
The prompt contains vague quantity language, incomplete evidence, sampled data, or a request for the best estimate, likelihood, or count.

## Hard Boundary
- Not causal attribution
- Not belief tracking
- Not emotion inference
- Not viewpoint or visibility reasoning
- Not pragmatic meaning repair
- Not trust or relationship judgment

## Shortcut To Avoid
- Do not explain the answer as a motive, intention, or hidden belief when the question is numeric or probabilistic.
- Do not jump from one small clue to certainty when the scene only supports a best estimate.
- Do not confuse a social estimate with an emotional or moral judgment.

## Common Failure Modes
- Overweighting one visible sample and ignoring the base rate.
- Answering with a causal story instead of an estimate.
- Treating uncertainty as ignorance when the task only requires the most likely value.
- Using a relational or emotional macro when the core is numerical approximation.
- Giving an exact count when the scene only supports a rough estimate.

## Minimal Pair
- Case: A jar is partly visible and the question asks for the best estimate of how many items are inside. | Why: The core task is quantity estimation from partial observation.
- Case: A small survey gives a few responses and the question asks how likely the larger group is to agree. | Why: The core task is probability estimation from a sample and base rate.

## Boundary Stress Test
- If the scene asks why the person acted that way, it is not this macro.
- If the scene asks what someone believes another person saw or knew, it is not this macro.
- If the scene asks whether a remark was rude or embarrassing, it is not this macro.
- If the scene asks for a numerical guess plus a hidden intention, solve the estimate here only if the estimate is the main question.

## Generalization Note
This macro covers robust estimation across benchmark-style partial-information items and real-world judgments where people must infer rough quantities, rates, or likelihoods without full data.
