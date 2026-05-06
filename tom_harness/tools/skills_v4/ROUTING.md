# Skills Routing Guide (v4)

This file is the shared routing layer for the **22 mindreading skills** in
`skills_v4/`. Use it before opening any specific skill when the main
uncertainty is *which reasoning tool should be activated*, not the answer
itself.

It is the merged successor of:

- `papers/skills_v3/ROUTING.md` (table-style families A–G, 15 skills)
- `papers/skill_v2/ROUTING_GUIDE.md` (LLM-router design notes, 12 skills)

The router can be:

- a **dedicated LLM call** that emits `Skill: <ID>` (programmatic — use
  `llm_router.py`); or
- a **human / one-call route-and-solve** model that reads this file plus
  the per-skill `SKILL.md` files and emits both the skill choice and the
  answer in one JSON object.

---

## Router First Principle

> **Route by the question's required output, not by the story's surface
> topic.**

The same story can mention emotion, belief, dialogue, and deception at
once. The correct skill is the one whose **decision variable** matches
the asked output. The decision variable for each skill is named in
`skill*/references/examples.md`.

---

## Machine Router Contract

Use this contract when `ROUTING.md` is embedded into an automated router
prompt:

1. Return exactly one line: `Skill: <ID>`.
2. `<ID>` must be one of `skill1` ... `skill22`; `NONE` is allowed only
   when the harness run explicitly permits it.
3. Prefer the closest skill whenever the item asks for social reasoning,
   belief tracking, emotion, intention, indirect speech, knowledge,
   perception, preference, quantity, spatial perspective, or action
   choice.
4. If `NONE` is permitted, use it only when the question is outside the
   22 Theory-of-Mind skill areas. Do not use `NONE` merely because the
   match is imperfect.
5. Choose by the asked output and decision variable, then use the
   boundary checks below to break ties.

---

## Fast Routing Workflow

1. Identify the asked output.
2. Name the decision variable that determines that output.
3. Check the nearest neighbouring skills before committing.
4. Use the **narrowest** skill that directly matches the asked output.
5. If the question changes from `what` to `why`, or from `truth` to
   `motive`, or from `emotion-label` to `emotion-explanation`, **reroute**.
6. If the task is within the broad Theory-of-Mind scope, choose the
   closest skill even when the match is imperfect. Return `NONE` only for
   questions outside the 22 skill areas.

---

## Family A — Social Harm and Knowledge

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill1` | Was a remark inappropriate? Which remark was inappropriate? | Whether a spoken line exposes a sensitive fact in a socially harmful way | The question targets the remark itself | `skill2`, `skill15` | If the question asks whether the speaker knew or remembered the fact, switch to `skill2`. If the question asks WHY the speaker said something polite-but-strategic (flattery), switch to `skill15`. |
| `skill2` | Did X know, remember, or forget a fact? | The target person's access to the fact | The question targets knowledge, memory, awareness, or forgetting | `skill1`, `skill3` | If the question targets whether the line itself was socially wrong, switch to `skill1`. If the access is about a moved object's location, switch to `skill3`. |

---

## Family B — Belief Tracking

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill3` | Where will X look? | X's own last-seen location belief | One mind is queried and the object was moved unseen | `skill4`, `skill5` | If the question becomes `X thinks Y will look`, switch to `skill4`. If it becomes label-versus-content, switch to `skill5`. |
| `skill4` | Where does X think Y will look? | X's model of Y's belief | Two minds are explicitly nested | `skill3`, `skill5` | If the outer thinker disappears, drop to `skill3`. If the issue is container content, switch to `skill5`. |
| `skill5` | What is in the container? What will someone think is inside? | Appearance or label versus real content | The conflict is about expected contents, not physical search location | `skill3`, `skill4` | If the story is about moved-object search, route back to `skill3` or `skill4`. |

---

## Family C — Social Cue Interpretation

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill6` | What does the observer think, feel, or do after a cue? | The observer's inferred belief from limited visible evidence | The output is the observer's reaction | `skill7`, `skill12` | If the task asks why the sender made the cue, switch to `skill7`. If it is indirect meaning from words rather than a cue, switch to `skill12`. |
| `skill7` | Why did the sender smile, wink, glance, or nudge? | The sender's hidden local goal | The output is the sender's intention behind a nonverbal cue | `skill6`, `skill12` | If the output is the observer's reaction, switch to `skill6`. If the signal is verbal rather than nonverbal, switch to `skill12`. |
| `skill12` | What does the speaker really mean? What do they want the listener to do? | Hidden speech act behind literal words | The output is request, complaint, warning, refusal, reminder, or invitation | `skill7`, `skill13` | If the signal is a cue rather than speech, switch to `skill7`. If the task asks how to persuade someone, switch to `skill13`. |

---

## Family D — Emotion and Appraisal

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill8` | What emotion does the character feel (incl. hidden / suppressed)? | Character-specific appraisal override | The output is the emotion label itself; or "real / hidden feeling" of someone masking it | `skill9`, `skill14`, `skill22` | If the question asks why the surprising emotion occurs, switch to `skill9`. If it asks whether an emotion statement is true, switch to `skill14`. If the question is about MORAL emotion after a possibly-harmful action, switch to `skill22`. |
| `skill9` | Why does the character feel this surprising emotion? | Hidden prior cause that flips the expected appraisal | The question explicitly asks for explanation of the reversal | `skill8` | If the task only asks which emotion fits, drop back to `skill8`. |
| `skill22` | What does X feel after their action possibly caused harm? | Whether ANY of the 5 anti-guilt checks fires (age / uncertainty / self-justifying / external reassurance / explicit indifference) | Moral-emotion item with an "easy" guilt option that the story actively undermines | `skill8`, `skill11` | If no anti-guilt cue is present, fall back to `skill8` (general appraisal override). If the answer follows from a wrong belief about the situation rather than from a moral judgement, route to `skill8` belief-as-appraisal mode. |

---

## Family E — Quantitative Scalar Reasoning

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill10` | What is the best estimate before observation? | Scalar phrase to prior-count mapping | The question is about a vague proportion before any update | `skill11` | If part of the set has been observed and the question asks for a revised estimate, switch to `skill11`. |
| `skill11` | What is the best estimate after partial observation? | Posterior update from prior plus observed subset, under HARD SUM CONSTRAINT | The question asks for a revised whole-set estimate | `skill10` | If there is no observation update, drop back to `skill10`. |

---

## Family F — Influence, Strategy, Decision

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill13` | How should one character persuade another? | Listener-specific barrier or incentive | The output is the best influence strategy | `skill12`, `skill18` | If the task is decoding what a sentence already means, switch to `skill12`. If the task is "what action will the actor TAKE to satisfy another party's preference?", switch to `skill18`. |
| `skill18` | Whose preference wins when actor must act for / with another party? | Which of 4 patterns fits (solo-for-other / shared-hybrid / explicit-flip / pursuing) | Discrepant desires, multiple desires, prediction-of-actions where actor's own preference differs from target's | `skill13`, `skill21` | If the task is "what message should X send to convince Y", switch to `skill13`. If the task is "what does X do NEXT given multiple competing draws", switch to `skill21`. |
| `skill20` | How should the speaker mention a technical term to this specific listener? | Listener's expertise level (expert / peer / novice) | "Aware of reader's knowledge" / audience-calibration items | `skill12`, `skill13` | If the task is about decoding hidden meaning, switch to `skill12`. If it is general persuasion strategy unrelated to expertise, switch to `skill13`. |
| `skill21` | What does the character do NEXT when several actions compete? | Priority order: prior commitment > ongoing activity > new invitation > background task | "Completion of failed actions"; multiple draws on the next action | `skill18` | If the question is who should adapt to whose preference, switch to `skill18`. |

---

## Family G — Truth and Motive

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill14` | Is the statement true? | Whether the proposition matches any genuine part of the speaker's state | The task is a yes-no truth judgment under mixed states, partial truth, or conflict | `skill15`, `skill8` | If the question asks why the speaker said it, switch to `skill15`. If it asks only for an emotion label, switch to `skill8`. |
| `skill15` | Why did the speaker say that? | Motive for a false, partial, selective, polite, or mistaken statement | The task is explanation of wording choice | `skill14`, `skill12` | If the task asks whether the statement is true, switch to `skill14`. If it asks for indirect speech meaning rather than motive under conflict, switch to `skill12`. |

---

## Family H — Spatial Perspective Taking

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill16` | What does the target viewer see from their vantage point? | Axis-mapping rule from the perceiver's grid to the target's grid (opposite / left / right / same side) | Spatial Construction, Picture Identification, dice / cube faces, multi-viewer table layouts | `skill19` | If the perceiver is restricted by a SENSORY channel (blind / deaf / behind glass), prefer `skill19` for the conclusion they form, then use `skill16` only for the geometry sub-step. |

---

## Family I — Knowledge Boundary

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill17` | What is the character imitating, given their fenced-off world knowledge? | Whether the inferred analogy lives INSIDE or OUTSIDE the character's accessible concept domain | Story explicitly limits the character's world ("never seen X", "lives where there are no Y", robot-only city) and asks about pretend / imitation / inference | `skill5`, `skill19` | If the boundary is about a CONTAINER's contents rather than world knowledge, switch to `skill5`. If the boundary is a SENSORY channel rather than world knowledge, switch to `skill19`. |

---

## Family J — Belief-Driven Moral Emotion (sub-family of D)

`skill22` lives logically inside Family D but is broken out here because
it requires a *different decision procedure* (the 5-check anti-guilt
filter) than the general appraisal-override skill `skill8`. See its
SKILL.md for the full filter.

---

## High-Value Boundary Checks

### `skill1` vs `skill2` vs `skill15`

- `skill1`: was the *remark* socially wrong?
- `skill2`: did the *speaker know* the hidden fact?
- `skill15`: *why* did the speaker word it that way (flattery, polite
  lie, selective truth, face-saving)?

### `skill3` vs `skill4` vs `skill5`

- One mind, search location → `skill3`.
- Two nested minds, search location → `skill4`.
- Container appearance vs reality → `skill5`.

### `skill6` vs `skill7` vs `skill12`

- Observer's inferred reaction → `skill6`.
- Sender's intention behind a nonverbal cue → `skill7`.
- Hidden meaning of spoken words → `skill12`.

### `skill8` vs `skill9` vs `skill22`

- Emotion label only (with appraisal override) → `skill8`.
- Why this *surprising* emotion occurs → `skill9`.
- Moral emotion after possibly-harmful action, with at least one
  anti-guilt cue (age, uncertainty, self-justifying, external
  reassurance, explicit indifference) → `skill22`.

### `skill10` vs `skill11`

- Before observation → `skill10`.
- After partial observation, with HARD SUM CONSTRAINT → `skill11`.

### `skill12` vs `skill13`

- Decode existing utterance's hidden act → `skill12`.
- Choose best influence strategy → `skill13`.

### `skill13` vs `skill18` vs `skill20` vs `skill21`

- "What should X *say* to convince Y?" → `skill13`.
- "Where should X *take / give / invite* Y?" with diverging preferences
  → `skill18`.
- "How should X *mention a term* to this specific listener?" → `skill20`.
- "What does X do *NEXT* given multiple competing draws on the next
  action?" → `skill21`.

### `skill14` vs `skill15`

- Yes-no truth judgment → `skill14`.
- Why this specific wording → `skill15`.

### `skill16` vs `skill19`

- Pure geometry / rotation given a fully-sighted observer → `skill16`.
- Restricted sensory channel filtering the conclusion → `skill19`.

### `skill17` vs `skill5`

- Fenced-off WORLD knowledge ("no birds here") → `skill17`.
- Fenced-off CONTAINER content (label vs truth) → `skill5`.

---

## Disambiguation Cues for the Most Confused Pairs

These cues are inherited from `papers/skill_v2/llm_router.py::ROUTER_CATALOG`
analysis: routing accuracy ≈ 70% in v2 was bottlenecked on these pairs.
Embed the cue when in doubt.

| Pair | Confusion symptom | Disambiguation cue |
|---|---|---|
| `skill8` vs `skill22` | "what does X feel after their action?" looks identical | `skill22` fires when the story includes an anti-guilt cue (young child / "MIGHT have" / "did a good deed and harm is indirect" / external reassurance / "doesn't bother to return"); else `skill8`. |
| `skill8` vs `skill9` | "real / hidden feeling" vs "expected vs observed" | `skill8` if the question asks "what is the feeling"; `skill9` if it asks "why this feeling instead of the expected one". |
| `skill3` vs `skill8` | "what does X think?" — belief or expectation? | `skill3` for object-location reasoning; `skill8` for emotional reaction to an event. |
| `skill1` vs `skill15` | flattery / polite lies both involve speech-act intent | `skill1` if the question is "did anyone say something inappropriate?"; `skill15` if it is "WHY did X say that flattering thing". |
| `skill13` vs `skill18` | both are "what does the actor do for the other party" | `skill13` if the action is *speech* aimed at convincing; `skill18` if the action is a *plan / gift / invitation* under diverging preferences. |
| `skill18` vs `skill21` | both involve choosing among options | `skill18` is about whose preference wins; `skill21` is about which prior commitment dominates. |

---

## Router Output Template

When routing before solving, use this compact template (the
`route_and_solve` JSON schema in the validation harness uses these same
field names):

- `asked_output`: what the question literally wants.
- `decision_variable`: the one variable that determines the answer.
- `predicted_skill`: the best-matching skill ID (`skill1` … `skill22` or
  `NONE`).
- `closest_alternative_skill`: the closest wrong skill and a one-line
  reason for rejecting it.

---

## Programmatic Router (LLM call)

For the production pipeline, prefer the dedicated router LLM call
implemented in `llm_router.py`. It reads each `skill*/SKILL.md`'s
frontmatter `description`, builds the catalog automatically, and emits a
single line `Skill: <ID>`. This avoids the 22-row table being shipped
verbatim into every routing prompt and keeps the catalog in sync with
the source of truth (the SKILL.md files) without any manual copying.

```python
from llm_router import build_router_prompt, parse_router_choice, get_skill_prompt
prompt = build_router_prompt(story, question, options, labels)
choice = parse_router_choice(model.interact(prompt, max_tokens=64)) or "NONE"
skill_text = get_skill_prompt(choice)   # None for NONE → vanilla fall-back
```

---

## General Rule

> If two skills seem plausible, prefer the one that is **narrower** and
> keyed to the **explicit question form**, not to the overall story
> theme.
