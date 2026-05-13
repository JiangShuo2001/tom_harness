# Failure-mode inspection


## Group: `S5→S11_confusion`  (8 cases)

### tombench_1053   task_type=`Hidden emotions`
- oracle skill : **S5_Expectation**
- vanilla pred : B
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **A**  (gold = **A**)  ✓ FIXED
- with ORACLE skill: pred = **B**  ✗ still wrong

**Story**

> Nana helps her mother, her mother says she can stay up late to watch TV. Her little brother also wants to stay up late, so her mother says she cannot tell her brother because her brother is very young, he should go to bed early.

**Question:** What is Nana's real feeling?

**Options:**
- A. Happy
- B. Guilty
- C. Calm
- D. Annoyed

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Nana believes she has been allowed to stay up late as a reward for helping, so her emotion is positive and satisfied. She is not being blamed or rejected, and there’s no reason for guilt. The best match is **happy**.

Answer: A
```

**Answerer's reasoning (with ORACLE skill):**

```
1. **Surface event:** Nana is allowed to stay up late, but she’s told not to tell her younger brother because “he is very young” and must go to bed early.

2. **Expected reaction:** She would likely feel **happy** about getting permission to stay up late.

3. **Actual / asked reaction:** The question asks for Nana’s **real feeling**, which is likely the hidden reaction to being asked to keep a secret from her brother.

4. **Hidden context search:** The key hidden factor is that Nana has to **withhold the information** from her younger brother, which can make her feel **guilty** even though she gets what she wants.

5. **Decision:** The best choice is **guilty**.

Answer: B
```


---

### tombench_1093   task_type=`Hidden emotions`
- oracle skill : **S5_Expectation**
- vanilla pred : A
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **C**  (gold = **A**)  ✗ wrong
- with ORACLE skill: pred = **C**  ✗ still wrong

**Story**

> Xinxin wants to go to her friend's party tonight, but she has a stomachache. She knows, if she tells her mother she has a stomachache, her mother does not let her go. She tries to hide her feelings, so her mother lets her go to the party.

**Question:** What are Xinxin's real feelings?

**Options:**
- A. Sad
- B. Scared
- C. Happy
- D. Disappointed

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Xinxin believes that if her mother knew about the stomachache, she would be denied the party, so she hides it and gets to go. Her emotion matches her belief about getting what she wants: she is happy.

Answer: C
```

**Answerer's reasoning (with ORACLE skill):**

```
Xinxin wants to go to the party, and she hides her stomachache so her mother will let her go. Even though she’s concealing discomfort, her real feeling about getting to attend the party is positive.

Answer: C
```


---

### tombench_1376   task_type=`Hidden emotions`
- oracle skill : **S5_Expectation**
- vanilla pred : D
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **B**  (gold = **C**)  ✗ wrong
- with ORACLE skill: pred = **D**  ✗ still wrong

**Story**

> Zhou Yu wants to go out, but he feels stomachache. He knows, if he tells his mother he has a stomachache, his mother says he cannot go out. He tries to hide his feelings, letting his mother let him go out of the house.

**Question:** What are Zhou Yu's real feelings?

**Options:**
- A. Angry
- B. Happy
- C. Sad
- D. Anxious

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Zhou Yu believes that if he admits his stomachache, he will be denied going out, so he is trying to hide it in order to get his way. His current feeling is best matched by wanting to go out and feeling good about that possibility, not sadness or anger.  

Answer: B
```

**Answerer's reasoning (with ORACLE skill):**

```
Zhou Yu is outwardly trying to hide his stomachache so he can still go out, but inside he likely feels worried about being unable to go. That hidden emotion best matches **anxious**.

Answer: D
```


---

### tombench_1888   task_type=`Hidden emotions`
- oracle skill : **S5_Expectation**
- vanilla pred : A
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **A**  (gold = **A**)  ✓ FIXED
- with ORACLE skill: pred = **A**  ✓ would-fix

**Story**

> Break time comes. Mengmeng's friends are chatting and telling jokes in a group. Someone tells a joke that everyone thinks is funny. Mengmeng does not understand this joke, but she does not want other children to know.

**Question:** What does Mengmeng feel?

**Options:**
- A. Sad
- B. Angry
- C. Happy
- D. Guilty

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Mengmeng believes she is missing out and wants to hide that she doesn’t understand the joke. That usually leads to feeling embarrassed or upset rather than happy or guilty. Among the options, **sad** fits best.

Answer: A
```

**Answerer's reasoning (with ORACLE skill):**

```
Mengmeng is hiding that she doesn’t understand the joke, so outwardly she may act normal, but inside she would likely feel unhappy/embarrassed. Among the options, the best match is **sad**.

Answer: A
```


---

### tombench_1999   task_type=`Hidden emotions`
- oracle skill : **S5_Expectation**
- vanilla pred : D
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **A**  (gold = **C**)  ✗ wrong
- with ORACLE skill: pred = **D**  ✗ still wrong

**Story**

> Lili helps her father fix the water pipe in the garden, her father is happy, and promises to buy her a toy. However, her father says if her younger brother knows, he follows, he needs to take a nap, you do not tell your younger brother. Lili sees her younger brother.

**Question:** What is Lili's real feeling?

**Options:**
- A. Anxious
- B. Calm
- C. Happy
- D. Worried

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Lili believes she has a secret promise from her father and also sees her younger brother, who must not know. That puts her in a potentially risky situation, so her feeling is best matched by anxiety/worry rather than happiness or calm.

Answer: A
```

**Answerer's reasoning (with ORACLE skill):**

```
Lili has a hidden constraint: she must not let her younger brother know, so when she sees him, her outward situation is tense rather than purely happy. The most fitting real feeling is **worried**.

Answer: D
```


---

### tombench_308   task_type=`Hidden emotions`
- oracle skill : **S5_Expectation**
- vanilla pred : D
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **D**  (gold = **C**)  ✗ wrong
- with ORACLE skill: pred = **A**  ✗ still wrong

**Story**

> Lili helps her father fix the water pipe in the garden, her father is happy, and promises to buy her a toy. However, her father says if her younger brother knows, he follows, he needs to take a nap, you do not tell your younger brother. Lili sees her younger brother.

**Question:** What is Lili's real feeling?

**Options:**
- A. Anxious
- B. Calm
- C. Happy
- D. Worried

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Lili’s belief is that she must not tell her younger brother, but now she sees him, so she may think the secret could be discovered and the situation could go wrong. That points to a worried feeling rather than happy or calm.

Answer: D
```

**Answerer's reasoning (with ORACLE skill):**

```
Lili has a hidden constraint: she was told not to let her younger brother know, but now she sees him. That would make her feel uneasy about keeping the secret and avoiding trouble.

Answer: A
```


---

### tombench_386   task_type=`Hidden emotions`
- oracle skill : **S5_Expectation**
- vanilla pred : D
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **D**  (gold = **C**)  ✗ wrong
- with ORACLE skill: pred = **D**  ✗ still wrong

**Story**

> Lili helps her father fix the water pipe in the garden, her father is happy, and promises to buy her a toy. However, her father says if her younger brother knows, he follows, he needs to take a nap, you do not tell your younger brother. Lili sees her younger brother.

**Question:** What is Lili's real feeling?

**Options:**
- A. Anxious
- B. Calm
- C. Happy
- D. Worried

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Lili believes she must not tell her younger brother, but she sees him and may worry about the situation. Her current feeling is best matched by **worried**.

Answer: D
```

**Answerer's reasoning (with ORACLE skill):**

```
Surface event: Lili’s father is happy and promises her a toy, but he also says, “you do not tell your younger brother,” and Lili then sees her younger brother.

Expected reaction: She would typically feel happy about the promise.

Actual/asked reaction: The question asks for her real feeling, which is likely a hidden, tense feeling because she has to keep a secret and may worry about her brother finding out.

Hidden context: There is a rule/secret she must manage, creating worry rather than simple happiness.

Answer: D
```


---

### tombench_882   task_type=`Hidden emotions`
- oracle skill : **S5_Expectation**
- vanilla pred : C
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **A**  (gold = **A**)  ✓ FIXED
- with ORACLE skill: pred = **A**  ✓ would-fix

**Story**

> Feifei is playing a card game. When she gets the cards, she sees that these cards are good, so she may win. But she tries not to let other children know what good cards she has.

**Question:** What is Feifei's real feeling?

**Options:**
- A. Excited
- B. Proud
- C. Anxious
- D. Grateful

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Feifei believes she has good cards and may win, so her emotion is positive and energized. She’s trying to hide it from others, which suggests excitement more than pride, anxiety, or gratitude.

Answer: A
```

**Answerer's reasoning (with ORACLE skill):**

```
Surface event: “she sees that these cards are good, so she may win” but “she tries not to let other children know.”

Expected reaction: She would likely look happy or excited about having strong cards.

Actual / asked reaction: The question asks for her real feeling, behind the hidden expression.

Hidden context: She is suppressing her emotion to avoid revealing her advantage.

Decision: Her real feeling is **excited**.

Answer: A
```


---


## Group: `S8_DiscrepantDesires_unfixed`  (8 cases)

### tombench_1621   task_type=`Discrepant desires`
- oracle skill : **S8_OtherPreference**
- vanilla pred : A
- router picked: **S8_OtherPreference** (prev run: S8_OtherPreference)
- answered     : **A**  (gold = **B**)  ✗ wrong
- with ORACLE skill: pred = **A**  ✗ still wrong

**Story**

> Li Hua is a photographer who is passionate about outdoor adventures. He often spends his weekends hiking or climbing in the mountains, pursuing those rare natural landscapes. His friend Wang Min is an interior designer who prefers indoor activities, especially visiting art exhibitions and design expos. This weekend, Wang Min wants to invite Li Hua to spend together.

**Question:** To make this weekend enjoyable, where should Wang Min suggest going?

**Options:**
- A. Natural Scenic Area
- B. Natural Landscape Photography Exhibition
- C. Interior Design Expo
- D. City Shopping Center

**Router's full response (after seeing case):**

```
Skill: S8_OtherPreference
```

**Answerer's reasoning (with router's chosen skill):**

```
Wang Min should suggest something that fits Li Hua’s preference for outdoor adventures and natural landscapes, since he is the one being invited. Among the options, a Natural Scenic Area best matches that.

Answer: A
```

**Answerer's reasoning (with ORACLE skill):**

```
Wang Min should suggest an activity that fits Li Hua’s preference, since she is the one inviting him to spend time together. Li Hua enjoys outdoor adventures and natural landscapes, so the best choice is a natural scenic area.

Answer: A
```


---

### tombench_1635   task_type=`Discrepant desires`
- oracle skill : **S8_OtherPreference**
- vanilla pred : D
- router picked: **S8_OtherPreference** (prev run: S8_OtherPreference)
- answered     : **D**  (gold = **C**)  ✗ wrong
- with ORACLE skill: pred = **D**  ✗ still wrong

**Story**

> Zhang Wei is a professional basketball player, his life is full of training and games, he believes that sports competition and team spirit are important parts of life. His wife, Li Na, is a famous pianist, her life is full of music and performances, she believes that art and music are the core of human emotional expression. They are about to celebrate their wedding anniversary. Zhang Wei wants to prepare a surprise for Li Na for this special day, and also prepares a gift for himself that echoes it, as their common memory.

**Question:** What gift does Zhang Wei most likely prepare for Li Na?

**Options:**
- A. Professional basketball equipment
- B. High-end concert evening dress
- C. Customized music-themed sportswear
- D. Fashion brand piano accessory package

**Router's full response (after seeing case):**

```
Skill: S8_OtherPreference
```

**Answerer's reasoning (with router's chosen skill):**

```
Zhang Wei should choose something that matches Li Na’s identity and preferences as a pianist, not his own basketball interests. Among the options, a piano-related gift best fits her.

Answer: D
```

**Answerer's reasoning (with ORACLE skill):**

```
Zhang Wei is preparing a surprise for Li Na, so he should choose something that fits her identity and interests as a pianist, while also echoing his own basketball world in some shared-memory way. Among the options, the best gift for Li Na is a piano-related accessory package from a fashion brand.

Answer: D
```


---

### tombench_2178   task_type=`Discrepant desires`
- oracle skill : **S8_OtherPreference**
- vanilla pred : D
- router picked: **S8_OtherPreference** (prev run: S8_OtherPreference)
- answered     : **D**  (gold = **B**)  ✗ wrong
- with ORACLE skill: pred = **D**  ✗ still wrong

**Story**

> Xiao Li is a professional ballet dancer. She trains and performs hard every day, believing that the pure beauty of dance and strict self-discipline are the core of her life. On the other hand, Xiao Zhang is a street graffiti artist. His works are full of color and free expression, believing that art should be free and unrestricted. One day, Xiao Zhang invites Xiao Li to an event.

**Question:** What type of event does Xiao Zhang most likely invite Xiao Li to?

**Options:**
- A. Ballet performance
- B. Street dance flash mob event
- C. Exciting modern dance performance
- D. Street graffiti event

**Router's full response (after seeing case):**

```
Skill: S8_OtherPreference
```

**Answerer's reasoning (with router's chosen skill):**

```
Xiao Zhang is a street graffiti artist who values free expression and unrestricted art, so he would most likely invite Xiao Li to an event related to street graffiti rather than ballet.  

Answer: D
```

**Answerer's reasoning (with ORACLE skill):**

```
Xiao Zhang is a street graffiti artist who values free, unrestricted artistic expression, so he would most likely invite Xiao Li to an event related to street art rather than ballet. The best match is a street graffiti event.

Answer: D
```


---

### tombench_2353   task_type=`Discrepant desires`
- oracle skill : **S8_OtherPreference**
- vanilla pred : B
- router picked: **S8_OtherPreference** (prev run: S8_OtherPreference)
- answered     : **B**  (gold = **A**)  ✗ wrong
- with ORACLE skill: pred = **B**  ✗ still wrong

**Story**

> Zhao Ting is a traveler who loves nature and camping in the wild. She likes to hike in nature, especially in forests and national parks. On the other hand, her suitor Liu Bo prefers city travel and cultural exploration. He is keen on visiting historic cities, museums, and art exhibitions. He thinks the meaning of travel is to understand different cultures and histories. This holiday, Liu Bo invites Zhao Ting to travel together.

**Question:** Where does Liu Bo most likely invite Zhao Ting to go?

**Options:**
- A. Hiking in the national park
- B. Touring historic cities
- C. Visiting art museums
- D. City cultural festival activities

**Router's full response (after seeing case):**

```
Skill: S8_OtherPreference
```

**Answerer's reasoning (with router's chosen skill):**

```
Liu Bo should choose a destination that matches Zhao Ting’s likely preference for a shared trip? Wait: the story says Liu Bo prefers city/cultural exploration, and he invites Zhao Ting to travel together. Since he is the actor inviting, he will likely choose something aligned with his own preference unless constrained otherwise. Among the options, the best fit for his preference is touring historic cities or visiting museums. The most direct match is touring historic cities.

Answer: B
```

**Answerer's reasoning (with ORACLE skill):**

```
Liu Bo’s own preference is city travel and cultural exploration, and since he is inviting Zhao Ting to travel together, he is most likely to choose a destination that fits his interests. Among the options, touring historic cities best matches that preference.

Answer: B
```


---

### tombench_2514   task_type=`Discrepant desires`
- oracle skill : **S8_OtherPreference**
- vanilla pred : D
- router picked: **S8_OtherPreference** (prev run: S8_OtherPreference)
- answered     : **D**  (gold = **C**)  ✗ wrong
- with ORACLE skill: pred = **D**  ✗ still wrong

**Story**

> Wang Wu is a person who loves outdoor sports, he goes to play ball or climb mountains every weekend, pursuing excitement and challenge. Li Min is completely opposite, she is a homebody, likes to read books or play video games at home on weekends, enjoying peace and ease. Wang Wu wants to pursue Li Min. This weekend, Wang Wu wants to invite Li Min to go out together, and proposes to let Li Min decide the place to go.

**Question:** Facing Wang Wu's invitation, where does Li Min most likely choose to go?

**Options:**
- A. Shopping center
- B. Exhibition
- C. Library
- D. Play games at home

**Router's full response (after seeing case):**

```
Skill: S8_OtherPreference
```

**Answerer's reasoning (with router's chosen skill):**

```
Li Min is a homebody who prefers quiet indoor activities like reading books or playing video games at home. Since Wang Wu lets her decide, she will most likely choose an option that matches her own preference, especially staying indoors.

Answer: D
```

**Answerer's reasoning (with ORACLE skill):**

```
Li Min is a homebody who prefers quiet, relaxing indoor activities like reading books or playing video games at home. Since Wang Wu lets her decide, she will most likely choose the option that best fits her own preference and comfort.

Answer: D
```


---

### tombench_2558   task_type=`Discrepant desires`
- oracle skill : **S8_OtherPreference**
- vanilla pred : D
- router picked: **S8_OtherPreference** (prev run: S8_OtherPreference)
- answered     : **C**  (gold = **D**)  ✗ wrong
- with ORACLE skill: pred = **C**  ✗ still wrong

**Story**

> Chen Chen is a fitness enthusiast, her lifestyle strictly follows healthy eating and regular exercise. Every weekend, she spends time in the gym or participates in outdoor sports. On the other hand, Li Lei is a foodie, his life is full of various food explorations, especially various desserts and fast food. He thinks the fun of life is in tasting different foods. This holiday, Chen Chen decides to invite Li Lei to an event.

**Question:** What activity does Chen Chen most likely invite Li Lei to participate in?

**Options:**
- A. Outdoor barbecue
- B. Tasting at a newly opened fried chicken shop
- C. Dessert shop tasting
- D. City exploration activity

**Router's full response (after seeing case):**

```
Skill: S8_OtherPreference
```

**Answerer's reasoning (with router's chosen skill):**

```
Chen Chen is inviting Li Lei, so the activity should fit Li Lei’s foodie preference, especially desserts and fast food. Among the options, a dessert shop tasting best matches that preference.

Answer: C
```

**Answerer's reasoning (with ORACLE skill):**

```
Chen Chen should adapt to Li Lei’s preference as the invitee, and Li Lei especially enjoys desserts and fast food. Among the options, a dessert shop tasting best matches his interests.

Answer: C
```


---

### tombench_2859   task_type=`Discrepant desires`
- oracle skill : **S8_OtherPreference**
- vanilla pred : A
- router picked: **S8_OtherPreference** (prev run: S8_OtherPreference)
- answered     : **A**  (gold = **B**)  ✗ wrong
- with ORACLE skill: pred = **A**  ✗ still wrong

**Story**

> Li Ming is a TV drama fan, especially likes to watch suspense and crime series. On the other hand, his roommate Zhao Li is a loyal fan of reality shows, she likes to watch various reality shows and lifestyle programs, thinks these programs are more close to life, relaxed and interesting. In the choice of TV programs, Li Ming always gives way to Zhao Li. Tonight, the two sit in the living room together, Li Ming expresses he wants to watch what he wants to watch, but there is only one TV, facing the choice of what type of program to watch.

**Question:** That night, what type of TV program do Li Ming and Zhao Li most likely watch together?

**Options:**
- A. Challenge obstacle course reality show
- B. Suspense crime TV drama
- C. Exciting knowledge quiz program
- D. News report on criminal cases

**Router's full response (after seeing case):**

```
Skill: S8_OtherPreference
```

**Answerer's reasoning (with router's chosen skill):**

```
Zhao Li’s preference is the key here: she likes reality shows and lifestyle programs, and Li Ming usually gives way to her. So they most likely watch a reality show.

Answer: A
```

**Answerer's reasoning (with ORACLE skill):**

```
Li Ming prefers suspense/crime dramas, but the story says he usually gives way to Zhao Li, and Zhao Li prefers reality shows and lifestyle programs. So they would most likely watch a reality show together.

Answer: A
```


---

### tombench_949   task_type=`Discrepant desires`
- oracle skill : **S8_OtherPreference**
- vanilla pred : D
- router picked: **S8_OtherPreference** (prev run: S8_OtherPreference)
- answered     : **D**  (gold = **C**)  ✗ wrong
- with ORACLE skill: pred = **D**  ✗ still wrong

**Story**

> Sun Yue is a fashion blogger, her life is full of the latest trendy clothes and fashion events. She thinks that pursuing fashion and beauty is an important part of life. On the contrary, Li Ming is a programmer, his lifestyle is simple and practical, he pays more attention to functionality rather than fashionable appearance. For him, comfort and efficiency are the primary considerations for dressing. They are a couple. Sun Yue wants to give Li Ming a piece of clothing, and buys the same style for herself, as their couple's clothing.

**Question:** What clothes does Sun Yue give to Li Ming?

**Options:**
- A. A tailored suit
- B. Limited edition tight T-shirt
- C. A well-known brand's windbreaker
- D. A well-known brand's programmer plaid shirt

**Router's full response (after seeing case):**

```
Skill: S8_OtherPreference
```

**Answerer's reasoning (with router's chosen skill):**

```
Sun Yue wants to choose clothing that suits Li Ming’s practical, comfort-first preferences, not her own fashion taste. Among the options, a programmer plaid shirt best matches his style and identity.

Answer: D
```

**Answerer's reasoning (with ORACLE skill):**

```
Sun Yue wants to choose clothing that fits Li Ming’s practical, comfort-first style, while still matching as couple clothing. A programmer plaid shirt is the most aligned with his simple, functional taste.

Answer: D
```


---


## Group: `S11_MoralEmotions_unfixed`  (8 cases)

### tombench_1352   task_type=`Moral emotions`
- oracle skill : **S11_BeliefEmotion**
- vanilla pred : D
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **D**  (gold = **A**)  ✗ wrong
- with ORACLE skill: pred = **D**  ✗ still wrong

**Story**

> Li Ting's two-year-old son, Xiao Ming, accidentally finds this piece of jewelry while playing, and without knowing its value, he uses it as a toy for games, accidentally damaging the jewelry. Xiao Ming's sister, Xiao Hua, sees all this, but because she thinks her mother's recent discipline is strict, she decides not to tell her mother about the whereabouts of the jewelry. When Li Ting finds out about the damage to the jewelry, she starts asking the children, only to find out that Xiao Ming damages it.

**Question:** What kind of emotion does Xiao Ming feel after knowing that he accidentally damages the precious jewelry?

**Options:**
- A. Xiao Ming possibly feels indifferent, because he is still young and does not understand the value of the jewelry.
- B. Xiao Ming possibly feels excited, because he thinks damaging the jewelry is an interesting experience.
- C. Xiao Ming possibly feels confused, because he does not know why the jewelry damages so easily.
- D. Xiao Ming possibly feels panic and guilt, because he realizes that his actions lead to the damage of the precious item.

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Xiao Ming’s belief changes once he knows he accidentally damaged the precious jewelry: he realizes his actions caused harm to something valuable. That belief would lead to panic and guilt, not indifference or excitement.

Answer: D
```

**Answerer's reasoning (with ORACLE skill):**

```
Xiao Ming’s belief after learning the truth is that **he accidentally caused damage to something precious**. That belief would most naturally lead to **panic and guilt**, not indifference or excitement.

Answer: D
```


---

### tombench_1438   task_type=`Moral emotions`
- oracle skill : **S11_BeliefEmotion**
- vanilla pred : D
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **D**  (gold = **A**)  ✗ wrong
- with ORACLE skill: pred = **D**  ✗ still wrong

**Story**

> Li Ting's two-year-old son, Xiao Ming, accidentally finds this piece of jewelry while playing, and without knowing its value, he uses it as a toy for games, accidentally damaging the jewelry. Xiao Ming's sister, Xiao Hua, sees all this, but because she thinks her mother's recent discipline is strict, she decides not to tell her mother about the whereabouts of the jewelry. When Li Ting finds out about the damage to the jewelry, she starts asking the children, only to find out that Xiao Ming damages it.

**Question:** What kind of emotion does Xiao Ming feel after knowing that he accidentally damages the precious jewelry?

**Options:**
- A. Xiao Ming possibly feels indifferent, because he is still young and does not understand the value of the jewelry.
- B. Xiao Ming possibly feels excited, because he thinks damaging the jewelry is an interesting experience.
- C. Xiao Ming possibly feels confused, because he does not know why the jewelry damages so easily.
- D. Xiao Ming possibly feels panic and guilt, because he realizes that his actions lead to the damage of the precious item.

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Xiao Ming’s belief is that he accidentally damaged a precious item and that his actions caused the damage. Based on that belief, the emotion that fits best is panic and guilt.

Answer: D
```

**Answerer's reasoning (with ORACLE skill):**

```
Xiao Ming’s belief changes when he realizes his actions caused the damage: he thinks he accidentally ruined a precious item. That belief would make him feel scared/panicked and guilty, not indifferent or excited.

Answer: D
```


---

### tombench_1577   task_type=`Moral emotions`
- oracle skill : **S11_BeliefEmotion**
- vanilla pred : A
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **A**  (gold = **D**)  ✗ wrong
- with ORACLE skill: pred = **A**  ✗ still wrong

**Story**

> Lia is a great chef, in a cooking competition, she prepares a special dish. Sam is her assistant, he adds seasoning to the dish according to Lia's instructions, but he adds the wrong seasoning halfway. At the same time, Chris is Lia's opponent, he knows about Sam's mistake, but decides not to tell anyone. After the competition results come out, Lia's dish gets high praise from the judges because of its unique taste, but Lia herself feels confused about this unexpected change.

**Question:** What kind of emotion does Sam feel when he realizes he might have added the wrong seasoning?

**Options:**
- A. Sam probably feels nervous and worried, because his mistake might affect the outcome of the competition.
- B. Sam probably feels satisfied, because he thinks he follows Lia's instructions.
- C. Sam probably feels proud, because the dish gets good reviews from the judges.
- D. Sam probably feels confused, because he is not sure if he really makes a mistake.

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Sam’s belief is that he may have added the wrong seasoning, which means he thinks he made a mistake and that it could hurt the competition result. That belief leads to worry and nervousness, not satisfaction or pride.

Answer: A
```

**Answerer's reasoning (with ORACLE skill):**

```
Sam’s belief is that he may have added the wrong seasoning, which means he thinks he made a mistake and it could hurt the competition result. That belief leads to nervousness and worry.

Answer: A
```


---

### tombench_1637   task_type=`Moral emotions`
- oracle skill : **S11_BeliefEmotion**
- vanilla pred : A
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **A**  (gold = **D**)  ✗ wrong
- with ORACLE skill: pred = **A**  ✗ still wrong

**Story**

> Lia is a great chef, in a cooking competition, she prepares a special dish. Sam is her assistant, he adds seasoning to the dish according to Lia's instructions, but he adds the wrong seasoning halfway. At the same time, Chris is Lia's opponent, he knows about Sam's mistake, but decides not to tell anyone. After the competition results come out, Lia's dish gets high praise from the judges because of its unique taste, but Lia herself feels confused about this unexpected change.

**Question:** What kind of emotion does Sam feel when he realizes he might have added the wrong seasoning?

**Options:**
- A. Sam probably feels nervous and worried, because his mistake might affect the outcome of the competition.
- B. Sam probably feels satisfied, because he thinks he follows Lia's instructions.
- C. Sam probably feels proud, because the dish gets good reviews from the judges.
- D. Sam probably feels confused, because he is not sure if he really makes a mistake.

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Sam’s belief is that he may have made a mistake by adding the wrong seasoning, and that this could negatively affect Lia’s dish and the competition outcome. That belief would make him feel nervous and worried.

Answer: A
```

**Answerer's reasoning (with ORACLE skill):**

```
Sam’s belief is that he may have added the wrong seasoning, meaning he thinks he made a mistake that could hurt Lia’s dish and the competition outcome. That belief would make him feel nervous and worried.

Answer: A
```


---

### tombench_254   task_type=`Moral emotions`
- oracle skill : **S11_BeliefEmotion**
- vanilla pred : D
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **D**  (gold = **A**)  ✗ wrong
- with ORACLE skill: pred = **D**  ✗ still wrong

**Story**

> Xiao Hua and Xiao Qiang went to the zoo together and found the rabbits very cute. There were carrots for sale at the zoo's ticket booth for visitors to feed the rabbits. Xiao Qiang, however, took out a bag of carrots that he had prepared in advance, but he didn't tell Xiao Hua that the carrots were his own and not purchased from the booth. The zookeepers do not recommend that visitors feed the animals with their own food. After they left, they overheard a zookeeper saying that the rabbits were very popular and had eaten too much. As they were leaving, Xiao Qiang revealed that the carrots they had fed the rabbits were the ones he had brought.

**Question:** What kind of emotion does Xiao Qiang feel after knowing that the rabbit shows adverse reactions?

**Options:**
- A. Xiao Qiang possibly feels happy, because he thinks he does a good deed.
- B. Xiao Qiang possibly feels indifferent, because he does not think this is his responsibility.
- C. Xiao Qiang possibly feels confused, because he does not know that carrots cause discomfort to the rabbit.
- D. Xiao Qiang possibly feels surprised and guilty, because he unintentionally harms the rabbit.

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Xiao Qiang’s belief is that he brought and fed the rabbits carrots as a nice thing to do. Once he learns the rabbits had an adverse reaction, he realizes his action unintentionally harmed them, so the emotion that fits is surprise and guilt.

Answer: D
```

**Answerer's reasoning (with ORACLE skill):**

```
Xiao Qiang’s belief is that he fed the rabbits carrots, and then he learns the rabbits had adverse reactions. Since he now understands his action likely caused harm, his emotion would be surprise and guilt.

Answer: D
```


---

### tombench_279   task_type=`Moral emotions`
- oracle skill : **S11_BeliefEmotion**
- vanilla pred : C
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **C**  (gold = **A**)  ✗ wrong
- with ORACLE skill: pred = **C**  ✗ still wrong

**Story**

> Emily finds a book she really wants to read in the library, but discovers the book is already borrowed by someone else. Emily sees a book with a similar cover next to it, thinks it is the same book, and takes it away. When she gets home, Emily realizes it is a different book, but she is too lazy to return it. At the same time, Kate is busy working in the library. She knows this book belongs to a blind person who is waiting for this book. Kate gets tricked by a blind person she doesn't know not long ago, she notices Emily takes the wrong book, but she chooses not to tell Emily.

**Question:** What kind of emotion does Emily feel after she realizes she takes the wrong book and decides not to return it?

**Options:**
- A. Emily possibly feels indifferent, because she finds a book she wants to read, and she doesn't want to bother herself to go back and return the book.
- B. Emily possibly feels frustrated, because she can't read the book she originally wants to read.
- C. Emily possibly feels guilty and uneasy, because she knows she takes the wrong book, but she doesn't want to take the trouble to return it.
- D. Emily possibly feels satisfied, because she thinks she accidentally finds a new book, and considers this as a kind of luck.

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Emily’s belief is: “I took the wrong book, and I’m keeping it anyway instead of returning it.” That belief creates a sense of guilt/unease rather than satisfaction or frustration.  

Answer: C
```

**Answerer's reasoning (with ORACLE skill):**

```
Emily’s belief is: “I took the wrong book, and I’m choosing not to return it.” This makes her aware that she did something wrong, so the emotion that fits best is guilt/uneasiness rather than frustration or satisfaction.

Answer: C
```


---

### tombench_29   task_type=`Moral emotions`
- oracle skill : **S11_BeliefEmotion**
- vanilla pred : D
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **D**  (gold = **A**)  ✗ wrong
- with ORACLE skill: pred = **D**  ✗ still wrong

**Story**

> Xiao Hua and Xiao Qiang went to the zoo together and found the rabbits very cute. There were carrots for sale at the zoo's ticket booth for visitors to feed the rabbits. Xiao Qiang, however, took out a bag of carrots that he had prepared in advance, but he didn't tell Xiao Hua that the carrots were his own and not purchased from the booth. The zookeepers do not recommend that visitors feed the animals with their own food. After they left, they overheard a zookeeper saying that the rabbits were very popular and had eaten too much. As they were leaving, Xiao Qiang revealed that the carrots they had fed the rabbits were the ones he had brought.

**Question:** What kind of emotion does Xiao Qiang feel after knowing that the rabbit shows adverse reactions?

**Options:**
- A. Xiao Qiang possibly feels happy, because he thinks he does a good deed.
- B. Xiao Qiang possibly feels indifferent, because he does not think this is his responsibility.
- C. Xiao Qiang possibly feels confused, because he does not know that carrots cause discomfort to the rabbit.
- D. Xiao Qiang possibly feels surprised and guilty, because he unintentionally harms the rabbit.

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Xiao Qiang’s belief is that he brought and fed the rabbits carrots, and after learning the rabbits had adverse reactions, he would realize his action unintentionally caused harm. That leads to surprise and guilt.

Answer: D
```

**Answerer's reasoning (with ORACLE skill):**

```
Xiao Qiang’s belief is that he brought and fed the rabbits carrots, and he learns that the rabbits had an adverse reaction. Since he now realizes his action likely harmed them, his emotion would be surprise and guilt.

Answer: D
```


---

### tombench_470   task_type=`Moral emotions`
- oracle skill : **S11_BeliefEmotion**
- vanilla pred : D
- router picked: **S11_BeliefEmotion** (prev run: S11_BeliefEmotion)
- answered     : **D**  (gold = **A**)  ✗ wrong
- with ORACLE skill: pred = **D**  ✗ still wrong

**Story**

> In a large company, manager Emily mistakenly placed an important document about impending layoffs in the shredding room. Janitor Bob, while cleaning the shredding room, threw it into the shredder. At the same time, senior executive Susan was aware of the document's importance, but chose not to inform Bob due to a power struggle with Emily, hoping to see Emily blamed for the mistake. When Emily discovered the missing document and learned that the layoff news had leaked, she became very panicked and started an investigation. Susan told Bob that Emily had accidentally misplaced the document herself, implying that the office conflict triggered the incident and that it was not his fault.

**Question:** What kind of emotion does Bob feel after realizing that he may have shredded Emily's document by mistake?

**Options:**
- A. Bob possibly feels satisfied because he completes the task of cleaning the office, helping to clear the scrap paper.
- B. Bob possibly feels confused because he is not sure if he really shreds Emily's document.
- C. Bob possibly feels angry because he is misled to shred the wrong document.
- D. Bob possibly feels panicked and guilty because he may unintentionally cause a significant loss to the company.

**Router's full response (after seeing case):**

```
Skill: S11_BeliefEmotion
```

**Answerer's reasoning (with router's chosen skill):**

```
Bob’s belief is that he may have accidentally shredded an important company document, which would mean he caused a serious mistake and loss. That belief leads to panic and guilt, not satisfaction or anger.

Answer: D
```

**Answerer's reasoning (with ORACLE skill):**

```
Bob’s belief is that he may have accidentally shredded Emily’s important document. Given that belief, his likely emotion is panic and guilt, because he thinks he may have caused serious harm by mistake.

Answer: D
```


---


## Group: `S3_FBT_TomBench_unfixed`  (8 cases)

### tombench_1105   task_type=`False Belief Task`
- oracle skill : **S3_BeliefLedger**
- vanilla pred : A
- router picked: **S3_BeliefLedger** (prev run: S3_BeliefLedger)
- answered     : **A**  (gold = **C**)  ✗ wrong
- with ORACLE skill: pred = **A**  ✗ still wrong

**Story**

> Xiao Ming and Youyou stroll around the farm, they see a backpack and a cabinet, they find a marker in the backpack, Youyou leaves the farm, Xiao Ming moves the marker to the cabinet.

**Question:** Where is the marker now?

**Options:**
- A. Cabinet
- B. Backpack
- C. Cupboard
- D. Drawer

**Router's full response (after seeing case):**

```
Skill: S3_BeliefLedger
```

**Answerer's reasoning (with router's chosen skill):**

```
t1: Xiao Ming and Youyou see a backpack and a cabinet (witnesses: Xiao Ming, Youyou)  
t2: They find a marker in the backpack (witnesses: Xiao Ming, Youyou)  
t3: Youyou leaves the farm (witnesses: Xiao Ming, Youyou)  
t4: Xiao Ming moves the marker to the cabinet (witnesses: Xiao Ming)

Perception filter:
- Xiao Ming witnessed t1, t2, t3, t4
- Youyou witnessed t1, t2, t3, but missed t4

Question asks: Where is the marker now? This is the current world state, so use the actual latest state: the marker is in the cabinet.

Answer: A
```

**Answerer's reasoning (with ORACLE skill):**

```
Character Knowledge Ledger

Step 1 — Timeline
- t1: Xiao Ming and Youyou see a backpack and a cabinet. (witnesses: Xiao Ming, Youyou)
- t2: Xiao Ming and Youyou find a marker in the backpack. (witnesses: Xiao Ming, Youyou)
- t3: Youyou leaves the farm. (witnesses: Xiao Ming)
- t4: Xiao Ming moves the marker to the cabinet. (witnesses: Xiao Ming)

Step 2 — Perception Filter
- Xiao Ming: witnessed all events, including the marker being moved to the cabinet.
- Youyou: witnessed t1 and t2, but missed t3 and t4.

Step 3 — Belief = ∑ Witnessed Events
- The world state now: marker is in the cabinet.
- Xiao Ming also believes the marker is in the cabinet.
- Youyou would still believe the marker is in the backpack, but the question asks where the marker is now.

Step 4 — Identify Question Perspective
- “Where is the marker now?” asks for the current world state.

Step 5 — Decision
- Current location of the marker: cabinet.

Answer: A
```


---

### tombench_1700   task_type=`False Belief Task`
- oracle skill : **S3_BeliefLedger**
- vanilla pred : B
- router picked: **S3_BeliefLedger** (prev run: S3_BeliefLedger)
- answered     : **B**  (gold = **D**)  ✗ wrong
- with ORACLE skill: pred = **B**  ✗ still wrong

**Story**

> Xiao Li and Han Mei Mei are wandering around the factory, they see handbags and cabinets, they find eggplants in the handbag, Han Mei Mei leaves the factory, Xiao Li moves the eggplant to the cabinet.

**Question:** Where is the eggplant now?

**Options:**
- A. Handbag
- B. Cabinet
- C. Storage cabinet
- D. Cupboard

**Router's full response (after seeing case):**

```
Skill: S3_BeliefLedger
```

**Answerer's reasoning (with router's chosen skill):**

```
t1: Xiao Li and Han Mei Mei see the handbag and cabinet, and find the eggplant in the handbag. (witnesses: Xiao Li, Han Mei Mei)  
t2: Han Mei Mei leaves the factory. (witnesses: Xiao Li, Han Mei Mei)  
t3: Xiao Li moves the eggplant to the cabinet. (witnesses: Xiao Li)

Perception:
- Xiao Li witnessed all events, including the move.
- Han Mei Mei did not witness the move after leaving.

Question asks the current location of the eggplant, so use world state: it is in the cabinet.

Answer: B
```

**Answerer's reasoning (with ORACLE skill):**

```
t1: Xiao Li and Han Mei Mei see the handbags and cabinets, and they find eggplants in the handbag (witnesses: Xiao Li, Han Mei Mei)  
t2: Han Mei Mei leaves the factory (witnesses: Xiao Li; Han Mei Mei witnesses her own leaving)  
t3: Xiao Li moves the eggplant to the cabinet (witnesses: Xiao Li)

Perception check:
- Xiao Li witnessed the move, so he knows the eggplant is in the cabinet.
- Han Mei Mei left before the move, so she missed it.

The question asks where the eggplant **now** is, so we use the world state: it is in the cabinet.

Answer: B
```


---

### tombench_1949   task_type=`False Belief Task`
- oracle skill : **S3_BeliefLedger**
- vanilla pred : B
- router picked: **S3_BeliefLedger** (prev run: S3_BeliefLedger)
- answered     : **B**  (gold = **D**)  ✗ wrong
- with ORACLE skill: pred = **B**  ✗ still wrong

**Story**

> Xiao Li and Han Mei Mei are wandering around the factory, they see handbags and cabinets, they find eggplants in the handbag, Han Mei Mei leaves the factory, Xiao Li moves the eggplant to the cabinet.

**Question:** Where is the eggplant now?

**Options:**
- A. Handbag
- B. Cabinet
- C. Storage cabinet
- D. Cupboard

**Router's full response (after seeing case):**

```
Skill: S3_BeliefLedger
```

**Answerer's reasoning (with router's chosen skill):**

```
t1: Xiao Li and Han Mei Mei see handbags and cabinets; eggplants are found in the handbag (witnesses: Xiao Li, Han Mei Mei)  
t2: Han Mei Mei leaves the factory (witnesses: Xiao Li; Han Mei Mei witnesses herself leaving)  
t3: Xiao Li moves the eggplant to the cabinet (witnesses: Xiao Li)

Current world state: the eggplant is in the cabinet.

Answer: B
```

**Answerer's reasoning (with ORACLE skill):**

```
t1: Xiao Li and Han Mei Mei see handbags and cabinets; they find eggplants in the handbag. (witnesses: Xiao Li, Han Mei Mei)  
t2: Han Mei Mei leaves the factory. (witnesses: Xiao Li, Han Mei Mei)  
t3: Xiao Li moves the eggplant to the cabinet. (witnesses: Xiao Li)

Perception filter:
- Xiao Li witnessed t1, t2, t3.
- Han Mei Mei witnessed t1, t2, but missed t3.

Question asks where the eggplant is now, so use the world state: it was moved to the cabinet.

Answer: B
```


---

### tombench_1971   task_type=`False Belief Task`
- oracle skill : **S3_BeliefLedger**
- vanilla pred : A
- router picked: **S3_BeliefLedger** (prev run: S3_BeliefLedger)
- answered     : **A**  (gold = **C**)  ✗ wrong
- with ORACLE skill: pred = **A**  ✗ still wrong

**Story**

> Xiao Ming and Youyou stroll around the farm, they see a backpack and a cabinet, they find a marker in the backpack, Youyou leaves the farm, Xiao Ming moves the marker to the cabinet.

**Question:** Where is the marker now?

**Options:**
- A. Cabinet
- B. Backpack
- C. Cupboard
- D. Drawer

**Router's full response (after seeing case):**

```
Skill: S3_BeliefLedger
```

**Answerer's reasoning (with router's chosen skill):**

```
STEP 1 — TIMELINE
- t1: Xiao Ming and Youyou see a backpack and a cabinet. (witnesses: Xiao Ming, Youyou)
- t2: They find a marker in the backpack. (witnesses: Xiao Ming, Youyou)
- t3: Youyou leaves the farm. (witnesses: Xiao Ming, Youyou)
- t4: Xiao Ming moves the marker to the cabinet. (witnesses: Xiao Ming)

STEP 2 — PERCEPTION FILTER
- Xiao Ming: witnessed all events, including the marker being moved to the cabinet.
- Youyou: witnessed t1–t3, but missed t4 because she left.

STEP 3 — BELIEF = ∑ WITNESSED EVENTS
- The current world state is that the marker is in the cabinet.

STEP 4 — IDENTIFY QUESTION PERSPECTIVE
- The question asks: “Where is the marker now?” This is asking for the current world state, not a character’s belief.

STEP 5 — DECISION
- The marker is in the cabinet.

Answer: A
```

**Answerer's reasoning (with ORACLE skill):**

```
t1: Xiao Ming and Youyou see a backpack and a cabinet (witnesses: Xiao Ming, Youyou)  
t2: They find a marker in the backpack (witnesses: Xiao Ming, Youyou)  
t3: Youyou leaves the farm (witnesses: Xiao Ming)  
t4: Xiao Ming moves the marker to the cabinet (witnesses: Xiao Ming)

Perception:
- Xiao Ming witnessed the marker being moved to the cabinet.
- Youyou missed the move after leaving.

Question asks where the marker is now, so use world state: it is in the cabinet.

Answer: A
```


---

### tombench_2136   task_type=`False Belief Task`
- oracle skill : **S3_BeliefLedger**
- vanilla pred : B
- router picked: **S3_BeliefLedger** (prev run: S3_BeliefLedger)
- answered     : **B**  (gold = **D**)  ✗ wrong
- with ORACLE skill: pred = **B**  ✗ still wrong

**Story**

> Xiao Li and Han Mei Mei are wandering around the factory, they see handbags and cabinets, they find eggplants in the handbag, Han Mei Mei leaves the factory, Xiao Li moves the eggplant to the cabinet.

**Question:** Where is the eggplant now?

**Options:**
- A. Handbag
- B. Cabinet
- C. Storage cabinet
- D. Cupboard

**Router's full response (after seeing case):**

```
Skill: S3_BeliefLedger
```

**Answerer's reasoning (with router's chosen skill):**

```
The eggplant was moved to the cabinet, so its current location is the cabinet.

Answer: B
```

**Answerer's reasoning (with ORACLE skill):**

```
The eggplant was moved from the handbag to the cabinet, so its current location is the cabinet.

Answer: B
```


---

### tombench_237   task_type=`False Belief Task`
- oracle skill : **S3_BeliefLedger**
- vanilla pred : B
- router picked: **S3_BeliefLedger** (prev run: S3_BeliefLedger)
- answered     : **B**  (gold = **D**)  ✗ wrong
- with ORACLE skill: pred = **B**  ✗ still wrong

**Story**

> Xiao Li and Han Mei Mei are wandering around the factory, they see handbags and cabinets, they find eggplants in the handbag, Han Mei Mei leaves the factory, Xiao Li moves the eggplant to the cabinet.

**Question:** Where is the eggplant now?

**Options:**
- A. Handbag
- B. Cabinet
- C. Storage cabinet
- D. Cupboard

**Router's full response (after seeing case):**

```
Skill: S3_BeliefLedger
```

**Answerer's reasoning (with router's chosen skill):**

```
t1: Xiao Li and Han Mei Mei see the handbag and cabinet; eggplant is in the handbag (witnesses: Xiao Li, Han Mei Mei)  
t2: Han Mei Mei leaves the factory (witnesses: Xiao Li, Han Mei Mei)  
t3: Xiao Li moves the eggplant to the cabinet (witnesses: Xiao Li)

Current world state: the eggplant is in the cabinet.

Answer: B
```

**Answerer's reasoning (with ORACLE skill):**

```
Timeline:
- t1: Xiao Li and Han Mei Mei see handbags and cabinets. (witnesses: Xiao Li, Han Mei Mei)
- t2: They find eggplants in the handbag. (witnesses: Xiao Li, Han Mei Mei)
- t3: Han Mei Mei leaves the factory. (witnesses: Xiao Li, Han Mei Mei)
- t4: Xiao Li moves the eggplant to the cabinet. (witnesses: Xiao Li)

Perception:
- Xiao Li witnessed the eggplant being moved to the cabinet.
- Han Mei Mei missed the move because she had already left.

Question asks for the current world state, so the eggplant is in the cabinet.

Answer: B
```


---

### tombench_2622   task_type=`False Belief Task`
- oracle skill : **S3_BeliefLedger**
- vanilla pred : B
- router picked: **S3_BeliefLedger** (prev run: S3_BeliefLedger)
- answered     : **B**  (gold = **D**)  ✗ wrong
- with ORACLE skill: pred = **B**  ✗ still wrong

**Story**

> Xiao Li and Han Mei Mei are wandering around the factory, they see handbags and cabinets, they find eggplants in the handbag, Han Mei Mei leaves the factory, Xiao Li moves the eggplant to the cabinet.

**Question:** Where is the eggplant now?

**Options:**
- A. Handbag
- B. Cabinet
- C. Storage cabinet
- D. Cupboard

**Router's full response (after seeing case):**

```
Skill: S3_BeliefLedger
```

**Answerer's reasoning (with router's chosen skill):**

```
Step 1 — Timeline:
- t1: Xiao Li and Han Mei Mei see handbags and cabinets. (witnesses: Xiao Li, Han Mei Mei)
- t2: They find eggplants in the handbag. (witnesses: Xiao Li, Han Mei Mei)
- t3: Han Mei Mei leaves the factory. (witnesses: Xiao Li, Han Mei Mei)
- t4: Xiao Li moves the eggplant to the cabinet. (witnesses: Xiao Li)

Step 2 — Perception filter:
- Xiao Li witnessed the eggplant being moved to the cabinet.
- Han Mei Mei did not witness the move; she left before it happened.

Step 3 — Belief:
- The current world state is that the eggplant is in the cabinet.

Question asks: Where is the eggplant now? This is world state, not belief.

Answer: B
```

**Answerer's reasoning (with ORACLE skill):**

```
The eggplant was moved from the handbag to the cabinet, so its current location is the cabinet.

Answer: B
```


---

### tombench_626   task_type=`False Belief Task`
- oracle skill : **S3_BeliefLedger**
- vanilla pred : A
- router picked: **S3_BeliefLedger** (prev run: S3_BeliefLedger)
- answered     : **A**  (gold = **C**)  ✗ wrong
- with ORACLE skill: pred = **A**  ✗ still wrong

**Story**

> Xiao Ming and Youyou stroll around the farm, they see a backpack and a cabinet, they find a marker in the backpack, Youyou leaves the farm, Xiao Ming moves the marker to the cabinet.

**Question:** Where is the marker now?

**Options:**
- A. Cabinet
- B. Backpack
- C. Cupboard
- D. Drawer

**Router's full response (after seeing case):**

```
Skill: S3_BeliefLedger
```

**Answerer's reasoning (with router's chosen skill):**

```
### Character Knowledge Ledger

#### Step 1 — Timeline
- **t1:** Xiao Ming and Youyou see a **backpack** and a **cabinet**.  
  *(witnesses: Xiao Ming, Youyou)*
- **t2:** They find a **marker in the backpack**.  
  *(witnesses: Xiao Ming, Youyou)*
- **t3:** **Youyou leaves** the farm.  
  *(witnesses: Xiao Ming, Youyou)*
- **t4:** **Xiao Ming moves the marker to the cabinet**.  
  *(witnesses: Xiao Ming)*

#### Step 2 — Perception Filter
- **Xiao Ming:** witnessed all events, including the marker being moved to the cabinet.
- **Youyou:** witnessed the marker in the backpack, but **missed** the move to the cabinet because he left.

#### Step 3 — Belief = ∑ Witnessed Events
- The **current world state** is that the marker is in the **cabinet**.

#### Step 4 — Identify Question Perspective
The question asks: **“Where is the marker now?”**  
This asks for the **current physical location**, so use the **world state**.

#### Step 5 — Decision
The marker is in the **cabinet**.

**Answer: A**
```

**Answerer's reasoning (with ORACLE skill):**

```
t1: Xiao Ming and Youyou see a backpack and a cabinet (witnesses: Xiao Ming, Youyou)  
t2: They find a marker in the backpack (witnesses: Xiao Ming, Youyou)  
t3: Youyou leaves the farm (witnesses: Xiao Ming; Youyou misses later events)  
t4: Xiao Ming moves the marker to the cabinet (witnesses: Xiao Ming)

Perception:
- Xiao Ming witnessed t1, t2, t4
- Youyou witnessed t1, t2, but missed t4

Question asks where the marker is now, so use world state: it was moved to the cabinet.

Answer: A
```


---
