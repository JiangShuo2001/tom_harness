# Skills Routing Guide

This file is the shared routing layer for the 15 mindreading skills.

Use it before opening a specific skill when the main uncertainty is not the answer itself, but which reasoning tool should be activated.

## Router First Principle

Route by the question's required output, not by the story's surface topic.

The same story can mention emotion, belief, dialogue, and deception at once. The correct skill is the one whose decision variable matches the asked output.

## Fast Routing Workflow

1. Identify the asked output.
2. Name the decision variable that determines that output.
3. Check the nearest neighboring skills before committing.
4. Use the narrowest skill that directly matches the asked output.
5. If the question changes from `what` to `why`, or from `truth` to `motive`, reroute.

## Family A: Social Harm And Knowledge

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill1` | Was a remark inappropriate? Which remark was inappropriate? | Whether a spoken line exposes a sensitive fact in a socially harmful way | The question targets the remark itself | `skill2` | If the question asks whether the speaker knew or remembered the fact, switch to `skill2` |
| `skill2` | Did X know, remember, or forget a fact? | The target person's access to the fact | The question targets knowledge, memory, awareness, or forgetting | `skill1` | If the question targets whether the line itself was socially wrong, switch to `skill1` |

## Family B: Belief Tracking

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill3` | Where will X look? | X's own last-seen location belief | One mind is queried and the object was moved unseen | `skill4`, `skill5` | If the question becomes `X thinks Y will look`, switch to `skill4`; if it becomes label-versus-content, switch to `skill5` |
| `skill4` | Where does X think Y will look? | X's model of Y's belief | Two minds are explicitly nested | `skill3`, `skill5` | If the outer thinker disappears, drop to `skill3`; if the issue is container content, switch to `skill5` |
| `skill5` | What is in the container? What will someone think is inside? | Appearance or label versus real content | The conflict is about expected contents, not physical search location | `skill3`, `skill4` | If the story is about moved-object search, route back to `skill3` or `skill4` |

## Family C: Social Cue Interpretation

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill6` | What does the observer think, feel, or do after a cue? | The observer's inferred belief from limited visible evidence | The output is the observer's reaction | `skill7`, `skill12` | If the task asks why the sender made the cue, switch to `skill7`; if it is indirect meaning from words rather than a cue, switch to `skill12` |
| `skill7` | Why did the sender smile, wink, glance, or nudge? | The sender's hidden local goal | The output is the sender's intention behind a nonverbal cue | `skill6`, `skill12` | If the output is the observer's reaction, switch to `skill6`; if the signal is verbal rather than nonverbal, switch to `skill12` |
| `skill12` | What does the speaker really mean? What do they want the listener to do? | Hidden speech act behind literal words | The output is request, complaint, warning, refusal, reminder, or invitation | `skill7`, `skill13` | If the signal is a cue rather than speech, switch to `skill7`; if the task asks how to persuade someone, switch to `skill13` |

## Family D: Emotion And Appraisal

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill8` | What emotion does the character feel? | Character-specific appraisal override | The output is the emotion label itself | `skill9`, `skill14` | If the question asks why the surprising emotion occurs, switch to `skill9`; if it asks whether an emotion statement is true, switch to `skill14` |
| `skill9` | Why does the character feel this surprising emotion? | Hidden prior cause that flips the expected appraisal | The question explicitly asks for explanation of the reversal | `skill8` | If the task only asks which emotion fits, drop back to `skill8` |

## Family E: Quantitative Scalar Reasoning

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill10` | What is the best estimate before observation? | Scalar phrase to prior-count mapping | The question is about a vague proportion before any update | `skill11` | If part of the set has been observed and the question asks for a revised estimate, switch to `skill11` |
| `skill11` | What is the best estimate after partial observation? | Posterior update from prior plus observed subset | The question asks for a revised whole-set estimate | `skill10` | If there is no observation update, drop back to `skill10` |

## Family F: Influence And Strategy

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill13` | How should one character persuade another? | Listener-specific barrier or incentive | The output is the best influence strategy | `skill12` | If the task is decoding what a sentence already means, switch to `skill12` |

## Family G: Truth And Motive

| Skill | Core Question | Decision Variable | Use When | Nearest Confusion | Handoff Rule |
| --- | --- | --- | --- | --- | --- |
| `skill14` | Is the statement true? | Whether the proposition matches any genuine part of the speaker's state | The task is a yes-no truth judgment under mixed states, partial truth, or conflict | `skill15`, `skill8` | If the question asks why the speaker said it, switch to `skill15`; if it asks only for an emotion label, switch to `skill8` |
| `skill15` | Why did the speaker say that? | Motive for a false, partial, selective, polite, or mistaken statement | The task is explanation of wording choice | `skill14`, `skill12` | If the task asks whether the statement is true, switch to `skill14`; if it asks for indirect speech meaning rather than motive under conflict, switch to `skill12` |

## High-Value Boundary Checks

### `skill1` vs `skill2`

- Ask: are we judging the remark, or the speaker's access to the hidden fact?
- `skill1` is about social harm.
- `skill2` is about knowledge state.

### `skill3` vs `skill4` vs `skill5`

- Ask: is this about search location or expected contents?
- If search location: count minds.
- One mind means `skill3`.
- Two nested minds means `skill4`.
- Label or appearance versus real contents means `skill5`.

### `skill6` vs `skill7` vs `skill12`

- Ask: whose mind is the output about?
- Observer reaction means `skill6`.
- Sender intention behind a nonverbal cue means `skill7`.
- Hidden meaning of spoken words means `skill12`.

### `skill8` vs `skill9`

- Ask: are we selecting the emotion, or explaining the reversal?
- Emotion label only means `skill8`.
- Why this surprising emotion means `skill9`.

### `skill10` vs `skill11`

- Ask: before observation or after observation?
- Prior estimation means `skill10`.
- Posterior update means `skill11`.

### `skill12` vs `skill13`

- Ask: decode meaning, or choose strategy?
- Existing utterance's hidden speech act means `skill12`.
- Best way to influence a listener means `skill13`.

### `skill14` vs `skill15`

- Ask: truth status or motive explanation?
- Yes-no truth judgment means `skill14`.
- Why the wording was chosen means `skill15`.

## Router Output Template

When routing before solving, use this compact template.

- `Asked output`: what the question literally wants.
- `Decision variable`: the one variable that determines the answer.
- `Chosen skill`: the best-matching skill.
- `Rejected neighbor`: the closest wrong skill and why it does not fit.

## General Rule

If two skills seem plausible, prefer the one that is narrower and keyed to the explicit question form rather than to the overall story theme.
