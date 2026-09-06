"""FastAPI wrapper around the agent.

    uv run uvicorn web.app:app --reload

The agent core knows nothing about HTTP. This file is a channel adapter, and it
is deliberately thin -- a voice or SMS front end would be a sibling of this file,
not a rewrite of anything underneath it.
"""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from bookly import config, store
from bookly.agent import run_turn
from bookly.session import get_session

app = FastAPI(title="Bookly Support Agent")
STATIC = Path(__file__).parent / "static"


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    language: str | None = None


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/config")
def get_config() -> dict:
    return {
        "mock_mode": config.MOCK_MODE,
        "model": None if config.MOCK_MODE else config.MODEL,
        "storage": store.stats(),
        "default_language": config.DEFAULT_LANGUAGE,
        "languages": list(config.SUPPORTED_LANGUAGES),
    }


@app.get("/api/session/{session_id}")
def get_session_transcript(session_id: str) -> dict:
    """Rehydrate a conversation after a reload, a crash, or a new device.

    Returns what the customer saw, not the model's transcript -- tool calls and
    thinking blocks are not theirs to read.
    """
    payload = store.load(session_id)
    if payload is None:
        return {"found": False, "transcript": [], "trace": []}
    return {
        "found": True,
        "session_id": session_id,
        "transcript": payload.get("transcript", []),
        "trace": payload.get("trace", []),
        "turn_count": payload.get("turn_count", 0),
    }


@app.post("/api/chat")
def chat(req: ChatRequest) -> StreamingResponse:
    """Stream agent events as server-sent events so the trace panel fills live."""
    session = get_session(req.session_id)
    if req.language in config.SUPPORTED_LANGUAGES:
        session.language = req.language

    def stream():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session.session_id})}\n\n"
        for event in run_turn(session, req.message):
            yield f"data: {json.dumps(event, default=str)}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
