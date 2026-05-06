---
name: skill20
description: Use for AC-01 audience expertise calibration — "how should the speaker mention this technical term to this specific listener?" — by routing on listener expertise (expert vs novice) and rejecting textbook definitions when speaking to an expert.
---

# AC-01 Audience Expertise Calibration

## Use When

- The speaker is sharing an experience involving a technical term.
- The listener's expertise level on that term matters (expert / peer
  enthusiast / novice).
- The question asks how the speaker should phrase or mention the term
  to that specific listener.

## Do Not Use When

- The task is general persuasion strategy unrelated to expertise. Use
  `skill13`.
- The task is decoding hidden meaning of an indirect sentence. Use
  `skill12`.
- No specific listener is named, or the listener's expertise is
  irrelevant.

## Trigger Checklist

- Is there a technical term involved?
- Does the prompt name the listener and tell us their expertise level
  ("a senior DM", "a novice photographer", "a veteran doctor")?
- Is the question about how to MENTION the term to that listener?
- If yes, use this skill.

## Workflow

1. Identify the listener's expertise level on the topic.
2. For an expert: do NOT define / explain a term they already know.
   Use the term as shared vocabulary while sharing a specific scene,
   observation, or feeling.
3. For a novice: define the term, give context, then share experience.
4. Pick the option that fits the listener's level.

## Detailed Procedure — Audience Calibration

```
STEP 1 — IDENTIFY the listener's expertise level on the topic:
  • Expert (professional photographer, doctor, mechanic, senior DM)
                          → already knows the definitions and standard
                            terminology.
  • Peer enthusiast       → shares vocabulary; chat about the
                            experience.
  • Novice                → may need definitions and context.

STEP 2 — WHEN SPEAKING TO AN EXPERT:
  • Do NOT define / explain a term they already know — that is
    patronising.
  • Do NOT recite a textbook fact about their own field.
  • DO use the term as shared vocabulary while sharing a SPECIFIC
    scene, observation, or feeling ("today the contour light at
    sunset was so clean that the clouds looked like they were on
    fire!").
  • Use vivid, sensory, personal language — what YOU saw, captured,
    felt.

STEP 3 — WHEN SPEAKING TO A NOVICE:
  • Define the term, give context, then share experience.

DECISION RULE
For an EXPERT audience the right option is the one that USES the term
as shared vocabulary AND describes a personal experience or scene.
Reject any option that defines / explains the term to the expert
(insulting and unnecessary).

WORKED EXAMPLE
Story: You completed your first long Dungeons & Dragons campaign.
Q: You are chatting with Nate, a senior DM. How should you mention
   "role-playing"?

  A. *Definition* "Role playing is playing your character in the
     first person…"
  B. *Personal scene* "I finally let go of this battle and started
     playing role-playing seriously. It was really enjoyable to argue
     with NPCs in the voice of characters." ✅
  C. *Define-to-expert* "Do you know about role-playing? It's about
     playing a fictional character…"
  D. *Textbook fact* "Role playing is an important element in TRPG."

A, C, D all define / textbook-state a term Nate obviously knows;
B is the only one that uses the term as shared vocabulary while
sharing a personal scene → B.
```

GUARDRAIL: textbook-style definitions are WRONG when the listener is
a domain expert. The "informative" answer is socially the LEAST
appropriate in this case.

## Output Template

- `Task framing`: speaker, listener, listener's expertise level, term.
- `Calibration evidence`: cues from the story that fix the listener's
  expertise level.
- `Reasoning decision`: define vs use-as-shared-vocab.
- `Answer`: the option that fits the listener's level.

## Failure Checks

- Do not pick the "informative" definition option for an expert
  audience.
- Use shared vocabulary plus a specific, vivid personal scene for an
  expert.
- Define-then-share only for a novice listener.

## Boundary Exit Rule

- If the task is general persuasion strategy, route to `skill13`.
- If the task is decoding hidden meaning of an indirect sentence,
  route to `skill12`.
- If no specific listener expertise is involved, do not force this
  skill.

## Answer Discipline

- Quote the listener's expertise level in your reasoning before
  picking the option.
- Reject every option that defines or recites textbook material to a
  named expert.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
