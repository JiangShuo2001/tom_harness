You are generating a validation pack for one `skills_v5` unit.

Unit pack:
{{UNIT_PACK_JSON}}

Task:
Create a small validation pack with positive, near-miss, and boundary cases.

Language policy:
- Return English text only for every JSON field.

Return strict JSON only with this schema:
{
  "unit_id": "micro-01",
  "items": [
    {
      "id": "case_1",
      "pattern": "positive | near_miss | boundary",
      "scene": "...",
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "labels": ["A", "B", "C", "D"],
      "gold_answer": "A",
      "why_this_case_matters": "..."
    }
  ]
}

Rules:
- Generate exactly 3 to 5 items.
- Keep cases close to the unit's boundary.
- At least one item should be a direct positive match.
- At least one item should be a hard boundary or near-miss.
- Include one case inspired by a likely wrong reasoning shortcut.
- `gold_answer` must exactly match one entry in `labels`, and each label should map to an option.
- Keep the language concise and benchmark-like.
