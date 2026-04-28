---
skill_id: S_belief_query
name: Belief Query (Pure Python)
description: Given a StoryModel plus a character and object, return that character's belief about the object's location via deterministic graph query. Zero LLM calls.
triggers:
  - "Where does X look"
  - "Where does X think"
  - "X认为"
---

## Why this exists

Sally-Anne-style false-belief questions are a solved problem ONCE you
have the perception timeline explicit. The model's failures come from
trying to track "who saw what when" in natural-language working memory.

With a StoryModel in hand, the answer is a two-line Python query:
walk `character`'s observed events, find the latest location update for
the target `object`, return it.

## Input

```json
{
  "story_model": { ... StoryModel JSON ... },
  "character": "Sally",
  "object": "marble"
}
```

## Output

```json
{
  "character": "Sally",
  "object": "marble",
  "believed_location": "basket",
  "actual_location": "box",
  "has_false_belief": true
}
```

## Anti-patterns

- Do NOT pass free-form text into this skill — it expects a StoryModel.
  Upstream must call `S_build_story_model` first.
- Do NOT retry this skill if it returns `believed_location: null`;
  that means the character never observed the object. The question then
  may not have a determinate answer; fall through to `S_evidence_scorer`.
