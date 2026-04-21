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
│                       Harness Layer                              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │    Scheduler    │ │  Tool Registry  │ │ Context Manager │    │
│  │   (状态机)      │ │   (工具分发)    │ │  (三级上下文)   │    │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘    │
│           │                   │                   │              │
│  ┌────────▼────────────────────▼───────────────────▼────────┐   │
│  │                     Planner Agent                         │   │
│  │  1. (强制) 查询 Memory Store 做 warm-start               │   │
│  │  2. 生成结构化 JSON 计划（phase → step）                 │   │
│  └──────────────────────────┬────────────────────────────────┘   │
│                             │                                    │
│  ┌────────────────────▼──────────────────────────────────┐       │
│  │                   Executor Agent                      │       │
│  │    每步 ReAct 循环：Reason → Act → Observe           │       │
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
                    │  failure_handlers    │
                    │  memory_index        │
                    │  validators          │
                    │  plan_templates/     │
                    └──────────────────────┘
                       (ToM 特化；均不污
                        染内核代码)
```

### 数据流（单个任务端到端）

```
问题 + 选项
    │
    ▼
ContextManager.begin_task()              (第二层状态初始化)
    │
    ▼
Planner.plan()
  ├── MemoryStore.run(query=...)         (强制 warm-start)
  ├── LLM 调用 → JSON 计划
  └── hooks.fire("after_plan")           (插件可修改计划)
    │
    ▼
Scheduler 按 phase × step 驱动循环
    │
    ▼ 对每个 step
Executor.execute_step()
  ├── Reason   (LLM 产出 Reasoning JSON)
  ├── Act      (若 step 含 tool，则 ToolRegistry.dispatch)
  └── Observe  → 结果写入 ExecutionContext
    │
    ▼
Executor.finalize_answer()               (LLM 选出字母答案)
    │
    ▼
Scheduler 将 (task, plan) 写入 MemoryStore   (若成功)
    │
    ▼
FinalResult   (answer + plan + traces + metadata)
```

---

## 安装

需要 Python ≥ 3.10。

```bash
git clone https://github.com/JiangShuo2001/tom_harness.git
cd tom_harness
pip install -r requirements.txt
```

依赖刻意保持最小：**只有 `pydantic>=2` 和 `requests`**。
没有 LangChain / AutoGen / LangGraph。

---

## 配置

Harness 通过一个 OpenAI 兼容格式的 Chat Completions 接口调用 LLM。
设置三个环境变量（或把 `.env.example` 复制成 `.env` 填上）：

```bash
export TOM_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"
export TOM_API_KEY="<你的 key>"
export TOM_MODEL="qwen3-32b"
```

代码中没有任何硬编码 key。若未设置 `TOM_API_KEY`，运行会直接报错退出。

---

## 快速上手

### 跑单题 demo（Sally-Anne 错误信念）

```bash
python examples/run_demo.py
```

预期输出：

```
========== FINAL ==========
answer:  A
success: True
plan.task_type: false_belief
phases: ['analyze_sallys_perspective']
num_steps: 1
elapsed: ~9s
```

### 跑 ToMBench 基准测试（无工具模式）

```bash
# 8 大任务 × 20 样本/任务 = 共 160 样本
python examples/run_tombench_harness.py --per_task 20 --workers 6 --tag notools
```

结果会写入 `results/harness_notools_results.jsonl` 和
`results/harness_notools_stats.json`。

### 作为库调用

```python
from tom_harness import (
    LLMClient, ToolRegistry, ContextManager, Planner, Executor, Scheduler,
)
from tom_harness.hooks import HookRegistry
from tom_harness.tools import MemoryStore

llm = LLMClient(api_base="...", api_key="...", model="qwen3-32b")
registry = ToolRegistry()
ctx = ContextManager()
hooks = HookRegistry()
memory = MemoryStore()

ctx.install_fixed(
    system_identity="A ToM-focused reasoning agent.",
    tool_schema_summary=registry.schema_summary(),
)

scheduler = Scheduler(
    planner=Planner(llm=llm, registry=registry, context=ctx, hooks=hooks, memory=memory),
    executor=Executor(llm=llm, registry=registry, context=ctx, hooks=hooks),
    registry=registry, context=ctx, hooks=hooks, memory=memory,
)

result = scheduler.run(
    task_id="q1",
    question="故事 + 问题……",
    options={"A": "...", "B": "...", "C": "...", "D": "..."},
)
print(result.answer, result.plan.task_type)
```

---

## 项目结构

```
tom_harness/
├── README.md                            ← 英文版
├── README_zh.md                         ← 当前文件
├── requirements.txt
├── .env.example
│
├── tom_harness/                          ← 核心包
│   ├── __init__.py
│   ├── schemas.py                        ← 所有 Pydantic 数据模型
│   ├── llm.py                            ← LLM 客户端
│   ├── context.py                        ← ContextManager (三级上下文)
│   ├── registry.py                       ← ToolRegistry (工具分发)
│   ├── hooks.py                          ← 插件钩子系统
│   ├── planner.py                        ← Planner Agent
│   ├── executor.py                       ← Executor Agent (ReAct)
│   ├── scheduler.py                      ← Scheduler (调度 + replan)
│   │
│   ├── tools/
│   │   ├── base.py                       ← Tool 抽象基类
│   │   ├── memory.py                     ← MemoryStore (任务-计划对)
│   │   ├── skills.py                     ← SkillLib (SKILL.md 加载器)
│   │   └── rag.py                        ← RAGEngine (语料检索)
│   │
│   └── plugins/
│       └── tom/                          ← ToM 专属插件 (可插拔)
│           ├── install.py                ← 一键挂载
│           ├── failure_handlers.py       ← 12 种 ToM 失败类型 → skill 映射
│           ├── memory_index.py           ← ToM 元数据富化
│           ├── validators.py             ← 一致性校验
│           └── plan_templates/           ← 计划骨架 SKILL.md
│               ├── false_belief.md
│               ├── knowledge_gate.md
│               └── aware_of_reader.md
│
├── examples/
│   ├── run_demo.py                       ← 单题演示
│   └── run_tombench_harness.py           ← 基准测试 runner
│
└── tests/
```

---

## 设计原则（协作者请务必对齐）

1. **内核是领域无关的**。`tom_harness/` 包（除 `plugins/tom/` 外）
   不应出现"信念""情绪""失言"这类字眼。若你想往内核加 ToM 相关逻辑，
   请改成**加一个 hook 点 + 把逻辑写进 plugin**。

2. **Schema 字段名不动**。`schemas.py` 中的字段（`plan_id`、`phases`、
   `steps`、`tool_type` 等）严格遵循项目原始规范，不得重命名。需要加
   领域特化字段时，用各模型上统一提供的 `metadata: dict` 插槽
   （`Plan`、`Phase`、`Step`、`Memory` 都有）。

3. **每次规划阶段都必须查询 Memory Store**。这是规范里的强制要求，
   哪怕 Memory 是冷启动的空库，也要走这次查询。

4. **插件只通过 hook 挂载，不得直接改内核**。当前支持的 hook 事件：
   `before_plan`、`after_plan`、`before_step`、`after_step`、
   `on_step_failure`、`before_finalize`、`enrich_memory`。

5. **不引入大型框架**。故意不依赖 LangChain、AutoGen、LangGraph、CrewAI
   等。保证系统对科研级使用是可检视、可调试的。

---

## 当前状态

| | |
|---|---|
| 版本 | 0.1.0 |
| 核心代码量 | ~2.4K 行 Python |
| 无工具模式基线 | ToMBench 160 样本，**70.6%** (qwen3-32b) |
| 已知限制 | Memory/Skill/RAG 尚未默认注册到 ToolRegistry；Planner 把过多题判为 `pragmatic_inference` |

完整 v0.1 基准测试报告见 `REPORT_HARNESS_NOTOOLS.md`。

---

## 如何参与贡献

### 工作流（branch + PR）

**禁止**直接推 `main`。`main` 已开启保护，所有变更必须通过 Pull Request
且至少 1 个 approving review 后才能合并。

```bash
# 1. 同步本地 main
git switch main
git pull

# 2. 开一个新分支（名字要能说明干什么）
git switch -c feature/wire-memory-tool

# 3. 改代码，commit 粒度小一点，message 写清楚
git add <文件>
git commit -m "Wire MemoryStore into ToolRegistry"

# 4. 把 feature 分支推到 GitHub
git push -u origin feature/wire-memory-tool

# 5. 在 GitHub 网页上针对 main 开 Pull Request
# 6. 根据 review 意见继续在同一分支 commit
# 7. 审过后在 GitHub UI 点 squash-merge 或 rebase-merge
```

分支命名约定：
- `feature/<短描述>` — 新功能
- `fix/<短描述>`     — bug 修复
- `exp/<短描述>`     — 研究实验（可能永不合并）
- `docs/<短描述>`    — 纯文档改动

### 如何加一个新工具

1. 在 `tom_harness/tools/` 下新建文件，继承
   `tom_harness.tools.base.Tool`。
2. 实现 `tool_type`、`tool_name`、`description`、`validate_params`、
   `run` 五个方法/属性。
3. 在 `tools/__init__.py` 里导出。
4. 在入口脚本里 `ToolRegistry.register(your_tool)` 即可。

### 如何加一个新 skill

在 `plugins/tom/plan_templates/`（或你自己的 plugin 目录）下放一个
`SKILL.md` 文件，使用以下 frontmatter：

```markdown
---
name: my_skill
skill_id: S12_my_skill
description: 一行描述本 skill 的作用。
triggers:
  - "触发本 skill 的特征短语"
---

## Workflow
1. ...
2. ...

## Output shape
...
```

然后 `SkillLib(skills_dir=Path(".../plan_templates"))` 自动加载，
或运行时 `skill_lib.load_dir(path)`。

若是过程性 skill（确定性 Python 而非 LLM 引导），加载后调用
`skill_lib.register_handler(skill_id, handler_fn, ...)`。

### 如何注册插件 hook

插件通过向命名事件挂回调来接入：

```python
from tom_harness.hooks import HookRegistry, RecoveryDirective

def my_failure_handler(step, trace, context):
    # 检查后返回 RecoveryDirective 或 None
    return RecoveryDirective(action="replan", failure_type="my_ftype")

hooks = HookRegistry()
hooks.register("on_step_failure", my_failure_handler)
```

当前内核会触发的事件（最新版以 `hooks.py` 为准）：
- `before_plan(question=..., task_type=...)`
- `after_plan(plan=...)` → 可返回修改后的 Plan
- `before_step(step=..., context=...)`
- `after_step(step=..., trace=..., context=...)`
- `on_step_failure(step=..., trace=..., context=...)` → RecoveryDirective
- `before_finalize(accumulated_results=...)`
- `enrich_memory(memory=...)` → 可返回修改后的 Memory

---

## 路线图

- [ ] **v0.2** —— 把 `MemoryStore` + `SkillLib` 默认注册进 `ToolRegistry`；
      在 `run_tombench_harness.py` 里安装 ToM plugin。
- [ ] **v0.3** —— 让 `RAGEngine` 带上社会规范知识语料
      （失言模式、语用规约）。
- [ ] **v0.4** —— 按 task_type 的专属 plan template（Scalar / Persuasion
      有自己的形状），替代当前 `pragmatic_inference` 的过度分类。
- [ ] **v0.5** —— 同一 harness 切换 adapter 跑 CogToM 和 ToMATO。
- [ ] **v1.0** —— Meta-Harness 风格的外循环，在 benchmark 分上自动优化
      harness 本身。

---

## 许可

研究代码 —— 见 `LICENSE`（待加）。默认：团队商定开源协议之前保留所有权利。

---

## 参考文献

架构借鉴自：

- [XSkill](https://arxiv.org/abs/2603.12056) —— 经验+技能双流持续学习。
- [Externalization in LLM Agents](https://arxiv.org/abs/2604.08224) —— Harness 工程综述。
- [Natural-Language Agent Harnesses](https://arxiv.org/abs/2603.25723) —— Harness 作为可编辑的自然语言 artifact。

完整 harness 领域综述（内部文档）：
`../survey_1/symbolictom_repro/REPORT_HARNESS_SURVEY.md`
