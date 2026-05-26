# Skills v5 Framework-Driven Generation

`skills_v5/generate_skill` is a runnable LLM-centered pipeline for producing the v5 social-mind skill library. The generation source of truth is the English framework file `social_mind_skill_framework_en.md`, supported by `skill_blueprint.json`.

The Chinese file `../social_mind_skill_framework_text.md` and the `.svg` / `.jpg` files are reference materials for human review. They are not read by the generator by default.

## Design stance

- 56 `micro-xx` units are atomic, diagnostic, and low-overlap with explicit boundaries.
- 20 `macro-xx` units are direct-route scene prototypes, not bundles of micro units.
- Micro and macro units use different generation prompts.
- The prompt input, framework text, generated registry fields, and rendered `SKILL.md` files are English.
- Both levels share one English framework text, one blueprint, one registry, and one audit layer.
- Route selection is handled by the L0 micro units.
- Macro units carry concrete `expandable_micro_ids`, not loose theme labels.
- Correct reasoning traces can strengthen workflows; wrong-answer traces can become boundary warnings.
- Feedback is selective and approval-gated. The generator never applies feedback or freezes a version automatically.

## Borrowed strengths

From `skills_v1`:

- error-cluster refinement
- validation packs
- boundary stress tests
- learning from correct and wrong solution paths

From `skills_v4`:

- one folder per routable unit
- `SKILL.md` as the compact contract
- `references/examples.md` for boundaries and minimal pairs
- compact frontmatter, decision variables, and boundary descriptions

## Output layout

```text
generated/<run_id>/
|-- manifest.json
|-- skill_registry.json
|-- audit_report.json
|-- feedback_candidates.json       # optional; candidates only
|-- approval_template.json         # optional; user fills approved_patch_ids
|-- micro-01/
|   |-- SKILL.md
|   |-- unit_pack.json
|   |-- references/examples.md
|   `-- validation_items.json       # optional
`-- macro-20/
    |-- SKILL.md
    |-- unit_pack.json
    |-- references/examples.md
    `-- validation_items.json       # optional
```

## Setup

```powershell
pip install requests
$env:SKILL_V5_API_KEY="your_api_key"
$env:SKILL_V5_MODEL="gpt-5.4-mini"
```

Optional endpoint variables:

```powershell
$env:SKILL_V5_BASE_URL="https://api.openai.com/v1"
$env:SKILL_V5_REASONING_EFFORT="medium"
$env:SKILL_V5_RUN_TIMEOUT="240"
$env:SKILL_V5_RUN_MAX_TOKENS="16384"
```

## Commands

Generate a complete run:

```powershell
python skill_generator.py run --validation
```

Generate only the shared registry:

```powershell
python skill_generator.py plan --out generated\plan_test
```

Use an existing registry and regenerate selected units:

```powershell
python skill_generator.py run --registry generated\run_x\skill_registry.json --only micro-01 macro-05 --out generated\rerun_selected
```

Partial `--only` runs skip full-library audit by default, because only selected unit folders exist in the output. Add `--audit-partial` when you want an audit focused on the generated subset.

Audit an existing run:

```powershell
python skill_generator.py audit --run generated\run_x
```

Generate selective feedback candidates from traces:

```powershell
python skill_generator.py feedback --run generated\run_x --traces traces.jsonl
```

This writes `feedback_candidates.json` and `approval_template.json`. It does not modify any `SKILL.md` file.

Apply only manually approved patches:

```powershell
# Edit approval_template.json and fill approved_patch_ids first.
python skill_generator.py apply --run generated\run_x --approval generated\run_x\approval_template.json
```

Freeze only after manual approval:

```powershell
python skill_generator.py freeze --run generated\run_x --tag v5-approved-001 --approved-by-user
```

## Trace format

`feedback` accepts JSON or JSONL. Useful fields are:

```json
{
  "unit_id": "macro-05",
  "kind": "wrong",
  "scene": "...",
  "question": "...",
  "gold_answer": "...",
  "model_answer": "...",
  "reasoning": "...",
  "error_type": "shortcut_or_boundary_error",
  "lesson": "..."
}
```

Correct traces can be marked with `kind: "correct"` or `is_correct: true`. Wrong traces can be marked with `kind: "wrong"` or `is_correct: false`.

## Approval policy

Feedback and freezing are two explicit gates:

1. `feedback` proposes small candidate patches only.
2. The user reviews and adds patch ids to `approval_template.json`.
3. `apply` updates only those approved patch ids and re-renders the affected unit files.
4. `freeze` snapshots a reviewed run only when `--approved-by-user` is passed.

This keeps `SKILL.md` concise while still allowing the library to learn from real failures.
