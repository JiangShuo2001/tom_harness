---
name: skill4
description: Use for FB-02 second-order location false belief — "Where does A think B will look?" — by maintaining three columns (real location, B's belief, A's model of B's belief) and answering from the outermost model.
---

# FB-02 Second-Order Location False Belief

## Use When

- The question asks where one character thinks another character will
  look.
- **Two** minds must be modelled: an outer thinker and an inner thinker.
- The answer depends on the outer thinker's *model* of the inner
  thinker's belief.

## Do Not Use When

- The question is only about one character's own search location. Use
  `skill3`.
- The task is about what should be inside a labeled container. Use
  `skill5`.
- The task is about emotion, hinting, or persuasion rather than nested
  belief.

## Trigger Checklist

- Does the question explicitly contain an outer thinker and an inner
  thinker?
- Is the answer about where the inner thinker will search or what the
  inner thinker believes?
- Does the story require keeping the two minds separate?
- If yes, use this skill.

## Workflow

1. Identify the outer thinker, inner thinker, object, and candidate
   locations.
2. Reconstruct what the inner thinker last knew (apply the
   `skill3`-style ledger to the inner thinker first).
3. Reconstruct what the outer thinker thinks the inner thinker knows
   (apply the ledger AGAIN, this time treating "what the inner thinker
   witnessed" as the fact whose access the outer thinker may or may not
   have).
4. Keep three columns explicit when needed: **real location**, **inner
   belief**, and **outer model of inner belief**.
5. Answer from the outer thinker's model of the inner thinker's belief.
6. If options are provided, choose the option that matches that
   second-order belief exactly.

## Detailed Procedure — Nested Ledger

Run the **Character Knowledge Ledger** (see `skill3` Detailed Procedure)
twice:

```
PASS 1 — INNER MIND
  apply Step 1–3 to the inner thinker (Y) on the moved object (Z)
  → inner_belief(Y, Z) = the last state Y witnessed of Z

PASS 2 — OUTER MIND
  apply Step 1–3 to the outer thinker (X) on "what Y currently
  believes about Z" — i.e. the perceptible action that would have
  conveyed Y's perception to X
  → outer_model(X, inner_belief(Y, Z))

Answer = outer_model(X, inner_belief(Y, Z))
```

If X did not witness whether Y saw the move, X's model of Y's belief is
"Y still thinks the object is where Y last left it" — even if X
themselves saw the move and knows the new location.

GUARDRAIL: do NOT collapse to single-mind reasoning after the second pass.
The answer is the *outer thinker's model of the inner thinker's belief*,
which can differ from BOTH the world state AND the inner thinker's actual
current belief.

## Output Template

- `Task framing`: outer thinker, inner thinker, object, and requested
  belief target.
- `Belief evidence`: who saw the move, who missed it, and what each
  person knows.
- `Reasoning decision`: the outer thinker's model of the inner thinker's
  search location.
- `Answer`: the second-order belief, mapped to the exact option if
  needed.

## Failure Checks

- Keep both minds separate at every step.
- Do not answer with the real location.
- Do not collapse the outer model into the inner character's own direct
  belief.
- Track similar container names carefully.

## Boundary Exit Rule

- If the question only asks where a single character will look, route
  down to `skill3`.
- If the task is about contents rather than locations, route to
  `skill5`.
- If the outer thinker is not actually queried, do not force
  second-order reasoning.

## Answer Discipline

- In multiple-choice settings, derive the second-order belief first,
  then select the exact matching option text.
- Do not choose the real location option simply because it reflects the
  latest event in the story.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
- The shared ledger procedure lives in `skill3/SKILL.md`.
