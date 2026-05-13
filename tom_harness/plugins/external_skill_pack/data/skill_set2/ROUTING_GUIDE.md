# Skill Routing — Design Guide (中英对照)

> Companion to [`SKILLS_CATALOG.md`](./SKILLS_CATALOG.md).
> Source: [`llm_router.py`](./llm_router.py).

This document describes **how a single case (story + question + options) is
routed to one of the 12 skills** (or `NONE` for vanilla fall-back), why
the routing is done by an LLM rather than by a static `task_type`-based
table, and which design choices keep the router stable.

---

## 1. Why a router (and not a static table)?

**EN.** We deliberately do **not** use the dataset's `task_type` field at
inference time. Real users don't tag their questions with
`Faux-pas Recognition Test` or `Persuasion Story Task`; the router has to
work from the raw input alone. Furthermore, several skills are
*cross-task-type* by design — for instance `S4_Strategic` covers Strange
Story, Persuasion, Ambiguous Story, Discrepant intentions, Hinting, and
Double Bluff. A static `task_type → skill` mapping cannot generalise to
unseen task types or to corpora that lack such labels.

**中文。** 我们有意 不使用 数据集自带的 `task_type` 字段做路由。真实用户提
问时不会给问题打上 `Faux-pas Recognition Test` 或 `Persuasion Story Task`
之类的标签,路由必须 只依赖原始输入(故事 + 问题 + 选项)。另外,我们的多个
skill 本来就是 跨 task_type 设计 的——例如 `S4_Strategic` 同时覆盖 Strange
Story、Persuasion、Ambiguous Story、Discrepant intentions、Hinting、
Double Bluff。一张固定的 `task_type → skill` 表既不能迁移到未见过的 task
type,也无法适配那些根本就没有这种标签的语料。

---

## 2. Architecture — three-stage pipeline

```
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│  raw case            │    │  router (LLM call)   │    │  answerer (LLM call) │
│  story + question +  │ ─► │  reads CATALOG +     │ ─► │  receives chosen     │
│  options             │    │  emits  Skill: <ID>  │    │  SKILL prompt + base │
└──────────────────────┘    └──────────────────────┘    └──────────────────────┘
                                       │
                                       └──► NONE  ──► vanilla prompt (no skill)
```

**EN.** Three components: (1) the **router** sees the raw case + the 12
catalog descriptions and emits a single line `Skill: <ID>`; (2) the
**skill prompt** is looked up from the catalog and prepended to the
question; (3) the **answerer** (any LLM) sees the full prompt and emits a
multiple-choice answer. The router and answerer can be *the same model* or
*different models* — in our experiments the router is fixed to
`gpt-5.4-mini` and the answerer is varied (`gpt-5.4-mini`, `glm-5`).

**中文。** 三个环节:(1) **路由器** 看 原始 case + 12 条 skill 简介,输出一
行 `Skill: <ID>`;(2) **skill 提示词** 从 catalog 里查表,拼接在题目前面;
(3) **答题模型** 拿到完整 prompt 后输出选项答案。路由器和答题模型 可以是同
一个模型,也可以是不同模型 ——在我们的实验里,路由器固定用 `gpt-5.4-mini`
,答题模型则换成 `gpt-5.4-mini` / `glm-5`。

---

## 3. The router prompt (what the LLM actually sees)

The router prompt is built by `build_router_prompt(story, question, options, labels)` and contains:

```
You are a skill router for Theory-of-Mind multiple-choice questions.
Read the story, question, and options below, then pick the ONE strategy
that best matches the case. Pick at most one.

Available strategies:

- S1_FauxPas: Social interaction where someone may say something inappropriate, …
- S2_Scalar:  Story uses scalar quantifiers (most / some / a few / hardly any) …
- … (12 catalog entries + NONE)

Decision rules:
- Look at WHAT THE QUESTION IS ASKING and WHAT KIND OF REASONING is required.
- Match to the strategy whose triggering pattern best fits.
- If no strategy clearly applies, choose NONE.

Reply with EXACTLY this format on a single line, with no additional text:
Skill: <ID>

=== STORY === <story>
=== QUESTION === <question>
=== OPTIONS === <A./B./C./D. ...>
```

**EN.** Three deliberate properties of this prompt:

1. **Catalog descriptions are *short, trigger-pattern-style*** (see
   `ROUTER_CATALOG` in `llm_router.py`). They describe the *shape of the
   case* — "story uses scalar quantifiers + total N + sub-counts" — rather
   than the underlying procedure. The full procedure (S2's TIGHT ranges,
   SUM constraint etc.) is *not* shown to the router; it would only
   confuse the routing decision.
2. **Decision rule is anchored on what the question asks**, not on
   surface keywords in the story. "How should X persuade Y?" is the
   trigger for S4 even if the story mentions a faux-pas-like setting.
3. **`NONE` is a first-class option.** When no skill cleanly applies, the
   router must say so; we then fall back to the vanilla prompt rather than
   force-fit a wrong skill.

**中文。** 这套 prompt 有 三处刻意的设计:

1. **Catalog 写成短小的"触发模式"** (见 `llm_router.py::ROUTER_CATALOG`)。
   每条描述讲的是 案件的"形状"——比如"故事里有数量词 + 总数 + 子数"——而
   不讲底层的解题过程。S2 完整的 TIGHT range、SUM constraint 都 不 给路由
   看;喂给它只会干扰路由判断。
2. **决策规则锚定在"问题问的是什么"**,而不是故事里出现的浅表关键词。哪
   怕故事里有像 faux-pas 的情节,只要问题问的是"X 怎么说服 Y?",就该走 S4
   。
3. **`NONE` 是一等公民**。任何 skill 都不太合适时,路由必须明说;此时回落
   到 vanilla prompt,而不是硬塞一个错的 skill。

---

## 4. Catalog descriptions — design principles

Each `S*` description in `ROUTER_CATALOG` follows the same template:

```
S<N>_<Name>:
  <when does this skill fire?  — a short trigger pattern>
  <what does the question typically look like?  — 1–2 example questions>
  <(optional) how is it different from a similar skill?>
```

**EN.** Three concrete examples:

- `S2_Scalar` is described in **structural** terms — "story uses scalar
  quantifiers ... together with an explicit total N and one or two
  concrete sub-counts" — so the router can fire on any case with that
  shape, even if it isn't called "Scalar Implicature Test".
- `S5_Expectation` and `S11_BeliefEmotion` are the most easily-confused
  pair, so `S5`'s description ends with an explicit
  **disambiguation clause**:
  > "Distinguish from S11: S5 fires when story explicitly mentions
  > hiding / masking / suppressing; S11 fires when no hiding is involved
  > and emotion just follows from the believed situation."
- `S11_BeliefEmotion` carries TWO sub-cases ("(a) general belief→emotion"
  and "(b) MORAL EMOTION items") because both fall under the same skill
  but trigger on different question shapes.

**中文。** 每条 catalog 描述都遵循同一模板:**触发模式 + 典型问句 + 与相
似 skill 的区分**。三个具体例子:

- `S2_Scalar` 用 结构化描述——"故事里有 scalar 数量词 + 一个显式总数 + 一两
  个具体子数"——这样路由能识别 任何 形状一致的案件,而不依赖 task_type 名
  字叫不叫 "Scalar Implicature Test"。
- `S5_Expectation` 和 `S11_BeliefEmotion` 是最容易混淆的一对,所以 `S5` 描
  述末尾专门加了 区分说明:
  > "与 S11 的区别:故事里出现 hiding / masking / suppressing 字样时走
  > S5;没有遮掩、情绪只是顺着角色的'信念状态'生成时,走 S11。"
- `S11_BeliefEmotion` 写了 两个子用法 ——"(a) 普通的信念→情绪"和"(b)
  Moral emotion 题"——因为它们落在同一个 skill 下,但题面长得不一样,需要
  让路由都能识别。

---

## 5. Output parsing — robust to noisy LLM responses

`parse_router_choice(response)` does two passes:

**EN.**

1. **Preferred:** look for an explicit `Skill: <ID>` (or `skill：<ID>`,
   handling Chinese full-width colon) line. If found and the ID is in the
   valid set, return it.
2. **Fallback:** scan the whole response for any token matching the regex
   `\b(S[1-7]_[A-Za-z]+|NONE)\b` and return the **last** match. This
   handles the common case where the model writes a brief justification
   first ("This is a faux-pas case") and then concludes with the ID; the
   last token wins, which is typically the conclusion.
3. If neither finds a valid ID, return `None`. The experiment script then
   coerces this to `"NONE"` and uses the vanilla prompt.

**中文。**

1. **优先**:在响应里找 `Skill: <ID>`(或 `skill：<ID>`,兼容中文全角冒号
   ) 一行。命中且 ID 合法,直接返回。
2. **兜底**:把整个响应按正则 `\b(S[1-7]_[A-Za-z]+|NONE)\b` 扫一遍,取
   最后一次匹配 。这样能容许模型先写一两句理由("这是个 faux-pas 案件"),
   再以 ID 收尾——以最后那个为准,通常是它真正的结论。
3. 两步都拿不到合法 ID,返回 `None`,实验脚本会把它当成 `"NONE"` 走 vanilla
   prompt 路径。

---

## 6. Disambiguation rules — the high-confusion pairs

The router gets ~30% of cases wrong. Inspection of mis-routes shows the
errors cluster on a handful of *near-twin* skill pairs. The current
catalog encodes explicit disambiguation cues for the worst three:

| Pair | Confusion symptom | Disambiguation cue (now embedded in catalog) |
|---|---|---|
| **S5** vs **S11** | "what is X's real feeling?" looks identical | S5 = story mentions hiding/masking/suppressing; S11 = no hiding, emotion follows belief |
| **S3** vs **S5** | "what does X think?" — belief or expectation? | S3 = state-of-the-world / object-location reasoning; S5 = emotional reaction to surface event |
| **S1** vs **S4** | flattery / persuasion both involve speech-act intent | S1 = listener-discomfort / "did anyone say something inappropriate?"; S4 = "what does X really mean?" / "how should X persuade Y?" |

**EN.** The disambiguation cue is added directly into the *more
permissive* of the two skills, so the router only needs to remember one
extra rule. (For example, the cue lives inside S5's catalog string, not
S11's, because S11 is described in narrower terms and S5 is the one that
tends to over-fire.)

**中文。** 区分提示直接嵌进 **更容易过度触发** 的那个 skill 描述里,这样路
由只需要记一个额外规则。例如那条 "story mentions hiding" 的 cue 写在 S5 的
catalog 里,而不是 S11——因为 S11 的描述本来就更窄,容易过界的是 S5。

---

## 7. Why a single skill (and not multi-skill ensembling)?

**EN.** Pick exactly one. We tried (in early prototypes) returning the
top-2 skills and ensembling their answers; this hurt accuracy because:

- The two skill prompts often *contradict each other* (e.g. S2 enforces a
  numeric SUM constraint that S4 has no use for, and the model gets
  confused trying to honour both).
- Concatenating two long prompts pushes the answerer toward token-budget
  truncation (which we already had to fight separately for `glm-5`).
- The marginal accuracy gain is < 1pp in our pilot data, far less than
  a clean single-skill fix.

So the router commits to **one** skill, and `NONE` is the explicit escape
hatch when nothing fits. The answerer is then on a *clean*, focused
prompt path.

**中文。** 路由 只挑一个 。早期原型试过让路由返回 Top-2 skill,把两段 skill
prompt 都塞进答题模型里 ensemble,但效果反而下降:

- 两段 skill 提示经常 自相矛盾(例如 S2 要严格守数值求和约束,S4 完全用不
  到;模型左右为难)。
- 两段长 prompt 拼在一起会把答题模型推向 token 截断 (这个问题在 `glm-5`
  上我们另外修复过)。
- 在试点数据上 ensemble 带来的提升不到 1pp,远小于单 skill 应用得当带来的
  收益。

因此路由器 只承诺一个 skill,实在没有合适的就返回 `NONE` 走 vanilla 兜
底,让答题模型走在一条 干净、聚焦 的提示路径上。

---

## 8. End-to-end usage (code-level)

The minimal usage pattern from `experiment_per_model.py`:

```python
from llm_agents import load_model
from llm_router import build_router_prompt, parse_router_choice, get_skill_prompt
from eval_new_benchmarks import build_vanilla_prompt, extract_answer_letter

router_model   = load_model("gpt-5.4-mini")
answerer_model = load_model("glm-5")

# 1) Routing pass
router_prompt = build_router_prompt(item["story"], item["question"],
                                     item["options"], item["labels"])
choice = parse_router_choice(router_model.interact(router_prompt, max_tokens=64))
choice = choice or "NONE"

# 2) Build the answerer prompt with (or without) a skill
skill = get_skill_prompt(choice)               # None when choice == "NONE"
base  = build_vanilla_prompt(item["story"], item["question"],
                              item["options"], item["labels"])
prompt = (
    "You are answering a Theory-of-Mind multiple-choice question.\n"
    "Apply the following strategy carefully, then answer.\n\n"
    f"=== STRATEGY ===\n{skill}\n=== END STRATEGY ===\n\n"
    f"=== QUESTION ===\n{base}"
) if skill else base

# 3) Answer pass
resp = answerer_model.interact(prompt, max_tokens=8192)
pred = extract_answer_letter(resp, item["labels"])
```

The router pass costs ~64 tokens, the answer pass ~2k–8k tokens; the
router is cached per case so the same router decision is reused across
multiple answerer models.

**中文(简要)。** 路由调用 ≈ 64 tokens(廉价),答题调用 ≈ 2k–8k tokens
(主要成本)。同一个 case 的路由结果被缓存,跨答题模型复用——这样在比较
`gpt-5.4-mini` vs `glm-5` 时,两边走的是 完全相同 的 skill 选择,排除了路由
噪声对模型差异的污染。

---

## 9. Failure modes & open issues

**EN.**

- **Routing accuracy ≈ 70%.** The bottleneck is the S5/S11 boundary and
  the S4 over-trigger on Discrepant-intentions cases that are actually
  borderline between S4 and S11.
- **`gpt-5.4-mini` as the fixed router.** A weaker router model would
  drop accuracy noticeably; a stronger one (e.g. `o3`) would help but
  break the cost equation.
- **Catalog drift.** Every time we add a skill, the router has to be
  re-prompted with the longer catalog; descriptions of *existing* skills
  sometimes need a `Distinguish from S<new>` line to keep boundaries
  sharp.
- **Adversarial / out-of-domain cases.** A genuinely novel ToM pattern
  may correctly route to `NONE` — that's the system working as
  designed — but adds 0 fix value. The remedy is to add a new skill, not
  to broaden an existing one.

**中文。**

- **路由准确率 ≈ 70%。** 当前瓶颈在 S5/S11 边界,以及 S4 在"Discrepant
  intentions"上的过度触发——那些 case 在 S4 / S11 之间本来就模糊。
- **路由用固定 `gpt-5.4-mini`。** 换更弱的模型路由准确率会明显掉;换更强
  的(如 `o3`)能再涨,但破坏成本结构。
- **Catalog 膨胀风险。** 每加一个 skill,路由 prompt 都会变长;现有 skill
  的描述有时也得补一句 "与 S<new> 的区分" 才能保持边界清晰。
- **对抗 / 域外案件。** 真正新型的 ToM 模式可能被路由 正确地 判为 `NONE`
  ——这是系统的设计意图——但对 fix 率没贡献。要补它,只能 加新 skill,而不是
  把某个已有 skill 改宽。

---

## 10. TL;DR

**EN.** The router is one cheap LLM call that reads only the case + a 12-
line catalog and writes back one line `Skill: <ID>`. It deliberately works
without `task_type`, commits to one skill (or `NONE`), encodes
disambiguation cues for the high-confusion pairs, and is decoupled from
the answerer model so the same routing decision can be re-used across
different answerer models for fair comparison.

**中文。** 路由就是一次便宜的 LLM 调用:输入 = 案件 + 12 条 catalog 简介,
输出 = 一行 `Skill: <ID>`。它 不依赖 task_type 标签,只挑一个 skill (或
`NONE`),在易混淆的 skill 对里嵌入了区分线索,并且 与答题模型解耦——同一份
路由决策可以跨多个答题模型复用,做到公平对比。
