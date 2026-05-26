---
name: macro-16
level: macro
layer: macro
family: "dialogue-misunderstanding-repair-and-clarification"
description: "Route here when a live conversational misunderstanding must be clarified on the spot."
---

# Dialogue Misunderstanding Repair and Clarification

## Use When
- Use when two speakers are in an active conversation and one utterance has been misunderstood, misread, or ambiguously interpreted.
- Use when the best move is immediate clarification, restatement, or a check for shared meaning.
- Use when the scene is about resolving what was meant right now, not repairing relationship damage later.
- Use when the key task is to detect a mismatch between intended meaning and received meaning in real time.

## Do Not Use When
- Do not use when the main issue is apology, compensation, or relationship repair after offense or harm.
- Do not use when the scene is mainly about persuasion, negotiation, or audience calibration rather than misunderstanding.
- Do not use when the question is about truth, lying, or concealment instead of live clarification.
- Do not use when the problem is a long-term trust or identity judgment rather than a momentary conversational mismatch.

## Decision Variable
how to detect and clarify a live misunderstanding in conversation

## Direct Route Rule
Route immediately when the scene is a live conversational misunderstanding that can be clarified on the spot.

## Expand With Micro Units
- micro-36
- micro-40
- micro-48

## Trigger Checklist
- A speaker says something that is taken the wrong way, or the listener shows confusion.
- The scene includes a repair move such as 'What do you mean?', 'I meant...', 'No, I said...', or a restatement.
- The correct answer depends on what the speaker intended versus what the listener heard.
- The misunderstanding can be fixed immediately through clarification, not by apology or mediation.
- The key uncertainty is conversational meaning, reference, or interpretation in the moment.

## Workflow
- Identify the utterance or gesture that caused the mismatch.
- Determine whether the problem is ambiguity, wrong reference, wrong implication, or wrong assumption.
- Infer the most likely intended meaning from context and conversational goals.
- Choose the clarifying response: ask a clarifying question, restate the meaning, or correct the misread.
- Confirm the shared interpretation and stop once the conversation is aligned.
- If the scene has harm, embarrassment, or offense beyond simple confusion, exit to apology or social repair skills.

## Special Case
**Ambiguous reference with no damage**: If the misunderstanding is only about who, what, where, or which item was meant, resolve it with a neutral clarifying question or precise restatement; do not add apology or moral interpretation unless the scene explicitly includes harm.

Scene: One person says, 'Put it on the table,' and the listener is not sure whether 'it' means the keys, the box, or the bag. The speaker is still present and can clarify immediately.
Question: What should the listener do?
Answer logic: This is a live ambiguity, so the correct move is to ask for clarification or use surrounding context to identify the referent. The scene is about shared meaning, not apology, offense, or persuasion.

## Boundary Exit Rule
- Exit to macro-17 if the scene shifts from clarification to apology after hurt, embarrassment, or offense.
- Exit to macro-09 / macro-18 if the main task becomes strategic persuasion, negotiation, or audience adaptation.
- Exit to macro-08 if the core question is whether a statement is true, deceptive, or ironic rather than simply misunderstood.
- Exit to macro-07 if the misunderstood content is an indirect speech act and the issue is what the utterance was performing.
- Add micro-36 when conversational implicature is the source of the mismatch.
- Add micro-40 when audience calibration must be repaired (level, identity, stance).
- Add micro-48 when the misread involves a private or sensitive disclosure.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
The conversation contains an immediate sign of confusion, correction, or repair: 'What do you mean?', 'No, I meant...', 'I thought you said...', or a direct restatement to align meaning.
