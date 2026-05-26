---
name: micro-54
level: micro
layer: L7
family: "quantity-probability"
description: "Estimate how observed sample evidence should revise a quantity judgment while keeping base rates, vague language, and causal explanations separate."
---

# Quantity Update After Partial Observation

## Use When
- Use when a character or reasoner sees only part of a set, group, container, sequence, or population and must revise an estimate about the whole.
- Use when the answer depends on how many, how much, or what proportion is suggested by sampled observations.
- Use when a prior quantity estimate is changed by concrete sampled evidence, such as several checked items, a few observed people, or a partial count.
- Use when the question asks what someone should now expect after looking at some cases but not all cases.

## Do Not Use When
- Do not use when the only issue is interpreting a vague quantifier such as 'some,' 'most,' or 'almost none' without new observation; use micro-53.
- Do not use when the answer mainly depends on background commonness, typical category frequency, or a known base rate rather than a sample just observed; use micro-55.
- Do not use when the task is to identify what caused an outcome, even if quantities are mentioned; use micro-56.
- Do not use when the main problem is hierarchy, role permission, escalation, or power-sensitive communication; use micro-52.
- Do not use when the question asks for exact arithmetic from complete information rather than estimate revision from partial observation.

## Decision Variable
sample-driven quantity revision

## Trigger Checklist
- A quantity, proportion, frequency, or amount is unknown or initially uncertain.
- Only part of the relevant set has been observed, checked, counted, or sampled.
- The observed subset provides evidence about the unobserved remainder.
- The question asks for an updated estimate, expectation, likelihood, or judgment about the whole.
- The sample's representativeness, size, and direction are more important than social status, blame, or language politeness.

## Workflow
- Identify the target quantity: what amount, count, proportion, or frequency is being estimated.
- Separate the prior expectation from the new sample evidence, if a prior is given.
- Describe the sample: how many cases were observed, what was found, and whether the sample was selected randomly, conveniently, or in a biased way.
- Update cautiously: stronger samples shift the estimate more; tiny or biased samples shift it less.
- Preserve uncertainty about the unobserved cases instead of treating the sample as a complete count.
- Answer in the form requested: revised estimate, likely range, comparison, or qualitative expectation.

## Special Case
**Biased or non-representative sample**: If the observed sample was selected in a way that overrepresents one kind of case, use it as weak evidence and avoid projecting it directly to the whole group.

Scene: A teacher wants to know whether most students finished the homework. She asks the three students sitting in the front row, and all three say yes.
Question: Should she now think almost everyone finished?
Answer logic: The sample points toward some completion, but it is small and may be biased because front-row students may be more prepared. Her estimate should rise only modestly, not jump to 'almost everyone.'

## Boundary Exit Rule
- Exit to micro-53 if the problem is only about what a phrase like 'most,' 'a few,' or 'about half' means, with no sampled observation changing the estimate.
- Exit to micro-55 if the evidence is mainly a stable base rate, stereotype of category frequency, or typicality judgment rather than observed partial cases.
- Exit to micro-56 if the central question is why an outcome happened or which factor produced it.
- Exit to a macro quantity route when the scene requires multiple quantity operations, such as interpreting a vague prior, updating from evidence, and comparing final estimates.
- Do not force this unit when the observed information is complete; complete counts require direct calculation, not partial-observation updating.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when partial sampled evidence should change an estimate about a larger unobserved quantity.
