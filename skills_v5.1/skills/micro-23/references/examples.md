# micro-23 Examples and Boundaries

## Decision Variable
the character's next likely action

## Route Signal
Use this micro unit when the answer must be an observable next behavior derived from the character's belief state and active goal.

## Hard Boundary
- Action prediction is future-facing; intention recognition is explanation of a current or past behavior.
- Action prediction outputs behavior; desire or goal units output internal preference or objective structure.
- Action prediction can use commitments as evidence, but if the central variable is priority among commitments, route away.
- Action prediction should not replace false-belief reasoning; it uses the belief result to predict behavior.

## Shortcut To Avoid
- Do not predict from the real state of the world when the character has a different belief.
- Do not answer with a motive such as 'to help' when the question asks what the character will physically do next.

## Common Failure Modes
- Reality leak: using information the character did not observe.
- Motive-action swap: giving the purpose instead of the next behavior.
- Overplanning: inventing a complex plan when the immediate next step is enough.
- Commitment confusion: treating all competing tasks as simple action prediction when a prior obligation is decisive.

## Minimal Pair
- Case: Nora sees a cup fall under the sofa and wants to pick it up. The question asks, 'What will Nora do next?' | Why: The task is to predict the next observable action from Nora's belief and goal: she will look or reach under the sofa.
- Case: Nora points under the sofa and smiles. The question asks, 'Why is Nora pointing there?' | Why: This does not match action prediction; it asks for the purpose behind a current cue, so it belongs to intention recognition.

## Boundary Stress Test
- If the character wants an object but falsely believes it is in the old location, predict search at the old location.
- If the character has two possible next actions but only one serves the active goal under their belief, choose that action.
- If the prompt asks whether the character will keep a promise or accept a new invitation, check whether commitment priority is the better route.
- If the prompt asks what the character is trying to accomplish by knocking, waving, or glancing, do not use this unit.

## Generalization Note
This unit generalizes across benchmark false-belief tasks and real-world scenes by applying the same belief-plus-goal rule to predict the next observable action.
