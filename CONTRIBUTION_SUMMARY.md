# Merge Candidate — Contribution Summary

> **Branch**: `merge/jingshuo-from-jiangshuo`
> **Source**: `feature/external-skill-packs` HEAD = `db5f58c`
> **Common ancestor with `experiment/plan-a-skill-rag-inject`**: `9c994ab`
> **Date**: 2026-04-28
> **Author of this distillation**: jiangshuo branch

This branch is offered for merge against `main` (or for jingya to integrate
into his branch). Below is what we contributed since fork from `9c994ab`.

---

## Headline result

On 160-sample stratified ToMBench pool, **qwen-plus** model:

| Configuration | Overall | Source |
|---|---:|---|
| raw direct (no skill, no harness) | **73.8%** | `examples/run_skills_direct.py` |
| selective_v04 inferred (signature router) | **78.1%** | `examples/run_selective_harness.py` |
| oracle per-task best skill (matrix sweep) | **81.2%** | `examples/run_skill_matrix.py` |
| selective_v04 oracle (rule + task labels) | **78.8%** | thin harness |
| full harness baseline (Plan/Execute/Finalize) | 69.4% | `examples/run_compare_skill_packs.py` |
| full harness + selective_v04 | 70.6% | same |

Direct/thin path beats full harness by ~7pp — Plan/Execute multi-step
adds noise on this benchmark. Selective routing (gated skill application)
is the breakthrough. Oracle 81.2% has small-sample selection bias; CV
de-watered estimate is ~76-78%.

---

## A. Skill utilization (~70% of contribution)

### Adapter pattern — `tom_harness/plugins/external_skill_pack/`
- `adapter.py` — `SkillPackAdapter` ABC + `SkillPackInfo` + `RoutingResult`
- `set1_adapter.py` — wraps the 15 SKILL.md skill pack (rule-based router from `ROUTING.md`)
- `set2_adapter.py` — wraps the 12 set2 prompts + their LLM router (sandbox import to avoid name collision)
- `selective_router.py` — v0.4 signature-driven gate
  - scalar quantifier signal → cs1_skill11/cs1_skill10
  - belief-switch signal → cs1_skill3
  - unexpected-cue signal → cs2_S5_Expectation
  - else → raw

**Design principle**: skill pack source code is NOT modified. Adapters
load their `.md` / `.py` files as black-box prompts.

### Runners — `examples/`
- `run_skills_direct.py` — pure ceiling: skill_body + LLM call, no harness
- `run_selective_harness.py` — thin harness (SkillLib + adapter + selective router; bypasses Plan/Execute)
- `run_compare_skill_packs.py` — full harness (Scheduler + Planner + Executor + adapter)
- **NEW** `run_skill_matrix.py` — sweep all 27 skills × 160 samples; build (task, skill) → acc matrix; compute oracle ceiling
- **NEW** `run_task_classifier_inferred.py` — LLM task classifier + cached per-task best skill (no extra LLM cost beyond classifier)
- **NEW** `run_self_consistency.py` — n=5 majority vote at temp=0.4 on Persuasion + Faux-pas (result: 0 lift; deterministic LLM)

### Frozen artifact — `results/frozen_v04_selective/`
- Immutable record of the v0.4 baseline-beaten configuration (also tagged `v0.4-selective-baseline-beaten`)
- Contains 3 result jsonls + RESULT_REPORT.md

---

## B. Critical bug fixes (B1/B4/B6/B7/B9) — already on jingya branch

`tom_harness/{executor,scheduler,planner}.py`. Full audit in `BUG_AUDIT_REPORT.md`.

- **B1** `_render_accumulated()` JSON-aware renderer (replaces `repr(v)[:400]` which truncated structured outputs mid-JSON)
- **B4** finalize `max_tokens` 256 → 1024
- **B6** scheduler tracks `completed_step_ids`; warns on unmet `depends_on`
- **B7** `_collect_skill_votes` top-level only (no recursion into Memory plan trees → false votes)
- **B9** Planner validates `tool_name` against registry at plan-assembly; unknown tools → pure-reasoning step
- Strengthened `FINALIZE_SYSTEM` prompt with CRITICAL clause

Already ported to jingya's branch as `900d0c6`. **Re-merge will be a no-op
on his side for this part.**

---

## C. Reasoning persistence (B2 fix)

`tom_harness/executor.py` (commit `beee5b0`):
1. After Reason step, write `reasoning_of_step_N` into `accumulated_results`
2. Pass `Reasoning` into `_act()`; declarative skills receive it via `input_context`
3. `REASON_SYSTEM` prompt nudge: "if prior reasoning_of_step_N entries exist, build on them"

**Note**: jingya independently fixed the orphaned-Reasoning bug at `ab5dde7`
with a slightly different approach (passes reasoning chain + plan overview
to Reason and Finalize). Both write into `accumulated_results` — should
merge with manual conflict resolution (4 small hunks, all same-intent
divergences).

---

## D. Methodology

- 3-tier ceiling decomposition: pure direct ↔ thin harness ↔ full harness
- Per-(task, skill) accuracy matrix as the principled oracle measurement
- Empirical confirmation that self-consistency yields 0 lift here (model
  is deterministic on these inputs even at temp=0.4)
- LLM task classifier evaluated against rule-based selective router
  (rule-based wins: 78.1% > classifier 76.9% — narrow rules with raw
  fallback beat 8-way classifier with 27.5% misroute rate)

---

## How to merge

```bash
git fetch origin
git checkout main   # or experiment/plan-a-skill-rag-inject
git merge origin/merge/jingshuo-from-jiangshuo
```

### Expected conflicts (from dry-run on 2026-04-27)

| File | Type | Resolution |
|---|---|---|
| `tom_harness/executor.py` | UU (4 hunks) | Same-intent divergence (REASON prompt wording, f-string folding, `_act(reasoning=)` kwarg, `_render_plan_overview` helper). Keep our `_act` signature with `reasoning=`; keep his `_render_plan_overview` helper; pick either prompt phrasing. |
| `.gitignore` | UU | Trivial; concatenate both rule sets. |

### Auto-merging files (no conflict, may need testing)
`tom_harness/scheduler.py`, `tom_harness/planner.py`, `tom_harness/context.py`, `tom_harness/llm.py`, `tom_harness/tools/__init__.py`, `tom_harness/tools/rag.py`, `examples/run_tombench_harness.py`, `README.md`, `README_zh.md`

### Pure additions from this branch (no conflict)
`tom_harness/plugins/external_skill_pack/`, `examples/run_skills_direct.py`, `examples/run_selective_harness.py`, `examples/run_compare_skill_packs.py`, `examples/run_skill_matrix.py`, `examples/run_task_classifier_inferred.py`, `examples/run_self_consistency.py`, `BUG_AUDIT_REPORT.md`, `results/frozen_v04_selective/` (frozen artifact)

### Pure additions from his branch (no conflict)
`tom_harness/skill_router.py`, `tom_harness/tools/playbook.py`, `tom_harness/tools/tomrag/`, `benchmark/`, `examples/run_cogtom_harness.py`, `docs/下一步计划.md`

The skill systems (`plugins/external_skill_pack/` adapter pattern vs
`tom_harness/skill_router.py` hardcoded router) **don't conflict at the
file level but represent two parallel approaches**. Consider: keep both
side-by-side and decide later which becomes the main path on `main`.

---

## How to validate

After merge, recommended sanity tests:

```bash
# 1. Pure ceiling — should match 73.8% baseline / 78.1% selective on 160 samples
TOM_API_KEY=... TOM_MODEL=qwen-plus python examples/run_skills_direct.py --per_task 20

# 2. Thin harness selective — should match 76-78%
TOM_API_KEY=... TOM_MODEL=qwen-plus python examples/run_selective_harness.py --per_task 20

# 3. Full harness post-fix — should be ~69-71% (the harness drag is real and orthogonal to the bug fix)
TOM_API_KEY=... TOM_MODEL=qwen-plus python examples/run_compare_skill_packs.py --configs baseline selective_v04 --per_task 20

# 4. (Optional, ~6 min) full skill matrix — reproduces oracle 81.2%
TOM_API_KEY=... TOM_MODEL=qwen-plus python examples/run_skill_matrix.py --per_task 20
```
