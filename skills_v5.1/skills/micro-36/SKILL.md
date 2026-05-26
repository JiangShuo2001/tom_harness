---
name: micro-36
level: micro
layer: L5
family: "language-pragmatics"
description: "Diagnostic micro skill for inferring the unstated extra meaning a speaker communicates from context."
---

# Conversational Implicature

## Use When
- Use when the question asks what extra meaning was communicated by context, beyond the literal sentence.
- Use when the answer depends on the implicit information the listener is expected to infer from the situation, wording, or conversational context.

## Do Not Use When
- Do not use when the task is to identify the social act being performed by the utterance, such as requesting, warning, refusing, reminding, or hinting; that is indirect speech act.
- Do not use when the task is to judge whether the sentence is true, false, misleading, or a lie; that is truth/lie or misleading expression.
- Do not use when the key issue is who believes what, who saw what, or what someone intends to do rather than what extra meaning was conveyed.

## Decision Variable
the unstated meaning inferred from context

## Trigger Checklist
- The utterance is literally incomplete, too weak, or oddly phrased unless context is used.
- The question asks what the speaker meant beyond the words actually said.
- The answer is an inferred proposition, not the speech act itself and not the truth value of the sentence.
- The listener must combine wording, shared expectations, and scene context to recover the extra message.

## Workflow
- Identify the literal sentence meaning first.
- Ask what additional proposition a cooperative listener is meant to infer.
- Use context, relevance, and conversational expectations to derive the unstated message.
- Return only the implied content, not the act being performed and not whether the sentence is true.

## Special Case
**Scalar implicature**: When a weaker term is used on a natural scale, the implicature may be the stronger excluded alternative, if context supports it.

Scene: A parent asks, 'Did you eat all the cookies?' The child says, 'I ate some.'
Question: What is implied?
Answer logic: Literal meaning: at least some cookies were eaten. In this context, the extra communicated meaning is that not all cookies were eaten.

## Boundary Exit Rule
- Exit to micro-34 Literal Meaning if the question is about the explicit content of the words, not the extra message.
- Exit to micro-35 Indirect Speech Act if the question is about what social action the utterance performs rather than what extra proposition it conveys.
- Exit to micro-37 Truth, Lie, and Half-Truth if the question asks whether the utterance is factually true or false.
- Exit to micro-38 Misleading and Selective Expression if the question is whether a true statement is steering the listener toward a false belief.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use when a scene asks what is communicated implicitly by an utterance, especially when the words alone do not fully answer the question.
