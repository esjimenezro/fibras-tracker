from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from modules.wiki.exceptions import WikiAgentError
from modules.wiki.exceptions import WikiAuthError
from modules.wiki.exceptions import WikiConnectionError
from modules.wiki.exceptions import WikiRateLimitError
from modules.wiki.models import WikiAgentEventType
from modules.wiki.models import WikiToolUse
from modules.wiki.repositories import AnthropicWikiAgentReadRepository


# --- Fakes standing in for the anthropic streaming client -------------------

class _FakeStream:
    """Iterable stand-in for anthropic's MessageStream."""

    def __init__(self, events, final_message, request_id):
        """Store the scripted events, final message and request id to replay."""
        self._events = events
        self._final_message = final_message
        self.request_id = request_id
        self.closed = False

    def __iter__(self):
        """Yield the scripted stream events in order."""
        return iter(self._events)

    def get_final_message(self):
        """Return the scripted accumulated message."""
        return self._final_message

    def close(self):
        """Record that the stream was closed (context-manager exit)."""
        self.closed = True


class _FakeStreamManager:
    """Context manager stand-in for the object returned by ``messages.stream()``."""

    def __init__(self, stream, raise_on_enter):
        """Hold the stream to hand out, or the exception to raise on entry."""
        self._stream = stream
        self._raise_on_enter = raise_on_enter

    def __enter__(self):
        """Raise the scripted error, or return the fake stream."""
        if self._raise_on_enter is not None:
            raise self._raise_on_enter
        return self._stream

    def __exit__(self, *_exc):
        """Close the stream on exit, mirroring the real manager."""
        if self._stream is not None:
            self._stream.close()
        return False


class _FakeMessages:
    """Stand-in for ``client.messages`` that records the stream() kwargs."""

    def __init__(self, manager, calls):
        """Hold the manager to return and the list that records call kwargs."""
        self._manager = manager
        self._calls = calls

    def stream(self, **kwargs):
        """Record the request kwargs and return the fake stream manager."""
        self._calls.append(kwargs)
        return self._manager


class _FakeAnthropic:
    """Stand-in for ``anthropic.Anthropic()``."""

    def __init__(self, api_key, manager, calls):
        """Expose api_key and a messages object wired to the fake manager."""
        self.api_key = api_key
        self.messages = _FakeMessages(manager, calls)


def _install_fake_anthropic(monkeypatch, *, events=None, final_message=None,
                            request_id="req-abc123", api_key="sk-ant-test",
                            raise_on_enter=None):
    """Patch ``anthropic.Anthropic`` with a fake and return (calls, stream).

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        events: Scripted stream events (objects with ``.type`` / ``.text``).
        final_message: Object returned by ``stream.get_final_message()``.
        request_id: Value exposed as ``stream.request_id``.
        api_key: Value exposed as ``client.api_key``.
        raise_on_enter: Exception raised when the ``with`` block is entered.

    Returns:
        tuple: (list recording each ``stream()`` kwargs dict, the _FakeStream).
    """
    stream = _FakeStream(events or [], final_message, request_id)
    manager = _FakeStreamManager(stream, raise_on_enter)
    calls: list[dict] = []
    monkeypatch.setattr(
        anthropic,
        "Anthropic",
        lambda *_a, **_kw: _FakeAnthropic(api_key, manager, calls),
    )
    return calls, stream


def _text_event(text):
    """Build a fake 'text' delta stream event."""
    return SimpleNamespace(type="text", text=text)


def _text_block(text):
    """Build a fake assistant text content block."""
    return SimpleNamespace(type="text", text=text)


def _tool_use_block(block_id, name, tool_input):
    """Build a fake assistant tool_use content block."""
    return SimpleNamespace(type="tool_use", id=block_id, name=name, input=tool_input)


def _final_message(content, stop_reason, *, input_tokens=100, output_tokens=20,
                   cache_read_input_tokens=0):
    """Build a fake accumulated message with a usage record."""
    usage = SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=cache_read_input_tokens,
    )
    return SimpleNamespace(content=content, stop_reason=stop_reason, usage=usage)


_REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def _status_error(cls, status):
    """Build an anthropic APIStatusError subclass instance for tests."""
    return cls("boom", response=httpx2.Response(status, request=_REQUEST), body=None)


@pytest.fixture
def repo():
    """Return an AnthropicWikiAgentReadRepository instance."""
    return AnthropicWikiAgentReadRepository()


# --- Construction ----------------------------------------------------------

def test_construction_never_builds_the_client(repo):
    """Instantiation does not build anthropic.Anthropic() (deferred to retrieve_data)."""
    assert isinstance(repo, AnthropicWikiAgentReadRepository)


# --- Success path --------------------------------------------------------------

def test_streams_text_deltas_then_one_turn_complete(monkeypatch, repo):
    """Each 'text' event becomes a TEXT_DELTA; the turn ends with one TURN_COMPLETE."""
    _install_fake_anthropic(
        monkeypatch,
        events=[_text_event("Hola"), SimpleNamespace(type="content_block_stop"), _text_event(" mundo")],
        final_message=_final_message([_text_block("Hola mundo")], "end_turn",
                                     input_tokens=42, output_tokens=3, cache_read_input_tokens=11),
        request_id="req-xyz",
    )

    events = list(repo.retrieve_data(system="s", messages=[{"role": "user", "content": "hi"}],
                                     tools=[], model="claude-haiku-4-5", max_tokens=64))

    kinds = [event.type for event in events]
    assert kinds == [
        WikiAgentEventType.TEXT_DELTA,
        WikiAgentEventType.TEXT_DELTA,
        WikiAgentEventType.TURN_COMPLETE,
    ]
    assert [event.text for event in events[:2]] == ["Hola", " mundo"]

    final = events[-1]
    assert final.text == "Hola mundo"
    assert final.stop_reason == "end_turn"
    assert final.tool_uses == []
    assert final.request_id == "req-xyz"
    assert final.usage == {"input_tokens": 42, "output_tokens": 3, "cache_read_input_tokens": 11}


def test_turn_complete_carries_tool_uses(monkeypatch, repo):
    """A tool_use content block is normalized into a WikiToolUse on TURN_COMPLETE."""
    _install_fake_anthropic(
        monkeypatch,
        events=[],
        final_message=_final_message(
            [_tool_use_block("toolu_1", "read_index", {"ticker": "danhos13"})],
            "tool_use",
        ),
    )

    events = list(repo.retrieve_data(system="s", messages=[], tools=[],
                                     model="claude-haiku-4-5", max_tokens=64))

    final = events[-1]
    assert final.type == WikiAgentEventType.TURN_COMPLETE
    assert final.stop_reason == "tool_use"
    assert final.text == ""
    assert final.tool_uses == [
        WikiToolUse(id="toolu_1", name="read_index", input={"ticker": "danhos13"})
    ]


def test_none_cache_read_tokens_coerced_to_zero(monkeypatch, repo):
    """A null cache_read_input_tokens from the SDK is reported as 0."""
    _install_fake_anthropic(
        monkeypatch,
        events=[_text_event("x")],
        final_message=_final_message([_text_block("x")], "end_turn", cache_read_input_tokens=None),
    )

    final = list(repo.retrieve_data(system="s", messages=[], tools=[],
                                    model="m", max_tokens=8))[-1]

    assert final.usage["cache_read_input_tokens"] == 0


def test_forwards_request_arguments_verbatim_to_stream(monkeypatch, repo):
    """system, messages, tools, model and max_tokens are passed straight through."""
    calls, _ = _install_fake_anthropic(
        monkeypatch,
        events=[],
        final_message=_final_message([_text_block("")], "end_turn"),
    )
    messages = [{"role": "user", "content": "q"}]
    tools = [{"name": "read_index", "description": "d", "input_schema": {"type": "object"}}]

    list(repo.retrieve_data(system="SYS", messages=messages, tools=tools,
                            model="claude-haiku-4-5", max_tokens=123))

    assert calls == [{
        "model": "claude-haiku-4-5",
        "max_tokens": 123,
        "system": "SYS",
        "messages": messages,
        "tools": tools,
    }]


# --- Credential guard --------------------------------------------------------

@pytest.mark.parametrize("api_key", [None, ""])
def test_missing_api_key_raises_wiki_auth_error(monkeypatch, repo, api_key):
    """A missing/blank ANTHROPIC_API_KEY fails as WikiAuthError before any request."""
    calls, _ = _install_fake_anthropic(monkeypatch, api_key=api_key)

    with pytest.raises(WikiAuthError):
        list(repo.retrieve_data(system="s", messages=[], tools=[], model="m", max_tokens=8))

    assert calls == []


# --- Exception mapping ------------------------------------------------------

@pytest.mark.parametrize(
    "raised, expected",
    [
        pytest.param(_status_error(anthropic.AuthenticationError, 401), WikiAuthError, id="auth"),
        pytest.param(_status_error(anthropic.RateLimitError, 429), WikiRateLimitError, id="rate_limit"),
        pytest.param(anthropic.APIConnectionError(message="down", request=_REQUEST),
                     WikiConnectionError, id="connection"),
        pytest.param(anthropic.APITimeoutError(_REQUEST), WikiConnectionError, id="timeout"),
        pytest.param(_status_error(anthropic.BadRequestError, 400), WikiAgentError, id="bad_request"),
        pytest.param(anthropic.AnthropicError("weird"), WikiAgentError, id="other_anthropic_error"),
    ],
)
def test_maps_anthropic_errors_to_domain_errors(monkeypatch, repo, raised, expected):
    """Every anthropic failure surfaces as its mapped domain exception, chained."""
    _install_fake_anthropic(monkeypatch, raise_on_enter=raised)

    with pytest.raises(expected) as exc_info:
        list(repo.retrieve_data(system="s", messages=[], tools=[], model="m", max_tokens=8))

    assert exc_info.value.__cause__ is raised


# --- Cleanup on abandonment -------------------------------------------------

def test_abandoned_generator_closes_the_stream(monkeypatch, repo):
    """Closing the generator mid-turn runs the `with` exit and releases the stream."""
    _, stream = _install_fake_anthropic(
        monkeypatch,
        events=[_text_event("a"), _text_event("b")],
        final_message=_final_message([_text_block("ab")], "end_turn"),
    )

    generator = repo.retrieve_data(system="s", messages=[], tools=[], model="m", max_tokens=8)
    next(generator)
    assert stream.closed is False

    generator.close()

    assert stream.closed is True
