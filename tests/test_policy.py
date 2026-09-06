"""Tests for the policy engine.

These matter more than they look. The whole architectural claim is that refund
eligibility is deterministic and therefore testable -- if that claim is true,
these tests exist and pass; if eligibility lived in the prompt, this file could
not be written at all.
"""

import pytest

from bookly.data import REFUNDS
from bookly.policy import RETURN_WINDOW_DAYS, check_eligibility
from bookly.session import Session
from bookly.tools import execute_tool


@pytest.fixture(autouse=True)
def clean_refunds():
    REFUNDS.clear()
    yield
    REFUNDS.clear()


def test_recent_physical_order_is_returnable():
    r = check_eligibility("BK-1001")
    assert r.eligible
    assert r.refundable_amount_eur == pytest.approx(18.99)
    assert r.days_remaining == RETURN_WINDOW_DAYS - 5


def test_order_past_the_window_is_refused():
    r = check_eligibility("BK-1002")
    assert not r.eligible
    assert r.reason_code == "OUTSIDE_RETURN_WINDOW"


def test_undelivered_order_is_refused():
    r = check_eligibility("BK-1003")
    assert not r.eligible
    assert r.reason_code == "NOT_YET_DELIVERED"


def test_ebook_is_non_returnable():
    r = check_eligibility("BK-1004")
    assert not r.eligible
    assert r.reason_code == "NON_RETURNABLE_FORMAT"


def test_unknown_order():
    assert check_eligibility("BK-9999").reason_code == "ORDER_NOT_FOUND"


def test_single_item_of_multi_item_order():
    r = check_eligibility("BK-1005", sku="PB-7788")
    assert r.eligible
    assert r.refundable_amount_eur == pytest.approx(14.00)


def test_second_refund_is_refused():
    session = Session()
    session.verified_orders.add("BK-1001")
    session.eligibility_checks["BK-1001"] = check_eligibility("BK-1001")
    first = execute_tool("issue_refund", {"order_id": "BK-1001", "customer_confirmed": True}, session)
    assert first["success"] and not first["already_refunded"]
    assert check_eligibility("BK-1001").reason_code == "ALREADY_REFUNDED"
