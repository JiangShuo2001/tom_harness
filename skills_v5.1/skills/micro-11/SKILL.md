---
name: micro-11
level: micro
layer: L2
family: "belief-models"
description: "Determine a single character's current belief about the facts from that character's own evidence and perspective."
---

# First-Order Belief

## Use When
- Use when the question asks what one character believes, thinks is true, expects to be true, or assumes about the current facts.
- Use when the answer depends on the character's subjective representation of reality, not on the narrator's true state alone.
- Use when the belief may be true, false, uncertain, outdated, or incomplete, but the task is to state the character's own model of the situation.
- Use inside a larger false-belief, search-location, trust, or communication scene when the local diagnostic step is: what does this one person believe right now?

## Do Not Use When
- Do not use when the main question is whether the belief conflicts with reality; route to False Belief if the discrepancy itself is the target.
- Do not use when the target variable is what the character remembers, forgot, or misremembers after prior exposure; route to Memory, Forgetting, and Misremembering.
- Do not use when the issue is whether the character has background expertise, cultural knowledge, or conceptual competence needed to interpret something; route to Knowledge Boundary.
- Do not use when the question asks what X thinks Y believes, knows, expects, or will do based on Y's belief; route to Second-Order or Recursive Belief.
- Do not use when the answer is primarily about desire, intention, emotion, deception motive, or moral evaluation rather than factual belief.

## Decision Variable
the character's current factual belief

## Trigger Checklist
- A specific character is the belief holder.
- The question asks what that character believes, thinks, assumes, expects, or would say is true.
- There is evidence about what the character perceived, was told, inferred, or failed to observe.
- The answer can be framed as a factual proposition from that character's point of view.
- No nested mind-reading is required beyond the target character's own belief.

## Workflow
- Identify the target believer and freeze the scene at the time asked about.
- List only the information available to that character before that time: direct perception, testimony, prior assumptions, and obvious inferences.
- Exclude facts the narrator or other characters know but the target did not observe or learn.
- Construct the simplest factual proposition the character would currently treat as true, likely, or unknown.
- If reality differs from that proposition, note the belief as the character's belief without making discrepancy the main variable.
- Answer in the character's perspective, using uncertainty when the character has insufficient evidence.

## Special Case
**Belief Without Error**: A first-order belief does not need to be false; if the character's available evidence matches reality, still state the character's subjective belief rather than routing only because the belief is correct.

Scene: Maya sees Leo put the blue notebook in the drawer. No one moves it afterward. Later, Maya returns to the room.
Question: Where does Maya think the blue notebook is?
Answer logic: Maya directly saw the notebook placed in the drawer and received no later evidence of a move, so her current factual belief is that the notebook is in the drawer. This is first-order belief even though it is also true.

## Boundary Exit Rule
- Exit to micro-12 False Belief if the requested answer is about the mismatch between belief and actual state, such as 'why is X wrong?' or 'where will X mistakenly look?'
- Exit to micro-13 Second-Order or Recursive Belief if the question embeds another person's mental state, such as 'What does A think B believes?'
- Exit to micro-09 Memory, Forgetting, and Misremembering if the decisive issue is retention, forgetting, or distorted recall after earlier exposure.
- Exit to micro-10 Knowledge Boundary if the decisive issue is whether the character has the background competence to understand a term, custom, profession, clue, or symbol.
- Exit to perception or attention units if the character's belief cannot be assessed until deciding what the character could see, hear, or notice.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when the scene requires reconstructing one character's current factual model of the world from that character's own access to evidence.
