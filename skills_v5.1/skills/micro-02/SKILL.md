---
name: micro-02
level: micro
layer: L0
family: "meta-control"
description: "Separates text evidence, inference, and commonsense completion to identify what supports a conclusion."
---

# Evidence-Chain Construction

## Use When
- Use when the task asks which statement or clue supports a conclusion from the text.
- Use when you must separate direct evidence, inferred support, and commonsense completion.
- Use when the main job is to trace the evidential chain behind an answer, not to choose among rival explanations.

## Do Not Use When
- Do not use when the task is selecting the best explanation among several plausible interpretations; that is micro-03.
- Do not use when the issue is only identifying the question type or required mental variable; that is micro-01.
- Do not use when the main problem is bias correction, perspective distortion, or moral shortcut checking; that is micro-04.
- Do not use when the question asks for the final answer directly without asking what supports it.

## Decision Variable
which evidence supports the conclusion

## Trigger Checklist
- The question asks for support, proof, or backing for a conclusion.
- You can separate the prompt into text evidence, inference, and outside knowledge.
- The answer depends on whether a statement is directly stated, implied, or just commonsense completion.
- You are not being asked to compare competing narratives or judge which explanation is best.

## Workflow
- Identify the conclusion being tested.
- List what is directly stated in the text.
- Mark what is inferred from the text versus supplied by commonsense.
- Choose the evidence that actually supports the conclusion, not the explanation that feels most complete.
- If the support comes only from outside knowledge, treat it as completion, not textual evidence.

## Special Case
**Commonsense completion is not text evidence**: If the answer only works after adding unstated world knowledge, label it as inference or completion rather than direct evidence.

Scene: A story says Maya looked outside, saw dark clouds, and carried an umbrella.
Question: What evidence supports the conclusion that Maya expected rain?
Answer logic: The dark clouds and umbrella are the support. The expectation of rain is an inference built from those clues, not a separately stated fact.

## Boundary Exit Rule
- Exit to micro-03 if the task asks which explanation is best or requires comparing multiple plausible interpretations.
- Exit to micro-01 if the task is only about identifying the relevant skill, variable, or question type.
- Exit to micro-04 if the main issue is whether your own intuition, bias, or moral reaction is distorting the judgment.
- Stop when the diagnostic is complete and the substantive answer is now needed.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when the prompt asks what evidence supports a conclusion or requires sorting direct text, inference, and commonsense completion.
