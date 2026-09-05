import copy
import json

import pytest

from config import WIKI_QUERY_MAX_TOKENS
from config import WIKI_QUERY_MAX_TOOL_ITERATIONS
from config import WIKI_QUERY_MODEL
from modules.common.schemas import ServiceStatus
from modules.fundamentals.repositories import JsonFundamentalsReadRepository
from modules.wiki.exceptions import WikiAgentError
from modules.wiki.exceptions import WikiAuthError
from modules.wiki.exceptions import WikiConnectionError
from modules.wiki.exceptions import WikiRateLimitError
from modules.wiki.models import WikiAgentEvent
from modules.wiki.models import WikiAgentEventType
from modules.wiki.models import WikiChatMessage
from modules.wiki.models import WikiErrorCategory
from modules.wiki.models import WikiQueryRequest
from modules.wiki.models import WikiStreamEventType
from modules.wiki.models import WikiToolUse
from modules.wiki.repositories import FileSystemWikiIndexReadRepository
from modules.wiki.repositories import FileSystemWikiPageReadRepository
from modules.wiki.repositories import FileSystemWikiSchemaReadRepository
from modules.wiki.services import WikiQueryService


# --- Fake agent repository (the seam ESJ-25 tests through) -----------------

class _FakeAgentRepository:
    """Replays scripted WikiAgentEvent lists, one list per model turn."""

    def __init__(self, turns):
        """Store one scripted event list per expected retrieve_data call."""
        self._turns = [list(turn) for turn in turns]
        self.calls: list[dict] = []

    def retrieve_data(self, *, system, messages, tools, model, max_tokens):
        """Record the request and yield the next scripted turn's events."""
        self.calls.append({
            "system": system,
            "messages": copy.deepcopy(messages),
            "tools": tools,
            "model": model,
            "max_tokens": max_tokens,
        })
        if not self._turns:
            raise AssertionError("agent repository called more times than scripted")
        yield from self._turns.pop(0)


class _RaisingAgentRepository:
    """Raises a scripted exception when its turn is consumed."""

    def __init__(self, exc):
        """Store the exception to raise on iteration."""
        self._exc = exc
        self.calls: list[dict] = []

    def retrieve_data(self, **kwargs):
        """Record the call, then raise (generator body, deferred to iteration)."""
        self.calls.append(kwargs)
        raise self._exc
        yield  # pragma: no cover - makes this a generator


def _text_delta(text):
    """Build a TEXT_DELTA agent event."""
    return WikiAgentEvent(type=WikiAgentEventType.TEXT_DELTA, text=text)


def _turn_end(text):
    """Build a TURN_COMPLETE agent event that ends the turn with text."""
    return WikiAgentEvent(type=WikiAgentEventType.TURN_COMPLETE, text=text, stop_reason="end_turn")


def _turn_tool_use(*tool_uses):
    """Build a TURN_COMPLETE agent event whose stop_reason is 'tool_use'."""
    return WikiAgentEvent(
        type=WikiAgentEventType.TURN_COMPLETE,
        text="",
        stop_reason="tool_use",
        tool_uses=list(tool_uses),
    )


def _tool_use(block_id, name, **tool_input):
    """Build a WikiToolUse with the given id, name and input kwargs."""
    return WikiToolUse(id=block_id, name=name, input=tool_input)


@pytest.fixture
def make_service():
    """Return a factory that wires WikiQueryService with real content repos."""
    def _make(agent_repository):
        return WikiQueryService(
            agent_repository=agent_repository,
            index_repository=FileSystemWikiIndexReadRepository(),
            page_repository=FileSystemWikiPageReadRepository(),
            schema_repository=FileSystemWikiSchemaReadRepository(),
            fundamentals_repository=JsonFundamentalsReadRepository(),
        )
    return _make


def _request(**overrides):
    """Build a WikiQueryRequest with sensible defaults for tests."""
    kwargs = {"ticker": "DANHOS13", "question": "¿por qué subió el apalancamiento?"}
    kwargs.update(overrides)
    return WikiQueryRequest(**kwargs)


# --- Happy path -------------------------------------------------------------

def test_run_ok_extracts_citations(make_service):
    """A single end_turn answer is returned with its wikilinks as citations."""
    agent = _FakeAgentRepository([[
        _text_delta("Según [[2024-Q1]] "),
        _text_delta("el apalancamiento subió."),
        _turn_end("Según [[2024-Q1]] el apalancamiento subió."),
    ]])

    result = make_service(agent).run(request=_request())

    assert result.status == ServiceStatus.OK
    assert result.data.answer_text == "Según [[2024-Q1]] el apalancamiento subió."
    assert result.data.citations == ["2024-Q1"]


def test_stream_event_sequence_text_status_text_final(make_service):
    """stream() yields TEXT deltas, a STATUS before tool dispatch, then FINAL."""
    agent = _FakeAgentRepository([
        [_text_delta("Voy a revisar. "), _turn_tool_use(_tool_use("t1", "read_index", ticker="DANHOS13"))],
        [_text_delta("Según [[2024-Q1]]."), _turn_end("Según [[2024-Q1]].")],
    ])

    events = list(make_service(agent).stream(request=_request()))

    assert [event.type for event in events] == [
        WikiStreamEventType.TEXT,
        WikiStreamEventType.STATUS,
        WikiStreamEventType.TEXT,
        WikiStreamEventType.FINAL,
    ]
    assert events[1].text == "Consultando la wiki…"
    assert events[-1].data.citations == ["2024-Q1"]


# --- Request assembly ------------------------------------------------------

def test_request_is_assembled_with_cache_breakpoints_and_live_schema(make_service):
    """system is a cached block holding shell + live SCHEMA.md; last tool is cached."""
    agent = _FakeAgentRepository([[_turn_end("hola")]])

    make_service(agent).run(request=_request())

    call = agent.calls[0]
    assert isinstance(call["system"], list)
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "Operación: Query" in call["system"][0]["text"]
    assert "DANHOS13" in call["system"][0]["text"]
    assert call["tools"][-1]["cache_control"] == {"type": "ephemeral"}
    assert call["model"] == WIKI_QUERY_MODEL
    assert call["max_tokens"] == WIKI_QUERY_MAX_TOKENS


def test_history_is_collapsed_to_text_turns(make_service):
    """Prior turns become plain user/assistant text dicts before the new question."""
    agent = _FakeAgentRepository([[_turn_end("respuesta")]])
    request = _request(
        question="¿y la ocupación?",
        history=[
            WikiChatMessage(role="user", content="¿por qué subió el LTV?"),
            WikiChatMessage(role="assistant", content="Subió por nueva deuda."),
        ],
    )

    make_service(agent).run(request=request)

    assert agent.calls[0]["messages"] == [
        {"role": "user", "content": "¿por qué subió el LTV?"},
        {"role": "assistant", "content": "Subió por nueva deuda."},
        {"role": "user", "content": "¿y la ocupación?"},
    ]


def test_dangling_history_turn_is_dropped(make_service):
    """An incomplete trailing user turn is dropped (all-or-nothing per pair)."""
    agent = _FakeAgentRepository([[_turn_end("respuesta")]])
    request = _request(
        question="pregunta nueva",
        history=[
            WikiChatMessage(role="user", content="q1"),
            WikiChatMessage(role="assistant", content="a1"),
            WikiChatMessage(role="user", content="q2 sin respuesta"),
        ],
    )

    make_service(agent).run(request=request)

    assert agent.calls[0]["messages"] == [
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "pregunta nueva"},
    ]


# --- Tool dispatch -------------------------------------------------------------

def test_tool_use_dispatches_read_index_and_feeds_result_back(make_service):
    """A read_index call is dispatched; the next turn carries the real index.md."""
    agent = _FakeAgentRepository([
        [_turn_tool_use(_tool_use("t1", "read_index", ticker="DANHOS13"))],
        [_turn_end("Listo.")],
    ])

    result = make_service(agent).run(request=_request())

    assert result.status == ServiceStatus.OK
    second_call_messages = agent.calls[1]["messages"]
    assistant_block = second_call_messages[-2]
    assert assistant_block["role"] == "assistant"
    assert assistant_block["content"][0] == {
        "type": "tool_use", "id": "t1", "name": "read_index", "input": {"ticker": "DANHOS13"},
    }
    tool_result = second_call_messages[-1]["content"][0]
    assert tool_result["type"] == "tool_result"
    assert tool_result["tool_use_id"] == "t1"
    assert tool_result["is_error"] is False
    assert "## Trimestres" in tool_result["content"]


def test_tool_call_with_foreign_ticker_is_rejected_and_loop_continues(make_service):
    """A tool call for another FIBRA returns is_error without reading anything."""
    agent = _FakeAgentRepository([
        [_turn_tool_use(_tool_use("t1", "read_index", ticker="FMTY14"))],
        [_turn_end("ok")],
    ])

    result = make_service(agent).run(request=_request(ticker="DANHOS13"))

    assert result.status == ServiceStatus.OK
    tool_result = agent.calls[1]["messages"][-1]["content"][0]
    assert tool_result["is_error"] is True
    assert "DANHOS13" in tool_result["content"]
    assert "## Trimestres" not in tool_result["content"]


def test_read_fundamentals_dispatch_returns_filtered_json(make_service):
    """read_fundamentals returns the ticker/period-filtered records as JSON."""
    agent = _FakeAgentRepository([
        [_turn_tool_use(_tool_use("t1", "read_fundamentals", ticker="DANHOS13", period="1T2024"))],
        [_turn_end("ok")],
    ])

    make_service(agent).run(request=_request())

    tool_result = agent.calls[1]["messages"][-1]["content"][0]
    assert tool_result["is_error"] is False
    payload = json.loads(tool_result["content"])
    assert payload
    assert all(record["ticker"] == "DANHOS13" and record["period"] == "1T2024" for record in payload)


def test_read_page_miss_returns_is_error_with_valid_names(make_service):
    """An unknown page name yields an is_error result listing the valid names."""
    agent = _FakeAgentRepository([
        [_turn_tool_use(_tool_use("t1", "read_page", ticker="DANHOS13", page_name="2099-Q9"))],
        [_turn_end("ok")],
    ])

    make_service(agent).run(request=_request())

    tool_result = agent.calls[1]["messages"][-1]["content"][0]
    assert tool_result["is_error"] is True
    assert "2024-Q1" in tool_result["content"]


# --- Terminal errors ------------------------------------------------------

def test_iteration_cap_without_answer_yields_incomplete(make_service):
    """Exhausting the tool-iteration cap ends with ERROR / INCOMPLETE."""
    turns = [
        [_turn_tool_use(_tool_use(f"t{index}", "read_index", ticker="DANHOS13"))]
        for index in range(WIKI_QUERY_MAX_TOOL_ITERATIONS)
    ]
    agent = _FakeAgentRepository(turns)

    events = list(make_service(agent).stream(request=_request()))

    assert events[-1].type == WikiStreamEventType.ERROR
    assert events[-1].error_category == WikiErrorCategory.INCOMPLETE


def test_end_turn_without_text_yields_incomplete(make_service):
    """An end_turn with only whitespace text is treated as INCOMPLETE, not FINAL."""
    agent = _FakeAgentRepository([[_turn_end("   ")]])

    events = list(make_service(agent).stream(request=_request()))

    assert events[-1].type == WikiStreamEventType.ERROR
    assert events[-1].error_category == WikiErrorCategory.INCOMPLETE


@pytest.mark.parametrize(
    "raised, expected",
    [
        pytest.param(WikiAuthError("sin key"), WikiErrorCategory.AUTH, id="auth"),
        pytest.param(WikiRateLimitError("despacio"), WikiErrorCategory.RATE_LIMIT, id="rate_limit"),
        pytest.param(WikiConnectionError("caído"), WikiErrorCategory.CONNECTION, id="connection"),
        pytest.param(WikiAgentError("raro"), WikiErrorCategory.INTERNAL, id="agent_error"),
        pytest.param(RuntimeError("boom"), WikiErrorCategory.INTERNAL, id="unexpected"),
    ],
)
def test_exceptions_become_terminal_error_events(make_service, raised, expected):
    """Every failure from the agent port is mapped to a terminal ERROR event."""
    agent = _RaisingAgentRepository(raised)

    events = list(make_service(agent).stream(request=_request()))

    assert len(events) == 1
    assert events[0].type == WikiStreamEventType.ERROR
    assert events[0].error_category == expected


def test_run_maps_terminal_error_event_to_error_schema(make_service):
    """run() turns a terminal ERROR event into an ERROR schema with the message."""
    agent = _RaisingAgentRepository(WikiConnectionError("timeout contra la API"))

    result = make_service(agent).run(request=_request())

    assert result.status == ServiceStatus.ERROR
    assert "timeout contra la API" in result.error_message
