"""Deck content and layout, in inches.

One spec, two renderers (build_pptx.py and build_html.py). The HTML preview
exists because this machine has no PowerPoint, Keynote or LibreOffice -- it is
how the layout gets eyeballed before the .pptx ships.

Coordinates are inches on a 13.333 x 7.5 canvas. Font sizes are points.
"""

W, H = 13.333, 7.5
M = 0.85  # side margin

# Palette: pulled from the product UI so the deck and the demo look related.
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

SERIF = "Cambria"
SANS = "Calibri"


def rect(x, y, w, h, fill, radius=0.0, line=None):
    return {"t": "rect", "x": x, "y": y, "w": w, "h": h, "fill": fill,
            "radius": radius, "line": line}


def text(x, y, w, h, body, size=15, color=INK, font=SANS, bold=False,
         italic=False, align="l", spacing=1.18, space_after=0):
    """`body` is a string, or a list of (string, {overrides}) run tuples."""
    return {"t": "text", "x": x, "y": y, "w": w, "h": h, "body": body,
            "size": size, "color": color, "font": font, "bold": bold,
            "italic": italic, "align": align, "spacing": spacing,
            "space_after": space_after}


def arrow(x, y, w, color=MOSS):
    return {"t": "arrow", "x": x, "y": y, "w": w, "color": color}


AUTHOR = "Seyfullah Ural"
DATE = "September 2026"


# --------------------------------------------------------------------------
# Slide 1 - Thesis
# --------------------------------------------------------------------------
S1 = {
    "bg": GREEN_DEEP,
    "notes": (
        "The whole deck hangs off one sentence. Every design decision that "
        "follows is downstream of refusing to let the model be the authority on "
        "facts, permissions, or money."
    ),
    "el": [
        text(M, 1.05, 8.0, 0.3, "BOOKLY  ·  SOLUTIONS ENGINEERING TAKE-HOME",
             size=12, color=MOSS, bold=True, font=SANS),
        text(M, 1.72, 11.2, 2.5,
             "The model should never\ndecide what's true.",
             size=52, color=WHITE, font=SERIF, bold=True, spacing=1.06),
        rect(M, 4.42, 1.5, 0.035, MOSS),
        text(M, 4.84, 9.9, 1.15,
             "A customer support agent for Bookly, built so that language "
             "understanding and business authority are deliberately different "
             "parts of the system.",
             size=17, color=SOFT, spacing=1.32),
        text(M, 6.55, 6.0, 0.32, f"{AUTHOR}   ·   {DATE}",
             size=12.5, color=MUTED_DARK),
        text(7.0, 6.55, 5.48, 0.32, "Python  ·  Anthropic API  ·  no agent framework",
             size=12.5, color=MUTED_DARK, align="r"),
    ],
}


# --------------------------------------------------------------------------
# Slide 2 - Architecture
# --------------------------------------------------------------------------
_BOXW, _BOXH, _BOXY = 2.62, 1.62, 2.62
_GAP = 0.42
_X0 = M


def _pipe(i):
    return _X0 + i * (_BOXW + _GAP)


S2 = {
    "bg": CREAM,
    "notes": (
        "Walk left to right. The one thing to land: the tool layer is where the "
        "guardrails live, and policy.py is ordinary Python with no model in it. "
        "Memory is split -- the transcript is the model's, the verified facts are "
        "the application's."
    ),
    "el": [
        text(M, 0.72, 10.5, 0.62, "How a question becomes an answer",
             size=35, color=INK, font=SERIF, bold=True),
        text(M, 1.44, 11.3, 0.4,
             "Four components, and only the first one is probabilistic.",
             size=16, color=MUTED),

        # Pipeline boxes
        rect(_pipe(0), _BOXY, _BOXW, _BOXH, WHITE, 0.09, line="DEDDD8"),
        text(_pipe(0) + 0.24, _BOXY + 0.22, _BOXW - 0.48, 0.3, "PROMPTS",
             size=11, color=MOSS, bold=True),
        text(_pipe(0) + 0.24, _BOXY + 0.58, _BOXW - 0.48, 0.34, "System prompt",
             size=16.5, color=INK, bold=True),
        text(_pipe(0) + 0.24, _BOXY + 0.95, _BOXW - 0.48, 0.6,
             "Tone and judgement only.\nNo business rules.", size=12.5, color=MUTED,
             spacing=1.25),

        rect(_pipe(1), _BOXY, _BOXW, _BOXH, GREEN, 0.09),
        text(_pipe(1) + 0.24, _BOXY + 0.22, _BOXW - 0.48, 0.3, "ORCHESTRATION",
             size=11, color=MOSS, bold=True),
        text(_pipe(1) + 0.24, _BOXY + 0.58, _BOXW - 0.48, 0.34, "Agent loop",
             size=16.5, color=WHITE, bold=True),
        text(_pipe(1) + 0.24, _BOXY + 0.95, _BOXW - 0.48, 0.6,
             "Hand-written, ~60 lines.\nIteration cap, full trace.",
             size=12.5, color=SOFT, spacing=1.25),

        rect(_pipe(2), _BOXY, _BOXW, _BOXH, WHITE, 0.09, line="DEDDD8"),
        text(_pipe(2) + 0.24, _BOXY + 0.22, _BOXW - 0.48, 0.3, "TOOLS",
             size=11, color=MOSS, bold=True),
        text(_pipe(2) + 0.24, _BOXY + 0.58, _BOXW - 0.48, 0.34, "Tool layer",
             size=16.5, color=INK, bold=True),
        text(_pipe(2) + 0.24, _BOXY + 0.95, _BOXW - 0.48, 0.6,
             "Identity checks and refund\npreconditions live here.",
             size=12.5, color=MUTED, spacing=1.25),

        rect(_pipe(3), _BOXY, _BOXW, _BOXH, WHITE, 0.09, line="DEDDD8"),
        text(_pipe(3) + 0.24, _BOXY + 0.22, _BOXW - 0.48, 0.3, "MEMORY",
             size=11, color=MOSS, bold=True),
        text(_pipe(3) + 0.24, _BOXY + 0.58, _BOXW - 0.48, 0.34, "Split state",
             size=16.5, color=INK, bold=True),
        text(_pipe(3) + 0.24, _BOXY + 0.95, _BOXW - 0.48, 0.6,
             "Transcript for the model.\nVerified facts for the app.",
             size=12.5, color=MUTED, spacing=1.25),

        arrow(_pipe(0) + _BOXW + 0.10, _BOXY + _BOXH / 2, _GAP - 0.20),
        arrow(_pipe(1) + _BOXW + 0.10, _BOXY + _BOXH / 2, _GAP - 0.20),
        arrow(_pipe(2) + _BOXW + 0.10, _BOXY + _BOXH / 2, _GAP - 0.20),

        # Callout
        rect(M, 4.90, 11.63, 1.42, SOFT, 0.09),
        text(M + 0.34, 5.12, 3.5, 0.32, "THE LOAD-BEARING PART",
             size=11, color=GREEN, bold=True),
        text(M + 0.34, 5.50, 10.95, 0.72,
             [("check_return_eligibility", {"font": "Courier New", "bold": True, "color": GREEN}),
              (" is ordinary Python. No model, no prompt, no temperature. It is the "
               "only authority on whether something can be returned — and the agent "
               "is not permitted to contradict it.", {})],
             size=15, color=INK, spacing=1.3),

        text(M, 6.62, 11.63, 0.42,
             [("The core knows nothing about HTTP. ", {"bold": True}),
              ("The web chat and the CLI are both thin adapters over one run_turn(). "
               "A voice channel would be a sibling of those files, not a rewrite of "
               "anything underneath.", {})],
             size=13, color=MUTED),
    ],
}


# --------------------------------------------------------------------------
# Slide 3 - Key decisions
# --------------------------------------------------------------------------
_CW = (W - 2 * M - 2 * 0.40) / 3
_CY = 2.18
_CH = 4.80

_DECISIONS = [
    ("01", "Eligibility is code,\nnot a prompt",
     "Refund rules live in policy.py and run as plain Python.",
     "Every policy change is a deploy, not a prompt edit.",
     "It becomes auditable and unit-testable. There is no prompt to jailbreak, "
     "and no temperature at which 45 becomes less than 30."),
    ("02", "The write tool has\npreconditions",
     "issue_refund refuses unless identity was verified, eligibility passed, "
     "and the customer said yes.",
     "More code than a line of prompt instruction.",
     "\"Always confirm first\" is a suggestion. This is a precondition. The model "
     "is now allowed to be wrong without the customer paying for it."),
    ("03", "Required arguments\ngenerate the dialogue",
     "lookup_order cannot be called without both an order id and an email.",
     "Less freedom in how the agent phrases its way there.",
     "Nobody wrote a script for collecting them. The schema makes a half-informed "
     "call impossible, so the agent asks. Flow control by type signature."),
]

_el3 = [
    text(M, 0.72, 10.5, 0.62, "Three decisions worth defending",
         size=35, color=INK, font=SERIF, bold=True),
    text(M, 1.44, 11.3, 0.4,
         "Each one moves authority out of the model and into code.",
         size=16, color=MUTED),
]
for i, (num, title, what, traded, bought) in enumerate(_DECISIONS):
    cx = M + i * (_CW + 0.40)
    _el3 += [
        rect(cx, _CY, _CW, _CH, WHITE, 0.09, line="DEDDD8"),
        text(cx + 0.30, _CY + 0.22, 1.0, 0.42, num,
             size=25, color=MOSS, font=SERIF, bold=True),
        text(cx + 0.30, _CY + 0.68, _CW - 0.60, 0.78, title,
             size=19, color=INK, font=SERIF, bold=True, spacing=1.14),
        text(cx + 0.30, _CY + 1.60, _CW - 0.60, 0.78, what,
             size=13, color=INK, spacing=1.26),
        text(cx + 0.30, _CY + 2.56, _CW - 0.60, 0.24, "TRADED AWAY",
             size=9.5, color=CLAY, bold=True),
        text(cx + 0.30, _CY + 2.84, _CW - 0.60, 0.48, traded,
             size=12, color=MUTED, spacing=1.24),
        text(cx + 0.30, _CY + 3.54, _CW - 0.60, 0.24, "WORTH IT BECAUSE",
             size=9.5, color=GREEN, bold=True),
        text(cx + 0.30, _CY + 3.82, _CW - 0.60, 0.95, bought,
             size=12, color=MUTED, spacing=1.24),
    ]

S3 = {
    "bg": CREAM,
    "notes": (
        "Do not read the cards. Pick decision 2 and tell the story: the customer "
        "who insists, the model that wants to please, and the four unit tests that "
        "make it not matter."
    ),
    "el": _el3,
}


# --------------------------------------------------------------------------
# Slide 4 - Proof
# --------------------------------------------------------------------------
S4 = {
    "bg": CREAM,
    "notes": (
        "The brain-swap is the strongest evidence in the deck. Delete the API key "
        "and a dumb rule-based planner drives the same tools -- every guardrail "
        "still holds, because none of them were ever in the prompt."
    ),
    "el": [
        text(M, 0.72, 10.5, 0.62, "Where the architecture shows up",
             size=35, color=INK, font=SERIF, bold=True),
        text(M, 1.44, 11.3, 0.4,
             "Three moments from the demo, and one experiment.",
             size=16, color=MUTED),

        # Refusal moment
        rect(M, 2.22, 5.62, 1.62, CLAY_SOFT, 0.09),
        text(M + 0.32, 2.44, 4.98, 0.28, "IT SAYS NO, AND MEANS IT",
             size=11, color=CLAY, bold=True),
        text(M + 0.32, 2.78, 4.98, 0.92,
             "A refund request on an order delivered 45 days ago. The agent "
             "checks, refuses, explains why, and offers a human. It cannot be "
             "argued out of the number 30.",
             size=13.5, color=INK, spacing=1.28),

        # Clarifying moment
        rect(M + 5.62 + 0.39, 2.22, 5.62, 1.62, WHITE, 0.09, line="DEDDD8"),
        text(M + 5.62 + 0.71, 2.44, 4.98, 0.28, "IT ASKS INSTEAD OF GUESSING",
             size=11, color=GREEN, bold=True),
        text(M + 5.62 + 0.71, 2.78, 4.98, 0.92,
             "\"I want to return my book\" on an order containing two books. It "
             "names both and asks which — rather than picking one and being "
             "wrong half the time.",
             size=13.5, color=INK, spacing=1.28),

        # The experiment
        rect(M, 4.16, 11.63, 2.16, GREEN, 0.09),
        text(M + 0.34, 4.42, 6.0, 0.3, "THE EXPERIMENT WORTH RUNNING",
             size=11, color=MOSS, bold=True),
        text(M + 0.34, 4.78, 11.0, 1.32,
             "Delete the API key and the agent falls back to a scripted, rule-based "
             "planner. It is far worse at understanding English — and every single "
             "guardrail still holds. Identity is still checked, the 30-day rule "
             "still bites, refunds still need confirmation.\n"
             "Because none of that was ever in the prompt.",
             size=16, color=WHITE, spacing=1.34),

        text(M, 6.62, 11.63, 0.52,
             [("13 unit tests cover the policy engine and the refund gate — including four ways a persuasive customer might talk the model into a refund it must not make.", {"italic": True})],
             size=12.5, color=MUTED),
    ],
}


# --------------------------------------------------------------------------
# Slide 5 - What I'd change
# --------------------------------------------------------------------------
_NEXT = [
    ("Build the eval set", "The policy half is tested. The model half is not measured at all — did it pick the right tool, did it ask when it should have asked, did it stay grounded? Without that, the next prompt change is a guess."),
    ("Persist the session", "State is in-process today. A real deployment needs it in Redis or Postgres, keyed by conversation, so a dropped connection is not a lost customer."),
    ("Instrument cost and latency per turn", "Support economics are per-contact. If you cannot see what a resolution costs, you cannot argue for the deflection rate."),
    ("Add tone regression tests", "An LLM-as-judge over recorded transcripts, so a prompt tweak that makes the agent subtly colder gets caught before a customer feels it."),
]

_el5 = [
    text(M, 0.72, 10.5, 0.62, "What I'd do differently",
         size=35, color=INK, font=SERIF, bold=True),
    text(M, 1.44, 11.3, 0.4,
         "In order. The first one is not close.",
         size=16, color=MUTED),
]
_ry = 2.24
for i, (title, body) in enumerate(_NEXT):
    first = i == 0
    _el5 += [
        rect(M, _ry, 11.63, 0.94, SOFT if first else WHITE, 0.07,
             line=None if first else "DEDDD8"),
        text(M + 0.30, _ry + 0.20, 0.5, 0.34, str(i + 1),
             size=17, color=MOSS if not first else GREEN, font=SERIF, bold=True),
        text(M + 0.82, _ry + 0.15, 3.35, 0.58, title,
             size=16.5, color=INK, bold=True, font=SERIF),
        text(M + 4.28, _ry + 0.15, 7.05, 0.66, body,
             size=12.5, color=MUTED, spacing=1.24),
    ]
    _ry += 1.06

_el5.append(
    text(M, 6.72, 11.63, 0.52,
         [("The thesis is falsifiable: ", {"bold": True}),
          ("if the guardrails were really in the architecture and not the prompt, "
           "swapping the model out shouldn't change what the system permits. It doesn't.", {})],
         size=13.5, color=GREEN)
)

S5 = {"bg": CREAM,
      "notes": "Close on the eval point -- it is the answer that separates people who have shipped an agent from people who have demoed one.",
      "el": _el5}


SLIDES = [S1, S2, S3, S4, S5]
