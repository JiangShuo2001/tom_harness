---
name: micro-42
level: micro
layer: L6
family: "norms-relationships"
description: "Diagnose whether an act or remark breaches social tact and creates embarrassment or offense."
---

# Faux Pas and Offense

## Use When
- Use when the question asks whether a behavior, remark, or disclosure is socially appropriate in the current setting.
- Use when the key judgment is whether the act would reasonably embarrass, offend, or make others uncomfortable.
- Use when the scene is about tact, decorum, or an awkward social breach rather than blame, repair, or persuasion.

## Do Not Use When
- Do not use when the main question is who caused harm, whether harm was intentional, or whether blame is deserved.
- Do not use when the main task is to repair, apologize, reconcile, or manage the relationship after the breach.
- Do not use when the issue is adapting a message to the listener's level, identity, or knowledge; use audience calibration instead.
- Do not use when the issue is influence, negotiation, fairness, or reciprocity rather than social tact.

## Decision Variable
whether the act violates expected social tact enough to embarrass or offend

## Trigger Checklist
- Is the prompt asking if something was rude, awkward, inappropriate, embarrassing, or offensive?
- Is there a social norm for the setting that the act may have crossed?
- Would a reasonable observer see the act as a tact breach, even if no one was harmed?
- Is intent secondary to social appropriateness?

## Workflow
- Identify the relevant setting, audience, and social norm.
- Ask whether the act crosses a tact boundary for that setting.
- Judge likely embarrassment or offense from the viewpoint of others present.
- Return the faux pas judgment without shifting to blame, repair, or persuasion.

## Special Case
**Accidental private disclosure**: If someone reveals private, sensitive, or socially delicate information in the wrong setting, classify it as a faux pas even when the speaker did not mean harm; if the question asks about fault, blame, or apology, switch out of this unit.

Scene: At a dinner party, someone casually mentions another guest's recent breakup in front of everyone.
Question: Was that inappropriate?
Answer logic: Yes. The key variable is social tact: the comment exposes private information in a setting where it is likely to embarrass the person, so it is a faux pas even if unintentional.

## Boundary Exit Rule
- Exit to micro-43 if the question turns on responsibility, intentional harm, or blameworthiness.
- Exit to micro-49 if the question is about how to apologize, repair, or restore the relationship.
- Exit to micro-40 if the question is about tailoring speech to the listener's expertise, age, identity, or stance.
- Exit to micro-44 or micro-51 if the question is about negotiation, fairness, reciprocity, or strategic influence.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use when a behavior or remark is being judged for social appropriateness, tact, embarrassment, or offense, especially in front of an audience.
