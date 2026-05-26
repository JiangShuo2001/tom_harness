---
name: micro-35
level: micro
layer: L5
family: "language-pragmatics"
description: "Diagnose the social action an utterance is performing when the wording is indirect, polite, or conventionally used for hinting, requesting, refusing, reminding, or warning."
---

# Indirect Speech Act

## Use When
- Use when the question asks what social act the utterance is performing, not just what it literally says.
- Use when a sentence functions as a request, refusal, warning, reminder, hint, or invitation through indirect wording.
- Use when the key task is to identify the speaker's action in context from the utterance form.

## Do Not Use When
- Do not use when the main question is the sentence's explicit semantic content; use Literal Meaning instead.
- Do not use when the main question is what extra implied information is conveyed but the act itself is not in question; use Conversational Implicature instead.
- Do not use when the main question is whether the statement is true, false, or deceptive; use Truth, Lie, and Half-Truth instead.
- Do not use when the scene requires diagnosing emotion, belief, or intention apart from the act performed.

## Decision Variable
the social action the utterance is performing

## Trigger Checklist
- Is the utterance indirect rather than direct?
- Is the answer a speech act like request, refusal, warning, reminder, hint, or invitation?
- Would the literal sentence mislead if taken as the whole answer?
- Is context needed to identify what the speaker is doing socially?

## Workflow
- First identify the literal sentence meaning.
- Then ask what communicative action the speaker is performing in context.
- Map the utterance to the most specific speech act that fits the scene.
- Ignore extra implied content unless it is needed to identify the act itself.

## Special Case
**Polite indirect request**: When a statement is phrased as a comment, need, or question but functions as a request, answer with the request act, not the literal content or the implied inconvenience.

Scene: A says to B, 'It's getting cold in here.' B is near the window.
Question: What is A doing socially?
Answer logic: The literal content is about temperature, but in context A is performing an indirect request for B to close the window or help fix the draft.

## Boundary Exit Rule
- Exit to micro-34 Literal Meaning if the question is about what the sentence explicitly says rather than what it is doing socially.
- Exit to micro-36 Conversational Implicature if the question is about hidden extra meaning conveyed beyond the act being performed.
- Exit to micro-37 Truth, Lie, and Half-Truth or micro-38 Misleading and Selective Expression if truth, deception, or speaker sincerity is the main target.
- Exit to micro-39 Speaker Motivation if the diagnostic target is the social motive for choosing those words rather than the act performed.
- Exit to a belief, desire, or emotion unit if the scene is better described as belief, desire, or emotion inference without an utterance-act focus.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when an utterance must be classified by its social function in context, especially for indirect requests, refusals, reminders, warnings, hints, or invitations.
