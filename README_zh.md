# tom_harness

> 面向心智理论 (Theory-of-Mind, ToM) 基准测试的轻量级、技能驱动的 Agent Harness。
> 单次推理运行时 (v2) 为默认模式；Plan-then-Execute 架构可用于多步研究场景。

English version: [README.md](README.md)

---

## 这是什么？

`tom_harness` 是一套 **Agent Harness** —— 即围绕大语言模型构建的基础设施，用来把"文本生成器"变成"特定任务上可靠的推理器"。这里的任务是**社会认知 / 心智理论**：回答关于角色心理状态、错误信念、隐藏情绪、语用推理等的选择题。

系统支持三种执行模式：

1. **单次推理运行时 (v2, 默认)**：路由 → 组装 prompt（skill + RAG + playbook）→ 单次 LLM 调用 → 验证器检查 → 返回答案。这是基准评测的标准路径。
2. **Full harness**（Plan → Execute → Finalize）：Planner 生成多阶段计划，Executor 通过 ReAct 循环逐步执行，Finalizer 综合得出答案。
3. **Thin harness**（技能前置单次 LLM 调用）：选择性路由器挑选最佳技能提示词，拼接在问题前面，一次 LLM 调用完成。

### 工具层 (v2)

单次推理运行时提供三个可插拔模块：

- **Skills v4** — 22 个精选 SKILL.md 推理提示 + LLM 路由器 (SkillV4Router)
- **RAG v2** — 基于类别的 FAISS 检索，使用改写后的聚类数据（1500 条精简文档，来源：ATOMIC、Social Chemistry、NormBank）
- **Memory Playbook** — 静态策略注入（ACE 精炼的 playbook）

---

## 架构（v2 单次推理运行时）

```
┌─────────────────────────────────────────────────────────────────┐
│                    HarnessRuntime (single-shot)                  │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ SkillV4Router│    │  RAGv2Engine │    │   Playbook   │      │
│  │ (22 skills,  │    │ (FAISS+bge,  │    │  (static txt │      │
│  │  LLM-routed) │    │  1500 docs)  │    │   injection) │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │               │
│  ┌──────▼───────────────────▼───────────────────▼────────────┐  │
│  │              Prompt Assembly                               │  │
│  │  [Skill body] + [RAG context] + [Playbook] +              │  │
│  │  [Story] + [Question] + [Options] + [Format instruction]  │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │                    LLM Call (single-shot)                  │  │
│  │  System: "Read story, give reason, then JSON answer"      │  │
│  │  → Returns: reasoning + {"answer": "A"|"B"|"C"|"D"}      │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │              Validators (optional retry)                   │  │
│  │  ScalarProceduralValidator: arithmetic check for           │  │
│  │  Scalar Implicature tasks → suggest/retry if invalid      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 安装

需要 Python ≥ 3.10。

```bash
git clone <repo-url>
cd tom_harness
pip install -r requirements.txt
```

**额外依赖（RAG 模式）**：

```bash
pip install langchain-core langchain-community faiss-cpu sentence-transformers
```

依赖刻意保持最小：内核只需 **`pydantic>=2` 和 `requests`**。

---

## 配置

Harness 通过一个 OpenAI 兼容格式的 Chat Completions 接口调用 LLM。
设置三个环境变量（或把 `.env.example` 复制成 `.env` 填上）：

```bash
export TOM_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"
export TOM_API_KEY="<你的 key>"
export TOM_MODEL="qwen3.5-27b"
```

---

## 快速上手

### 跑单题 demo（Sally-Anne）

```bash
python examples/run_demo.py
```

### 跑 ToMBench 基准测试（单次推理 v2 运行时 — 默认）

```bash
# 全部任务，每任务 20 样本（基线，不启用任何模块）
python examples/run_tombench_harness.py --limit 20

# 启用技能路由（22 个 LLM 路由技能）
python examples/run_tombench_harness.py --skill --limit 20

# 启用 RAG v2 检索
python examples/run_tombench_harness.py --rag --limit 20

# 启用 Memory Playbook
python examples/run_tombench_harness.py --memory --limit 20

# 全部模块组合
python examples/run_tombench_harness.py --skill --rag --memory --limit 20

# 指定任务
python examples/run_tombench_harness.py --tasks "False Belief Task,Hinting Task Test" --limit 10

# 全部样本（不限制数量）
python examples/run_tombench_harness.py --limit 0

# 显示详细日志
python examples/run_tombench_harness.py --tasks "False Belief Task" --limit 5 -v
```

### 跑消融实验（全部 7 种模块组合）

```bash
# 全量数据（全部任务，全部样本）
bash examples/run_ablation.sh

# 快速测试（每任务 2 样本）
bash examples/run_ablation.sh --limit 2

# 指定任务
bash examples/run_ablation.sh --tasks "False Belief Task,Persuasion Story Task"
```

消融脚本运行 7 种组合：baseline、skill、rag、memory、skill+rag、skill+memory、skill+rag+memory。已完成的运行会自动跳过。

### 重跑失败样本 / 恢复中断的运行

```bash
# 仅重跑预测为空的样本
python examples/rerun_failed.py results/ablation_0507/2_skill --skill

# 恢复中断的运行（补全缺失样本）
python examples/rerun_failed.py results/ablation_0507/7_rag_memory --rag --memory --resume
```

### 计算详细统计（8 类任务 + 6 个能力维度）

```bash
# 对父目录下所有配置计算
python examples/compute_detailed_stats.py results/ablation_0507

# 单个配置
python examples/compute_detailed_stats.py results/ablation_0507/2_skill
```

### 跑 ToMBench 基准测试 (thin harness — selective skill routing)

```bash
# 使用 regex-based 路由选择器 + 每个问题单一 LLM 调用
python examples/run_selective_harness.py --limit 20

# 特定任务
python examples/run_selective_harness.py --tasks "Scalar Implicature Test" --limit 0
```

可用的 ToMBench 任务（`--tasks` 参数需使用精确名称）：

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

### 跑 CogToM 基准测试

```bash
# 全部类别，每类别 20 样本
python examples/run_cogtom_harness.py --limit 20

# 指定类别
python examples/run_cogtom_harness.py --category "Belief" --limit 10

# 多个类别
python examples/run_cogtom_harness.py --category "Belief,Emotion,Desire" --limit 5
```

可用的 CogToM 类别（`--category` 参数需使用精确名称）：

```
Belief    Comprehensive    Desire    Emotion
Intention Knowledge        Non-literal Percept
```

---

## Memory Playbook（`--memory`）

Memory Playbook 会将预构建的 ACE 框架策略注入到 Planner 提示词中。这些策略经过多轮迭代精炼，包含：

- **策略与洞察** —— 经过验证的 ToM 任务推理模式
- **常见错误规避** —— 需要防范的错误模式
- **问题求解启发式** —— 通用决策规则

### 配置

将 playbook 文件（`.txt` 或 `.md`）放在 `memory_playbook/` 目录下：

```
memory_playbook/
└── epoch_1_step_600_playbook.txt    ← ACE 精炼的策略
```

### 用法

```bash
# ToMBench + Memory Playbook
python examples/run_tombench_harness.py --memory --limit 20

# CogToM + Memory Playbook
python examples/run_cogtom_harness.py --memory --category "Belief" --limit 10

# 自定义 playbook 目录
python examples/run_tombench_harness.py --memory --memory_dir /path/to/my_playbook/
```

Playbook 内容**仅注入到 Planner** 提示词中（不进入 Executor 的 ReAct 循环）。Planner 的系统提示词会指导 LLM 主动参考 playbook 中的策略并避免文档中记录的常见错误。

| 参数 | 默认值 | 说明 |
|:---|:---|:---|
| `--memory` | 关闭 | 启用 Memory Playbook 注入到 Planner |
| `--memory_dir` | `memory_playbook/` | Playbook 文件目录路径 |

---

## RAG 检索（`--rag`）

RAG v2 在单次推理时提供基于类别的社会规范/常识知识检索。

### 数据与索引

RAG v2 使用 bge-m3 embeddings，覆盖三个原始知识源经过聚类改写后的 1500 条精简文档：
- **ATOMIC** —— 常识因果知识
- **Social Chemistry** —— 社会规范
- **NormBank** —— 行为准则

数据放在 `tom_harness/tools/rag_v2_data/`，FAISS 索引缓存在 `tom_harness/tools/rag_v2_index/` —— 后续运行从磁盘秒加载。

### 用法

```bash
python examples/run_tombench_harness.py --rag --limit 20
python examples/run_cogtom_harness.py --rag --category "Belief" --limit 10
```

| 参数 | 默认值 | 说明 |
|:---|:---|:---|
| `--rag` | 关闭 | 启用 RAG v2 检索 |
| `--rag_data_dir` | `tom_harness/tools/rag_v2_data` | RAG 数据目录 |
| `--rag_index_dir` | `tom_harness/tools/rag_v2_index` | FAISS 索引缓存目录 |
| `--rag_model` | `model/bge-m3` | Embedding 模型路径或 HuggingFace 名称 |
| `--rag_rewritten` | 开启 | 使用改写后的聚类数据 |

### 同时启用 Memory Playbook + RAG

两者可以同时开启：

```bash
python examples/run_tombench_harness.py --memory --rag --limit 20 --tag memory_rag
```

---

## LLM 交互缓存

每次 LLM 调用（系统提示词、用户提示词、响应、耗时）都会记录到 JSONL 文件，用于调试和分析。缓存在**每个任务开始时重置**。

缓存路径：`results/<tag>/llm_cache/llm_interactions.jsonl`

每行包含：
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

## 输出结构

每次运行在 `results/<out_dir>/` 下产出以下文件：

```
results/<out_dir>/
├── results.jsonl              ← 逐样本记录
├── stats.json                 ← 按任务/类别 + 总体准确率统计
├── stats_detailed.json        ← （可选）8 类任务 + 6 能力维度细分
├── run.log                    ← 详细框架日志
└── llm_cache/
    └── llm_interactions.jsonl ← 原始 LLM 请求/响应缓存
```

### results.jsonl 格式

```json
{
  "id": "False Belief Task_0001",
  "task": "False Belief Task",
  "answer": "B",
  "predicted": "B",
  "correct": true,
  "skill_id": "skill3",
  "n_llm_calls": 1,
  "elapsed_sec": 5.12,
  "error": null,
  "thinking": "故事中 Sally 把球放在篮子里然后离开，Anne 把球移走了。Sally 仍然相信球在篮子里。"
}
```

### 准确率计算

- `predicted=""` （解析失败）或 `error != null` 的记录计为**错误**
- 准确率 = `correct / (total - errors)` —— 错误从分母中排除
- 这避免了解析失败人为拉低准确率

---

## CLI 参考

### `run_tombench_harness.py`

| 参数 | 默认值 | 说明 |
|:---|:---|:---|
| `--data_dir` | `benchmark/ToMBench/` | ToMBench JSONL 目录 |
| `--tasks` | 全部任务 | 逗号分隔的任务名 |
| `--limit` | 20 | 每任务最大样本数（0 = 不限制） |
| `--offset` | 0 | 每任务跳过前 N 个样本 |
| `--workers` | 8 | 并行 worker 数 |
| `--verbose` / `-v` | 关闭 | 在控制台显示详细框架日志 |
| `--out_dir` | `results` | 输出根目录 |
| `--skill` | 关闭 | 启用 LLM 路由技能注入（22 个 v4 技能） |
| `--rag` | 关闭 | 启用 RAG v2 检索 |
| `--rag_data_dir` | `tom_harness/tools/rag_v2_data` | RAG 数据目录 |
| `--rag_index_dir` | `tom_harness/tools/rag_v2_index` | RAG 索引目录 |
| `--rag_model` | `model/bge-m3` | Embedding 模型 |
| `--rag_rewritten` | 开启 | 使用改写后的聚类数据（1500 条） |
| `--memory` | 关闭 | 启用 Memory Playbook |
| `--memory_dir` | `memory_playbook/` | Playbook 目录路径 |

### `run_cogtom_harness.py`

与上面相同的参数，以下为不同之处：

| 参数 | 默认值 | 说明 |
|:---|:---|:---|
| `--data_dir` | `benchmark/cogtom/` | CogToM 数据目录 |
| `--category` | 全部类别 | 逗号分隔的类别名（替代 `--tasks`） |
| `--limit` | 20 | 每类别最大样本数 |
| `--offset` | 0 | 每类别跳过前 N 个样本 |
| `--tag` | `cogtom` | 默认运行标签 |

---

## 项目结构

```
tom_harness/
├── README.md
├── README_zh.md
├── requirements.txt
├── .env.example
│
├── benchmark/                           ← 数据加载器 & 数据集
│   ├── load_tombench.py                 ← ToMBench JSONL 加载器
│   ├── load_cogtom.py                   ← CogToM JSONL 加载器
│   ├── ToMBench/                        ← ToMBench 数据（20 个任务 .jsonl 文件）
│   └── cogtom/                          ← CogToM 数据
│       ├── CogToM-en.jsonl              ← 英文版（8513 样本）
│       └── CogToM-zh.jsonl              ← 中文版
│
├── memory_playbook/                     ← 静态 playbook 文件
│   └── epoch_1_step_600_playbook.txt    ← ACE 精炼的策略
│
├── tom_harness/                         ← 核心包
│   ├── schemas.py                       ← Pydantic 数据模型
│   ├── llm.py                           ← LLM 客户端 + 交互缓存 + JSON 解析
│   ├── runtime.py                       ← HarnessRuntime（v2 单次推理路径）
│   ├── context.py                       ← ContextManager（三级上下文 + playbook 注入）
│   ├── registry.py                      ← ToolRegistry（二维分发：tool_type + tool_name）
│   ├── hooks.py                         ← 插件钩子系统（7 个扩展点）
│   ├── planner.py                       ← Planner Agent（v1 多步路径，仍可用）
│   ├── executor.py                      ← Executor Agent（ReAct 循环）
│   ├── scheduler.py                     ← Scheduler（v1 编排器）
│   │
│   ├── routing/                         ← v2 路由器
│   │   ├── base.py                      ← Router ABC + RouteDecision
│   │   ├── skill_v4_router.py           ← LLM 路由器（22 个 SKILL.md）
│   │   └── oracle_picks.py              ← 静态查表路由（用于消融对比）
│   │
│   ├── validators/                      ← v2 程序化验证器
│   │   ├── base.py                      ← Validator ABC + ValidationResult
│   │   └── scalar_procedural.py         ← Scalar Implicature 算术校验
│   │
│   ├── tools/
│   │   ├── base.py                      ← Tool 抽象基类 + ToolResult 封装
│   │   ├── memory.py                    ← MemoryStore（向量索引的任务-计划对，v1）
│   │   ├── playbook.py                  ← MemoryPlaybook（静态策略加载器）
│   │   ├── skills_v4/                   ← 22 个 v4 SKILL.md（按目录组织）
│   │   ├── rag_v2/                      ← RAG v2 引擎（类别感知的 FAISS 检索）
│   │   ├── rag_v2_data/                 ← 1500 条改写后的聚类知识
│   │   └── rag_v2_index/                ← FAISS 索引缓存
│   │
│   └── plugins/                         ← v1 插件系统（仍可用）
│       └── tom/                         ← ToM 专属插件（hooks + skills）
│
├── examples/
│   ├── run_demo.py                      ← 单题演示（Sally-Anne）
│   ├── run_tombench_harness.py          ← ToMBench v2 运行时 runner（默认）
│   ├── run_ablation.sh                  ← 消融实验脚本（7 种组合）
│   ├── rerun_failed.py                  ← 重跑失败样本 / 恢复中断运行
│   ├── compute_detailed_stats.py        ← 8 任务 + 6 能力维度细分统计
│   ├── run_selective_harness.py         ← thin harness（选择性路由）
│   ├── run_cogtom_harness.py            ← CogToM 基准测试 runner
│   └── ...                              ← 其他研究脚本
│
├── docs/                                ← 分析文档
└── results/                             ← 输出（gitignored）
```

---

## 设计原则

1. **内核是领域无关的。** `tom_harness/`（`plugins/tom/` 除外）不出现信念、情绪、失言等字眼。
2. **Schema 字段稳定。** `schemas.py` 中的字段遵循项目原始规范。扩展请用 `metadata: dict`。
3. **每次规划都必须查询 Memory Store**（强制 warm-start，即使为空）。
4. **插件通过 hook 挂载，不直接改内核。**
5. **不引入大型框架。** 内核不依赖 LangChain/AutoGen/LangGraph。

---

## 许可

研究代码 —— 见 `LICENSE`（待加）。

---

## 参考文献

- [XSkill](https://arxiv.org/abs/2603.12056) —— 经验+技能双流持续学习。
- [Externalization in LLM Agents](https://arxiv.org/abs/2604.08224) —— Harness 工程综述。
- [Natural-Language Agent Harnesses](https://arxiv.org/abs/2603.25723) —— Harness 作为自然语言 artifact。
