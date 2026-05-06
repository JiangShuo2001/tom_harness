# FP-01 Reference

## Decision Variable

- The key variable is whether a spoken line makes a sensitive fact
  socially harmful in that moment, OR whether a positive remark is
  serving a clear strategic gain rather than a literal compliment.

## Route Signal

- Use this skill when the question targets the remark itself (`Was that
  inappropriate?` / `Which sentence was wrong to say?`) or when the
  question asks for the *purpose* of an obviously strategic compliment.

## Hard Boundary

- If the question asks whether the speaker knew, remembered, or forgot
  the fact, route to `skill2`.
- If the question asks "why did X word it this way" (forgetting, polite
  lie, face-saving, selective truth), route to `skill15`.
- If there is no spoken line to evaluate, do not use this skill.

## Shortcut To Avoid

- Do not label a line as faux pas just because it is negative, awkward,
  or blunt.
- Do not solve by keyword matching without checking social harm.
- Do not default to "sincerely expresses love" when the praise sits in
  a setting with a clear social-influence incentive.

## Common Failure Modes

- Confusing social inappropriateness with factual error.
- Returning a paraphrase instead of the exact offending sentence.
- Smuggling in the speaker-knowledge question when the prompt only asks
  about the remark.
- Taking strategic flattery at face value because it is grammatically a
  compliment.

## Minimal Pair

- Case A: a negative remark with no sensitive fact is blunt but not
  necessarily a faux pas.
- Case B: a mild-looking remark that exposes a painful fact is a faux
  pas.
- Case C: an over-the-top compliment to a powerful audience at a
  networking event is strategic flattery, not literal praise.

## Boundary Stress Test

- `Did he know her grandmother had died?` → `skill2`, not this skill.
- `Which sentence was inappropriate?` → this skill.
- `Why did she compliment him on his project right before asking for a
  raise?` → this skill, strategic-flattery branch.
- `Why did she politely say "it's fine" instead of telling him she was
  upset?` → `skill15`.

## Generalization Note

- The transferable core is social-harm detection from dialogue context:
  identify when a spoken line exposes a sensitive fact in a way that
  embarrasses or hurts the listener; or when a positive remark is best
  read as a strategic move rather than a literal compliment.
