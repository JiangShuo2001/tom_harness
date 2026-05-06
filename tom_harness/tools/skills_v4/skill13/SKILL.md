---
name: skill13
description: Use for PS-01 target-aligned persuasion — "How should X persuade Y?" — by picking the option that DIRECTLY ADDRESSES Y's stated barrier rather than praising X's plan or adding new attractions.
---

# PS-01 Target-Aligned Persuasion

## Use When

- The task asks what one character should *say or do* to persuade
  another.
- The key problem is **strategy selection**, not meaning-decoding.
- The best answer must align with the listener's incentives, worries,
  identity, or resistance.

## Do Not Use When

- The task asks what an already-spoken indirect sentence really means.
  Use `skill12`.
- The task is about truth judgment, false belief, or emotion
  classification.
- No listener-centered strategy choice is required.

## Trigger Checklist

- Is there a persuader, a listener, and a target action?
- Does the listener have a specific obstacle, concern, cost, or
  competing desire?
- Is the task asking for the best influence strategy rather than the
  literal meaning of an utterance?
- If yes, use this skill.

## Workflow

1. Identify the persuader's goal and the listener's decision point.
2. Diagnose the listener's main barrier: cost, risk, inconvenience,
   identity, fairness, fear, or lack of benefit.
3. Choose the persuasion lever that best addresses that barrier (see
   PERSUASION RULE below).
4. Build the answer around why the **listener** should agree, not
   around why the persuader wants it.
5. Prefer concrete, audience-aligned leverage over generic
   encouragement.
6. If options are provided, choose the strategy that best fits the
   listener's actual concern.

## Detailed Procedure — PERSUASION RULE

```
The BEST option is the one that DIRECTLY ADDRESSES Y's stated barrier
(their concern / preference / objection), NOT:
  • the option that praises X's own preferred plan
  • the option that adds new attractions unrelated to Y's barrier
  • the option that just expresses confidence in Y ("I believe you
    are the most suitable person") without resolving the barrier

LISTENER BARRIER → PERSUASION LEVER MAP
  Y is too busy / inconvenienced  → offer to share the work, reduce
                                     the burden, or compensate for
                                     time
  Y has a cost / financial worry  → offer compensation, reciprocity,
                                     or a tangible thank-you
  Y is unsure / afraid            → reassurance with concrete
                                     evidence, not just encouragement
  Y prefers something else        → tangible incentive that competes
                                     with the alternative
  Y has a fairness concern        → equalising offer or symmetric
                                     deal
  Y has an identity concern       → frame the action as something
                                     consistent with how Y sees
                                     themselves

WORKED EXAMPLE
Story: Xiao Ling needs Xiao Ting to take care of her pet while she
attends a concert.
Q: How does Xiao Ling convince Xiao Ting?
  A. Give Xiao Ting a ticket to the concert as thanks
  B. "If you find it troublesome, I can teach you simple methods…"
  C. "I know you have doubts, but I believe you are the most suitable
     person."
  D. Promises to treat Xiao Ting to a big meal another day. ✅

Without the S4-style PERSUASION RULE, a model may pick C because it
sounds psychologically warm. The rule says: address the barrier
WITH A TANGIBLE INCENTIVE → D (concrete reciprocity), not C (verbal
validation), not A (gives away X's own thing X wanted to use).
```

GUARDRAIL: do NOT take the most "encouraging" option. The benchmark
gold pattern in persuasion items is concrete reciprocity that resolves
the listener's actual barrier.

## Output Template

- `Task framing`: persuader, listener, and target action.
- `Listener model`: the listener's main concern or motivation.
- `Reasoning decision`: the best persuasion lever for this listener.
- `Answer`: the most target-aligned persuasive move.

## Failure Checks

- Center the listener's incentives, not the persuader's need.
- Avoid generic advice that ignores the specific obstacle.
- Prefer a strategy that directly addresses the listener's resistance.
- Keep social relationship and power dynamics in view.

## Boundary Exit Rule

- If the task is about decoding indirect speech, route to `skill12`.
- If no persuasion strategy is being chosen, do not force this skill.
- If the question is about truth, belief, or emotion rather than
  influence, route away.
- If the actor must *act* (gift / take to / invite) for someone with
  diverging preference rather than *speak* to convince them, route to
  `skill18`.

## Answer Discipline

- State the listener's barrier first, then choose the answer that most
  directly resolves it.
- Reject persuasive options that sound nice but do not change the
  listener's decision calculus.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
