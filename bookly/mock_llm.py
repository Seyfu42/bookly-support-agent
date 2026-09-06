"""Scripted fallback planner -- the agent without the model.

This exists so `git clone && uv run` produces a working demo with no API key,
and so a live demo can never be derailed by a network blip. It is a rule-based
planner, not an LLM: rigid, literal, and incapable of handling a sentence it was
not written for.

That contrast is the point. It reuses the *same* tools, the *same* policy engine
and the *same* refund preconditions as the real agent. Everything that protects
the customer or the business is shared; only the language understanding differs.
Swapping the brain out does not change what the system is allowed to do -- which
is the strongest available evidence that the safety properties live in the
architecture rather than in the prompt.
"""

import re
from collections.abc import Iterator

from bookly.session import Session
from bookly.tools import execute_tool

ORDER_RE = re.compile(r"\b(BK[-\s]?\d{4})\b", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")

RETURN_WORDS = ("return", "refund", "send back", "money back", "cancel")
STATUS_WORDS = ("where", "status", "track", "arrive", "shipped", "delivery", "when")
HUMAN_WORDS = ("human", "person", "agent", "manager", "representative", "speak to someone")
YES_WORDS = ("yes", "yep", "yeah", "sure", "please do", "go ahead", "confirm", "ok", "okay", "do it")


def _say(session: Session, text: str) -> dict:
    session.messages.append({"role": "assistant", "content": text})
    session.log("assistant", text)
    return {"type": "reply", "text": text}


def _call(session: Session, name: str, args: dict) -> Iterator[dict]:
    """Run a tool, emitting the same events the real loop emits."""
    yield {"type": "tool_call", "name": name, "args": args}
    session.log("tool_call", name, args)
    result = execute_tool(name, args, session)
    yield {"type": "tool_result", "name": name, "result": result}
    session.log("tool_result", name, result)
    session.scratch["last_result"] = result


def run_turn_mock(session: Session, user_text: str) -> Iterator[dict]:
    text = user_text.lower()
    sc = session.scratch

    # Accumulate identifiers across turns -- this is the multi-turn collection.
    if m := ORDER_RE.search(user_text):
        sc["order_id"] = m.group(1).upper().replace(" ", "-")
    if m := EMAIL_RE.search(user_text):
        sc["email"] = m.group(0).lower()

    if any(w in text for w in HUMAN_WORDS):
        yield from _call(session, "escalate_to_human", {
            "reason": "Customer asked for a human.",
            "conversation_summary": f"Customer said: {user_text}",
        })
        yield _say(session, "Of course — I've passed you to a colleague. They'll pick this up within about four hours and they can see everything we've discussed, so you won't need to repeat yourself.")
        return

    # Awaiting a yes/no on a quoted refund.
    if sc.get("pending_refund"):
        order_id = sc["pending_refund"]
        if any(w in text for w in YES_WORDS):
            sc.pop("pending_refund")
            yield from _call(session, "issue_refund", {"order_id": order_id, "customer_confirmed": True})
            res = sc["last_result"]
            if res.get("success"):
                yield _say(session, f"Done — €{res['amount_eur']:.2f} is on its way back to your original payment method, and it should land within 5–7 business days. Your refund reference is {res['refund_id']}.")
            else:
                yield _say(session, f"I couldn't complete that: {res.get('error')}")
            return
        sc.pop("pending_refund")
        yield _say(session, "No problem — I've left the order as it is. Anything else I can help with?")
        return

    # Intent persists across turns. Without this the planner forgets why it
    # asked for an order number the moment the customer supplies one -- the
    # scripted planner has no idea what a conversation is, so we track it.
    if any(w in text for w in RETURN_WORDS):
        sc["intent"] = "return"
    elif any(w in text for w in STATUS_WORDS):
        sc.setdefault("intent", "status")

    wants_return = sc.get("intent") == "return"
    wants_status = sc.get("intent") == "status"

    if wants_return or wants_status:
        # Clarifying question: refuse to act on half the facts.
        if not sc.get("order_id"):
            yield _say(session, "Happy to help with that. What's the order number? It starts with BK- and it's in your confirmation email.")
            return
        if not sc.get("email"):
            yield _say(session, f"Thanks. And which email address was {sc['order_id']} placed with? I just need it to confirm the order is yours.")
            return

        yield from _call(session, "lookup_order", {"order_id": sc["order_id"], "email": sc["email"]})
        res = sc["last_result"]
        if not res.get("found"):
            sc.pop("order_id", None)
            yield _say(session, "Hmm, that order number and email don't match up. Could you double-check both for me?")
            return

        order = res["order"]

        if wants_status and not wants_return:
            sc.pop("intent", None)
            if order["status"] == "in_transit":
                yield _say(session, f"Your order is on its way — {order['carrier']} has it, tracking {order['tracking_number']}, and it's estimated to arrive on {order['estimated_delivery']}.")
            else:
                yield _say(session, f"That one was delivered on {order['delivered_at']} via {order['carrier']} (tracking {order['tracking_number']}). Let me know if it didn't reach you.")
            return

        # Clarifying question: a multi-item order is genuinely ambiguous.
        if len(order["items"]) > 1 and not sc.get("sku"):
            titles = " or ".join(f"“{i['title']}”" for i in order["items"])
            sc["awaiting_item"] = order["order_id"]
            yield _say(session, f"That order has two books in it — {titles}. Which one would you like to return?")
            return

        yield from _call(session, "check_return_eligibility", {"order_id": order["order_id"], "sku": sc.get("sku")})
        check = sc["last_result"]
        sc.pop("intent", None)
        if check["eligible"]:
            sc["pending_refund"] = order["order_id"]
            yield _say(session, f"Good news — that's still within the 30-day window, with {check['days_remaining']} days to spare. I can refund €{check['refundable_amount_eur']:.2f} to your original payment method. Shall I go ahead?")
        else:
            yield _say(session, f"I'm sorry — I can't process a return on that one. {check['explanation']} I know that's not what you were hoping for; I can put you through to a colleague if you'd like to talk it through.")
        return

    # Item disambiguation follow-up.
    if sc.get("awaiting_item"):
        from bookly.data import ORDERS
        order = ORDERS[sc["awaiting_item"]]
        for item in order["items"]:
            if item["title"].lower().split()[0] in text:
                sc["sku"] = item["sku"]
                sc.pop("awaiting_item")
                yield from _call(session, "check_return_eligibility", {"order_id": order["order_id"], "sku": item["sku"]})
                check = sc["last_result"]
                if check["eligible"]:
                    sc["pending_refund"] = order["order_id"]
                    yield _say(session, f"Got it — “{item['title']}”. That's within the window, so I can refund €{check['refundable_amount_eur']:.2f}. Shall I go ahead?")
                else:
                    yield _say(session, f"I'm sorry — {check['explanation']}")
                return

    # Everything else is a knowledge question.
    yield from _call(session, "search_help_center", {"query": user_text})
    res = sc["last_result"]
    if res.get("results"):
        top = res["results"][0]
        yield _say(session, f"{top['body']}\n\n(From our help centre: {top['title']}, {top['id']})")
    else:
        yield _say(session, "I don't have anything on that in the help centre, and I'd rather not guess. Would you like me to put you through to a colleague?")
