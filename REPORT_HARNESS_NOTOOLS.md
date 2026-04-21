# Harness v0.1 — No-Tools Baseline Run

> **模式**: Plan + Execute, 不注册任何工具 (Memory/Skill/RAG 均未挂载到 ToolRegistry)
> **模型**: qwen3-32b (DashScope, enable_thinking=False, temperature=0.0)
> **样本**: ToMBench 8 大任务分层采样，每任务 20 条 → 共 160 样本
> **日期**: 2026-04-20

---

## 1. 结论

| 指标 | 数值 |
|------|------|
| **Overall 准确率** | **113/160 = 70.6%** |
| 规划失败率 | 0/160 |
| 执行错误率 | 0/160 |
| 平均耗时/样本 | **19.8 秒** |
| 平均 phases/plan | 1.54 (min 1, max 3) |
| 平均 steps/plan | 2.56 (min 1, max 6) |

**基础设施层面全部通过**：0 个 parsing 失败、0 个工具分发错误、0 个 plan schema 违规、0 个 context 构建失败。框架本身可以 run。

## 2. 与历史 Baseline 对比（ToMBench 8 大任务）

| 任务 | Harness no-tools<br>(qwen3-32b) | 27B baseline<br>(2月) | 27B think<br>(2月) | 9B baseline<br>(2月) |
|------|:----:|:----:|:----:|:----:|
| Ambiguous Story | 65.0% | 82.0% | 83.5% | 75.0% |
| False Belief | **90.0%** | 86.0% | 95.3% | 77.2% |
| Faux-pas Recognition | 70.0% | 80.5% | 80.0% | 76.4% |
| Hinting Task | **90.0%** | 92.2% | 91.3% | 79.6% |
| Persuasion | 60.0% | 59.0% | 58.0% | 59.0% |
| Scalar Implicature | 35.0% | 49.0% | 56.5% | 46.0% |
| Strange Story | 85.0% | 86.2% | 86.5% | 81.8% |
| Unexpected Outcome | 70.0% | 77.0% | 75.7% | 67.0% |
| **Overall (8 tasks)** | **70.6%** | 78.7% | 81.5% | 72.2% |

注：前三列模型跑的是全量 2860 样本，harness 这列是 160 样本；模型也不同（新 qwen3-32b vs 老 Qwen3.5-27B）。横向比只能看趋势。

**三个观察**:
1. **整体比纯 baseline 低 ~8pp**。不意外——分 N 次 API 调用累积了 parsing 噪声、强制 JSON 结构消耗了一部分 token 预算、且 executor 的每步调用 context 被切碎。这正是"先不加工具"本来该出现的结果。
2. **False Belief 持平甚至反超** (90.0% vs 27B 的 86.0%)。结构化分解对信念追踪有帮助——Planner 倾向于生成"角色识别 → 信念分配"的两阶段 plan，天然匹配 Sally-Anne 模式。
3. **Scalar Implicature 大幅下跌** (35% vs 49%)。量词推理在 CoT 一气呵成时还能做对，拆成多步后反而更容易跑偏。

## 3. Planner 的行为画像

**产出的 task_type 分布**（160 条里）:

| task_type | 数量 | 占比 |
|-----------|----:|----:|
| pragmatic_inference | 114 | 71% |
| false_belief | 14 | 9% |
| general_tom | 11 | 7% |
| hidden_emotion | 11 | 7% |
| perspective_taking | 10 | 6% |

**Benchmark task → Planner task_type 交叉表**（主要归类）:

| ToMBench 任务 | Planner 判断 |
|---|---|
| False Belief Task | `false_belief` ×13, `general_tom` ×4, `pragmatic_inference` ×3 |
| Faux-pas Recognition | `pragmatic_inference` ×15, `general_tom` ×4 |
| Ambiguous Story | **全部** `pragmatic_inference` ×20 |
| Hinting Task | **全部** `pragmatic_inference` ×20 |
| Persuasion Story | `pragmatic_inference` ×11, `perspective_taking` ×9 |
| Scalar Implicature | `pragmatic_inference` ×18, `general_tom` ×2 |
| Strange Story | `pragmatic_inference` ×17, `hidden_emotion` ×2 |
| Unexpected Outcome | `pragmatic_inference` ×10, `hidden_emotion` ×9 |

**诊断**: Planner 过度把问题归为 `pragmatic_inference`（71%）。未来加 skill/template 时，应当显式引导 planner 区分 scalar / knowledge_gate / faux_pas 等子类。

## 4. Plan 结构统计

- 单 phase plan 占多数（1.54 avg）——Planner 倾向于简洁分解
- 步骤数多在 2-3 步——ReAct 循环深度合理，无过度拆分
- 最大 6 步出现在 Strange Story（复杂情境题）

## 5. 字母偏好

| | A | B | C | D |
|---|---|---|---|---|
| 答案 | 43 | 44 | 39 | 34 |
| 预测 | 50 | 47 | 30 | 33 |

**轻微 A 偏好** (+7)，C 欠预测 (-9)。与历史 baseline 的趋势一致（全局字母分布大体校准），但 C 欠预测需要注意。

## 6. 耗时分析

- 平均 **19.8 秒/样本**（vs 27B baseline 的 0.2 秒/样本）
- 原因：每个样本至少 **1 次 plan + N 次 step reason + 1 次 finalize** ≈ 4-6 次 LLM 调用
- 6 workers 并行下，160 样本 **8.9 分钟**跑完，速率可接受
- 实际生产用途下耗时会是主要成本问题；未来要加 prompt caching

## 7. 关键结论

- ✅ **基础设施正确**: 0 个 parsing/schema/dispatch 错误，Plan JSON 稳定产出，ReAct 循环稳定执行，Memory warm-start 逻辑正确
- ⚠️ **准确率低于纯 CoT baseline 约 8pp**: 这是"光有骨架、没有工具"的固有代价。Plan+Execute 的收益要靠后续接上 skill / memory / RAG 才能兑现
- ✅ **分解天然帮了 False Belief**: 结构化拆分对信念追踪有正向效果
- ❌ **Scalar Implicature 受伤最重**: 量词推理不适合拆分，未来需要特殊路径
- 📋 **Planner 分类过度聚集**: 71% 归为 pragmatic_inference，需要更精细的类型化引导

## 8. 下一步建议

1. **接入 Memory Store**：持久化成功 (task, plan) 对，让 warm-start 生效
2. **接入 Skill Lib**：把 11 个 ToM SKILL 注册成可调用工具，让 executor 能 dispatch
3. **接入 RAG**：社会规范知识库
4. **安装 ToM plugin**：`plugins/tom/install.py` 里的 failure_handlers / memory_index / validators
5. **Planner 分类引导**：在 system prompt 里列出 task_type 候选集，减少 `pragmatic_inference` 过度覆盖
6. **针对 Scalar / Persuasion 的专属 plan template**：这两类任务拆分反而有害，可能需要"single-step"模板

## 9. 产出文件

- `results/harness_notools_results.jsonl` — 每样本一行 JSON，含 plan 结构/预测/正确性
- `results/harness_notools_stats.json` — 按任务聚合统计
- `logs/run_harness_notools.log` — 完整运行日志
