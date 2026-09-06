import pytest

from config import WIKI_QUERY_MAX_TOOL_RESULT_CHARS
from modules.wiki.models import WikiAgentEvent
from modules.wiki.models import WikiAgentEventType
from modules.wiki.models import WikiChatMessage
from modules.wiki.models import WikiQueryRequest
from modules.wiki.models import WikiToolUse
from modules.wiki.processors import WikiMessageProcessor


@pytest.fixture
def processor():
    """Return a WikiMessageProcessor instance."""
    return WikiMessageProcessor()


def _request(question="pregunta nueva", history=None):
    """Build a WikiQueryRequest for the message-processor tests."""
    return WikiQueryRequest(ticker="DANHOS13", question=question, history=history or [])


# --- initial_messages --------------------------------------------------------

def test_initial_messages_without_history_is_just_the_question(processor):
    """With no history the result is a single user turn with the question."""
    assert processor.initial_messages(request=_request(question="¿y la ocupación?")) == [
        {"role": "user", "content": "¿y la ocupación?"},
    ]


def test_initial_messages_collapses_history_pairs(processor):
    """Each (user, assistant) history pair becomes two plain text turns."""
    request = _request(
        question="q3",
        history=[
            WikiChatMessage(role="user", content="q1"),
            WikiChatMessage(role="assistant", content="a1"),
            WikiChatMessage(role="user", content="q2"),
            WikiChatMessage(role="assistant", content="a2"),
        ],
    )

    assert processor.initial_messages(request=request) == [
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "q2"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "q3"},
    ]


def test_initial_messages_drops_a_dangling_history_turn(processor):
    """An unpaired trailing turn is dropped (all-or-nothing per pair)."""
    request = _request(
        history=[
            WikiChatMessage(role="user", content="q1"),
            WikiChatMessage(role="assistant", content="a1"),
            WikiChatMessage(role="user", content="q2 sin respuesta"),
        ],
    )

    assert processor.initial_messages(request=request) == [
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "pregunta nueva"},
    ]


# --- assistant_content -----------------------------------------------------

def test_assistant_content_with_text_and_tool_uses(processor):
    """A text preamble plus each tool_use are rebuilt as content blocks in order."""
    turn = WikiAgentEvent(
        type=WikiAgentEventType.TURN_COMPLETE,
        text="Voy a revisar.",
        stop_reason="tool_use",
        tool_uses=[
            WikiToolUse(id="t1", name="read_index", input={"ticker": "DANHOS13"}),
            WikiToolUse(id="t2", name="read_page", input={"ticker": "DANHOS13", "page_name": "2024-Q1"}),
        ],
    )

    assert processor.assistant_content(turn=turn) == [
        {"type": "text", "text": "Voy a revisar."},
        {"type": "tool_use", "id": "t1", "name": "read_index", "input": {"ticker": "DANHOS13"}},
        {"type": "tool_use", "id": "t2", "name": "read_page",
         "input": {"ticker": "DANHOS13", "page_name": "2024-Q1"}},
    ]


def test_assistant_content_omits_empty_text_block(processor):
    """A pure tool-use turn (no text) yields only tool_use blocks."""
    turn = WikiAgentEvent(
        type=WikiAgentEventType.TURN_COMPLETE,
        text="",
        stop_reason="tool_use",
        tool_uses=[WikiToolUse(id="t1", name="read_index", input={"ticker": "DANHOS13"})],
    )

    assert processor.assistant_content(turn=turn) == [
        {"type": "tool_use", "id": "t1", "name": "read_index", "input": {"ticker": "DANHOS13"}},
    ]


# --- tool_result ----------------------------------------------------------

def test_tool_result_passes_short_content_through(processor):
    """Content under the cap is returned unchanged with the is_error flag."""
    assert processor.tool_result(tool_use_id="t1", content="hola", is_error=False) == {
        "type": "tool_result",
        "tool_use_id": "t1",
        "content": "hola",
        "is_error": False,
    }


def test_tool_result_truncates_oversized_content(processor):
    """Content over the cap is truncated and marked."""
    payload = "x" * (WIKI_QUERY_MAX_TOOL_RESULT_CHARS + 500)

    result = processor.tool_result(tool_use_id="t1", content=payload, is_error=False)

    assert result["content"].startswith("x" * WIKI_QUERY_MAX_TOOL_RESULT_CHARS)
    assert result["content"].endswith("[contenido truncado]")
    assert len(result["content"]) < len(payload)


def test_tool_result_keeps_is_error_true(processor):
    """The is_error flag is propagated."""
    assert processor.tool_result(tool_use_id="t1", content="falló", is_error=True)["is_error"] is True
