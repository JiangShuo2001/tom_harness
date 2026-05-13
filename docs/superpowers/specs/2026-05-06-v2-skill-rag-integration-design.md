# V2 Skill/RAG Integration Design

**Date:** 2026-05-06
**Branch:** `experiment/v2-skill-rag-memory`
**Strategy:** Approach A — adapt HarnessRuntime to host v2 components

## Goal

Replace the existing skill (12 hardcoded skills + signature-based routing) and RAG (custom FAISS wrapper, no category awareness) systems with:

- **Skills v4**: 22 declarative SKILL.md skills with LLM-based routing
- **RAG v2**: Category-aware retrieval with keyword reranking and rewritten-cluster support

The three prompt-injection modules (Skill, RAG, Playbook) operate independently and are toggled via CLI flags. MemoryStore and Playbook remain unchanged.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Integration strategy | Full replacement | No v1/v2 coexistence needed |
| Router | v4 LLM router replaces all existing routing | v4 router is self-contained, auto-builds catalog from SKILL.md frontmatter |
| Procedural handlers | Remove | v4 skills encode equivalent logic as prompt instructions; keeping handlers creates dual paths |
| RAG + Skill relationship | Independent modules | Each injects its own section into the prompt; no inter-dependency |
| Prompt assembly | Per-module on/off via CLI flags | Matches existing `--skill`, `--rag`, `--memory` pattern in run_tombench_harness.py |
| Runtime architecture | Keep HarnessRuntime (single-shot + validator-retry) | Proven architecture; validator-retry has independent value |

## File Structure Changes

### Move into project

| Source (repo root) | Destination (tom_harness/) | Notes |
|---|---|---|
| `skills_v4/skill1..22/` | `tom_harness/tools/skills_v4/skill1..22/` | 22 SKILL.md + references dirs |
| `skills_v4/llm_router.py` | `tom_harness/tools/skills_v4/llm_router.py` | Catalog builder + router prompt + parser |
| `skills_v4/ROUTING.md` | `tom_harness/tools/skills_v4/ROUTING.md` | Router guide document |
| `rag_v2/src/rag_v2.py` | `tom_harness/tools/rag_v2.py` | ToMRAGv2 class (single file) |
| `rag_v2/data/*.jsonl` | `tom_harness/tools/rag_v2_data/` | JSONL knowledge bases |
| `rag_v2/index_rewritten/` | `tom_harness/tools/rag_v2_index/` | Pre-built FAISS indices |

### New files

| Path | Purpose |
|---|---|
| `tom_harness/routing/skill_v4_router.py` | `SkillV4Router(Router)` — LLM-based router adapter |
| `tom_harness/tools/skills_v4/__init__.py` | Package init for skills_v4 module |

### Modified files

| Path | Change |
|---|---|
| `tom_harness/routing/base.py` | Remove "MUST NOT make LLM calls" constraint from Router docstring |
| `tom_harness/runtime.py` | Extend `_build_user_prompt` for 3-module injection; update `HarnessRuntime` to accept optional `rag_engine` and `playbook`; update `build_default_runtime` factory |
| `tom_harness/tools/__init__.py` | Export `RAGv2Engine` and `SkillV4Router` |
| `examples/run_tombench_harness.py` | Use new components; update `--rag*` defaults to point at `rag_v2_data/`; add `--rag_rewritten` flag |

### Delete

| Path | Reason |
|---|---|
| `tom_harness/skill_router.py` | Replaced by `skills_v4/llm_router.py` |
| `tom_harness/plugins/tom/skills/handlers.py` | Procedural handlers removed |
| `tom_harness/plugins/tom/router.py` | Signature-based routing removed |
| `tom_harness/tools/tomrag/` | Old RAG backend replaced by rag_v2 |
| `tom_harness/tools/rag.py` | Old RAGEngine replaced by RAGv2Engine |
| `tom_harness/tools/skills.py` | Old SkillLib replaced by skills_v4/llm_router.py |

## Component Designs

### SkillV4Router

Location: `tom_harness/routing/skill_v4_router.py`

```python
@dataclass
class SkillV4Router(Router):
    llm: LLMClient
    skills_dir: Path  # points to tom_harness/tools/skills_v4/

    def route(self, *, question, story, options, task_type=None) -> RouteDecision:
        # 1. Import and use skills_v4.llm_router.build_router_prompt()
        # 2. self.llm.chat() with router system prompt
        # 3. parse_router_choice() → skill_id or None
        # 4. Return RouteDecision(skill_id=skill_id)

    def get_skill_body(self, skill_id: str) -> str | None:
        # Delegate to skills_v4.llm_router.get_skill_prompt()
```

The router uses `LLMClient.chat()` (same interface as the rest of the harness) rather than the standalone `model.interact()` pattern from skills_v4's original `route()` function. This keeps the LLM abstraction consistent.

The `skills_v4/llm_router.py` module's `ROUTER_CATALOG`, `build_router_prompt`, `parse_router_choice`, and `get_skill_prompt` functions are reused directly. The `route()` convenience function (which expects a different model interface) is not used.

### RAGv2Engine

Location: `tom_harness/tools/rag_v2.py`

```python
@dataclass
class RAGv2Engine:
    data_dir: str
    index_dir: str
    model_name: str = "model/bge-m3"
    use_rewritten: bool = True

    _backend: ToMRAGv2 | None  # lazy init

    def build_index(self, force_rebuild=False, num_samples=-1):
        # Instantiate ToMRAGv2 and call build_index()

    def retrieve(self, query: str, category: str | None = None, top_k: int = 5) -> str:
        # search() + format_context() → prompt-injectable string

    def size(self) -> int:
        # Total indexed documents
```

`ToMRAGv2` is embedded directly (not wrapped as a Tool subclass) since the runtime calls it explicitly rather than through the registry. Dependencies: `langchain-community`, `langchain-core`, `faiss-cpu`.

### Prompt Assembly

Location: `tom_harness/runtime.py`

The `_build_user_prompt` function gains three optional keyword arguments:

```python
def _build_user_prompt(*, story, question, options,
                       skill_body=None,
                       rag_context=None,
                       playbook=None) -> str:
```

Assembly order when all three are present:

1. `## Reasoning Skill (apply before answering)` — skill_body
2. `## Background Knowledge` — rag_context
3. `## Playbook` — playbook
4. `## Story` — story text
5. `## Question` — question text
6. `## Options` — formatted A/B/C/D
7. `## Answer` — output format instruction

Each section is only included if its value is non-None and non-empty.

### HarnessRuntime Changes

```python
@dataclass
class HarnessRuntime:
    llm: LLMClient
    router: Router                         # now SkillV4Router
    validators: list[Validator]
    rag_engine: RAGv2Engine | None = None  # NEW
    playbook: str | None = None            # NEW — static text

    def answer_one(self, *, question, story, options, task_type=None) -> RuntimeResult:
        # 1. Route
        decision = self.router.route(...)
        skill_body = self.router.get_skill_body(decision.skill_id) if decision.skill_id else None

        # 2. RAG retrieve (if engine present)
        rag_context = None
        if self.rag_engine:
            rag_context = self.rag_engine.retrieve(query=question, category=task_type)

        # 3. Build prompt with all available modules
        base_user = _build_user_prompt(
            story=story, question=question, options=options,
            skill_body=skill_body, rag_context=rag_context, playbook=self.playbook,
        )

        # 4. LLM call + validators (unchanged logic)
        ...
```

`skill_lib: SkillLib` field is removed. The router itself holds skill content access via `get_skill_body()`.

### run_tombench_harness.py Changes

The `build_harness()` function changes to construct `HarnessRuntime` (instead of `Scheduler`):

```python
def build_harness(*, rag_engine=None, playbook=None, skill_router=None,
                  cache_dir=None, enable_validator=True):
    llm = LLMClient(...)
    router = skill_router or SkillV4Router(llm=llm, skills_dir=SKILLS_V4_DIR)
    return build_default_runtime(
        llm=llm, router=router,
        rag_engine=rag_engine, playbook=playbook,
        enable_scalar_validator=enable_validator,
    )
```

CLI flag changes:
- `--rag_data_dir` default → `tom_harness/tools/rag_v2_data/`
- `--rag_index_dir` default → `tom_harness/tools/rag_v2_index/`
- New: `--rag_rewritten` (bool, default True) — controls `use_rewritten` flag
- `--skill` now implies SkillV4Router (no more SkillRouter from skill_router.py)

The `process_one()` function changes to call `runtime.answer_one()` instead of `scheduler.run()`. The result record format updates accordingly (no more `num_phases`, `plan_task_type`, `phase_names` — these were Plan/Execute artifacts).

## Plan/Execute Pipeline

The old `Scheduler → Planner → Executor` pipeline (`scheduler.py`, `planner.py`, `executor.py`) remains in the codebase but is no longer used by the main runner. The runner now calls `HarnessRuntime.answer_one()` directly. These files are not deleted (they may serve future multi-step research scenarios) but receive no modifications.

The `plugins/tom/install.py` wiring that registered hooks, plan templates, and procedural handlers into the old pipeline is also left in place but becomes inert for the new path.

## What Stays Unchanged

- `tom_harness/llm.py` — LLMClient interface
- `tom_harness/tools/memory.py` — MemoryStore
- `tom_harness/tools/playbook.py` — MemoryPlaybook
- `tom_harness/validators/` — ScalarProceduralValidator and base
- `tom_harness/hooks.py` — HookRegistry
- `tom_harness/schemas.py` — data models
- `benchmark/` — data loading
- `memory_playbook/` — playbook text files

## Dependency Changes

New runtime dependencies (already used by rag_v2):
- `langchain-community`
- `langchain-core`
- `faiss-cpu` (replaces direct faiss usage in old tomrag)

Removed:
- No new dependencies for skills_v4 (pure Python + SKILL.md files)

## Testing Strategy

1. **Smoke test**: Run `python examples/run_tombench_harness.py --limit 5` with each flag combination (`--skill`, `--rag`, `--memory`, all three, none)
2. **Router accuracy**: Compare v4 router's skill assignment against known task_type → skill mappings
3. **RAG retrieval**: Verify category-aware routing returns relevant passages for known categories
4. **Regression**: Compare overall accuracy on a fixed sample set before/after migration
