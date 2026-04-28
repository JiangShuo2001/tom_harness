"""StoryModel — the external ToM state object.

Design brief
------------
LLMs are bad at maintaining solid state across multi-step reasoning. They
are great at structured parsing. So: parse the story ONCE into a rigorous
state object, then let deterministic Python code answer every subsequent
question against that state. This is the pattern proven by S02
(quantifier_solve) — extended here to false-belief and knowledge tasks.

The StoryModel captures four things:

  1. sentences[] — the story tokenised by sentence, so every fact we
     record can cite its source.
  2. characters[] — the agents. Name consistency is critical.
  3. events[]    — the ordered timeline. Each event is a tuple
     (actor, action, object, from-loc, to-loc, observers, sentence_id).
     Observers are the subset of characters who were present and able to
     perceive the event.
  4. declarations[] — explicit factual statements that aren't events
     ("Lilei has never seen a carrot"). These populate character
     knowledge gaps separately from perception.

From these four lists every belief / knowledge question the benchmark
asks can be answered by graph queries rather than LLM imagination:

  - "What does C think about object X's location?" →
      look up the latest event in which X moved AND C was an observer;
      if none, fall back to latest observation of X by C; else unknown.

  - "Does C know Fact F?" →
      F ∈ C.explicit_knowledge ∪ C.implicit_knowledge ?
      implicit_knowledge is populated from context (e.g., "meets her
      retired neighbour" → C knows neighbour is retired).

The LLM is invoked only to build this model; every downstream skill
reads it mechanically.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────────────────────────

ActionKind = Literal[
    "put", "move", "hide", "take",             # object manipulation
    "enter", "leave",                           # presence change
    "see", "look", "observe",                   # pure perception
    "say", "declare",                           # speech act
    "arrive", "depart",                         # location change
    "other",
]


class Event(BaseModel):
    """A single story event with explicit perceivers."""
    event_id: str
    order: int                                   # temporal rank (0, 1, 2, ...)
    sentence_id: int                             # index into StoryModel.sentences
    actor: str | None = None                     # who performed the action
    action: ActionKind = "other"
    object: str | None = None                    # what was acted upon
    from_location: str | None = None
    to_location: str | None = None
    observers: list[str] = Field(default_factory=list)   # who perceived it


class Declaration(BaseModel):
    """An explicit propositional statement in the story.

    Distinct from Event: these are background facts ("C has never seen X",
    "the ribs were made by Aunt Wang", "uncle Liu is retired"). They are
    credited to a character's knowledge iff the story establishes that
    character observed/heard the declaration.
    """
    sentence_id: int
    subject: str                                 # what the fact is about
    predicate: str                               # the claimed property
    polarity: bool = True                        # True iff affirmative
    known_by: list[str] = Field(default_factory=list)   # which chars know this
    not_known_by: list[str] = Field(default_factory=list)   # explicitly ignorant


class StoryModel(BaseModel):
    """The full externalized state derived from a story."""
    sentences: list[str] = Field(default_factory=list)
    characters: list[str] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    declarations: list[Declaration] = Field(default_factory=list)
    # parser-level metadata for debugging
    parse_meta: dict[str, Any] = Field(default_factory=dict)

    # ─── Graph queries ────────────────────────────────────────────────────

    def events_observed_by(self, character: str) -> list[Event]:
        """All events in which `character` is an observer, in temporal order."""
        return sorted(
            (e for e in self.events if character in e.observers),
            key=lambda e: e.order,
        )

    def latest_known_location(self, character: str, obj: str) -> str | None:
        """Last location `character` perceived for `obj`, or None if never observed.

        Follows the standard Sally-Anne semantics: if `character` was
        absent when `obj` moved, their belief is frozen at the pre-move
        state. If `character` is the mover or was present, their belief
        tracks reality.
        """
        last_loc: str | None = None
        for e in self.events_observed_by(character):
            if e.object != obj:
                continue
            # Object-manipulation events tell us a new location
            if e.action in {"put", "move", "hide", "take"} and e.to_location:
                last_loc = e.to_location
            elif e.action in {"see", "look", "observe"} and e.to_location:
                last_loc = e.to_location
            # from_location at time of observation is also informative
            elif e.from_location:
                last_loc = e.from_location
        return last_loc

    def actual_location(self, obj: str) -> str | None:
        """The true current location of `obj` after all events."""
        last_loc: str | None = None
        for e in sorted(self.events, key=lambda e: e.order):
            if e.object == obj and e.action in {"put", "move", "hide", "take"}:
                if e.to_location:
                    last_loc = e.to_location
                elif e.from_location:
                    last_loc = e.from_location
        return last_loc

    def character_knows(self, character: str, subject: str, predicate: str) -> str:
        """Three-value answer: 'yes' | 'no' | 'unknown'.

        - 'yes' iff character ∈ declaration.known_by for matching (subject, predicate)
        - 'no' iff character ∈ declaration.not_known_by
        - 'unknown' otherwise (no declaration recorded)
        """
        for d in self.declarations:
            if d.subject == subject and predicate.lower() in d.predicate.lower():
                if character in d.not_known_by:
                    return "no"
                if character in d.known_by:
                    return "yes"
        return "unknown"

    def characters_present_at(self, event_order: int) -> set[str]:
        """All characters who are in-scene just before event at `event_order`.

        Computed from the running trace of enter/leave events up to that point.
        """
        present: set[str] = set(self.characters)   # default: everyone in scene
        for e in sorted(self.events, key=lambda e: e.order):
            if e.order >= event_order:
                break
            if e.action == "leave" and e.actor:
                present.discard(e.actor)
            elif e.action in {"enter", "arrive"} and e.actor:
                present.add(e.actor)
        return present


# ─────────────────────────────────────────────────────────────────────────────
# JSON schema description (for LLM structured output)
# ─────────────────────────────────────────────────────────────────────────────

PARSER_SCHEMA_HINT = """\
Output ONLY a JSON object matching this schema:
{
  "sentences": ["<sentence 1>", "<sentence 2>", ...],
  "characters": ["<name>", ...],
  "events": [
    {
      "event_id": "e1",
      "order": 0,
      "sentence_id": 0,
      "actor": "<name or null>",
      "action": "<put|move|hide|take|enter|leave|see|look|observe|say|declare|arrive|depart|other>",
      "object": "<thing or null>",
      "from_location": "<place or null>",
      "to_location": "<place or null>",
      "observers": ["<name>", ...]
    }, ...
  ],
  "declarations": [
    {
      "sentence_id": 0,
      "subject": "<what the fact is about>",
      "predicate": "<the claimed property>",
      "polarity": true,
      "known_by": ["<name>", ...],
      "not_known_by": ["<name>", ...]
    }, ...
  ]
}

Rules for observers:
- The actor of an event is ALWAYS an observer of that event.
- Include every character who was present in the scene and not said to be absent.
- If the story says "X leaves" before an event, X must NOT be an observer.
- If the story says "while X is away / X returns", X observes nothing between
  the leave and return.

Rules for declarations:
- Extract explicit factual sentences that aren't object movements.
- Populate known_by for characters the story says witnessed/were told the fact.
- Populate not_known_by only when the story EXPLICITLY states the character
  does not know (e.g., "never seen", "unaware", "does not know", "一无所知").
- Do NOT fabricate; when uncertain, leave both lists empty.
"""
