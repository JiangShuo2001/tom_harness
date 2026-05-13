# Validation Runner Usage

## Files

- `run_validation.py`: main validation runner
- `example_api_adapter.py`: placeholder API adapter
- `rubric.md`: how to interpret the scoring fields
- `scoring_template.csv`: manual template for external review
- `routing_template.csv`: scaffold for manual or future automatic routing evaluation

## API Setup

The runner is already wired to the OpenAI Python SDK with the OpenRouter endpoint.

Before running, set:

```bash
set OPENROUTER_API_KEY=your_openrouter_key
```

The script uses:
- `base_url=https://openrouter.ai/api/v1`
- `OpenAI` client from the `openai` package
- `extra_body={reasoning: {enabled: True}}`

If you want a different provider later, edit `call_model_api()` in `run_validation.py`.

For slower models or free endpoints, you can also tune:
- `--timeout 180`
- `--max-retries 3`
- `--disable-reasoning`
- `--limit 1`

## Example Commands

```bash
python skills/skills-validation/run_validation.py --skill skill3 --model your-model-name
python skills/skills-validation/run_validation.py --skill skill8 --model your-model-name --run-types baseline with_skill wrong_skill
python skills/skills-validation/run_validation.py --skill skill14 --model your-model-name --temperature 0.0
python skills/skills-validation/run_validation.py --skill skill3 --model google/gemma-4-31b-it:free
python skills/skills-validation/run_validation.py --skill skill3 --model google/gemma-4-31b-it:free --limit 1 --disable-reasoning --timeout 180 --max-retries 3
python skills/skills-validation/run_validation.py --mode route_and_solve --pack gpt54mini_positive_routing_pack.json --model openai/gpt-5.4-mini
python skills/skills-validation/run_validation.py --mode route_and_solve --model openai/gpt-5.4-nano --limit 20
```

## Output Layout

Results are written under:

`skills/skills-validation/results/<skill>/<model>/`

Files:
- `raw_results.json`
- `summary.json`
- `scored_rows.csv`

These files currently score answer accuracy, not routing accuracy.

For routing analysis, use `skills/ROUTING.md` together with `routing_template.csv` to record:

- whether the item should trigger a skill at all
- the best skill
- the nearest confusing skill
- the decision variable the router should have identified

For one-call route-and-solve runs, results are written under:

`skills/skills-validation/results/<pack_name>/<model>/route_and_solve/`

The main files are still:
- `raw_results.json`
- `summary.json`
- `scored_rows.csv`

The `summary.json` for route-and-solve includes:
- `routing_accuracy`
- `answer_accuracy`
- `both_accuracy`
- per-skill routing and answer metrics
- routing confusion counts

## Expected Model Output Schema

The prompt now follows Tombench-style multiple-choice evaluation and asks the model to return strict JSON with these keys:

- `selected_option_label`
- `selected_option_text`
- `reasoning_summary`
- `should_trigger_skill`
- `did_trigger_skill_correctly`
- `decision_variable_identified`
- `shortcut_avoided`
- `boundary_respected`
- `notes`

Main accuracy is computed from whether `selected_option_label` matches the original `correct_answer` option label in the validation item.

## Recommended Two-Stage Evaluation

For higher-quality optimization, use two stages instead of looking only at final accuracy.

1. Routing stage

- Use `skills/ROUTING.md`.
- Decide `best_skill`, `backup_skill`, and `closest_wrong_skill`.
- Record the result in `routing_template.csv` or an equivalent JSON pack.

2. Answer stage

- Run `baseline` to see the model's unaided answer quality.
- Run `with_skill` to see whether the intended skill improves performance.
- Run `wrong_skill` to test whether a neighboring but wrong skill degrades or blurs the boundary.

This separation matters because a skill can be good while the router is bad, or vice versa.

## One-Call Route-And-Solve Mode

If you care more about cost and end-to-end behavior than about perfectly isolating routing from solving, use `--mode route_and_solve`.

In this mode, the model gets:
- `ROUTING.md`
- a compact registry distilled from all 15 skills
- the multiple-choice item

It must return, in one JSON object:
- `predicted_skill`
- `selected_option_label`
- `selected_option_text`
- `decision_variable`
- `routing_reasoning_summary`
- `answer_reasoning_summary`
- `closest_alternative_skill`
- `notes`

This lets one API call evaluate both `did the model route correctly?` and `did it answer correctly after choosing that skill?`

## Recommended Secret Handling

- Do not hardcode the API key inside the script.
- Prefer an environment variable such as `OPENROUTER_API_KEY`.
