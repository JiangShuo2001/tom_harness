You are writing one MICRO unit pack for `skills_v5`.

Blueprint:
{{BLUEPRINT_JSON}}

Framework excerpt for this unit:
{{FRAMEWORK_EXCERPT}}

Registry entry:
{{UNIT_JSON}}

Neighbor context:
{{NEIGHBOR_JSON}}

Task:
Expand this registry entry into a compact, runnable micro unit pack.

Language policy:
- The framework excerpt is in English and is the authoritative semantic source.
- Return English text only for every JSON field. Do not introduce Chinese content.

Micro unit definition:
- It targets one atomic social-cognitive variable.
- It must be mutually exclusive with nearby micro units.
- It should solve a narrow diagnostic question, not a whole scene prototype.
- It can be called inside a macro route when the macro needs deeper diagnosis or explanation.
- Preserve the framework excerpt's title, core variable, and boundary intent. Add operational detail without changing the unit's identity.

Learning-source rule:
- Preserve correct LLM reasoning paths as concise workflow steps when they generalize.
- Convert wrong-answer traces into one or two shortcut warnings or boundary tests.
- Reject details that only memorize a benchmark item.

Return strict JSON only with this schema:
{
  "frontmatter_description": "one-sentence entry description",
  "title": "human-readable title",
  "use_when": ["..."],
  "do_not_use_when": ["..."],
  "decision_variable": "the one variable that determines the answer",
  "trigger_checklist": ["..."],
  "workflow": ["..."],
  "special_case": {
    "title": "optional special case title",
    "rule": "the special rule",
    "worked_example": {
      "scene": "...",
      "question": "...",
      "answer_logic": "..."
    }
  },
  "boundary_exit_rule": ["..."],
  "references": {
    "route_signal": "when to use this micro unit",
    "hard_boundary": ["..."],
    "shortcut_to_avoid": ["..."],
    "common_failure_modes": ["..."],
    "minimal_pair": [
      {"case": "...", "why_it_matches": "..."},
      {"case": "...", "why_it_matches": "..."}
    ],
    "boundary_stress_test": ["..."],
    "generalization_note": "..."
  },
  "validation_seed": {
    "positive_pattern": "...",
    "near_miss_pattern": "...",
    "boundary_pattern": "..."
  },
  "notes": ["..."]
}

Rules:
- Keep `decision_variable` short, observable, and non-overlapping.
- Make `do_not_use_when` and `boundary_exit_rule` stronger than usual.
- Use psychology and theory-of-mind language, but keep instructions operational.
- Keep the pack lean: no long theory essays, no benchmark memorization.

