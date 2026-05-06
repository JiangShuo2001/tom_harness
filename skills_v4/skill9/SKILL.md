---
name: skill9
description: Use for UO-02 unexpected-outcome explanation — "should feel X but instead feels Y, why?" — by finding the hidden prior fact that flips the appraisal in BOTH directions.
---

# UO-02 Hidden Cause Reconstruction

## Use When

- The question says a character should feel one way but instead shows
  another emotion and asks **why**.
- The task is **explanation** of emotional reversal, not direct emotion
  selection.
- The correct answer must supply the hidden prior fact or appraisal
  that bridges expected and observed emotion.

## Do Not Use When

- The question only asks which emotion the character feels. Use
  `skill8`.
- The task is about mixed-emotion truth judgment or statement motive.
- The answer choices are just plain emotion labels without explanation.

## Trigger Checklist

- Does the prompt explicitly contrast `expected emotion` with
  `observed emotion`?
- Does it ask `why` the observed emotion occurs?
- Must the answer explain BOTH the event and the emotional reversal?
- If yes, use this skill.

## Workflow

1. Identify the **default expected** emotion.
2. Identify the **observed surprising** emotion.
3. Search for the hidden prior fact, relationship, plan, or appraisal
   that would reverse the interpretation.
4. Test candidate explanations against **both sides**: they must
   explain why the default emotion weakens AND why the observed emotion
   appears.
5. Reject side stories that only make the observed emotion plausible
   without bridging the reversal.
6. If options are provided, choose the explanation that best links
   expected and observed emotion.

## Detailed Procedure — Two-sided Explanation Filter

```
EXPECTED  ◄────── default appraisal of the visible event
OBSERVED  ◄────── what the character actually shows

For each candidate explanation X:
  • Does X reduce the warrant for EXPECTED?     (must be YES)
  • Does X provide warrant for OBSERVED?        (must be YES)
  • Is X explicitly supported by a story sentence, not invented?
                                                (must be YES)
Pick the option for which all three are YES. If two pass, prefer the
one whose support sentence is closer in the text to the surprising
emotion.
```

GUARDRAIL: a side story that merely sets the scene for OBSERVED but
leaves EXPECTED equally warranted is INSUFFICIENT — it does not bridge
the reversal.

## Output Template

- `Task framing`: expected emotion, observed emotion, and visible event.
- `Hidden cause`: the extra fact or appraisal that changes the
  interpretation.
- `Reasoning decision`: how the hidden cause flips the emotional
  outcome (must explain both sides).
- `Answer`: the explanation that bridges the full reversal.

## Failure Checks

- The answer must explain both the original expectation and the
  surprising result.
- Reject merely plausible background details that do not drive the
  reversal.
- Keep explanation mode separate from plain emotion-classification mode.

## Boundary Exit Rule

- If the question only asks `what emotion`, route to `skill8`.
- If the task is about truthfulness or motive for speaking, route to
  `skill14` / `skill15`.
- If there is no expected-versus-observed contrast, do not force this
  skill.

## Answer Discipline

- In multiple-choice settings, eliminate options that explain only the
  final emotion but not the reversal from the expected emotion.
- Prefer the option that most tightly connects to the explicit scene
  details.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
