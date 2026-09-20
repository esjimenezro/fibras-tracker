import json
from collections.abc import Iterator
from typing import Optional

from config import WIKI_QUERY_MAX_TOKENS
from config import WIKI_QUERY_MAX_TOOL_ITERATIONS
from config import WIKI_QUERY_MODEL
from modules.common.repositories import JsonCatalogReadRepository
from modules.common.repositories.base import BaseCatalogReadRepository
from modules.common.schemas import ServiceStatus
from modules.fundamentals.repositories import JsonFundamentalsReadRepository
from modules.fundamentals.repositories.base import BaseFundamentalsReadRepository
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
from modules.wiki.processors import WikiRosterProcessor
from modules.wiki.repositories.base import BaseWikiAgentReadRepository
from modules.wiki.repositories.base import BaseWikiCatalogReadRepository
from modules.wiki.repositories.base import BaseWikiIndexReadRepository
from modules.wiki.repositories.base import BaseWikiPageReadRepository
from modules.wiki.repositories.base import BaseWikiSchemaReadRepository
from modules.wiki.repositories import AnthropicWikiAgentReadRepository
from modules.wiki.repositories import FileSystemWikiCatalogReadRepository
from modules.wiki.repositories import FileSystemWikiIndexReadRepository
from modules.wiki.repositories import FileSystemWikiPageReadRepository
from modules.wiki.repositories import FileSystemWikiSchemaReadRepository
from modules.wiki.schemas import WikiQueryServiceSchema
from modules.wiki.services._wiki_query_prompt import FOCUS_COMPARISON_TEMPLATE
from modules.wiki.services._wiki_query_prompt import FOCUS_PRIMARY_TEMPLATE
from modules.wiki.services._wiki_query_prompt import INSTRUCTIONS_HEADER
from modules.wiki.services._wiki_query_prompt import INSTRUCTIONS_TOOLS
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
        agent_repository: Optional[BaseWikiAgentReadRepository] = None,
        index_repository: Optional[BaseWikiIndexReadRepository] = None,
        page_repository: Optional[BaseWikiPageReadRepository] = None,
        schema_repository: Optional[BaseWikiSchemaReadRepository] = None,
        fundamentals_repository: Optional[BaseFundamentalsReadRepository] = None,
        catalog_repository: Optional[BaseCatalogReadRepository] = None,
        wiki_catalog_repository: Optional[BaseWikiCatalogReadRepository] = None,
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
            catalog_repository: FIBRA catalog reader, used by read_wiki_catalog.
                Defaults to JsonCatalogReadRepository.
            wiki_catalog_repository: Wiki ticker roster reader, used by
                read_wiki_catalog. Defaults to FileSystemWikiCatalogReadRepository.
        """
        self._agent_repository = agent_repository or AnthropicWikiAgentReadRepository()
        self._index_repository = index_repository or FileSystemWikiIndexReadRepository()
        self._page_repository = page_repository or FileSystemWikiPageReadRepository()
        self._schema_repository = schema_repository or FileSystemWikiSchemaReadRepository()
        self._fundamentals_repository = fundamentals_repository or JsonFundamentalsReadRepository()
        self._catalog_repository = catalog_repository or JsonCatalogReadRepository()
        self._wiki_catalog_repository = wiki_catalog_repository or FileSystemWikiCatalogReadRepository()
        self._citation_processor = CitationProcessor()
        self._fundamentals_filter = FundamentalsQueryFilterProcessor()
        self._message_processor = WikiMessageProcessor()
        self._roster_processor = WikiRosterProcessor()

    def run(self, request: WikiQueryRequest) -> WikiQueryServiceSchema:
        """Drain stream() and map its single terminal event to the output schema.

        Args:
            request: The wiki query (an allowed FIBRA scope, one question plus history).

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
        ERROR / INCOMPLETE. An empty ``request.tickers`` is a caller bug (there is
        no scope to answer within) and also yields ERROR / INTERNAL, rather than
        assembling a prompt with nothing in scope.

        Args:
            request: The wiki query (an allowed FIBRA scope, one question plus history).

        Returns:
            Iterator[WikiStreamEvent]: The event stream described above. Never
                raises; failures become a terminal ERROR event.
        """
        try:
            if not request.tickers:
                raise ValueError("WikiQueryRequest.tickers must not be empty")
            tickers_label = ", ".join(request.tickers)
            focus = (
                FOCUS_PRIMARY_TEMPLATE.format(primary_ticker=request.primary_ticker, tickers=tickers_label)
                if request.primary_ticker
                else FOCUS_COMPARISON_TEMPLATE.format(tickers=tickers_label)
            )
            system = [{
                "type": "text",
                "text": INSTRUCTIONS_HEADER + focus + INSTRUCTIONS_TOOLS + self._schema_repository.retrieve_data(),
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
                    if self._has_foreign_ticker(turn=turn, allowed_tickers=request.tickers):
                        yield self._fixed_answer_event(OUT_OF_SCOPE_MESSAGE.format(tickers=tickers_label))
                        return
                    messages.append({
                        "role": "assistant",
                        "content": self._message_processor.assistant_content(turn=turn),
                    })
                    yield WikiStreamEvent(type=WikiStreamEventType.STATUS, text=STATUS_CONSULTING)
                    results = [self._dispatch(tool_use=tool_use) for tool_use in turn.tool_uses]
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
                    yield self._fixed_answer_event(UNGROUNDED_MESSAGE.format(tickers=tickers_label))
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

    def _has_foreign_ticker(self, turn: WikiAgentEvent, allowed_tickers: list[str]) -> bool:
        """Report whether any tool call in the turn targets a ticker outside the allowed scope.

        Args:
            turn: The TURN_COMPLETE event whose stop_reason was "tool_use".
            allowed_tickers: The FIBRA tickers this query may read from.

        Returns:
            bool: True if at least one tool_use both carries a ``ticker`` argument
                and that argument matches none of ``allowed_tickers``
                (case-insensitive). A tool_use with no ``ticker`` argument never
                counts as foreign.
        """
        allowed = {ticker.casefold() for ticker in allowed_tickers}
        return any(
            "ticker" in tool_use.input and str(tool_use.input["ticker"]).casefold() not in allowed
            for tool_use in turn.tool_uses
        )

    def _dispatch(self, tool_use: WikiToolUse) -> dict:
        """Execute one (already scope-approved) tool call and return its tool_result.

        A bad tool call (missing arg, unknown page, cross-FIBRA name) becomes an
        ``is_error`` result rather than raising.

        Args:
            tool_use: The requested tool call (id, name, input), already validated
                to target a ticker within the request's allowed scope.

        Returns:
            dict: An Anthropic ``tool_result`` block for ``tool_use.id``.
        """
        try:
            content = self._run_tool(tool_use=tool_use)
            return self._message_processor.tool_result(
                tool_use_id=tool_use.id, content=content, is_error=False,
            )
        except (FileNotFoundError, ValueError, KeyError) as exc:
            return self._message_processor.tool_result(
                tool_use_id=tool_use.id, content=str(exc), is_error=True,
            )

    def _run_tool(self, tool_use: WikiToolUse) -> str:
        """Route a tool call to its repository/processor and return the raw payload.

        Args:
            tool_use: The requested tool call. Its own ``ticker`` input (not a
                service-wide default) selects which FIBRA's data is read, since a
                multi-ticker query can dispatch different tickers per call.
                ``read_wiki_catalog`` takes no ``ticker`` at all.

        Returns:
            str: The raw tool payload (wiki markdown, roster text, or
                fundamentals as JSON).

        Raises:
            FileNotFoundError: If a wiki page or index is missing.
            ValueError: If the page name is malformed, the tool name is unknown,
                or a required string argument (``ticker``, ``page_name``,
                ``period``) is present but not a non-blank string.
            KeyError: If a required tool argument is absent.
        """
        if tool_use.name == "read_wiki_catalog":
            return self._roster_processor.process(
                fibras=self._catalog_repository.retrieve_data(),
                wiki_tickers=self._wiki_catalog_repository.retrieve_data(),
            )
        ticker = self._require_str(tool_use=tool_use, key="ticker")
        if tool_use.name == "read_index":
            return self._index_repository.retrieve_data(ticker=ticker.lower())
        if tool_use.name == "read_page":
            return self._page_repository.retrieve_data(
                ticker=ticker.lower(),
                page_name=self._require_str(tool_use=tool_use, key="page_name"),
            )
        if tool_use.name == "read_fundamentals":
            period = tool_use.input.get("period")
            records = self._fundamentals_filter.process(
                records=self._fundamentals_repository.retrieve_data(),
                ticker=ticker.upper(),
                period=self._require_str(tool_use=tool_use, key="period") if period is not None else None,
            )
            return json.dumps(
                [record.model_dump(mode="json") for record in records],
                ensure_ascii=False,
                indent=2,
            )
        raise ValueError(f"Tool desconocida: {tool_use.name}")

    def _require_str(self, tool_use: WikiToolUse, key: str) -> str:
        """Read and type-check a required string argument from a tool call.

        Model-supplied tool input is an untyped dict (``WikiToolUse.input:
        dict``); nothing upstream guarantees a given key is a string before it
        reaches ``.lower()``/``.upper()`` or an equality filter. Centralizing the
        check here turns a malformed argument into a ``ValueError`` — caught by
        ``_dispatch``'s narrow except clause into a per-call ``is_error`` tool
        result — instead of an uncaught ``AttributeError`` that would abort the
        whole query via ``stream()``'s outer catch-all.

        Args:
            tool_use: The tool call being validated.
            key: The input key expected to hold a non-empty string.

        Returns:
            str: The validated argument value.

        Raises:
            KeyError: If key is absent from tool_use.input.
            ValueError: If the value is present but not a non-blank string.
        """
        value = tool_use.input[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key!r} debe ser un string no vacío en la llamada a {tool_use.name}")
        return value

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
