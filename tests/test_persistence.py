"""Tests for durable sessions.

The interesting assertions here are not "did the text come back" -- they are
about the *security-relevant* half of the state. A restored session must not
silently regain trust it had not earned, and must not lose trust it had.
"""

import pytest

from bookly import store
from bookly.policy import check_eligibility
from bookly.session import Session, get_session


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "test.db")
    store.init()
    yield


def _populated() -> Session:
    s = Session()
    s.messages = [{"role": "user", "content": "hi"}]
    s.say("user", "hi")
    s.verified_orders.add("BK-1001")
    s.eligibility_checks["BK-1001"] = check_eligibility("BK-1001")
    s.log("tool_call", "lookup_order", {"order_id": "BK-1001"})
    s.turn_count = 3
    return s


def test_session_survives_a_restart():
    s = _populated()
    s.persist()

    restored = get_session(s.session_id)
    assert restored.session_id == s.session_id
    assert restored.messages == s.messages
    assert restored.transcript == s.transcript
    assert restored.turn_count == 3


def test_verified_orders_survive_as_a_set():
    s = _populated()
    s.persist()
    restored = get_session(s.session_id)
    # Not a list, not a string -- the refund gate does a set membership test.
    assert restored.verified_orders == {"BK-1001"}


def test_eligibility_rehydrates_as_an_object_not_a_dict():
    """The refund gate reads `.eligible` and `.reason_code` as attributes.

    If this came back as a plain dict the gate would raise AttributeError, and a
    broken gate is a gate that fails open. Worth a test of its own.
    """
    s = _populated()
    s.persist()
    check = get_session(s.session_id).eligibility_checks["BK-1001"]
    assert check.eligible is True
    assert check.reason_code == "ELIGIBLE"
    assert check.refundable_amount_eur == pytest.approx(18.99)


def test_unknown_session_id_yields_a_fresh_session_not_an_error():
    s = get_session("does-not-exist")
    assert s.messages == []
    assert s.verified_orders == set()
    assert s.session_id != "does-not-exist"


def test_a_restored_session_does_not_invent_verification():
    """A conversation that never verified an order must not come back trusted."""
    s = Session()
    s.messages = [{"role": "user", "content": "refund please"}]
    s.turn_count = 1
    s.persist()
    assert get_session(s.session_id).verified_orders == set()


def test_escalation_flag_round_trips():
    s = _populated()
    s.escalated = True
    s.persist()
    assert get_session(s.session_id).escalated is True


def test_stats_counts_sessions_and_turns():
    for _ in range(3):
        _populated().persist()
    st = store.stats()
    assert st["sessions"] == 3
    assert st["turns"] == 9
