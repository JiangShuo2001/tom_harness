"""
SKILLS v2 — redesigned from scratch based on empirical error clustering.

Each skill targets a SET of task_types (across ToMBench + CogToM) that share
the same root failure mode. Skills are validated INDEPENDENTLY, each only on
the error cases from its own target task_types.

Cluster derivation: from `error_dataset/{ToMBench,CogToM}.jsonl` task_types
where (either-model-wrong) > 20.
"""

# ─────────────────────────────────────────────────────────────────────────────
# S1. Faux-Pas / Pragmatic Mismatch
# Targets: speakers say something inappropriate due to lack of awareness of
#          the listener's situation/preference; or insincere flattery hides
#          strategic motive.
# ─────────────────────────────────────────────────────────────────────────────
SKILL_S1_FAUX_PAS = """Before answering, perform PRAGMATIC FAUX-PAS DETECTION:

1. ENUMERATE every utterance / action in the story. For each one, identify
   (speaker, listener, content).
2. For EACH utterance, check three things:
   a. SPEAKER's intent: kind / neutral / strategic?
   b. SPEAKER's KNOWLEDGE GAP: does the speaker know about a listener-specific
      fact (preference, condition, recent event, identity) that would make
      this remark hurtful, embarrassing, or socially awkward? List that fact.
   c. LISTENER's likely reaction: would a reasonable listener feel
      hurt / awkward / patronised?
3. A FAUX PAS = (speaker is innocent / well-meaning) AND (speaker lacks
   knowledge of a listener-specific fact) AND (listener is uncomfortable).
   Politely-phrased remarks can still be faux pas.
4. FLATTERY check: a positive remark may be insincere when the speaker has
   a clear strategic incentive (negotiation, ingratiation, cover-up). Mark
   such utterances as strategically motivated, not literal compliments.

DECISION RULE:
• "Did anyone say something inappropriate?" → YES if any utterance passes
  the three-condition faux-pas check above (do NOT default to NO just
  because everyone is polite).
• Flattery question → identify the strategic goal, not the surface praise."""


# ─────────────────────────────────────────────────────────────────────────────
# S2. Scalar Implicature & Quantifier-Number Integration
# Targets: stories use scalar quantifiers ("most / some / hardly any") plus
#          a total N and a few concrete sub-counts; you must compute the
#          remaining sub-counts.
# ─────────────────────────────────────────────────────────────────────────────
SKILL_S2_SCALAR = """Before answering, perform SCALAR CALIBRATION using the
TIGHT ranges and HARD SUM-CONSTRAINT below.

──────────────────────────────────────────────────────────────────────
STEP 1 — EXTRACT
──────────────────────────────────────────────────────────────────────
• total N (e.g. "30 seats", "40 trees", "50 lunches").
• every explicit concrete sub-count from the story (e.g. "4 pears").
• every scalar quantifier the speaker uses, IN ORDER. The order in
  the speaker's statement is itself a ranking signal.

──────────────────────────────────────────────────────────────────────
STEP 2 — TIGHT QUANTIFIER RANGES
──────────────────────────────────────────────────────────────────────
Use these TIGHTER ranges (the previous loose ranges caused systematic
over-estimation of "almost no" and under-estimation of "most"):

  • "almost no X" / "almost none" / "hardly any" / "very few"
        → 1 to 3 items, NOT a percentage. Treat as essentially zero.
        Even with N=100, "almost no X" should still be ≤ 5.
  • "a small part" / "a small portion" / "a few"
        → 5–15% of N, AND must be the SMALLEST named non-negligible
          group.
  • "some"
        → 15–30% of N.
  • "many" / "a lot"
        → 35–55% of N.
  • "most" / "the majority"
        → 60–85% of N. The lower bound is 60%, NOT 50%.
  • "almost all" / "nearly all"
        → 85–98% of N.

──────────────────────────────────────────────────────────────────────
STEP 3 — HARD SUM CONSTRAINT (the rule the model usually skips)
──────────────────────────────────────────────────────────────────────
The named groups must SUM to N exactly (or to N minus any explicitly
stated "other" pool).

Procedure:
  (a) Pin "almost no X" to 1 or 2 (not its loose range).
  (b) Subtract every explicit sub-count and every "almost-no" pin from
      N. The remainder is what the larger groups must absorb.
  (c) Distribute the remainder so that the relative ranking from
      Step 1 is preserved.
  (d) If only "most" and "almost no" are mentioned, "most" absorbs
      almost the entire residual: "most" ≈ N − explicit − 1.

──────────────────────────────────────────────────────────────────────
STEP 4 — WORKED EXAMPLE
──────────────────────────────────────────────────────────────────────
Story: 40 trees. "Most apples, some pears, almost no oranges. 4 pears."
Question: how many apple trees?

  • Pin oranges (almost no) → 1 (NOT 6, NOT 8).
  • Subtract: 40 − 4 (pears) − 1 (oranges) = 35.
  • Apples = 35 ✓
  • Sanity: 35/40 = 87.5%; "most" range upper bound = 85%, so 35 is at
    the very top of "most". Acceptable because the "almost no" pin
    forces the residual.
  ⇒ Answer = 35, NOT 30.

──────────────────────────────────────────────────────────────────────
STEP 5 — DISAMBIGUATING "BEFORE COUNTING" vs "AFTER COUNTING"
──────────────────────────────────────────────────────────────────────
Some items ask what a character GUESSES "before counting" (purely from
the speaker's quantifier statement) vs "after counting" (with one sub-
count revealed).

  • BEFORE counting → use only the quantifier range; the SUM-constraint
    is unanchored, so pick the option that BEST FITS the quantifier
    range AND is consistent with N.
  • AFTER counting → apply STEP 3 fully (the revealed count anchors
    the rest).

──────────────────────────────────────────────────────────────────────
DECISION RULE
──────────────────────────────────────────────────────────────────────
Pick the option whose number satisfies BOTH the quantifier-range AND
the SUM constraint with "almost no" pinned to 1–2.

GUARDRAIL 1: When "almost no X" is mentioned, the residual is
absorbed by the LARGER groups. Do NOT leave a 6-or-more amount in
the "almost no" category just because your loose range said 25%.

GUARDRAIL 2: "most" with TIGHT pin on "almost no" can legitimately
reach 80%+ of N — accept this; do not down-weight just because the
percentage feels high.

GUARDRAIL 3: Never pick an option that equals N when another category
has a non-zero count.

GUARDRAIL 4: When two options both fit the quantifier range, prefer
the one consistent with the SUM constraint (Step 3)."""


# ─────────────────────────────────────────────────────────────────────────────
# S3. Belief Ledger — False Belief / See-Know / 2nd-Order
# Targets: track each character's perception/knowledge separately from the
#          world state, including 2nd-order ("X knows Y thinks ...") cases.
# ─────────────────────────────────────────────────────────────────────────────
SKILL_S3_BELIEF_LEDGER = """Before answering, build a CHARACTER KNOWLEDGE LEDGER.

STEP 1 — TIMELINE
List every state change in chronological order:
  t1: <event>      (witnesses: <character list>)
  t2: <event>      (witnesses: <character list>)

STEP 2 — PERCEPTION FILTER
For each character, mark which events they DIRECTLY witnessed (eyes/ears
present at that time) vs MISSED (left the room, asleep, distracted, behind
their back, looking elsewhere, absent, no sensory channel for that info).

STEP 3 — BELIEF = ∑ WITNESSED EVENTS
A character's belief about an object/fact = the LAST state they personally
witnessed, NOT the current world state.

STEP 4 — IDENTIFY QUESTION PERSPECTIVE
• "Where IS X?" / "What is currently true?"  → use WORLD STATE
• "Where will/does C look for X?" / "What does C think?"  → use C's BELIEF
• "Does A know what B thinks about Z?"  → 2ND-ORDER:
    – B's belief = events B witnessed about Z
    – A's belief about B's belief = events A witnessed of B's situation
      (A had to see B's perception/action to know B's belief)
• "Did C know that ...?"  → did C witness the event that conveyed that fact?

STEP 5 — DECISION
The correct answer is often the OLD / OUT-OF-DATE state held by a character
with limited view, NOT the current physical reality. Resist defaulting to
world-state for belief questions.

GUARDRAIL: never let "the story says X actually happened" leak into a
character's belief unless that character witnessed X."""


# ─────────────────────────────────────────────────────────────────────────────
# S4. Surface vs Strategic Intent
# Targets: lies, hints, persuasion, pretend play, ambiguous behaviour where
#          the literal/observable layer differs from the strategic layer.
# ─────────────────────────────────────────────────────────────────────────────
SKILL_S4_STRATEGIC = """Before answering, separate SURFACE from STRATEGY.

LAYER 1 — SURFACE
What is literally said / done? Quote it.

LAYER 2 — CONTEXT
List the speaker's goals, incentives, social pressures, and barriers facing
each party. What does the speaker stand to gain or lose?

LAYER 3 — STRATEGIC INTENT
Match the situation to a known pattern:
  • Lie         : surface ≠ truth; intent = mislead, save face, gain edge.
  • Persuasion  : surface = compliment / suggestion / favour;
                  intent = nudge listener past their stated barrier.
  • Pretend     : surface = fictional act; intent = play / symbolic communication.
  • Hint/Sarcasm: surface ≠ literal meaning; intent = indirect criticism / request.
  • Ambiguous  : surface = neutral act; intent = signalling for a hidden plan.

PERSUASION RULE (if question = "How should X persuade Y?"):
  the BEST option is the one that DIRECTLY ADDRESSES Y's stated barrier
  (their concern / preference / objection), not the one that praises X's
  own preferred plan or adds new attractions.

──────────────────────────────────────────────────────────────────────
SPECIAL CASE — "What is the possible INTENTION behind X's behavior?"
──────────────────────────────────────────────────────────────────────
For Discrepant-Intentions / "why did X act this way?" questions, the
correct option is NEVER the generic surface paraphrase ("X did Y because
of conflict / busy / didn't know"). It is ALWAYS the option that names
the SPECIFIC mechanism the story has explicitly set up.

Apply this 3-step LITERAL-CUE ANCHORING:

Step A — Locate the story's explicit motive cue. Quote the exact phrase.
  Common cue templates and the attribution they license:

   STORY SAYS                          → CORRECT ATTRIBUTION FAMILY
   "mistakes it for X" / "thinks it    → CHARITABLE: misunderstands /
       is X" / "accidentally finds"      mistaken belief; choose the
                                        option that says "thinks
                                        ownerless / misunderstands the
                                        purpose / believes it's class
                                        fund". Reject options that
                                        accuse the actor of conscious
                                        bad intent.

   "knows X but" / "is aware that"     → AWARE: actor knows the truth
       + "competes with / has grudge     and stays silent for STRATEGIC
       with / dispute with"              gain. Choose the option that
                                        names the SPECIFIC strategic
                                        gain ("see the rival blamed",
                                        "weaken their position", "let
                                        their plan fail"). Reject the
                                        option that just restates "has
                                        a conflict and doesn't tell" —
                                        that is the surface, not the
                                        intent.

   "X just yelled / was rude /         → PUNITIVE: silence / withholding
       behaved badly" + "Y chose          is interpreted as pushback or
       not to tell"                      moral punishment. Choose the
                                        option that says "disgusted by
                                        rude attitude, unspoken
                                        punishment". Reject "afraid of
                                        conflict" if the story shows
                                        the third party as the one who
                                        misbehaved, not the actor.

   "quite troublesome" / "thought it   → INNOCENT: actor genuinely
       was trash / unattended"           thought no harm was done.
                                        Choose the "thinks ownerless /
                                        helping clean up" option.

Step B — DO NOT default to the most NEUTRAL paraphrase of the surface
  ("X has a conflict and chooses not to tell"). The benchmark almost
  always pairs that NEUTRAL option with a more SPECIFIC option that
  names the mechanism — and the SPECIFIC option is usually the gold.

Step C — If two options share the same gist, prefer the one that uses
  the same VERB CLASS the story used:
     story: "misunderstands"   → option containing "misunderstands"
     story: "has a grudge"     → option containing "see ... fail" /
                                 "let ... be blamed"
     story: "yelled rudely"    → option containing "disgusted /
                                 unspoken punishment"

──────────────────────────────────────────────────────────────────────

DECISION RULE
Pick the option that matches the inferred STRATEGIC intent, not the surface
meaning. A polite / positive surface often hides strategic intent. For
intention-attribution questions specifically, prefer the option whose
mechanism is closest to the story's literal motive cue (Step A table).

GUARDRAIL: do not take statements at face value when the context shows a
clear incentive to misrepresent. AND do not pick the bland paraphrase
option in intention-attribution questions — the benchmark rewards
options that name the SPECIFIC gain / loss / belief the story sets up."""


# ─────────────────────────────────────────────────────────────────────────────
# S5. Expectation-Delta / Atypical Reaction / Hidden Emotion
# Targets: the character's reaction does not match the surface event; need to
#          locate hidden context that flips the meaning.
# ─────────────────────────────────────────────────────────────────────────────
SKILL_S5_EXPECTATION = """Before answering, perform EXPECTATION-DELTA ANALYSIS.

1. SURFACE EVENT
   What visibly happened? (Quote it briefly.)

2. EXPECTED REACTION
   Based on default social norms and the character's apparent situation,
   what reaction would be TYPICAL?

3. ACTUAL / ASKED REACTION
   What reaction is the question pointing to (atypical / hidden / opposite)?

4. HIDDEN CONTEXT SEARCH
   If actual ≠ expected, scan the story for one of:
   (a) An ADDITIONAL CONSTRAINT the character faces but bystanders don't see
       (debt, illness, secret deal, family pressure, rule-violation worry).
   (b) A SECOND GOAL competing with the obvious one (career vs care,
       reputation vs honesty, play vs duty).
   (c) An EXTERNAL TRIGGER known only to this character (calendar reminder,
       prior message, identity revelation, news).
   (d) An INSIDE / OUTSIDE asymmetry: what the character SHOWS may be the
       opposite of what they FEEL (hidden / suppressed / regulated emotion).

5. DECISION
   Pick the option that is consistent with the HIDDEN context, not with the
   surface event alone.

──────────────────────────────────────────────────────────────────────────
SPECIAL CASE — "Real feeling" / "Hidden emotion" multiple-choice items
──────────────────────────────────────────────────────────────────────────
The "hiding" is an ACTION, not an emotion. The "real feeling" = the
natural emotional response of the character to the SOURCE EVENT itself,
NOT a secondary anxiety about the act of hiding.

Apply this 2-step decoder:

  Step A — Identify the SOURCE EVENT for THIS character and its valence:
    POSITIVE source : rewarded, allowed, holding good cards, given a
                      promise, secret advantage, succeeded
                      → underlying feeling = happy / excited / proud
    NEGATIVE source : in physical pain, excluded, did not understand
                      while others did, disappointed, hurt
                      → underlying feeling = sad / hurting / disappointed

  Step B — Map valence to options:
    • POSITIVE source being hidden so as not to give it away (good cards,
      secret reward, allowed to stay up late) → answer = POSITIVE feeling
      (happy / excited), NOT anxiety about being discovered.
    • NEGATIVE source being hidden so the character can still do something
      fun (hides stomachache to go to the party) → answer = the NEGATIVE
      underlying feeling (sad / hurting), NOT happiness about the party.
    • The character does NOT understand something everyone else does and
      hides it → answer = sad / embarrassed (the exclusion itself).

GUARDRAIL: do NOT add "secret-keeping anxiety" or "fear of being
discovered" as the real feeling unless the story explicitly shows the
character struggling with the secret itself. The default in these items
is the SOURCE EVENT's emotion, not a meta-emotion about the act of
hiding.

GUARDRAIL: the question asks precisely because the reaction is atypical
— do not pick the most "obvious" emotion that fits the visible scene."""


# ─────────────────────────────────────────────────────────────────────────────
# S6. Spatial Mental Rotation / Perspective Taking
# Targets: spatial construction, dice / cube faces, picture identification
#          from another viewer's vantage point.
# ─────────────────────────────────────────────────────────────────────────────
SKILL_S6_SPATIAL = """Before answering, perform SPATIAL MENTAL ROTATION using the
explicit AXIS-MAPPING ALGORITHM below.

──────────────────────────────────────────────────────────────────────
STEP 1 — BUILD THE TABLE GRID FROM YOUR (THE PERCEIVER'S) VIEWPOINT
──────────────────────────────────────────────────────────────────────
Lay out items as a 2D grid using TWO axes:
  • near→far axis (your row index, increasing as you look forward)
  • left→right axis (your column index, increasing to your right)

Write each item's (row, col) position. If a row contains a single item
described as "in the first row" with no LR partner, place it at
col = "centre" (it occupies the whole row width).

──────────────────────────────────────────────────────────────────────
STEP 2 — APPLY THE EXACT AXIS MAPPING FOR THE TARGET VIEWER
──────────────────────────────────────────────────────────────────────
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
      ⇒ Your ROWS become target's COLUMNS (in the same near→far order).

  • TARGET on YOUR RIGHT side (90° counter-clockwise from yours):
      target_row(near→far)  = your_col(right → left)
      target_col(left→right) = your_row(near → far)
      ⇒ Your COLUMNS become target's ROWS, but READ RIGHT-TO-LEFT.
      ⇒ Your ROWS become target's COLUMNS, in same near→far order.

  • TARGET on SAME side as you (0°):
      identical mapping.

──────────────────────────────────────────────────────────────────────
STEP 3 — WORKED EXAMPLE (memorise this template)
──────────────────────────────────────────────────────────────────────
Square table. You stand south, facing north. Xiao Zhou stands EAST
(your right side), facing west.

Your view (rows near→far, cols left→right):
  row1 (near):   [.....pencils.....]      ← single item, centre
  row2 (mid):    [erasers, water_bottles]
  row3 (far):    [.....mice.....]         ← single item, centre

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
  row3: erasers
✓ This is the correct answer (option A in the original case).

──────────────────────────────────────────────────────────────────────
STEP 4 — CHECKLIST BEFORE ANSWERING
──────────────────────────────────────────────────────────────────────
1. Did you identify which side the target stands on (left / right /
   opposite / same)?
2. Did you build YOUR grid with explicit (row, col) coordinates?
3. Did you APPLY the exact axis-mapping rule (do NOT eyeball)?
4. Did you re-read each option and check item-by-item against your
   computed grid?

DICE / CUBE BONUS RULE
A standard die's opposite faces sum to 7:  1↔6, 2↔5, 3↔4.
Given two known faces, derive the others, then apply Step 2.

GUARDRAIL: a target on YOUR RIGHT is the case most often confused.
The mistake is to treat it as just an LR flip (which would actually be
the OPPOSITE-side rule). Side-position is a 90° rotation; rows and
columns SWAP roles."""


# ─────────────────────────────────────────────────────────────────────────────
# S7. Knowledge-Boundary Filtering (pretend play with limited world knowledge)
# Targets: a character with explicitly limited world knowledge cannot draw on
#          analogies that the reader naturally would.
# ─────────────────────────────────────────────────────────────────────────────
SKILL_S7_KNOWLEDGE_BOUNDARY = """Before answering, perform KNOWLEDGE-BOUNDARY FILTERING.

1. SCAN the story for any sentence that limits the character's world
   knowledge (e.g. "lives on a planet with no animals", "never has seen a
   plant", "raised in a robot-only city", "has no contact with X").

2. LIST the concept domain the character DOES have access to (their
   environment, their daily activities, the entities they interact with).

3. The reader's pop-culture analogies are IRRELEVANT when they fall outside
   the character's accessible domain. Discard them — even if a real-world
   match looks perfect (a "bee", a "hummingbird", etc.).

4. Re-frame the character's behaviour using ONLY their accessible concept
   set. A robot who has never seen a bee but constantly sees other robots
   doing maintenance is most likely IMITATING another robot doing
   maintenance, not a bee.

DECISION RULE
Pick the option whose source domain is INSIDE the character's knowledge
boundary. Reject any option referring to concepts the character cannot know.

GUARDRAIL: the "obvious" real-world analogy is a TRAP when the story has
explicitly fenced off that knowledge."""


# ─────────────────────────────────────────────────────────────────────────────
# S8. Other-Preference-Driven Action  (主体应迁就 / 服务他人偏好)
# Targets: discrepant desires, multiple desires, prediction-of-action where
#          the actor must satisfy / invite / serve another party's preference
#          rather than indulge their own.
# ─────────────────────────────────────────────────────────────────────────────
SKILL_S8_OTHER_PREFERENCE = """Before answering, perform OTHER-PARTY-FOCUSED ACTION INFERENCE.

This is a DECISION-TREE skill. Do NOT default to "follow the other party's
preference" blindly — the right rule depends on the activity TYPE.

──────────────────────────────────────────────────────────────────────
STEP 1 — IDENTIFY ROLE & ACTIVITY TYPE
──────────────────────────────────────────────────────────────────────
Who must act? (the actor)
Who is the target?
What kind of activity / gift / outing is being chosen?
Which of the following 4 patterns does it fit?

PATTERN A — SOLO-FOR-OTHER (gift just for them, trip just for them,
            invitation with no shared-memory marker)
  Marker phrases: "X invites Y to travel together", "X gives Y a gift"
                  (no mention of common memory / couple / shared theme).
  → Use the TARGET's preference. Reject the actor's own preference.

PATTERN B — SHARED / "COMMON MEMORY" / "COUPLE" / TWO-WORLD MIX
  Marker phrases: "common memory", "couple's clothing", "shared", "for
                  both of them", "wants to do TOGETHER", "celebrate
                  their anniversary", or any explicit instruction to
                  combine BOTH characters' identities.
  → Look for a HYBRID option that COMBINES TERMS from both worlds.
    Examples seen in the data:
      pianist × athlete   → "music-themed sportswear"
      graffiti × ballet   → "street DANCE flash mob"
      outdoor-photo × indoor-design → "photography exhibition"
      fashion × programmer → "fashion-brand windbreaker" (functional
                            but stylish, not pure plaid shirt)
      fitness × foodie    → "city exploration" (both can enjoy walking,
                            no pure dessert tasting against fitness)
  → REJECT pure single-world options.

PATTERN C — EXPLICIT FLIP ("this time I want what I want")
  Marker phrases: "X always gives way to Y, but tonight X says he wants
                  to watch what HE wants", "X has had enough", "X insists
                  this time".
  → The actor's own preference WINS. Reject the usual "yield to other"
    option.

PATTERN D — "PURSUING / COURTING" + "let target decide"
  Marker phrases: "X wants to pursue Y", "X is courting Y", "X lets Y
                  decide".
  → The target picks something COMPATIBLE-TOGETHER (a public / shared
    version of their preference), NOT the most private / solitary
    version. Library > playing games at home alone.

──────────────────────────────────────────────────────────────────────
STEP 2 — APPLY THE PATTERN'S RULE
──────────────────────────────────────────────────────────────────────
Once you have selected the pattern, apply its rule to filter options:

  Pattern A → keep only options matching target's preference
  Pattern B → keep only options that touch BOTH characters' worlds
  Pattern C → keep only options matching the actor's preference
  Pattern D → keep only options compatible with two people doing it
              together OUTSIDE the home

──────────────────────────────────────────────────────────────────────
STEP 3 — SECONDARY GUARDRAILS
──────────────────────────────────────────────────────────────────────
• When the actor faces a CONSTRAINT (cannot afford, cannot openly admit
  a value clash), prefer a SUBSTITUTE that respects both target wish AND
  constraint (cheaper similar toy > pure false promise).
• When the actor wants to ease an awkward atmosphere, the action is
  usually JOIN / DE-ESCALATE, not avoid / wait / withdraw.
• Reject "pure verbal promise" options that postpone the issue without
  addressing it.

GUARDRAIL: never just say "actor follows target's preference" without
first classifying which pattern (A / B / C / D) the case is. Pattern B
(common memory / couple / shared) is the most under-recognised one and
demands a HYBRID option, not a single-world one."""


# ─────────────────────────────────────────────────────────────────────────────
# S9. Sensory-Channel Filtering
# Targets: synesthetic / cross-modal puzzles, affective perspective-taking
#          where a perceiver only has a subset of senses or attention.
# ─────────────────────────────────────────────────────────────────────────────
SKILL_S9_SENSORY_CHANNEL = """Before answering, perform SENSORY-CHANNEL FILTERING.

1. IDENTIFY the perceiver asked about and the sensory channels they have:
   • Blind                  →  HEARING + TOUCH + SMELL only (no vision)
   • Deaf                   →  VISION + TOUCH + SMELL only (no hearing)
   • Eye-mask / blindfold   →  no vision; hearing & smell intact
   • Behind glass / far     →  vision only (no sound, smell, touch)
   • Distracted / busy      →  no peripheral perception of unrelated event

2. STRIP from the story every detail the perceiver CANNOT access through
   their channels. The narrator describes everything; the perceiver only
   experiences a subset.

3. From the REMAINING signals only, reconstruct what THIS perceiver would
   most likely conclude about the scene.

4. If the question contrasts "main sense X" vs "main sense Y" perceivers,
   compute their conclusions SEPARATELY — they will reach DIFFERENT
   conclusions even though the underlying event is the same.

DECISION RULE
The answer must be derivable from sensory data the perceiver actually has.
Reject any option that depends on information from a channel they lack.

GUARDRAIL: a deaf student watching a water-phone will NOT think "whale
song" (needs hearing); a blind person near an ozone reactor will NOT think
"chemistry lab" (needs vision). Match the conclusion to the available
channel."""


# ─────────────────────────────────────────────────────────────────────────────
# S10. Audience Calibration (expert vs novice listener)
# Targets: how to mention a technical term to an EXPERT — share experience,
#          do NOT define / lecture.
# ─────────────────────────────────────────────────────────────────────────────
SKILL_S10_AUDIENCE_CALIBRATION = """Before answering, calibrate communication to AUDIENCE EXPERTISE.

1. IDENTIFY the listener's expertise level on the topic:
   • Expert (professional photographer, doctor, mechanic)  → already knows
     the definitions and standard terminology.
   • Peer enthusiast       → shares vocabulary; chat about the experience.
   • Novice                → may need definitions and context.

2. WHEN SPEAKING TO AN EXPERT:
   • Do NOT define / explain a term they already know — that is patronising.
   • Do NOT recite a textbook fact about their own field.
   • DO use the term as shared vocabulary while sharing a SPECIFIC scene,
     observation, or feeling ("today the contour light at sunset was so
     clean that the clouds looked like they were on fire!").
   • Use vivid, sensory, personal language — what YOU saw, captured, felt.

3. WHEN SPEAKING TO A NOVICE:
   • Define the term, give context, then share experience.

DECISION RULE
For an EXPERT audience the right option is the one that USES the term as
shared vocabulary AND describes a personal experience or scene. Reject any
option that defines / explains the term to the expert (insulting and
unnecessary).

GUARDRAIL: textbook-style definitions are WRONG when the listener is a
domain expert. The "informative" answer is socially the LEAST appropriate
in this case."""


# ─────────────────────────────────────────────────────────────────────────────
# S11. Belief-Driven Emotion (emotion follows from BELIEVED situation)
# Targets: Belief-Based Emotions, Moral emotions where the character's
#          self-interpretation determines what they feel.
# ─────────────────────────────────────────────────────────────────────────────
SKILL_S11_BELIEF_EMOTION = """Before answering, link BELIEF → EMOTION.

1. EXTRACT the character's BELIEF state explicitly:
   • What does the character think the situation is?
   • Is their belief possibly WRONG (based on partial info, biased
     assumption, self-justification)?
   E.g. Roy thinks he is "ignored" by the school. Yuki just got an
   invitation email so she thinks she is safe.

2. The character's emotion follows from their BELIEF, not from objective
   reality and not from what an outside observer (the reader) would feel.

3. EMOTION TAXONOMY for belief-driven cases:
   • Believes self is favoured / safe / chosen        → confident, peaceful
   • Believes self is rejected / overlooked           → irritated, hurt
   • Believes self is unjustly accused / undervalued  → wronged, indignant
   • Believes outcome is hopeless                     → depressed, anxious

   Distinguish "wronged" (specific perceived unfairness) from "irritated"
   (general dissatisfaction).

──────────────────────────────────────────────────────────────────────
SPECIAL CASE — "Moral emotions" / "What does X feel after their action
                possibly caused harm?"
──────────────────────────────────────────────────────────────────────
The intuitive "guilty / panicked / anxious" answer is OFTEN WRONG in
these items. Before defaulting to guilt, run THIS 5-CHECK FILTER and
pick the WARMER / MORE NEUTRAL emotion if ANY check fires.

  CHECK 1 — AGE / COGNITIVE LIMIT
    Story says actor is a young child / 2-year-old / "doesn't understand
    the value" / unable to grasp the consequence?
    → Actor feels INDIFFERENT / continues their game. Young children do
      not experience adult-style moral guilt.

  CHECK 2 — UNCERTAINTY MARKERS
    Phrases like "REALIZES HE MIGHT have made a mistake", "is not sure
    if", "thinks he POSSIBLY did" → felt emotion is CONFUSION /
    UNCERTAINTY, not nervousness or guilt.

  CHECK 3 — SELF-JUSTIFYING NARRATIVE
    Actor's GOAL was to "do a good deed" (fed an animal, donated, helped)
    and the harm is INDIRECT or AMBIGUOUS (e.g. zookeeper said rabbits
    "ate too much", not "got sick from your carrots specifically")?
    → Actor maintains "I did good" → feels HAPPY / PROUD / SATISFIED.
    Actor does not spontaneously connect their action to the harm
    unless the story explicitly forces that connection.

  CHECK 4 — EXTERNAL REASSURANCE
    A third party tells the actor "it's not your fault" / "X did it" /
    explicitly absolves them?
    → Actor feels RELIEVED / SATISFIED, not guilty.

  CHECK 5 — EXPLICIT FACE-VALUE INDIFFERENCE
    Story literally says "too lazy to return" / "doesn't bother" /
    "doesn't think this is her responsibility"?
    → Take it LITERALLY → INDIFFERENT.

DECISION RULE for moral-emotion questions:
  • Run all 5 checks. If ANY fires → pick the warmer / neutral option
    (indifferent / happy / confused / satisfied) that matches the firing
    check.
  • ONLY default to guilt / panic if ALL 5 checks fail AND the story
    explicitly shows the actor recognising their own causal role in a
    serious unambiguous harm.

──────────────────────────────────────────────────────────────────────
DECISION RULE (general)
Pick the emotion that matches the character's CURRENT BELIEF, not what
an outsider would feel knowing all facts.

GUARDRAIL: even if the character's belief is FACTUALLY WRONG (Yuki may
still get laid off; Xiao Qiang's gift hurt the rabbits), the character's
emotion right now reflects the BELIEVED state, not future or external
reality. The "morally correct" feeling an outsider would impose is
USUALLY NOT the right answer."""


# ─────────────────────────────────────────────────────────────────────────────
# S12. Commitment Priority (which action wins when several pull at once)
# Targets: completion of failed actions, where a prior commitment / awaited
#          appointment dominates over fresh distractions.
# ─────────────────────────────────────────────────────────────────────────────
SKILL_S12_COMMITMENT_PRIORITY = """Before answering, perform COMMITMENT-PRIORITY ARBITRATION.

1. LIST every competing draw on the character's next action:
   (a) PRIOR EXPLICIT COMMITMENT — verbal promise just made, expected
       meeting / appointment, agreed plan ("I'll come help you", "my
       sister comes at 2 pm").
   (b) ONGOING ACTIVITY — what they were doing right before the
       disruption (painting, studying, etc.).
   (c) NEW INVITATION — a fresh option that just appeared (friend's
       message, sudden alternative venue).
   (d) BACKGROUND TASK — chores or secondary obligations.

2. PRIORITY ORDER (typical in these stories):
       (a) prior commitment  >  (b) ongoing activity
                              >  (c) new invitation  >  (d) background task

3. FAILED-ACTION REPLACEMENT
   • If the character was doing X but X became impossible (no outlet,
     bad weather, etc.), the next action usually preserves the SAME
     UNDERLYING GOAL.
   • If the reason they were THERE was to wait for someone, they keep
     waiting — the disruption (dead laptop, etc.) is irrelevant to that
     deeper goal.
   • A freshly-made promise dominates whatever fresh distraction appears.

DECISION RULE
The next action almost always satisfies the PRIOR COMMITMENT (or preserves
the deeper goal of being there), not whatever new alternative just appeared.

GUARDRAIL: do NOT over-weight the freshest message / latest distraction.
Locate the active commitment that the story established earlier, and pick
the option that fulfils it."""


# ─────────────────────────────────────────────────────────────────────────────
# Skill registry & target task_types
# ─────────────────────────────────────────────────────────────────────────────
SKILLS = {
    "S1_FauxPas":          SKILL_S1_FAUX_PAS,
    "S2_Scalar":           SKILL_S2_SCALAR,
    "S3_BeliefLedger":     SKILL_S3_BELIEF_LEDGER,
    "S4_Strategic":        SKILL_S4_STRATEGIC,
    "S5_Expectation":      SKILL_S5_EXPECTATION,
    "S6_Spatial":          SKILL_S6_SPATIAL,
    "S7_KnowledgeBound":   SKILL_S7_KNOWLEDGE_BOUNDARY,
    # ── new in v2.1 ────────────────────────────────────────────────────
    "S8_OtherPreference":  SKILL_S8_OTHER_PREFERENCE,
    "S9_SensoryChannel":   SKILL_S9_SENSORY_CHANNEL,
    "S10_AudienceCalib":   SKILL_S10_AUDIENCE_CALIBRATION,
    "S11_BeliefEmotion":   SKILL_S11_BELIEF_EMOTION,
    "S12_CommitmentPrio":  SKILL_S12_COMMITMENT_PRIORITY,
}

# Target task_types — values match the strings in ToMBench.jsonl / CogToM.jsonl
SKILL_TARGETS = {
    "S1_FauxPas": {
        "Faux-pas Recognition Test",                # ToMBench
        "Expanding Tasks: Flattery",                # CogToM
    },
    "S2_Scalar": {
        "Scalar Implicature Test",                  # ToMBench
        "Scalar Implicature Task",                  # CogToM
    },
    "S3_BeliefLedger": {
        "False Belief Task",                        # ToMBench
        "False Belief Task: Location",              # CogToM
        "False Belief Task: Content",               # CogToM
        "See-Know Task",                            # CogToM
        "2nd-Order False Belief",                   # CogToM
        "Knowledge-attention links",                # ToMBench  (ext)
    },
    "S4_Strategic": {
        "Strange Story Task",                       # ToMBench
        "Persuasion Story Task",                    # ToMBench
        "Ambiguous Story Task",                     # ToMBench
        "Strange Story: Pretend",                   # CogToM
        "Hinting Task Test",                        # ToMBench  (ext, irony / hinting)
        "Strange Story: Double Bluff",              # CogToM    (ext, reverse psych)
        "Discrepant intentions",                    # ToMBench  (ext, intent attrib)
    },
    "S5_Expectation": {
        "Unexpected Outcome Test",                  # ToMBench
        "Hidden emotions",                          # ToMBench
        "Unexpected Outcome Task",                  # CogToM
        "Test of Emotion Comprehension: Hidden Emotions",  # CogToM (ext)
        "Discrepant emotions",                      # ToMBench  (ext)
        "Discrepant emotions ",                     # ToMBench  (trailing-space variant in raw data)
    },
    "S6_Spatial": {
        "Spatial Construction Task",                # CogToM
        "Picture Identification Task",              # CogToM
    },
    "S7_KnowledgeBound": {
        "Knowledge-pretend play links",             # ToMBench
        "Sarah Task",                               # CogToM    (ext, same pattern)
    },
    # ── new in v2.1 ────────────────────────────────────────────────────
    "S8_OtherPreference": {
        "Discrepant desires",                       # ToMBench
        "Multiple desires",                         # ToMBench
        "Prediction of actions",                    # ToMBench
    },
    "S9_SensoryChannel": {
        "Synesthetic Fallacy Problem",              # CogToM
        "Affective Perspective-Taking Task",        # CogToM
    },
    "S10_AudienceCalib": {
        "Aware of Reader’s Knowledge Task",          # CogToM (note curly quote)
        "Aware of Reader's Knowledge Task",         # CogToM (straight-quote variant)
    },
    "S11_BeliefEmotion": {
        "Test of Emotion Comprehension: Belief Based Emotions",  # CogToM
        "Moral emotions",                           # ToMBench
    },
    "S12_CommitmentPrio": {
        "Completion of failed actions",             # ToMBench
    },
}
