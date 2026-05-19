# Design notes — Harness Optimizer v0.1

This document explains the *why* behind the v0.1 design. The README
covers *how*; this is for future contributors deciding whether to
honour or break a given choice.

---

## 1. Why an offline module instead of inline runtime patches?

There are three reasons we deliberately kept the optimizer outside the
runtime tree:

**Blast radius.** Changing routing / gating / prompt assembly inside
`tom_harness/runtime.py` has high blast radius: every benchmark script
under `examples/` runs through that file. A bad search step would
silently regress benchmark numbers. Keeping the optimizer in a
separate package means any code-path it touches is *new* code-path,
so a bug in the optimizer cannot regress the runtime's existing
behaviour until someone explicitly opts in.

**Iteration speed.** A search loop must be able to evolve its policy
schema rapidly. If the schema lives in runtime code, every iteration
risks a merge conflict with whoever is shipping a runtime fix. With
the schema in `coding/optimizer/policies/*.yaml`, the search loop
mutates YAML; only the integration points (added later) need to be
stable.

**Optionality.** Some research scenarios genuinely want the unmodified
runtime — e.g. measuring the baseline harness lift vs raw LLM. A
`policy_bundle_path=None` switch (see `docs/integration_suggestions.md`
建议 1) keeps that path intact.

---

## 2. Why direction 1 + 2 first?

The brief lists four directions; we cover #1 (route+gate) and #2
(prompt-compose) in v0.1, leaving #3 (RAG/memory/skill internals) and
#4 (validators) as schemas + stubs.

This ordering follows three observations from the existing reports:

* **#1 has the largest negative tail.** The brief calls out that skill
  has clear positive lift on average but causes hard regressions on
  some scenes — the asymmetric loss profile means a per-scene gate
  with positive/negative triggers and confidence thresholds (exactly
  what `route_gate_target` implements) recovers the most accuracy.

* **#2 is the easiest win on context cost.** RAG is described as a net
  negative because its noise is overwriting story-level details. The
  prompt-compose policy can drop low-relevance RAG and cap memory
  top-k *without* needing any model change. The token-budget /
  priority machinery is also a structural place to express the
  "anti-overmentalizing instruction" and "story always wins" rules
  the brief asks for.

* **#3 and #4 require infrastructure that does not yet exist.** A real
  RAG-query-rewriter needs an LLM judge or a labelled relevance set;
  a real ToM validator needs eight new classes implementing
  belief-state / actor-observer / over-mentalizing checks. v0.1 ships
  the schema and YAML examples so those engines can land later
  without breaking the bundle format.

---

## 3. Anti-overfitting strategy

The optimizer is a search loop, so over-fitting to the search set is
the canonical risk. v0.1 builds three guards in:

**Held-out split.** The intended workflow is:

```
ToMBench-full  -- 80/20 -->  search_set / held_out_set
```

Optimizer fitness is computed on `search_set`. The chosen bundle is
*then* re-scored on `held_out_set`; if held-out accuracy regresses
relative to baseline, the bundle is rejected even if search-set
accuracy improved. The `ExperienceStore.save_score` payload should
record both numbers so the proposer can see the gap.

**Penalty for damage_count.** The fitness function is **not** raw
accuracy. It is:

```
fitness = accuracy
        + α · repair_count            (turned wrong into right via modules)
        − β · damage_count            (turned right into wrong via modules)
        − γ · normalised_token_cost
        − δ · normalised_latency
```

`repair_count` and `damage_count` are derivable from each Trace's
`direct_answer` vs `predicted` (see `trace_schema.Trace.repaired` /
`.damaged`). The asymmetric treatment matters: a bundle that flips
ten right answers to wrong is *worse* than one that leaves accuracy
flat, even if it also turns ten wrong answers into right.

**Trigger granularity.** Positive/negative triggers are string-level,
not LLM-judged. That is by design — it limits how aggressively the
optimizer can exploit individual samples. If a single positive
trigger lifts only one sample, the optimizer has learned a near-zero
generalisation signal; we'd rather it explore a coarser knob.

---

## 4. Evaluation metrics

Each run should record at minimum:

| Metric                         | Definition                                          |
| ------------------------------ | --------------------------------------------------- |
| `accuracy`                     | predicted == gold rate                              |
| `baseline_correct_retention`   | of samples where direct_answer == gold, how many remain correct after modules |
| `repair_count`                 | direct_answer ≠ gold AND predicted == gold          |
| `damage_count`                 | direct_answer == gold AND predicted ≠ gold          |
| `avg_prompt_tokens`            | mean of `Trace.prompt_tokens`                       |
| `avg_validator_flags`          | mean count of `validator_flags` per sample          |
| `module_conflict_count`        | sum of conflicts written to `module_conflicts.jsonl`|
| `latency_p50` / `p95`          | placeholder until real runs land                    |

Pareto curve is preferred over a single scalar — the proposer should
keep any bundle that is non-dominated on (accuracy, avg_prompt_tokens,
damage_count).

---

## 5. ExperienceStore as the substrate for a Meta-Harness

The current `ExperienceStore` is intentionally schema-light: it just
writes JSON and YAML to disk. We expect a future Claude-Code / Codex
proposer to:

1. **Read** the latest N runs from `optimizer_runs/`.
2. **Cluster failures** by `failure_type` + `scene_tag`.
3. **Propose** a candidate policy mutation (e.g., "add negative
   trigger 'observer acts after others leave' to
   `skill7_nonverbal_cue`").
4. **Persist** the new candidate at
   `optimizer_runs/run_NNN/candidate_policy.yaml`.
5. **Trigger** an evaluator run.

Because the store never imports anything from `tom_harness`, the
proposer can be any process — a Python script, a Claude Code session,
a Codex CLI invocation. The only contract is the file layout.

The `FAILURE_TYPES` vocabulary in `trace_schema.py` is the
controlled-vocab seed for that clustering step.

---

## 6. Why pure-Python and standard-library-first?

The optimizer must run on the same constrained environments that
researchers use to run tom_harness benchmarks. PyYAML is the only
non-stdlib dependency, and even that is optional thanks to the
mini-YAML parser in `config.py`. Concretely:

* No `pydantic`, no `dataclasses-json`, no `omegaconf`. Adding any of
  them would force the runtime to grow that dep, which violates the
  non-invasive contract.
* No networking, no embeddings, no LLM calls. v0.1 evaluators are
  pure-function over trace files.

---

## 7. Known limitations

* The mini-YAML fallback (`config.py:_MiniYamlParser`) is *deliberately*
  limited. It exists only so the package imports without PyYAML.
  Anyone hand-authoring complex policies should install PyYAML.
* `_trigger_matches` is loose token-overlap. It will produce false
  positives for short triggers. Tightening it to phrase or embedding
  similarity is an obvious next step.
* The token estimator (`_approx_tokens`) uses 4 chars/token; real
  tokenisation may diverge by up to 30%. The optimizer's *structural*
  decisions (drop / crop / preserve) are correct under this estimate;
  exact budget compliance must be re-checked by the runtime with its
  own tokenizer.
* No live integration test against the runtime. That is deferred until
  the integration suggestions are accepted and at least one
  `policy_bundle_path` consumer exists in `tom_harness/runtime.py`.
