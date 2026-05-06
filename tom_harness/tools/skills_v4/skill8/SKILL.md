---
name: skill8
description: Use for UO-01 atypical emotion attribution and "real / hidden / suppressed feeling" questions — pick the emotion when a character-specific override or hidden context flips the default everyday script.
---

# UO-01 Atypical Emotion Attribution (with Hidden-Emotion Decoder)

## Use When

- The question asks what emotion a character has or shows.
- The obvious default everyday emotion may be wrong.
- A trait, prior goal, relationship, value, or hidden appraisal changes
  the default script.
- The question asks for the **REAL / HIDDEN / SUPPRESSED feeling** of
  someone who is consciously masking it (good cards they hide, joke
  they don't get and hide, stomach-ache they hide).

## Do Not Use When

- The question explicitly asks WHY a surprising emotion happened. Use
  `skill9`.
- The task is mixed-emotion truth judgment or statement truthfulness.
  Use `skill14`.
- The question is moral-emotion after a possibly-harmful action with an
  anti-guilt cue. Use `skill22`.
- The story contains no meaningful override and only asks for a
  standard typical reaction.

## Trigger Checklist

- Does the story invite an obvious default emotion?
- Is there a character-specific override such as bravery, guilt, prior
  arrangement, role obligation, moral appraisal, or an explicit
  hiding / masking action?
- Is the question asking `which emotion`, not `why this emotion`?
- If yes, use this skill.

## Workflow

1. Write down the default emotion an average person might feel.
2. Search for override cues: character trait, prior goal, value
   conflict, relationship history, social norm, or self-appraisal.
3. Recompute the emotion from the character's specific appraisal, not
   from the generic script.
4. Prefer the narrower social emotion if it better explains the
   override.
5. If the task is really asking for the *hidden cause* of the reversal,
   stop and route to `skill9`.
6. If options are provided, pick the option that best reflects the
   overridden appraisal.

## Detailed Procedure — Expectation-Delta Analysis

```
1. SURFACE EVENT
   What visibly happened? (Quote it briefly.)

2. EXPECTED REACTION
   Based on default social norms and the character's apparent
   situation, what reaction would be TYPICAL?

3. ACTUAL / ASKED REACTION
   What reaction is the question pointing to (atypical / hidden /
   opposite)?

4. HIDDEN CONTEXT SEARCH
   If actual ≠ expected, scan the story for one of:
   (a) An ADDITIONAL CONSTRAINT the character faces but bystanders
       don't see (debt, illness, secret deal, family pressure,
       rule-violation worry).
   (b) A SECOND GOAL competing with the obvious one (career vs care,
       reputation vs honesty, play vs duty).
   (c) An EXTERNAL TRIGGER known only to this character (calendar
       reminder, prior message, identity revelation, news).
   (d) An INSIDE / OUTSIDE asymmetry: what the character SHOWS may be
       the opposite of what they FEEL (hidden / suppressed / regulated
       emotion).

5. DECISION
   Pick the option that is consistent with the HIDDEN context, not with
   the surface event alone.
```

## Special Case — "Real feeling" / "Hidden emotion" multiple-choice items

The "hiding" is an **action**, not an emotion. The "real feeling" = the
natural emotional response of the character to the **SOURCE EVENT**
itself, NOT a secondary anxiety about the act of hiding.

Apply this 2-step decoder:

```
Step A — Identify the SOURCE EVENT for THIS character and its valence:
  POSITIVE source : rewarded, allowed, holding good cards, given a
                    promise, secret advantage, succeeded
                    → underlying feeling = happy / excited / proud
  NEGATIVE source : in physical pain, excluded, did not understand
                    while others did, disappointed, hurt
                    → underlying feeling = sad / hurting / disappointed

Step B — Map valence to options:
  • POSITIVE source being hidden so as not to give it away (good
    cards, secret reward, allowed to stay up late) → answer =
    POSITIVE feeling (happy / excited), NOT anxiety about being
    discovered.
  • NEGATIVE source being hidden so the character can still do
    something fun (hides stomach-ache to go to the party) → answer =
    the NEGATIVE underlying feeling (sad / hurting), NOT happiness
    about the party.
  • The character does NOT understand something everyone else does
    and hides it → answer = sad / embarrassed (the exclusion itself).
```

GUARDRAIL 1: do NOT add "secret-keeping anxiety" or "fear of being
discovered" as the real feeling unless the story explicitly shows the
character struggling with the secret itself. The default in these items
is the SOURCE EVENT's emotion, not a meta-emotion about the act of
hiding.

GUARDRAIL 2: the question asks precisely because the reaction is
atypical — do not pick the most "obvious" emotion that fits the visible
scene.

## Output Template

- `Task framing`: character, event, and default expected emotion.
- `Override evidence`: trait, goal, relationship, hiding action, or
  self-appraisal cue.
- `Reasoning decision`: why the default script is overridden (or what
  the source-event valence is, for hidden-emotion items).
- `Answer`: the final overridden / hidden emotion.

## Failure Checks

- Do not answer from average-person intuition alone.
- Check override cues before committing to fear, anger, sadness, or
  happiness.
- Consider narrower emotions such as guilt, regret, embarrassment,
  disgust, curiosity, relief, or worry.
- Separate emotion selection from hidden-cause explanation.
- For hidden-emotion items, do NOT default to "anxiety about being
  caught".

## Boundary Exit Rule

- If the prompt says `should feel X but instead feels Y, why`, route to
  `skill9`.
- If the task is about truth status of a statement, route to `skill14`.
- If the task is moral emotion after a possibly-harmful action with an
  anti-guilt cue, route to `skill22`.
- If there is no override cue at all, do not force atypical-emotion
  reasoning.

## Answer Discipline

- In multiple-choice settings, name the default emotion first, then
  check which option is best supported by the override evidence.
- Reject broad but generic options when a narrower override emotion is
  clearly licensed.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
