# micro-11 Examples and Boundaries

## Decision Variable
the character's current factual belief

## Route Signal
Use this micro unit when the scene requires reconstructing one character's current factual model of the world from that character's own access to evidence.

## Hard Boundary
- The unit answers only first-order factual belief: what X believes about the world.
- It does not evaluate whether X's belief is false unless that is only a supporting observation.
- It does not model one person's belief about another person's belief.
- It does not decide background knowledge, memory retention, intention, preference, or emotion as the primary variable.

## Shortcut To Avoid
- Do not answer from the narrator's omniscient facts; filter through the target character's evidence.
- Do not automatically label every belief question as false belief; first determine whether the target is simply asking for the character's own representation.
- Do not infer that a character knows a later event merely because the reader knows it.

## Common Failure Modes
- Confusing actual location or actual facts with the character's believed facts.
- Overrouting to false belief whenever an unseen change occurs, even when the prompt only asks what the character currently believes.
- Treating a lack of background expertise as a belief problem instead of a knowledge-boundary problem.
- Missing that the character may be uncertain rather than holding a definite belief.
- Accidentally answering what another character thinks the target believes.

## Minimal Pair
- Case: Nina hears that the meeting is in Room 4 and has not heard any update. The question asks, 'Where does Nina think the meeting is?' | Why: The target is Nina's own current factual belief based on information available to her.
- Case: Nina hears that the meeting is in Room 4, but it was moved to Room 6 without her knowledge. The question asks, 'Is Nina wrong about the meeting room?' | Why: This should exit to False Belief because the requested variable is the conflict between Nina's belief and reality.

## Boundary Stress Test
- If X saw the original event but missed the later change, answer what X still believes, unless the prompt asks specifically about the error-reality gap.
- If X was told a fact by an unreliable person but has no reason to doubt it, represent X's belief from X's perspective; do not substitute the speaker's reliability judgment unless asked.
- If X lacks the specialized knowledge to interpret a clue, do not invent a belief from the clue; route to Knowledge Boundary.
- If X once knew the fact but may have forgotten it, resolve memory state before using first-order belief.
- If the prompt says 'What does A think B will believe?' route away to recursive belief.

## Generalization Note
First-order belief is the basic theory-of-mind operation of separating a character's subjective factual model from reality and from other minds; it applies across object-location tasks, conversations, plans, rumors, and everyday misunderstandings.
