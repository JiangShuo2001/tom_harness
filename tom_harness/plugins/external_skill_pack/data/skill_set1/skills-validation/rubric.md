# Validation Rubric

Use this rubric to compare `baseline`, `with_skill`, and optionally `wrong_skill` runs.

## Current Answer-Validation Fields

- `item_id`: stable item id from `validation_items.json`
- `run_type`: baseline | with_skill | wrong_skill
- `should_trigger_skill`: yes | no | boundary
- `did_trigger_skill_correctly`: yes | no
- `decision_variable_identified`: yes | no
- `shortcut_avoided`: yes | no
- `boundary_respected`: yes | no
- `option_correct`: yes | no
- `notes`: short explanation of the model's reasoning quality

## Scoring Guide

- `did_trigger_skill_correctly`: Did the model pick the right skill behavior for this item?
- `decision_variable_identified`: Did it use the variable named in the skill reference, rather than a surface cue?
- `shortcut_avoided`: Did it avoid the banned heuristic listed under `Shortcut To Avoid`?
- `boundary_respected`: Did it avoid crossing into a neighboring skill when the item was near-miss or boundary?
- `option_correct`: Did the selected option label match the gold multiple-choice answer?

## Recommended Routing-Validation Fields

These are not yet auto-scored by `run_validation.py`, but they are the recommended next layer.

- `best_skill`: the primary intended skill for the item
- `backup_skill`: closest acceptable fallback when the boundary is soft
- `closest_wrong_skill`: the most likely confusion skill
- `router_decision_variable`: the variable the router should name before solving
- `routing_correct_strict`: whether the chosen skill equals `best_skill`
- `routing_correct_relaxed`: whether the chosen skill equals `best_skill` or `backup_skill`

## Success Criteria

A skill is promising when:
- `with_skill` beats `baseline` on positives
- `with_skill` does not degrade badly on near-miss items
- `with_skill` does not over-trigger on boundary items
- gains in accuracy are accompanied by gains in `decision_variable_identified`

A routing layer is promising when:

- strict routing is high on clear positive items
- relaxed routing stays high on boundary items
- `wrong_skill` performs worse than `with_skill` on the same items
- routing gains translate into answer gains rather than just better self-report fields
