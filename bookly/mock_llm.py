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

It is bilingual for the same reason. Note how German is handled: the planner
renders `reason_code` -- a machine-readable enum from policy.py -- into German
itself. policy.py has no idea any of this exists. The rule emits a code; the
presentation layer decides what that code sounds like in a given language.
"""

import re
from collections.abc import Iterator

from bookly.session import Session
from bookly.tools import execute_tool

ORDER_RE = re.compile(r"\b(BK[-\s]?\d{4})\b", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")

RETURN_WORDS = ("return", "refund", "send back", "money back", "cancel",
                "rückgabe", "ruckgabe", "rueckgabe", "zurückgeben", "zuruckgeben",
                "erstattung", "retoure", "zurückschicken", "geld zurück", "stornieren")
STATUS_WORDS = ("where", "status", "track", "arrive", "shipped", "delivery", "when",
                "wo ist", "sendung", "verfolgen", "ankommen", "geliefert", "wann",
                "bestellung", "lieferung")
HUMAN_WORDS = ("human", "person", "agent", "manager", "representative", "speak to someone",
               "mensch", "mitarbeiter", "kollege", "berater", "jemandem sprechen")
YES_WORDS = ("yes", "yep", "yeah", "sure", "please do", "go ahead", "confirm", "ok",
             "okay", "do it", "ja", "gerne", "bitte", "machen sie", "einverstanden")


# --- copy, per language -----------------------------------------------------

LINES = {
    "escalated": {
        "en": "Of course — I've passed you to a colleague. They'll pick this up within about four hours and they can see everything we've discussed, so you won't need to repeat yourself.",
        "de": "Selbstverständlich — ich habe Sie an eine Kollegin oder einen Kollegen weitergeleitet. Die Rückmeldung kommt innerhalb von etwa vier Stunden, und der gesamte Verlauf ist einsehbar. Sie müssen also nichts wiederholen.",
    },
    "refunded": {
        "en": "Done — €{amount:.2f} is on its way back to your original payment method, and it should land within 5–7 business days. Your refund reference is {ref}.",
        "de": "Erledigt — {amount:.2f} € sind auf dem Weg zurück auf Ihr ursprüngliches Zahlungsmittel und sollten innerhalb von 5 bis 7 Werktagen ankommen. Ihre Erstattungsreferenz lautet {ref}.",
    },
    "refund_failed": {
        "en": "I couldn't complete that: {error}",
        "de": "Das konnte ich nicht abschließen: {error}",
    },
    "refund_declined": {
        "en": "No problem — I've left the order as it is. Anything else I can help with?",
        "de": "Kein Problem — ich habe die Bestellung unverändert gelassen. Kann ich sonst etwas für Sie tun?",
    },
    "ask_order": {
        "en": "Happy to help with that. What's the order number? It starts with BK- and it's in your confirmation email.",
        "de": "Das mache ich gerne. Wie lautet die Bestellnummer? Sie beginnt mit BK- und steht in Ihrer Bestellbestätigung.",
    },
    "ask_email": {
        "en": "Thanks. And which email address was {order_id} placed with? I just need it to confirm the order is yours.",
        "de": "Danke. Und mit welcher E-Mail-Adresse wurde {order_id} bestellt? Ich brauche sie nur zur Bestätigung, dass die Bestellung Ihnen gehört.",
    },
    "mismatch": {
        "en": "Hmm, that order number and email don't match up. Could you double-check both for me?",
        "de": "Hmm, Bestellnummer und E-Mail-Adresse passen nicht zusammen. Könnten Sie bitte beides noch einmal prüfen?",
    },
    "in_transit": {
        "en": "Your order is on its way — {carrier} has it, tracking {tracking}, and it's estimated to arrive on {eta}.",
        "de": "Ihre Bestellung ist unterwegs — {carrier} hat sie, Sendungsnummer {tracking}, voraussichtliche Zustellung am {eta}.",
    },
    "delivered": {
        "en": "That one was delivered on {date} via {carrier} (tracking {tracking}). Let me know if it didn't reach you.",
        "de": "Diese Bestellung wurde am {date} über {carrier} zugestellt (Sendungsnummer {tracking}). Sagen Sie mir Bescheid, falls sie nicht angekommen ist.",
    },
    "which_item": {
        "en": "That order has two books in it — {titles}. Which one would you like to return?",
        "de": "Diese Bestellung enthält zwei Bücher — {titles}. Welches möchten Sie zurückgeben?",
    },
    "eligible": {
        "en": "Good news — that's still within the 30-day window, with {days} days to spare. I can refund €{amount:.2f} to your original payment method. Shall I go ahead?",
        "de": "Gute Nachricht — das liegt noch innerhalb der 30-Tage-Frist, mit {days} Tagen Puffer. Ich kann {amount:.2f} € auf Ihr ursprüngliches Zahlungsmittel erstatten. Soll ich das veranlassen?",
    },
    "eligible_item": {
        "en": "Got it — “{title}”. That's within the window, so I can refund €{amount:.2f}. Shall I go ahead?",
        "de": "Verstanden — „{title}“. Das liegt innerhalb der Frist, ich kann also {amount:.2f} € erstatten. Soll ich das veranlassen?",
    },
    "not_eligible": {
        "en": "I'm sorry — I can't process a return on that one. {reason} I know that's not what you were hoping for; I can put you through to a colleague if you'd like to talk it through.",
        "de": "Es tut mir leid — eine Rückgabe ist hier nicht möglich. {reason} Ich weiß, das ist nicht die Antwort, die Sie sich erhofft haben. Gerne verbinde ich Sie mit einer Kollegin oder einem Kollegen.",
    },
    "article": {
        "en": "{body}\n\n(From our help centre: {title}, {id})",
        "de": "{body}\n\n(Aus unserem Hilfebereich: {title}, {id})",
    },
    "no_article": {
        "en": "I don't have anything on that in the help centre, and I'd rather not guess. Would you like me to put you through to a colleague?",
        "de": "Dazu finde ich nichts im Hilfebereich, und ich möchte nicht raten. Soll ich Sie mit einer Kollegin oder einem Kollegen verbinden?",
    },
}

# policy.py emits a language-neutral reason_code and an English hint. Rendering
# that code into a sentence is a presentation job, so it happens here.
REASONS = {
    "OUTSIDE_RETURN_WINDOW": {
        "de": "Bestellung {order_id} wurde vor {days} Tagen zugestellt und liegt damit außerhalb der 30-tägigen Rückgabefrist.",
    },
    "NOT_YET_DELIVERED": {
        "de": "Bestellung {order_id} wurde noch nicht zugestellt — die Rückgabefrist beginnt erst mit der Zustellung.",
    },
    "NON_RETURNABLE_FORMAT": {
        "de": "Diese Bestellung enthält ausschließlich digitale Artikel, die vom Umtausch ausgeschlossen sind, sobald der Download-Link versendet wurde.",
    },
    "ALREADY_REFUNDED": {
        "de": "Bestellung {order_id} wurde bereits erstattet.",
    },
}


def _t(session: Session, key: str, **kw) -> str:
    return LINES[key].get(session.language, LINES[key]["en"]).format(**kw)


def _reason(session: Session, check: dict) -> str:
    """Render an eligibility verdict in the conversation's language."""
    if session.language == "en":
        return check["explanation"]
    template = REASONS.get(check["reason_code"], {}).get("de")
    if not template:
        return check["explanation"]
    return template.format(
        order_id=check.get("order_id", ""),
        days=check.get("days_since_delivery") or 0,
    )


def _say(session: Session, text: str) -> dict:
    session.messages.append({"role": "assistant", "content": text})
    session.log("assistant", text)
    session.say("bot", text)
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
        yield _say(session, _t(session, "escalated"))
        return

    # Awaiting a yes/no on a quoted refund.
    if sc.get("pending_refund"):
        order_id = sc["pending_refund"]
        if any(w in text for w in YES_WORDS):
            sc.pop("pending_refund")
            yield from _call(session, "issue_refund",
                             {"order_id": order_id, "customer_confirmed": True})
            res = sc["last_result"]
            if res.get("success"):
                yield _say(session, _t(session, "refunded",
                                       amount=res["amount_eur"], ref=res["refund_id"]))
            else:
                yield _say(session, _t(session, "refund_failed", error=res.get("error")))
            return
        sc.pop("pending_refund")
        yield _say(session, _t(session, "refund_declined"))
        return

    # Intent persists across turns. Without this the planner forgets why it
    # asked for an order number the moment the customer supplies one.
    if any(w in text for w in RETURN_WORDS):
        sc["intent"] = "return"
    elif any(w in text for w in STATUS_WORDS):
        sc.setdefault("intent", "status")

    wants_return = sc.get("intent") == "return"
    wants_status = sc.get("intent") == "status"

    if wants_return or wants_status:
        # Clarifying question: refuse to act on half the facts.
        if not sc.get("order_id"):
            yield _say(session, _t(session, "ask_order"))
            return
        if not sc.get("email"):
            yield _say(session, _t(session, "ask_email", order_id=sc["order_id"]))
            return

        yield from _call(session, "lookup_order",
                         {"order_id": sc["order_id"], "email": sc["email"]})
        res = sc["last_result"]
        if not res.get("found"):
            sc.pop("order_id", None)
            yield _say(session, _t(session, "mismatch"))
            return

        order = res["order"]

        if wants_status and not wants_return:
            sc.pop("intent", None)
            if order["status"] == "in_transit":
                yield _say(session, _t(session, "in_transit", carrier=order["carrier"],
                                       tracking=order["tracking_number"],
                                       eta=order["estimated_delivery"]))
            else:
                yield _say(session, _t(session, "delivered", date=order["delivered_at"],
                                       carrier=order["carrier"],
                                       tracking=order["tracking_number"]))
            return

        # Clarifying question: a multi-item order is genuinely ambiguous.
        if len(order["items"]) > 1 and not sc.get("sku"):
            joiner = " oder " if session.language == "de" else " or "
            titles = joiner.join(f"„{i['title']}“" if session.language == "de"
                                 else f"“{i['title']}”" for i in order["items"])
            sc["awaiting_item"] = order["order_id"]
            yield _say(session, _t(session, "which_item", titles=titles))
            return

        yield from _call(session, "check_return_eligibility",
                         {"order_id": order["order_id"], "sku": sc.get("sku")})
        check = dict(sc["last_result"], order_id=order["order_id"])
        sc.pop("intent", None)
        if check["eligible"]:
            sc["pending_refund"] = order["order_id"]
            yield _say(session, _t(session, "eligible", days=check["days_remaining"],
                                   amount=check["refundable_amount_eur"]))
        else:
            yield _say(session, _t(session, "not_eligible", reason=_reason(session, check)))
        return

    # Item disambiguation follow-up.
    if sc.get("awaiting_item"):
        from bookly.data import ORDERS
        order = ORDERS[sc["awaiting_item"]]
        for item in order["items"]:
            if item["title"].lower().split()[0] in text:
                sc["sku"] = item["sku"]
                sc.pop("awaiting_item")
                yield from _call(session, "check_return_eligibility",
                                 {"order_id": order["order_id"], "sku": item["sku"]})
                check = dict(sc["last_result"], order_id=order["order_id"])
                if check["eligible"]:
                    sc["pending_refund"] = order["order_id"]
                    yield _say(session, _t(session, "eligible_item", title=item["title"],
                                           amount=check["refundable_amount_eur"]))
                else:
                    yield _say(session, _t(session, "not_eligible",
                                           reason=_reason(session, check)))
                return

    # Everything else is a knowledge question.
    yield from _call(session, "search_help_center", {"query": user_text})
    res = sc["last_result"]
    if res.get("results"):
        top = res["results"][0]
        yield _say(session, _t(session, "article", body=top["body"],
                               title=top["title"], id=top["id"]))
    else:
        yield _say(session, _t(session, "no_article"))
