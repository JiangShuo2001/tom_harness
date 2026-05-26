---
name: micro-01
level: micro
layer: L0
family: "meta-control"
description: "Identify the psychological or social variable the prompt is actually asking for, without solving the substantive scene."
---

# Task Routing

## Use When
- Use when the prompt is asking what kind of mental, social, or pragmatic variable must be identified before solving.
- Use when you need to name the entry point such as belief, desire, intention, emotion, norm, trust, privacy, audience, or evidence type.
- Use when the task is to route the question to the right capability rather than answer the scene directly.
- Use when the stem asks "what is being tested" or "which capability applies" rather than asking for a scene answer.

## Do Not Use When
- Do not use when the prompt asks for the actual answer to the scene, such as what someone believes, feels, wants, says, knows, or will do.
- Do not use when the task is to weigh evidence, support a conclusion, or separate text from inference; use evidence-chain work instead.
- Do not use when the task is to compare several plausible explanations; use explanation competition instead.
- Do not use when the question is already clearly inside a specific micro skill and no routing decision is needed.

## Decision Variable
the target psychological or social variable the question asks about

## Trigger Checklist
- The prompt is asking what kind of thing is being tested, not what happened.
- You can name the answer as a variable category before any scene reasoning.
- More than one substantive skill could apply, so the first job is to choose the right lens.
- The key choice is the capability entry point, not the scene outcome.

## Workflow
- Read the question stem and identify the requested output type.
- Strip away story details and ask what variable would make the answer possible.
- Label the target variable at the right abstraction level, such as belief, desire, intention, emotion, norm, trust, or pragmatic meaning.
- If the prompt is actually asking for evidence, competing explanations, or scene resolution, exit to the neighboring skill instead of continuing here.

## Special Case
**Meta-question about the task itself**: If the prompt asks what the question is asking, answer only with the target variable category and do not infer the scene content.

Scene: A story describes two people arguing, and the question asks whether this is mainly about what one person knew, what one person wanted, or what one person intended.
Question: What is the question really asking for?
Answer logic: Do not solve the argument. Identify the target variable as the mental-state type being tested, then route to the matching substantive skill.

## Boundary Exit Rule
- Exit immediately once the target variable is named.
- If the next step is to judge truth, belief, emotion, intention, evidence, or outcome, hand off to the relevant substantive micro skill.
- If the task asks which evidence supports a conclusion, use evidence-chain construction instead.
- If the task asks which explanation best fits, use multiple-explanation competition instead.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use when the question is about selecting the right social-cognitive lens or capability entry point, not solving the underlying scene.
