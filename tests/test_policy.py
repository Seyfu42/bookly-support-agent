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


def test_policy_is_language_neutral():
    """The rule must not know or care what language the conversation is in.

    This is the whole point of the German feature: `reason_code` is a
    machine-readable enum, so switching language changes the wording of the
    reply and nothing about the decision. If someone later adds a language
    branch to policy.py, this test should fail.

    Checked against the module's *identifiers* via the AST rather than its raw
    text -- a prose mention of the word "language" in a docstring is fine, a
    variable called `language` is not.
    """
    import ast
    import inspect

    from bookly import policy

    tree = ast.parse(inspect.getsource(policy))
    identifiers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            identifiers.add(node.id)
        elif isinstance(node, ast.Attribute):
            identifiers.add(node.attr)
        elif isinstance(node, ast.arg):
            identifiers.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            identifiers.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            identifiers.update(a.name for a in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                identifiers.add(node.module)

    for ident in identifiers:
        low = ident.lower()
        for banned in ("lang", "locale", "german", "i18n", "translat"):
            assert banned not in low, f"policy.py references '{ident}' - it must stay language-free"

    # And the signature takes no language argument.
    params = set(inspect.signature(policy.check_eligibility).parameters)
    assert params == {"order_id", "sku"}, params


def test_same_verdict_in_both_languages():
    """Switching language changes the wording, never the decision."""
    from bookly.session import Session
    from bookly.tools import execute_tool

    verdicts = []
    for lang in ("en", "de"):
        s = Session()
        s.language = lang
        result = execute_tool(
            "check_return_eligibility", {"order_id": "BK-1002", "sku": None}, s
        )
        verdicts.append(
            (result["eligible"], result["reason_code"], result["days_remaining"])
        )
    assert verdicts[0] == verdicts[1] == (False, "OUTSIDE_RETURN_WINDOW", -15)
