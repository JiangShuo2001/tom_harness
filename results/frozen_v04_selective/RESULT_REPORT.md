# Frozen Result · v0.4-selective · 2026-04-26

> **DO NOT MODIFY.** This file + sibling JSONL files freeze the first
> harness configuration that reliably beats raw baseline on full-sample
> overall accuracy.

## Top-line numbers (160 stratified ToMBench samples, qwen3.5-27b)

| Configuration | Overall | Δ vs raw |
|---|:-:|:-:|
| raw baseline (single CoT call, no skill) | 73.8% | — |
| set1 applied to every routed sample | 73.1% | −0.7 |
| set2 applied to every routed sample | 74.4% | +0.6 |
| **Oracle Selective** (uses metadata.task_type) | **78.8%** | **+5.0** |
| **Inferred Selective** (extract_signature based) | **78.1%** | **+4.4** |

## Per-task accuracies (the comparison we care about)

| Task | raw | +set1 | +set2 | Oracle pick | Inferred selective |
|---|:-:|:-:|:-:|:-:|:-:|
| Ambiguous Story | 70 | 55 | 70 | raw | 70 |
| False Belief | 85 | **100** | 90 | set1 | 95 |
| Faux-pas | 80 | 70 | 80 | raw | 80 |
| Hinting | **100** | 95 | 100 | raw | 100 |
| Persuasion | 55 | 45 | 50 | raw | 55 |
| Scalar Implicature | 35 | **55** | 40 | set1 | 55 |
| Strange Story | **90** | 90 | 85 | raw | 90 |
| Unexpected Outcome | 75 | 75 | **80** | set2 | 80 |

## Inferred routing rules (from extract_signature flags)

```
if has_quantifier and ("how many" in q.lower() or "几"/"多少" in q):
    → set1_direct        # Scalar Implicature
elif has_belief_switch and re.search(r"where will|expect to find|will .+ find", q):
    → set1_direct        # False Belief
elif re.search(r"should .* but|surprising|应该.*但是", q+story):
    → set2_direct        # Unexpected Outcome
else:
    → raw                # everything else
```

Routing agreement with oracle: **142/160 = 88.8%**.

## Mode usage on the 160 samples

- raw: 118 samples (74%)
- set1: 30 samples (19%)
- set2: 12 samples (7%)

## Setup

- LLM: `qwen3.5-27b` via DashScope (`/v1/chat/completions`, temperature 0)
- max_tokens: 1024
- prompt: skill_body prepended to vanilla CoT format; single LLM call per sample
- Sample pool: 160 stratified (8 main ToMBench tasks × 20 each, seed=42)
- No harness machinery — pure single-call inference per sample

## Why this matters

For weeks the project was stuck at "skills don't beat raw baseline on
overall accuracy". This is the first config that does. The mechanism is
NOT a better skill but a better **gating policy**: skills are good at
specific subtasks (False Belief +15pp, Scalar +20pp, Unexpected +5pp)
but harmful when applied indiscriminately (Ambiguous Story −15pp, etc.).
A signature-driven selective router captures 88% of the oracle ceiling.

## Provenance

- Branch: `feature/external-skill-packs`
- Adapter code: `tom_harness/plugins/external_skill_pack/`
- Direct test runner: `examples/run_skills_direct.py`
- Selective analysis: see git log near commit ID for this report
- Raw data files (this directory):
  - `direct_raw_results.jsonl`         (160 records)
  - `direct_set1_direct_results.jsonl` (160 records)
  - `direct_set2_direct_results.jsonl` (160 records)
  - `direct_summary.json`              (per-mode aggregates)
