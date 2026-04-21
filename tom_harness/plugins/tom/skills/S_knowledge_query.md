---
skill_id: S_knowledge_query
name: Knowledge Query (Pure Python)
description: Does a character know a declared fact? Returns yes / no / unknown based on StoryModel.declarations. Zero LLM calls.
triggers:
  - "Does X know"
  - "Is X aware"
  - "X知道"
---

## Why this exists

Faux-pas and knowledge-gate questions hinge on whether a character has
explicit knowledge of a fact. The StoryModel's `declarations` list
captures this cleanly:
- `known_by[character]` → yes
- `not_known_by[character]` → no
- neither → unknown (downstream should apply implicit-knowledge
  inference via `S06_implicit_knowledge`)

## Input

```json
{
  "story_model": { ... },
  "character": "Li Na",
  "subject": "Uncle Liu",
  "predicate": "retired"
}
```

## Output

```json
{"character": "Li Na", "subject": "Uncle Liu",
 "predicate": "retired", "verdict": "yes"}
```

## Coupling with S06

If this skill returns `verdict: unknown`, the planner should route to
`S06_implicit_knowledge`, which handles contextually-inferable knowledge
that isn't explicitly stated. Most faux-pas errors live in that gap.
