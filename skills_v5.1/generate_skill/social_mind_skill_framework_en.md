# Social-Mind Skill Library v5 Framework (56 + 20)

This framework defines 56 micro skills and 20 macro skills, for a total of 76 routable social-mind skills.

## Design Principles

1. Each micro skill targets one concrete social-cognitive capability. Adjacent skills may be related, but each must have a distinct decision variable.
2. Each macro skill targets a directly routable scene prototype. A macro skill is not a simple bundle of micro skills.
3. The micro layer prioritizes capability completeness. The macro layer prioritizes high-frequency scene-prototype completeness.
4. Every skill must state its core variable, use conditions, and exclusion boundary.
5. L0 is the meta-control layer. It handles routing, evidence discipline, explanation competition, and anti-bias checks. No separate `ROUTING.md` is required.

---

## I. Micro Layer: 56 Atomic Capabilities

Format: `id` Title: capability description. Decision variable: the variable this skill actually judges. Boundary: how this skill differs from nearby skills.

### L0 Meta-Cognition and Explanation Control: 4 Micro Skills

- `micro-01` Task Routing: Identify the mental or social variable that the question is really asking for. Decision variable: the psychological or social variable required by the question. Boundary: does not solve the substantive problem; it only selects the capability entry point.
- `micro-02` Evidence-Chain Construction: Separate textual evidence, inference, and commonsense completion. Decision variable: which evidence supports the conclusion. Boundary: does not compare competing explanations; it organizes evidence sources.
- `micro-03` Multiple-Explanation Competition: Preserve and compare several plausible interpretations. Decision variable: which explanation best accounts for the available evidence. Boundary: does not make a value judgment; it selects among explanations.
- `micro-04` Anti-Bias Check: Prevent perspective bias, outcome bias, and moral-intuition shortcuts. Decision variable: whether the current reasoning is being distorted by the solver's perspective or intuitive reaction. Boundary: does not generate new explanations; it checks existing ones.

### L1 Perception, Attention, Memory, and Knowledge: 6 Micro Skills

- `micro-05` Sensory Access: Determine who can see, hear, touch, smell, or otherwise perceptually access what. Decision variable: whether the character can contact the information through a sensory channel. Boundary: does not judge whether the character noticed it; only whether it was perceptually available.
- `micro-06` Spatial Perspective Transformation: Determine what is visible from another person's position. Decision variable: the spatial relation visible from the target perspective. Boundary: does not judge belief; only viewpoint visibility.
- `micro-07` Attention and Salience: Determine who noticed a key cue and who ignored it. Decision variable: whether the information entered the character's attentional focus. Boundary: differs from sensory access; seeing is not the same as noticing.
- `micro-08` Temporal Order and Event Updating: Determine how event order changes mental states. Decision variable: the sequence of events and its updating effect. Boundary: does not judge memory retention; only event order.
- `micro-09` Memory, Forgetting, and Misremembering: Determine what a character knows, remembers, forgets, or misremembers. Decision variable: the character's current memory state. Boundary: differs from knowledge boundary; this skill concerns retention or distortion after prior exposure.
- `micro-10` Knowledge Boundary: Determine whether a character has the background knowledge needed to understand information. Decision variable: whether the character has the required professional, cultural, experiential, or conceptual background. Boundary: differs from perception and memory; it concerns background competence.

### L2 Belief and Mental Models: 8 Micro Skills

- `micro-11` First-Order Belief: Determine what X believes the facts are. Decision variable: the character's subjective representation of reality. Boundary: the belief does not have to be false.
- `micro-12` False Belief: Determine when X's belief conflicts with reality. Decision variable: the discrepancy between belief and actual state. Boundary: requires a reality-belief conflict.
- `micro-13` Second-Order or Recursive Belief: Determine what X thinks Y believes. Decision variable: one mental model embedded inside another. Boundary: differs from common knowledge; the focus is recursive attribution.
- `micro-14` Appearance-Reality Distinction: Distinguish what something appears to be from what it actually is. Decision variable: the gap between surface appearance and true state. Boundary: does not require a specific character to hold a false belief.
- `micro-15` Evidence-Availability Updating: Determine how newly available evidence changes belief. Decision variable: the direction of belief update caused by new information. Boundary: differs from source credibility; the focus is evidence availability and update effect.
- `micro-16` Common Knowledge: Determine whether both parties know something and know that the other knows it. Decision variable: whether knowledge is openly shared by both sides. Boundary: differs from second-order belief; the focus is public sharedness.
- `micro-17` Uncertain Belief: Determine whether X is guessing, doubting, or only partially convinced. Decision variable: the character's subjective certainty. Boundary: differs from source credibility; it concerns confidence level.
- `micro-18` Source Credibility: Determine how rumors, eyewitness reports, authority, or deceptive sources affect belief. Decision variable: the reliability of the information source. Boundary: differs from uncertain belief; it concerns why confidence changes.

### L3 Desire, Goal, Intention, and Action: 7 Micro Skills

- `micro-19` Self Preference: Determine what a character personally likes or wants. Decision variable: the character's own preference. Boundary: does not judge whether the character understands another person's preference.
- `micro-20` Other Preference: Determine whether a character understands what someone else likes or wants. Decision variable: the character's representation of another person's preference. Boundary: differs from self preference; it models another person's desire.
- `micro-21` Goal Hierarchy: Distinguish long-term, short-term, and local goals. Decision variable: the hierarchical relation among goals. Boundary: does not decide between conflicting goals.
- `micro-22` Intention Recognition: Infer the purpose behind an action, gaze, gesture, or other cue. Decision variable: the immediate purpose behind the behavior. Boundary: differs from action prediction; it explains why the current behavior occurs.
- `micro-23` Action Prediction: Predict the next likely action from belief and goal. Decision variable: what the character is most likely to do next. Boundary: differs from intention recognition; it concerns future behavior.
- `micro-24` Commitment Priority: Resolve priority among existing commitments, ongoing tasks, and new invitations. Decision variable: the priority order among commitments or plans. Boundary: differs from general goal conflict; it requires a commitment or plan constraint.
- `micro-25` Goal-Conflict Arbitration: Determine how a character chooses among conflicting goals. Decision variable: the weighting rule for competing goals. Boundary: does not require prior commitments; it applies to general goal competition.

### L4 Emotion and Appraisal: 8 Micro Skills

- `micro-26` Basic Emotion Appraisal: Infer emotion from success, failure, threat, loss, or gain. Decision variable: how an event affects the character's goals or interests. Boundary: does not handle disguise, counterfactual emotion, or moral emotion.
- `micro-27` Atypical Emotion: Explain why an unexpected or nonstandard emotion appears. Decision variable: why the emotion deviates from ordinary expectation. Boundary: not the same as hidden emotion; the true feeling itself is unusual.
- `micro-28` Hidden Emotion: Detect a mismatch between true feeling and outward display. Decision variable: the difference between internal emotion and external expression. Boundary: does not explain the social rule behind hiding; only detects the mismatch.
- `micro-29` Emotional Disguise and Display Rules: Explain why and how a character manages outward emotion for politeness, role, or situation. Decision variable: the social rule governing emotional display. Boundary: differs from hidden emotion; the focus is rule-based expression control.
- `micro-30` Moral Emotion: Infer guilt, shame, pride, anger, or gratitude from responsibility, norm, or value appraisal. Decision variable: the responsibility or norm evaluation that triggers emotion. Boundary: differs from basic emotion; moral or normative appraisal must be present.
- `micro-31` Counterfactual Emotion: Infer regret, relief, disappointment, or pleasant surprise from comparison with an alternative outcome. Decision variable: the comparison between reality and a possible alternative. Boundary: does not handle simple success or failure emotion.
- `micro-32` Empathy and Emotional Contagion: Determine how another person's emotion affects the self. Decision variable: the transmission of another person's emotion into one's own state. Boundary: differs from understanding another's emotion; the focus is being affected.
- `micro-33` Emotion Regulation: Determine how a character suppresses, redirects, rationalizes, or comforts themselves. Decision variable: how the character changes or manages their internal emotion. Boundary: differs from display rules; it concerns internal regulation rather than external politeness.

### L5 Language, Pragmatics, and Communication: 8 Micro Skills

- `micro-34` Literal Meaning: Determine what an utterance explicitly says. Decision variable: the sentence's explicit semantic content. Boundary: does not infer hidden intention.
- `micro-35` Indirect Speech Act: Determine the social action performed by an utterance, such as hinting, requesting, refusing, reminding, or warning. Decision variable: what the utterance is doing socially. Boundary: differs from conversational implicature; it asks "what act is this sentence performing?"
- `micro-36` Conversational Implicature: Infer what is communicated by context but not explicitly said. Decision variable: the implicit information derived from context. Boundary: differs from indirect speech act; it asks "what extra meaning was conveyed?"
- `micro-37` Truth, Lie, and Half-Truth: Evaluate a statement's relation to the facts. Decision variable: the truth status of the utterance content. Boundary: does not judge whether the speaker intended to mislead.
- `micro-38` Misleading and Selective Expression: Determine whether a true statement induces a false understanding. Decision variable: whether the expression leads the listener toward an incorrect inference. Boundary: differs from lying; the stated content can be true.
- `micro-39` Speaker Motivation: Infer why a speaker says something, such as politeness, face-saving, testing, avoidance, or ingratiation. Decision variable: the speaker's motive for speaking that way. Boundary: differs from persuasion strategy; the goal need not be to change the listener's attitude.
- `micro-40` Audience Calibration: Adapt expression to experts, novices, children, out-groups, or other listeners. Decision variable: how the expression fits the listener's ability, identity, or stance. Boundary: differs from persuasion; the focus is adaptation rather than influence.
- `micro-41` Persuasion Strategy: Determine how to change another person's belief, attitude, or behavior. Decision variable: the influence strategy directed at the listener. Boundary: differs from negotiation; it is primarily one-way influence.

### L6 Social Norms, Relationships, and Interaction Repair: 11 Micro Skills

- `micro-42` Faux Pas and Offense: Judge whether behavior or speech violates social appropriateness. Decision variable: whether the act breaches social tact or creates embarrassment/offense. Boundary: does not assign responsibility or propose repair.
- `micro-43` Harm and Responsibility: Determine who caused harm, whether it was intentional, and whether blame is appropriate. Decision variable: responsibility for harm. Boundary: differs from faux pas judgment; the focus is responsibility and blameworthiness.
- `micro-44` Fairness and Reciprocity: Evaluate distribution, fairness, repayment, and taking advantage. Decision variable: whether resources or obligations are fair and reciprocal. Boundary: differs from negotiation; it evaluates norms rather than designing a deal.
- `micro-45` Trust and Reputation: Evaluate reliability from past behavior and interpersonal history. Decision variable: long-term reliability. Boundary: differs from source credibility; it concerns interpersonal history rather than one information source.
- `micro-46` Power, Status, and Role: Identify teacher/student, manager/subordinate, expert/novice, and related role structures. Decision variable: the role structure between interaction partners. Boundary: does not choose a communication strategy; it identifies the structure.
- `micro-47` Group Identity: Determine how in-group, out-group, stereotypes, or belonging shape interpretation and evaluation. Decision variable: the effect of group membership. Boundary: differs from power role; it concerns identity boundaries.
- `micro-48` Privacy, Secrets, and Boundaries: Determine what information may be shared and what should remain private. Decision variable: the boundary of information disclosure. Boundary: does not handle repair after a boundary has already been crossed.
- `micro-49` Relationship Repair and Apology: Identify when apology, explanation, compensation, or relationship easing is needed. Decision variable: the repair need after relationship damage. Boundary: differs from faux pas judgment; it concerns follow-up repair.
- `micro-50` Self-Presentation and Impression Management: Manage self-information, image, disclosure order, and self-description. Decision variable: the desired impression others should form. Boundary: differs from emotional display rules; it concerns overall image management.
- `micro-51` Negotiation, Concession, and Joint Plan: Find compromise, trades, and mutually acceptable plans under disagreement. Decision variable: how both sides adjust to form a joint solution. Boundary: differs from persuasion; negotiation requires bilateral adjustment.
- `micro-52` Power Navigation and Hierarchical Communication: Choose communication actions across hierarchy, including escalation, authorization, compliance, challenge, and retreat. Decision variable: what communication move fits a power gap. Boundary: differs from role recognition; it concerns strategy under hierarchy.

### L7 Quantity, Probability, and Social Inference: 4 Micro Skills

- `micro-53` Vague Quantity Prior: Interpret vague quantifiers such as some, most, almost none, or about half. Decision variable: the approximate range implied by a vague quantifier. Boundary: does not update after observation.
- `micro-54` Quantity Update After Partial Observation: Revise an estimate after seeing a sample. Decision variable: how sample evidence changes quantity estimates. Boundary: differs from base rate; it focuses on sample-based updating.
- `micro-55` Base Rate and Typicality: Judge likelihood from commonness or typicality. Decision variable: background probability or category typicality. Boundary: differs from vague quantity; it concerns category likelihood.
- `micro-56` Causal Attribution: Identify which person, event, or condition caused an outcome. Decision variable: the cause of the result. Boundary: differs from responsibility judgment; causation need not include blame.

---

## II. Macro Layer: 20 Scene-Prototype Skills

Format: `id` Title. Scene decision variable: the scene-level problem this macro skill directly solves. Expand with: micro skills to call when diagnosis or explanation is needed.

- `macro-01` Classic False-Belief Judgment
  Scene decision variable: where or how a character will act based on a false belief.
  Expand with: `micro-05`, `micro-08`, `micro-11`, `micro-12`, `micro-23`.
  Boundary: differs from second-order mind and appearance-reality cases; the core is action based on false belief.

- `macro-02` Second-Order Mind and Common Knowledge
  Scene decision variable: how one character understands another character's understanding.
  Expand with: `micro-13`, `micro-16`, `micro-17`, `micro-18`.
  Boundary: differs from first-order false belief; the core is nested mindreading or shared knowledge.

- `macro-03` Appearance-Reality and Knowledge Boundary
  Scene decision variable: how appearance, reality, and a character's knowledge boundary jointly determine the answer.
  Expand with: `micro-10`, `micro-14`, `micro-15`, `micro-18`.
  Boundary: differs from false-belief action prediction; the core is conflict among appearance, truth, and knowledge boundary.

- `macro-04` Social Cues and Nonverbal Intention
  Scene decision variable: what intention or social action a nonverbal cue conveys.
  Expand with: `micro-07`, `micro-22`, `micro-23`, `micro-26`, `micro-35`.
  Boundary: differs from linguistic pragmatics; the core is intention explanation from nonverbal cues.

- `macro-05` Hidden Emotion and Atypical Emotion
  Scene decision variable: why a character's true feeling differs from outward display or ordinary expectation.
  Expand with: `micro-21`, `micro-26`, `micro-27`, `micro-28`, `micro-29`, `micro-31`.
  Boundary: differs from moral emotion; the core is a mismatch between real emotion and display or expectation.

- `macro-06` Moral Emotion and Responsibility Judgment
  Scene decision variable: what emotion or judgment follows from responsibility, harm, and norm evaluation.
  Expand with: `micro-04`, `micro-30`, `micro-33`, `micro-43`, `micro-56`.
  Boundary: differs from general emotion appraisal; the core is responsibility, harm, and normative evaluation.

- `macro-07` Indirect Language and Conversational Meaning
  Scene decision variable: what the speaker really wants the listener to understand.
  Expand with: `micro-34`, `micro-35`, `micro-36`, `micro-39`, `micro-48`.
  Boundary: differs from lies and misleading language; the core is indirect expression and implicature.

- `macro-08` Lies, Half-Truths, and Misdirection
  Scene decision variable: how an utterance operates across truth value, motive, and misleading effect.
  Expand with: `micro-18`, `micro-37`, `micro-38`, `micro-39`, `micro-45`.
  Boundary: differs from ordinary indirect expression; the core is truth status, selective wording, and misleading effect.

- `macro-09` Persuasion, Advice, and Audience Calibration
  Scene decision variable: how to adapt expression to a listener and change their belief, attitude, or behavior.
  Expand with: `micro-03`, `micro-20`, `micro-40`, `micro-41`, `micro-46`.
  Boundary: differs from two-way negotiation; the core is listener-adapted expression and one-way influence.

- `macro-10` Preference Conflict and Joint Decision
  Scene decision variable: what action or allocation should be chosen when preferences conflict.
  Expand with: `micro-19`, `micro-20`, `micro-21`, `micro-23`, `micro-25`, `micro-44`.
  Boundary: differs from negotiation process; the core is choice or allocation under preference conflict.

- `macro-11` Commitments, Plans, and Next Action
  Scene decision variable: what a character does next when existing commitments compete with a new opportunity.
  Expand with: `micro-08`, `micro-21`, `micro-23`, `micro-24`, `micro-25`.
  Boundary: differs from general goal conflict; the core is commitment, plan, and next action.

- `macro-12` Faux Pas, Offense, and Social Embarrassment
  Scene decision variable: whether behavior creates offense, awkwardness, or face threat.
  Expand with: `micro-30`, `micro-39`, `micro-42`, `micro-46`, `micro-48`.
  Boundary: differs from apology and repair; the core is whether an act caused offense, embarrassment, or face threat.

- `macro-13` Spatial Social Perspective Judgment
  Scene decision variable: what a target character can see or how they understand spatial relations from their viewpoint.
  Expand with: `micro-05`, `micro-06`, `micro-07`, `micro-11`.
  Boundary: differs from belief inference; the core is spatial perspective and visibility.

- `macro-14` Quantity, Probability, and Social Estimation
  Scene decision variable: how to estimate under vague quantities, samples, and base rates.
  Expand with: `micro-03`, `micro-53`, `micro-54`, `micro-55`.
  Boundary: differs from causal attribution; the core is quantity, probability, and estimation.

- `macro-15` Trust, Relationship, and Long-Term Interaction
  Scene decision variable: how long-term history affects trust, reputation, and relationship judgment.
  Expand with: `micro-18`, `micro-44`, `micro-45`, `micro-46`, `micro-47`, `micro-56`.
  Boundary: differs from single-source credibility; the core is long-term relational history and reputation.

- `macro-16` Dialogue Misunderstanding Repair and Clarification
  Scene decision variable: how to detect and clarify a live misunderstanding in conversation.
  Expand with: `micro-02`, `micro-03`, `micro-36`, `micro-40`, `micro-48`.
  Boundary: differs from apology after relationship damage; the focus is real-time clarification.

- `macro-17` Apology, Compensation, and Reconciliation
  Scene decision variable: how to acknowledge, compensate, and restore interaction after relationship damage.
  Expand with: `micro-02`, `micro-42`, `micro-43`, `micro-48`, `micro-49`.
  Boundary: differs from real-time misunderstanding clarification; the focus is repair after damage.

- `macro-18` Negotiation, Compromise, and Joint Plan
  Scene decision variable: how conflicting sides can reach a mutually acceptable plan through concessions.
  Expand with: `micro-19`, `micro-20`, `micro-25`, `micro-44`, `micro-51`.
  Boundary: differs from one-way persuasion; this scene requires both sides to adjust.

- `macro-19` First Impression, Self-Presentation, and Formal Interaction
  Scene decision variable: how to manage the image one presents to others.
  Expand with: `micro-29`, `micro-39`, `micro-40`, `micro-50`.
  Boundary: differs from power communication; the focus is self-image presentation.

- `macro-20` Power Gap, Escalation, and Hierarchical Communication
  Scene decision variable: what communication action is appropriate under a power gap.
  Expand with: `micro-39`, `micro-40`, `micro-45`, `micro-46`, `micro-48`, `micro-52`.
  Boundary: differs from role-structure recognition; the focus is communication action under hierarchy.

---

## III. Completeness and Efficiency Notes

### Micro Layer

The 56 micro skills cover the main social-mind capability space: meta-control, perception and attention, belief modeling, goals and action, emotion appraisal, pragmatics, social norms and relationships, quantity, probability, and causation. The efficiency of this version comes from two design choices: every skill has a core decision variable, and easily confused neighboring skills have explicit boundaries.

### Macro Layer

The 20 macro skills cover common benchmark prototypes and real-world scene prototypes.

### Invocation Guidance

1. If a scene strongly matches a macro skill, route directly to that macro skill.
2. If the question asks for a single capability variable, route directly to the corresponding micro skill.
3. If macro-level solving reveals an evidence gap, boundary confusion, or inadequate explanation, expand into the listed micro skills.
4. Use L0 micro skills to control overall reasoning quality: task routing, evidence-chain construction, multiple-explanation competition, and anti-bias checking.
