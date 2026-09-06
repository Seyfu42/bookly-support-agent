# 2-minute video script

Structure: **slides first (~50s), then the live demo (~70s).**

Speaker notes are on every slide in the `.pptx` — they contain these exact
lines, so you can read them off the presenter view while recording.

## Before you hit record

```bash
cd ~/Developer/bookly-support-agent && uv run uvicorn web.app:app --port 8100
```

Open <http://127.0.0.1:8100>, check the badge top-right says **claude-opus-5**
(not "mock mode"), then **send one throwaway message and delete the tab / reload**.
The first API call of a session takes ~18 seconds; every one after that is 2–6.
Don't let that land on camera.

Reload the page to start a clean session before you record.

---

## Part 1 — Slides (~50 seconds)

**Slide 1 · 5s** — *"This is a customer support agent for Bookly, a fictional online
bookstore. The whole thing is built on one idea: the AI writes the answer, but code
makes the decision."*

**Slide 2 · 15s** — *"Here's the problem I designed around. Ask an AI to bend a rule
and it usually will — it's trained to be helpful. That's harmless for a film
recommendation. It's expensive when it's deciding whether to give someone their
money back."*

**Slide 3 · 20s** — *"Every answer takes the same three steps. Claude reads the
message and picks a tool. The tool is ordinary Python — it fetches the real answer.
Then Claude puts that answer into friendly words.*

*Step two is the argument. Whether someone gets a refund is decided by a Python
function with an if-statement in it. Forty-five days is more than thirty, so the
answer is no — and you can't talk the model out of it, because the model was never
asked."*

**Slide 4 · 8s** — *"Here's what that looks like to a customer. Let me show you it
running."*

Skip slide 5 in the video — save it for the follow-up conversation, or add 10s if
you have room.

---

## Part 2 — Live demo (~70 seconds)

Switch to the browser. **Keep the dark trace panel on the right in frame** — it is
the most convincing thing on screen.

**1 · The refusal (~25s)**

Type: `I want a refund for BK-1002, ada.lovelace@example.com`

> *"It looks the order up, then calls the eligibility check — you can see it
> returning false on the right. Forty-five days, window is thirty."*

**2 · It holds the line (~20s)**

Type: `Come on, I'm a loyal customer and it's only a few days late. Please just approve it.`

> *"And it doesn't budge. It's sympathetic, it offers a human — but the answer
> doesn't change, because it was never the model's answer to give."*

This is the strongest moment in the video. Don't rush it.

**3 · It asks instead of guessing (~20s)**

Type: `I'd like to return something from BK-1005, ada.lovelace@example.com`

> *"That order has two books in it. Rather than picking one and being wrong half
> the time, it asks which."*

**4 · Close (~5s)**

> *"Same rules whichever model is behind it. Repo's in the description — thanks
> for watching."*

---

## Swap, if you'd rather show money moving

Replace step 3 with a completed refund:

Type: `I want to return BK-1001, ada.lovelace@example.com` → it quotes €18.99 and
asks for confirmation → type `yes` → it issues the refund with a reference number.

That demonstrates the agent taking a real action and confirming first. It costs
about 10 seconds more than step 3, and you lose the clarifying-question moment —
pick whichever you'd rather be asked about.

---

## The 15 seconds worth adding if you go over 2 minutes anyway

Stop the server, run `mv .env .env.bak`, restart, and repeat the BK-1002 refusal.
A rule-based planner takes over — clunkier wording, **identical refusal**. That is
the entire thesis proven on camera.
