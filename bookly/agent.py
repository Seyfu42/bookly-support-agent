"""The agent loop.

Written by hand rather than with a framework. The assignment asks to see the
orchestration, and there is a real argument for it beyond that: this loop is
~60 lines, and every one of them is a place where a support agent needs a
policy hook -- iteration caps, tool gating, trace emission, error surfacing.
Frameworks put those behind a callback API. Here they are just code.

The loop is a generator so callers can render each step as it happens. The web
UI streams these events straight into the trace panel, which turns the agent
from a black box into something a customer-experience lead can audit.
"""

import json
from collections.abc import Iterator

import anthropic

from bookly import config
from bookly.prompts import SYSTEM_PROMPT
from bookly.session import Session
from bookly.tools import TOOL_SCHEMAS, execute_tool

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.API_KEY)
    return _client


def _call_model(session: Session):
    return _get_client().messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=SYSTEM_PROMPT,
        tools=TOOL_SCHEMAS,
        messages=session.messages,
        # Thinking runs adaptively by default on Opus 5. Effort is turned down
        # from the default "high" because support turns are shallow reasoning
        # over fresh tool output, and latency is part of the customer experience.
        output_config={"effort": config.EFFORT},
    )


def _text_of(response) -> str:
    return "\n".join(b.text for b in response.content if b.type == "text").strip()


def run_turn(session: Session, user_text: str) -> Iterator[dict]:
    """Run one user turn to completion, yielding observable events."""
    session.turn_count += 1
    session.messages.append({"role": "user", "content": user_text})

    if config.MOCK_MODE:
        from bookly.mock_llm import run_turn_mock

        yield from run_turn_mock(session, user_text)
        return

    for iteration in range(config.MAX_TOOL_ITERATIONS):
        try:
            response = _call_model(session)
        except anthropic.AuthenticationError:
            yield {
                "type": "error",
                "message": (
                    "Anthropic rejected the API key. Check ANTHROPIC_API_KEY in .env, "
                    "or delete it to run in mock mode."
                ),
            }
            return
        except anthropic.RateLimitError:
            yield {"type": "error", "message": "Rate limited by the API. Try again in a moment."}
            return
        except anthropic.APIStatusError as exc:
            yield {"type": "error", "message": f"API error {exc.status_code}: {exc.message}"}
            return
        except anthropic.APIConnectionError:
            yield {"type": "error", "message": "Could not reach the Anthropic API. Check your connection."}
            return

        session.messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            reply = _text_of(response) or "Sorry, I lost my train of thought there. Could you say that again?"
            session.log("assistant", reply)
            yield {"type": "reply", "text": reply}
            return

        # The model may narrate before acting; show that text so the customer
        # is not staring at a silent screen while tools run.
        if preamble := _text_of(response):
            yield {"type": "partial", "text": preamble}

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            args = block.input if isinstance(block.input, dict) else json.loads(block.input)
            yield {"type": "tool_call", "name": block.name, "args": args}
            session.log("tool_call", block.name, args)

            result = execute_tool(block.name, args, session)
            yield {"type": "tool_result", "name": block.name, "result": result}
            session.log("tool_result", block.name, result)

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                    "is_error": bool(result.get("error")),
                }
            )

        # All results from one assistant turn go back in a single user message.
        session.messages.append({"role": "user", "content": tool_results})

    yield {
        "type": "error",
        "message": (
            f"Stopped after {config.MAX_TOOL_ITERATIONS} tool calls without a final "
            "answer. Escalating would be the right move here."
        ),
    }


def reply_to(session: Session, user_text: str) -> str:
    """Convenience wrapper for callers that only want the final text."""
    text = ""
    for event in run_turn(session, user_text):
        if event["type"] in ("reply", "error"):
            text = event.get("text") or event.get("message", "")
    return text
