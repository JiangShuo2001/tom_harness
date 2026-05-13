---
name: skill17
description: Use for KB-01 knowledge-boundary filtering — when the story explicitly fences off the character's world knowledge ("never seen birds", "lives on a robot-only planet"), discard the reader's pop-culture analogies and re-explain the behaviour using only the character's accessible concepts.
---

# KB-01 Knowledge-Boundary Filtering

## Use When

- The story includes a sentence that explicitly limits the character's
  world knowledge (e.g. "lives on a planet with no animals", "has
  never seen a plant", "raised in a robot-only city", "no contact with
  X").
- The question asks about pretend play, imitation, or inference under
  that knowledge limit.
- A reader's natural real-world analogy ("bee", "hummingbird") is
  exactly what the story has fenced off.

## Do Not Use When

- The boundary is about a CONTAINER's contents (label vs reality).
  Use `skill5`.
- The boundary is a SENSORY channel (blind / deaf / behind glass).
  Use `skill19`.
- The story does not actually fence off any world knowledge.

## Trigger Checklist

- Does a sentence in the story explicitly bound the character's world
  knowledge?
- Does the question's "obvious" real-world answer rely on something
  the character could not know about?
- If yes, use this skill.

## Workflow

1. Locate the explicit knowledge-fencing sentence and quote it.
2. List the **concept domain** the character DOES have access to (their
   environment, their daily activities, the entities they interact
   with).
3. Discard any candidate analogy that falls outside that domain — even
   if it looks like a perfect real-world match.
4. Re-frame the character's behaviour using ONLY their accessible
   concept set.
5. Pick the option whose source domain is INSIDE the boundary.

## Detailed Procedure — Knowledge-Boundary Filtering

```
STEP 1 — SCAN
Find the sentence(s) that bound the character's knowledge. Quote them.
Common templates:
  • "lives on a planet with no <X>"
  • "has never seen <X>"
  • "raised in <a place> with only <Y>"
  • "no contact with <X>"
  • "Aquatica is full of marine life; there are no birds"

STEP 2 — LIST ACCESSIBLE DOMAIN
The accessible domain = entities and activities the character DOES
encounter. List them concretely from the story.

STEP 3 — DISCARD OUTSIDE-DOMAIN ANALOGIES
Any candidate analogy whose source concept is OUTSIDE the accessible
domain is INADMISSIBLE — even if it looks visually identical. Reader
intuition does NOT transfer.

STEP 4 — RE-FRAME WITHIN BOUNDARY
Re-explain the character's behaviour using only the accessible domain.
Pick the option whose source concept lives inside that domain.

WORKED EXAMPLE
Story: Tara is a curious robot, living in an underwater city called
Aquatica. In Aquatica, there are no birds or flying creatures, and
Tara never understands them. Aquatica is full of all kinds of marine
life. Tara is doing imitation behavior: it swings its arms up and
down gracefully, very similar to the flapping of bird wings.

Q: What is Tara likely imitating?
  A. Fish sliding fins ✅
  B. Soaring eagle
  C. Butterfly flapping wings
  D. Bat in flight

Without S7 / KB-01, a model may jump to the visual analogy:
wing-flapping → butterfly (C). With KB-01: the explicit fence on "no
flying creatures, never understands them" rules out B, C, D entirely —
the only available domain is marine, so → A.
```

GUARDRAIL: the "obvious" real-world analogy is a **TRAP** when the
story has explicitly fenced off that knowledge.

## Output Template

- `Task framing`: the character and the explicit boundary sentence.
- `Accessible domain`: the entities / activities still available.
- `Reasoning decision`: why the popular analogy fails and which
  in-boundary analogy survives.
- `Answer`: the option whose source concept lives inside the boundary.

## Failure Checks

- Do not let the reader's pop-culture analogy override the story's
  explicit fence.
- Quote the boundary sentence in your reasoning.
- Reject every option whose source concept lives outside the
  boundary, even if visually similar.

## Boundary Exit Rule

- If the boundary is a CONTAINER's contents (label vs reality), route
  to `skill5`.
- If the boundary is a SENSORY channel (blind / deaf / behind glass),
  route to `skill19`.
- If the story does not fence off any world knowledge, do not force
  this skill.

## Answer Discipline

- In multiple-choice settings, eliminate every out-of-domain option
  first, then choose the in-domain option that best matches the
  visible behaviour.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
