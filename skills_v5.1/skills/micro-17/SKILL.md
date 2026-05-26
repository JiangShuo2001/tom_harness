---
name: micro-17
level: micro
layer: L2
family: "belief-models"
description: "Diagnose whether a character is unsure, guessing, doubting, or only partly convinced."
---

# Uncertain Belief

## Use When
- Use when the task asks how sure the character is, not what they think is true.
- Use when the character is guessing, doubting, hedging, or only partly convinced.
- Use when confidence level must be judged separately from the content of the belief.

## Do Not Use When
- Do not use when the main issue is whether new evidence should change the belief; use evidence updating instead.
- Do not use when the main issue is whether a source is trustworthy, credible, or deceptive; use source credibility instead.
- Do not use when the main issue is whether two people share knowledge or know that the other knows; use common knowledge instead.
- Do not use when the task asks what the person wants or prefers; use preference or goal skills instead.

## Decision Variable
the character's subjective certainty

## Trigger Checklist
- Is the question about how sure, unsure, or hesitant the person is?
- Does the scene include words like guess, think maybe, not sure, doubt, probably, maybe, or partially believe?
- Is the belief content already known, while the remaining issue is the strength of conviction?
- Would the answer change if the person were more or less confident without changing the evidence?

## Workflow
- Identify the proposition the character is considering.
- Look for explicit confidence markers, hesitation, or self-reported doubt.
- Separate certainty from evidence strength and source trustworthiness.
- Judge the degree of conviction: confident, uncertain, guessing, or skeptical.
- If the question asks why certainty changed, exit to evidence or credibility skills.

## Special Case
**Partial belief without full commitment**: When a character accepts a claim only tentatively, the answer is still uncertain belief even if they act as if it may be true.

Scene: Mina says, 'I think the meeting is at 3, but I am not fully sure.'
Question: How certain is Mina?
Answer logic: She does not have full conviction. The key variable is her subjective certainty, so the correct diagnosis is partial confidence, not the meeting time or the reliability of her source.

## Boundary Exit Rule
- If the question asks whether the belief should become stronger or weaker after new information, exit to evidence updating.
- If the question asks whether a report, rumor, or speaker is reliable, exit to source credibility.
- If the question asks what someone knows about another person's knowledge, exit to common knowledge or nested belief.
- If the question asks what the person prefers, wants, or intends, exit to goal-action skills.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when the scene centers on a character's level of conviction, doubt, or guessing rather than on truth, evidence, or source quality.
