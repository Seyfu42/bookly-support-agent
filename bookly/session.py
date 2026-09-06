"""Conversation state.

Two kinds of memory live here, and keeping them apart is deliberate:

  * `messages` is the model's memory -- the transcript it sees each turn.
  * everything else is the *application's* memory -- facts the application knows
    and the model cannot talk its way around. Whether identity was verified and
    whether an eligibility check passed are security-relevant, so they are held
    here as plain Python and consulted by the tool layer, not recalled from the
    transcript by the model.

In production this is a Redis hash or a Postgres row keyed by conversation id.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceEntry:
    """One observable step, surfaced in the UI so the agent is not a black box."""

    kind: str  # "tool_call" | "tool_result" | "assistant" | "note"
    label: str
    detail: Any = None


@dataclass
class Session:
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    # Model-visible transcript.
    messages: list[dict] = field(default_factory=list)

    # Application-owned facts. Never inferred from the transcript.
    verified_orders: set[str] = field(default_factory=set)
    eligibility_checks: dict[str, Any] = field(default_factory=dict)
    escalated: bool = False

    # Working memory for the scripted fallback planner (see mock_llm.py).
    scratch: dict = field(default_factory=dict)

    # Observability.
    trace: list[TraceEntry] = field(default_factory=list)
    turn_count: int = 0

    def log(self, kind: str, label: str, detail: Any = None) -> TraceEntry:
        entry = TraceEntry(kind=kind, label=label, detail=detail)
        self.trace.append(entry)
        return entry


SESSIONS: dict[str, Session] = {}


def get_session(session_id: str | None) -> Session:
    if session_id and session_id in SESSIONS:
        return SESSIONS[session_id]
    session = Session()
    SESSIONS[session.session_id] = session
    return session
