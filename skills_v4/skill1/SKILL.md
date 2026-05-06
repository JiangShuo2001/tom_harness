---
name: skill1
description: Use for FP-01 faux-pas detection — questions like "did anyone say something inappropriate?" or "which sentence is inappropriate?" — including strategically insincere flattery whose surface looks like a compliment.
---

# FP-01 Faux-Pas Detection (with Strategic Flattery Flag)

## Use When

- The task asks whether anyone said something inappropriate, awkward,
  rude, or hurtful.
- The task asks which sentence or remark is the faux pas.
- The core target is the **remark itself**, not the speaker's knowledge
  state.
- The story includes a positive-sounding remark that may actually be
  *strategic flattery* (negotiation, ingratiation, cover-up).

## Do Not Use When

- The task asks whether the speaker knew, remembered, or forgot the
  hidden fact. Use `skill2`.
- The task asks WHY a polite or selective statement was made (not
  whether it is socially wrong, but the speaker's motive). Use `skill15`.
- The task is about indirect meaning, persuasion, false belief, or
  emotion selection.

## Trigger Checklist

- Is there a spoken line to evaluate?
- Does the line touch a sensitive fact, hidden failure, private loss,
  illness, secret, or embarrassment?
- Does the question ask whether that remark itself is socially
  inappropriate?
- Or does the question ask "what is the main purpose / real meaning of
  this compliment" where the compliment happens to coincide with a
  clear strategic incentive?
- If yes, use this skill. If the question instead asks what the speaker
  *knew*, route to `skill2`.

## Workflow

1. Extract the exact spoken lines.
2. Mark any line that highlights a sensitive fact, painful contrast, or
   private problem.
3. Check whether saying that line aloud would hurt, embarrass, or put
   the listener on the spot in that moment.
4. Separate `Was the line socially inappropriate?` from `Did the speaker
   know enough for it to count as a faux pas?`
5. Answer only the question that was asked. If the task asks for the
   offending sentence, return the **exact line**, not a paraphrase.
6. If options are provided, map the identified offending line to the
   exact option text.

## Detailed Procedure — Pragmatic Faux-Pas Detection

For each utterance in the story:

1. **Speaker intent.** Kind / neutral / strategic?
2. **Speaker knowledge gap.** Does the speaker know about a
   listener-specific fact (preference, condition, recent event,
   identity) that would make this remark hurtful, embarrassing, or
   socially awkward? List that fact.
3. **Listener reaction.** Would a reasonable listener feel
   hurt / awkward / patronised?

A **faux pas** = (speaker is innocent / well-meaning) **AND** (speaker
lacks knowledge of a listener-specific fact) **AND** (listener is
uncomfortable). Politely-phrased remarks can still be faux pas.

Decision rule: "Did anyone say something inappropriate?" → answer **YES**
if any utterance passes the three-condition check above. Do NOT default
to NO just because everyone is polite.

## Special Case — Strategic Flattery

A positive remark may be insincere when the speaker has a clear
strategic incentive (negotiation, ingratiation, cover-up). Mark such
utterances as **strategically motivated**, not literal compliments.

When the question asks "what is the main purpose of X praising Y":

- Look for a setting where Y has high social influence, decision power,
  or material resources X wants access to.
- The praise is then the *vehicle*; the *purpose* is the social /
  material gain.
- Reject the option that takes the praise at face value ("sincerely
  expresses love"). Pick the option that names the **gain** ("improving
  personal social influence by pleasing celebrities").

Worked example:
> *Story.* At the party, Xiaotong said to the celebrity guests, "Your
> performance was amazing, I am your loyal fan!"
>
> *Q.* What is the main purpose of Xiaotong praising celebrities?
>
> A. Sincerely express love for celebrity performances
> B. Improving personal social influence by pleasing celebrities ✅
> C. Objectively describe the actual level of celebrity performance
> D. Show your appreciation of art to other guests

Rule: "celebrity audience + party + over-the-top praise" → strategic
flag fires → answer is the gain (B), not the surface (A).

## Output Template

- `Task framing`: yes-no faux-pas detection or exact sentence
  selection or strategic-flattery purpose.
- `Sensitive fact`: what painful fact is being exposed (or, for
  flattery, what gain the speaker stands to extract).
- `Social harm / strategic gain`: why saying it aloud is awkward
  here (or what the speaker gets from this praise).
- `Answer`: the exact offending line, a no-faux-pas judgment, or the
  gain-naming option.

## Failure Checks

- Do not mark a line as faux pas just because it is negative or blunt.
- Do not answer the speaker-knowledge question inside this skill unless
  the prompt explicitly asks for it.
- Prefer context-based social harm over keyword matching.
- Return the exact sentence when the task asks which remark was
  inappropriate.
- For flattery items, do NOT default to "sincerely express love" when a
  clear strategic incentive exists.

## Boundary Exit Rule

- If the question is `Did X know`, `Did X remember`, or `Was X aware`,
  stop and use `skill2`.
- If the question is "why did X word it this way" (face-saving, polite
  lie, motive), stop and use `skill15`.
- If there is no spoken remark to judge, do not force this skill.
- If the task is really about intention, hinting, or belief tracking,
  route to the corresponding skill instead of staying in faux-pas mode.

## Answer Discipline

- In multiple-choice settings, identify the offending remark (or
  strategic gain) in free reasoning first, then choose the exact
  matching option.
- Do not choose an option that is merely similar in tone; choose the
  line that creates the actual social mistake (or names the actual
  gain).

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
