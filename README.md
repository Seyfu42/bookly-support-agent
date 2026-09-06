# Bookly Support Agent

A customer support AI agent for Bookly, a fictional online bookstore. It handles
**order status** and **returns/refunds** end to end, and answers general policy
questions from a help centre.

Built with the Anthropic API and a hand-written agent loop — no agent framework.

---

## The thesis in one line

**The model decides what to *say* and which tool to *reach for*. It never decides
what is true, what is allowed, or what moves money.**

Everything below follows from that.

| Question | Who answers it | Where |
|---|---|---|
| What does the customer want? | The model | `bookly/agent.py` |
| What is this order's status? | The order system | `bookly/tools.py` |
| Can this be returned? | **Deterministic Python** | `bookly/policy.py` |
| Is this caller who they claim? | **The tool layer** | `bookly/tools.py` |
| May this refund go through? | **Preconditions in code** | `bookly/tools.py` |
| How do we say it kindly? | The model | `bookly/prompts.py` |

An LLM asked *"can I return a book I received 45 days ago?"* is under real
pressure to be agreeable. It will find a reason to say yes. Moving that decision
into `policy.py` removes the opportunity: there is no prompt to jailbreak, and no
temperature at which 45 becomes less than 30.

---

## Run it

Requires [uv](https://docs.astral.sh/uv/) and nothing else — no Node, no build step.

```bash
git clone <this-repo> && cd bookly-support-agent
uv venv --python 3.12 && uv pip install -e ".[dev]"
```

**Web chat** (recommended — shows the live tool trace):

```bash
uv run uvicorn web.app:app --port 8100
```

Then open <http://127.0.0.1:8100>.

**Terminal:**

```bash
uv run cli.py
```

**Tests:**

```bash
uv run pytest -q
```

### API key (optional)

```bash
cp .env.example .env   # then paste your key into .env
```

Without a key the agent runs in **mock mode**: a scripted rule-based planner
drives the *same* tools, the *same* policy engine and the *same* refund
preconditions. So `git clone && uv run` gives a working demo on any machine, and
a live demo can't be killed by a flaky network.

That fallback is also the cleanest evidence for the thesis. Swapping the brain
out changes how well the agent understands a sentence. It does not change one
thing about what the system is *permitted to do*.

---

## Try these

| Say this | What it demonstrates |
|---|---|
| `Where is my order?` → `BK-1003` → `ada.lovelace@example.com` | **Multi-turn** identity collection |
| `I want to return a book` → `BK-1001, ada.lovelace@example.com` → `yes` | **Tool use** + confirm-before-refund |
| `I want a refund for BK-1002, ada.lovelace@example.com` | **Refuses politely** — 45 days, outside the window |
| `Return something from BK-1005, ada.lovelace@example.com` | **Clarifying question** — two books, won't guess |
| `Refund BK-1004 ada.lovelace@example.com` | Ebooks are non-returnable |
| `How long does shipping take?` | Grounded retrieval with source citation |
| `Can I speak to a human?` | Graceful escalation |

Test data lives in `bookly/data.py`. Every order exists to make one branch of the
policy reachable.

---

## Architecture

```
      customer turn
            │
            ▼
   ┌──────────────────┐
   │   agent loop     │   bookly/agent.py — hand-written, ~60 lines
   │  (while tool_use)│   iteration cap · error surfacing · trace events
   └────────┬─────────┘
            │  Claude Opus 5 + tool schemas + system prompt
            ▼
   ┌──────────────────┐
   │   tool layer     │   bookly/tools.py — where the guardrails actually live
   └────────┬─────────┘
            │
   ┌────────┴─────────────────────────────────────┐
   │                                              │
   ▼                    ▼                ▼        ▼
lookup_order    check_return_      issue_refund  search_help_center
(verifies         eligibility      (3 hard        (grounded answers,
 id + email)    ── policy.py ──     preconditions)  cited by article id)
                deterministic
```

Session state (`bookly/session.py`) is deliberately split in two:

- `messages` — what the model sees.
- `verified_orders`, `eligibility_checks` — what the *application* knows.

Security-relevant facts live in the second group, as plain Python. The model
cannot talk its way around a `set`.

### Why a hand-written loop

The loop is short, and every line of it is a place a support agent needs a policy
hook: iteration caps, tool gating, trace emission, error surfacing. A framework
puts those behind a callback API. Here they are just code you can read.

### Three decisions worth defending

**1. Eligibility is code, not a prompt.** Trade-off: every policy change is a
deploy, not a prompt edit. Worth it because the rule becomes auditable and
unit-testable — see `tests/test_policy.py`. That is the artefact a compliance
team asks for, and no prompt can produce it.

**2. Preconditions on the write tool, not instructions about it.** `issue_refund`
refuses unless identity was verified, eligibility was checked *and passed*, and
the customer confirmed. A prompt saying "always confirm first" is a suggestion.
`tests/test_refund_gate.py` shows the model being overruled in four different
ways it might be talked into a bad refund.

**3. Required tool arguments generate the conversation.** `lookup_order` needs
both an order id and an email. Nobody wrote a dialogue script for collecting
them — the schema makes the call impossible without both, so the model asks. Flow
control through type signatures rather than prompt instructions.

### What I'd change first for production

Add the **eval set** before anything else. Every safety property here is asserted
by unit tests over deterministic code, which is exactly right for policy — but
there is currently nothing measuring the model's half: did it pick the right
tool, did it ask when it should have asked, did it stay grounded? Without that,
the next prompt change is a guess. Then: real persistence (state is in-process
today), an LLM-as-judge for tone regression, structured logging with per-turn
cost, and server-side refusal fallbacks — omitted here to keep the demo free of
beta API dependencies a reviewer would have to debug.

---

---

## Assumptions

The brief said to make reasonable assumptions and document them. These are mine,
with the reasoning, so you can tell which are considered positions and which are
just scope.

**Chat, not voice.** The brief allowed either. Chat lets the four hours go into
agent behaviour rather than audio plumbing. The mitigation is structural rather
than promissory: the core takes text in and returns events, and both `web/app.py`
and `cli.py` are thin adapters over the same `run_turn()`. A voice channel is a
third sibling, not a rewrite.

**Two use cases, not five.** Order status and returns/refunds, following the
brief's own steer toward depth. Returns is the interesting one — it is the only
flow with a real eligibility decision, a real irreversible action, and a genuine
reason to refuse a customer. Adding damaged-items or password-reset would have
added surface area without adding an argument.

**Identity verification is a stand-in, not a claim.** Matching an order id
against the email on the order is enough to demonstrate *that* verification gates
tool access, and where that gate belongs. It is not authentication. Real
deployment puts a session token from the customer's logged-in context here, and
the tool layer is the right place for it either way.

**All backends are mocked.** Orders, the help centre and refunds are Python dicts
in `bookly/data.py`. Each stands for a different real system — an OMS, a CMS, a
payments service — and the agent reaches all of them only through the tool layer,
so replacing a mock with an HTTP call changes one function body and nothing else.

**Retrieval is keyword matching, not embeddings.** With five help-centre articles,
a vector store would be theatre. The interface — a query in, cited article ids
out — is what matters, and it is the same interface a real index would present.

**"Today" is pinned to 6 September 2026** (`bookly/data.py`). Return-window maths
against a moving clock would mean the demo drifts: the order that proves the
30-day refusal would eventually stop being 45 days old. Pinning it keeps the
scenarios stable and the tests deterministic.

**State is in-process and single-instance.** Sessions live in a module-level dict.
Fine for a demo, wrong for production — it is the second item on the "what I'd do
differently" list.

**Prices in EUR, shipping copy written for Germany.** Bookly is fictional; this
just keeps the demo internally consistent.

**No authentication on the web endpoint.** `/api/chat` is open, and the server is
meant to run on localhost. Putting real auth in front of it would have
demonstrated nothing the tool layer does not already demonstrate.

## Layout

```
bookly/
  agent.py      the loop
  tools.py      schemas + dispatch + guardrails
  policy.py     deterministic eligibility rules
  prompts.py    system prompt (tone and judgement only)
  session.py    conversation + application state
  data.py       mock order and help-centre backends
  mock_llm.py   scripted planner for the no-API-key path
web/
  app.py        FastAPI channel adapter (SSE)
  static/       single-file chat UI, no build step
cli.py          terminal channel adapter
tests/          policy and guardrail tests
```

The core knows nothing about HTTP. `web/app.py` and `cli.py` are both thin
adapters over the same `run_turn()`. A voice or SMS front end would be a sibling
of those files, not a rewrite of anything underneath.
