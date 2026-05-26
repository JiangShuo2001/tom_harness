---
name: micro-18
level: micro
layer: L2
family: "belief-models"
description: "Determine how the credibility of an information source changes what a character believes or how much weight they give a report."
---

# Source Credibility

## Use When
- Use when a character's belief depends on who provided the information, such as a rumor, eyewitness, expert, authority, friend, enemy, or known liar.
- Use when the question asks whether a character should believe, doubt, discount, or update based on the source's reliability.
- Use when two sources give conflicting claims and the answer depends on which source is more trustworthy, informed, biased, or deceptive.
- Use when the key issue is not merely what was said, but whether the speaker or channel is credible.

## Do Not Use When
- Do not use when the only issue is how certain the character feels without any evidence about the source's reliability; use uncertain belief instead.
- Do not use when the question asks whether information is openly shared by both parties; use common knowledge instead.
- Do not use when the question asks what someone likes or wants, unless credibility of a report about that preference is the central variable.
- Do not use when the answer follows directly from what the character personally saw, with no evaluation of testimony, rumor, authority, or deception.
- Do not use for general lying analysis unless the main task is how the listener's belief changes because the speaker is or is not credible.

## Decision Variable
source reliability

## Trigger Checklist
- Is a belief based on testimony, rumor, report, advice, warning, review, accusation, or authority?
- Is there information about the source's accuracy, expertise, access, honesty, bias, or motive to deceive?
- Would the character believe something different if the same statement came from a different source?
- Are there competing sources with different credibility levels?
- Is the question asking why confidence changes rather than simply whether the character is confident?

## Workflow
- Identify the claim being transmitted to the character.
- Identify the source or channel of the claim, including whether it is direct eyewitness, hearsay, expert judgment, rumor, authority, advertisement, enemy, friend, or known deceiver.
- Assess source reliability using available cues: access to facts, past accuracy, expertise, honesty, bias, incentives, and possible deception.
- Separate source credibility from the content's plausibility; a plausible claim from an unreliable source may still be discounted.
- Infer the character's belief update: accept, reject, doubt, seek confirmation, or hold a weaker belief.
- If the question asks another mental state, use source credibility only as an input and route to the target unit if credibility is no longer central.

## Special Case
**Reliable source versus direct perception**: If a character directly perceived the relevant fact, direct perception usually overrides later testimony unless the testimony gives a reason to doubt the perception.

Scene: Maya saw Leo put the keys in the drawer. Later, Sam, who often makes up stories, says Leo put the keys in the backpack.
Question: Where will Maya think the keys are?
Answer logic: Maya has direct perceptual evidence for the drawer and Sam is an unreliable source. She should keep the drawer belief or at most doubt slightly, rather than fully updating to the backpack.

## Boundary Exit Rule
- If the problem is only about confidence level with no source-quality cue, exit to micro-17 Uncertain Belief.
- If the problem is about whether both people know and know that the other knows, exit to micro-16 Common Knowledge.
- If the problem is about a character's own desire, liking, or choice, exit to micro-19 Self Preference.
- If the problem is about whether one character understands another person's desire, exit to micro-20 Other Preference.
- If the problem asks where someone will search after an unseen move and the source of information is not evaluated, exit to the relevant belief or false-belief route.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when a belief update turns on the trustworthiness, expertise, access, bias, or honesty of the person or channel providing information.
