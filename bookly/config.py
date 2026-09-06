"""Runtime configuration, resolved once at import."""

import os

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Opus 5 is the default. Swap to claude-sonnet-5 for ~2.5x cheaper, snappier turns.
MODEL = os.getenv("BOOKLY_MODEL", "claude-opus-5")

# Support chat is latency-sensitive and the reasoning here is shallow (pick a tool,
# read a result, phrase a reply), so "high" (the API default) buys nothing but wall time.
EFFORT = os.getenv("BOOKLY_EFFORT", "medium")

MAX_TOKENS = 4096

# Safety valve: a runaway tool loop is the classic way an agent burns a customer's
# patience and your API budget. Real turns here use 1-3 tool calls.
MAX_TOOL_ITERATIONS = 8

# True when we have no API key and fall back to the scripted planner.
MOCK_MODE = not API_KEY
