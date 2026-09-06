"""Terminal chat with the Bookly agent.

    uv run cli.py

Shows the tool trace inline so you can watch the agent work.
"""

import sys

from bookly import config
from bookly.agent import run_turn
from bookly.session import Session

DIM, CYAN, GREEN, YELLOW, RESET = "\033[2m", "\033[36m", "\033[32m", "\033[33m", "\033[0m"


def main() -> None:
    session = Session()
    mode = "mock mode (no API key)" if config.MOCK_MODE else f"live · {config.MODEL}"
    print(f"{CYAN}Bookly Support{RESET} {DIM}— {mode}{RESET}")
    print(f"{DIM}Try: “where is my order?” · “I want to return a book” · Ctrl-C to quit{RESET}\n")

    while True:
        try:
            user = input(f"{GREEN}you ›{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return
        if not user:
            continue
        if user in {"/quit", "/exit"}:
            return

        for event in run_turn(session, user):
            kind = event["type"]
            if kind == "tool_call":
                print(f"  {DIM}→ {event['name']}({event['args']}){RESET}")
            elif kind == "tool_result":
                preview = str(event["result"])
                if len(preview) > 160:
                    preview = preview[:157] + "…"
                print(f"  {DIM}← {preview}{RESET}")
            elif kind in ("reply", "partial"):
                print(f"{CYAN}bookly ›{RESET} {event['text']}")
            elif kind == "error":
                print(f"{YELLOW}!{RESET} {event['message']}", file=sys.stderr)
        print()


if __name__ == "__main__":
    main()
