# FB-02 Reference

## Decision Variable

- The key variable is the outer thinker's model of the inner thinker's belief, not the real location and not the inner thinker's raw belief alone.

## Route Signal

- Use this skill when the prompt explicitly asks what one character thinks another character will do or believe.

## Hard Boundary

- If only one character's own search location is asked, route to `skill3`.
- If the task is about expected contents in a container, route to `skill5`.

## Shortcut To Avoid

- Do not answer with reality.
- Do not flatten the two-mind structure into a single belief state.

## Common Failure Modes

- Treating `X thinks Y will look` as if it were just `Y will look`.
- Losing track of who saw the move and who only knows that someone else missed it.
- Choosing the option that matches the latest event instead of the outer model.

## Minimal Pair

- Case A: first-order question asks where Y will look. Use `skill3`.
- Case B: second-order question asks where X thinks Y will look. Use this skill.

## Boundary Stress Test

- `Where does Li Lei think Han Meimei will search?` -> this skill.
- `Where will Han Meimei search?` -> `skill3`.

## Generalization Note

- The transferable core is nested perspective tracking: model what one character thinks another character believes without collapsing the two minds into one.
