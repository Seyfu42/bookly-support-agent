# 2-minute video script

Structure: **slides first (~55s), then the live demo (~75s).** Aim for 2:00-2:30
— the brief asks for two minutes, and for a solutions-engineering role the
concision is part of what is being assessed.

Speaker notes are on every slide in the `.pptx` — they contain these exact lines,
so you can read them off the presenter view while recording.

## Before you hit record

```bash
cd ~/Developer/bookly-support-agent && uv run uvicorn web.app:app --port 8100
```

Open <http://127.0.0.1:8100> and check three things:

1. The badge top-right says **claude-opus-5**, not "mock mode".
2. The language toggle is on **EN**.
3. **Send one throwaway message, then click "New conversation".** The first API
   call of a server's life takes ~18 seconds; every one after is 2-6. Do not let
   that land on camera.

---

## Part 1 — Slides (~55 seconds)

**Slide 1 · 5s** — *"This is a customer support agent for Bookly, a fictional
online bookstore. The whole thing is built on one idea: the AI writes the answer,
but code makes the decision."*

**Slide 2 · 15s** — *"Here's the problem I designed around. Ask an AI to bend a
rule and it usually will — it's trained to be helpful. That's harmless for a film
recommendation. It's expensive when it's deciding whether to give someone their
money back."*

**Slide 3 · 20s** — *"Every answer takes the same three steps. Claude reads the
message and picks a tool. The tool is ordinary Python — it fetches the real
answer. Then Claude puts that answer into friendly words.*

*Step two is the argument. Whether someone gets a refund is decided by a Python
function with an if-statement in it. Forty-five days is more than thirty, so the
answer is no — and you can't talk the model out of it, because the model was
never asked."*

If you have a spare beat: *"and conversations are stored in SQLite, so all of
this survives a server restart."*

**Slide 4 · 15s** — *"Same refusal in two languages. Look at the bottom: that's
one tool result, shared by both. Let me show you it running."*

Skip slide 5 in the video — it's a better answer to a follow-up question than a
rushed eight seconds on camera.

---

## Part 2 — Live demo (~75 seconds)

Switch to the browser. **Keep the dark trace panel on the right in frame** — it
is the most convincing thing on screen.

**1 · The refusal (~25s)**

Type: `I want a refund for BK-1002, ada.lovelace@example.com`

> *"It looks the order up, then calls the eligibility check — you can see it
> returning false on the right. Forty-five days, window is thirty."*

**2 · It holds the line (~20s)**

Type: `Come on, I'm a loyal customer and it's only a few days late. Please just approve it.`

> *"And it doesn't budge. It's sympathetic, it offers a human — but the answer
> doesn't change, because it was never the model's answer to give."*

This is the strongest moment in the video. Don't rush it.

**3 · The same thing in German (~20s)**

Click **DE**, then click the chip:
`Ich möchte eine Erstattung für BK-1002, ada.lovelace@example.com`

> *"Same order, German. And look at the trace panel — the customer-facing text
> changed, but the reason code is still OUTSIDE_RETURN_WINDOW in English. The
> policy engine doesn't know German exists."*

Point at the trace panel while you say it. The contrast is the whole thesis in
one frame.

**4 · Close (~10s)**

> *"Same rules whichever language, whichever model. Repo's in the description —
> thanks for watching."*

---

## Swaps, if you'd rather show something else

**Money actually moving.** Replace step 3 with:
`I want to return BK-1001, ada.lovelace@example.com` → it quotes EUR 18.99 and
asks for confirmation → `yes` → it issues the refund with a reference number.
Shows the agent taking a real action and confirming first, but you lose the
German moment.

**It asks instead of guessing.** `I'd like to return something from BK-1005,
ada.lovelace@example.com` — two books in that order, so it asks which one rather
than picking and being wrong half the time.

---

## Optional segments, if you record a longer deep-dive

**Durable sessions (~25s).** Needs a terminal in frame, so it does not fit the
2-minute cut.

1. Have the BK-1002 refusal on screen.
2. In the terminal, Ctrl-C the server, then start it again.
3. Reload the browser — the conversation and the trace come back, with a
   "restored from storage" marker.
4. Type something deliberately vague: `But it's only a couple of weeks late. Can
   you make an exception?`

It answers *"fifteen days past…"* — a number it could only know from the
eligibility check made before the process died. Don't demo that the text came
back; demo that **the agent still knows.**

**The brain swap (~15s).** Stop the server, `mv .env .env.bak`, restart, and
repeat the BK-1002 refusal. A rule-based planner takes over — clunkier wording,
**identical refusal**, in either language. That is the entire thesis on camera.
