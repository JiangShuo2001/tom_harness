---
name: skill12
description: Use for HT-01 indirect speech meaning — the speaker says something polite or vague and the task asks what they really mean (request, complaint, warning, refusal, reminder, invitation).
---

# HT-01 Indirect Speech Meaning

## Use When

- The speaker says something indirect and the task asks what they
  really mean.
- The correct answer is an underlying speech act such as request,
  complaint, warning, refusal, reminder, or invitation.
- The listener is expected to infer more than the literal words.

## Do Not Use When

- The task asks for a *persuasion strategy* to influence someone. Use
  `skill13`.
- The task is about a nonverbal cue rather than spoken language. Use
  `skill7`.
- The task is about statement *truth* or *motive* for nonliteral speech
  in Strange-Story style. Use `skill14` or `skill15`.

## Trigger Checklist

- Is the literal sentence weaker, vaguer, or more polite than the real
  intended act?
- Does the context reveal a concrete hidden need, complaint, or
  desired action?
- Is the question asking for the speaker's real meaning or intended
  listener response?
- If yes, use this skill.

## Workflow

1. Identify the literal utterance and the listener.
2. Identify the immediate problem, desire, obstacle, or social
   pressure.
3. Translate the utterance into its hidden speech act using the
   surface-vs-strategy decoder below.
4. State the concrete action, recognition, or change the speaker wants
   from the listener.
5. Prefer **functional meaning** over paraphrasing surface wording.
6. If options are provided, choose the option that best matches the
   intended speech act.

## Detailed Procedure — Surface vs Strategy Decoder

```
LAYER 1 — SURFACE
Quote the literal sentence.

LAYER 2 — CONTEXT
What is the immediate problem in the scene? (Open window in winter,
guest waiting too long, child making noise, dish that's been finished,
…) What does the speaker stand to gain or lose by being indirect?

LAYER 3 — HIDDEN SPEECH ACT — match the situation to a known pattern:
  • Request   : surface = polite observation  → "please do X"
  • Complaint : surface = mild remark         → "I don't like Y"
  • Warning   : surface = casual mention      → "be careful about Z"
  • Refusal   : surface = vague excuse        → "no, I won't"
  • Reminder  : surface = neutral fact        → "remember to do W"
  • Invitation: surface = open observation    → "come join V"
  • Hint/Sarcasm : surface ≠ literal meaning  → indirect criticism

DECISION RULE
Pick the option whose meaning advances the speaker's local need, NOT
the option that paraphrases the surface words.
```

## Output Template

- `Task framing`: literal utterance and target listener.
- `Context evidence`: the local problem or desire that motivates
  indirectness.
- `Reasoning decision`: the hidden speech act.
- `Answer`: what the speaker really means or wants.

## Failure Checks

- Do not just restate the surface wording.
- Prefer action-oriented or function-oriented interpretations.
- Match the social function of the utterance, not just its topic.
- Distinguish request, complaint, refusal, reminder, and warning.

## Boundary Exit Rule

- If the task asks how to persuade someone, route to `skill13`.
- If the task is about a smile, nod, glance, or nudge, route to
  `skill7` or `skill6`.
- If the question is about whether the statement is true or why it was
  said under mixed motives, route to `skill14` or `skill15`.

## Answer Discipline

- Infer the hidden speech act first, then choose the response that
  best captures that act.
- Reject options that merely paraphrase the words without recovering
  the intended listener effect.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
