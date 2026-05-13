---
name: skill5
description: Use for FB-03 container content / label false belief — "What is in the box?" or "What will X expect inside?" — by separating apparent content, real content, and the target perspective.
---

# FB-03 Container Content / Label False Belief

## Use When

- The task is about what should be in a container, what someone expects
  to find inside, or what the label suggests.
- The container's label, appearance, or expected content differs from
  the real content.
- The answer depends on who opened the container and who only saw the
  outside.

## Do Not Use When

- The task is about where a moved object will be searched for. Use
  `skill3` or `skill4`.
- The main issue is sender intention, emotion selection, or persuasion.
- There is no appearance-versus-reality split inside a container.

## Trigger Checklist

- Is the contrast between `apparent content` and `real content` central
  to the question?
- Does the story specify who opened the container and who only saw the
  label or outside?
- Is the answer about expected contents rather than physical location?
- If yes, use this skill.

## Workflow

1. Identify the container, its **apparent content** (label / outside),
   and its **real content**.
2. Track who opened the container, who only saw the label, and whose
   perspective the question asks for.
3. Decide whether the requested answer should follow label-based
   expectation or true knowledge.
4. Keep `appearance`, `reality`, and `target belief` separate all the
   way through.
5. If the task is actually about a moved object's location, **stop and
   route to `skill3` or `skill4`**.
6. If options are provided, choose the exact option that matches the
   requested perspective.

## Detailed Procedure — Container Ledger

```
TABLE
| Container | Label / outside cue | Real content | Who opened? | Who only saw outside? |

QUESTION-TYPE MAP
• "What is really in the X?"                    → use REAL CONTENT
• "What is on the label?" / "What does it
   look like from outside?"                     → use APPARENT CONTENT
• "What does C think is in the X?"
    – if C opened it                            → use REAL CONTENT
    – if C only saw the label                   → use APPARENT CONTENT
• "What will C be surprised to find?"           → diff between APPARENT
                                                  and REAL content,
                                                  from C's prior =
                                                  apparent
```

GUARDRAIL: do NOT use first-order moved-object reasoning here. There is
no movement in space; the conflict is between inside and outside of one
container.

## Output Template

- `Task framing`: container, apparent content, real content, and target
  perspective.
- `Perspective evidence`: who saw inside and who did not.
- `Reasoning decision`: whether the answer follows appearance or true
  knowledge.
- `Answer`: expected content or known content, mapped to the exact
  option if needed.

## Failure Checks

- Separate label, reality, and belief.
- Do not swap expected content with actual content.
- Track who opened the container before answering.
- Keep content reasoning separate from location reasoning.

## Boundary Exit Rule

- If the task asks where someone will search for a moved object, route
  to `skill3` or `skill4`.
- If no appearance-versus-reality split exists, do not force this skill.
- If the task is about emotion or intention rather than contents, route
  away.

## Answer Discipline

- In multiple-choice settings, determine the correct perspective first,
  then choose the exact matching content option.
- Do not let a semantically related distractor replace the exact
  apparent or real content named by the story.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
