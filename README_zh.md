# tom_harness

> 面向心智理论 (Theory-of-Mind, ToM) 基准测试的轻量级、技能驱动的 Agent Harness。
> 基于 Plan-then-Execute 架构 + ReAct 内循环；通用内核 + 可插拔的 ToM 特化层。

English version: [README.md](README.md)

---

## 这是什么？

`tom_harness` 是一套 **Agent Harness** —— 即围绕大语言模型构建的基础设施，
用来把"文本生成器"变成"特定任务上可靠的推理器"。这里的任务是
**社会认知 / 心智理论**：回答关于角色心理状态、错误信念、隐藏情绪、
语用推理等的选择题。

系统把**战略规划**与**战术执行**解耦：

1. **Planner**（规划 Agent）把问题转成结构化的多阶段计划；
2. **Executor**（执行 Agent）用 ReAct 循环（Reason → Act → Observe）逐步执行；
3. **Tool Layer**（工具层）提供外化认知能力：Memory、Skills、RAG。

架构遵循项目组设定的规范。**内核是领域无关的**（同一骨架也能跑法律或
数学推理）；所有 **ToM 相关知识都以外部插件形式挂载** —— 作为可加载的
skill、validator、failure handler 等接入。

---

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         Harness Layer                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │    Scheduler    │ │  Tool Registry  │ │ Context Manager │    │
│  │   (状态机)      │ │   (工具分发)    │ │  (三级上下文)   │    │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘    │
│           │                   │                   │              │
│  ┌────────▼────────────────────▼───────────────────▼────────┐   │
│  │                     Planner Agent                         │   │
│  │ 1. (强制) 查询 Memory Store 做 warm-start                │   │
│  │ 2. 注入 Memory Playbook 策略（若启用）                   │   │
│  │ 3. 生成结构化 JSON 计划（phase → step）                  │   │
│  └──────────────────────────┬────────────────────────────────┘   │
│                             │                                    │
│  ┌────────────────────▼──────────────────────────────────┐       │
│  │                  Executor Agent                       │       │
│  │        每步 ReAct 循环：Reason → Act → Observe        │       │
│  └──────────────────────────┬────────────────────────────┘       │
│                             │                                    │
│  ┌────────────────────▼──────────────────────────────────┐       │
│  │                     Tool Layer                        │       │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │       │
│  │  │ Memory Store │ │  Skill Lib   │ │  RAG Engine  │   │       │
│  │  └──────────────┘ └──────────────┘ └──────────────┘   │       │
│  └───────────────────────────────────────────────────────┘       │
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
export TOM_MODEL="qwen3-32b"
```

---

## 快速上手

### 跑单题 demo（Sally-Anne）

```bash
python examples/run_demo.py
```

### 跑 ToMBench 基准测试

```bash
# 全部任务，每任务 20 样本
python examples/run_tombench_harness.py --limit 20

# 指定任务
python examples/run_tombench_harness.py --tasks "False Belief Task,Hinting Task Test" --limit 10

# 全部样本（不限制数量）
python examples/run_tombench_harness.py --limit 0

# 显示详细日志
python examples/run_tombench_harness.py --tasks "False Belief Task" --limit 5 -v
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

RAG 在执行过程中提供社会规范/常识知识的动态检索。

### 构建 FAISS 索引（一次性）

RAG 引擎使用 bge-m3 embeddings，覆盖三个知识源（共 57.7 万条）：
- **ATOMIC** —— 常识因果知识（8.1 万条）
- **Social Chemistry** —— 社会规范（34 万条）
- **NormBank** —— 行为准则（15.5 万条）

```bash
# 全量索引构建（CPU 约 30-60 分钟）
python -c "from tom_harness.tools import RAGEngine; r = RAGEngine(); r.build_index()"

# 小样本快速测试（每源 100 条，约几分钟）
python -c "from tom_harness.tools import RAGEngine; r = RAGEngine(); r.build_index(num_samples=100); print(f'Done: {r.size()} docs')"
```

索引缓存在 `tom_harness/tools/tomrag/index/` —— 后续运行从磁盘秒加载。

### 用法

```bash
python examples/run_tombench_harness.py --rag --limit 20
python examples/run_cogtom_harness.py --rag --category "Belief" --limit 10
```

| 参数 | 默认值 | 说明 |
|:---|:---|:---|
| `--rag` | 关闭 | 启用 RAG 检索 |
| `--rag_data_dir` | `tom_harness/tools/tomrag/data` | JSONL 知识语料目录 |
| `--rag_index_dir` | `tom_harness/tools/tomrag/index` | FAISS 索引缓存目录 |
| `--rag_model` | `model/bge-m3` | Embedding 模型路径或 HuggingFace 名称 |

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

每次运行在 `results/<tag>/` 下产出以下文件：

```
results/<tag>/
├── results.jsonl              ← 逐样本记录（id、预测、正确与否、耗时等）
├── stats.json                 ← 按任务/类别 + 总体准确率统计
├── run.log                    ← 详细框架日志（按任务分组，不交叉）
└── llm_cache/
    └── llm_interactions.jsonl ← 原始 LLM 请求/响应缓存
```

所有输出文件在每次运行时**覆盖写入**（无断点续跑机制）。

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
| `--tag` | `notools` | 运行标签（结果保存到 `<out_dir>/<tag>/`） |
| `--memory` | 关闭 | 启用 Memory Playbook |
| `--memory_dir` | `memory_playbook/` | Playbook 目录路径 |
| `--rag` | 关闭 | 启用 RAG 检索 |
| `--rag_data_dir` | `tom_harness/tools/tomrag/data` | RAG 数据目录 |
| `--rag_index_dir` | `tom_harness/tools/tomrag/index` | RAG 索引目录 |
| `--rag_model` | `model/bge-m3` | Embedding 模型 |

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
│   ├── llm.py                           ← LLM 客户端 + 交互缓存
│   ├── context.py                       ← ContextManager（三级上下文 + playbook）
│   ├── registry.py                      ← ToolRegistry（工具分发）
│   ├── hooks.py                         ← 插件钩子系统
│   ├── planner.py                       ← Planner Agent
│   ├── executor.py                      ← Executor Agent（ReAct）
│   ├── scheduler.py                     ← Scheduler（调度 + replan）
│   │
│   ├── tools/
│   │   ├── base.py                      ← Tool 抽象基类
│   │   ├── memory.py                    ← MemoryStore（动态任务-计划对）
│   │   ├── playbook.py                  ← MemoryPlaybook（静态策略加载器）
│   │   ├── skills.py                    ← SkillLib（SKILL.md 加载器）
│   │   ├── rag.py                       ← RAGEngine（FAISS 适配器）
│   │   └── tomrag/                      ← ToMRAG 子包
│   │       ├── rag.py                   ← LangChain + FAISS 核心
│   │       ├── data/                    ← 知识语料（57.7 万条）
│   │       └── index/                   ← FAISS 向量索引（运行时构建）
│   │
│   └── plugins/tom/                     ← ToM 专属插件
│
├── examples/
│   ├── run_demo.py                      ← 单题演示
│   ├── run_tombench_harness.py          ← ToMBench 基准测试 runner
│   └── run_cogtom_harness.py            ← CogToM 基准测试 runner
│
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
