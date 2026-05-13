# Critical Bug Audit & Unified Fix Report

> **日期**: 2026-04-27
> **触发**: 合作者反映"我们最早版本 finalizer 根本不接受更早阶段的输入"
> **结论**: 反映**部分确认**——见 §1 物理诊断；统一修复已应用

---

## 1. 验证合作者反映的 bug（B1）

**真相**: Initial commit (`229881b`) 的 `finalize_answer` 代码：

```python
user = (
    f"## Question\n{question}\n\n"
    f"## Options\n..." + "\n\n"
    f"## Accumulated Step Results\n"
    + "\n".join(f"- {k}: {repr(v)[:400]}" for k, v in accumulated.items())   # ← 致命
)
```

`accumulated_results` **确实**被塞进 prompt — 字面意义上"接受"了上游输入。但是：

- `repr(v)[:400]` 把每个 value 截断到 **400 字符**，且用 Python `repr()` 格式（带引号、转义字符）。一个典型 StoryModel 输出 2-5 KB，被切成 `"{'sentences': ['Sally puts marble in basket', 'Sally l` 这种结构残缺的字符串 — 对 LLM 完全是乱码
- `FINALIZE_SYSTEM` 的 prompt 一句话："Pick the single best answer letter. Reply with ONLY a JSON object." — **不强制 LLM 使用 accumulated**
- Reasoning 对象**完全未进入 prompt**（仅入 ExecutionTrace），合作者抓住的现象之一

**判定**: 合作者的批评在事实上**部分错位**（accumulated 字面被传），在精神上**完全正确**（实际效果约等于不接受）。**这个 bug 从 v0.1 一直存活到本次修复前**。

---

## 2. 全分支 bug 存活矩阵

| Bug | main | v0.2 | v0.3 | external-skill-packs | experiment (Jingya) |
|---|:-:|:-:|:-:|:-:|:-:|
| B1 finalize `repr[:400]` 截断 | ❌ | ❌ | ❌ | ❌→✅ | ❌→✅ |
| B2 Reasoning orphaned | ❌ | ❌ | ✅ | ✅ | ✅* |
| B3 MemoryStore 无锁 | ❌ | ❌ | ✅ | ✅ | ❌ |
| B4 finalize max_tokens=256 | ❌ | ❌ | ❌ | ❌→✅ | ❌→✅ |
| B6 depends_on 不强制 | ❌ | ❌ | ❌ | ❌→✅ | ❌ |
| B7 vote scan recurse Memory | n/a | n/a | ❌ | ❌→✅ | n/a |
| B8 story 注入靠 runner | ❌ | ❌ | ✅ | ✅ | ❌ |
| B9 tool_name 不校验 | ❌ | ❌ | ❌ | ❌→✅ | ❌ |
| B10 memory 收"运气对" | n/a | n/a | ❌ | ❌ | ❌ |

\* Jingya 的 `ab5dde7` 用不同思路修了 reasoning（直接传给 finalize），与我们 v0.3 的 "持久化到 accumulated" 思路并行不冲突。

---

## 3. 统一修复 (commit `e6f8600`)

**4 个文件，89 行 insertion，33 行 deletion**:

- `tom_harness/executor.py`:
  - 新增 `_render_accumulated()` helper：JSON-aware 1500 字符上限，超过后明示 `[...truncated]`
  - 替换 finalize 渲染 `repr(v)[:400]` → `_render_accumulated(accumulated)` (B1)
  - finalize `max_tokens=256` → `1024` (B4)
  - `_collect_skill_votes` 改为只扫顶层 dict，不递归 Memory plans (B7)
  - `FINALIZE_SYSTEM` prompt 加 CRITICAL 段强约束 LLM 必须用 accumulated
- `tom_harness/scheduler.py`: 加 `completed_step_ids` set，对未完成依赖输出 warning (B6)
- `tom_harness/planner.py`: plan 装配时校验 `tool_name in registry`，失败转纯推理 step (B9)

**已应用于的分支** (push 到 GitHub):
- ✅ `feature/external-skill-packs` (我们最新主线)
- ✅ `experiment/plan-a-skill-rag-inject` (Jingya 分支，仅 executor.py portion)
- 🚧 `main` (本地已 commit，远端因 branch protection 需要 PR 才能 merge)
- 待办: `feature/memory-and-skills-v0.2`, `feature/v0.3-state-backed-skills` (历史分支，低优先级)

---

## 4. 验证: post-fix benchmark on claude-haiku-4-5

160 样本 baseline (我们自己 11 skill, 不含外部 pack):

| Task | Acc |
|---|:-:|
| Hinting Task Test | 95.0% |
| False Belief Task | 90.0% |
| Unexpected Outcome Test | 80.0% |
| Strange Story Task | 75.0% |
| Faux-pas Recognition Test | 60.0% |
| Ambiguous Story Task | 50.0% |
| Scalar Implicature Test | 50.0% |
| Persuasion Story Task | 45.0% |
| **Overall** | **68.1%** |

**B6 / B9 修复在 log 中确认 firing**：
- `WARNING ... Planner emitted unknown tool (skill, S_evidence_scorer) — converting step to pure-reasoning` (B9)
- `WARNING ... step ... declares depends_on=['1'] but ['1'] are not yet completed — executing anyway` (B6)

**已知边缘问题**: 少量 sample 仍因 `Tool not registered` abort —— B9 在 plan 装配捕获了大多数 case，但有些路径（疑似 select_skills 后 Planner 重写 tool_name）漏过。**记录待跟进，不阻塞当前修复主线**。

---

## 5. 待办

- [ ] 在 `feature/memory-and-skills-v0.2`、`feature/v0.3-state-backed-skills` 上 backport 同款 patch（低优先级）
- [ ] 给 `main` 分支开 PR 走 review-merge 流程
- [ ] 跟进 B9 边缘漏 case
- [ ] 修复 B5（`record_step_result` 同 key 静默覆盖）和 B10（"运气对"也写进 memory）— 中等优先级
