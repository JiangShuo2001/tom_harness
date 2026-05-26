---
name: macro-15
level: macro
layer: macro
family: "relationships"
description: "Direct-route macro for judging trust, reputation, identity, role, and relationship decisions from long-term interaction history."
---

# Trust, Relationship, and Long-Term Interaction

## Use When
- Use when the question depends on a person's reputation, reliability, loyalty, role, or history with others.
- Use when past interactions change how the character should be judged now.
- Use when long-term relationship context matters more than a single statement, single event, or one-time credibility cue.
- Use when the scene asks who to trust, how to interpret behavior in a relationship, or how history should affect future interaction.

## Do Not Use When
- Do not use when the core issue is a live misunderstanding that should be clarified immediately in conversation.
- Do not use when the main issue is apology, compensation, or repairing damage after an offense.
- Do not use when the case is mainly about spatial perspective, quantity estimation, or a one-off belief update without relationship history.
- Do not use when the task is only to judge whether one statement is true from a single source of evidence.

## Decision Variable
how long-term history affects trust, reputation, identity, role, and relationship judgment

## Direct Route Rule
Route immediately when trust, reputation, identity, role, or long-term relational history matters.

## Expand With Micro Units
- micro-18
- micro-44
- micro-45
- micro-46
- micro-47
- micro-56

## Trigger Checklist
- The scene mentions past behavior, repeated interaction, or a known track record.
- The answer depends on whether someone is trustworthy, loyal, reliable, or credible over time.
- A relationship label, social role, or reputation changes the interpretation of the current event.
- The question is about how to treat someone now based on history, not just the current utterance.
- There is a distinction between temporary behavior and stable relational pattern.

## Workflow
- Identify the long-term relationship variable: trust, loyalty, reputation, identity, or role.
- Collect the history signal: repeated actions, prior promises, known patterns, and social standing.
- Weigh history over isolated surface cues unless the scene explicitly overrides history.
- Infer the most reasonable relationship judgment or action based on accumulated evidence.
- If the case is actually about a narrower sub-skill such as credibility, apology, or live clarification, exit to the relevant micro or neighboring macro.

## Special Case
**Mixed history with one new event**: When a single new event conflicts with a long record, the long-term pattern usually sets the baseline unless the scene states a decisive rupture, verified betrayal, or formal role change.

Scene: A coworker has been dependable for years but misses one deadline after a family emergency.
Question: Should their reliability be judged as bad now?
Answer logic: Use the long-term record as the main signal. The one missed deadline is a temporary exception, not enough by itself to replace the established trust pattern.

## Boundary Exit Rule
- Exit to macro-08 / micro-37 if the task is really about whether one statement is true or false from a single source.
- Exit to macro-17 if the scene is a repair conversation, apology, or reconciliation after harm.
- Exit to macro-16 if the main issue is clarifying a misunderstanding in real time.
- Exit to macro-19 if the question is about first impression only and no relationship history is available.
- Exit to macro-01 / macro-07 / macro-20 if another macro better captures the core (false belief, indirect meaning, or power-distance communication).
- Add micro-18 when single-source credibility within a longer relationship is the deciding factor.
- Add micro-44 when fairness or reciprocity history controls the judgment.
- Add micro-45 when long-term reliability or reputation must be diagnosed.
- Add micro-46 when the role or status structure of the relationship matters.
- Add micro-47 when group identity changes how history is read.
- Add micro-56 when causal attribution across the history is required.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Long-term history, reputation, loyalty, trustworthiness, role, or identity determines the answer.
