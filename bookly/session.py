"""Conversation state, and how it survives a restart.

Two kinds of memory live here, and keeping them apart is deliberate:

  * `messages` is the model's memory -- the transcript it sees each turn.
  * everything else is the *application's* memory -- facts the application knows
    and the model cannot talk its way around. Whether identity was verified and
    whether an eligibility check passed are security-relevant, so they are held
    here as plain Python and consulted by the tool layer, not recalled from the
    transcript by the model.

That split is also why persistence had to be written by hand rather than by
pickling the object: `verified_orders` is a security boundary, so it round-trips
through an explicit schema where you can see exactly what is restored.
"""

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from bookly import store
from bookly.policy import EligibilityResult


@dataclass
class TraceEntry:
    """One observable step, surfaced in the UI so the agent is not a black box."""

    kind: str  # "tool_call" | "tool_result" | "assistant" | "note"
    label: str
    detail: Any = None


@dataclass
class Session:
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    # Model-visible transcript. Plain JSON-serialisable dicts throughout, so a
    # conversation can be written to storage and replayed to the API unchanged.
    messages: list[dict] = field(default_factory=list)

    # What the UI renders. Kept separate from `messages` because the model's
    # transcript contains tool calls and thinking blocks a customer never sees.
    transcript: list[dict] = field(default_factory=list)

    # Application-owned facts. Never inferred from the transcript.
    verified_orders: set[str] = field(default_factory=set)
    eligibility_checks: dict[str, Any] = field(default_factory=dict)
    escalated: bool = False

    # Working memory for the scripted fallback planner (see mock_llm.py).
    scratch: dict = field(default_factory=dict)

    # Observability.
    trace: list[TraceEntry] = field(default_factory=list)
    turn_count: int = 0

    # -- observability -----------------------------------------------------
    def log(self, kind: str, label: str, detail: Any = None) -> TraceEntry:
        entry = TraceEntry(kind=kind, label=label, detail=detail)
        self.trace.append(entry)
        return entry

    def say(self, role: str, text: str) -> None:
        """Record something the customer actually saw."""
        self.transcript.append({"role": role, "text": text})

    # -- persistence -------------------------------------------------------
    def to_payload(self) -> dict:
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "transcript": self.transcript,
            "verified_orders": sorted(self.verified_orders),
            "eligibility_checks": {
                k: asdict(v) for k, v in self.eligibility_checks.items()
            },
            "escalated": self.escalated,
            "scratch": self.scratch,
            "trace": [asdict(t) for t in self.trace],
            "turn_count": self.turn_count,
        }

    @classmethod
    def from_payload(cls, p: dict) -> "Session":
        return cls(
            session_id=p["session_id"],
            messages=p.get("messages", []),
            transcript=p.get("transcript", []),
            verified_orders=set(p.get("verified_orders", [])),
            eligibility_checks={
                k: EligibilityResult(**v)
                for k, v in p.get("eligibility_checks", {}).items()
            },
            escalated=p.get("escalated", False),
            scratch=p.get("scratch", {}),
            trace=[TraceEntry(**t) for t in p.get("trace", [])],
            turn_count=p.get("turn_count", 0),
        )

    def persist(self) -> None:
        store.save(
            self.session_id,
            self.to_payload(),
            turn_count=self.turn_count,
            escalated=self.escalated,
        )


store.init()


def get_session(session_id: str | None) -> Session:
    """Load a conversation from storage, or start a new one.

    An unknown id yields a fresh session rather than an error -- a customer whose
    cookie outlived the database should get a working chat, not a stack trace.
    """
    if session_id:
        payload = store.load(session_id)
        if payload is not None:
            return Session.from_payload(payload)
    return Session()
