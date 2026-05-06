---
name: skill19
description: Use for SC-01 sensory-channel filtering — the perceiver only has a SUBSET of senses (blind, deaf, blindfolded, behind glass, distracted) and the question asks what THAT perceiver concludes from the scene.
---

# SC-01 Sensory-Channel Filtering

## Use When

- A perceiver in the story has only a SUBSET of senses available
  (blind, deaf, blindfolded, behind glass, far away, distracted).
- The narrator describes multi-modal cues but the perceiver only
  experiences a subset.
- The question asks "what does the deaf student think you are doing?",
  "what does the blind person conclude?", "what does the person
  relying on sound infer?".

## Do Not Use When

- All perceivers have full senses; the task is geometry only. Use
  `skill16`.
- The boundary is about WORLD KNOWLEDGE (no birds in this city), not
  a sensory restriction. Use `skill17`.
- The question is about an observer interpreting an ambiguous cue.
  Use `skill6`.

## Trigger Checklist

- Is one perceiver explicitly described as missing a sensory channel?
- Does the question ask what THAT perceiver concludes about the scene?
- If yes, use this skill.

## Workflow

1. Identify the perceiver and their available channels.
2. Strip from the story every detail that depends on a missing
   channel.
3. From the REMAINING signals only, reconstruct what THIS perceiver
   would conclude.
4. If the question contrasts two perceivers with different main
   senses, compute their conclusions SEPARATELY.

## Detailed Procedure — Sensory-Channel Filtering

```
STEP 1 — IDENTIFY the perceiver and the sensory channels they have:
  • Blind                  → HEARING + TOUCH + SMELL only (no vision)
  • Deaf                   → VISION + TOUCH + SMELL only (no hearing)
  • Eye-mask / blindfold   → no vision; hearing & smell intact
  • Behind glass / far     → vision only (no sound, smell, touch)
  • Distracted / busy      → no peripheral perception of unrelated
                             event

STEP 2 — STRIP from the story every detail the perceiver CANNOT
access through their channels. The narrator describes everything; the
perceiver only experiences a subset.

STEP 3 — From the REMAINING signals only, reconstruct what THIS
perceiver would most likely conclude about the scene.

STEP 4 — If the question contrasts "main sense X" vs "main sense Y"
perceivers, compute their conclusions SEPARATELY. They will reach
DIFFERENT conclusions even though the underlying event is the same.

DECISION RULE
The answer must be derivable from sensory data the perceiver actually
has. Reject any option that depends on information from a channel they
lack.

GUARDRAILS
• A deaf student watching a water-phone will NOT think "whale song"
  (needs hearing).
• A blind person near an ozone reactor will NOT think "chemistry lab"
  (needs vision).
• A distracted student will not perceive a quiet event happening
  behind their back.
• A "behind glass" observer perceives shapes but not smells or
  conversation.

WORKED EXAMPLE
Story: A music professor demonstrates a water-phone (a metal
percussion instrument played with a bow, producing eerie sliding
notes). Alice is deaf; Bob is blindfolded. Both are in the same room.

Q: What does Alice think Bob is hearing?

  Wrong: "whale song" — Alice cannot hear the sound and does not
         have the vocabulary anchor that the sound is whale-like.
  Right: "scraping a metal bowl with a stick" — Alice sees the
         visual setup and would describe it visually.
```

## Output Template

- `Task framing`: perceiver and their available sensory channels.
- `Stripped scene`: which story details survive after removing the
  missing-channel cues.
- `Reasoning decision`: what THIS perceiver concludes from the
  remaining signals.
- `Answer`: the option that fits the surviving sensory data.

## Failure Checks

- Reject options that require a channel the perceiver lacks.
- Compute each perceiver's conclusion separately when contrasting two
  perceivers.
- Do not import multi-modal narrator details into a single-channel
  perceiver's mind.

## Boundary Exit Rule

- If all perceivers have full senses and the task is just geometry,
  route to `skill16`.
- If the boundary is world-knowledge fencing (no birds), route to
  `skill17`.
- If the task is observer-reaction interpretation of an ambiguous
  cue, route to `skill6`.

## Answer Discipline

- Quote the perceiver's available channels in your reasoning before
  selecting the option.
- Reject options whose key detail depends on a missing channel.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
