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

The system separates *strategic planning* from *tactical execution*:

1. **Planner** turns a question into a structured multi-phase plan.
2. **Executor** runs each step via a ReAct (Reason → Act → Observe) loop.
3. **Tool layer** provides externalized cognition: Memory, Skills, RAG.

The architecture follows the spec handed down by the project lead. The
**core is domain-agnostic** (the same skeleton could run legal or math
reasoning); all **ToM-specific knowledge is external** — loaded as
pluggable skills, validators, and failure handlers.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Harness Layer                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │    Scheduler    │ │  Tool Registry  │ │ Context Manager │    │
│  │ (state machine) │ │  (dispatch)     │ │ (three-tier)    │    │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘    │
│           │                   │                   │              │
│  ┌────────▼────────────────────▼───────────────────▼────────┐   │
│  │                     Planner Agent                         │   │
│  │ 1. (mandatory) query Memory Store for warm-start         │   │
│  │ 2. generate structured JSON plan (phases → steps)        │   │
│  └──────────────────────────┬────────────────────────────────┘   │
│                             │                                    │
│  ┌────────────────────▼──────────────────────────────────┐       │
│  │                  Executor Agent                       │       │
│  │        ReAct loop per step: Reason → Act → Observe    │       │
│  └──────────────────────────┬────────────────────────────┘       │
│                             │                                    │
│  ┌────────────────────▼──────────────────────────────────┐       │
│  │                     Tool Layer                        │       │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │       │
│  │  │ Memory Store │ │  Skill Lib   │ │  RAG Engine  │   │       │
│  │  └──────────────┘ └──────────────┘ └──────────────┘   │       │
│  └───────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                    ┌──── plugins/tom/ ────┐
                    │  failure_handlers   │
                    │  memory_index       │
                    │  validators         │
                    │  plan_templates/    │
                    └─────────────────────┘
                    (ToM-specific; none of
                     this lives in core)
```

### Data flow (one task, end to end)

```
question + options
      │
      ▼
ContextManager.begin_task()           (tier-2 state initialized)
      │
      ▼
Planner.plan()
  ├── MemoryStore.run(query=...)      (mandatory warm-start)
  ├── LLM call → JSON Plan
  └── hooks.fire("after_plan")        (plugins may amend)
      │
      ▼
Scheduler iterates phases × steps
      │
      ▼ for each step
Executor.execute_step()
  ├── Reason  (LLM → Reasoning JSON)
  ├── Act     (ToolRegistry.dispatch if step has a tool)
  └── Observe → record in ExecutionContext
      │
      ▼
Executor.finalize_answer()            (LLM picks the letter)
      │
      ▼
Scheduler persists (task, plan) → MemoryStore  (if success)
      │
      ▼
FinalResult  (answer + plan + traces + metadata)
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
The RAG tool layer requires the extra langchain ecosystem + bge-m3 embedding model.

---

## Configuration

The harness talks to an OpenAI-compatible Chat Completions endpoint. Set
three environment variables (or create a `.env` from `.env.example`):

```bash
export TOM_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"
export TOM_API_KEY="<your key>"
export TOM_MODEL="qwen3-32b"
```

The code never hardcodes keys. Runs will fail loudly if `TOM_API_KEY` is
not set.

---

## Quickstart

### Run the single-question demo (Sally-Anne)

```bash
python examples/run_demo.py
```

Expected output:

```
========== FINAL ==========
answer:  A
success: True
plan.task_type: false_belief
phases: ['analyze_sallys_perspective']
num_steps: 1
elapsed: ~9s
```

### Run the ToMBench benchmark (no-tools mode)

```bash
# 20 samples per task × 8 main ToMBench tasks = 160 samples total
python examples/run_tombench_harness.py --limit 20 --workers 8 --tag notools
```

Results land in `results/<tag>/results.jsonl` and `results/<tag>/stats.json`.

### Run the ToMBench benchmark (with RAG retrieval)

**Build the index once before first run** (one-time, then loads from disk in seconds):

```bash
# Full index — ~577k social-norm entries, CPU ~30-60 min
python -c "from tom_harness.tools import RAGEngine; r = RAGEngine(); r.build_index()"

# Or test with a small sample first (100 per source, ~a few minutes)
python -c "from tom_harness.tools import RAGEngine; r = RAGEngine(); r.build_index(num_samples=100); print(f'Done: {r.size()} docs')"
```

After the index is built, enable with `--rag`:

```bash
# 8 main tasks with RAG retrieval
python examples/run_tombench_harness.py --rag --limit 20 --workers 8 --tag with_rag
```

**RAG flags:**

| Flag | Default | Description |
|:---|:---|:---|
| `--rag` | off | Enable RAG retrieval (default is pure plan+execute) |
| `--rag_data_dir` | `tom_harness/tools/tomrag/data` | JSONL knowledge corpus directory |
| `--rag_index_dir` | `tom_harness/tools/tomrag/index` | FAISS index directory |
| `--rag_model` | `model/bge-m3` | Embedding model path |

### Use as a library

```python
from tom_harness import (
    LLMClient, ToolRegistry, ContextManager, Planner, Executor, Scheduler,
)
from tom_harness.hooks import HookRegistry
from tom_harness.tools import MemoryStore, RAGEngine, SkillLib

llm = LLMClient(api_base="...", api_key="...", model="qwen3-32b")
registry = ToolRegistry()
ctx = ContextManager()
hooks = HookRegistry()
memory = MemoryStore()
skill_lib = SkillLib()

# RAG: build once, share globally
rag = RAGEngine()            # defaults: tomrag/data + tomrag/index + model/bge-m3
rag.build_index()            # run once before first use; subsequent runs skip this
if rag.size() > 0:
    registry.register(rag)  # RAG registered → Planner sees rag_retrieve in AVAILABLE TOOLS

ctx.install_fixed(
    system_identity="A ToM-focused reasoning agent.",
    tool_schema_summary=registry.schema_summary(),
)

scheduler = Scheduler(
    planner=Planner(llm=llm, registry=registry, context=ctx, hooks=hooks, memory=memory),
    executor=Executor(llm=llm, registry=registry, context=ctx, hooks=hooks, skill_lib=skill_lib),
    registry=registry, context=ctx, hooks=hooks, memory=memory,
)

result = scheduler.run(
    task_id="q1",
    question="Story + question ...",
    options={"A": "...", "B": "...", "C": "...", "D": "..."},
)
print(result.answer, result.plan.task_type)
```

---

## Project structure

```
tom_harness/
├── README.md                           ← you are here
├── README_zh.md                      ← Chinese version
├── requirements.txt
├── .env.example
│
├── tom_harness/                         ← the package
│   ├── __init__.py
│   ├── schemas.py                       ← all Pydantic data models
│   ├── llm.py                           ← thin LLM client
│   ├── context.py                       ← ContextManager (three-tier)
│   ├── registry.py                      ← ToolRegistry (dispatch)
│   ├── hooks.py                         ← plugin hook system
│   ├── planner.py                       ← Planner Agent
│   ├── executor.py                      ← Executor Agent (ReAct)
│   ├── scheduler.py                     ← Scheduler (orchestrator + replan)
│   │
│   ├── tools/
│   │   ├── base.py                      ← Tool ABC
│   │   ├── memory.py                    ← MemoryStore (task-plan pairs)
│   │   ├── skills.py                    ← SkillLib (SKILL.md loader)
│   │   ├── rag.py                       ← RAGEngine (adapter wrapping ToMRAG)
│   │   └── tomrag/                     ← ToMRAG sub-package (FAISS retrieval)
│   │       ├── __init__.py
│   │       ├── rag.py                  ← ToMRAG core (LangChain + FAISS)
│   │       ├── data/                   ← Knowledge corpus (577k entries)
│   │       │   ├── atomic.jsonl        ← ATOMIC commonsense因果 (81k)
│   │       │   ├── social_chem.jsonl   ← Social Chemistry 社会规范 (340k)
│   │       │   └── normbank.jsonl     ← NormBank 行为准则 (155k)
│   │       └── index/                  ← FAISS vector index (built at runtime)
│   │           ├── atomic/
│   │           ├── social_chem/
│   │           └── normbank/
│   │
│   └── plugins/
│       └── tom/                         ← ToM-specific plugin (pluggable)
│           ├── install.py               ← one-call wiring
│           ├── failure_handlers.py      ← 12 ToM failure types → skills
│           ├── memory_index.py          ← ToM metadata enrichment
│           ├── validators.py            ← consistency checks
│           └── plan_templates/          ← markdown plan skeletons
│
├── examples/
│   ├── run_demo.py                    ← single-question walkthrough
│   └── run_tombench_harness.py        ← benchmark runner
│
└── docs/
    └── agent_execution_flow.md         ← Agent execution flow walkthrough
```
│               ├── false_belief.md
│               ├── knowledge_gate.md
│               └── aware_of_reader.md
│
├── examples/
│   ├── run_demo.py                      ← single-question walkthrough
│   └── run_tombench_harness.py          ← benchmark runner
│
└── tests/
```

---

## Design principles (so contributors stay aligned)

1. **Core is domain-agnostic.** Nothing in `tom_harness/` (outside
   `plugins/tom/`) should mention belief, emotion, faux-pas, etc. If you
   find yourself wanting to add ToM-specific logic to core, add a hook
   point instead and put the logic in a plugin.

2. **Schemas are stable.** The fields in `schemas.py` follow the original
   project spec (`plan_id`, `phases`, `steps`, `tool_type`, etc.). Do not
   rename them. To add domain-specific fields, use the generic
   `metadata: dict` slot available on `Plan`, `Phase`, `Step`, and
   `Memory`.

3. **Memory Store is queried in every planning pass.** This is mandatory
   per spec and cannot be skipped — even a cold (empty) memory still
   receives the query.

4. **Plugins register through hooks, never by editing core.** Supported
   hook events: `before_plan`, `after_plan`, `before_step`, `after_step`,
   `on_step_failure`, `before_finalize`, `enrich_memory`.

5. **No heavy frameworks.** We deliberately do not depend on LangChain,
   AutoGen, LangGraph, CrewAI, etc. Keeps the system inspectable and
   debuggable at the research level.

---

## Current status

| | |
|---|---|
| Version | **1.1** |
| Core code | ~2.4 K lines of Python |
| No-tools baseline | **66.9%** on 160 ToMBench samples (qwen3-32b) |
| RAG mode | **Integrated** — ToMRAG 577k social-norm entries + bge-m3 FAISS index |
| RAG activation | `--rag` flag (off by default; pure plan+execute otherwise) |
| Memory/Skill tool wiring | Not enabled by default yet (interface ready) |

---

## How to contribute

### Workflow (branch + PR)

Do **not** push directly to `main`. `main` is protected and only accepts
merges via Pull Request with at least one approving review.

```bash
# 1. Sync your local main
git switch main
git pull

# 2. Create a feature branch (use a descriptive name)
git switch -c feature/wire-memory-tool

# 3. Make changes, commit often with clear messages
git add <files>
git commit -m "Wire MemoryStore into ToolRegistry"

# 4. Push your branch to GitHub
git push -u origin feature/wire-memory-tool

# 5. Open a Pull Request on GitHub targeting main.
# 6. Address review comments by pushing more commits to the same branch.
# 7. After approval, squash-merge or rebase-merge via the GitHub UI.
```

Branch naming convention:
- `feature/<short-desc>` — new capability
- `fix/<short-desc>`     — bug fix
- `exp/<short-desc>`     — research experiment (may never merge)
- `docs/<short-desc>`    — documentation only

### How to add a new tool

1. Subclass `tom_harness.tools.base.Tool` in a new file under
   `tom_harness/tools/`.
2. Implement `tool_type`, `tool_name`, `description`, `validate_params`,
   `run`.
3. Export it from `tools/__init__.py`.
4. Register an instance with `ToolRegistry.register(my_tool)` in your
   entry-point script.

### How to add a new skill

Drop a `SKILL.md` file into `plugins/tom/plan_templates/` (or your own
plugin directory) with this frontmatter:

```markdown
---
name: my_skill
skill_id: S12_my_skill
description: One-line description.
triggers:
  - "phrase that should activate this skill"
---

## Workflow
1. …
2. …

## Output shape
…
```

Load it by calling `SkillLib(skills_dir=Path(".../plan_templates"))` or
`skill_lib.load_dir(path)`.

For procedural skills (deterministic Python rather than LLM-guided),
call `skill_lib.register_handler(skill_id, handler_fn, ...)` after
loading the markdown.

### How to add a plugin hook

Plugins register callbacks against named events:

```python
from tom_harness.hooks import HookRegistry, RecoveryDirective

def my_failure_handler(step, trace, context):
    # inspect, then return a RecoveryDirective or None
    return RecoveryDirective(action="replan", failure_type="my_ftype")

hooks = HookRegistry()
hooks.register("on_step_failure", my_failure_handler)
```

Events currently fired by the core (see `hooks.py` for the up-to-date
list):
- `before_plan(question=..., task_type=...)`
- `after_plan(plan=...)` → may return an amended Plan
- `before_step(step=..., context=...)`
- `after_step(step=..., trace=..., context=...)`
- `on_step_failure(step=..., trace=..., context=...)` → RecoveryDirective
- `before_finalize(accumulated_results=...)`
- `enrich_memory(memory=...)` → may return an amended Memory

---

## Roadmap

- [ ] **v0.2** — Wire `MemoryStore` + `SkillLib` into `ToolRegistry` by
      default; install the ToM plugin in `run_tombench_harness.py`.
- [ ] **v0.3** — Ship `RAGEngine` with a social-norm knowledge corpus
      (Faux-pas patterns, pragmatic conventions).
- [ ] **v0.4** — Per-task-type plan templates (Scalar / Persuasion have
      their own shapes); replace `pragmatic_inference` over-classification.
- [ ] **v0.5** — Run on CogToM and ToMATO benchmarks (same harness,
      different adapters).
- [ ] **v1.0** — Meta-Harness style outer loop that optimizes the harness
      itself over benchmark score.

---

## License

Research code — see `LICENSE` (to be added). Default: all rights reserved
until the team agrees on an open-source license.

---

## References

Architecture inspired by:

- [XSkill](https://arxiv.org/abs/2603.12056) — dual-stream (experience + skill) continual learning.
- [Externalization in LLM Agents](https://arxiv.org/abs/2604.08224) — harness engineering framework.
- [Natural-Language Agent Harnesses](https://arxiv.org/abs/2603.25723) — harness as editable natural-language artifact.

See `../survey_1/symbolictom_repro/REPORT_HARNESS_SURVEY.md` (internal) for
a full survey of the harness landscape.
