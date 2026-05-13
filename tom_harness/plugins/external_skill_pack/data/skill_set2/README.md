# Skills v2 — Theory-of-Mind Skill Library + LLM Router

Self-contained drop of the v2.1 skill set (12 skills + LLM router) for ToM
benchmark error reduction on **ToMBench** and **CogToM**, validated with
`gpt-5.4-mini`.

End-to-end LLM-routed result on the union of all target task types
(718 previously-wrong cases):

| Metric | Value |
|---|---|
| End-to-end fix rate | **49–51%** (run-to-run variance ±2pp) |
| LLM router accuracy | **~70%** |
| Cases routed to `NONE` | ~2% |

Comparison vs the static-task-type oracle baseline: **+3–4pp** (oracle ~46%).

---

## Directory layout

```
skill_v2/
├── README.md                   # this file
├── skills.py                   # 12 skill prompts (S1 … S12) + SKILL_TARGETS map
├── llm_router.py               # LLM-based skill router (one prompt → skill_id)
├── validate_oracle.py          # per-skill validation, oracle routing
├── validate_routed.py          # end-to-end LLM-routed validation
├── inspect_failures.py         # round-2 failure inspector (Spatial / DiscrInt / Scalar)
├── inspect_failures_round1.py  # round-1 failure inspector (S5↔S11, MoralEmo, …)
└── data/
    ├── ToMBench.jsonl          # source error cases (gpt-5.4-mini & glm-5 mistakes)
    ├── CogToM.jsonl            # source error cases
    ├── results/
    │   ├── oracle_results.json / ORACLE_RESULTS.md
    │   └── routed_results.json / ROUTED_RESULTS.md
    └── inspections/
        ├── FAILURE_INSPECTION.md          # round-1 root-cause analysis
        ├── failure_inspection_raw.json
        ├── FAILURE_INSPECTION_R2.md       # round-2 root-cause analysis
        ├── failure_inspection_r2.json
        └── uncovered_samples.txt          # raw samples per uncovered task_type
```

External dependency: `../PercepToM/llm_agents.py` and
`../PercepToM/eval_new_benchmarks.py` are reused for model loading and
prompt/answer-letter helpers. Nothing is written back to that folder.

---

## The 12 skills

| ID | Name | Targets |
|---|---|---|
| **S1** | `FauxPas` | Faux-pas Recognition / Flattery |
| **S2** | `Scalar` | Scalar Implicature Test/Task |
| **S3** | `BeliefLedger` | False-Belief, See-Know, 2nd-Order, Knowledge-attention |
| **S4** | `Strategic` | Strange-Story, Hinting, Persuasion, Ambiguous, Pretend, Double-Bluff, **Discrepant intentions** |
| **S5** | `Expectation` | Hidden / Discrepant emotions, Unexpected outcomes |
| **S6** | `Spatial` | Spatial Construction, Picture Identification |
| **S7** | `KnowledgeBound` | Knowledge-pretend, Sarah Task |
| **S8** | `OtherPreference` | Discrepant / Multiple desires, Prediction of actions |
| **S9** | `SensoryChannel` | Affective Perspective-Taking, Synesthetic Fallacy |
| **S10** | `AudienceCalib` | Aware of Reader's Knowledge |
| **S11** | `BeliefEmotion` | Belief-based / Moral emotions |
| **S12** | `CommitmentPrio` | Completion of failed actions |

The full mapping is in `skills.py::SKILL_TARGETS`.

---

## How to run

```bash
cd papers/skill_v2

# Oracle routing (each case sent to its target skill via SKILL_TARGETS)
python validate_oracle.py

# LLM-routed end-to-end (router decides skill from raw case)
python validate_routed.py

# Pull failing-case reasoning for the 4 highest-ROI failure modes
python inspect_failures_round1.py

# Pull failing-case reasoning for Spatial / DiscrIntent / Scalar
python inspect_failures.py
```

Environment knobs (all scripts):

| Env var | Default | Meaning |
|---|---|---|
| `V2_MODEL` | `gpt-5.4-mini` | Answerer model |
| `V2_ROUTER_MODEL` | = `V2_MODEL` | Router model (only used by `validate_routed.py`) |
| `V2_MAX_PER_TT` | `30` | Cap of cases per (dataset, task_type) |
| `V2_WORKERS` | `32` | Thread-pool workers |

Outputs land under `data/results/` and `data/inspections/`.

---

## How the skills were built

1. Started from full ToMBench + CogToM error datasets (cases where
   `gpt-5.4-mini` or `glm-5` was wrong).
2. Aggregated by `(dataset, task_type)` → identified high-error clusters.
3. Sampled 2–3 actual error cases per cluster and read them line-by-line
   (see `data/inspections/uncovered_samples.txt`).
4. Distilled root failure modes into 12 generalisable skill prompts.
5. Validated:
   - **Oracle routing** (`validate_oracle.py`): each error case fed into
     its `SKILL_TARGETS[task_type]` skill — measures the ceiling of
     skill prompt quality alone.
   - **LLM routing** (`validate_routed.py`): router LLM picks the skill
     from raw input — measures the production setting where `task_type`
     is unknown.
6. Two rounds of targeted prompt fixes based on the failure-inspection
   files:
   - **Round 1** (`inspect_failures_round1.py`): S5↔S11 confusion,
     `Hidden emotion` source-event identification, Moral-emotion 5-check
     filter, S8 decision-tree.
   - **Round 2** (`inspect_failures.py`): S6 axis-mapping algorithm,
     S4 intent-attribution literal-cue table, S2 tight quantifier
     ranges + hard sum constraint.

---

## Key design notes

### Skill prompt style
- Each skill is a *small structured procedure* (numbered steps + decision
  rule + guardrails), not a free-form hint.
- Where empirical errors clustered around one "intuitive trap", a
  **`SPECIAL CASE`** block is added with explicit step-by-step decoding
  (e.g. S5 hidden-emotion 2-step decoder, S11 moral-emotion 5-check
  filter, S2 worked example).

### Router design (`llm_router.py`)
- One LLM call returns a single id from `{S1 … S12, NONE}`.
- The catalog string carries 1–3 sentence descriptions tuned to
  distinguish the historically-confused pairs (S3↔S4, S5↔S11).
- `NONE` is a real label: cases that don't clearly fit any skill skip
  the skill prompt entirely (vanilla baseline) — empirically picked
  ~2% of the time.

### Empirically observed limitations
- ~10–15% of remaining errors are **dataset labelling artefacts** in
  ToMBench (e.g. translation mismatches in Scalar Implicature Test where
  the gold doesn't fit any reasonable English reading). Cannot be fixed
  at the prompt level; documented in
  `data/inspections/FAILURE_INSPECTION_R2.md`.
- Persuasion and Faux-pas remain the lowest-fix-rate task types and are
  candidates for future work.
