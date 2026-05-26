---
name: micro-16
level: micro
layer: L2
family: "belief-models"
description: "Use this unit to judge whether a fact is openly shared and mutually known by both parties."
---

# Common Knowledge

## Use When
- Use when the question asks whether both people know the same fact and each knows that the other knows it.
- Use when the key issue is whether a fact is publicly shared rather than privately held.
- Use when mutual awareness of shared knowledge is the target, not who believes what about a future action.

## Do Not Use When
- Do not use when the task is about what one person thinks another person will do or believe; that is second-order belief or action prediction.
- Do not use when the issue is whether someone saw, heard, remembered, or learned the fact; that is perception, memory, or evidence availability.
- Do not use when the issue is whether the fact is true, misleading, or from a reliable source; that is source credibility or belief update.
- Do not use when only one person knows the fact, or when the sharedness is not established.
- Do not infer common knowledge from mere co-presence (same room, same meeting) without an explicit mutual-awareness marker such as a public announcement, joint acknowledgement, or visible eye contact during the disclosure.

## Decision Variable
whether the fact is mutually known as public shared knowledge

## Trigger Checklist
- A mutual-awareness marker is present: public announcement, explicit acknowledgement, eye contact during disclosure, or joint witnessing with confirmation.
- Both parties received the same disclosure event, not merely the same fact through separate channels.
- Each party can recognize that the other received it (visibility, audibility, or explicit confirmation).
- The question asks about shared awareness, not about the content of the fact.
- Co-presence alone (same room, same meeting) is not enough; a marker must make the sharedness recognizable to each party.

## Workflow
- Identify the fact in question.
- Check whether both parties received or witnessed the same disclosure.
- Verify whether each party can reasonably know that the other has the same information.
- If mutual awareness is explicit, classify as common knowledge.
- If only one direction of belief is asked, switch to second-order belief instead.

## Special Case
**Public announcement creates shared knowledge**: A public statement can create common knowledge only if the scene makes mutual awareness salient, not merely because both people were in the room.

Scene: A manager announces the meeting time to the whole team in front of everyone.
Question: Do both workers know the meeting time and know that the other knows it?
Answer logic: Yes, because the announcement was public and the shared disclosure makes mutual awareness explicit.

## Boundary Exit Rule
- If the question becomes what one person expects another person to do, use second-order belief or action prediction.
- If the question becomes whether someone noticed or learned the fact, use perception, memory, or evidence availability.
- If the question becomes whether the source is trustworthy, use source credibility.
- If mutual awareness is not established, stop and do not infer common knowledge.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use when the scene asks whether a fact is publicly shared and mutually known by both parties.
