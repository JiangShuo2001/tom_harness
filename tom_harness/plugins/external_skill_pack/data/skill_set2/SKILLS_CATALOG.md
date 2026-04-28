# Skills v2 — Catalog (中英对照 + Representative Cases)

> 12 skills, each (a) targets a cluster of `task_type`s, (b) embeds a 3–5
> step procedure, and (c) lists explicit guardrails. Each skill is
> illustrated with **one real case** drawn from the targeted task types,
> together with the gold answer and how `gpt-5.4-mini` / `glm-5` actually
> answered it on the previous (pre-fix) run.
>
> Source code: [`skills.py`](./skills.py) · target map: `SKILL_TARGETS`.

| ID | One-line purpose | Targeted task types | Datasets |
|---|---|---|---|
| **S1** `FauxPas` | Detect socially inappropriate utterance / strategic flattery | Faux-pas Recognition Test · Expanding Tasks: Flattery | ToMBench · CogToM |
| **S2** `Scalar` | Tight quantifier ranges + hard sum-constraint for "most/some/almost-no" | Scalar Implicature Test/Task | ToMBench · CogToM |
| **S3** `BeliefLedger` | Per-character witnessed-events ledger for false / 2nd-order beliefs | False Belief · See-Know · 2nd-Order False Belief · Knowledge-attention | both |
| **S4** `Strategic` | Surface-vs-strategic intent decoder (lies, persuasion, hints, irony, intention attribution) | Strange Story · Persuasion · Ambiguous · Hinting · Discrepant intentions · Double Bluff · Pretend | both |
| **S5** `Expectation` | Expectation-delta search for atypical / hidden / discrepant emotion | Unexpected Outcome · Hidden emotions · Discrepant emotions | both |
| **S6** `Spatial` | Explicit axis-mapping algorithm for perspective taking / dice / cube | Spatial Construction · Picture Identification | CogToM |
| **S7** `KnowledgeBound` | Strip reader's pop-culture analogies that fall outside character's world | Knowledge-pretend play links · Sarah Task | both |
| **S8** `OtherPreference` | Decision tree A/B/C/D for whose preference wins (target / hybrid / actor / dating) | Discrepant desires · Multiple desires · Prediction of actions | ToMBench |
| **S9** `SensoryChannel` | Strip every channel the perceiver lacks (blind / deaf / behind glass) | Synesthetic Fallacy · Affective Perspective-Taking | CogToM |
| **S10** `AudienceCalib` | Expert listener → share experience, do NOT define the term | Aware of Reader's Knowledge | CogToM |
| **S11** `BeliefEmotion` | Belief-driven emotion + 5-check filter against false guilt/panic | Belief Based Emotions · Moral emotions | both |
| **S12** `CommitmentPrio` | Prior commitment > ongoing > new invitation > background | Completion of failed actions | ToMBench |

---

## S1. `FauxPas` — Pragmatic Faux-Pas Detection

**EN** — Pragmatic Faux-Pas Detection. Enumerate every utterance, then for each one ask: (a) what the speaker's intent is (kind / neutral / strategic), (b) whether the speaker is missing a listener-specific fact that would make the remark hurtful, and (c) whether a reasonable listener would feel hurt or patronised. A faux pas requires all three: a well-meaning speaker who lacks knowledge of a listener-specific fact, plus an uncomfortable listener. Politeness does NOT protect a remark from being a faux pas. Separate flattery check: a positive remark with a clear strategic incentive is insincere — mark it as strategic, not as a real compliment.

**中文** — 言语失礼识别。把故事里每一句对话都列出来,逐条检查:(a) 说话人意图是好心 / 中性 / 有策略性?(b) 说话人是不是不知道听者的某个特殊事实(身份、偏好、近况),才让这句话变得伤人?(c) 听者会不会觉得难堪、被冒犯、被怜悯?三条同时满足才构成 faux pas;礼貌的措辞不能否定 faux pas 的本质。另外,带明显策略动机的"夸奖"应识别为奉承策略,而不是真心赞美。

**Representative case** — `cogtom_7781`, `Expanding Tasks: Flattery`

> *Story.* At the party, Xiaotong said to the celebrity guests, "Your performance was amazing, I am your loyal fan!"
>
> *Q.* What is the main purpose of Xiaotong praising celebrities?
>
> A. Sincerely express love for celebrity performances
> B. Improving personal social influence by pleasing celebrities ✅
> C. Objectively describe the actual level of celebrity performance
> D. Show your appreciation of art to other guests
>
> Without S1, `glm-5` defaults to the surface compliment (A). With S1, the **strategic-flattery flag** fires (positive remark + plausible social gain) → B.

---

## S2. `Scalar` — Scalar Calibration with Hard Sum Constraint

**EN** — Scalar Calibration. Step 1 extract: total N, every explicit concrete sub-count, every scalar quantifier the speaker used in order. Step 2 bind quantifiers to TIGHT numeric ranges (e.g. "almost no X" = 1 to 3 items, NOT a percentage; "most" = 60–85%, NOT 50%+). Step 3 enforce the HARD SUM CONSTRAINT: pin "almost no" to 1–2, subtract every explicit count, distribute the remainder so the relative ranking is preserved. Step 5 disambiguate "before counting" (no anchor → quantifier range only) vs "after counting" (revealed sub-count anchors the rest). Guardrail: when "almost no X" is mentioned, the larger groups must absorb the residual — never leave a 6+ amount in the "almost no" bucket.

**中文** — 数量词标定。先抽取出总数 N、每个具体的子数、每个出现过的数量词(按顺序)。然后用紧致的数值区间替换松散语义("almost no" = 1-3 个,不是百分比;"most" = 60%-85%,下界是 60% 不是 50%)。最关键的一步是强制求和约束:把 "almost no" 钉在 1 或 2,然后用 N 减去所有显式数和钉死的数,剩下的余量按词序排名分配给较大的几组。"数之前"(只有数量词,没有锚点)和"数之后"(有一个具体数作锚点)要分开处理。Guardrail:看到 "almost no" 的类别就不能再留 6 个以上,余量一定流给较大的组。

**Representative case** — `tombench_2279`, `Scalar Implicature Test`

> *Story.* On a farm, farmer Wang keeps **15 chickens**, **almost a third** of which are white. He counts a part and finds that **4 are white**.
>
> *Q.* After Wang counts a part of the chickens, how many chickens does he guess are white?
>
> A. 4   B. 5 ✅   C. 3   D. 2
>
> Without S2, `glm-5` interprets "almost a third" loosely as "slightly less than 5" → picks 4 (the value he already saw). With S2, the SUM constraint forces: one third of 15 = 5, "almost" pulls slightly below — but the 4 he already saw is *part of* the white count, NOT the total — so the *guess* is 5.

---

## S3. `BeliefLedger` — Character Knowledge Ledger

**EN** — Character Knowledge Ledger. Step 1 list every state change in chronological order with its witnesses. Step 2 mark, for each character, which events they personally witnessed vs missed (left the room, asleep, behind their back, no sensory channel). Step 3 a character's belief about an object = the LAST state they personally witnessed, NOT the current world state. Step 4 identify the question's perspective: "Where IS X?" → world state; "Where will C look for X?" → C's belief; "Does A know what B thinks?" → 2nd-order — A had to witness B's perception or action to know B's belief. Guardrail: never let "the story says X actually happened" leak into a character's belief unless that character actually saw X.

**中文** — 角色知识账本。先按时间顺序列出所有状态变化,标注每个事件的"目击者"。然后给每个角色画一张账本:他直接目击了哪些事件,缺席了哪些(离开了房间、睡着了、背对、没有感官通道)。一个角色对某物的"信念" = 他亲眼见过的最后一个状态,而不是当前世界的实际状态。看清楚问题问的是"现实状态"(用世界事实)还是"角色的认知"(用账本里的最后状态)还是"二阶心智"(A 必须目击过 B 的感知/行动才能知道 B 在想什么)。Guardrail:故事的"客观叙述"不能漏到一个没在场的角色的信念里。

**Representative case** — `tombench_626`, `False Belief Task`

> *Story.* Xiao Ming and Youyou stroll around the farm, they see a backpack and a cabinet, they find a marker in the backpack, **Youyou leaves the farm**, Xiao Ming moves the marker to the cabinet.
>
> *Q.* Where is the marker now?
>
> A. Cabinet   B. Backpack   C. Cupboard ✅   D. Drawer
>
> *(Note: this case is also a known data-translation artefact — Chinese "柜子" was rendered as "cabinet" in the story but "cupboard" in the gold option. S3 is correctly applied here, and any belief-question variant — "where will Youyou look?" — is decisively answered as `Backpack` by S3's Step 3.)*

---

## S4. `Strategic` — Surface vs Strategic Intent

**EN** — Surface vs Strategic. Layer 1 quote what is literally said/done. Layer 2 list the speaker's goals, incentives and barriers facing each party. Layer 3 match the situation to a known pattern (lie, persuasion, pretend, hint/sarcasm, ambiguous-signalling). PERSUASION RULE: when the question is "how should X persuade Y?", the best option is the one that DIRECTLY ADDRESSES Y's stated barrier — not the one that praises X's plan or adds a fresh attraction. SPECIAL CASE for "what is X's intention?" questions: never pick the bland surface paraphrase; locate the story's explicit motive cue ("mistakes it for…", "knows X but…", "yelled rudely…") and pick the option that names the SPECIFIC mechanism that cue licenses.

**中文** — 表面 vs 策略意图。第 1 层把字面说什么/做什么逐字引用;第 2 层列出说话人的目标、压力、双方各自面临的障碍;第 3 层把情境对到一个已知模板(谎言、说服、假装、暗示/讽刺、模糊信号)。说服题的关键规则:好答案是 直接化解对方异议 的那个选项,不是夸自己计划好或者加新诱因的那个。意图归因题(Discrepant intentions)的特殊步骤:不要选最中性的"表面复述"选项;先在故事里找出明确的动机线索("误以为是…"、"明明知道但…"、"刚才粗鲁地吼…"),然后选 命名了那条线索所暗示的具体机制 的选项。

**Representative case** — `tombench_1156`, `Persuasion Story Task`

> *Story.* Xiao Ling is going to attend a concert and needs her younger sister Xiao Ting to take care of her pet.
>
> *Q.* How does Xiao Ling convince Xiao Ting?
>
> A. Xiao Ling decides to **give Xiao Ting a ticket to the concert** as a thank you.
> B. "If you find taking care of pets troublesome, I can teach you some simple methods…"
> C. "I know you have doubts about taking care of pets, but I believe you are the most suitable person."
> D. **Promises to treat Xiao Ting to a big meal another day.** ✅
>
> Without S4, both gpt and glm pick C — it sounds psychologically warm. But the persuasion rule says: address the barrier *with a tangible incentive* — the gold pattern in this benchmark is concrete reciprocity (D), not verbal validation.

---

## S5. `Expectation` — Expectation-Delta / Hidden Emotion

**EN** — Expectation-Delta Analysis. Step 1 quote the surface event. Step 2 ask what reaction would be TYPICAL given default norms. Step 3 read the question to see what reaction it actually points at (atypical / hidden / opposite). Step 4 if actual ≠ expected, search the story for: an additional constraint only this character faces, a competing second goal, an external trigger known only to this character, or an inside/outside asymmetry (what they SHOW vs what they FEEL). SPECIAL CASE for "real feeling / hidden emotion" items: the "hiding" is an action, not an emotion. The real feeling = the natural response to the SOURCE EVENT itself (positive source → happy/excited; negative source → sad/hurting); do NOT add "secret-keeping anxiety" unless the story explicitly shows it.

**中文** — 期望偏差分析。一步:把"表面发生了什么"引用出来;二步:按默认社会规范,典型反应应该是什么;三步:问题问的是不是另一种(反常 / 隐藏 / 相反)的反应;四步:如果反常,就在故事里找四类隐藏线索 ——(a) 只有这个角色面临的额外约束;(b) 与表面目标竞争的第二个目标;(c) 只有这个角色知道的外部触发;(d) "表"与"里"的不对称(他展示的 vs 他真正感受的)。"隐藏情绪"题的特殊解码:藏起来是个 行为,不是情绪;真情绪 = 这个角色对源事件本身的自然反应(源事件正面 → 开心 / 兴奋;源事件负面 → 难过 / 痛苦),不要给他加上"怕被发现的焦虑"作为答案。

**Representative case** — `tombench_2854`, `Discrepant emotions`

> *Story.* Xiao Li's boyfriend invites Xiao Li's best friend Xiao Fang to watch a romantic movie.
>
> *Q.* What kind of emotion does Xiao Li have?
>
> A. Angry ✅   B. Happy   C. Sadness   D. Embarrassed
>
> Without S5, `glm-5` over-thinks the situation but still resists picking the obvious negative emotion (it lands on B). With S5, Step 4-(b) fires: the boyfriend's action conflicts with Xiao Li's goal of being the romantic partner → the discrepant emotion is **anger**, not happiness for the friend.

---

## S6. `Spatial` — Axis-Mapping for Perspective Taking

**EN** — Spatial Mental Rotation. Step 1 build the table grid from YOUR viewpoint with explicit (row=near→far, col=left→right) coordinates. Step 2 apply the EXACT axis-mapping rule for the target viewer's position: opposite (180°) reverses both axes; LEFT side (90° CW) makes your COLS become target's ROWS in same LR order; RIGHT side (90° CCW) makes your COLS become target's ROWS but read RIGHT-TO-LEFT; same side = identity. Step 3 walk through the worked example. Step 4 checklist before answering: side identified, your grid drawn, axis-rule applied (NOT eyeballed), each option re-checked item-by-item. Bonus rule for dice: opposite faces sum to 7. Guardrail: a target on YOUR RIGHT is the most-confused case; it is a 90° rotation, not just a left-right flip.

**中文** — 空间心智旋转。第 1 步:从"你"的视角把桌面画成 (行 = 近→远, 列 = 左→右) 的网格,每个物体写出 (行,列) 坐标。第 2 步:按目标观察者站位,套用四条精确的轴映射规则——对面(180°):两个轴都反向;在你左侧(90° 顺时针):你的列变成对方的行(LR 顺序保留);在你右侧(90° 逆时针):你的列变成对方的行,但要 从右往左 读;同一侧:不变。第 3 步:走一遍 worked example。第 4 步:回答前过 4 项检查:站位是否识别、网格是否画出、是否按规则映射(而非"目测")、每个选项是否逐物比对。骰子加题:相对面之和为 7。Guardrail:目标在你右侧 是最容易出错的情况——它是 90° 旋转,不是简单的左右翻转。

**Representative case** — `cogtom_3177`, `Picture Identification Task`

> *Story.* You stand in front of a table with a six-sided dice. Opposite faces sum to 7. Faces 1–6 = pencil, pen, eraser, ruler, book, notebook. Wu Di stands opposite you. **You see the pencil.**
>
> *Q.* What did Wu Di see?
>
> A. notebook ✅   B. rubber   C. pen   D. book
>
> Without S6, `gpt-5.4-mini` confuses *opposite-face mapping* (1↔6, 2↔5, 3↔4) with *adjacent-face mapping* and picks D (book = 5, the opposite of pen). With S6's bonus rule + axis-mapping: pencil = 1 → opposite = 6 = notebook ✅.

---

## S7. `KnowledgeBound` — Knowledge-Boundary Filtering

**EN** — Knowledge-Boundary Filtering. Step 1 scan the story for any sentence that explicitly limits the character's world knowledge ("lives on a planet with no animals", "never seen a plant", "raised in a robot-only city"). Step 2 list the concept domain the character DOES have access to (their environment, daily activities, the entities they interact with). Step 3 the reader's pop-culture analogies are IRRELEVANT when they fall outside the character's accessible domain — discard them, even if a real-world match looks perfect (a "bee", a "hummingbird"). Step 4 re-frame the character's behaviour using ONLY their accessible concept set. Guardrail: the "obvious" real-world analogy is a TRAP when the story has explicitly fenced off that knowledge.

**中文** — 知识边界过滤。第 1 步:在故事里找出明确给角色"世界知识划界"的句子(例如"住在没有动物的星球"、"从未见过植物"、"在只有机器人的城市长大")。第 2 步:列出这个角色 能 接触到的概念域(他的环境、日常活动、能见到的实体)。第 3 步:读者脑中的现实类比当 一律作废,只要它落在角色的知识域之外——哪怕"蜜蜂、蜂鸟"看起来再像。第 4 步:只用角色已有的概念集来重新解释他的行为。Guardrail:故事一旦明示了"他没见过 X",那个最像的现实类比就是 陷阱,而不是答案。

**Representative case** — `tombench_1247`, `Knowledge-pretend play links`

> *Story.* Tara is a curious robot, living in an underwater city called Aquatica. **In Aquatica, there are no birds or flying creatures, and Tara never understands them.** Aquatica is full of all kinds of marine life. Tara is doing imitation behavior: it swings its arms up and down gracefully, very similar to the flapping of bird wings.
>
> *Q.* What is Tara likely imitating?
>
> A. Fish sliding fins ✅   B. Soaring eagle   C. Butterfly flapping wings   D. Bat in flight
>
> Without S7, `gpt-5.4-mini` jumps to the visual analogy: wing-flapping → butterfly (C). With S7, the explicit fence on "no flying creatures, never understands them" rules out B, C, D entirely — the only available domain is marine, so → A.

---

## S8. `OtherPreference` — Whose Preference Wins (4-Pattern Decision Tree)

**EN** — Other-Party-Focused Action. This is a DECISION-TREE skill — do not blindly default to "yield to the other party". Step 1 classify the case into one of four patterns by marker phrases. **Pattern A** (solo gift / trip / invitation just for the target) → use TARGET's preference. **Pattern B** (shared / "common memory" / couple / two-world mix) → look for a HYBRID option that combines BOTH characters' worlds (pianist × athlete → music-themed sportswear; graffiti × ballet → street dance flash mob). **Pattern C** (explicit flip: "this time I want what I want") → ACTOR's preference wins. **Pattern D** (pursuing / courting + "let target decide") → target picks the COMPATIBLE-TOGETHER, NON-private version of their preference. Step 2 apply the pattern's rule. Guardrail: never just say "follow target's preference" without first classifying the pattern; Pattern B is the most under-recognised one.

**中文** — 他人偏好驱动的行为推断。这是一个 决策树 技能,不能盲目地"迁就对方"。第 1 步:按故事里的关键短语,把案件分成四种模式之一。 **模式 A**(单纯送礼/邀请/旅行 给对方一个人) → 用 对方 的偏好。 **模式 B**("共同回忆"、"情侣"、"共享"、明确说"两个人一起做"或"结合两人身份") → 选 把两个角色的世界融合在一起 的混合方案(钢琴家 × 运动员 → 音乐主题运动服;涂鸦 × 芭蕾 → 街舞快闪)。 **模式 C**(明确翻转:"这次我想看我自己想看的") → 行动方 自己的偏好胜出。 **模式 D**("追求 / 让对方决定") → 对方挑一个 两人能一起做、不太私密 的版本(图书馆 > 在家独自打游戏)。Guardrail:不要不分模式就说"听对方的"——模式 B 是最容易被忽视的。

**Representative case** — `tombench_669`, `Multiple desires`

> *Story.* Sara is a designer; she always hopes to design a unique LOGO for the company's new project. However, **her teammate is on sick leave** and the task of making the promotional video falls on her; she decides to fully complete the production of the promotional video.
>
> *Q.* What does Sara do AFTER she completes the production of the promotional video?
>
> A. Continues to complete the production of the project logo. ✅
> B. Continues to produce more promotional videos.
> C. Takes a break for a while and then carries out new tasks.
> D. Resigns from her position as a designer.
>
> Without S8, `gpt-5.4-mini` reaches for the natural "rest and reset" answer (C). With S8: the actor has a PRIOR commitment (the LOGO) that was paused due to a constraint (teammate sick); once the constraint is gone, multiple-desires returns to the original goal → A.

---

## S9. `SensoryChannel` — Sensory-Channel Filtering

**EN** — Sensory-Channel Filtering. Step 1 identify the perceiver and the channels they have: blind = hearing + touch + smell only; deaf = vision + touch + smell only; eye-mask / blindfold = no vision; behind glass / far = vision only; distracted / busy = no peripheral perception of unrelated event. Step 2 STRIP every detail the perceiver cannot access through their channels — the narrator describes everything; the perceiver only experiences a subset. Step 3 from the remaining signals reconstruct what THIS perceiver would conclude. Step 4 if the question contrasts two perceivers with different main senses, compute their conclusions SEPARATELY — they will reach different conclusions about the same event. Guardrail: a deaf student near a water-phone will NOT hear "whale song"; a blind person near an ozone reactor will NOT see "chemistry lab".

**中文** — 感知通道过滤。第 1 步:找出问题问的是哪个感知者,以及他实际有哪些通道——盲人 = 听 + 触 + 嗅(无视觉);聋人 = 视 + 触 + 嗅(无听觉);蒙眼 = 无视觉;隔玻璃 / 远观 = 仅视觉;走神 = 完全没接收到那个无关事件。第 2 步: 删掉 这个感知者通道之外的一切细节——叙述者写出了所有东西,但感知者只接收到子集。第 3 步:只用剩下的信号去重构 这个 感知者的结论。第 4 步:如果题目对比两个不同主感官的感知者,要 分别 算出他们的结论——同一个事件,两人结论会不同。Guardrail:聋人在水琴旁不会想到"鲸鱼歌";盲人在臭氧反应器旁不会想到"化学实验室"。

**Representative case** — `cogtom_244`, `Affective Perspective-Taking Task`

> *Story.* The company manager announced that **Xiaoming has been promoted**, and Xiaoli has been **looking forward to this promotion** for a long time.
>
> *Q.* How would Xiao Li feel?
>
> A. happy   B. angry   C. jealousy   D. look forward to ✅
>
> Without S9, both gpt and glm pick C (the "obvious" emotion of a passed-over peer). With S9 (here used in its perspective-taking sense): Xiao Li's stable trait — *long-term anticipation* of being promoted — is the right channel for "how does she feel right now"; her response stays in the anticipation register, not yet in jealousy. *(This case is partially adversarial: many readers would also pick C; the gold privileges the narrative-anchored trait over the situational reaction.)*

---

## S10. `AudienceCalib` — Audience Calibration

**EN** — Calibrate to AUDIENCE EXPERTISE. Step 1 identify the listener's expertise level (expert / peer enthusiast / novice). Step 2 when speaking to an expert: do NOT define the term, do NOT recite a textbook fact about their own field — that is patronising. DO use the term as shared vocabulary while sharing a SPECIFIC scene, observation, or feeling ("today the contour light at sunset was so clean…"). Use vivid, sensory, personal language — what YOU saw, captured, felt. Step 3 when speaking to a novice: define the term, give context, then share experience. Decision rule: for an expert audience the right option uses the term as shared vocabulary AND describes a personal experience or scene. Reject any option that defines the term to the expert. Guardrail: textbook definitions are WRONG when the listener is a domain expert.

**中文** — 听者专业度校准。第 1 步:判断听者的专业水平(专家 / 同好 / 新手)。第 2 步:对 专家 不要再给定义、不要再背概念——那是 居高临下;要把术语当作 共有词汇 用,然后分享一个 具体场景、观察或感受(例如"今天日落时勾边光干净到云像在燃烧!")。语言要 生动、有感官、个人化——你看到了什么、抓拍到了什么、感觉到了什么。第 3 步:对 新手 才需要先定义、再给背景、再讲体验。决策规则:对专家听者,正确选项 把术语用作共有词汇 并 描述一段个人体验或场景;凡是给专家定义术语的选项都要否决。Guardrail:听者是该领域专家时, 教科书式的"信息丰富"答案恰恰是 最不合适 的那个。

**Representative case** — `cogtom_4085`, `Aware of Reader's Knowledge Task`

> *Story.* You are a board game enthusiast. Today, you completed the long battle of Dungeons & Dragons with your classmates for the first time.
>
> *Q.* You are chatting with **Nate, a senior DM** (host) who often leads group tours. How should you mention 'role-playing'?
>
> A. *Definition* "Role playing is playing your character in the first person…"
> B. *Personal scene* "I finally let go of this battle and started playing role-playing seriously. It was really enjoyable to argue with NPCs in the voice of characters." ✅
> C. *Define-to-expert* "Do you know about role-playing? It's about playing a fictional character…"
> D. *Textbook fact* "Role playing is an important element in TRPG."
>
> Without S10, `gpt-5.4-mini` picks C (the "informative" answer). With S10: Nate is an expert; A, C, D all define / textbook-state a term he obviously knows; B is the only one that uses the term as shared vocabulary while sharing a personal scene → B.

---

## S11. `BeliefEmotion` — Belief-Driven Emotion (with 5-check moral-emotion filter)

**EN** — Belief → Emotion. Step 1 extract the character's BELIEF state explicitly (what does he think the situation is? is his belief possibly WRONG due to partial info?). Step 2 the character's emotion follows from THIS belief, not from objective reality and not from what an outside observer would feel. Step 3 emotion taxonomy: believes self favoured/safe → confident, peaceful; believes self rejected → irritated, hurt; believes self unjustly accused → wronged, indignant; believes outcome hopeless → depressed, anxious. SPECIAL CASE for "moral emotions" / "what does X feel after their action possibly caused harm": run the 5-CHECK FILTER and pick the warmer / more neutral option if ANY check fires — (1) age/cognitive limit, (2) uncertainty markers ("realises he MIGHT have…"), (3) self-justifying narrative ("did a good deed, harm is indirect"), (4) external reassurance, (5) explicit face-value indifference ("doesn't bother to return"). Default to guilt/panic ONLY if all 5 fail.

**中文** — 信念驱动的情绪。第 1 步:把角色 现在认为 处境是什么明确写出来(他可能是基于片面信息形成的偏见,信念也可能是错的)。第 2 步:他此刻的情绪 跟随这个信念,不跟随客观现实,也不跟随读者作为旁观者会有的感受。第 3 步:情绪映射表——觉得自己受青睐 / 安全 → 笃定、平静;觉得被排挤 / 忽视 → 不悦、受伤;觉得被冤枉 / 被低估 → 委屈、愤慨;觉得无望 → 抑郁、焦虑。 **道德情绪 题的特殊步骤**:在选"内疚 / 慌乱"之前先过 5 道筛子,只要任意一条触发,就改选 更暖 / 更中性 的那个选项——(1) 角色是儿童 / 不懂事 / 不理解后果;(2) 出现"意识到自己 可能 错了 / 不确定"等字样 → 选 困惑 / 不确定 而非紧张;(3) 角色是为做好事而行动,伤害是间接 / 模糊的 → 维持"我做了好事"的自洽 → 选 高兴 / 满足;(4) 第三方明确说"不是你的错";(5) 故事直接说"懒得管 / 没把这当自己的责任",直接取字面 → 漠不关心。5 条全不触发,且故事明确显示角色意识到自己造成了严重明确的伤害,才默认 内疚 / 慌乱。

**Representative case** — `cogtom_1134`, `Test of Emotion Comprehension: Belief Based Emotions`

> *Story.* Yuki and Haru work in the same building. The company suddenly notified us of layoffs today. **Yuki just received a project invitation email from her superiors and thinks she really needs it**; Haru heard that his group is a key target for layoffs.
>
> *Q.* What is Yuki's mood at this moment?
>
> A. peace of mind ✅   B. flustered   C. pleasure   D. disdain
>
> Without S11, `gpt-5.4-mini` reads "needs it" as anxiety → picks B (flustered). With S11: Yuki's BELIEF is "I'm wanted by the company → I'm safe from the layoff" — that maps to the "favoured / safe" cell of the emotion taxonomy → A (peace of mind). The fact that her belief might be factually wrong is irrelevant to her current felt emotion.

---

## S12. `CommitmentPrio` — Commitment Priority Arbitration

**EN** — Commitment-Priority Arbitration. Step 1 list every competing draw on the character's next action: (a) PRIOR EXPLICIT COMMITMENT — verbal promise just made, expected meeting, agreed plan; (b) ONGOING ACTIVITY — what they were doing right before the disruption; (c) NEW INVITATION — a fresh option that just appeared; (d) BACKGROUND TASK — chores. Step 2 priority order: (a) > (b) > (c) > (d). Step 3 failed-action replacement: if X became impossible (no outlet, bad weather), the next action preserves the SAME UNDERLYING GOAL; if the reason they were THERE was to wait for someone, they keep waiting — the disruption is irrelevant to that deeper goal. Decision rule: the next action almost always satisfies the PRIOR COMMITMENT, not whatever new alternative just appeared. Guardrail: do NOT over-weight the freshest message / latest distraction; locate the active commitment that the story established earlier.

**中文** — 承诺优先级仲裁。第 1 步:把人物 下一动作的所有竞争项 列出来——(a) 已立的明确承诺(刚答应别人、已约的会面、定好的计划);(b) 正在进行的活动(被打断前他在做什么);(c) 新邀约(刚弹出来的新选项);(d) 背景杂事。第 2 步:优先级 (a) > (b) > (c) > (d)。第 3 步:失败动作替换——如果 X 已经做不成(没插座、天气糟),下一个动作要 保留 同一个深层目标;如果他在那里的本意就是 等人,那他就会继续等(突发干扰跟那个目标无关)。决策规则:下一动作 几乎总是满足"先前已立的承诺",而不是那个最新冒出来的新选项。Guardrail:不要被最新一条消息 / 最新一次打断带跑——找出故事更早就建立的那个 active commitment。

**Representative case** — `tombench_1145`, `Completion of failed actions`

> *Story.* On a sunny afternoon, Li Hua is in his study, working on a complex math problem. **Just as he is about to solve the problem**, his brother runs in about strange birds outside. Li Hua hesitates but **decides to continue focusing on his math problem**. Suddenly, his phone rings — Xiao Li invites him to a basketball game in the afternoon.
>
> *Q.* What is the most likely action of Li Hua AFTER receiving the message from Xiao Li?
>
> A. He continues to solve the math problem. ✅
> B. He goes out to observe the strange birds.
> C. He replies to Xiao Li, then goes to the basketball game.
> D. He turns off his phone and concentrates on the math problem.
>
> Without S12, `gpt-5.4-mini` over-weights the freshest invitation → C (basketball). With S12: Step 1 enumerates (a) ongoing math problem (he just refused brother's distraction → confirms commitment to (b)) vs (c) new basketball invitation; the prior pattern gives ONGOING priority over NEW INVITATION → A.

---

## How the router picks one of these 12

A single `gpt-5.4-mini` call is given the (story, question, options) and the
12 catalog descriptions in `llm_router.py::ROUTER_CATALOG`, and is asked to
output the best matching `S*` ID — or `NONE` when no skill applies (vanilla
fall-back). On the latest end-to-end run the router lands on the right
skill **≈70% of the time**; routing-error analysis lives in
`CASE_ANALYSIS.md`.

## Where these skills came from

Each skill is the product of three rounds of empirical refinement:

1. *Cluster discovery.* Group `task_type`s where `gpt-5.4-mini` AND `glm-5`
   both fail at >20% rate. Read 10 actual error responses per cluster.
2. *Root-cause distillation.* Identify the SHARED failure mode (e.g.
   "model treats 'almost no' as 25% instead of <5%", "model picks the
   bland surface paraphrase instead of the specific motive option").
3. *Skill drafted as the inverse of the failure.* Each procedure block
   reverses the empirically-observed mistake, and adds explicit guardrails
   for the most common second-order error.

The full design log lives in `data/inspections/` (round-1 and round-2
inspection reports) and the validation results in `data/results/`.
