---
name: micro-10
level: micro
layer: L1
family: "perception-memory-knowledge"
description: "Diagnose whether a character has the background knowledge needed to interpret information, without confusing it with perception, memory, or factual belief."
---

# Knowledge Boundary

## Use When
- Use when the question is whether the character has enough professional, cultural, experiential, or conceptual background to understand what was said, shown, or implied.
- Use when the key issue is comprehension blocked by missing background knowledge, not by not seeing, not remembering, or holding a false belief.
- Use when one person would understand a reference, term, custom, or concept and another would not because of different prior knowledge.

## Do Not Use When
- Do not use when the main issue is whether the character noticed, heard, saw, or otherwise perceived the information.
- Do not use when the main issue is whether the character remembers, forgets, or misremembers something they previously knew.
- Do not use when the main issue is what the character believes is true or false about the world; route to belief or false-belief skills instead.
- Do not use when the question is about intention, emotion, persuasion, or social etiquette unless the decisive barrier is background competence itself.

## Decision Variable
whether the character has the background required to interpret the information

## Trigger Checklist
- Is the barrier missing training, expertise, culture, experience, or conceptual familiarity?
- Would the character still fail to understand even if they clearly perceived the information?
- Is the contrast between informed and uninformed listener the key diagnostic split?
- Does the scene ask about comprehension of jargon, reference, custom, or domain-specific meaning?

## Workflow
- Identify the exact information the character must interpret.
- Ask what background knowledge is required to make sense of it.
- Check whether the character has that background.
- Infer understanding, partial understanding, or misunderstanding from that knowledge gap.
- Do not infer lack of perception, memory, or false belief unless the scene explicitly asks for those.

## Special Case
**Hears the words but lacks the key**: If the character perceives the message but cannot decode its meaning because they lack the needed background, this is still Knowledge Boundary.

Scene: A nurse tells a patient that the test result is "benign." The patient hears the word clearly but does not know its medical meaning.
Question: Does the patient understand what the nurse means?
Answer logic: Yes, this is a knowledge boundary case: perception is intact, but the patient lacks the medical background needed to interpret the term.

## Boundary Exit Rule
- Exit to micro-09 if the issue is whether the character once learned it, now retains it, or has forgotten it.
- Exit to micro-11 or micro-12 if the issue is what the character thinks is true, not whether they have the background to interpret it.
- Exit to micro-05 if the issue is whether the character saw, heard, or noticed the cue at all.
- Stop when the diagnostic is complete and the task moves to emotion, intention, or action prediction.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when the scene hinges on whether a person can correctly interpret information because of missing background knowledge, expertise, or cultural context.
