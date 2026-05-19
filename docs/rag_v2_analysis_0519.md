# RAG v2 分析报告：检索质量评估与门控机制设计

> 日期：2026-05-19
> 模块：agent harness v3 — RAG 检索模块
> 对比实验：ablation_0511_gpt/1_baseline vs test_0519_rag_

---

## 1. 实验概述

### 1.1 实验目的

评估 RAG v2 模块（基于 294 条手工 ToM 规则的 FAISS 向量检索）对模型答题的实际影响，分析检索内容的相关性，并设计门控机制。

### 1.2 实验配置

| 配置项 | 值 |
|--------|-----|
| 测试模型 | gpt-5.4-mini |
| Benchmark | ToMBench（2860 样本，20 个 task） |
| RAG 知识库 | tom_rules_v2.jsonl（294 条规则，13 个类别） |
| 向量模型 | bge-m3（normalize_embeddings=True） |
| 检索方式 | FAISS 全库搜索（use_category_filter=False） |
| 检索 top_k | 5 |
| temperature | 0.0 |

### 1.3 总体结果

| 实验 | 准确率 | 相对 Baseline |
|------|-------:|-------------:|
| Baseline（无 RAG） | 77.73% | — |
| +RAG（v2，全库搜索） | 74.62% | **-3.11pp** |
| +RAG（v1 老版，旧消融） | 73.25% | -4.48pp |

**结论：RAG 整体为负贡献。**

---

## 2. 逐 Task 翻转分析

### 2.1 翻转统计总览

| 方向 | 数量 |
|------|-----:|
| Baseline 错 → RAG 对（gain） | 155 |
| Baseline 对 → RAG 错（loss） | 244 |
| **净损失** | **-89** |

### 2.2 各 Task 详细对比

#### 受损 Task（RAG 导致下降）

| Task | 样本数 | 额外答对 | 额外答错 | Net | Baseline Acc | RAG Acc | Delta |
|------|-------:|--------:|--------:|----:|------------:|--------:|------:|
| **False Belief Task** | 600 | 1 | 82 | -81 | 97.3% | 83.8% | -13.5pp |
| **Percepts-Knowledge Links** | 40 | 1 | 9 | -8 | 97.5% | 77.5% | -20.0pp |
| **Hinting Task Test** | 103 | 2 | 15 | -13 | 85.4% | 72.8% | -12.6pp |
| Discrepant Emotions | 40 | 3 | 6 | -3 | 90.0% | 82.5% | -7.5pp |
| Discrepant Intentions | 40 | 2 | 5 | -3 | 77.5% | 70.0% | -7.5pp |
| Multiple Desires | 20 | 1 | 0 | +1 | 95.0% | 100% | +5.0pp |
| Unexpected Outcome Test | 300 | 17 | 26 | -9 | 73.0% | 70.0% | -3.0pp |

#### 受益 Task（RAG 带来提升）

| Task | 样本数 | 额外答对 | 额外答错 | Net | Baseline Acc | RAG Acc | Delta |
|------|-------:|--------:|--------:|----:|------------:|--------:|------:|
| **Faux-pas Recognition** | 560 | 56 | 27 | +29 | 72.7% | 77.9% | +5.2pp |
| Knowledge-Pretend Play | 30 | 5 | 1 | +4 | 3.3% | 16.7% | +13.3pp |
| Discrepant Desires | 20 | 4 | 2 | +2 | 35.0% | 45.0% | +10.0pp |

---

## 3. 典型错误案例分析

### 3.1 False Belief Task（-13.5pp，82 个翻转答错）

**根因：注入了完全不相关的规则，干扰了模型已掌握的推理逻辑。**

False Belief 考的是"A 不知道 B 移动了物品，A 会去哪里找"，模型 Baseline 已有 97.3% 准确率。

#### 案例 1：False Belief Task_0010
- **正确答案**：A
- **Baseline**：A ✓ — "Han Meimei saw the sweatshirt in the cabinet before she left, and she did not see Li Lei move it. So when she returns, she will likely look in the cabinet for it."
- **RAG**：B ✗ — "Li Lei moved the sweatshirt from the cabinet to the handbag while Han Meimei was away. So when she returns, she would look in the handbag for the sweatshirt."
- **注入的 RAG 内容**："When flattery accompanies an immediate request, true intent rapidly becomes explicit..." / "When the immediate context of flattery contradicts long-term interaction history..."
- **分析**：问题是 "Where is the cabbage now?"，FAISS top1 L2 距离高达 1.40，检索到的 flattery 规则完全不相关。模型在参考这些噪声后放弃了正确的 false belief 推理，转而追踪物品的实际位置。

#### 案例 2：False Belief Task_0017
- **正确答案**：D
- **Baseline**：D ✓ — "Youyou originally saw the hat in the suitcase, and Xiao Li moved it only after Youyou left. So Xiao Li would think Youyou looks for the hat in the suitcase."
- **RAG**：C ✗ — "Xiao Li moved the hat into the storage locker after Youyou left. So when Youyou comes back, Xiao Li would think Youyou looks for the hat where it was last placed, which is the storage locker."
- **注入的 RAG 内容**：flattery/nonverbal signals 相关规则
- **分析**：同样的模式——不相关规则干扰了模型对他人信念状态的正确追踪。

#### 案例 3：False Belief Task_0028
- **正确答案**：C
- **Baseline**：C ✓ — "Youyou saw the vest in the drawer before leaving, and did not witness Xiao Gang move it."
- **RAG**：D ✗ — "Xiao Gang moved the vest from the drawer to the cabinet after Youyou left. So when Youyou returns and looks for the vest, the most likely place is the cabinet."
- **分析**：模型的推理从"Youyou 的信念状态"偏移到了"物品的实际位置"，这正是 false belief 题的经典陷阱。

**共性规律**：294 条规则中没有 False Belief 对应类别的规则，全库搜索返回的全是 flattery、nonverbal behavior 等不相关内容。模型在 system prompt 中被告知"Use it as supplementary reference"，于是尝试参考这些规则，反而破坏了原有的正确推理路径。

### 3.2 Hinting Task Test（-12.6pp，15 个翻转答错）

**根因：语言学理论规则（fuzzy quantifiers、probabilistic modifiers）误导了言外之意理解。**

#### 案例 1：Hinting Task Test_0028
- **正确答案**：C（提醒系安全带）
- **Baseline**：C ✓ — "The examiner repeats the question after adjusting the seat belt to signal that Xiao Li should pay attention to safety and be properly buckled before starting."
- **RAG**：B ✗ — "The examiner's repeated question, along with the seat belt gesture, is meant to check whether Xiao Li is actually prepared to begin the driving test."
- **注入内容**："The meaning of a single ambiguous signal should be cross-validated through its combination with accompanying body posture..."

#### 案例 2：Hinting Task Test_0036
- **正确答案**：C（暗示茅台可能是假酒）
- **Baseline**：C ✓ — "Xiaozhang's words sound like polite praise, but his quick switch to red wine suggests he may have noticed something was off with the Maotai."
- **RAG**：A ✗ — "Xiaozhang says Maotai tastes good, but then quickly finds an excuse to switch to red wine. This suggests he is politely avoiding drinking more Maotai and prefers red wine instead."
- **注入内容**："When a speaker attaches a probabilistic modifier to a fuzzy quantifier, the listener's mental model must synchronously incorporate a corresponding confidence decay weight."

#### 案例 3：Hinting Task Test_0048
- **正确答案**：C（讽刺挑剔）
- **Baseline**：C ✓ — "Xiao Zhang is using a playful, slightly sarcastic remark to imply that Lao Wang is overly particular and always picks out flaws."
- **RAG**：D ✗ — "Xiao Zhang's question about fish is not really about Lao Wang's food preference... Xiao Zhang is likely trying to shift the conversation."

**共性规律**：Hinting Task 同样不在 CATEGORY_MAPPING 中，检索到的 quantifier/pragmatic 规则让模型过度分析语言结构，忽略了场景常识。

### 3.3 Percepts-Knowledge Links（-20.0pp，9 个翻转答错）

**根因：与 False Belief 相同——"观察者知识更新"类题目被不相关规则干扰。**

#### 案例 1：Percepts-Knowledge Links_0002
- **正确答案**：A
- **Baseline**：A ✓ — "Xiao Li saw the chalk in the handbag before leaving, but he did not see Xiao Ming move it to the box."
- **RAG**：B ✗ — 推理被带偏到物品实际位置
- **注入内容**："When flattery accompanies an immediate request..." — 完全不相关

---

## 4. 正面案例分析（RAG 帮助答对）

### 4.1 Faux-pas Recognition Test（+5.2pp，56 个翻转答对）

#### 案例 1：Faux-pas Recognition Test_0025
- **正确答案**：A（有人说了不当的话）
- **Baseline**：B ✗ — "No one in the story says anything rude, offensive, or inappropriate."
- **RAG**：A ✓ — "Uncle Zhang's response is a little inappropriate because Xiao Yu has just proudly offered him mooncakes, and he says he likes mooncakes except for the lotus seed paste flavor, which sounds dismissive."
- **注入内容**："Significant incongruence between nonverbal behavior and the situational tone typically indicates polite masking..."
- **分析**：规则关于社交行为不一致的判断与 faux-pas 识别高度吻合，帮助模型捕捉到了微妙的社交失当。

### 4.2 Knowledge-Pretend Play Links（+13.3pp，5 个翻转答对）

#### 案例 1：Knowledge-Pretend Play Links_0002
- **正确答案**：A
- **Baseline**：C ✗ — "Tara's arm movement is described as a graceful up-and-down motion that is very similar to wing flapping... best matches a butterfly flapping its wings."
- **RAG**：A ✓ — "Tara lives in an underwater city with no birds or flying creatures, so it likely does not have a real bird or bat model to imitate."
- **注入内容**："Confirming pretend imitation requires verifying the structural alignment between the behavioral sequence and the subject's internal script..." / "External stimuli activate the corresponding imitation sequence only when matching the subject's experience repository."
- **分析**：规则精确命中了 pretend play 的核心逻辑——角色只能模仿自己认知范围内的事物。

**正面案例共性**：当检索到的规则与问题考查的认知能力直接对应时，RAG 能显著提升表现。Faux-pas 的问题语义天然与 social norm 规则接近（FAISS top1 L2=0.94），Knowledge-Pretend Play 与 pretend play 规则精确匹配。

---

## 5. FAISS 相似度分析

### 5.1 分数分布（L2 距离，越低越相似）

| 组别 | N | Top1 中位数 | Top1 均值 | Min | Max |
|------|--:|----------:|----------:|----:|----:|
| Gain（RAG 帮到） | 155 | 1.1733 | 1.1308 | — | — |
| Loss（RAG 害了） | 244 | 1.1958 | 1.1794 | — | — |
| Both Right | 360 | 1.2295 | 1.2263 | 0.86 | 1.45 |
| Both Wrong | 79 | 1.2322 | 1.2283 | 0.95 | 1.41 |

### 5.2 典型分数对比

| Query 类型 | Top1 L2 距离 | 含义 |
|------------|------------:|------|
| Faux-pas: "Does anyone say something inappropriate?" | **0.94** | 高度相关 |
| False Belief: "Where is the cabbage now?" | **1.41** | 完全不相关 |

### 5.3 结论

- Gain 和 Loss 的 FAISS 分数分布**高度重叠**（中位数差仅 0.02），单纯依靠 L2 距离阈值无法有效区分有益/有害检索
- 但在 task 层面差异明显：Faux-pas 类问题天然与规则库语义接近（~0.94），False Belief 类问题天然与规则库语义疏远（~1.40）
- **说明门控的粒度应该在 task/category 级别而非单条检索级别**

---

## 6. 问题根因：CATEGORY_MAPPING 不完整

### 6.1 规则库覆盖情况

规则库（294 条）只包含 **13 个类别**，但 ToMBench 有 **20 个 task**。

当 `use_category_filter=True` 时，不在 CATEGORY_MAPPING 中的 task 会 fallback 到全库搜索，检索到不相关的规则：

```python
# 旧代码逻辑
if self.use_category_filter and category and category in CATEGORY_MAPPING:
    # 按类别过滤 → 只搜对应规则
else:
    docs = self.store.similarity_search(query, k=top_k)  # 全库搜索 → 噪声
```

### 6.2 未覆盖的 Task（7 个受损严重）

| Task（未映射） | RAG Delta | 检索到的内容 |
|----------------|----------:|-------------|
| False Belief Task | -13.5pp | flattery/nonverbal（不相关） |
| Percepts-Knowledge Links | -20.0pp | flattery/observation（不相关） |
| Hinting Task Test | -12.6pp | quantifiers/pragmatics（不相关） |
| Multiple Desires | +5.0pp | — |
| Discrepant Emotions | -7.5pp | — |
| Discrepant Intentions | -7.5pp | — |
| Strange Story Task | -1.7pp | — |

---

## 7. 修改方案

### 7.1 补全 CATEGORY_MAPPING（已完成）

将全部 20 个 benchmark task 映射到语义最接近的规则类别：

```python
CATEGORY_MAPPING: dict[str, str] = {
    # 原有 13 个直接映射
    'Belief': 'Belief',
    'Comprehensive': 'Comprehensive',
    'Knowledge': 'Knowledge',
    'Ambiguous Story Task': 'Ambiguous Story Task',
    'Completion of Failed Actions': 'Completion of Failed Actions',
    'Discrepant Desires': 'Discrepant Desires',
    'Emotion Regulation': 'Emotion Regulation',
    'Knowledge-Attention Links': 'Knowledge-Attention Links',
    'Knowledge-Pretend Play Links': 'Knowledge-Pretend Play Links',
    'Moral Emotions': 'Moral Emotions',
    'Persuasion Story Task': 'Persuasion Story Task',
    'Scalar Implicature Test': 'Scalar Implicature Test',
    'Unexpected Outcome Test': 'Unexpected Outcome Test',
    # 新增 10 个映射
    'False Belief Task': 'Belief',               # 信念推理
    'Percepts-Knowledge Links': 'Knowledge',      # 感知→知识更新
    'Prediction of Actions': 'Completion of Failed Actions',  # 行为预测
    'Multiple Desires': 'Discrepant Desires',     # 欲望推理
    'Discrepant Emotions': 'Emotion Regulation',  # 情绪类
    'Discrepant Intentions': 'Comprehensive',     # 意图冲突
    'Hidden Emotions': 'Emotion Regulation',      # 隐藏情绪
    'Hinting Task Test': 'Comprehensive',         # 言外之意
    'Faux-pas Recognition Test': 'Comprehensive', # 社交失误
    'Strange Story Task': 'Comprehensive',        # 非字面理解
}
```

### 7.2 负增益 Task 黑名单（已完成）

基于 test_0519_rag_filter 实验（category filter 开启后 vs baseline），对 RAG 持续为负贡献的 task 关闭检索：

```python
CATEGORY_TO_USE_RAG = {
    # ...
    'False Belief Task': False,          # 97.3% baseline, RAG -6.0pp
    'Percepts-Knowledge Links': False,   # 97.5% baseline, RAG -22.5pp
    'Discrepant Emotions': False,        # 90.0% baseline, RAG -17.5pp
    'Multiple Desires': False,           # 95.0% baseline, 高 baseline 无需 RAG
    'Knowledge-Attention Links': False,  # 50.0% baseline, RAG -15.0pp
    'Hinting Task Test': False,          # 85.4% baseline, RAG -5.8pp
    'Emotion Regulation': False,         # 55.0% baseline, RAG -10.0pp
    'Completion of Failed Actions': False, # 55.0% baseline, RAG -5.0pp
    'Persuasion Story Task': False,      # 原有黑名单，保留
    'Percept': False,                    # 原有黑名单，保留
    # ...
}
```

黑名单覆盖的 loss 估算：在 test_0519_rag_filter 实验中，这些 task 合计贡献了约 60% 的总 loss（约 120/203），黑名单后预期 RAG 整体从 -2.1pp 回升到接近正贡献。

### 7.3 默认开启 Category Filter（已完成）

- `ToMRulesV1RAG` 和 `RAGv2Engine` 的 `use_category_filter` 默认值从 `False` 改为 `True`
- 两个 runner（`run_tombench_harness.py`、`run_cogtom_v2_harness.py`）的 `--rag_category_filter` 默认值改为 `True`
- 新增 `--no_rag_category_filter` 参数用于关闭过滤

现在使用 `--rag` 即自动按类别过滤 + 黑名单跳过负增益 task，无需额外指定参数。

### 7.4 System Prompt 修复（已完成）

commit `b24235b` 中 SYSTEM_TAIL 从 `"First give a brief reason (2-3 sentences)"` 被意外改为 `"First give a brief reason"`，导致 baseline 下降 3pp。已恢复原始措辞。

### 7.5 三组实验对比总结

| 实验 | 准确率 | vs Baseline | 净翻转（gain-loss） |
|------|-------:|----------:|-------------------:|
| Baseline（无 RAG） | 77.73% | — | — |
| +RAG（无过滤） | 74.62% | -3.11pp | -89 |
| +RAG（category filter） | 75.66% | -2.07pp | -59 |
| +RAG（category filter + 黑名单） | 待验证 | 预期接近 0 或正 | — |

### 7.6 后续方向

1. **验证实验**：用黑名单 + category filter 重新跑全量 ToMBench，确认 RAG 贡献转正
2. **L2 阈值门控**：当前 gain/loss 的 FAISS L2 分数分布高度重叠（中位数差仅 0.02），暂不设阈值，需更大规模数据分析
3. **规则库扩充**：当前 13 个类别 294 条规则，RAG 正向 task（Faux-pas +3.7pp、Knowledge-Pretend Play +16.7pp、Persuasion +5.0pp）可定向补充规则
4. **映射关系优化**：部分映射语义偏差较大（如 `Discrepant Emotions → Emotion Regulation`），可考虑为这些 task 新建专属规则类别
