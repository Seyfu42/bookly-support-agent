"""Deck content and layout, in inches.

Designed to be TALKED OVER in a screen recording, not read in silence. That
drives every choice here: one idea per slide, headlines that carry the argument
on their own, and very little body text. The full script lives in each slide's
speaker notes.

One spec, two renderers (see build.py): the .pptx and an HTML preview.
Coordinates are inches on a 13.333 x 7.5 canvas. Font sizes are points.

Note: real PowerPoint sets lines taller than a browser does, so every text box
here carries deliberate vertical slack.
"""

W, H = 13.333, 7.5
M = 0.95

INK = "14201C"
GREEN = "1F5F4F"
GREEN_DEEP = "12352C"
MOSS = "8FB3A4"
SOFT = "E8F0ED"
CREAM = "F6F5F3"
WHITE = "FFFFFF"
CLAY = "A4552B"
CLAY_SOFT = "F5E7DE"
MUTED = "6E7671"
MUTED_DARK = "9DAAA3"
TRACE_BG = "14161A"
TRACE_INK = "9DB4AB"

SERIF = "Cambria"
SANS = "Calibri"
MONO = "Courier New"

AUTHOR = "Seyfullah Ural"
DATE = "September 2026"


def rect(x, y, w, h, fill, radius=0.0, line=None):
    return {"t": "rect", "x": x, "y": y, "w": w, "h": h, "fill": fill,
            "radius": radius, "line": line}


def text(x, y, w, h, body, size=16, color=INK, font=SANS, bold=False,
         italic=False, align="l", spacing=1.2, space_after=0):
    return {"t": "text", "x": x, "y": y, "w": w, "h": h, "body": body,
            "size": size, "color": color, "font": font, "bold": bold,
            "italic": italic, "align": align, "spacing": spacing,
            "space_after": space_after}


def arrow(x, y, w, color=MOSS):
    """A short connector between pipeline boxes."""
    return {"t": "arrow", "x": x, "y": y, "w": w, "color": color}


def headline(body, size=42, color=INK, y=0.95, w=11.2, h=1.7):
    return text(M, y, w, h, body, size=size, color=color, font=SERIF,
                bold=True, spacing=1.1)


# ---------------------------------------------------------------- Slide 1
S1 = {
    "bg": GREEN_DEEP,
    "notes": (
        "SAY: \"This is a customer support agent for Bookly, a fictional online "
        "bookstore. The whole thing is built on one idea, and it's on this slide: "
        "the AI writes the answer, but code makes the decision.\"\n\n"
        "Hold this slide for about five seconds. Don't explain it yet — the next "
        "slide explains why it matters."
    ),
    "el": [
        text(M, 1.30, 8.0, 0.35, "BOOKLY  ·  CUSTOMER SUPPORT AGENT",
             size=13, color=MOSS, bold=True),
        headline("The AI writes the answer.\nCode makes the decision.",
                 size=46, color=WHITE, y=2.05, w=11.4, h=2.4),
        rect(M, 4.80, 1.6, 0.04, MOSS),
        text(M, 6.45, 11.4, 0.42, f"{AUTHOR}   ·   {DATE}",
             size=13.5, color=MUTED_DARK),
    ],
}


# ---------------------------------------------------------------- Slide 2
# Architecture. The brief names four components to cover -- orchestration,
# tools, memory and prompts -- so all four are labelled explicitly.
_BW = (W - 2 * M - 3 * 0.30) / 4
_BY, _BH = 2.72, 2.10


def _box(i):
    return M + i * (_BW + 0.30)


_PARTS = [
    ("PROMPTS", "System prompt", "Tone and behaviour.\nNo business rules.", False),
    ("ORCHESTRATION", "The agent loop", "Hand-written, under 100\nlines. No framework.", True),
    ("TOOLS", "Five tools", "Identity checks and refund\npreconditions live here.", False),
    ("MEMORY", "Split state", "Transcript for the model.\nFacts for the app.", False),
]

_el2 = [
    headline("How a question becomes an answer", size=40, h=1.0),
    text(M, 2.05, 11.43, 0.45, "Four moving parts. Only one of them guesses.",
         size=17, color=MUTED),
]
for i, (label, title, body, lit) in enumerate(_PARTS):
    bx = _box(i)
    _el2 += [
        rect(bx, _BY, _BW, _BH, GREEN if lit else WHITE, 0.10,
             line=None if lit else "DEDDD8"),
        text(bx + 0.26, _BY + 0.24, _BW - 0.52, 0.30, label,
             size=10.5, color=MOSS, bold=True),
        text(bx + 0.26, _BY + 0.62, _BW - 0.52, 0.40, title,
             size=17, color=WHITE if lit else INK, font=SERIF, bold=True),
        text(bx + 0.26, _BY + 1.16, _BW - 0.52, 0.72, body,
             size=12.5, color=SOFT if lit else MUTED, spacing=1.3),
    ]
for i in range(3):
    _el2.append(arrow(_box(i) + _BW + 0.06, _BY + _BH / 2, 0.18))

_el2 += [
    rect(M, 5.18, 11.43, 1.20, SOFT, 0.10),
    text(M + 0.34, 5.40, 6.0, 0.30, "WHAT THE FLOW NEVER DOES", size=11,
         color=GREEN, bold=True),
    text(M + 0.34, 5.74, 10.75, 0.50,
         "A customer turn enters on the left and leaves as a reply. Nothing in "
         "between ever asks the model what the rules are.",
         size=15, color=INK, spacing=1.3),
    text(M, 6.62, 11.43, 0.45,
         [("Memory is deliberately split. ", {"bold": True}),
          ("The model sees the transcript. Whether identity was verified is held "
           "by the application, in SQLite — the model cannot talk its way around a set.",
           {})],
         size=13.5, color=MUTED),
]

S2 = {
    "bg": CREAM,
    "notes": (
        "SAY: \"The architecture has four parts. The system prompt handles tone "
        "and behaviour, how to talk to the customer, when to ask instead of "
        "guessing. There are no business rules in it at all.\"\n\n"
        "\"The agent loop is hand-written, under a hundred lines, and it handles "
        "the orchestration between the parts. The tools are where the guardrails "
        "actually sit, like identity checks and the refund preconditions. And the "
        "memory is split in two: the model gets the transcript, anything security "
        "relevant stays on the application side.\"\n\n"
        "\"The most important part is that nothing here asks the model what the "
        "rules are.\"\n\n"
        "About twenty seconds."
    ),
    "el": _el2,
}


# ---------------------------------------------------------------- Slide 3
# Key decisions. The brief asks for 2-3, each with what was chosen, what was
# traded away, and why it was worth it.
_DW = (W - 2 * M - 2 * 0.42) / 3
_DY, _DH = 2.72, 3.98

_DECISIONS = [
    ("01", "Eligibility is code,\nnot a prompt",
     "Policy changes need a deploy, not a prompt edit.",
     "Auditable, unit-testable, and there is no prompt to jailbreak."),
    ("02", "The refund tool has\npreconditions",
     "More code than a single line of instruction.",
     "“Always confirm first” is a suggestion. This is enforced."),
    ("03", "Required arguments\nmake the dialogue",
     "Less freedom in how the agent phrases its way there.",
     "Multi-turn collection with no dialogue script written."),
]

_el3 = [
    headline("Three decisions worth defending", size=40, h=1.0),
    text(M, 2.05, 11.43, 0.45,
         "Each one moves authority out of the model and into code.",
         size=17, color=MUTED),
]
for i, (num, title, traded, bought) in enumerate(_DECISIONS):
    dx = M + i * (_DW + 0.42)
    _el3 += [
        rect(dx, _DY, _DW, _DH, WHITE, 0.10, line="DEDDD8"),
        text(dx + 0.30, _DY + 0.26, 1.0, 0.42, num,
             size=26, color=MOSS, font=SERIF, bold=True),
        text(dx + 0.30, _DY + 0.76, _DW - 0.60, 0.86, title,
             size=18, color=INK, font=SERIF, bold=True, spacing=1.16),
        text(dx + 0.30, _DY + 1.78, _DW - 0.60, 0.26, "TRADED AWAY",
             size=10, color=CLAY, bold=True),
        text(dx + 0.30, _DY + 2.06, _DW - 0.60, 0.62, traded,
             size=12.5, color=MUTED, spacing=1.28),
        text(dx + 0.30, _DY + 2.76, _DW - 0.60, 0.26, "WORTH IT BECAUSE",
             size=10, color=GREEN, bold=True),
        text(dx + 0.30, _DY + 3.04, _DW - 0.60, 0.62, bought,
             size=12.5, color=INK, spacing=1.28),
    ]

_el3.append(
    text(M, 6.92, 11.43, 0.45,
         [("The through-line: ", {"bold": True, "color": GREEN}),
          ("an AI wants to please you, and a refund policy shouldn't. "
           "Every decision above takes one more judgement away from the model.", {})],
         size=13.5, color=MUTED)
)

S3 = {
    "bg": CREAM,
    "notes": (
        "SAY: \"I made three design decisions, and each one moves authority out "
        "of the model and into the code.\"\n\n"
        "1 - Eligibility lives in the code, not the prompt. A policy change needs "
        "a deploy instead of a quick prompt edit. In return I can audit it, I can "
        "unit-test it, and there is no prompt for anyone to jailbreak.\n\n"
        "2 - The refund tool does not trust the model. Before it moves money it "
        "checks two things itself: that we really verified the order against the "
        "customer's email, and that the eligibility check came back positive. If "
        "one is missing it refuses, even when the model asks it to go ahead.\n\n"
        "3 - The required arguments create the dialogue. I never wrote a "
        "conversation script; the tool cannot be called without an order number "
        "and an email, so the agent has to collect them first.\n\n"
        "Close with: the reason behind all three is the same. A model is trained "
        "to be helpful, so it will always try to find a way to say yes, and when "
        "it comes to money that becomes a problem.\n\n"
        "About twenty-five seconds. This is the slide they will ask about."
    ),
    "el": _el3,
}


# ---------------------------------------------------------------- Slide 4
_COLW = (W - 2 * M - 0.43) / 2
_COLY, _COLH = 2.62, 2.72

S4 = {
    "bg": CREAM,
    "notes": (
        "SAY: \"Same customer, same order, two languages. Nobody clicked a "
        "setting — the customer asked in German and the agent switched itself.\"\n\n"
        "\"Look at the bottom. That is one tool result, shared by both. "
        "policy.py has never heard of German — it returns a code, and the code is "
        "the same code. Language changes the wording. It cannot touch the "
        "decision.\"\n\n"
        "\"And if the customer pushes back — in either language — it still says "
        "no. I tested that.\"\n\n"
        "About twenty-five seconds, then cut to the live demo."
    ),
    "el": [
        headline("Same refusal. Two languages.", size=40, h=1.0),
        text(M, 2.05, 11.43, 0.45,
             "Real replies from the running agent. English is the default — the customer just asked for German.",
             size=17, color=MUTED),

        # --- English ---------------------------------------------------------
        rect(M, _COLY, _COLW, _COLH, WHITE, 0.10, line="DEDDD8"),
        text(M + 0.32, _COLY + 0.24, 2.0, 0.30, "ENGLISH", size=11, color=GREEN, bold=True),
        text(M + 0.32, _COLY + 0.60, _COLW - 0.64, 0.42,
             "“I want a refund for BK-1002”", size=13, color=MUTED, italic=True),
        text(M + 0.32, _COLY + 1.14, _COLW - 0.64, 1.40,
             "BK-1002 isn't eligible for a refund — your copy of Piranesi was "
             "delivered on 23 July, 45 days ago, which falls outside the 30-day "
             "return window.",
             size=14, color=INK, spacing=1.34),

        # --- German ----------------------------------------------------------
        rect(M + _COLW + 0.43, _COLY, _COLW, _COLH, SOFT, 0.10),
        text(M + _COLW + 0.75, _COLY + 0.24, 2.0, 0.30, "DEUTSCH", size=11, color=GREEN, bold=True),
        text(M + _COLW + 0.75, _COLY + 0.60, _COLW - 0.64, 0.42,
             "„Ich möchte eine Erstattung für BK-1002“", size=13, color=MUTED, italic=True),
        text(M + _COLW + 0.75, _COLY + 1.14, _COLW - 0.64, 1.40,
             "Leider kann ich für BK-1002 keine Erstattung veranlassen: Die "
             "Bestellung wurde vor 45 Tagen zugestellt und liegt damit außerhalb "
             "des 30-tägigen Rückgabefensters.",
             size=14, color=INK, spacing=1.34),

        # --- the shared decision ---------------------------------------------
        rect(M, 5.58, 11.43, 1.06, TRACE_BG, 0.10),
        text(M + 0.36, 5.76, 6.0, 0.30, "ONE TOOL RESULT — SHARED BY BOTH",
             size=11, color="6B7684", bold=True),
        text(M + 0.36, 6.08, 10.7, 0.40,
             [("check_return_eligibility  →  ", {"font": MONO, "color": TRACE_INK}),
              ('"eligible": false', {"font": MONO, "bold": True, "color": "E0885F"}),
              ('   "reason": "OUTSIDE_RETURN_WINDOW"', {"font": MONO, "color": TRACE_INK})],
             size=13),

        text(M, 6.86, 11.43, 0.42,
             [("policy.py has never heard of German.", {"bold": True, "color": GREEN}),
              (" It returns a code; turning that code into a sentence is a "
               "presentation job.", {})],
             size=14, color=MUTED),
    ],
}


# ---------------------------------------------------------------- Slide 5
_NEXT = [
    ("An eval set", "The rules are covered by unit tests. The model's judgement isn't measured at all — so the next prompt change would be a guess."),
    ("Streaming replies", "Answers arrive as a block after a pause. Streaming them word by word is the difference between a script and a product."),
    ("Cost per conversation", "Support is priced per contact. You can't argue for AI deflection without that number."),
]

_el5 = [
    headline("What I'd build next.", size=40, h=1.0),
    text(M, 2.05, 11.43, 0.45, "In order. The first one isn't close.",
         size=17, color=MUTED),
]
_ry = 3.05
for i, (title, body) in enumerate(_NEXT):
    first = i == 0
    _el5 += [
        rect(M, _ry, 11.43, 1.16, SOFT if first else WHITE, 0.09,
             line=None if first else "DEDDD8"),
        text(M + 0.36, _ry + 0.26, 0.6, 0.5, str(i + 1),
             size=22, color=GREEN if first else MOSS, font=SERIF, bold=True),
        text(M + 1.00, _ry + 0.23, 3.5, 0.6, title,
             size=19, color=INK, font=SERIF, bold=True),
        text(M + 4.75, _ry + 0.22, 6.30, 0.80, body,
             size=13.5, color=MUTED, spacing=1.3),
    ]
    _ry += 1.30

# Credit what is already done. "Here is my plan" is a wish list; "I said these
# were next and two of them are built" is follow-through.
_el5.append(
    text(M, 7.02, 11.43, 0.42,
         [("Durable sessions and German were the previous two on this list. ",
           {"bold": True, "color": GREEN}),
          ("Both are built.", {})],
         size=14, color=MUTED)
)

S5 = {
    "bg": CREAM,
    "notes": (
        "SAY: \"Three things I'd do next. The first one isn't close.\"\n\n"
        "\"The policy rules are covered by unit tests, so I know those are right. "
        "But nothing measures the model's half — did it pick the right tool, did it "
        "ask a question when it should have. Without an eval set, my next prompt "
        "change is a guess.\"\n\n"
        "If asked why these three: the first two on this list -- durable "
        "sessions and German -- are already built, so this is the list after "
        "those.\n\n"
        "Then close: \"That's the agent. Let me show you it running.\"\n\n"
        "About fifteen seconds."
    ),
    "el": _el5,
}


SLIDES = [S1, S2, S3, S4, S5]
