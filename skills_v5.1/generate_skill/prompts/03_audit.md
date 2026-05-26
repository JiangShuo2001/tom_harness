You are auditing the generated `skills_v5` library.

Blueprint:
{{BLUEPRINT_JSON}}

Authoritative framework text:
{{FRAMEWORK_TEXT}}

Registry summary:
{{REGISTRY_SUMMARY_JSON}}

L0 meta-control micro units:
{{L0_META_CONTROL_JSON}}

Generated unit summary:
{{UNIT_SUMMARY_JSON}}

Audit scope:
{{AUDIT_SCOPE}}

Audit chunk note:
{{AUDIT_CHUNK_NOTE}}

Task:
Identify coverage gaps, overlap risks, boundary confusions, weak descriptions, and bloat risks.

Language policy:
- Return English text only for every JSON field.
- Treat the English framework text as authoritative.

Important v5 design rule:
- There is no separate routing document or top-level routing authority.
- L0 micro units carry meta-control: route selection, evidence discipline, uncertainty, and anti-bias checks.
- Macro units are direct-route scene prototypes.
- Micro units are atomic diagnostic modules.
- Audit whether the generated L0 units are sufficient to replace any separate routing document.

Return strict JSON only with this schema:
{
  "coverage_gaps": ["..."],
  "l0_meta_control_gaps": ["..."],
  "overlap_risks": [
    {"unit_a": "micro-01", "unit_b": "micro-02", "reason": "..."}
  ],
  "boundary_confusions": [
    {"unit": "macro-01", "nearby_unit": "macro-02", "reason": "..."}
  ],
  "bloat_risks": [
    {"unit": "macro-01", "reason": "..."}
  ],
  "rewrite_targets": ["micro-01", "macro-01"],
  "summary": "..."
}

Audit priorities:
- Missing benchmark coverage.
- Missing real-world social coverage.
- Micro-unit overlap.
- Macro-unit direct-route ambiguity.
- Weak L0 route-selection / evidence / uncertainty / anti-bias coverage.
- Confused handoff between macro direct route and micro expansion.
- Skill files that include too many examples or too much theory.
- If audit scope is `partial`, do not report missing ungenerated units as coverage gaps. Focus on generated units and their relationship to the authoritative framework.
- Compare macro expansion ids against the framework text; theme-only expansion is a defect.

