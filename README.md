# tom_harness

> A lightweight, skill-based agent harness for Theory-of-Mind (ToM) benchmarks.
> Single-shot runtime with 76 hierarchical skills (v5.1) as default; legacy Plan-then-Execute architecture available for multi-step research.

中文版: [README_zh.md](README_zh.md)

---

## What is this?

`tom_harness` is an **agent harness** — the infrastructure that wraps around
a Large Language Model to turn it from a text generator into a reliable
reasoner on a specific task family. Here the task family is **social
cognition / Theory of Mind**: multiple-choice questions about characters'
mental states, false beliefs, hidden emotions, pragmatic inference, etc.

The system supports two execution modes:

1. **Single-shot runtime (default)**: Route → Build prompt (skill + RAG + playbook) → Single LLM call → Optional L0 review → Validator check → Return answer. This is the canonical path for benchmark evaluation.
2. **Legacy harness** (Plan → Execute → Finalize): Planner generates a multi-phase plan, Executor runs each step via a ReAct loop, Finalizer synthesizes the answer. Preserved under `tom_harness/legacy/` for multi-step research.

### Tool Layer

The single-shot runtime provides three pluggable modules:

- **Skills v5.1 (default)** — 76 curated SKILL.md reasoning prompts (20 macro + 56 micro) + 4-stage LLM-based router (`SkillV5Router`)
- **Skills v4 (legacy)** — 22 curated SKILL.md reasoning prompts + LLM-based router (`SkillV4Router`), selectable via `--skill-version v4`
- **RAG v2** — category-aware FAISS retrieval with optional `CategoryClassifier` (1500 condensed documents from ATOMIC, Social Chemistry, NormBank)
- **Memory Playbook** — selector-based strategy injection (ACE-refined playbook via `memory_playbook` package)

The **core is domain-agnostic** (the same skeleton could run legal or math
reasoning); all **ToM-specific knowledge is external** — loaded as
pluggable skills, validators, and failure handlers.

---

## Architecture (Single-Shot Runtime)

```
┌──────────────────────────────────────────────────────────────────────┐
│                     HarnessRuntime (single-shot)                     │
│                                                                      │
│  Stage 1-2: ROUTE                                                    │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ SkillV5Router (default) / SkillV4Router / NoOpRouter           │  │
│  │                                                                │  │
│  │ v5.1: micro-01 (route prep) → pick macros → expand micros     │  │
│  │       route_modes: baseline | macro_only | micro_only          │  │
│  │                    | hierarchical (default) | flat_all          │  │
│  │       inject_modes: full | light (default)                     │  │
│  └────────────────────────────┬───────────────────────────────────┘  │
│                               │                                      │
│  ┌──────────────┐  ┌──────────┴───┐  ┌──────────────┐               │
│  │  RAGv2Engine │  │ Skill bodies │  │   Playbook   │               │
│  │ (FAISS+bge,  │  │ (0-N skills  │  │  (selector-  │               │
│  │  1500 docs)  │  │  injected)   │  │   based)     │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                  │                        │
│  Stage 3: SOLVE                                                      │
│  ┌──────▼─────────────────▼──────────────────▼───────────────────┐   │
│  │              Prompt Assembly                                   │   │
│  │  [Skill body] + [RAG context] + [Playbook] +                 │   │
│  │  [Story] + [Question] + [Options] + [Format instruction]     │   │
│  └──────────────────────────┬────────────────────────────────────┘   │
│                              │                                       │
│  ┌───────────────────────────▼───────────────────────────────────┐   │
│  │                    LLM Call (single-shot)                      │   │
│  │  → Returns: reasoning + {"answer": "A"|"B"|"C"|"D"}          │   │
│  └───────────────────────────┬───────────────────────────────────┘   │
│                              │                                       │
│  Stage 4: L0 REVIEW (optional, --review-mode on)                     │
│  ┌───────────────────────────▼───────────────────────────────────┐   │
│  │  micro-02 (evidence chain) + micro-03 (explanation            │   │
│  │  competition) + micro-04 (anti-bias check)                    │   │
│  │  → chain-of-thought audit → may override draft answer         │   │
│  └───────────────────────────┬───────────────────────────────────┘   │
│                              │                                       │
│  ┌───────────────────────────▼───────────────────────────────────┐   │
│  │              Validators (optional retry)                       │   │
│  │  ScalarProceduralValidator: arithmetic check for               │   │
│  │  Scalar Implicature tasks → suggest/retry if invalid          │   │
│  └───────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Installation

Requires Python ≥ 3.10.

```bash
git clone <repo-url>
cd tom_harness
pip install -r requirements.txt
```

**Additional dependencies for RAG mode:**

```bash
pip install langchain-core langchain-community faiss-cpu sentence-transformers
```

Dependencies are intentionally minimal: core only needs **`pydantic>=2` and `requests`**.

---

## Configuration

The harness talks to an OpenAI-compatible Chat Completions endpoint. Set
environment variables (or create a `.env` from `.env.example`):

```bash
# Test model (the model being evaluated)
export TOM_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"
export TOM_API_KEY="<your key>"
export TOM_MODEL="qwen3.5-27b"
export TOM_TEMPERATURE="0.0"       # optional, default 0.0

# Helper model (for selector/classifier, independent of test model)
export HELPER_API_BASE="..."       # optional, falls back to TOM_API_BASE
export HELPER_API_KEY="..."        # optional, falls back to TOM_API_KEY
export HELPER_MODEL="..."          # optional, falls back to TOM_MODEL
```

---

## Quickstart

### Run ToMBench benchmark (default: v5.1 hierarchical skill routing)

```bash
# All tasks, 20 samples per task (baseline, no modules)
python examples/run_tombench_harness.py --limit 20

# With skill routing (v5.1, 76 skills, hierarchical mode)
python examples/run_tombench_harness.py --skill --limit 20

# With RAG v2 retrieval
python examples/run_tombench_harness.py --rag --limit 20

# With memory playbook (selector-based)
python examples/run_tombench_harness.py --memory --limit 20

# All modules combined
python examples/run_tombench_harness.py --skill --rag --memory --limit 20

# Skill + L0 review (chain-of-thought audit)
python examples/run_tombench_harness.py --skill --review-mode on --limit 20

# Specific route mode (flat_all picks from all 72 candidates)
python examples/run_tombench_harness.py --skill --route-mode flat_all --limit 20

# Use legacy v4 skill routing (22 skills)
python examples/run_tombench_harness.py --skill --skill-version v4 --limit 20

# Specific tasks only
python examples/run_tombench_harness.py --tasks "False Belief Task,Hinting Task Test" --limit 10

# All samples (no limit)
python examples/run_tombench_harness.py --limit 0

# With verbose logging
python examples/run_tombench_harness.py --tasks "False Belief Task" --limit 5 -v
```

### Run ablation experiments

```bash
# Full data (all tasks, all samples)
bash examples/run_ablation.sh

# Quick test (2 samples per task)
bash examples/run_ablation.sh --limit 2

# Specific tasks
bash examples/run_ablation.sh --tasks "False Belief Task,Persuasion Story Task"
```

### Run CogToM benchmark

```bash
python examples/run_cogtom_v2_harness.py --limit 20
python examples/run_cogtom_v2_harness.py --category "Belief" --limit 10
python examples/run_cogtom_v2_harness.py --category "Belief,Emotion,Desire" --limit 5
```

### Run Tactful-ToM benchmark

```bash
python examples/run_tactful_tom_harness.py --limit 20
bash examples/run_tactful_tom_ablation.sh --limit 5
```

### Rerun failed samples / resume interrupted runs

```bash
python examples/rerun_failed.py results/some_run/ --skill
python examples/rerun_failed.py results/some_run/ --skill --rag --resume
```

### Compute detailed statistics

```bash
python examples/compute_detailed_stats.py results/ablation_0507
python examples/compute_detailed_stats.py results/ablation_0507/2_skill
```

Available ToMBench tasks (use exact names with `--tasks`):

```
Ambiguous Story Task          Completion of Failed Actions
Discrepant Desires            Discrepant Emotions
Discrepant Intentions         Emotion Regulation
False Belief Task             Faux-pas Recognition Test
Hidden Emotions               Hinting Task Test
Knowledge-Attention Links     Knowledge-Pretend Play Links
Moral Emotions                Multiple Desires
Percepts-Knowledge Links      Persuasion Story Task
Prediction of Actions         Scalar Implicature Test
Strange Story Task            Unexpected Outcome Test
```

---

## Skill Routing (v5.1)

The default skill system uses **SkillV5Router**: a 4-stage LLM-based router over 76 skills organized into 20 macros and 56 micros under `skills_v5.1/skills/`.

### Route Modes

| Mode | Candidates | Description |
|:-----|:-----------|:------------|
| `baseline` | 0 | No routing, no skill injection |
| `macro_only` | 20 macros | Pick from macro skills only |
| `micro_only` | 52 non-L0 micros | Pick from micro skills only |
| `hierarchical` (default) | 20 → expanded | Step 1: pick macros; Step 2: pick micros from their expandable set |
| `flat_all` | 72 | Pick from all candidates (20 macros + 52 non-L0 micros) |

### Inject Modes

| Mode | Description |
|:-----|:------------|
| `full` | Inject complete SKILL.md content (frontmatter stripped) |
| `light` (default) | Inject structured summary (title, decision variable, workflow, special case) |

### L0 Skills (infrastructure layer)

| Skill | Role |
|:------|:-----|
| `micro-01` | Route prep — always injected as router system prompt |
| `micro-02` | Evidence chain — used in L0 review |
| `micro-03` | Explanation competition — used in L0 review |
| `micro-04` | Anti-bias check — used in L0 review |

### Legacy v4 Routing

22 curated skills under `tom_harness/tools/skills_v4/`, selectable via `--skill-version v4`. Uses `SkillV4Router` with a single LLM call to pick one skill.

---

## RAG Retrieval (`--rag`)

RAG v2 provides category-aware retrieval of social-norm / commonsense knowledge passages.

### Data

1500 condensed documents (clustered & rewritten) from three knowledge sources:
- **ATOMIC** — commonsense causal knowledge
- **Social Chemistry** — social norms
- **NormBank** — behavioral norms

Data: `tom_harness/tools/rag_v2_data/` | Index cache: `tom_harness/tools/rag_v2_index/`

### Usage

```bash
python examples/run_tombench_harness.py --rag --limit 20

# Disable category filter (enabled by default)
python examples/run_tombench_harness.py --rag --no_rag_category_filter --limit 20
```

| Flag | Default | Description |
|:---|:---|:---|
| `--rag` | off | Enable RAG v2 retrieval |
| `--rag_data_dir` | `tom_harness/tools/rag_v2_data` | RAG data directory |
| `--rag_index_dir` | `tom_harness/tools/rag_v2_index` | RAG index directory |
| `--rag_model` | `model/bge-m3` | Embedding model path or HuggingFace name |
| `--rag_category_filter` | on | Enable category-aware filtering |

---

## Memory Playbook (`--memory`)

Selector-based strategy injection using the `memory_playbook` package. A helper LLM classifies the question's subtask and selects relevant strategy bullets from the playbook.

```bash
python examples/run_tombench_harness.py --memory --limit 20
python examples/run_tombench_harness.py --memory --memory_playbook memory_playbook/playbook/final_playbook_pruned.txt
```

| Flag | Default | Description |
|:---|:---|:---|
| `--memory` | off | Enable memory playbook injection |
| `--memory_playbook` | `memory_playbook/playbook/final_playbook_pruned.txt` | Playbook file path |

---

## Output Structure

Each run produces the following under `results/<out_dir>/`:

```
results/<out_dir>/
├── results.jsonl              ← per-sample records
├── stats.json                 ← per-task + overall accuracy statistics
├── stats_detailed.json        ← (optional) 8-task + 6-ability breakdown
├── run.log                    ← detailed framework logs
└── llm_cache/
    └── llm_interactions.jsonl ← raw LLM request/response cache
```

### results.jsonl format

```json
{
  "id": "False Belief Task_0001",
  "task": "False Belief Task",
  "answer": "B",
  "predicted": "B",
  "correct": true,
  "skill_id": "macro-05",
  "skill_ids": ["macro-05", "micro-12"],
  "draft_predicted": "B",
  "review_changed": false,
  "n_llm_calls": 2,
  "elapsed_sec": 5.12,
  "error": null
}
```

### Accuracy calculation

- Records with `predicted=""` (parse failure) or `error != null` are counted as **errors**
- Accuracy = `correct / (total - errors)` — errors are excluded from the denominator

---

## CLI Reference

### `run_tombench_harness.py`

| Flag | Default | Description |
|:---|:---|:---|
| `--data_dir` | `benchmark/ToMBench/` | ToMBench JSONL directory |
| `--tasks` | all tasks | Comma-separated task names to include |
| `--limit` | 20 | Max samples per task (0 = no limit) |
| `--offset` | 0 | Skip first N samples per task |
| `--workers` | 8 | Number of parallel workers |
| `--verbose` / `-v` | off | Show detailed framework logs on console |
| `--out_dir` | `results` | Output directory |
| `--skill` | off | Enable skill injection |
| `--skill-version` | `v5` | Skill version: `v4` (22 skills) or `v5` (76 skills, default) |
| `--route-mode` | `hierarchical` | Route mode: baseline / macro_only / micro_only / hierarchical / flat_all |
| `--inject-mode` | `light` | Inject mode: full / light |
| `--review-mode` | `off` | L0 review: on / off |
| `--lang` | `en` | Language for router prompts: en / zh |
| `--rag` | off | Enable RAG v2 retrieval |
| `--rag_data_dir` | `tom_harness/tools/rag_v2_data` | RAG data directory |
| `--rag_index_dir` | `tom_harness/tools/rag_v2_index` | RAG index directory |
| `--rag_model` | `model/bge-m3` | Embedding model |
| `--rag_category_filter` | on | Category-aware RAG filtering |
| `--memory` | off | Enable memory playbook (selector-based) |
| `--memory_playbook` | `memory_playbook/playbook/...` | Playbook file path |

---

## Project Structure

```
tom_harness/
├── README.md
├── README_zh.md
├── requirements.txt
├── .env.example
│
├── benchmark/                           ← data loaders & datasets
│   ├── load_tombench.py                 ← ToMBench JSONL loader
│   ├── load_cogtom.py                   ← CogToM JSONL loader
│   ├── load_tactful_tom.py              ← Tactful-ToM loader
│   ├── ToMBench/                        ← ToMBench data (20 task .jsonl files)
│   ├── CogToM/                          ← CogToM data
│   ├── tactful-tom/                     ← Tactful-ToM data
│   └── ICTBench/                        ← ICTBench data
│
├── skills_v5.1/                         ← v5.1 skill pack (default)
│   └── skills/
│       ├── macro-01..20/                ← 20 macro skills (each with SKILL.md + unit_pack.json)
│       └── micro-01..56/               ← 56 micro skills (4 L0 + 52 domain)
│
├── memory_playbook/                     ← static playbook files
│   └── playbook/
│       └── final_playbook_pruned.txt    ← ACE-refined strategies
│
├── tom_harness/                         ← core package
│   ├── __init__.py                      ← public API: LLMClient, build_default_runtime
│   ├── llm.py                           ← LLM client + interaction cache + JSON parsing
│   ├── runtime.py                       ← HarnessRuntime (single-shot pipeline)
│   │
│   ├── routing/                         ← skill routers
│   │   ├── __init__.py                  ← re-exports: SkillV5Router, SkillV4Router, NoOpRouter
│   │   ├── base.py                      ← Router ABC + RouteDecision
│   │   ├── skill_v5_router.py           ← 4-stage LLM router (76 skills, v5.1)
│   │   ├── skill_v4_router.py           ← LLM router (22 skills, v4)
│   │   ├── l0_review.py                 ← L0 Review (micro-02/03/04 chain-of-thought audit)
│   │   └── oracle_picks.py              ← static lookup router (for ablation controls)
│   │
│   ├── validators/                      ← procedural validators
│   │   ├── base.py                      ← Validator ABC + ValidationResult
│   │   └── scalar_procedural.py         ← Scalar Implicature arithmetic check
│   │
│   ├── tools/
│   │   ├── base.py                      ← Tool ABC + ToolResult envelope
│   │   ├── memory.py                    ← MemoryStore (vector-indexed task-plan pairs, v1)
│   │   ├── playbook.py                  ← MemoryPlaybook (static strategy loader)
│   │   ├── rag_v2.py                    ← RAGv2Engine (category-aware FAISS retrieval)
│   │   ├── rag_v2_data/                 ← 1500 condensed knowledge documents
│   │   ├── rag_v2_index/                ← FAISS index cache
│   │   └── skills_v4/                   ← 22 v4 SKILL.md skills (legacy)
│   │
│   ├── plugins/                         ← plugin system (legacy hooks)
│   │   └── tom/                         ← ToM-specific plugins
│   │       ├── install.py               ← one-call installer for ToM hooks
│   │       ├── validators.py            ← after_step validators (belief-order, knowledge-gate)
│   │       ├── failure_handlers.py      ← classify failures → inject recovery skills
│   │       └── memory_index.py          ← TaskSignature extraction + memory enrichment
│   │
│   └── legacy/                          ← Plan-then-Execute architecture (preserved)
│       ├── __init__.py
│       ├── schemas.py                   ← Pydantic data models (Plan, Step, Phase, etc.)
│       ├── context.py                   ← ContextManager (3-tier context)
│       ├── registry.py                  ← ToolRegistry (2D dispatch)
│       ├── hooks.py                     ← plugin hook system (7 extension points)
│       ├── planner.py                   ← Planner Agent (question → structured Plan)
│       ├── executor.py                  ← Executor Agent (ReAct loop)
│       └── scheduler.py                ← Scheduler (orchestrator + replan + memory)
│
├── examples/
│   ├── run_tombench_harness.py          ← ToMBench runner (v5.1 default, --skill-version v4 for legacy)
│   ├── run_cogtom_v2_harness.py         ← CogToM benchmark runner
│   ├── run_tactful_tom_harness.py       ← Tactful-ToM benchmark runner
│   ├── run_oracle_skill_experiment.py   ← oracle skill experiment (ablation control)
│   ├── run_ablation.sh                  ← ablation experiment script
│   ├── run_cogtom_ablation.sh           ← CogToM ablation script
│   ├── run_tactful_tom_ablation.sh      ← Tactful-ToM ablation script
│   ├── rerun_failed.py                  ← rerun failed/empty samples (v5.1-compatible)
│   ├── compute_detailed_stats.py        ← stats by 8 task types + 6 ability dimensions
│   └── error_analysis_0507.py           ← error pattern analysis
│
├── docs/                                ← analysis & design documents
└── results/                             ← output (gitignored)
```

---

## Core Components

### HarnessRuntime (`runtime.py`)

The single-shot pipeline: `route → build_prompt → LLM call → L0 review → validators → answer`.

- `answer_one(question, story, options, task_type)` → `RuntimeResult`
- `build_default_runtime(llm, router, ...)` — convenience factory that wires the default validator stack

### LLM Client (`llm.py`)

Thin adapter over any OpenAI-compatible Chat Completions API.

- JSON parsing with robust fallback: direct parse → fenced code block → first balanced `{...}`
- Exponential backoff retry (default 3 attempts)
- Strips `<think>...</think>` inline tags
- Optional JSONL interaction caching for debug/analysis
- Configurable temperature via `TOM_TEMPERATURE` env var

### SkillV5Router (`routing/skill_v5_router.py`)

4-stage LLM-based router. The routing pipeline:

1. **Stage 1 (route prep)**: micro-01 always injected as router system prompt
2. **Stage 2 (route)**: Pick 0+ skills based on `route_mode`
   - `hierarchical`: pick macros → expand to micros → pick micros
   - Falls back to `micro_only` if no macros selected
3. **Skill rendering**: Render picked skills for prompt injection (`inject_mode`: full or light)
4. **Stage 4 (L0 review)**: Optional chain-of-thought audit via micro-02/03/04

### Validators (`validators/`)

- `Validator` ABC with `applies(task_type)` and `validate(...)` → `ValidationResult`
- `ScalarProceduralValidator`: arithmetic check for Scalar Implicature tasks; can suggest an answer or trigger LLM retry with feedback

---

## Legacy Architecture (`legacy/`)

The Plan-then-Execute architecture is preserved under `tom_harness/legacy/` for multi-step research scenarios. It includes:

| Component | File | Purpose |
|:----------|:-----|:--------|
| Schemas | `schemas.py` | Pydantic models: Plan, Step, Phase, ExecutionTrace, Memory, etc. |
| Context Manager | `context.py` | 3-tier context governance for LLM prompts |
| Tool Registry | `registry.py` | 2D dispatch by (tool_type, tool_name) |
| Hook System | `hooks.py` | 7 extension points for plugins |
| Planner | `planner.py` | Question → structured multi-phase Plan |
| Executor | `executor.py` | ReAct loop per step |
| Scheduler | `scheduler.py` | Orchestrator with replan + memory persistence |

---

## Plugin System (`plugins/tom/`)

ToM-specific hooks registered via `install.py`:

| Hook | File | Purpose |
|:-----|:-----|:--------|
| `on_step_failure` | `failure_handlers.py` | Classify failures (10+ types) → inject recovery skills on replan |
| `enrich_memory` | `memory_index.py` | Extract TaskSignature → enrich memory metadata |
| `after_step` | `validators.py` | Belief-order and knowledge-gate consistency checks (warn, not fail) |

**TaskSignature** (from `memory_index.py`): Pure-function, <1ms, no LLM — extracts `task_type`, `question_kind`, `character_count`, `belief_order`, bilingual feature flags via regex.

---

## Design Principles

1. **Core is domain-agnostic.** Nothing in `tom_harness/` (outside `plugins/tom/`) mentions belief, emotion, faux-pas, etc.
2. **External knowledge drives reasoning.** All ToM logic lives in skill files, not code.
3. **Single-shot by default.** Plan-then-Execute is preserved but no longer the default path.
4. **Skill version switchable.** `--skill-version {v4,v5}` allows explicit version selection.
5. **No heavy frameworks in core.** No LangChain/AutoGen dependency (only in RAG backend).
6. **Bilingual.** Feature extractors, skill content, and router prompts support English + Chinese.
7. **Thread-safe.** Runners support parallel execution via ThreadPoolExecutor.
8. **Crash-resumable.** `rerun_failed.py` can resume interrupted runs and fill in missing samples.

---

## All Example Scripts

| Script | Description |
|:-------|:------------|
| `run_tombench_harness.py` | ToMBench single-shot runner (v5.1 default, v4 via `--skill-version`) |
| `run_cogtom_v2_harness.py` | CogToM benchmark runner |
| `run_tactful_tom_harness.py` | Tactful-ToM benchmark runner |
| `run_oracle_skill_experiment.py` | Oracle skill experiment (ablation control) |
| `run_ablation.sh` | ToMBench ablation experiment (module combinations) |
| `run_cogtom_ablation.sh` | CogToM ablation experiment |
| `run_tactful_tom_ablation.sh` | Tactful-ToM ablation experiment |
| `rerun_failed.py` | Rerun failed/empty samples, resume interrupted runs (v5.1) |
| `compute_detailed_stats.py` | Compute stats by 8 task types + 6 ability dimensions |
| `error_analysis_0507.py` | Error pattern analysis |

---

## License

Research code — see `LICENSE` (to be added).

---

## References

- [XSkill](https://arxiv.org/abs/2603.12056) — dual-stream continual learning.
- [Externalization in LLM Agents](https://arxiv.org/abs/2604.08224) — harness engineering framework.
- [Natural-Language Agent Harnesses](https://arxiv.org/abs/2603.25723) — harness as natural-language artifact.
