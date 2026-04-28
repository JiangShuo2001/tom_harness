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

- **Skills** — curated reasoning prompts (27 skills across two contributor packs)
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
│  │ (state machine) │ │  (dispatch)     │ │ (phase-aware)   │   │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘   │
│           │                   │                   │             │
│  ┌────────▼────────────────────▼───────────────────▼────────┐  │
│  │                     Planner Agent                         │  │
│  │ 1. query Memory Store for warm-start                     │  │
│  │ 2. inject Memory Playbook / Skill prompt (if enabled)    │  │
│  │ 3. generate structured JSON plan (phases → steps)        │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │                  Executor Agent                           │  │
│  │   ReAct loop per step: Reason → Act → Observe             │  │
│  │   Phase-aware accumulated results → Finalizer             │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │                     Tool Layer                            │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │  │
│  │  │ Memory Store │ │  Skill Lib   │ │  RAG Engine  │      │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘      │  │
│  │  ┌──────────────────────────────────────────────────┐     │  │
│  │  │ External Skill Packs (Set1: 15, Set2: 12 skills)│     │  │
│  │  │ + Selective Router (regex-based, no LLM call)    │     │  │
│  │  └──────────────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────────┘  │
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
export TOM_MODEL="qwen3-32b"
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
│   ├── schemas.py                       ← Pydantic data models
│   ├── llm.py                           ← LLM client + interaction cache
│   ├── context.py                       ← ContextManager (three-tier + playbook)
│   ├── registry.py                      ← ToolRegistry (dispatch)
│   ├── hooks.py                         ← plugin hook system
│   ├── planner.py                       ← Planner Agent
│   ├── executor.py                      ← Executor Agent (ReAct)
│   ├── scheduler.py                     ← Scheduler (orchestrator + replan)
│   │
│   ├── tools/
│   │   ├── base.py                      ← Tool ABC
│   │   ├── memory.py                    ← MemoryStore (dynamic task-plan pairs)
│   │   ├── playbook.py                  ← MemoryPlaybook (static strategy loader)
│   │   ├── skills.py                    ← SkillLib (SKILL.md loader)
│   │   ├── rag.py                       ← RAGEngine (FAISS adapter)
│   │   └── tomrag/                      ← ToMRAG sub-package
│   │       ├── rag.py                   ← LangChain + FAISS core
│   │       ├── data/                    ← knowledge corpus (577k entries)
│   │       └── index/                   ← FAISS vector index (built at runtime)
│   │
│   ├── plugins/
│   │   ├── tom/                         ← ToM-specific hook plugins
│   │   └── external_skill_pack/         ← contributed skill packs
│   │       ├── adapter.py               ← SkillPackAdapter ABC
│   │       ├── set1_adapter.py          ← Set1 adapter (15 SKILL.md skills)
│   │       ├── set2_adapter.py          ← Set2 adapter (12 prompt-string skills)
│   │       ├── selective_router.py      ← regex-based skill router (no LLM call)
│   │       └── data/                    ← skill definition files
│   │           ├── skill_set1/          ← 15 SKILL.md files (faux-pas, belief, emotion…)
│   │           └── skill_set2/          ← skills.py + llm_router.py (12 skills)
│   │
│   └── skill_router.py                 ← LLM-based skill router (12 hardcoded skills)
│
├── examples/
│   ├── run_demo.py                      ← single-question demo
│   ├── run_tombench_harness.py          ← ToMBench full harness runner
│   ├── run_selective_harness.py         ← thin harness (selective routing)
│   ├── run_cogtom_harness.py            ← CogToM benchmark runner
│   ├── run_ablation.sh                  ← ablation experiment script
│   └── run_compare_skill_packs.py       ← skill pack comparison runner
│
├── docs/                                ← analysis documents
│
└── results/                             ← output (gitignored)
```

---

## Skill System

The harness supports two parallel skill routing systems:

### LLM-based router (`skill_router.py`)

Calls the LLM once to pick the best skill from 12 hardcoded prompts (S1–S12). Used by the full harness via `--skill` flag. Each skill is a structured reasoning workflow (e.g. Extract→Calibrate→Select for scalar implicature).

### Selective router (`plugins/external_skill_pack/selective_router.py`)

Regex-based router over 27 external skills (15 from Set1 + 12 from Set2). No extra LLM call — routes by pattern-matching on question text. Falls back to "raw" (no skill) when no pattern matches. Used by the thin harness (`run_selective_harness.py`).

### Ablation findings (Scalar Implicature Test, n=200)

| Variant | Accuracy |
|:--------|:---------|
| Baseline (framework only) | 58.5% |
| + Skill | **62.5%** (+4.0%) |
| + Memory | 61.0% (+2.5%) |
| + All | 60.5% (+2.0%) |
| + RAG | 57.0% (−1.5%) |

Skill brings the largest gain through workflow restructuring. RAG retrieves irrelevant commonsense passages that add noise. Memory (playbook) provides stable but modest improvement. See `docs/0428效果分析.md` for full analysis across three task types.

---

## Design Principles

1. **Core is domain-agnostic.** Nothing in `tom_harness/` (outside `plugins/tom/`) mentions belief, emotion, faux-pas, etc.
2. **Schemas are stable.** Fields in `schemas.py` follow the original project spec. Use `metadata: dict` for extensions.
3. **Memory Store is queried in every planning pass** (mandatory warm-start, even if empty).
4. **Plugins register through hooks, never by editing core.**
5. **No heavy frameworks.** No LangChain/AutoGen/LangGraph dependency in core.

---

## License

Research code — see `LICENSE` (to be added).

---

## References

- [XSkill](https://arxiv.org/abs/2603.12056) — dual-stream continual learning.
- [Externalization in LLM Agents](https://arxiv.org/abs/2604.08224) — harness engineering framework.
- [Natural-Language Agent Harnesses](https://arxiv.org/abs/2603.25723) — harness as natural-language artifact.
