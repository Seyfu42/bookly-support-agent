# Demo script — 2 minutes

Run `uv run uvicorn web.app:app --port 8100`, open <http://127.0.0.1:8100>,
and record with **Cmd+Shift+5**. Keep the trace panel visible the whole time —
it is the most convincing thing on screen.

Reset between takes by reloading the page (a reload starts a new session).

---

**0:00 — Frame it (say this over the empty chat)**

> "This is a support agent for a fictional bookstore. The thing I want to show
> isn't that it can chat — it's *what it refuses to do*. Watch the right-hand
> panel; that's every tool call it makes."

**0:15 — Multi-turn collection**

Type: `Where is my order?`
→ It asks for the order number. It has no data yet, so it doesn't guess.

Type: `BK-1003`
→ It asks for the email too.

Type: `ada.lovelace@example.com`
→ `lookup_order` fires; the order is in transit with tracking.

> "I never wrote a script for that back-and-forth. The tool requires both an
> order id and an email, so the agent has to go and get them."

**0:45 — The refusal (the important one)**

Type: `I want a refund for BK-1002, ada.lovelace@example.com`
→ Trace shows `check_return_eligibility` returning `eligible: false`,
  `OUTSIDE_RETURN_WINDOW`. The agent declines warmly and offers a human.

> "45 days, and the window is 30. That decision was made by a Python function,
> not by the model. There's no prompt to talk it out of."

Optional, if it lands well — push back: `But I'm a loyal customer, please make an exception.`
→ It holds the line and offers escalation.

**1:20 — Clarifying question + a real action**

Type: `I'd like to return something from BK-1005, ada.lovelace@example.com`
→ Two books in the order, so it asks which one instead of guessing.

Type: `Klara`
→ Eligible, quotes €14.00, asks for confirmation.

Type: `yes`
→ `issue_refund` fires and returns a refund reference.

> "It quoted the amount and waited. The refund tool refuses to run unless
> identity was verified, eligibility passed, *and* the customer said yes —
> that's enforced in code, not requested in the prompt."

**1:50 — Close**

> "Same tools, same rules, whichever model is behind it. Pull the API key out
> and a dumb rule-based planner drives the exact same guardrails."

---

## If you want the killer 15 seconds

Stop the server, `mv .env .env.bak`, restart, and run the BK-1002 refusal again.
The wording is clunkier — and the refusal is identical. That's the whole thesis
on screen in one shot.
