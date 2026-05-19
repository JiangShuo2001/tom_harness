# 对原项目的非强制集成建议

> 本文件**仅是建议**。在当前 checkpoint 中，`tom_harness/` 目录下的任何
> 文件都**没有被修改、移动或删除**。下文每条建议都列出涉及的原项目文件、
> 推荐的最小改动、风险与收益，并明确说明在不接入 optimizer 时如何保持
> 默认行为。

---

## 建议 1：HarnessRuntime 初始化时可选加载 policy_bundle

**涉及文件:**
- `tom_harness/runtime.py`

**建议改动:**
- 在 `HarnessRuntime` dataclass 上新增可选字段 `policy_bundle_path: str | None = None`。
- 在 `build_default_runtime` 上新增同名 keyword 参数，默认 `None`。
- 若 `policy_bundle_path` 为 `None`，保持现有行为完全不变。
- 若非空，加载 `coding.optimizer.policy_bundle.PolicyBundle`，并把它存到
  `self.policy_bundle`（仅在该次 runtime 生命周期内使用）。

**风险:** 低 — 默认参数 None 时旧调用路径完全不受影响。

**收益:** 让 runtime 能消费 optimizer 输出的 policy bundle，而不破坏既有调用。

---

## 建议 2：EnhancedRouter 之后增加 policy-based override

**涉及文件:**
- `tom_harness/routing/base.py`
- `tom_harness/routing/skill_v4_router.py`
- `tom_harness/runtime.py`

**建议改动:**
- 不要修改 `Router` 抽象类的方法签名；保持向后兼容。
- 在 `runtime.py` 的 `answer_one` 中，紧跟在 `router.route(...)` 之后，
  如果 `self.policy_bundle and self.policy_bundle.route_gate_policy`，
  构造 `coding.optimizer.targets.route_gate_target.RouteGatePolicyEngine`
  并调用 `engine.decide(decision, question + story)`。
- 把得到的 `ModuleGateDecision` 缓存到本地变量 `gate`，后续 skill /
  RAG / memory / validator 各分支根据 `gate.use_*` 决定是否启用。

**风险:** 低 — 没有改动 router 内部。

**收益:** 把"哪个 skill 触发 / 是否跳过 / 是否 fallback"这些决策权
从 router 内置启发转移到外部可搜索的 policy，对 reroute / bypass
场景特别有用。

---

## 建议 3：Skill / RAG / Memory gate 读取 gate_policy

**涉及文件:**
- `tom_harness/runtime.py`（位置在 `runtime.py` 80-130 行附近的 skill /
  RAG / playbook 拉取段落）

**建议改动:**
- 把当前的 `if skill_id and hasattr(...)` / `if self.rag_engine is not None`
  / `playbook=self.playbook` 三段，统一外面套一层 `gate.use_skill /
  use_rag / use_memory`：
  ```python
  use_skill = gate.use_skill if gate else bool(skill_id)
  skill_body = ... if use_skill else None
  ```
- 若 `gate.use_rag is False`，跳过 `self.rag_engine.retrieve(...)` 调用。
- 若 `gate.use_memory is False`，把 `playbook=None` 传给 `_build_user_prompt`。

**风险:** 低 — `gate is None` 时退化到旧行为。

**收益:** Direction 1（RouteDecision + Module Gate Optimizer）就此完整接入。

---

## 建议 4：PromptComposer 支持外部 PromptComposePolicy

**涉及文件:**
- `tom_harness/runtime.py`（`_build_user_prompt` 与 `_build_retry_prompt`）

**建议改动:**
- 不要内联替换现有 `_build_user_prompt`，而是新增一条分支：
  ```python
  if self.policy_bundle and self.policy_bundle.prompt_compose_policy:
      from coding.optimizer.targets.prompt_compose_target import (
          PromptComposePolicy,
      )
      from coding.optimizer.interfaces import ModuleOutput
      engine = PromptComposePolicy.from_policy(
          self.policy_bundle.prompt_compose_policy
      )
      module_outputs = [
          ModuleOutput("skill", skill_body or "", confidence=...),
          ModuleOutput("rag", rag_context or "", relevance=...),
          ModuleOutput("memory", self.playbook or ""),
      ]
      result = engine.render(
          task={"story": story, "question": question, "options": options},
          route_decision={"skill_id": skill_id, "confidence": decision.confidence},
          module_outputs=module_outputs,
      )
      system_prompt = result["system_prompt"]
      base_user    = result["user_prompt"]
  else:
      system_prompt = SYSTEM_RAW
      base_user    = _build_user_prompt(...)   # 旧路径完全保留
  ```

**风险:** 中 — 引入 `coding.optimizer` 作为 runtime 的可选依赖；
不接入时仍是零开销。

**收益:** Direction 2（PromptComposer Optimizer）就此完整接入；
runtime 可以读外部 token_budget / priority / module_budgets。

---

## 建议 5：RAG module 支持 query rewrite / source selection / relevance filter

**涉及文件:**
- 原项目里的 RAG engine 实现（仓库内尚未在 v3 中暴露统一文件名；
  建议为它增加一个 `retrieve_with_policy(query, rag_policy: dict)`
  入口，而不是修改现有 `retrieve(...)`）

**建议改动:**
- 新增 `retrieve_with_policy` 方法，签名见上；
- 内部根据 `rag_policy['query_rewrite']` 重写 query，
  根据 `top_k` 限制条数，根据 `require_relevance_score` 过滤。
- 不要触碰原 `retrieve` 接口。

**风险:** 低 — 新增方法，不动旧调用点。

**收益:** Direction 3 中的 RAG 子方向可以无侵入接入。

---

## 建议 6：Memory module 支持 playbook top-k retrieval

**涉及文件:**
- 原项目里 memory / playbook 装载点（runtime 当前传 `playbook: str`）

**建议改动:**
- 把 playbook 由 `str` 升级为可选的 `list[dict]`（带 `memory_id`,
  `positive_triggers`, `negative_triggers`, `known_wins`, `known_losses`
  字段）。
- 新增 `select_playbook_entries(task, route_decision, memory_policy) -> str`
  组合函数，输出仍是 `str`，与 runtime 现有期望兼容。
- 默认行为：若 `memory_policy` 缺失，返回拼接全文 == 旧行为。

**风险:** 低 — 默认输出与旧字符串拼接等价。

**收益:** Direction 3 中 memory 子方向接入；解决 playbook 过触发问题。

---

## 建议 7：Validator 支持 policy-selected validators

**涉及文件:**
- `tom_harness/validators/base.py`
- `tom_harness/validators/scalar_procedural.py`
- 未来新增的 ToM-specific validators

**建议改动:**
- 不修改现有 `Validator` 抽象类。
- 在 `runtime.py` 当前的 validator 循环之前，插入：
  ```python
  if self.policy_bundle and self.policy_bundle.validator_policy:
      from coding.optimizer.targets.validator_todo import ValidatorPolicy
      vpol = ValidatorPolicy.from_policy(
          self.policy_bundle.validator_policy
      )
      names = vpol.select_validators(decision, module_outputs, task=...)
      validators_to_run = [v for v in self.validators if v.name in names]
  else:
      validators_to_run = self.validators
  ```
- 给 `Validator` 子类各自加 `name: str` 类属性，使匹配可行；
  注意这是一行新增，**不修改**现有方法语义。

**风险:** 低 — 默认仍跑 `self.validators`。

**收益:** Direction 4（Validator Optimizer）就此接入，可按场景选择
不同 validator stack。

---

## 建议 8：MemoryWriter / logger 输出 optimizer trace

**涉及文件:**
- 任意一个 runtime 日志收尾位置（如 `runtime.py` 返回 `RuntimeResult`
  之前）

**建议改动:**
- 当 `self.policy_bundle and trace_writer` 时，构造一份与
  `coding/optimizer/trace_schema.py:Trace` 兼容的 dict 并写到
  `optimizer_runs/<run>/traces/<sample_id>.json`。
- 默认 `trace_writer is None` 时不写。

**风险:** 低 — 仅追加磁盘写入路径。

**收益:** Optimizer 的下一轮搜索可直接消费这些 trace 做信用分配。

---

## 接入顺序建议

1. **先做建议 1 + 3**（runtime 接收 policy_bundle、gate 决策接入）。
   这是收益最大、风险最低的一步；做完之后即可使用 Direction 1
   的全部能力。
2. **再做建议 4**（PromptComposer 接入）。两步打底之后整个
   "上下文过载" 的问题就有了系统性抓手。
3. **再做建议 8**（trace 输出），打通经验闭环。
4. **建议 5/6/7** 可与 Direction 3/4 的 engine 实现并行推进，
   不阻塞主路径。

每一步都是**新增分支**而非**替换原路径**，所以任何时候都可以
回退到 `policy_bundle_path=None` 来 100% 复现旧行为。
