You are designing the registry for `skills_v5`.

Blueprint:
{{BLUEPRINT_JSON}}

Authoritative framework text:
{{FRAMEWORK_TEXT}}

Task:
Create a complete registry with exactly 56 micro units and 20 macro units.

Language policy:
- The prompt input, authoritative framework, and all generated registry fields are in English.
- Return English text only. Do not introduce Chinese titles, explanations, or notes.

Core requirements:
- Micro units must target one primary capability with low overlap and explicit boundaries.
- Macro units must be directly routable scene prototypes.
- A scene that resembles a macro prototype may route directly to that macro unit.
- Micro units remain available as diagnostic and explanatory submodules.
- Fuse benchmark coverage and real-world social coverage.
- Prefer theory-of-mind and psychology language over benchmark labels.
- Use the layer system in the blueprint.
- Treat the authoritative framework text as the source of truth for unit ids, titles, core variables, boundaries, and macro-to-micro expansion ids.
- Do not rename or reorder the framework's unit ids.

Return strict JSON only with this schema:
{
  "library_name": "skills_v5",
  "micro_units": [
    {
      "id": "micro-01",
      "level": "micro",
      "layer": "L0",
      "family": "short family label",
      "title": "short readable title",
      "core_question": "the asked output this unit solves",
      "decision_variable": "the single variable that determines the answer",
      "use_when": ["..."],
      "do_not_use_when": ["..."],
      "boundary_neighbors": ["micro-02", "micro-03"],
      "source_mix": ["benchmark", "psychology", "real-world"]
    }
  ],
  "macro_units": [
    {
      "id": "macro-01",
      "level": "macro",
      "layer": "macro",
      "family": "short family label",
      "title": "short readable title",
      "core_question": "the scene prototype this unit solves",
      "decision_variable": "the single variable that determines the answer",
      "direct_route_rule": "when to route here immediately",
      "expandable_micro_ids": ["micro-05", "micro-08"],
      "boundary_neighbors": ["macro-02", "macro-03"],
      "source_mix": ["benchmark", "psychology", "real-world"]
    }
  ],
  "coverage_map": {
    "benchmark": ["..."],
    "real_world": ["..."]
  },
  "generation_notes": ["..."]
}

Ordering rule:
- Put all micro units first.
- Then put all macro units.
- Ids must be stable and unique.

Style rule:
- Make the registry psychologically meaningful.
- Make the macro units feel like reusable scene priors.
- Keep the decision variable short and concrete.
- Keep overlap low among micro units.
- For each macro unit, copy the concrete expandable micro ids from the framework text. Do not replace them with theme labels.

