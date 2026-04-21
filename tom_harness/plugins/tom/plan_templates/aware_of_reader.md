---
name: aware_of_reader_planning
skill_id: tpl_aware_of_reader
description: Plan skeleton for audience-adaptation / communication-style tasks.
triggers:
  - "explain to"
  - "audience"
  - "how should"
---

## Workflow

1. **Speaker profile** — expertise level and domain of the speaker.
2. **Listener profile** — expertise level and domain of the listener.
3. **Register detection** — classify each option by its technical register
   (expert jargon / analogy-based / beginner-friendly / mixed).
4. **Match register to listener** — the correct option is the one whose
   register best fits the listener's level. Experts don't need analogies;
   novices do.

## Common traps

- Picking the most accurate/complete option instead of the most
  *communicable* one.
- Ignoring domain mismatch (e.g., basketball analogy to a non-basketball-fan).

## Output shape

`{ "speaker_level": "expert|novice", "listener_level": "expert|novice", "answer_letter": "B" }`
