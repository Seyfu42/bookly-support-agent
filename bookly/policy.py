"""Deterministic return/refund policy.

This module is the thesis of the whole project in one file.

Refund eligibility is a *business rule*, not a language problem. It is computed
here in ordinary Python, and the model is never asked to judge it. The model's
job is to gather the inputs, call this code, and explain the verdict kindly.

Why it matters: an LLM asked "can I return a book I got 45 days ago?" is under
enormous pressure to be agreeable. It will find a reason to say yes. Moving the
decision out of the model removes the opportunity entirely -- there is no prompt
to jailbreak and no temperature at which 45 becomes less than 30. It also makes
the rule auditable and unit-testable, which is what a compliance team will
actually ask you for.
"""

from dataclasses import dataclass, field
from datetime import date

from bookly.data import ORDERS, REFUNDS, TODAY

RETURN_WINDOW_DAYS = 30
NON_RETURNABLE_FORMATS = {"ebook", "audiobook"}


@dataclass
class EligibilityResult:
    eligible: bool
    reason_code: str
    explanation: str
    refundable_amount_eur: float = 0.0
    days_since_delivery: int | None = None
    days_remaining: int | None = None
    policy_source: str = "HC-RETURNS-01"
    eligible_skus: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "eligible": self.eligible,
            "reason_code": self.reason_code,
            "explanation": self.explanation,
            "refundable_amount_eur": round(self.refundable_amount_eur, 2),
            "days_since_delivery": self.days_since_delivery,
            "days_remaining": self.days_remaining,
            "policy_source": self.policy_source,
            "eligible_skus": self.eligible_skus,
        }


def check_eligibility(order_id: str, sku: str | None = None) -> EligibilityResult:
    """Decide whether an order (or one item in it) can be returned.

    Rules are evaluated in a fixed order so the reason a customer is told is
    always the *first* thing that disqualifies them, not an arbitrary one.
    """
    order = ORDERS.get(order_id)
    if order is None:
        return EligibilityResult(
            eligible=False,
            reason_code="ORDER_NOT_FOUND",
            explanation=f"No order exists with id {order_id}.",
        )

    if order_id in REFUNDS:
        return EligibilityResult(
            eligible=False,
            reason_code="ALREADY_REFUNDED",
            explanation=(
                f"Order {order_id} was already refunded on "
                f"{REFUNDS[order_id]['refunded_at']}."
            ),
        )

    if order["status"] != "delivered":
        return EligibilityResult(
            eligible=False,
            reason_code="NOT_YET_DELIVERED",
            explanation=(
                f"Order {order_id} has status '{order['status']}' and has not been "
                "delivered yet. The return window opens on delivery."
            ),
        )

    items = order["items"]
    if sku is not None:
        items = [i for i in items if i["sku"] == sku]
        if not items:
            return EligibilityResult(
                eligible=False,
                reason_code="SKU_NOT_IN_ORDER",
                explanation=f"Item {sku} is not part of order {order_id}.",
            )

    delivered = date.fromisoformat(order["delivered_at"])
    days_since = (TODAY - delivered).days
    days_remaining = RETURN_WINDOW_DAYS - days_since

    if days_since > RETURN_WINDOW_DAYS:
        return EligibilityResult(
            eligible=False,
            reason_code="OUTSIDE_RETURN_WINDOW",
            explanation=(
                f"Order {order_id} was delivered {days_since} days ago, which is "
                f"outside the {RETURN_WINDOW_DAYS}-day return window."
            ),
            days_since_delivery=days_since,
            days_remaining=days_remaining,
        )

    returnable = [i for i in items if i["format"] not in NON_RETURNABLE_FORMATS]
    if not returnable:
        formats = ", ".join(sorted({i["format"] for i in items}))
        return EligibilityResult(
            eligible=False,
            reason_code="NON_RETURNABLE_FORMAT",
            explanation=(
                f"This order contains only digital items ({formats}), which are "
                "non-returnable once the download link has been issued."
            ),
            days_since_delivery=days_since,
            days_remaining=days_remaining,
        )

    amount = sum(i["price_eur"] * i["quantity"] for i in returnable)
    return EligibilityResult(
        eligible=True,
        reason_code="ELIGIBLE",
        explanation=(
            f"Delivered {days_since} days ago, {days_remaining} days remain in the "
            f"{RETURN_WINDOW_DAYS}-day window."
        ),
        refundable_amount_eur=amount,
        days_since_delivery=days_since,
        days_remaining=days_remaining,
        eligible_skus=[i["sku"] for i in returnable],
    )
