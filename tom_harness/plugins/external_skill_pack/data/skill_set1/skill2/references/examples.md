# FP-02 Reference

## Decision Variable

- The key variable is whether the target person had access to the fact being asked about.

## Route Signal

- Use this skill when the question is about knowledge, memory, awareness, forgetting, or missed information.

## Hard Boundary

- If the question is about whether a remark itself was inappropriate, route to `skill1`.
- If the question is about where someone will search or what they believe about a moved object, route to the false-belief skills.

## Shortcut To Avoid

- Do not infer knowledge from the final social outcome.
- Do not give the target person the narrator's information.

## Common Failure Modes

- Forgetting that absence means lack of exposure.
- Treating surprise as proof of prior knowledge.
- Mixing up `speaker knew` with `remark was harmful`.

## Minimal Pair

- Case A: the target saw or was told the fact, so they know it.
- Case B: the target missed it or forgot it, so they do not know it.

## Boundary Stress Test

- `Did she know he had lost his job?` -> this skill.
- `Was it rude to mention the job loss?` -> `skill1`.

## Generalization Note

- The transferable core is information-access tracking: determine what a person knows from what they saw, heard, remembered, or missed, without importing narrator knowledge.
