---
name: micro-04
level: micro
layer: L0
family: "meta-control"
description: "A meta-control unit for checking whether a current judgment is being distorted by the solver's own perspective, emotional reaction, or moral intuition."
---

# Anti-Bias Check

## Use When
- Use when the task is to audit whether a judgment may be skewed by perspective bias, outcome bias, or a gut-level moral reaction.
- Use when you need to check whether the current reasoning is being distorted by the solver's own viewpoint, sympathies, or intuitive reaction.
- Use when the main question is whether the reasoning process is biased, not what the correct social inference is.

## Do Not Use When
- Do not use when the task is to gather evidence, separate evidence from inference, or decide which clue supports a conclusion; use an evidence-chain unit instead.
- Do not use when the task is to compare multiple plausible explanations; use a multiple-explanation unit instead.
- Do not use when the task is about who can see, hear, or access information, or what is visible from a viewpoint; use perception or spatial-perspective units instead.
- Do not use when the main issue is the character's belief, emotion, intention, or social meaning itself rather than bias in the solver's reasoning.

## Decision Variable
presence of perspective-, outcome-, or moral-intuition distortion in the current reasoning

## Trigger Checklist
- Is the conclusion being driven by my own perspective instead of the scene facts?
- Is an emotional or moral reaction making the answer feel more certain than the evidence allows?
- Am I assuming the outcome should have been obvious just because I now know it?
- Am I checking the quality of the reasoning rather than generating a new explanation?
- Would the judgment change if I stripped away sympathy, blame, or hindsight?

## Workflow
- Identify the current conclusion or reaction that is under review.
- Separate scene facts from the solver's interpretation or gut reaction.
- Ask whether perspective, outcome knowledge, or moral intuition is pushing the answer.
- If bias is present, flag the distortion and suspend the judgment until the reasoning is cleaned up.
- Do not invent a new story; only assess whether the existing reasoning is biased.

## Special Case
**Moral Intuition Override**: If the answer feels morally obvious, first test whether that feeling is actually supported by the evidence or is just a shortcut reaction.

Scene: A person is accused of being selfish, and the solver immediately agrees because the outcome harmed someone.
Question: Should that reaction be trusted?
Answer logic: No. The harmful outcome may trigger blame, but the unit asks whether that blame is distorting judgment. The correct move is to check the evidence before accepting the moral conclusion.

## Boundary Exit Rule
- Exit to micro-05 or micro-11 if you need to decide what a character saw, knew, or believed rather than audit bias.
- Exit to micro-03 if you need to compare competing explanations rather than check for bias.
- Exit to micro-22 or micro-26 if you need to infer intention, emotion, or social meaning from behavior rather than audit bias.
- Stop when the bias check is complete and the substantive answer is now needed.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this unit when the question is whether a judgment, interpretation, or answer is being distorted by the solver's own perspective, hindsight, emotion, or moral intuition.
