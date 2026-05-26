# micro-15 Examples and Boundaries

## Decision Variable
the direction of belief change caused by newly available evidence

## Route Signal
Use this micro unit when a case asks how a new observation or disclosure changes belief, and the main output is the direction of the update.

## Hard Boundary
- Not source credibility, deception, or trustworthiness.
- Not second-order belief or common knowledge.
- Not appearance-reality as such.
- Not certainty level or doubt level.

## Shortcut To Avoid
- Do not jump from 'new information' to 'truth' without checking whether the question is about belief update.
- Do not infer from source trust unless the prompt explicitly asks about credibility.
- Do not confuse 'knowing the evidence' with 'knowing the answer'.

## Common Failure Modes
- Answering with the true state instead of the changed belief.
- Treating a weak clue as a full conclusion.
- Mixing update direction with source trustworthiness.
- Recasting an update question as a common-knowledge or recursive-belief question.

## Minimal Pair
- Case: A child thinks the gift is in the box, then hears the box was moved to the closet. | Why: The new information changes the child's belief about the likely location, so the update direction is the key variable.
- Case: A person hears a rumor from an unreliable gossip source. | Why: If the question is whether to trust the rumor source, the main issue is credibility, so this micro unit does not apply.

## Boundary Stress Test
- A clue appears that is true but only partly informative: ask only for the direction of belief change, not the final certainty.
- A speaker gives evidence while also being suspicious: if credibility is the question, switch away from this unit.
- A character learns something and also learns that others know it: that is no longer pure evidence updating.

## Generalization Note
This unit covers any case where a belief is revised because new evidence becomes available, regardless of whether the evidence is visual, verbal, remembered, or inferred.
