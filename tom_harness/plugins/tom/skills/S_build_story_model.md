---
skill_id: S_build_story_model
name: Build Externalized StoryModel
description: Parse the story ONCE into a Pydantic-validated StoryModel (events, observers, declarations). Required prerequisite for S_belief_query and S_knowledge_query.
triggers:
  - "before answering any belief or knowledge question"
---

## Why this exists

LLMs are bad at maintaining solid state across a reasoning chain. They
are great at structured parsing. So: **parse once, query many times**.

This skill converts the story into a Pydantic object whose fields have
strict semantics. Downstream skills (`S_belief_query`, `S_knowledge_query`)
read that object with deterministic Python code — no more LLM drift on
"whose belief was updated when".

## Output shape

See `plugins/tom/story_model.py:StoryModel` for the canonical schema:
sentences, characters, events (with observers + to_location), declarations
(with known_by / not_known_by lists).

## Critical parsing rules

- The actor of an event is ALWAYS an observer of that event.
- If the story says "X leaves" before an event, X must NOT be an observer
  of that event.
- Declarations with "never seen / unaware / does not know" populate
  `not_known_by`. Do NOT fabricate knowledge gaps.

## Usage

```json
{
  "tool_type": "skill",
  "tool_name": "execute_skill",
  "tool_params": {
    "skill_id": "S_build_story_model",
    "input_context": {"story": "<full story text>"}
  }
}
```
