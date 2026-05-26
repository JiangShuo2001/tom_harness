---
name: macro-02
level: macro
layer: macro
family: "nested-mind"
description: "Direct-route macro for scenes where one character models another character's understanding, including second-order belief and common knowledge."
---

# Second-Order Mind and Common Knowledge

## Use When
- Use when the answer depends on how one character represents another character's belief, ignorance, or likely inference.
- Use when shared knowledge, mutual awareness, or "who knows that who knows" is central to the scene.
- Use when the scene asks where someone thinks another person will look, act, or search.
- Use when nested belief is the deciding factor even if the surface story also contains a false-belief cue.

## Do Not Use When
- Do not use when the main task is only first-order false belief about reality with no model of another mind.
- Do not use when the core issue is appearance versus reality rather than nested belief.
- Do not use when the question is primarily about a nonverbal cue, emotion, pragmatics, or persuasion.
- Do not use when the scene is better explained by a narrower micro capability than nested mindreading.

## Decision Variable
how one character understands another character's understanding

## Direct Route Rule
Route immediately when one mind models another mind or shared knowledge is central.

## Expand With Micro Units
- micro-13
- micro-16
- micro-17
- micro-18

## Trigger Checklist
- One character must reason about another character's belief, expectation, or ignorance.
- The answer changes if you track an embedded belief such as A thinks that B thinks X.
- Shared knowledge, mutual awareness, or public vs private knowledge is relevant to the outcome.
- The scene asks about expected search, expected action, or expected reaction based on another person's mistaken or shared model.
- A first-order belief may be present, but it is not sufficient to answer correctly.

## Workflow
- Identify the outer thinker, the inner target mind, and the proposition being modeled.
- Separate reality from each character's private or shared knowledge state.
- Track whether the key issue is what A believes, what A believes B believes, or what both know.
- Predict the action or answer from the nested mental state, not from reality alone.
- If the scene adds a boundary issue, use the matching micro id only for repair or explanation.

## Special Case
**Common knowledge versus private belief**: When both characters know the same fact and also know that the other knows it, the relevant variable is not simple belief but mutual awareness; answer from the shared epistemic state.

Scene: A and B both saw the keys moved. Later, A wonders where B will search first.
Question: Where does A think B will look?
Answer logic: A knows B saw the move, so A expects B to search the new location rather than the old one; the answer follows B's knowledge as A represents it.

## Boundary Exit Rule
- Exit to macro-01 if the question is only about where X will look based on X's own first-order false belief, with no nested mind.
- Exit to macro-03 if the issue is appearance versus reality and a knowledge boundary, without modeling another person's model.
- Exit to macro-04 if the answer depends on a nonverbal cue's intended meaning rather than nested belief.
- Exit to macro-05 if the answer depends on hidden or atypical emotion rather than nested mindreading.
- Add micro-13 for explicit recursive-belief bookkeeping when the scene nests A-thinks-B-thinks.
- Add micro-16 when the scene turns on whether the fact is mutually known versus privately known.
- Add micro-17 when the inner mind's confidence level (sure, unsure, guessing) drives the answer.
- Add micro-18 when the inner mind's belief depends on source reliability.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
The scene contains embedded belief, such as who thinks what about whom, or whether a fact is mutually known, privately known, or known to be known.
