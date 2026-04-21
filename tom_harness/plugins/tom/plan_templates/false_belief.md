---
name: false_belief_planning
skill_id: tpl_false_belief
description: Recommended plan skeleton for first-order false-belief tasks.
triggers:
  - "false belief"
  - "错误信念"
  - "left the room"
---

## Workflow

1. **Character inventory** — identify every named agent in the story.
2. **Perception timeline** — for each agent, list which events they witnessed.
3. **Belief assignment** — for each agent, compute their belief about the
   object/state of interest at the time the question is asked.
4. **Option alignment** — compare each option against the belief-state dict
   and pick the unique match. Reject options that reflect *reality* rather
   than the asked agent's belief.

## Common traps

- Using the real final state instead of the agent's belief state.
- Forgetting to check whether the asked agent was absent at state-change time.

## Output shape

`{ "agent": "<who>", "belief": "<what they think>", "answer_letter": "A|B|C|D" }`
