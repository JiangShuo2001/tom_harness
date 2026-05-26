# micro-14 Examples and Boundaries

## Decision Variable
surface appearance versus true state

## Route Signal
Use this micro unit when the problem's central variable is the mismatch between how something seems and what it actually is, independent of any named person's mental state.

## Hard Boundary
- Appearance-reality is object- or situation-level; false belief is person-level.
- This unit does not predict actions from beliefs.
- This unit does not model nested minds.
- This unit does not handle belief revision after evidence except as background context.
- This unit does not decide whether information is mutually public.

## Shortcut To Avoid
- Do not answer from the misleading appearance when the question asks for reality.
- Do not convert every appearance-reality gap into a false-belief case; a belief-holder must be part of the asked question.

## Common Failure Modes
- Collapsing appearance and reality into one answer.
- Assuming all observers know the true state.
- Tracking a character's belief when the prompt only asks what is apparent and what is real.
- Ignoring wording such as 'looks like,' 'seems,' 'actually,' or 'really.'

## Minimal Pair
- Case: A sponge is painted to look like a rock. The question asks, 'What does it look like, and what is it really?' | Why: The task is to separate surface appearance from true identity without attributing a belief to anyone.
- Case: A child sees the painted sponge and is asked, 'What will the child think it is?' | Why: This is a near neighbor but should route away: the answer depends on the child's belief, not only the appearance-reality gap.

## Boundary Stress Test
- If a box labeled 'tea' contains buttons and the question asks what is actually inside, answer buttons using this unit.
- If someone saw only the tea label and the question asks what they believe is inside, exit to false belief or knowledge-access reasoning.
- If two people both watched the contents being changed and know the other watched, exit to common knowledge if shared awareness is the target.
- If a person first thinks the object is a toy but then touches it and learns it is food, exit to evidence-availability updating.

## Generalization Note
This unit applies across physical objects, social signals, labels, costumes, digital displays, and situational appearances whenever the reasoning target is the appearance/reality split itself.
