---
name: skill16
description: Use for SP-01 spatial perspective taking — what does a target viewer see from their vantage point, including dice / cube faces, picture identification, and multi-viewer table layouts — by applying an EXACT axis-mapping algorithm rather than eyeballing the rotation.
---

# SP-01 Spatial Perspective Taking

## Use When

- The story involves a spatial layout, a dice / cube, or multiple
  viewers at different positions on a table.
- The question asks what someone sees, draws, or describes from a
  particular vantage point ("what face does X see?", "which picture
  matches X's view?", "what does the table look like to X?").

## Do Not Use When

- The story has a sensory-channel restriction (blind / deaf / behind
  glass) that determines the conclusion. Use `skill19` for the
  conclusion; only use `skill16` for the geometry sub-step.
- The task is about belief, intention, or emotion rather than
  geometry.

## Trigger Checklist

- Is there a 2-D table grid or a 3-D cube / dice?
- Does the question name a specific viewer position (north / south /
  east / west, "opposite", "your left", "your right", "same side")?
- Is the asked output a per-viewer view of the layout?
- If yes, use this skill.

## Workflow

1. Identify YOUR viewpoint and the TARGET viewer's position relative
   to you.
2. Build YOUR grid with explicit `(row, col)` coordinates.
3. Apply the EXACT axis-mapping rule for the target's position
   (see Detailed Procedure below). DO NOT eyeball.
4. Re-check each option item-by-item against your computed grid.
5. For dice / cubes, use the bonus rule (opposite faces sum to 7).

## Detailed Procedure — Axis-Mapping Algorithm

```
STEP 1 — BUILD THE TABLE GRID FROM YOUR (THE PERCEIVER'S) VIEWPOINT
  Lay out items as a 2-D grid using TWO axes:
    • near→far axis (your row index, increasing as you look forward)
    • left→right axis (your column index, increasing to your right)

  Write each item's (row, col) position. If a row contains a single
  item described as "in the first row" with no LR partner, place it
  at col = "centre" (it occupies the whole row width).

STEP 2 — APPLY THE EXACT AXIS MAPPING FOR THE TARGET VIEWER
There are FOUR canonical positions. Memorise these mappings; do NOT
"freestyle" the rotation reasoning.

  • TARGET on the OPPOSITE side (180°):
      target_row(near→far)  = your_row(far → near)
      target_col(left→right) = your_col(right → left)
      ⇒ LR within each row reverses; rows reverse top-to-bottom.

  • TARGET on YOUR LEFT side (90° clockwise from yours):
      target_row(near→far)  = your_col(left → right)
      target_col(left→right) = your_row(near → far)
      ⇒ Your COLUMNS become target's ROWS (in the same LR order).
      ⇒ Your ROWS become target's COLUMNS (in the same near→far
        order).

  • TARGET on YOUR RIGHT side (90° counter-clockwise from yours):
      target_row(near→far)  = your_col(right → left)
      target_col(left→right) = your_row(near → far)
      ⇒ Your COLUMNS become target's ROWS, but READ RIGHT-TO-LEFT.
      ⇒ Your ROWS become target's COLUMNS, in same near→far order.

  • TARGET on SAME side as you (0°):
      identical mapping.

STEP 3 — WORKED EXAMPLE (memorise this template)
Square table. You stand south, facing north. Xiao Zhou stands EAST
(your right side), facing west.

Your view (rows near→far, cols left→right):
  row1 (near):   [.....pencils.....]      ← single item, centre
  row2 (mid):    [erasers, water_bottles]
  row3 (far):    [.....mice.....]          ← single item, centre

Convert to a 3×3 grid by item position:
  (col=L, row=mid) = erasers
  (col=R, row=mid) = water_bottles
  (col=C, row=near)= pencils
  (col=C, row=far) = mice

Apply the RIGHT-side rule (target_row = your_col read R→L):
  Zhou's row1 (near) = your col=R    ⇒ contains: water_bottles
  Zhou's row2 (mid)  = your col=C    ⇒ contains: pencils (Zhou-left=
                                       your near), mice (Zhou-right=
                                       your far)
  Zhou's row3 (far)  = your col=L    ⇒ contains: erasers

Zhou sees:
  row1: water bottles
  row2: pencils, mice
  row3: erasers       ← This is the correct answer.

STEP 4 — CHECKLIST BEFORE ANSWERING
1. Did you identify which side the target stands on (left / right /
   opposite / same)?
2. Did you build YOUR grid with explicit (row, col) coordinates?
3. Did you APPLY the exact axis-mapping rule (do NOT eyeball)?
4. Did you re-read each option and check item-by-item against your
   computed grid?
```

## Special Case — Dice / Cube Bonus Rule

A standard die's opposite faces sum to **7**: 1↔6, 2↔5, 3↔4. Given two
known faces, derive the others, then apply Step 2.

> Worked example: pencil = 1 → opposite = 6 = notebook. Reject "book
> = 5" as the opposite of pen=2 (book is opposite some other face);
> always check the 1↔6, 2↔5, 3↔4 pairing first.

GUARDRAIL: a target on **YOUR RIGHT** is the case most often confused.
The mistake is to treat it as just an LR flip (which would actually be
the OPPOSITE-side rule). Side-position is a 90° rotation; rows and
columns SWAP roles.

## Output Template

- `Task framing`: layout shape (table grid / dice / picture) and the
  target viewer's position.
- `Geometry evidence`: your `(row, col)` grid (or known dice faces).
- `Reasoning decision`: target view computed by the axis-mapping rule.
- `Answer`: the option that matches the target view item-by-item.

## Failure Checks

- Do not eyeball the rotation; apply the rule.
- Treat "your right side" as a 90° rotation, not an LR flip.
- For dice, always check the 1↔6, 2↔5, 3↔4 pairing.
- Re-check each option against your grid before answering.

## Boundary Exit Rule

- If the perceiver has a SENSORY restriction (blind / deaf / behind
  glass / blindfolded), use `skill19` for the conclusion they form;
  use `skill16` only as a sub-step for the geometry.
- If no spatial axis-mapping is required, do not force this skill.

## Answer Discipline

- Quote the axis-mapping rule you used in your reasoning before
  selecting the option.
- Reject options that are similar but differ on one item — the
  benchmark deliberately puts near-twin distractors.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
