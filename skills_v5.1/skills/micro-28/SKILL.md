---
name: micro-28
level: micro
layer: L4
family: "emotion-appraisal"
description: "Detects when a character's outward emotional expression differs from their privately felt emotion."
---

# Hidden Emotion

## Use When
- Use when the question asks what a character really feels despite a different facial expression, tone, posture, or statement.
- Use when the scene gives evidence for both an internal appraisal and an external display, and they conflict.
- Use when the answer depends on separating private affect from public expression rather than explaining the social rule for the display.
- Use when a character smiles, laughs, says they are fine, stays calm, or acts pleased while the situation suggests sadness, anger, fear, disappointment, embarrassment, or worry.

## Do Not Use When
- Do not use when the task only asks what emotion naturally follows from an event and there is no conflicting outward display; use Basic Emotion Appraisal instead.
- Do not use when the true emotion itself is surprising or nonstandard, with no masking or mismatch; use Atypical Emotion instead.
- Do not use when the main question is why a character hides emotion because of politeness, professionalism, role, culture, or etiquette; use Emotional Disguise and Display Rules instead.
- Do not use when guilt, shame, pride, gratitude, blame, or responsibility appraisal is the core issue; use Moral Emotion instead.
- Do not use when the question is about whether the display is socially appropriate, harmful, or offensive rather than whether it mismatches private feeling.

## Decision Variable
internal emotion versus external expression

## Trigger Checklist
- A private emotional cause is present, such as loss, rejection, disappointment, threat, humiliation, or frustration.
- An outward display is described, such as smiling, laughing, staying calm, saying 'I'm fine,' congratulating someone, or acting cheerful.
- The outward display is not the emotion that the private situation would normally produce.
- The question asks for the real feeling, hidden feeling, inner reaction, or mismatch between appearance and emotion.
- The social reason for masking may be present, but it is not the main variable needed to answer.

## Workflow
- Identify the event or information that affects the character privately.
- Infer the likely internal emotion from that private appraisal.
- Identify the character's observable expression, words, or behavior.
- Compare the internal emotion with the external display.
- If they diverge, answer with the private emotion and note that the display is not reliable evidence of the true feeling.
- Keep the explanation focused on the mismatch; do not turn the answer into a full account of etiquette, moral responsibility, or persuasion.

## Special Case
**Polite smile with private disappointment**: When a character outwardly responds positively to avoid exposing disappointment, treat the real emotion as the one supported by the private outcome, not by the smile.

Scene: Maya wanted the lead role in the play. Her friend got the role instead. When the cast list was announced, Maya smiled and said, 'That's wonderful, congratulations.' Later she sat alone looking upset.
Question: How does Maya really feel when she congratulates her friend?
Answer logic: The role outcome frustrates Maya's goal, so her private emotion is disappointment or sadness. The smile and congratulations are the outward display. Because the private appraisal and public expression conflict, this is hidden emotion.

## Boundary Exit Rule
- Exit to Basic Emotion Appraisal if there is only an event-to-emotion inference and no conflicting display.
- Exit to Atypical Emotion if the character's actual emotion is unusual but openly shown.
- Exit to Emotional Disguise and Display Rules if the key question is the norm, role, or strategy that explains why the character controls the display.
- Exit to Moral Emotion if the hidden feeling is mainly produced by responsibility, blame, guilt, shame, pride, or gratitude.
- Exit to a pragmatics or deception unit if the central issue is whether a spoken claim is true or intended to mislead, rather than what emotion is privately felt.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when a scene contrasts a character's private emotional state with a different outward expression or statement.
