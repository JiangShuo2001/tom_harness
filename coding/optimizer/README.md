# Harness Optimizer

> A standalone, **non-invasive** offline optimizer for the
> `tom_harness` Theory-of-Mind QA runtime.

The optimizer lives entirely under `coding/optimizer/`. It does not
import from `tom_harness`, does not modify any existing file in the
repository, and can be deleted without affecting the runtime.

---

## 1. What it is

`HarnessRuntime v3` (in `tom_harness/runtime.py`) is the **online**
single-shot executor: route → gather (skill / RAG / memory) → prompt
compose → LLM call → validators → return.

`HarnessOptimizer` is the **offline (or semi-offline) outer loop**.
Given historical execution traces and a search set, it searches for a
better **policy bundle** and writes it out as a YAML file. The runtime
can load that bundle to change its routing, gating, prompt composition,
RAG / memory / validator behaviour — without code changes.

```
HarnessRuntime v3 :  online executor       (one inference per sample)
HarnessOptimizer  :  offline outer loop    (search over policy bundles)
PolicyBundle      :  YAML artefact         (the contract between them)
```

The optimizer **does not run an LLM by itself** in v0.1. It produces
policies that demos and (future) evaluators can apply. The first
real production use is to (a) provide hand-tuned default policies, and
(b) form the substrate for a future Meta-Harness search loop.

---

## 2. The four optimization directions

| # | Direction | Status in v0.1 |
| - | --------- | -------------- |
| 1 | **RouteDecision + Module-Gate Optimizer** (Phase 1 + 2) | Fully implemented (`targets/route_gate_target.py`) |
| 2 | **PromptComposer Optimizer** (Phase 3) | Fully implemented (`targets/prompt_compose_target.py`) |
| 3 | **RAG / Memory / Skill internal-policy optimizer** | Schema + stubs only (`targets/rag_memory_skill_todo.py`) |
| 4 | **Validator / Finalizer / Recovery Optimizer** | Schema + stub interface (`targets/validator_todo.py`) |

Directions 1 and 2 are the only ones that have a demo (`route-gate-demo`,
`prompt-demo`) and a full default policy. The schemas for 3 and 4 are
stable enough that future work can fill in the engines without
touching the policy file format.

---

## 3. Directory layout

```
coding/optimizer/
├── README.md                       ← you are here
├── __init__.py
├── __main__.py                     ← enables `python -m optimizer …`
├── interfaces.py                   ← dataclasses + OptimizerTarget ABC
├── config.py                       ← YAML adapter + paths
├── policy_bundle.py                ← PolicyBundle (load / dump / merge / validate)
├── experience_store.py             ← ExperienceStore (per-run file I/O)
├── trace_schema.py                 ← Trace dataclass + failure-type vocabulary
├── cli.py                          ← argparse CLI (subcommands below)
├── targets/
│   ├── route_gate_target.py        ← (1) RouteGatePolicyEngine     — done
│   ├── prompt_compose_target.py    ← (2) PromptComposePolicy        — done
│   ├── rag_memory_skill_todo.py    ← (3) RAG / memory / skill stubs — TODO
│   └── validator_todo.py           ← (4) ValidatorPolicy stub       — TODO
├── policies/
│   ├── default_route_gate_policy.yaml
│   ├── default_prompt_compose_policy.yaml
│   └── default_policy_bundle.yaml  ← full bundle (slots for all four)
├── examples/
│   ├── route_gate_example_input.jsonl
│   └── prompt_compose_example_input.json
└── docs/
    ├── integration_suggestions.md  ← how to wire into tom_harness later
    └── design_notes.md             ← why these choices
```

`optimizer_runs/` is created **outside** the package (relative to the
working directory of the CLI) so that experience artefacts never live
inside the package or anywhere in `tom_harness/`.

---

## 4. Quick start

The two demos run with no LLM and no network.

```bash
# From the project root (one directory above `coding/`):
cd coding

python -m optimizer.cli inspect

python -m optimizer.cli route-gate-demo \
    --policy optimizer/policies/default_route_gate_policy.yaml \
    --input  optimizer/examples/route_gate_example_input.jsonl

python -m optimizer.cli prompt-demo \
    --policy optimizer/policies/default_prompt_compose_policy.yaml \
    --input  optimizer/examples/prompt_compose_example_input.json

python -m optimizer.cli validate-policy \
    --policy optimizer/policies/default_policy_bundle.yaml

python -m optimizer.cli init-run --name first_run
```

### What the demos demonstrate

**route-gate-demo** runs the policy over 6 representative samples and
shows the gating decision per sample. With the shipped defaults you
should see:

* `FalseBelief_0001` → skill=on (positive trigger `believes`), rag=off, memory=on.
* `Ambiguous_0022` → skill=**off** (`negative trigger 'what observer thinks'`
  caught the misroute), memory=on, validators include
  `actor_observer_checker` + `anti_overmentalizing_checker`.
* `Ambiguous_0023` → skill=on (positive trigger `smile gaze nod`).
* `LowConf_0001` → skill=**off** (`confidence 0.55 < 0.72`).

**prompt-demo** renders one Ambiguous-Social-Cue sample. With the
shipped defaults you should see:

* RAG entry with relevance 0.32 dropped (`rag_min_relevance: 0.72`).
* `memory_top_k: 3` enforced (5 memory entries become 3 in priority order).
* Story and options preserved verbatim, last in the prompt.
* `add_anti_overmentalizing_instruction` injected into the system prompt.
* Skill rendered as a **hard** constraint because its confidence (0.86)
  exceeds the `skill_as_hard_constraint_threshold` (0.85).
* Token estimate well under the 3500 budget.

---

## 5. PolicyBundle format

A complete example lives in
[`policies/default_policy_bundle.yaml`](policies/default_policy_bundle.yaml).
Top-level structure:

```yaml
version: "0.1.0"
created_at: "auto"
description: "..."

route_gate_policy:        # filled in v0.1
  default: { skill: conditional, rag: false, memory: true, validators: [] }
  false_belief: { ... }
  faux_pas:     { ... }
  scalar_implicature: { ... }
  ambiguous_social_cue: { ... }
  skill_policies:
    skill7_nonverbal_cue:
      positive_triggers: [...]
      negative_triggers: [...]
      fallback_skill: observer_perspective_inference
      confidence_threshold: 0.72

prompt_compose_policy:    # filled in v0.1
  global_token_budget: 3500
  priority:        { task_story: 100, options: 100, skill: 80, memory: 60, rag: 40 }
  module_budgets:  { skill: 700, memory: 900, rag: 500 }
  rules: { ... }

rag_policy:               # schema-only (TODO direction 3)
memory_policy:            # schema-only
validator_policy:         # schema-only (TODO direction 4)

metadata:
  optimized_on: [ToMBench-search]
  metrics: { accuracy: null, avg_tokens: null, repair_count: null, damage_count: null }
  notes: ["..."]
```

Slots may be omitted; missing slots mean "use built-in default".

---

## 6. Non-invasive integration with the runtime

`tom_harness` is **untouched** in this checkpoint. To make the runtime
*optionally* read a policy bundle in the future, only a handful of
files need a small additive change. See
[`docs/integration_suggestions.md`](docs/integration_suggestions.md)
for the per-file proposal. The short version:

* `HarnessRuntime` gains an optional `policy_bundle_path` argument. When
  it is `None`, behaviour is byte-identical to today.
* When the bundle is set, the runtime asks `RouteGatePolicyEngine` for
  the gate decision, asks `PromptComposePolicy` for the messages, and
  consults `ValidatorPolicy` for which validators to run.

None of those changes have been performed — they are pure
recommendations in a markdown file.

---

## 7. CLI reference

```text
python -m optimizer.cli inspect
python -m optimizer.cli route-gate-demo --policy <yaml> --input <jsonl>
python -m optimizer.cli prompt-demo     --policy <yaml> --input <json> [--output <md>]
python -m optimizer.cli init-run        [--name <slug>] [--runs-dir <dir>]
python -m optimizer.cli validate-policy --policy <yaml>
```

If `coding/` is not on `PYTHONPATH`, use the fully-qualified module
path instead: `python -m coding.optimizer.cli …`.

---

## 8. Dependencies

Standard library only, plus **optional** `PyYAML`.

If PyYAML is not installed the package falls back to a minimal indent-
based YAML reader (`config.py:_MiniYamlParser`) that handles the
subset of YAML used by `policies/*.yaml`. For non-trivial policies,
`pip install pyyaml` is recommended.

---

## 9. Future work

* **Direction 3** — turn the RAG / memory / skill stubs into real
  engines that can be searched. The schema in
  `default_policy_bundle.yaml` is already stable; only the engines
  need to be filled in.
* **Direction 4** — implement the eight ToM-specific validators and
  the ValidatorPolicy aggregator.
* **Proposer** — wire `experience_store` traces into a Claude Code or
  Codex proposer that mutates `candidate_policy.yaml` for the next
  optimizer run.
* **Evaluator** — score candidate bundles on `repair_count`,
  `damage_count`, `baseline_correct_retention`, `context_cost`,
  `latency`. See `docs/design_notes.md` for the planned metrics.
