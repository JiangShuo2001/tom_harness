# Skills v4 — Unified Theory-of-Mind Skill Library + LLM Router

Skills v4 merges two prior efforts into a single coherent library:

- **skills v2** (`papers/skill_v2`) — 12 deep, procedural skills hand-tuned
  on real ToMBench / CogToM error clusters, with a single LLM router.
  Strengths: rich numbered procedures, worked examples, hard guardrails,
  tight quantifier ranges, axis-mapping algorithm, 5-check moral-emotion
  filter, etc.
- **skills v3** (`papers/skills_v3`) — 15 narrower routable skills with a
  table-style markdown router (`ROUTING.md`) and per-skill validation
  packs. Strengths: clean per-skill folder layout
  (`SKILL.md` + `references/examples.md`), explicit boundary tables, near-
  twin disambiguation, route-and-solve evaluation harness.

v4 keeps **v3's structure** (one folder per skill, one router-friendly
`SKILL.md`, a sibling `references/examples.md`, and a top-level
`ROUTING.md`) and **embeds v2's procedural depth** into the matching
skills (as `## Detailed Procedure` and `## Special Case` sections). Six
skills that v3 did not cover (Spatial, Knowledge-Boundary, Other-
Preference, Sensory-Channel, Audience-Calibration, Commitment-Priority)
are added as `skill16`–`skill21`. The moral-emotion 5-check filter from
v2 S11 is promoted to its own skill (`skill22`).

---

## Directory layout

```
skills_v4/
├── README.md                  # this file
├── ROUTING.md                 # router contract: 10 families, 22 skills
├── llm_router.py              # auto-builds the router catalog from SKILL.md
├── skill1  … skill15/         # carried forward from v3 + v2 procedural depth
│   ├── SKILL.md
│   └── references/examples.md
└── skill16 … skill22/         # new from v2-only skills (Spatial, etc.)
    ├── SKILL.md
    └── references/examples.md
```

`llm_router.py` exposes a compact public API (`build_router_prompt`,
`parse_router_choice`, `route`, `get_skill_prompt`) and builds the router
catalog directly from each `SKILL.md` frontmatter description.

---

## The 22 skills

| ID | Family | Topic | Source |
|---|---|---|---|
| `skill1`  | A — Social harm & knowledge | Faux-pas detection (was the remark inappropriate?) | v3 + v2 S1 flattery flag |
| `skill2`  | A | Speaker knowledge / memory tracking | v3 + v2 S3 perception filter |
| `skill3`  | B — Belief tracking | First-order location false belief | v3 + v2 S3 ledger |
| `skill4`  | B | Second-order location false belief | v3 + v2 S3 nested ledger |
| `skill5`  | B | Container content / label false belief | v3 + v2 S3 ledger |
| `skill6`  | C — Social cue interpretation | Observer reaction to ambiguous cue | v3 |
| `skill7`  | C | Sender intention behind nonverbal cue | v3 + v2 S4 surface-vs-strategy |
| `skill8`  | D — Emotion & appraisal | Atypical emotion attribution | v3 + v2 S5 hidden-emotion 2-step decoder |
| `skill9`  | D | Hidden-cause reconstruction (why surprising emotion?) | v3 + v2 S5 expectation-delta |
| `skill10` | E — Quantitative scalar | Scalar prior estimation (before observation) | v3 + v2 S2 TIGHT ranges |
| `skill11` | E | Scalar update (after observation) | v3 + v2 S2 hard SUM constraint |
| `skill12` | C / F | Indirect speech meaning | v3 + v2 S4 surface-vs-strategy |
| `skill13` | F — Influence & strategy | Target-aligned persuasion | v3 + v2 S4 PERSUASION RULE |
| `skill14` | G — Truth & motive | Truth judgment under mixed states | v3 |
| `skill15` | G | Motive for nonliteral / partial / polite speech | v3 + v2 S4 intent-attribution table |
| `skill16` | H — Spatial reasoning | Spatial perspective / dice / picture identification | v2 S6 |
| `skill17` | I — Knowledge boundary | Strip pop-culture analogies fenced off by the story | v2 S7 |
| `skill18` | F | Other-preference action (4-pattern decision tree) | v2 S8 |
| `skill19` | C / H | Sensory-channel filtering (blind / deaf / behind glass) | v2 S9 |
| `skill20` | F | Audience expertise calibration (expert vs novice listener) | v2 S10 |
| `skill21` | F | Commitment-priority arbitration (which action wins?) | v2 S12 |
| `skill22` | D | Belief-driven moral emotion (5-check anti-guilt filter) | v2 S11 |

Family abbreviations follow the extended `ROUTING.md`. A skill can sit in
two families if it is genuinely cross-family (e.g. `skill12` is both a
cue-interpretation and a strategic-meaning skill).

---

## How to use

### 1. As a router + answerer pair (production / evaluation)

```python
from llm_router import build_router_prompt, parse_router_choice, get_skill_prompt
from llm_agents import load_model
from eval_new_benchmarks import build_vanilla_prompt, extract_answer_letter

router_model   = load_model("gpt-5.4-mini")
answerer_model = load_model("glm-5")

router_prompt = build_router_prompt(
    item["story"], item["question"], item["options"], item["labels"],
)
choice = parse_router_choice(router_model.interact(router_prompt, max_tokens=64))
choice = choice or "NONE"

skill = get_skill_prompt(choice)               # None when choice == "NONE"
base  = build_vanilla_prompt(item["story"], item["question"],
                              item["options"], item["labels"])
prompt = (
    "You are answering a Theory-of-Mind multiple-choice question.\n"
    "Apply the following strategy carefully, then answer.\n\n"
    f"=== STRATEGY ===\n{skill}\n=== END STRATEGY ===\n\n"
    f"=== QUESTION ===\n{base}"
) if skill else base

resp = answerer_model.interact(prompt, max_tokens=8192)
pred = extract_answer_letter(resp, item["labels"])
```

For the bundled `experiment_per_model.py`, configure OpenAI-compatible
endpoints with environment variables:

```powershell
$env:GLM_BASE_URL = "https://open.bigmodel.cn/api/coding/paas/v4"
$env:GLM_API_KEY = "<your-api-key>"
$env:EXP_DATASETS = "ToMBench"
$env:EXP_DATASET_FILES = "ToMBench=ToMBench_glm5.jsonl"
$env:EXP_ROUTER = "glm-5"
$env:EXP_ANSWERERS = "glm-5"
$env:EXP_WORKERS = "8"
$env:EXP_ROUTER_GUIDE = "compact"  # none/catalog, compact, or full
$env:EXP_ALLOW_NONE = "true"       # false forces the router to pick the closest skill
# Optional: set a stable output folder name. If omitted, a timestamped
# run_YYYYMMDD_HHMMSS folder is created automatically.
$env:EXP_RUN_ID = "tombench_glm5_run1"
python .\skills_v4\experiment_per_model.py
```

Results are written to a new directory under
`skills_v4/data/results/per_model/`. Each row in the JSON output includes
the router-selected `skill`. `NONE` rows are recorded but not sent to the
answerer, because no skill prompt would be used. Set `EXP_REASONING_EFFORT`
only if your endpoint supports an OpenAI-style `reasoning.effort` request
field.

`EXP_ROUTER_GUIDE` controls how much of `ROUTING.md` is included in the
router prompt:

- `none` / `catalog`: only use the 22 `SKILL.md` frontmatter descriptions.
- `compact`: include the fast workflow, boundary checks, and confused-pair
  cues from `ROUTING.md` while keeping prompts moderate.
- `full`: include the full `ROUTING.md`; strongest context, highest token
  cost.

`EXP_ALLOW_NONE=false` is useful for coverage experiments: the router must
choose the closest skill from `skill1` to `skill22`. With the default
`true`, `NONE` is allowed as a last resort and skipped during answering.

### 2. As a one-call route-and-solve workflow

Use the prompt scaffolding in `ROUTING.md` together with each
`skill*/SKILL.md` distilled into a compact registry. The model returns a
single JSON object with both `predicted_skill` and the chosen option
label. The reference implementation in `papers/skills_v3/skills-validation/run_validation.py`
supports this mode and can be repointed at this directory when that
legacy validation harness is available.

### 3. As a human reading aid

For each skill, read `SKILL.md` (the routable contract) first and then
`references/examples.md` (decision variable, hard boundary, minimal pair,
common failure modes). The `## Detailed Procedure` / `## Special Case`
blocks are the v2-derived deep prompts that were empirically validated
against real error cases.

---

## Design principles

1. **Route on what the question asks, not on story keywords.** The same
   story can mention emotion, belief, dialogue, and deception at once;
   the right skill is the one whose decision variable matches the asked
   output.
2. **One skill at a time, plus `NONE`.** The router commits to a single
   skill or returns `NONE` for a vanilla fall-back. Multi-skill ensembling
   was tried in v2 and hurt accuracy because long combined prompts made
   the answerer drift.
3. **Decision variable first, options second.** Each skill names the one
   variable that determines the answer in `references/examples.md`. The
   workflow is built around computing that variable, not around scanning
   options for keywords.
4. **Special cases beat generic procedures.** When a single high-error
   sub-pattern is identifiable (hidden emotion, moral emotion, "almost
   no" quantifier, target-on-your-right spatial rotation, intention
   attribution with literal motive cue), the skill ships a dedicated
   `## Special Case` block with a worked example.
5. **Explicit boundary exits.** Every skill ends with a `## Boundary
   Exit Rule` listing the nearest neighbouring skills and the cue that
   should hand the case off. This is what lets the router stay below
   ~30% mis-routing on the historically confused pairs.

---

## Provenance

- Empirical refinement source: `papers/skill_v2/data/inspections/` (round-1
  and round-2 failure inspections on `gpt-5.4-mini` and `glm-5`).
- Per-skill validation packs: `papers/skills_v3/skills-validation/`
  (the existing harness can be repointed at this directory).
- The 12-vs-15 mapping rationale is documented in each `SKILL.md`'s
  `## References` section where applicable.
