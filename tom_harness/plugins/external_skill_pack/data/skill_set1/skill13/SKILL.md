---
name: skill13
description: Use for PS-01 persuasion questions that ask how one character should convince another by aligning the message to the listener's incentives, worries, and resistance.
---

# PS-01 Target Aligned Persuasion

## Use When

- The task asks what one character should say or do to persuade another.
- The key problem is not meaning-decoding but strategy selection.
- The best answer must align with the listener's incentives, worries, identity, or resistance.

## Do Not Use When

- The task asks what an already-spoken indirect sentence really means. Use `skill12`.
- The task is about truth judgment, false belief, or emotion classification.
- No listener-centered strategy choice is required.

## Trigger Checklist

- Is there a persuader, a listener, and a target action?
- Does the listener have a specific obstacle, concern, cost, or competing desire?
- Is the task asking for the best influence strategy rather than the literal meaning of an utterance?
- If yes, use this skill.

## Workflow

1. Identify the persuader's goal and the listener's decision point.
2. Diagnose the listener's main barrier: cost, risk, inconvenience, identity, fairness, fear, or lack of benefit.
3. Choose the persuasion lever that best addresses that barrier.
4. Build the answer around why the listener should agree, not around why the persuader wants it.
5. Prefer concrete, audience-aligned leverage over generic encouragement.
6. If options are provided, choose the strategy that best fits the listener's actual concern.

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
- If the question is about truth, belief, or emotion rather than influence, route away.

## Answer Discipline

- State the listener's barrier first, then choose the answer that most directly resolves it.
- Reject persuasive options that sound nice but do not change the listener's decision calculus.

## References

- For compact boundaries, minimal pairs, and common confusions, read `references/examples.md`.
