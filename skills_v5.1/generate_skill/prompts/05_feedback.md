You are proposing selective feedback patches for one `skills_v5` unit.

Blueprint:
{{BLUEPRINT_JSON}}

Current unit pack:
{{UNIT_PACK_JSON}}

Audit report:
{{AUDIT_JSON}}

Correct and wrong reasoning traces:
{{TRACE_JSON}}

Maximum patches for this unit: {{MAX_PATCHES}}

Task:
Propose only high-value candidate patches. Do not rewrite the whole unit.

Language policy:
- Return English text only for every JSON field and every patch value.

Selection policy:
- Keep patches sparse. If there is no durable lesson, return an empty patch list.
- Prefer adding one boundary, shortcut warning, or workflow step over long examples.
- Preserve correct reasoning paths only when they generalize beyond one item.
- Use wrong-answer traces to prevent recurring errors through concise warnings or boundary tests.
- Reject patches with high bloat risk unless they fix a severe routing or reasoning failure.

Return strict JSON only with this schema:
{
  "patches": [
    {
      "patch_id": "macro-05-p1",
      "target_id": "macro-05",
      "op": "append | extend | set | merge | remove",
      "path": "references.shortcut_to_avoid",
      "value": "concise patch value",
      "priority": 1,
      "rationale": "why this patch helps generalization",
      "bloat_risk": "low | medium | high"
    }
  ]
}

Supported paths include:
- use_when
- do_not_use_when
- trigger_checklist
- workflow
- boundary_exit_rule
- references.hard_boundary
- references.shortcut_to_avoid
- references.common_failure_modes
- references.boundary_stress_test
- references.generalization_note

The code enforces this path whitelist. Do not propose any other path.

Rules:
- Do not propose more than {{MAX_PATCHES}} patches.
- Do not propose a patch that copies a full trace into the skill.
- Do not invent new unit ids.
- Prefer `append` for one concise item and `extend` only for two or three short items.
