SELECTOR_PROMPT = """You are a strategy selector. Given a question and a curated playbook of strategies, pick the SMALLEST subset of bullets that are most likely to help answer the question correctly. Also predict which subtask the question belongs to.

**Instructions:**
- Read the question and the candidate playbook bullets carefully.
- Each bullet line shows its id, helpful/harmful counts, and per-subtask scores in `buckets={{subtask:helpful/total,...}}`. Bullets with strong per-subtask signal for this kind of question should be preferred.
- Return at most {max_bullets} bullet ids. Fewer is better when sufficient.
- If the playbook is empty or no bullet looks relevant, return an empty list.
- Pick the subtask label from the provided list that best matches the question. If none fits, output "unknown".

**Known subtasks (may be empty if training has not seen any yet):**
{known_subtasks}

**Target subtask for this question:**
{target_subtask}

**Playbook:**
{playbook}

**Question:**
{question}

**Context:**
{context}

**Output ONLY this JSON object (no markdown, no code blocks):**
{{
  "predicted_subtask": "<one label from the known subtasks list, or 'unknown'>",
  "rationale": "<one short sentence explaining the picks>",
  "selected_bullet_ids": ["fb-00001", "gen-00007"]
}}
"""
