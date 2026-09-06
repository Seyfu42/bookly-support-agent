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
S2 = {
    "bg": CREAM,
    "notes": (
        "SAY: \"Here's the problem I designed around. If you ask an AI to bend a "
        "rule, it usually will — it's trained to be helpful. That's harmless when "
        "it's guessing a film recommendation. It's expensive when it's deciding "
        "whether to give someone their money back.\"\n\n"
        "\"So I made a rule for myself: the model is never allowed to make that "
        "decision.\"\n\nAbout fifteen seconds."
    ),
    "el": [
        headline("An AI wants to please you.\nA refund policy shouldn't."),
        rect(M, 3.55, 5.55, 2.05, CLAY_SOFT, 0.10),
        text(M + 0.40, 3.85, 4.75, 0.32, "A CHATBOT OPTIMISES FOR",
             size=12, color=CLAY, bold=True),
        text(M + 0.40, 4.30, 4.75, 1.05, "Making you happy\nright now.",
             size=25, color=INK, font=SERIF, bold=True, spacing=1.15),

        rect(M + 6.08, 3.55, 5.55, 2.05, SOFT, 0.10),
        text(M + 6.48, 3.85, 4.75, 0.32, "A SUPPORT AGENT MUST OPTIMISE FOR",
             size=12, color=GREEN, bold=True),
        text(M + 6.48, 4.30, 4.75, 1.05, "Being right\nabout money.",
             size=25, color=INK, font=SERIF, bold=True, spacing=1.15),

        text(M, 6.20, 11.4, 0.45,
             "Both matter. Only one of them can be left to a language model.",
             size=17, color=MUTED, italic=True),
    ],
}


# ---------------------------------------------------------------- Slide 3
_SW = (W - 2 * M - 2 * 0.45) / 3
_SY, _SH = 3.05, 3.05

_STEPS = [
    ("1", "Claude picks a tool", "It reads the message and chooses: look up this order, check this refund, search the help pages.", GREEN),
    ("2", "Python decides", "45 days since delivery. The window is 30. The answer is no — computed by code, not judged by the model.", CLAY),
    ("3", "Claude replies", "It explains the outcome kindly. It is not allowed to overturn step 2, however the customer asks.", GREEN),
]

_el3 = [
    headline("Every answer takes the same three steps.", size=40, h=1.0),
    text(M, 2.15, 11.4, 0.45,
         "The middle one is the whole argument.",
         size=17, color=MUTED),
]
for i, (num, title, body, accent) in enumerate(_STEPS):
    sx = M + i * (_SW + 0.45)
    mid = i == 1
    _el3 += [
        rect(sx, _SY, _SW, _SH, SOFT if mid else WHITE, 0.10,
             line=None if mid else "DEDDD8"),
        text(sx + 0.34, _SY + 0.30, 1.2, 0.62, num,
             size=34, color=accent, font=SERIF, bold=True),
        text(sx + 0.34, _SY + 1.02, _SW - 0.68, 0.62, title,
             size=20, color=INK, font=SERIF, bold=True, spacing=1.15),
        text(sx + 0.34, _SY + 1.80, _SW - 0.68, 1.05, body,
             size=13.5, color=MUTED, spacing=1.3),
    ]

_el3.append(
    text(M, 6.42, 11.43, 0.52,
         [("Conversations live in SQLite, not memory. ", {"bold": True}),
          ("Restart the server mid-conversation and the agent still knows which "
           "order you meant — and still refuses the refund.", {})],
         size=14, color=MUTED)
)

S3 = {
    "bg": CREAM,
    "notes": (
        "SAY: \"Every single answer goes through the same three steps.\"\n\n"
        "\"Claude reads the message and picks a tool. The tool is ordinary Python "
        "— it goes and gets the real answer. Then Claude puts that answer into "
        "friendly words.\"\n\n"
        "\"Step two is the argument. Whether someone gets a refund is decided by a "
        "Python function with an if-statement in it. Forty-five days is more than "
        "thirty, so the answer is no — and there's no way to talk the model out of "
        "it, because the model was never asked.\"\n\n"
        "If you have a spare beat, add: \"and conversations are stored in SQLite, so this survives a server restart.\" Otherwise skip it.\n\n"
        "About twenty seconds. This is the slide that matters most."
    ),
    "el": _el3,
}


# ---------------------------------------------------------------- Slide 4
_COLW = (W - 2 * M - 0.43) / 2
_COLY, _COLH = 2.62, 2.72

S4 = {
    "bg": CREAM,
    "notes": (
        "SAY: \"Same customer, same order, two languages. On the left English, on "
        "the right German — and the agent is genuinely answering in German, not "
        "translating a script.\"\n\n"
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
             "Real replies from the running agent. English is the default; German is a toggle.",
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
