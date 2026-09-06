"""Mock backend systems.

In a real deployment each of these is a network call to a different system of record:
orders live in an OMS, articles in a help-center CMS, refunds in a payments service.
They are mocked here so the demo runs offline, but the *shape* is the point: the agent
reaches them only through the tool layer, never through its own prompt.
"""

from datetime import date, timedelta

TODAY = date(2026, 9, 6)


def _days_ago(n: int) -> str:
    return (TODAY - timedelta(days=n)).isoformat()


def _days_ahead(n: int) -> str:
    return (TODAY + timedelta(days=n)).isoformat()


# --- Orders -----------------------------------------------------------------
# Deliberately shaped so every branch of the return policy is reachable in a demo.

ORDERS = {
    "BK-1001": {
        "order_id": "BK-1001",
        "email": "ada.lovelace@example.com",
        "status": "delivered",
        "placed_at": _days_ago(12),
        "delivered_at": _days_ago(5),
        "carrier": "DHL",
        "tracking_number": "DHL-884120355",
        "items": [
            {
                "sku": "HC-8841",
                "title": "The Midnight Library",
                "format": "hardcover",
                "quantity": 1,
                "price_eur": 18.99,
            }
        ],
        "total_eur": 18.99,
    },
    "BK-1002": {
        "order_id": "BK-1002",
        "email": "ada.lovelace@example.com",
        "status": "delivered",
        "placed_at": _days_ago(52),
        "delivered_at": _days_ago(45),
        "carrier": "DHL",
        "tracking_number": "DHL-771204918",
        "items": [
            {
                "sku": "PB-2019",
                "title": "Piranesi",
                "format": "paperback",
                "quantity": 1,
                "price_eur": 24.50,
            }
        ],
        "total_eur": 24.50,
    },
    "BK-1003": {
        "order_id": "BK-1003",
        "email": "ada.lovelace@example.com",
        "status": "in_transit",
        "placed_at": _days_ago(2),
        "delivered_at": None,
        "estimated_delivery": _days_ahead(3),
        "carrier": "Hermes",
        "tracking_number": "HRM-556201773",
        "items": [
            {
                "sku": "HC-3310",
                "title": "Babel",
                "format": "hardcover",
                "quantity": 1,
                "price_eur": 32.00,
            }
        ],
        "total_eur": 32.00,
    },
    "BK-1004": {
        "order_id": "BK-1004",
        "email": "ada.lovelace@example.com",
        "status": "delivered",
        "placed_at": _days_ago(12),
        "delivered_at": _days_ago(12),
        "carrier": "digital",
        "tracking_number": None,
        "items": [
            {
                "sku": "EB-5567",
                "title": "Project Hail Mary",
                "format": "ebook",
                "quantity": 1,
                "price_eur": 12.99,
            }
        ],
        "total_eur": 12.99,
    },
    "BK-1005": {
        "order_id": "BK-1005",
        "email": "ada.lovelace@example.com",
        "status": "delivered",
        "placed_at": _days_ago(9),
        "delivered_at": _days_ago(3),
        "carrier": "DHL",
        "tracking_number": "DHL-990133284",
        "items": [
            {
                "sku": "PB-7788",
                "title": "Klara and the Sun",
                "format": "paperback",
                "quantity": 1,
                "price_eur": 14.00,
            },
            {
                "sku": "HC-1122",
                "title": "Sea of Tranquility",
                "format": "hardcover",
                "quantity": 1,
                "price_eur": 26.00,
            },
        ],
        "total_eur": 40.00,
    },
    "BK-2001": {
        "order_id": "BK-2001",
        "email": "grace.hopper@example.com",
        "status": "delivered",
        "placed_at": _days_ago(20),
        "delivered_at": _days_ago(14),
        "carrier": "DHL",
        "tracking_number": "DHL-120099831",
        "items": [
            {
                "sku": "HC-4455",
                "title": "The Overstory",
                "format": "hardcover",
                "quantity": 1,
                "price_eur": 21.00,
            }
        ],
        "total_eur": 21.00,
    },
}

# Refunds already issued, keyed by order id. Mutated by the issue_refund tool so
# the demo can show idempotency.
REFUNDS: dict[str, dict] = {}


# --- Help centre ------------------------------------------------------------
# Stands in for a retrieval index. Each article carries a stable id so the agent
# can cite exactly which source a claim came from.

ARTICLES = [
    {
        "id": "HC-RETURNS-01",
        "title": "Return policy",
        "keywords": ["return", "returns", "send back", "refund", "policy", "window"],
        "body": (
            "Physical books may be returned within 30 days of delivery, provided they "
            "are in resalable condition. Refunds are issued to the original payment "
            "method. Return shipping is free within the EU. Ebooks and audiobooks are "
            "non-returnable once the download link has been issued."
        ),
    },
    {
        "id": "HC-REFUNDS-02",
        "title": "When will I get my money back?",
        "keywords": ["refund", "money back", "how long", "processed", "payment"],
        "body": (
            "Once a return is approved, the refund is sent to your original payment "
            "method within 5-7 business days. Your bank may take an additional 2-3 "
            "days to display it."
        ),
    },
    {
        "id": "HC-SHIPPING-03",
        "title": "Shipping times and costs",
        "keywords": ["shipping", "delivery", "how long", "arrive", "cost", "postage"],
        "body": (
            "Standard shipping within Germany takes 2-4 business days and is free on "
            "orders over EUR 20. Elsewhere in the EU takes 4-7 business days. Express "
            "shipping is next business day if ordered before 14:00 CET."
        ),
    },
    {
        "id": "HC-DAMAGED-04",
        "title": "Damaged or wrong item",
        "keywords": ["damaged", "broken", "wrong", "torn", "missing", "defective"],
        "body": (
            "Report damaged or incorrect items within 14 days of delivery. We ship a "
            "replacement at no cost and you keep the damaged copy. This is handled "
            "separately from the standard return flow and is not subject to the "
            "30-day return window."
        ),
    },
    {
        "id": "HC-PASSWORD-05",
        "title": "Resetting your password",
        "keywords": ["password", "reset", "login", "sign in", "locked out", "account"],
        "body": (
            "Use the 'Forgot password' link on the sign-in page. The reset email "
            "arrives within a few minutes and the link is valid for 60 minutes. "
            "Support staff cannot reset a password on your behalf."
        ),
    },
]
