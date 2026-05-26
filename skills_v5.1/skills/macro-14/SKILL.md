---
name: macro-14
level: macro
layer: macro
family: "estimation"
description: "Direct-route macro for estimating quantities, probabilities, or best guesses from partial evidence, vague counts, or base rates."
---

# Quantity, Probability, and Social Estimation

## Use When
- Use when the scene asks for a count, amount, proportion, likelihood, or best estimate under incomplete or noisy evidence.
- Use when the main task is to update a guess from a sample, a base rate, or partial observation.
- Use when a social judgment is framed as an estimate rather than a causal, emotional, or relational inference.
- Use when the question is about how many, how much, how likely, or which option is more probable.

## Do Not Use When
- Do not use when the real task is causal attribution, such as why an event happened or who caused it.
- Do not use when the scene is mainly about belief, intention, emotion, language meaning, trust, or social repair.
- Do not use when spatial viewpoint, visibility, or perspective taking is the core problem.
- Do not use when the question is primarily about offense, embarrassment, or faux pas rather than estimation.

## Decision Variable
how to estimate under vague quantities, samples, and base rates

## Direct Route Rule
Route immediately when vague quantities or partial observation require estimation or update.

## Expand With Micro Units
- micro-53
- micro-54
- micro-55

## Trigger Checklist
- The question asks for an approximate number, amount, rate, or probability.
- Only part of the relevant evidence is visible, sampled, or known.
- A base rate, prior frequency, or small sample must be turned into a best estimate.
- The answer should be the most likely estimate, not a narrative explanation.
- The scene does not hinge on who believes what, who saw what, or what someone meant.

## Workflow
- Identify the target quantity: count, amount, proportion, or probability.
- Separate observed evidence from hidden total population, unseen cases, or prior base rate.
- Check whether the question asks for a point estimate, a comparison, or a likely range.
- Use the strongest available evidence without overfitting a tiny sample.
- If the evidence is partial, return the best estimate that balances sample clues and prior frequency.
- State the answer as the most probable value or the most defensible approximation.

## Special Case
**Small sample versus base rate**: When a tiny sample conflicts with a stable base rate, prefer the base rate unless the sample is clearly diagnostic or the prompt explicitly asks for the sample-only estimate.

Scene: A manager sees only two customer reviews, both positive, but knows the product category is usually mixed.
Question: How likely is the product to be broadly well received?
Answer logic: Do not treat two positive reviews as decisive. Combine the small sample with the broader category base rate, then give the most likely moderate estimate rather than an extreme conclusion.

## Boundary Exit Rule
- Exit to a causal macro / micro-56 if the question is really about why something happened, not how likely or how many.
- Exit to macro-01 / macro-02 / macro-05 / macro-07 if the answer depends on belief, intention, emotion, or communication meaning rather than estimation.
- Exit to macro-13 if the key issue is perspective, visibility, or who noticed what.
- Exit to macro-15 / macro-17 / macro-12 if the scene is better handled by trust history, apology, or embarrassment.
- Add micro-53 when interpreting a vague quantifier ("a few", "most", "almost half").
- Add micro-54 when sample observations must be turned into a population estimate.
- Add micro-55 when a base rate or category typicality drives the answer.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
The prompt contains vague quantity language, incomplete evidence, sampled data, or a request for the best estimate, likelihood, or count.
