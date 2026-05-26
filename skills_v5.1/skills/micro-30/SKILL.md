---
name: micro-30
level: micro
layer: L4
family: "emotion-appraisal"
description: "Infers guilt, shame, pride, anger, or gratitude from a moral, norm-based, or responsibility-based appraisal."
---

# Moral Emotion

## Use When
- Use when the question asks which moral emotion someone feels after judging responsibility, blame, credit, obligation, fairness, harm, or thanks.
- Use when the emotion depends on whether the person sees themselves or another as responsible, deserving, at fault, benefitted, or norm-violating.
- Use when the key clue is a moral appraisal rather than a basic feeling trigger like pain, loss, surprise, or fear.
- Use when the answer requires inferring guilt, shame, pride, anger, or gratitude from a social or moral evaluation.

## Do Not Use When
- Do not use when the task is only to detect hidden emotion without needing the moral reason behind it.
- Do not use when the task is about display rules, politeness, or why emotion is masked rather than which moral emotion is felt.
- Do not use when the emotion is regret, relief, disappointment, or pleasant surprise from a comparison with an alternative outcome.
- Do not use when the emotion is a basic affect caused by direct events with no norm, blame, credit, or obligation appraisal.
- Do not use when the question is about empathy or emotional contagion from another person's feeling.

## Decision Variable
the responsibility or norm appraisal behind the emotion

## Trigger Checklist
- Is there blame, fault, credit, duty, fairness, harm, apology, or thanks in the scene?
- Does the person evaluate themselves or someone else as responsible or deserving?
- Is the emotion better explained by moral standing than by raw outcome or physical event?
- Would the answer change if the responsibility or norm judgment changed?

## Workflow
- Identify the moral appraisal: blame, credit, obligation, violation, harm, or benefit.
- Determine whose responsibility is being evaluated: self, other person, or group.
- Map that appraisal to the likely moral emotion: guilt or shame for self-blame, pride for credit, anger for wrongdoing by another, gratitude for received benefit.
- Check that the explanation depends on the moral evaluation, not just on general mood or display.

## Special Case
**Mixed appraisal with one dominant moral driver**: If multiple feelings are possible, choose the one most directly caused by the responsibility or norm judgment. Use this unit only when a moral appraisal is the main driver, even if a basic emotion is also present.

Scene: A student breaks a class rule and feels bad because they know they caused trouble for the teacher.
Question: What emotion is most directly supported?
Answer logic: The key variable is self-blame for a norm violation. That supports guilt, not just sadness or fear.

## Boundary Exit Rule
- Exit to micro-28 Hidden Emotion if the main task is to infer what someone feels beneath a mask, and the moral reason is not being asked for.
- Exit to micro-29 Emotional Disguise and Display Rules if the main task is why the person is hiding or showing emotion in public.
- Exit to micro-31 Counterfactual Emotion if the core comparison is what happened versus what might have happened.
- Exit to micro-26 Basic Emotion Appraisal if there is no responsibility, norm, or value appraisal in the scene.
- Exit to micro-32 Empathy and Emotional Contagion if the emotion is caused by absorbing another person's feeling rather than by a moral judgment.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Route here when emotion inference depends on moral responsibility or norm evaluation rather than on simple event-based affect.
