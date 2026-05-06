---
name: skill21
description: Use for CP-01 commitment-priority arbitration — "what does X do NEXT?" when several actions compete (prior commitment, ongoing activity, fresh invitation, background task) — by enforcing the priority order and applying failed-action replacement.
---

# CP-01 Commitment-Priority Arbitration

## Use When

- The story sets up a character with several competing draws on their
  next action (recent verbal promise, awaited appointment, ongoing
  activity, fresh invitation, background chore).
- The question asks what the character will do **NEXT**.
- The original activity may have been disrupted (laptop dies, weather
  changes, brother interrupts).

## Do Not Use When

- The task is who should adapt to whose preference. Use `skill18`.
- The task is what to *say* to convince the other party. Use
  `skill13`.
- The task is about belief, emotion, or hidden meaning rather than
  next-action prediction.

## Trigger Checklist

- Is there a "completion of failed actions" / "what does X do next"
  question?
- Are there multiple time-ordered claims on the next action (prior
  promise, current task, new invite, chore)?
- If yes, use this skill.

## Workflow

1. List every competing draw on the character's next action.
2. Apply the priority order below.
3. Apply the failed-action replacement rule if the original activity
   became impossible.
4. Pick the option that satisfies the dominant commitment.

## Detailed Procedure — Commitment-Priority Arbitration

```
STEP 1 — LIST every competing draw on the character's next action:
  (a) PRIOR EXPLICIT COMMITMENT — verbal promise just made, expected
      meeting / appointment, agreed plan ("I'll come help you", "my
      sister comes at 2 pm").
  (b) ONGOING ACTIVITY — what they were doing right before the
      disruption (painting, studying, etc.).
  (c) NEW INVITATION — a fresh option that just appeared (friend's
      message, sudden alternative venue).
  (d) BACKGROUND TASK — chores or secondary obligations.

STEP 2 — PRIORITY ORDER (typical in these stories):
       (a) prior commitment  >  (b) ongoing activity
                              >  (c) new invitation
                              >  (d) background task

STEP 3 — FAILED-ACTION REPLACEMENT
  • If the character was doing X but X became impossible (no outlet,
    bad weather, etc.), the next action usually preserves the SAME
    UNDERLYING GOAL.
  • If the reason they were THERE was to wait for someone, they keep
    waiting — the disruption (dead laptop, etc.) is irrelevant to
    that deeper goal.
  • A freshly-made promise dominates whatever fresh distraction
    appears.

DECISION RULE
The next action almost always satisfies the PRIOR COMMITMENT (or
preserves the deeper goal of being there), not whatever new
alternative just appeared.

WORKED EXAMPLE
Story: Li Hua is in his study, working on a complex math problem.
Just as he is about to solve the problem, his brother runs in about
strange birds outside. Li Hua hesitates but decides to continue
focusing on his math problem. Suddenly, his phone rings — Xiao Li
invites him to a basketball game in the afternoon.

Q: What is the most likely action of Li Hua AFTER receiving the
   message from Xiao Li?

  A. He continues to solve the math problem. ✅
  B. He goes out to observe the strange birds.
  C. He replies to Xiao Li, then goes to the basketball game.
  D. He turns off his phone and concentrates on the math problem.

Reasoning: (b) ongoing math problem — already confirmed by him
refusing brother's distraction — vs (c) new basketball invitation;
ongoing activity beats new invitation → A.
```

GUARDRAIL: do NOT over-weight the freshest message / latest
distraction. Locate the active commitment that the story established
earlier, and pick the option that fulfils it.

## Output Template

- `Task framing`: the character and all competing draws on the next
  action.
- `Priority decision`: which level of the (a)>(b)>(c)>(d) hierarchy
  dominates.
- `Reasoning decision`: how that dominant commitment maps to a
  concrete next action.
- `Answer`: the option that fulfils the dominant commitment.

## Failure Checks

- Do not pick the option that satisfies the freshest distraction.
- Apply the failed-action replacement rule when the original activity
  became impossible.
- Reject options that abandon the dominant commitment without an
  explicit reason in the story.

## Boundary Exit Rule

- If the task is who should adapt to whose preference, route to
  `skill18`.
- If the task is what to say to convince the other party, route to
  `skill13`.
- If the task is just classifying the character's emotion, route to
  the relevant emotion skill.

## Answer Discipline

- Enumerate (a) / (b) / (c) / (d) explicitly in your reasoning before
  picking the option.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
