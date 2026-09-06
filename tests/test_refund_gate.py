"""Tests for the refund preconditions.

Each of these is a scenario where a sufficiently persuasive customer -- or a
prompt-injected one -- talks the model into calling issue_refund when it should
not have. In every case the tool layer refuses regardless of what the model
decided, which is the property we actually want.
"""

import pytest

from bookly.data import REFUNDS
from bookly.policy import check_eligibility
from bookly.session import Session
from bookly.tools import execute_tool


@pytest.fixture(autouse=True)
def clean_refunds():
    REFUNDS.clear()
    yield
    REFUNDS.clear()


def _verified_session(order_id: str) -> Session:
    s = Session()
    s.verified_orders.add(order_id)
    return s


def test_refund_without_identity_verification_is_refused():
    result = execute_tool(
        "issue_refund", {"order_id": "BK-1001", "customer_confirmed": True}, Session()
    )
    assert result["success"] is False
    assert "Identity not verified" in result["error"]


def test_refund_without_eligibility_check_is_refused():
    result = execute_tool(
        "issue_refund",
        {"order_id": "BK-1001", "customer_confirmed": True},
        _verified_session("BK-1001"),
    )
    assert result["success"] is False
    assert "No eligibility check" in result["error"]


def test_refund_of_ineligible_order_is_refused_even_when_confirmed():
    session = _verified_session("BK-1002")
    session.eligibility_checks["BK-1002"] = check_eligibility("BK-1002")
    result = execute_tool(
        "issue_refund", {"order_id": "BK-1002", "customer_confirmed": True}, session
    )
    assert result["success"] is False
    assert "OUTSIDE_RETURN_WINDOW" in result["error"]
    assert "BK-1002" not in REFUNDS


def test_refund_without_customer_confirmation_is_refused():
    session = _verified_session("BK-1001")
    session.eligibility_checks["BK-1001"] = check_eligibility("BK-1001")
    result = execute_tool(
        "issue_refund", {"order_id": "BK-1001", "customer_confirmed": False}, session
    )
    assert result["success"] is False
    assert "not confirmed" in result["error"]


def test_wrong_email_does_not_verify_or_leak_order_details():
    session = Session()
    result = execute_tool(
        "lookup_order", {"order_id": "BK-1001", "email": "attacker@example.com"}, session
    )
    assert result["found"] is False
    assert "order" not in result
    assert session.verified_orders == set()


def test_happy_path_succeeds():
    session = _verified_session("BK-1001")
    session.eligibility_checks["BK-1001"] = check_eligibility("BK-1001")
    result = execute_tool(
        "issue_refund", {"order_id": "BK-1001", "customer_confirmed": True}, session
    )
    assert result["success"] is True
    assert result["amount_eur"] == pytest.approx(18.99)
