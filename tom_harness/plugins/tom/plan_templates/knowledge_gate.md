---
name: knowledge_gate_planning
skill_id: tpl_knowledge_gate
description: Plan skeleton for tasks where a character has never encountered X.
triggers:
  - "never seen"
  - "一无所知"
  - "从未见过"
---

## Workflow

1. **Identify the knowledge-gap declaration** — find the explicit sentence
   stating that some agent does NOT know some entity.
2. **Build knows/not_knows map** — structured dict per character.
3. **Filter options via knowledge gate** — reject every option that
   presupposes the agent has knowledge they lack.
4. **Pick from remaining** — if exactly one option survives, that is the
   answer. If multiple survive, default to the most generic/ambiguous one.

## Common traps

- Applying reader-level knowledge to the character.
- Letting the most salient option dominate even when it violates the gate.

## Output shape

`{ "blocked_options": ["A","C"], "survived_options": ["B","D"], "answer_letter": "B" }`
