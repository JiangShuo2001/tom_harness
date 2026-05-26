You are writing one MACRO unit pack for `skills_v5`.

Blueprint:
{{BLUEPRINT_JSON}}

Framework excerpt for this unit:
{{FRAMEWORK_EXCERPT}}

Registry entry:
{{UNIT_JSON}}

Neighbor context:
{{NEIGHBOR_JSON}}

Task:
Expand this registry entry into a compact, runnable macro scene-prototype unit pack.

Language policy:
- The framework excerpt is in English and is the authoritative semantic source.
- Return English text only for every JSON field. Do not introduce Chinese content.

Macro unit definition:
- It is not merely a bundle of micro units.
- It can directly solve a matching scene by using a reusable scene prior.
- It should state the canonical scene structure, direct route rule, and answer logic. A matching scene may route here directly even if micro-level diagnosis could also help.
- Micro units are optional expansions for diagnosis, boundary repair, and explanation.
- Preserve the framework excerpt's scene core variable, boundary, and concrete micro expansion ids.

Learning-source rule:
- Preserve correct LLM reasoning paths as canonical scene workflow when they generalize.
- Convert wrong-answer traces into failure-mode warnings, boundary exits, or micro-expansion triggers.
- Reject details that would bloat the skill or memorize a single benchmark item.

Return strict JSON only with this schema:
{
  "frontmatter_description": "one-sentence direct-route description",
  "title": "human-readable title",
  "use_when": ["..."],
  "do_not_use_when": ["..."],
  "decision_variable": "the main scene variable that determines the answer",
  "direct_route_rule": "when to route here immediately and solve directly",
  "expandable_micro_ids": ["micro-05", "micro-08"],
  "trigger_checklist": ["canonical scene features"],
  "workflow": ["direct scene-solution steps"],
  "special_case": {
    "title": "optional special case title",
    "rule": "the special rule",
    "worked_example": {
      "scene": "...",
      "question": "...",
      "answer_logic": "..."
    }
  },
  "boundary_exit_rule": ["when to leave this macro or add a micro unit"],
  "references": {
    "route_signal": "scene prototype signal",
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
- The direct route rule must be strong enough to solve similar scenes immediately.
- Do not reduce the macro to a list of micro units.
- Include concrete micro ids only as optional repair or explanation.
- Keep the pack lean and router-friendly.

