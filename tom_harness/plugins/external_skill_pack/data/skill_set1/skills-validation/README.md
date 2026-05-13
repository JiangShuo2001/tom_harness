# Validation Packs

This validation folder now follows the original Tombench multiple-choice form as closely as possible.

- Validation items should keep original `options`, `correct_answer`, and `correct_answer_text`.
- The runner asks the model to choose exactly one option label.
- Main accuracy is computed by comparing the selected option label against the original correct option label.
- This makes the outputs easier to compare with prior Tombench-style runs.

Current validation is answer-centric. The next layer should be routing-centric: first test whether the model selected the right skill, then test whether the chosen skill improved the final answer.

Validation code now lives alongside these packs:

- `run_validation.py`: runner with pluggable API hook
- `example_api_adapter.py`: placeholder adapter reference
- `USAGE.md`: setup and command examples
- `rubric.md`: scoring interpretation guide
- `scoring_template.csv`: manual review template
- `routing_template.csv`: scaffold for future routing validation packs

The shared skill-boundary reference now lives in:

- `../ROUTING.md`

## Wrong Skill Mode

- `wrong_skill` now supports injecting a genuinely mismatched skill instead of reusing the target skill.
- Use `--wrong-skill-name <skillX>` to choose the mismatched skill manually.
- If not provided, the runner uses a built-in mapping:
  - `skill3 -> skill5`
  - `skill8 -> skill9`
  - `skill14 -> skill15`

This mode is useful because it separates two questions:

- Does the target skill help on in-domain items?
- Does a neighboring but wrong skill hurt or blur the decision boundary?

## Recommended Next Validation Layer

For future routing validation, add these fields to each item or to a paired routing sheet:

- `should_use_skill`: `yes`, `no`, or `boundary`
- `best_skill`: the intended primary skill
- `backup_skill`: the closest acceptable fallback skill when the boundary is soft
- `closest_wrong_skill`: the most likely confusion skill
- `decision_variable`: the variable the router should identify before solving

The recommended workflow is:

1. Route the item with `ROUTING.md` only.
2. Record whether the chosen skill matches `best_skill`.
3. Run answer validation with `baseline`, `with_skill`, and `wrong_skill`.
4. Compare answer gains against routing quality rather than accuracy alone.

## skill3
- title: FB-01 First-Order Location False Belief Validation Pack
- file: `skill3/validation_items.json`
- positives: 4
- near_miss: 3
- boundary: 3

## skill8
- title: UO-01 Atypical Emotion Attribution Validation Pack
- file: `skill8/validation_items.json`
- positives: 4
- near_miss: 3
- boundary: 3

## skill14
- title: SS-01 Truth Judgment For Mixed States Validation Pack
- file: `skill14/validation_items.json`
- positives: 4
- near_miss: 3
- boundary: 3
