---
name: micro-37
level: micro
layer: L5
family: "language-pragmatics"
description: "Evaluate whether an utterance's explicit content is true, false, or only partly supported by the known facts."
---

# Truth, Lie, and Half-Truth

## Use When
- Use when the question asks whether a stated claim matches the facts available in the scene.
- Use when the answer depends on classifying explicit utterance content as true, false, partly true, or unsupported.
- Use when a character says something and the task is to compare the wording against what actually happened or what is actually the case.
- Use when a half-truth must be identified because the utterance contains both accurate and inaccurate explicit content.

## Do Not Use When
- Do not use when the main issue is whether the speaker intended to mislead; route to speaker motivation or misleading expression instead.
- Do not use when the statement is literally true but creates a false impression through omission or framing; route to Misleading and Selective Expression.
- Do not use when the question asks what the speaker implied beyond the literal words; route to Conversational Implicature.
- Do not use when the question asks what social act the utterance performs, such as requesting, warning, refusing, or hinting; route to Indirect Speech Act.
- Do not use when the truth depends on what a character believes rather than what is factually true; first route to the relevant belief or knowledge unit.

## Decision Variable
truth status of explicit content

## Trigger Checklist
- There is a specific utterance, claim, answer, promise, report, or description to evaluate.
- The scene provides facts that can be compared against the utterance.
- The question asks whether the utterance is true, false, accurate, inaccurate, a lie, or a half-truth.
- The needed judgment concerns the words stated, not the hidden motive or listener interpretation.
- The utterance can be decomposed into one or more explicit propositions.

## Workflow
- Quote or paraphrase only the explicit content that was asserted.
- Separate the utterance into atomic factual propositions if it contains multiple claims.
- List the relevant scene facts that bear directly on each proposition.
- Compare each proposition with the facts: mark it true, false, unsupported, or partly true.
- Classify the whole utterance: true if all central explicit claims match the facts, false if a central claim conflicts with facts, half-truth if explicit content mixes true and false or materially incomplete asserted claims.
- Do not infer deception, politeness, or strategic motive unless the question separately asks for it.

## Special Case
**Literally true but misleading**: If every explicit claim is true but the wording predictably leads the listener to a false conclusion, this unit may say the literal content is true, then exit to micro-38 for the misleading effect.

Scene: Maya ate the last cookie after Ben left. When Ben asks, 'Did you eat the cookies this morning?', Maya says, 'I ate one cookie before lunch.' She did eat one cookie before lunch, but it was also the last cookie.
Question: Was Maya's statement true?
Answer logic: The explicit content 'I ate one cookie before lunch' matches the facts, so its truth status is true. Whether it misleads Ben about the last cookie is a separate micro-38 question.

## Boundary Exit Rule
- If the explicit words are already classified and the remaining question is why the speaker chose them, exit to micro-39.
- If the explicit words are true but the listener is guided toward a wrong inference, exit to micro-38.
- If the answer requires adding unstated contextual meaning, exit to micro-36.
- If the utterance functions mainly as a request, warning, refusal, reminder, or invitation, exit to micro-35.
- If the relevant comparison is between a character's belief and reality rather than a statement and reality, exit to the appropriate belief or knowledge unit before using this one.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when the diagnostic target is the factual accuracy of what was explicitly said.
