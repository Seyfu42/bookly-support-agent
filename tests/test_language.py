"""Tests for the language switch.

The switch is a tool, not a prompt instruction, for the same reason the refund
gate is: the model asks, the application decides. These tests pin down that the
application really is the one deciding -- and that nothing about switching
language can reach the policy engine.
"""

import pytest

from bookly import config, store
from bookly.session import Session, get_session
from bookly.tools import execute_tool


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "lang.db")
    store.init()
    yield


def test_english_is_the_default():
    assert config.DEFAULT_LANGUAGE == "en"
    assert Session().language == "en"


def test_agent_can_switch_to_german():
    s = Session()
    result = execute_tool("set_language", {"language": "de"}, s)
    assert result["success"] is True
    assert result["previous"] == "en"
    assert s.language == "de"


def test_agent_can_switch_back():
    s = Session()
    execute_tool("set_language", {"language": "de"}, s)
    execute_tool("set_language", {"language": "en"}, s)
    assert s.language == "en"


def test_unsupported_language_is_refused_and_changes_nothing():
    """The model may ask for French. It does not get French."""
    s = Session()
    result = execute_tool("set_language", {"language": "fr"}, s)
    assert result["success"] is False
    assert "not supported" in result["error"]
    assert s.language == "en"


def test_switch_survives_a_restart():
    s = Session()
    execute_tool("set_language", {"language": "de"}, s)
    s.persist()
    assert get_session(s.session_id).language == "de"


def test_switching_language_cannot_change_a_verdict():
    """The point of the whole feature: wording moves, decisions don't."""
    verdicts = []
    for target in ("en", "de"):
        s = Session()
        execute_tool("set_language", {"language": target}, s)
        r = execute_tool("check_return_eligibility", {"order_id": "BK-1002", "sku": None}, s)
        verdicts.append((s.language, r["eligible"], r["reason_code"]))

    assert verdicts[0] == ("en", False, "OUTSIDE_RETURN_WINDOW")
    assert verdicts[1] == ("de", False, "OUTSIDE_RETURN_WINDOW")


def test_help_centre_answers_in_the_conversation_language():
    s = Session()
    en = execute_tool("search_help_center", {"query": "shipping"}, s)
    execute_tool("set_language", {"language": "de"}, s)
    de = execute_tool("search_help_center", {"query": "versand"}, s)

    assert en["results"][0]["id"] == de["results"][0]["id"] == "HC-SHIPPING-03"
    assert en["results"][0]["body"] != de["results"][0]["body"]
    assert "Werktage" in de["results"][0]["body"]
