# tom_harness

> A lightweight, skill-based agent harness for Theory-of-Mind (ToM) benchmarks.
> Plan-then-Execute architecture with ReAct inner loop; generic core + pluggable ToM specialization.

中文版: [README_zh.md](README_zh.md)

---

## What is this?

`tom_harness` is an **agent harness** — the infrastructure that wraps around
a Large Language Model to turn it from a text generator into a reliable
reasoner on a specific task family. Here the task family is **social
cognition / Theory of Mind**: multiple-choice questions about characters'
mental states, false beliefs, hidden emotions, pragmatic inference, etc.

The system supports two execution modes:

1. **Full harness** (Plan → Execute → Finalize): Planner generates a multi-phase
   plan, Executor runs each step via a ReAct loop, Finalizer synthesizes the answer.
2. **Thin harness** (Skill-prepended single LLM call): A selective router picks
   the best skill prompt, prepends it to the question, and calls the LLM once.

### Tool Layer

The full harness provides externalized cognition through three pluggable modules:

- **Skills** — curated reasoning prompts (27 external skills + 16 built-in skills across multiple packs)
- **Memory Playbook** — ACE-refined strategies injected into the Planner
- **RAG** — commonsense knowledge retrieval (ATOMIC, Social Chemistry, NormBank)

The architecture follows the spec handed down by the project lead. The
**core is domain-agnostic** (the same skeleton could run legal or math
reasoning); all **ToM-specific knowledge is external** — loaded as
pluggable skills, validators, and failure handlers.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Harness Layer                           │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │    Scheduler    │ │  Tool Registry  │ │ Context Manager │   │
│  │ (orchestrator)  │ │  (dispatch)     │ │ (3-tier context)│   │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘   │
│           │                   │                   │             │
│  ┌────────▼────────────────────▼───────────────────▼────────┐  │
│  │                     Planner Agent                         │  │
│  │ 1. (mandatory) query Memory Store for warm-start         │  │
│  │ 2. inject Memory Playbook / Skill / RAG (if enabled)     │  │
│  │ 3. generate structured JSON plan (phases → steps)        │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │                  Executor Agent                           │  │
│  │   ReAct loop per step: Reason → Act → Observe             │  │
│  │   Phase-aware accumulated results → Finalizer             │  │
│  │   Supports sub-steps (recursive execution)                │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │                     Tool Layer                            │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │  │
│  │  │ Memory Store │ │  Skill Lib   │ │  RAG Engine  │      │  │
│  │  │ (vector idx) │ │ (declarative │ │ (FAISS+bge)  │      │  │
│  │  │              │ │  +procedural)│ │              │      │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘      │  │
│  │  ┌──────────────────────────────────────────────────┐     │  │
│  │  │ Built-in Skills: 16 ToM-specific skills          │     │  │
│  │  │ External Packs: Set1 (15) + Set2 (12) skills     │     │  │
│  │  │ Routers: LLM-based / Selective (regex-based)     │     │  │
│  │  └──────────────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Plugin System (Hooks)                  │  │
│  │  • ToM validators (belief-order, knowledge-gate checks)  │  │
│  │  • Failure handlers (classify → inject recovery skills)  │  │
│  │  • Memory enrichment (TaskSignature fingerprinting)     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
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
three environment variables (or create a `.env` from `.env.example`):

```bash
export TOM_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"
export TOM_API_KEY="<your key>"
export TOM_MODEL="qwen3.5-27b"
```

---

## Quickstart

### Single-question demo (Sally-Anne)

```bash
python examples/run_demo.py
```

### Run ToMBench benchmark (full harness)

```bash
# All tasks, 20 samples per task
python examples/run_tombench_harness.py --limit 20

# Specific tasks only
python examples/run_tombench_harness.py --tasks "False Belief Task,Hinting Task Test" --limit 10

# All samples (no limit)
python examples/run_tombench_harness.py --limit 0

# With verbose logging
python examples/run_tombench_harness.py --tasks "False Belief Task" --limit 5 -v
```

### Run ToMBench benchmark (thin harness — selective skill routing)

```bash
# Uses regex-based selective router + single LLM call per question
python examples/run_selective_harness.py --limit 20

# Specific tasks
python examples/run_selective_harness.py --tasks "Scalar Implicature Test" --limit 0
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

### Run CogToM benchmark

```bash
# All categories, 20 samples per category
python examples/run_cogtom_harness.py --limit 20

# Specific category
python examples/run_cogtom_harness.py --category "Belief" --limit 10

# Multiple categories
python examples/run_cogtom_harness.py --category "Belief,Emotion,Desire" --limit 5
```

Available CogToM categories (use exact names with `--category`):

```
Belief    Comprehensive    Desire    Emotion
Intention Knowledge        Non-literal Percept
```

---

## Memory Playbook (`--memory`)

The Memory Playbook injects pre-built ACE-framework strategies into the Planner prompt. These are curated through multi-round iterative refinement and contain:

- **Strategies & Insights** — proven reasoning patterns for ToM tasks
- **Common Mistakes to Avoid** — error patterns to guard against
- **Problem-Solving Heuristics** — general decision rules

### Setup

Place playbook files (`.txt` or `.md`) in the `memory_playbook/` directory:

```
memory_playbook/
└── epoch_1_step_600_playbook.txt    ← ACE-refined strategies
```

### Usage

```bash
# ToMBench with memory playbook
python examples/run_tombench_harness.py --memory --limit 20

# CogToM with memory playbook
python examples/run_cogtom_harness.py --memory --category "Belief" --limit 10

# Custom playbook directory
python examples/run_tombench_harness.py --memory --memory_dir /path/to/my_playbook/
```

The playbook content is injected **only into the Planner** prompt (not the Executor's ReAct loop). The Planner system prompt instructs the LLM to actively reference playbook strategies and avoid documented common mistakes.

| Flag | Default | Description |
|:---|:---|:---|
| `--memory` | off | Enable memory playbook injection into planner |
| `--memory_dir` | `memory_playbook/` | Path to playbook directory |

---

## RAG Retrieval (`--rag`)

RAG provides dynamic retrieval of social-norm / commonsense knowledge passages during execution.

### Build the FAISS index (one-time setup)

The RAG engine uses bge-m3 embeddings over three knowledge sources (577k total entries):
- **ATOMIC** — commonsense causal knowledge (81k)
- **Social Chemistry** — social norms (340k)
- **NormBank** — behavioral norms (155k)

```bash
# Full index build (~30-60 min on CPU)
python -c "from tom_harness.tools import RAGEngine; r = RAGEngine(); r.build_index()"

# Quick test with small sample (100 per source, ~few minutes)
python -c "from tom_harness.tools import RAGEngine; r = RAGEngine(); r.build_index(num_samples=100); print(f'Done: {r.size()} docs')"
```

The index is cached to `tom_harness/tools/tomrag/index/` — subsequent runs load from disk in seconds.

### Usage

```bash
python examples/run_tombench_harness.py --rag --limit 20
python examples/run_cogtom_harness.py --rag --category "Belief" --limit 10
```

| Flag | Default | Description |
|:---|:---|:---|
| `--rag` | off | Enable RAG retrieval |
| `--rag_data_dir` | `tom_harness/tools/tomrag/data` | JSONL knowledge corpus directory |
| `--rag_index_dir` | `tom_harness/tools/tomrag/index` | FAISS index cache directory |
| `--rag_model` | `model/bge-m3` | Embedding model path or HuggingFace name |

### Combining Memory Playbook + RAG

Both can be enabled simultaneously:

```bash
python examples/run_tombench_harness.py --memory --rag --limit 20 --tag memory_rag
```

---

## LLM Interaction Cache

Every LLM call (system prompt, user prompt, response, timing) is logged to a JSONL file for debugging and analysis. The cache is **reset at the start of each task**.

Cache location: `results/<tag>/llm_cache/llm_interactions.jsonl`

Each line contains:
```json
{
  "seq": 1,
  "timestamp": "2026-04-24T09:35:28+0800",
  "model": "qwen3-32b",
  "duration_ms": 9867,
  "system": "You are the Planner...",
  "user": "## Context\n...",
  "response": "{\"task_type\": \"false_belief\", ...}"
}
```

---

## Output Structure

Each run produces the following under `results/<tag>/`:

```
results/<tag>/
├── results.jsonl              ← per-sample records (id, predicted, correct, timing, etc.)
├── stats.json                 ← per-task/category + overall accuracy statistics
├── run.log                    ← detailed framework logs (per-task, non-interleaved)
└── llm_cache/
    └── llm_interactions.jsonl ← raw LLM request/response cache
```

All output files are **overwritten** on each run (no resume mechanism).

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
| `--out_dir` | `results` | Root output directory |
| `--tag` | `notools` | Run tag (results saved to `<out_dir>/<tag>/`) |
| `--memory` | off | Enable memory playbook |
| `--memory_dir` | `memory_playbook/` | Playbook directory path |
| `--rag` | off | Enable RAG retrieval |
| `--rag_data_dir` | `tom_harness/tools/tomrag/data` | RAG data directory |
| `--rag_index_dir` | `tom_harness/tools/tomrag/index` | RAG index directory |
| `--rag_model` | `model/bge-m3` | Embedding model |

### `run_cogtom_harness.py`

Same flags as above, with these differences:

| Flag | Default | Description |
|:---|:---|:---|
| `--data_dir` | `benchmark/cogtom/` | CogToM data directory |
| `--category` | all categories | Comma-separated category names (replaces `--tasks`) |
| `--limit` | 20 | Max samples per category |
| `--offset` | 0 | Skip first N samples per category |
| `--tag` | `cogtom` | Default run tag |

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
│   ├── ToMBench/                        ← ToMBench data (20 task .jsonl files)
│   └── cogtom/                          ← CogToM data
│       ├── CogToM-en.jsonl              ← English (8513 samples)
│       └── CogToM-zh.jsonl              ← Chinese
│
├── memory_playbook/                     ← static playbook files
│   └── epoch_1_step_600_playbook.txt    ← ACE-refined strategies
│
├── tom_harness/                         ← core package
│   ├── schemas.py                       ← Pydantic data models (Plan, Step, Phase, ExecutionTrace, etc.)
│   ├── llm.py                           ← LLM client + interaction cache + JSON parsing
│   ├── context.py                       ← ContextManager (3-tier context + playbook injection)
│   ├── registry.py                      ← ToolRegistry (2D dispatch by tool_type + tool_name)
│   ├── hooks.py                         ← plugin hook system (7 extension points)
│   ├── planner.py                       ← Planner Agent (question → structured Plan)
│   ├── executor.py                      ← Executor Agent (ReAct loop + finalization)
│   ├── scheduler.py                     ← Scheduler (orchestrator + replan + memory persistence)
│   ├── skill_router.py                  ← LLM-based skill router (12 hardcoded skills)
│   │
│   ├── tools/
│   │   ├── base.py                      ← Tool ABC + ToolResult envelope
│   │   ├── memory.py                    ← MemoryStore (vector-indexed task-plan pairs)
│   │   ├── playbook.py                  ← MemoryPlaybook (static strategy loader)
│   │   ├── skills.py                    ← SkillLib (declarative + procedural skills)
│   │   ├── rag.py                       ← RAGEngine (FAISS adapter)
│   │   └── tomrag/                      ← ToMRAG sub-package
│   │       ├── rag.py                   ← LangChain + FAISS + bge-m3 embeddings
│   │       ├── data/                    ← knowledge corpus (577k entries)
│   │       └── index/                   ← FAISS vector index (built at runtime)
│   │
│   ├── plugins/
│   │   ├── tom/                         ← ToM-specific plugins
│   │   │   ├── install.py               ← one-call installer for ToM hooks + skills
│   │   │   ├── router.py                ← signature-based skill gating
│   │   │   ├── validators.py            ← after_step validators (belief-order, knowledge-gate)
│   │   │   ├── failure_handlers.py      ← classify failures → inject recovery skills
│   │   │   ├── memory_index.py          ← TaskSignature extraction + memory enrichment
│   │   │   ├── story_model.py           ← externalized ToM state (Event, Declaration, queries)
│   │   │   ├── plan_templates/          ← 3 plan-template skills
│   │   │   └── skills/                  ← 13 reasoning skills + procedural handlers
│   │   │       ├── handlers.py          ← Python implementations (quantifier, story_model, etc.)
│   │   │       └── *.md                 ← SKILL.md files
│   │   │
│   │   └── external_skill_pack/         ← contributed skill packs
│   │       ├── adapter.py               ← SkillPackAdapter ABC
│   │       ├── set1_adapter.py          ← Set1 adapter (15 SKILL.md skills)
│   │       ├── set2_adapter.py          ← Set2 adapter (12 prompt-string skills)
│   │       ├── selective_router.py      ← meta-router (regex-based, no LLM call)
│   │       └── data/
│   │           ├── skill_set1/          ← 15 skills (faux-pas, belief, emotion, etc.)
│   │           │   ├── ROUTING.md       ← routing rules documentation
│   │           │   └── skill1..15/      ← each with SKILL.md
│   │           └── skill_set2/          ← 12 skills
│   │               ├── skills.py        ← SKILL_S1..S12 prompt strings
│   │               └── llm_router.py    ← LLM-based router for Set2
│
├── examples/
│   ├── run_demo.py                      ← single-question demo (Sally-Anne)
│   ├── run_tombench_harness.py          ← ToMBench full harness runner
│   ├── run_selective_harness.py         ← thin harness (selective routing)
│   ├── run_cogtom_harness.py            ← CogToM benchmark runner
│   ├── run_tombench_with_skills.py      ← ToMBench with LLM skill router
│   ├── run_skills_direct.py             ← direct skill invocation (no harness)
│   ├── run_compare_skill_packs.py       ← skill pack comparison runner
│   ├── run_self_consistency.py          ← self-consistency voting runner
│   ├── run_skill_matrix.py              ← skill × task matrix evaluation
│   ├── run_task_classifier_inferred.py  ← task-type classifier evaluation
│   ├── run_tombench_v03.py              ← v0.3 baseline runner
│   └── run_ablation.sh                  ← ablation experiment script
│
├── docs/                                ← analysis documents
│   ├── 0428效果分析.md                  ← ablation findings (CN)
│   └── ...
│
└── results/                             ← output (gitignored)
```

---

## Core Components In Depth

### Data Schemas (`schemas.py`)

All core data structures are Pydantic v2 models. Domain-specific fields live in `metadata: dict` — the core never reads metadata; only plugins do.

| Class | Purpose |
|:------|:--------|
| `ToolType` | Enum: MEMORY, SKILL, RAG, NONE |
| `ToolCall` | Standardized tool invocation: `tool_type`, `tool_name`, `tool_params`, `output_mapping` |
| `Step` | Single execution step: `step_id`, `step_order`, `description`, `depends_on`, `tool`, `sub_steps` |
| `Phase` | Macro stage: `phase_id`, `phase_name`, `steps[]` |
| `Plan` | Planner output: `task_id`, `task_type`, `phases[]`, `memory_references[]`, `expected_final_output` |
| `ExecutionTrace` | Audit record: `reasoning`, `tool_call`, `observation`, `step_result` |
| `Memory` | Stored (task, plan) pair: `task`, `plan`, `execution_summary`, `success`, `score` |
| `ExecutionContext` | Per-step context: `plan`, `current_phase_id`, `current_step`, `global_context` |
| `FinalResult` | Harness output: `task_id`, `answer`, `success`, `plan`, `traces[]`, `elapsed_sec` |

### LLM Client (`llm.py`)

Thin adapter over any OpenAI-compatible Chat Completions API.

- **`chat(system, user, temperature, max_tokens, enable_thinking)`** → raw string
- **`chat_json(system, user, **kwargs)`** → parsed dict
- JSON parsing with robust fallback: direct parse → fenced code block → first balanced `{...}` object
- Exponential backoff retry (default 3 attempts)
- Strips `<think>...</think>` inline tags
- Optional JSONL interaction caching for debug/analysis
- Supports vLLM-style and DashScope-style thinking mode

### Context Manager (`context.py`)

Three-tier context governance for LLM prompts:

| Tier | Content | Lifecycle |
|:-----|:--------|:----------|
| **Tier 1 (fixed)** | Agent identity, tool schemas, safety policy | Set once at startup |
| **Tier 1.5 (semi-static)** | Memory Playbook, Skill instructions, RAG passages | Per-task |
| **Tier 2 (dynamic)** | Task state, retrieved memories, accumulated results | Per-task, updated per step |
| **Tier 3 (transient)** | Single-step reasoning scratchpad | Cleared after each step |

Key methods:
- `install_fixed(system_identity, tool_schema_summary, safety_policy)` — once at setup
- `install_playbook(content)` / `install_skill(content)` / `install_rag_context(content)` — per task
- `begin_task(question, options)` → `GlobalContext`
- `record_step_result(phase_name, variable_name, value)` — accumulate step outputs
- `render_fixed_preamble()` → Tier 1 string
- `render_dynamic_state(include_accumulated)` → Tiers 1.5 + 2 + 3 string

### Tool Registry (`registry.py`)

Two-dimensional registry keyed by `(tool_type, tool_name)`:

- `register(tool, permissions)` — add a tool with optional permission requirements
- `dispatch(ToolCall, caller_scope)` → `ToolResult` — resolve, validate params, invoke, wrap result
- Permission check: `required ⊆ caller_scope`
- `schema_summary()` → compact schema string for Planner context

### Hook System (`hooks.py`)

Plugin hook registry with 7 extension points:

| Hook | Signature | Returns |
|:-----|:----------|:--------|
| `before_plan` | `(question, task_type)` | Optional preamble text |
| `after_plan` | `(plan)` | Optional amended plan |
| `before_step` | `(step, context)` | Side effects only |
| `after_step` | `(step, trace, context)` | Side effects only |
| `on_step_failure` | `(step, trace, context)` | `RecoveryDirective` or None |
| `before_finalize` | `(accumulated_results)` | Side effects only |
| `enrich_memory` | `(memory)` | Annotated `Memory` |

`RecoveryDirective` actions: `retry`, `replan`, `skip`, `abort`. Can inject skills on replan.

### Planner Agent (`planner.py`)

Transforms question → structured multi-phase `Plan` in one LLM call:

1. Fire `before_plan` hooks (plugins inject preamble)
2. Query Memory Store (top_k=3, mandatory warm-start even if empty)
3. Format memory block, playbook block, skill block, RAG block
4. Single LLM call: `llm.chat_json(PLANNER_SYSTEM, user_template)`
5. Parse JSON → validate tool names against registry (unknown tools → None)
6. Fire `after_plan` hooks (plugins may amend)
7. Return typed `Plan`

On JSON parse failure, allows one repair pass before raising.

### Executor Agent (`executor.py`)

ReAct loop for each step: **Reason → Act → Observe → Record**.

- **Reason**: LLM call with full plan overview + dynamic state + current step description
- **Act**: If step has a tool, dispatch via registry; otherwise reasoning becomes output
- **Observe**: Store tool result in accumulated_results under `output_mapping.store_to`
- **Sub-steps**: Recursive execution up to `max_substep_depth`

**Finalization** (`finalize_answer`):
1. Scan accumulated results for skill-emitted "recommendation" or "answer_letter" votes
2. If unanimous or strict-majority → short-circuit return (skip LLM call)
3. Otherwise → LLM finalize call with truncated accumulated results → answer letter

### Scheduler / Orchestrator (`scheduler.py`)

Top-level lifecycle manager. Domain-agnostic — all ToM logic lives in plugins.

**`run(task_id, question, options, dataset)`** → `FinalResult`:

1. `context.begin_task(question, options)`
2. (Optional) Skill router → inject skill context
3. (Optional) RAG retrieval → inject passages
4. **Plan**: `planner.plan(...)` with exception guard
5. **Execute**: Phase-by-phase, step-by-step
   - Enforce `depends_on` (warn if unsatisfied)
   - On step failure: fire `on_step_failure` hook → `RecoveryDirective`
     - `replan` (max 2 replans): inject failure info, re-plan, restart
     - `skip`: continue to next step
     - `abort`: return failure immediately
6. **Finalize**: `executor.finalize_answer(...)` → answer letter
7. **Persist memory**: If success → create Memory → fire `enrich_memory` hook → `memory.insert()`
8. Return `FinalResult`

---

## Execution Flow

```
Scheduler.run(task_id, question, options)
│
├─ context.begin_task(question, options)
├─ [Optional] skill_router.route() → inject skill context
├─ [Optional] rag_engine.run() → inject RAG passages
│
├─ PLANNING ─────────────────────────────────────────────
│  planner.plan(task_id, question, options)
│  ├─ fire("before_plan")              ← plugin hooks
│  ├─ memory.run(query, top_k=3)      ← mandatory warm-start
│  ├─ llm.chat_json(PLANNER_SYSTEM, user_template)
│  ├─ _assemble_plan() → validate tool names → Plan
│  └─ fire("after_plan", plan)         ← plugin hooks
│
├─ EXECUTION ────────────────────────────────────────────
│  for phase in plan.phases:
│    for step in phase.steps:
│      executor.execute_step(ctx, execution_order)
│      ├─ fire("before_step")
│      ├─ _reason_about(ctx)           ← LLM: thought + state_analysis
│      ├─ if step.tool:
│      │    registry.dispatch(tool_call) → ToolResult
│      │    context.record_step_result(phase, key, value)
│      ├─ recurse into sub_steps (if any)
│      ├─ fire("after_step")
│      └─ context.clear_transient()
│
│      if step failed:
│        fire("on_step_failure") → RecoveryDirective
│        ├─ "replan" → re-plan with failure context (max 2×)
│        ├─ "skip"   → continue
│        └─ "abort"  → return failure
│
├─ FINALIZE ─────────────────────────────────────────────
│  executor.finalize_answer(question, options, accumulated)
│  ├─ scan for skill votes (unanimous/majority → short-circuit)
│  └─ else: LLM call → answer letter
│
├─ PERSIST MEMORY ───────────────────────────────────────
│  if success:
│    Memory(task, plan, summary) → fire("enrich_memory") → memory.insert()
│
└─ return FinalResult(task_id, answer, success, plan, traces, elapsed_sec)
```

---

## Tool Layer

### Memory Store (`tools/memory.py`)

Vector-indexed store of `(task, plan)` pairs for warm-start retrieval.

- Default embedder: character-trigram hashing (256-dim, zero-dependency)
- Cosine similarity retrieval with `top_k` and `similarity_threshold`
- Metadata filtering (plugins post-filter by any metadata key)
- Optional JSONL persistence (crash-resumable)
- Thread-safe (RLock)

### Skill Library (`tools/skills.py`)

Directory-based skill index supporting two modes:

| Mode | Definition | Execution |
|:-----|:-----------|:----------|
| **Declarative** | SKILL.md with frontmatter + workflow | LLM call against skill text |
| **Procedural** | SKILL.md + Python handler | Direct Python function call |

SKILL.md frontmatter: `skill_id`, `name`, `description`, `triggers[]`; rest → `metadata`.

### RAG Engine (`tools/rag.py` + `tools/tomrag/rag.py`)

FAISS-backed retrieval over social-norm knowledge bases:

| Source | Entries | Content |
|:-------|:--------|:--------|
| `atomic.jsonl` | 81k | Commonsense causal knowledge |
| `social_chem.jsonl` | 340k | Social norms |
| `normbank.jsonl` | 155k | Behavioral norms |

Backend: LangChain + FAISS + HuggingFace bge-m3 embeddings (normalize=True, batch_size=32).

---

## Plugin System

### ToM Plugin (`plugins/tom/`)

One-call installer (`install()`) that registers:

| Component | File | Purpose |
|:----------|:-----|:--------|
| **Validators** | `validators.py` | after_step checks: belief-order, knowledge-gate (warn, not fail) |
| **Failure Handlers** | `failure_handlers.py` | Classify failures → inject recovery skills on replan |
| **Memory Index** | `memory_index.py` | Extract `TaskSignature` → enrich memory metadata |
| **Story Model** | `story_model.py` | Externalized ToM state: parse story ONCE → deterministic queries |
| **Router** | `router.py` | Signature-based skill gating (avoid over-invoking) |
| **Procedural Handlers** | `skills/handlers.py` | Python implementations for 8+ skills |

**TaskSignature** (from `memory_index.py`): Pure-function, <1ms, no LLM — extracts `task_type`, `question_kind`, `character_count`, `belief_order`, bilingual feature flags via regex.

**StoryModel** (from `story_model.py`): LLM parses story → Pydantic-validated `Events[]` + `Declarations[]` → deterministic Python queries (`latest_known_location`, `character_knows`, etc.) — zero hallucination after parse.

**Procedural Handlers** (from `skills/handlers.py`):

| Handler | Strategy |
|:--------|:---------|
| `S02_quantifier_solve` | Map quantifiers to fraction ranges → solve linear constraints |
| `S_build_story_model` | LLM parse → StoryModel Pydantic validation |
| `S_belief_query` | Pure Python over StoryModel (zero LLM) |
| `S_knowledge_query` | Pure Python over StoryModel (zero LLM) |
| `S_evidence_scorer` | LLM scores each option per sentence (-1 to +2) |
| `S_minimal_intervention` | Two-phase: extract objections → 4-dimension scoring |
| `S05_emotion_moderation` | Bilingual emotion lexicon scan → fallthrough to evidence_scorer |
| `S07_causal_chain` | Extract tail clauses + contrasts → mechanism overlap scoring |

### External Skill Packs (`plugins/external_skill_pack/`)

Pluggable adapters consuming external skill sets via `SkillPackAdapter` ABC:

| Pack | Skills | Format | Routing |
|:-----|:-------|:-------|:--------|
| **Set1** | 15 skills (cs1_skill1..15) | SKILL.md files | Static regex rules from ROUTING.md |
| **Set2** | 12 skills (cs2_S1..S12) | Python string constants | LLM-based or signature-based |

**SelectiveRouter** (`selective_router.py`): Meta-adapter with frozen v0.4 rules:
1. `has_quantifier + "how many"` → cs1_skill10/11 (scalar)
2. `has_belief_switch + belief query` → cs1_skill3 (false belief)
3. `"should X but / surprising"` → cs2_S5 (unexpected outcome)
4. Fallthrough → no skill (raw)

---

## Skill Routing: Three Modes

| Router | Skills | Mechanism | LLM Calls | Used By |
|:-------|:-------|:----------|:----------|:--------|
| **LLM Router** (`skill_router.py`) | 12 hardcoded (S1–S12) | LLM picks best skill per question | 1 extra per question | `run_tombench_with_skills.py` |
| **Selective Router** (`selective_router.py`) | 27 external (Set1+Set2) | Regex pattern matching | 0 | `run_selective_harness.py` |
| **ToM Router** (`plugins/tom/router.py`) | 16 built-in | TaskSignature → skill gating | 0 | Full harness (internal) |

---

## How the Framework Works: Loading Mechanisms

### Skill System

**LLM-based Router** (12 skills):
1. `SkillRouter(llm)` initialized at startup
2. Per question: `router.route(question, options)` → LLM call → skill_id or `"NONE"`
3. `router.get_skill_prompt(skill_id)` → full prompt text
4. Injected into Planner context as "Strategy Guide"

**Selective Router** (27 external skills):
1. `SelectiveRouter()` initialized → loads Set1 + Set2 adapters
2. `router.load_into(skill_lib)` loads all 27 skills
3. Per question: `router.route(question, story, options, task_type)` → regex rules
4. Returns `RoutingResult(skill_id, confidence, rationale)` or `skill_id=None`
5. Skill body prepended to prompt in thin harness mode

### Memory Playbook: Static Strategy Injection

1. `MemoryPlaybook(playbook_dir="memory_playbook/")` loads all `.txt`/`.md` files
2. Concatenated into single string
3. `ctx.install_playbook(content)` stores in ContextManager
4. Injected **only into Planner** system prompt as "Memory Playbook" section

### RAG: Dynamic Knowledge Retrieval

1. `RAGEngine(data_dir, index_dir, model_name)` wraps `ToMRAG` backend
2. `build_index()`: if cached → load from disk (seconds); if not → embed all docs, build FAISS, save (~30-60 min CPU)
3. `registry.register(rag)` makes RAG available as tool
4. Per question: `rag.run(query, top_k=5)` → retrieved passages
5. Formatted and injected into context as "Retrieved Knowledge"

### Execution Modes: Full vs Thin Harness

| Mode | Planner | Executor | Skill Routing | Use Case |
|:-----|:--------|:---------|:--------------|:---------|
| **Full harness** | Multi-phase plan | ReAct loop per step | LLM-based / ToM Router | Complex reasoning requiring decomposition |
| **Thin harness** | None | None | Selective (regex) | Simple prompt prepending, minimal overhead |

---

## All Example Scripts

| Script | Description |
|:-------|:------------|
| `run_demo.py` | Single Sally-Anne question through full harness |
| `run_tombench_harness.py` | ToMBench full harness benchmark (parallel, configurable) |
| `run_cogtom_harness.py` | CogToM benchmark runner (8 categories) |
| `run_selective_harness.py` | Thin harness with selective routing (regex-based) |
| `run_tombench_with_skills.py` | ToMBench with LLM skill router enabled |
| `run_skills_direct.py` | Direct skill invocation without harness (testing) |
| `run_compare_skill_packs.py` | Compare Set1 vs Set2 skill packs |
| `run_self_consistency.py` | Self-consistency voting (multiple runs → majority) |
| `run_skill_matrix.py` | Skill × task matrix evaluation |
| `run_task_classifier_inferred.py` | Task-type classifier accuracy evaluation |
| `run_tombench_v03.py` | v0.3 baseline runner |
| `run_ablation.sh` | Shell script for ablation experiments |

---

## Ablation Findings (Scalar Implicature Test, n=200)

| Variant | Accuracy |
|:--------|:---------|
| Baseline (framework only) | 58.5% |
| + Skill | **62.5%** (+4.0%) |
| + Memory | 61.0% (+2.5%) |
| + All | 60.5% (+2.0%) |
| + RAG | 57.0% (−1.5%) |

**Key insights**:
- **Skill** brings the largest gain through workflow restructuring
- **RAG** retrieves irrelevant commonsense passages that add noise for this task type
- **Memory** (playbook) provides stable but modest improvement
- See `docs/0428效果分析.md` for full analysis across three task types

---

## Design Principles

1. **Core is domain-agnostic.** Nothing in `tom_harness/` (outside `plugins/tom/`) mentions belief, emotion, faux-pas, etc.
2. **Schemas are stable.** Fields in `schemas.py` follow the original project spec. Use `metadata: dict` for extensions.
3. **Memory Store is queried in every planning pass** (mandatory warm-start, even if empty).
4. **Plugins register through hooks, never by editing core.** Seven well-defined extension points.
5. **No heavy frameworks in core.** No LangChain/AutoGen/LangGraph dependency (only in RAG backend).
6. **Deterministic where possible.** State-tracking skills use Python; LLM only for structured parsing.
7. **Bilingual.** Feature extractors, skill content, and failure taxonomy support English + Chinese.
8. **Thread-safe.** MemoryStore uses RLock; runners support parallel execution via ThreadPoolExecutor.
9. **Crash-resumable.** Memory persistence via JSONL; LLM interaction caching for replay.

---

## Extending the Framework

### Adding a New Skill

1. Create `SKILL.md` in a skill directory with frontmatter:
   ```yaml
   ---
   skill_id: my_skill
   name: My Custom Skill
   description: What this skill does
   triggers:
     - pattern1
     - pattern2
   ---
   ```
2. Write the skill workflow in the body (Markdown)
3. (Optional) Add a procedural handler in Python for deterministic execution
4. Load via `skill_lib.load_dir(path)` or register handler via `skill_lib.register_handler()`

### Adding a New Plugin

1. Create a new module under `plugins/`
2. Register hooks via `hook_registry.register(event_name, callback_fn)`
3. Available hooks: `before_plan`, `after_plan`, `before_step`, `after_step`, `on_step_failure`, `before_finalize`, `enrich_memory`

### Adding Custom Knowledge to RAG

1. Create a JSONL file in `tom_harness/tools/tomrag/data/`
2. Format: `{"id": "...", "text": "...", "source": "my_source", "category": "...", "title": "...", "metadata": {}}`
3. Add your source to the `sources` list in `ToMRAG.build_index()`
4. Run `build_index(force_rebuild=True)` to rebuild

---

## License

Research code — see `LICENSE` (to be added).

---

## References

- [XSkill](https://arxiv.org/abs/2603.12056) — dual-stream continual learning.
- [Externalization in LLM Agents](https://arxiv.org/abs/2604.08224) — harness engineering framework.
- [Natural-Language Agent Harnesses](https://arxiv.org/abs/2603.25723) — harness as natural-language artifact.
