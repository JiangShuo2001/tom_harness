# Harness Optimizer（中文版）

> 面向 `tom_harness` Theory-of-Mind QA Runtime 的**独立、非侵入式**离线优化器。

本模块完整位于 `coding/optimizer/` 目录下，**不 import** `tom_harness`，
**不修改**仓库内任何已有文件，整体可删除而不影响 runtime 运行。

---

## 1. 它是什么

`HarnessRuntime v3`（位于 `tom_harness/runtime.py`）是 **在线**单次推理执行器：
route → gather（skill / RAG / memory）→ prompt compose → LLM 调用 → validator → 返回。

`HarnessOptimizer` 是 **离线 / 半离线的外层优化循环**。它读取历史执行 trace
和 search set，搜索更优的 **policy bundle**，并以 YAML 形式产出。
Runtime 可加载该 bundle 来改变其 routing / gating / prompt 组装 / RAG /
memory / validator 行为，**不需要改代码**。

```
HarnessRuntime v3 :  在线执行器     （每个样本一次推理）
HarnessOptimizer  :  离线外层循环   （在 policy bundle 空间搜索）
PolicyBundle      :  YAML 工件      （两者之间的契约）
```

v0.1 中 optimizer **本身不调用 LLM**。它产出 policy，由 demo 与（未来的）
evaluator 应用。首批生产用途有两个：
(a) 提供手工调好的默认 policy；
(b) 为后续 Meta-Harness 搜索循环奠定底座。

---

## 2. 四个优化方向

| # | 方向 | v0.1 状态 |
| - | --- | --------- |
| 1 | **RouteDecision + Module-Gate Optimizer**（Phase 1 + 2） | 完整实现（`targets/route_gate_target.py`） |
| 2 | **PromptComposer Optimizer**（Phase 3） | 完整实现（`targets/prompt_compose_target.py`） |
| 3 | **RAG / Memory / Skill 内部策略 Optimizer** | 仅有 schema + stub（`targets/rag_memory_skill_todo.py`） |
| 4 | **Validator / Finalizer / Recovery Optimizer** | 仅有 schema + stub 接口（`targets/validator_todo.py`） |

只有方向 1 和 2 拥有可运行的 demo（`route-gate-demo`、`prompt-demo`）
和完整的默认 policy。方向 3 和 4 的 schema 已经稳定，未来可在不破坏
policy 文件格式的前提下补全 engine。

---

## 3. 目录结构

```
coding/optimizer/
├── README.md                       ← 英文版
├── README_cn.md                    ← 当前文档
├── __init__.py
├── __main__.py                     ← 启用 `python -m optimizer …`
├── interfaces.py                   ← dataclass + OptimizerTarget ABC
├── config.py                       ← YAML 适配器 + 路径
├── policy_bundle.py                ← PolicyBundle（load / dump / merge / validate）
├── experience_store.py             ← ExperienceStore（每次 run 的文件 I/O）
├── trace_schema.py                 ← Trace dataclass + failure-type 词表
├── cli.py                          ← argparse CLI（子命令见下）
├── targets/
│   ├── route_gate_target.py        ← (1) RouteGatePolicyEngine     — 已完成
│   ├── prompt_compose_target.py    ← (2) PromptComposePolicy       — 已完成
│   ├── rag_memory_skill_todo.py    ← (3) RAG / memory / skill stub — TODO
│   └── validator_todo.py           ← (4) ValidatorPolicy stub      — TODO
├── policies/
│   ├── default_route_gate_policy.yaml
│   ├── default_prompt_compose_policy.yaml
│   └── default_policy_bundle.yaml  ← 完整 bundle（含全部 5 个 slot）
├── examples/
│   ├── route_gate_example_input.jsonl
│   └── prompt_compose_example_input.json
└── docs/
    ├── integration_suggestions.md  ← 后续如何接入 tom_harness
    └── design_notes.md             ← 为什么这么设计
```

`optimizer_runs/` 在包**外**生成（相对 CLI 工作目录），保证经验工件
永远不写入本包，也不写入 `tom_harness/`。

---

## 4. 快速上手

两个 demo 不需要 LLM、不需要联网。

```bash
# 在项目根目录（coding/ 的上一级）下：
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

### 两个 demo 各演示什么

**route-gate-demo** 把 policy 应用到 6 个代表性样本，逐样本输出 gate 决策。
使用默认 policy 时你应当看到：

* `FalseBelief_0001` → skill=on（命中 positive trigger `believes`），rag=off，memory=on。
* `Ambiguous_0022` → skill=**off**（negative trigger `'what observer thinks'`
  成功捕获误触发），memory=on，validators 含
  `actor_observer_checker` + `anti_overmentalizing_checker`。
* `Ambiguous_0023` → skill=on（positive trigger `smile gaze nod`）。
* `LowConf_0001` → skill=**off**（`confidence 0.55 < 0.72`）。

**prompt-demo** 渲染一个 Ambiguous Social Cue 样本。使用默认 policy 时
你应当看到：

* relevance 0.32 的 RAG 被丢弃（`rag_min_relevance: 0.72`）。
* `memory_top_k: 3` 生效（5 条 memory 按优先级裁到 3 条）。
* Story 与 options 原文保留，置于 prompt 末尾。
* `add_anti_overmentalizing_instruction` 注入到 system prompt。
* 因 skill confidence (0.86) 超过 `skill_as_hard_constraint_threshold` (0.85)，
  skill 以 **hard constraint** 形式渲染。
* token 估值远低于 3500 budget。

---

## 5. PolicyBundle 格式

完整示例见
[`policies/default_policy_bundle.yaml`](policies/default_policy_bundle.yaml)。
顶层结构：

```yaml
version: "0.1.0"
created_at: "auto"
description: "..."

route_gate_policy:        # v0.1 已填充
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

prompt_compose_policy:    # v0.1 已填充
  global_token_budget: 3500
  priority:        { task_story: 100, options: 100, skill: 80, memory: 60, rag: 40 }
  module_budgets:  { skill: 700, memory: 900, rag: 500 }
  rules: { ... }

rag_policy:               # 仅 schema（方向 3 TODO）
memory_policy:            # 仅 schema
validator_policy:         # 仅 schema（方向 4 TODO）

metadata:
  optimized_on: [ToMBench-search]
  metrics: { accuracy: null, avg_tokens: null, repair_count: null, damage_count: null }
  notes: ["..."]
```

任意 slot 可以缺失；缺失即表示"使用 runtime 内置默认行为"。

---

## 6. 与 runtime 的非侵入式集成

当前 checkpoint 中 `tom_harness/` **完全未被改动**。如果未来希望让
runtime 可选地读取 policy bundle，仅需对少量文件做加性改动，详见
[`docs/integration_suggestions.md`](docs/integration_suggestions.md)。
要点：

* `HarnessRuntime` 增加可选参数 `policy_bundle_path`。该参数为 `None` 时，
  行为与今天逐字节一致。
* 该参数非空时，runtime 询问 `RouteGatePolicyEngine` 拿 gate 决策、
  询问 `PromptComposePolicy` 拿 messages、询问 `ValidatorPolicy` 拿
  本次该跑哪些 validator。

以上**全部尚未实施** —— 它们是 markdown 文件中的纯建议。

---

## 7. CLI 参考

```text
python -m optimizer.cli inspect
python -m optimizer.cli route-gate-demo --policy <yaml> --input <jsonl>
python -m optimizer.cli prompt-demo     --policy <yaml> --input <json> [--output <md>]
python -m optimizer.cli init-run        [--name <slug>] [--runs-dir <dir>]
python -m optimizer.cli validate-policy --policy <yaml>
```

如果 `coding/` 不在 `PYTHONPATH` 中，请改用全限定模块路径：
`python -m coding.optimizer.cli …`。

---

## 8. 依赖

仅 Python 标准库 + **可选** `PyYAML`。

未安装 PyYAML 时，包会回退到 `config.py:_MiniYamlParser` 中的极简
缩进式 YAML reader，足以读取 `policies/*.yaml` 中使用的子集。
若需要手工编写复杂 policy，建议 `pip install pyyaml`。

---

## 9. 后续工作

* **方向 3** —— 把 RAG / memory / skill 的 stub 升级为可被搜索的真实
  engine。`default_policy_bundle.yaml` 中的 schema 已经稳定，仅需补
  engine 实现。
* **方向 4** —— 实现 8 个 ToM-specific validator 与 ValidatorPolicy 聚合器。
* **Proposer** —— 把 `experience_store` 中的 trace 接入 Claude Code 或
  Codex 提案器，让其在每轮 optimizer run 中变更 `candidate_policy.yaml`。
* **Evaluator** —— 在 `repair_count` / `damage_count` /
  `baseline_correct_retention` / `context_cost` / `latency` 上为
  candidate bundle 打分。具体度量定义见
  [`docs/design_notes.md`](docs/design_notes.md)。
