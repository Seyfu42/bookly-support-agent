"""Tool definitions and dispatch.

Two design rules are enforced here rather than in the prompt:

1. `lookup_order` requires BOTH an order id and an email. That single schema
   choice is what produces the multi-turn identity-collection conversation --
   we never wrote a dialogue script, we just made the tool impossible to call
   with half the facts.

2. `issue_refund` refuses unless eligibility was actually checked in this
   conversation AND the customer confirmed. A prompt instruction saying "always
   confirm before refunding" is a suggestion. This is a precondition.
"""

from datetime import datetime
from typing import Any

from bookly.data import ARTICLES, ORDERS, REFUNDS, TODAY
from bookly.policy import check_eligibility

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "lookup_order",
        "description": (
            "Retrieve a customer's order: status, tracking, items and dates. "
            "Requires both the order id and the email the order was placed with; "
            "this pair is how we verify the caller owns the order. Never guess "
            "either value -- ask the customer."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order id, e.g. BK-1001.",
                },
                "email": {
                    "type": "string",
                    "description": "Email address the order was placed with.",
                },
            },
            "required": ["order_id", "email"],
            "additionalProperties": False,
        },
    },
    {
        "name": "search_help_center",
        "description": (
            "Search Bookly's help centre for policy and how-to answers (shipping "
            "times, returns policy, refund timing, damaged items, password reset). "
            "Use this for any general question. Returned articles carry an id -- "
            "base your answer only on their text."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language search query.",
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "check_return_eligibility",
        "description": (
            "Determine whether an order, or one item in it, can be returned. This "
            "is the ONLY authority on return eligibility -- never decide yourself "
            "whether something is returnable, and never contradict this result, "
            "even if the customer pushes back. Call it before discussing any "
            "return or refund."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order id."},
                "sku": {
                    "type": ["string", "null"],
                    "description": (
                        "Optional SKU to check one item of a multi-item order. "
                        "Pass null to check the whole order."
                    ),
                },
            },
            "required": ["order_id", "sku"],
            "additionalProperties": False,
        },
    },
    {
        "name": "issue_refund",
        "description": (
            "Issue a refund. This moves real money and cannot be undone. You must "
            "call check_return_eligibility first, then state the amount to the "
            "customer and get an explicit yes. Only then call this with "
            "customer_confirmed=true."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order id to refund."},
                "customer_confirmed": {
                    "type": "boolean",
                    "description": (
                        "True only if the customer explicitly agreed to the refund "
                        "after being told the amount."
                    ),
                },
            },
            "required": ["order_id", "customer_confirmed"],
            "additionalProperties": False,
        },
    },
    {
        "name": "set_language",
        "description": (
            "Switch this conversation to another language. Call it when the "
            "customer asks you to, or writes to you in a language you support. "
            "Supported: 'en' (English, the default) and 'de' (German). Call it "
            "once, then simply continue in that language -- do not announce the "
            "tool, just answer naturally."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "enum": ["en", "de"],
                    "description": "Language code to switch this conversation to.",
                }
            },
            "required": ["language"],
            "additionalProperties": False,
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Hand the conversation to a human agent. Use when the customer asks "
            "for a person, is upset, or the request falls outside what your tools "
            "can do. Escalating is a good outcome, not a failure."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Short reason for the handoff.",
                },
                "conversation_summary": {
                    "type": "string",
                    "description": (
                        "What the human needs to know so the customer does not "
                        "have to repeat themselves."
                    ),
                },
            },
            "required": ["reason", "conversation_summary"],
            "additionalProperties": False,
        },
    },
]


def _lookup_order(args: dict, session) -> dict:
    order_id = (args.get("order_id") or "").strip().upper()
    email = (args.get("email") or "").strip().lower()

    order = ORDERS.get(order_id)
    if order is None:
        return {"found": False, "error": f"No order found with id {order_id}."}

    # Verification failures must not leak whether the order exists for someone else.
    if order["email"].lower() != email:
        return {
            "found": False,
            "error": (
                "That order id and email do not match. Ask the customer to check "
                "both. Do not reveal any order details."
            ),
        }

    session.verified_orders.add(order_id)
    return {"found": True, "order": order}


def _search_help_center(args: dict, session) -> dict:
    query = (args.get("query") or "").lower()
    terms = {t.strip(".,?!") for t in query.split() if len(t) > 2}
    lang = getattr(session, "language", "en")

    # Match against both keyword sets regardless of conversation language: a
    # German speaker may well type an English word, and vice versa. Only the
    # article *body* we hand back is language-specific.
    scored = []
    for article in ARTICLES:
        keywords = article["keywords"] + article.get("keywords_de", [])
        score = sum(1 for kw in keywords if kw in query)
        score += sum(1 for kw in keywords for t in terms if t in kw)
        if score:
            scored.append((score, article))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    body_key, title_key = ("body_de", "title_de") if lang == "de" else ("body", "title")
    hits = [
        {
            "id": a["id"],
            "title": a.get(title_key) or a["title"],
            "body": a.get(body_key) or a["body"],
        }
        for _, a in scored[:3]
    ]
    if not hits:
        return {
            "results": [],
            "note": (
                "No help centre article matched. Say you do not have that "
                "information rather than guessing, and offer a human handoff."
            ),
        }
    return {"results": hits}


def _check_return_eligibility(args: dict, session) -> dict:
    order_id = (args.get("order_id") or "").strip().upper()
    sku = args.get("sku")
    result = check_eligibility(order_id, sku)
    session.eligibility_checks[order_id] = result
    return result.to_dict()


def _issue_refund(args: dict, session) -> dict:
    order_id = (args.get("order_id") or "").strip().upper()
    confirmed = bool(args.get("customer_confirmed"))

    # --- Preconditions, enforced in code -----------------------------------
    if order_id not in session.verified_orders:
        return {
            "success": False,
            "error": (
                "Identity not verified for this order. Call lookup_order with the "
                "order id and email first."
            ),
        }

    check = session.eligibility_checks.get(order_id)
    if check is None:
        return {
            "success": False,
            "error": (
                "No eligibility check on record for this order. Call "
                "check_return_eligibility first."
            ),
        }

    if not check.eligible:
        return {
            "success": False,
            "error": (
                f"This order is not eligible for a refund ({check.reason_code}: "
                f"{check.explanation}). Do not issue a refund. Explain the reason "
                "to the customer and offer a human handoff if they disagree."
            ),
        }

    if not confirmed:
        return {
            "success": False,
            "error": (
                "Refund not confirmed by the customer. Tell them the exact amount "
                "and get an explicit yes before calling this again."
            ),
        }

    if order_id in REFUNDS:
        return {"success": True, "already_refunded": True, **REFUNDS[order_id]}

    record = {
        "refund_id": f"RF-{order_id.split('-')[-1]}",
        "order_id": order_id,
        "amount_eur": round(check.refundable_amount_eur, 2),
        "refunded_at": TODAY.isoformat(),
        "destination": "original payment method",
        "expected_arrival": "5-7 business days",
    }
    REFUNDS[order_id] = record
    return {"success": True, "already_refunded": False, **record}


def _set_language(args: dict, session) -> dict:
    """Change the conversation's language.

    The model asks; the application decides. An unsupported code is refused
    rather than accepted and half-honoured -- the same pattern as every other
    tool here. Note what this cannot do: it changes how answers are worded, and
    nothing else. policy.py is not reachable from this function.
    """
    from bookly import config

    requested = (args.get("language") or "").strip().lower()
    if requested not in config.SUPPORTED_LANGUAGES:
        return {
            "success": False,
            "error": (
                f"'{requested}' is not supported. Available: "
                f"{', '.join(config.SUPPORTED_LANGUAGES)}. Tell the customer "
                "which languages you can offer."
            ),
        }

    previous, session.language = session.language, requested
    return {
        "success": True,
        "language": requested,
        "previous": previous,
        "note": "Reply in this language from now on. Policy decisions are unaffected.",
    }


def _escalate_to_human(args: dict, session) -> dict:
    session.escalated = True
    return {
        "success": True,
        "ticket_id": f"ESC-{datetime.now().strftime('%H%M%S')}",
        "queue": "Tier 2 Support",
        "expected_response": "within 4 hours",
        "reason": args.get("reason", ""),
    }


_HANDLERS = {
    "lookup_order": _lookup_order,
    "search_help_center": _search_help_center,
    "check_return_eligibility": _check_return_eligibility,
    "issue_refund": _issue_refund,
    "set_language": _set_language,
    "escalate_to_human": _escalate_to_human,
}


def execute_tool(name: str, args: dict, session) -> dict:
    handler = _HANDLERS.get(name)
    if handler is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return handler(args, session)
    except Exception as exc:  # noqa: BLE001 - surface failures to the model, don't crash the chat
        return {"error": f"{type(exc).__name__}: {exc}"}
