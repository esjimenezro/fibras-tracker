import json
from collections.abc import Iterator
from typing import Optional

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
from modules.wiki.models import WikiErrorCategory
from modules.wiki.models import WikiQueryRequest
from modules.wiki.models import WikiQueryResponse
from modules.wiki.models import WikiStreamEvent
from modules.wiki.models import WikiStreamEventType
from modules.wiki.models import WikiToolUse
from modules.wiki.processors import CitationProcessor
from modules.wiki.processors import FundamentalsQueryFilterProcessor
from modules.wiki.processors import WikiMessageProcessor
from modules.wiki.repositories import AnthropicWikiAgentReadRepository
from modules.wiki.repositories import FileSystemWikiIndexReadRepository
from modules.wiki.repositories import FileSystemWikiPageReadRepository
from modules.wiki.repositories import FileSystemWikiSchemaReadRepository
from modules.wiki.schemas import WikiQueryServiceSchema
from modules.wiki.services._wiki_query_prompt import INSTRUCTIONS_SHELL
from modules.wiki.services._wiki_query_prompt import OUT_OF_SCOPE_MESSAGE
from modules.wiki.services._wiki_query_prompt import STATUS_CONSULTING
from modules.wiki.services._wiki_query_prompt import TOOL_SCHEMAS
from modules.wiki.services._wiki_query_prompt import UNGROUNDED_MESSAGE


_ERROR_CATEGORY_BY_EXCEPTION = {
    WikiAuthError: WikiErrorCategory.AUTH,
    WikiRateLimitError: WikiErrorCategory.RATE_LIMIT,
    WikiConnectionError: WikiErrorCategory.CONNECTION,
    WikiAgentError: WikiErrorCategory.INTERNAL,
}


class WikiQueryService:
    """Orchestrates the agentic wiki query: tool loop, dispatch and error taxonomy.

    Transformation: WikiQueryRequest ──▶ stream of WikiStreamEvent (token text,
    status notes, one terminal FINAL or ERROR).

    The single external boundary is BaseWikiAgentReadRepository (one call = one
    model turn); this service owns the loop across turns, the tool dispatch table,
    ticker-scope enforcement, tool-result truncation, citation extraction and the
    mapping of domain exceptions to terminal ERROR events. It never raises: every
    failure is surfaced as a terminal ERROR event.

    Two guards do not trust the model's judgement:
        * a tool call for a different FIBRA aborts the query with a fixed reply;
        * an answer produced without a single successful in-scope tool call is
          replaced with a fixed "could not ground this" reply.
    """

    def __init__(
        self,
        agent_repository=None,
        index_repository=None,
        page_repository=None,
        schema_repository=None,
        fundamentals_repository=None,
    ):
        """Wire the service, defaulting each repository to its concrete implementation.

        Args:
            agent_repository: One-turn LLM agent port. Defaults to
                AnthropicWikiAgentReadRepository.
            index_repository: Wiki index reader. Defaults to
                FileSystemWikiIndexReadRepository.
            page_repository: Wiki page reader. Defaults to
                FileSystemWikiPageReadRepository.
            schema_repository: Wiki SCHEMA.md reader. Defaults to
                FileSystemWikiSchemaReadRepository.
            fundamentals_repository: Raw fundamentals reader. Defaults to
                JsonFundamentalsReadRepository.
        """
        self._agent_repository = agent_repository or AnthropicWikiAgentReadRepository()
        self._index_repository = index_repository or FileSystemWikiIndexReadRepository()
        self._page_repository = page_repository or FileSystemWikiPageReadRepository()
        self._schema_repository = schema_repository or FileSystemWikiSchemaReadRepository()
        self._fundamentals_repository = fundamentals_repository or JsonFundamentalsReadRepository()
        self._citation_processor = CitationProcessor()
        self._fundamentals_filter = FundamentalsQueryFilterProcessor()
        self._message_processor = WikiMessageProcessor()

    def run(self, request: WikiQueryRequest) -> WikiQueryServiceSchema:
        """Drain stream() and map its single terminal event to the output schema.

        Args:
            request: The wiki query (one FIBRA, one question plus history).

        Returns:
            WikiQueryServiceSchema: status OK with the enriched WikiQueryResponse
                on success, or status ERROR with error_message otherwise. Never
                raises.
        """
        terminal: Optional[WikiStreamEvent] = None
        for event in self.stream(request=request):
            if event.type in (WikiStreamEventType.FINAL, WikiStreamEventType.ERROR):
                terminal = event

        if terminal is None:
            return WikiQueryServiceSchema(
                status=ServiceStatus.ERROR,
                error_message="La consulta no produjo un evento terminal.",
            )
        if terminal.type == WikiStreamEventType.FINAL:
            return WikiQueryServiceSchema(status=ServiceStatus.OK, data=terminal.data)
        return WikiQueryServiceSchema(status=ServiceStatus.ERROR, error_message=terminal.error_message)

    def stream(self, request: WikiQueryRequest) -> Iterator[WikiStreamEvent]:
        """Run the agentic loop for one query, yielding UI-ready stream events.

        Emits a TEXT event per streamed answer chunk and a STATUS event before
        each round of tool calls, then exactly one terminal event: FINAL carrying
        the enriched WikiQueryResponse, or ERROR carrying an error_category. The
        request is assembled as ``tools → system → messages`` with a
        ``cache_control`` breakpoint on the stable prefix; ``system`` is the
        instruction shell plus the live SCHEMA.md. The tool loop is capped at
        WIKI_QUERY_MAX_TOOL_ITERATIONS.

        A FINAL is also emitted, carrying a fixed reply, when the model calls a
        tool for a different FIBRA or answers without a successful in-scope tool
        call. Exhausting the cap, or a final turn with no text, yields
        ERROR / INCOMPLETE.

        Args:
            request: The wiki query (one FIBRA, one question plus history).

        Returns:
            Iterator[WikiStreamEvent]: The event stream described above. Never
                raises; failures become a terminal ERROR event.
        """
        try:
            system = [{
                "type": "text",
                "text": INSTRUCTIONS_SHELL.format(ticker=request.ticker) + self._schema_repository.retrieve_data(),
                "cache_control": {"type": "ephemeral"},
            }]
            messages = self._message_processor.initial_messages(request=request)
            grounded = False

            for _ in range(WIKI_QUERY_MAX_TOOL_ITERATIONS):
                turn = None
                for event in self._agent_repository.retrieve_data(
                    system=system,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    model=WIKI_QUERY_MODEL,
                    max_tokens=WIKI_QUERY_MAX_TOKENS,
                ):
                    if event.type == WikiAgentEventType.TEXT_DELTA:
                        yield WikiStreamEvent(type=WikiStreamEventType.TEXT, text=event.text)
                    elif event.type == WikiAgentEventType.TURN_COMPLETE:
                        turn = event

                if turn is not None and turn.stop_reason == "tool_use":
                    if self._has_foreign_ticker(turn=turn, request_ticker=request.ticker):
                        yield self._fixed_answer_event(OUT_OF_SCOPE_MESSAGE.format(ticker=request.ticker))
                        return
                    messages.append({
                        "role": "assistant",
                        "content": self._message_processor.assistant_content(turn=turn),
                    })
                    yield WikiStreamEvent(type=WikiStreamEventType.STATUS, text=STATUS_CONSULTING)
                    results = [
                        self._dispatch(tool_use=tool_use, request_ticker=request.ticker)
                        for tool_use in turn.tool_uses
                    ]
                    if any(not result["is_error"] for result in results):
                        grounded = True
                    messages.append({"role": "user", "content": results})
                    continue

                answer_text = (turn.text or "").strip() if turn is not None else ""
                if not answer_text:
                    yield self._error_event(
                        category=WikiErrorCategory.INCOMPLETE,
                        message="El modelo terminó el turno sin texto de respuesta.",
                    )
                    return
                if not grounded:
                    yield self._fixed_answer_event(UNGROUNDED_MESSAGE.format(ticker=request.ticker))
                    return
                citations = self._citation_processor.process(answer_text=answer_text)
                yield WikiStreamEvent(
                    type=WikiStreamEventType.FINAL,
                    data=WikiQueryResponse(answer_text=answer_text, citations=citations),
                )
                return

            yield self._error_event(
                category=WikiErrorCategory.INCOMPLETE,
                message="Se alcanzó el límite de iteraciones de tools sin una respuesta final.",
            )
        except (WikiAuthError, WikiRateLimitError, WikiConnectionError, WikiAgentError) as exc:
            yield self._error_event(
                category=_ERROR_CATEGORY_BY_EXCEPTION[type(exc)],
                message=str(exc),
            )
        except Exception as exc:
            yield self._error_event(category=WikiErrorCategory.INTERNAL, message=str(exc))

    def _has_foreign_ticker(self, turn: WikiAgentEvent, request_ticker: str) -> bool:
        """Report whether any tool call in the turn targets a different FIBRA.

        Args:
            turn: The TURN_COMPLETE event whose stop_reason was "tool_use".
            request_ticker: The FIBRA ticker this query is scoped to.

        Returns:
            bool: True if at least one tool_use has a non-matching ``ticker``
                argument (compared case-insensitively).
        """
        return any(
            str(tool_use.input.get("ticker", "")).casefold() != request_ticker.casefold()
            for tool_use in turn.tool_uses
        )

    def _dispatch(self, tool_use: WikiToolUse, request_ticker: str) -> dict:
        """Execute one (already scope-approved) tool call and return its tool_result.

        A bad tool call (missing arg, unknown page, cross-FIBRA name) becomes an
        ``is_error`` result rather than raising.

        Args:
            tool_use: The requested tool call (id, name, input).
            request_ticker: The FIBRA ticker this query is scoped to.

        Returns:
            dict: An Anthropic ``tool_result`` block for ``tool_use.id``.
        """
        try:
            content = self._run_tool(tool_use=tool_use, request_ticker=request_ticker)
            return self._message_processor.tool_result(
                tool_use_id=tool_use.id, content=content, is_error=False,
            )
        except (FileNotFoundError, ValueError, KeyError) as exc:
            return self._message_processor.tool_result(
                tool_use_id=tool_use.id, content=str(exc), is_error=True,
            )

    def _run_tool(self, tool_use: WikiToolUse, request_ticker: str) -> str:
        """Route a tool call to its repository/processor and return the raw payload.

        Args:
            tool_use: The requested tool call.
            request_ticker: The FIBRA ticker this query is scoped to.

        Returns:
            str: The raw tool payload (wiki markdown, or fundamentals as JSON).

        Raises:
            FileNotFoundError: If a wiki page or index is missing.
            ValueError: If the page name is malformed, or the tool name is unknown.
            KeyError: If a required tool argument is absent.
        """
        if tool_use.name == "read_index":
            return self._index_repository.retrieve_data(ticker=request_ticker.lower())
        if tool_use.name == "read_page":
            return self._page_repository.retrieve_data(
                ticker=request_ticker.lower(),
                page_name=tool_use.input["page_name"],
            )
        if tool_use.name == "read_fundamentals":
            records = self._fundamentals_filter.process(
                records=self._fundamentals_repository.retrieve_data(),
                ticker=request_ticker.upper(),
                period=tool_use.input.get("period"),
            )
            return json.dumps(
                [record.model_dump(mode="json") for record in records],
                ensure_ascii=False,
                indent=2,
            )
        raise ValueError(f"Tool desconocida: {tool_use.name}")

    def _fixed_answer_event(self, text: str) -> WikiStreamEvent:
        """Build a terminal FINAL event carrying a fixed (canned) reply.

        Args:
            text: The fixed reply to return as the answer.

        Returns:
            WikiStreamEvent: A FINAL event with no citations.
        """
        return WikiStreamEvent(
            type=WikiStreamEventType.FINAL,
            data=WikiQueryResponse(answer_text=text, citations=[]),
        )

    def _error_event(self, category: WikiErrorCategory, message: str) -> WikiStreamEvent:
        """Build a terminal ERROR stream event.

        Args:
            category: The failure category driving the UI banner.
            message: Human-readable failure detail.

        Returns:
            WikiStreamEvent: An ERROR event.
        """
        return WikiStreamEvent(
            type=WikiStreamEventType.ERROR,
            error_category=category,
            error_message=message,
        )
