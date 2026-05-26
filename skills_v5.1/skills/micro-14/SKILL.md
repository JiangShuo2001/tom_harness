---
name: micro-14
level: micro
layer: L2
family: "belief-models"
description: "Distinguishes a surface appearance from the true state of an object, situation, or signal without requiring any specific character to hold a false belief."
---

# Appearance-Reality Distinction

## Use When
- Use when the question asks what something looks like versus what it really is.
- Use when a disguise, misleading surface, container, label, lighting condition, costume, replica, trick, or partial view creates an appearance that conflicts with the actual state.
- Use when the correct answer depends on separating perceptual presentation from objective reality rather than tracking a person's belief.
- Use inside an appearance-reality macro case when the local diagnostic question is simply the appearance/reality gap.

## Do Not Use When
- Do not use when the answer depends on what a specific person believes despite reality; route to false belief.
- Do not use when the question asks what one person thinks another person believes; route to recursive belief.
- Do not use when new evidence changes someone's belief over time; route to evidence-availability updating.
- Do not use when the key issue is whether information is openly shared by both parties; route to common knowledge.
- Do not use when the surface is not misleading and the task is ordinary object identification.

## Decision Variable
surface appearance versus true state

## Trigger Checklist
- Is there an apparent identity, property, location, meaning, or condition?
- Is there a separate true identity, property, location, meaning, or condition?
- Does the question ask to distinguish these two levels directly?
- Can the answer be given without assigning a belief to a named character?
- Is the mismatch caused by perceptual presentation, disguise, labeling, concealment, illusion, or incomplete surface information?

## Workflow
- Identify the surface cue: what the thing seems to be from outward appearance.
- Identify the true state: what the thing actually is according to the scene facts.
- Compare the two and state the gap explicitly.
- Answer the asked level only: appearance if asked what it looks like, reality if asked what it is.
- If a character's belief is requested, exit to the appropriate belief-tracking skill instead of solving only the appearance-reality gap.

## Special Case
**Misleading container or label**: When a container, wrapper, sign, or label suggests one content but the scene states a different content, treat the label as appearance and the stated content as reality unless the question asks what a person believes from seeing the label.

Scene: A cookie tin is used to store sewing needles. The lid still shows pictures of cookies.
Question: What does the tin appear to contain, and what does it really contain?
Answer logic: The pictures and familiar container create the appearance of cookies, but the scene states the real contents are sewing needles. No specific character belief is required.

## Boundary Exit Rule
- If the prompt asks where a person will search, what they think is inside, or what they will say based on limited access, exit to false belief or knowledge-access tracking.
- If the prompt asks what A thinks B thinks about the appearance, exit to recursive belief.
- If the prompt turns on who learned the truth after receiving evidence, exit to evidence-availability updating.
- If the prompt turns on whether everyone knows that everyone knows the truth, exit to common knowledge.
- If there is no conflict between appearance and reality, do not force this unit.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when the problem's central variable is the mismatch between how something seems and what it actually is, independent of any named person's mental state.
