---
skill_id: S08_perception_timeline
name: Perception Timeline (False Belief Backbone)
description: Build a per-character timeline of what each agent has perceived vs. what has happened while they were absent. This is the causal substrate every false-belief and knowledge question relies on.
triggers:
  - "leaves"
  - "离开"
  - "while .+ is away"
  - "enters"
---

## Problem this skill solves

The classical Sally-Anne pattern, but also any question whose answer
depends on **asymmetric observation**. Rather than trying to compute
belief states by template, build the substrate (who saw what when) and
derive the belief from it.

## Workflow

1. **List events** in temporal order: `E1, E2, ...`, each tagged with
   `{actor, observers, action, object?, location?}`.
2. **For each character**, compute `perceived[c] = {E_i : c ∈ observers[E_i]}`.
3. **Derive belief state** for each character as the latest state of the
   object/location in `perceived[c]`:
   - If object was moved in an event c did NOT observe, c's belief about
     object location = the pre-move location.
4. **For the queried character**, return `belief_state[queried_char]`.
5. **Handle sub-case: knowing agent**. If the query asks about the
   character who performed the last observed action, their belief ==
   reality (no false belief).

## Output shape

```json
{
  "events": [
    {"id": "E1", "actor": "Sally", "action": "put marble in basket",
     "observers": ["Sally", "Anne"], "object": "marble", "loc": "basket"},
    {"id": "E2", "actor": "Sally", "action": "leave room",
     "observers": ["Anne"], "object": null, "loc": null},
    {"id": "E3", "actor": "Anne", "action": "move marble",
     "observers": ["Anne"], "object": "marble", "loc": "box"}
  ],
  "perceived": {
    "Sally": ["E1", "E2"],
    "Anne":  ["E1", "E2", "E3"]
  },
  "belief_state": {
    "Sally": {"marble_location": "basket"},
    "Anne":  {"marble_location": "box"}
  },
  "queried_character": "Sally",
  "answer_letter": "A"
}
```

## Anti-patterns

- Do NOT skip the perception-timeline step even when the story is short;
  explicit structure prevents the model from accidentally cross-wiring
  characters' beliefs.
- Do NOT forget to include the character who performs an action in
  observers — actors are always observers of their own actions.
- Do NOT collapse perceive ≠ know: seeing a label on a box is not the
  same as knowing what's inside (see S03 for subject disambiguation).
