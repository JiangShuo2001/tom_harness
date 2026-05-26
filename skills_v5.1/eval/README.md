# skills_v5 evaluation

Evaluate the 76-skill library against ToMBench (2860 items × EN + ZH).

## Layout

```
skills_v5/
├── data/
│   ├── build_dataset.py        # split source ToMBench → bilingual jsonl
│   ├── ToMBench_en.jsonl       # 2860 items
│   └── ToMBench_zh.jsonl       # 2860 items
├── eval/
│   ├── eval_tombench.py        # main runner
│   ├── runs/<run_id>/
│   │   ├── config.json
│   │   ├── results.jsonl       # one row per item (resumable)
│   │   └── summary.json
│   ├── README.md
│   └── .env.example
└── skills/                     # 20 macros + 56 micros (4 L0 + 52 others)
```

## Pipeline (4 stages per item)

```
[1] route prep    inject micro-01 (task routing) as router system prompt
[2] route         pick 0+ skills (depends on --route-mode)
[3] solve         picked skills injected; LLM outputs draft letter
[4] review (opt)  if --review-mode on: inject micro-02 + micro-03 + micro-04
                  with the draft, LLM outputs final letter (= draft if no
                  change needed). Both draft and final are recorded so the
                  review lift can be measured without a second run.
```

L0 micros (`micro-01..04`) are reserved for stages 1 and 4. They never appear
as candidates in stages 2–3; the 52 non-L0 micros + 20 macros are the
route-able pool.

## Routing modes (`--route-mode`)

| mode           | candidate pool                                              | LLM router calls | output |
| -------------- | ----------------------------------------------------------- | ---------------- | ------ |
| `baseline`     | (none — stage 2 skipped)                                    | 0                | none   |
| `macro_only`   | 20 macros                                                   | 1                | 0+ macros |
| `micro_only`   | 52 non-L0 micros                                            | 1                | 0+ micros |
| `hierarchical` | step1: 20 macros; step2: UNION of `expandable_micro_ids` of picked macros, OR all 52 non-L0 micros if step1 picked nothing | 1–2 | 0+ macros + 0+ micros |
| `flat_all`     | 72 skills (20 macros + 52 non-L0 micros)                    | 1                | 0+ skills |

Every routing step is allowed to answer `none`. In `hierarchical`, picking
`none` (or `[]`) in step 1 does NOT skip step 2 — instead step 2's candidate
pool widens to the full 52 non-L0 micros, so the LLM can still pick
diagnostic micros when no scene-prototype macro fits. To pick no skill at
all, the LLM must answer `none` at BOTH steps.

## Injection mode (`--inject-mode`)

Controls how ALL skill content is rendered — stage 1 micro-01, stage 3 routed
skills, and stage 4 review micros — uniformly per run.

| mode    | rendering                                              | size                   |
| ------- | ------------------------------------------------------ | ---------------------- |
| `full`  | the unit's complete SKILL.md text                       | ~4.5 KB / macro        |
| `light` | title + decision_variable + direct_route_rule (macro only) + workflow + special_case.worked_example + boundary_exit_rule | ~50% of full |

## Review mode (`--review-mode`)

| value | stage 3 solver output                                       | stage 4                                                                                                                                                           | LLM calls per item |
| ----- | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| `off` | letter only                                                 | skipped; final letter == draft                                                                                                                                    | —                  |
| `on`  | structured `REASONING: …\nANSWER: <letter>` (forced format) | reviewer sees the solver's picked skills + reasoning + draft letter, audits via micro-02/03/04, outputs its own `REASONING + ANSWER`. Final letter = reviewer's. | +1                 |

When `on`, the reviewer audits the solver's chain (not the question from
scratch), so it can actually check evidence chain (02), competing
interpretations (03), and bias (04). The result row records `draft_pred`,
`pred`, `draft_correct`, `correct`, `review_changed`, plus `draft_reasoning`
and `review_reasoning` so the audit trail is inspectable. `draft_reasoning`
and `review_reasoning` are empty when `--review-mode off`.

## Setup

```
pip install openai
export OPENAI_API_KEY=sk-...
export SKILL_V5_BASE_URL=https://api.openai.com/v1     # or your gateway
export SKILL_V5_MODEL=gpt-4o-mini                      # or claude-* via gateway
```

## Run

Smoke (50 items):
```
python eval/eval_tombench.py --route-mode baseline                            --lang en --limit 50
python eval/eval_tombench.py --route-mode macro_only   --inject-mode light --review-mode on  --lang en --limit 50
python eval/eval_tombench.py --route-mode hierarchical --inject-mode full  --review-mode on  --lang en --limit 50
```

Full run:
```
python eval/eval_tombench.py --route-mode hierarchical --inject-mode light --review-mode on --lang en --workers 8
```

Resume:
```
python eval/eval_tombench.py --route-mode flat_all --inject-mode full --review-mode on --lang en \
    --workers 8 --run-id flat_all_full_review-on_en_gpt-4o-mini_1735000000 --resume
```

Re-summarize:
```
python eval/eval_tombench.py --summarize-only --run-id <run_id>
```

## summary.json fields

- `overall_acc`           — accuracy of `pred` (final, post-review if on).
- `draft_acc`             — accuracy of `draft_pred` (pre-review). Lets one
                            run answer "did review help".
- `review_changed`        — number of items where the reviewer changed the
                            letter.
- `review_flips_correct`  — draft wrong → final right (true wins).
- `review_flips_wrong`    — draft right → final wrong (review regressions).
- `n_routed_to_none`      — items where the router picked nothing.
- `errors`                — items that threw.
- `by_task`, `by_ability` — accuracy split by ToMBench task / ability tag.
- `by_first_pick`         — accuracy when the listed skill was the first pick.
- `by_n_picked`           — accuracy by number of skills picked (0/1/2/3+).
- `pick_frequency`        — how often each skill was selected.

## Diagnostic comparisons

- `baseline` vs `<route>` — total lift from skill content.
- `macro_only` vs `micro_only` — which granularity informs more.
- `hierarchical` vs `flat_all` — does macro-then-micro decomposition beat
  free choice from 76.
- `light` vs `full` injection — does the full SKILL.md help or hurt vs the
  compact slice.
- `draft_acc` vs `overall_acc` in any `--review-mode on` run — net review
  contribution. `review_flips_correct - review_flips_wrong` tells you if
  review is net-positive.
- `summary.by_n_picked` — accuracy by picks count; reveals whether extra
  skills are noise.
- `summary.pick_frequency` — rarely-picked skills are wasted load.

## Notes

- `SKILL.md` and `unit_pack.json` are read once and cached per process.
- Item failures get an `error` field; the runner does not abort.
- `--workers` controls in-flight LLM calls. Tune to your rate limit.
- LLM retries are configurable: `--max-attempts` sets the upper bound
  (default 3), `--retry-backoff-cap` caps exponential backoff between
  retries in seconds (default 8; use 0 to retry immediately).
- Per-stage token budgets are independent:
  - `--router-max-tokens` (default 128) — each router call
  - `--solver-max-tokens` (default 2048) — solver draft. With
    `--review-mode on` the solver also emits a REASONING block, so the
    default leaves headroom; for letter-only solving with `--review-mode off`
    you can drop to ~256.
  - `--reviewer-max-tokens` (default 2048) — L0 reviewer (also emits
    REASONING + ANSWER).
- `--timeout` (default 120s) sets the per-request HTTP timeout.
- `--review-mode on` doubles per-item LLM calls (router + solver + reviewer
  vs router + solver). Plan budget accordingly.
