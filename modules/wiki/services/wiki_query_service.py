import json
from collections.abc import Iterator
from typing import Optional

from config import WIKI_QUERY_MAX_TOKENS
from config import WIKI_QUERY_MAX_TOOL_ITERATIONS
from config import WIKI_QUERY_MAX_TOOL_RESULT_CHARS
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
from modules.wiki.repositories import AnthropicWikiAgentReadRepository
from modules.wiki.repositories import FileSystemWikiIndexReadRepository
from modules.wiki.repositories import FileSystemWikiPageReadRepository
from modules.wiki.repositories import FileSystemWikiSchemaReadRepository
from modules.wiki.schemas import WikiQueryServiceSchema


_READ_INDEX_DESCRIPTION = (
    "Devuelve el índice de navegación (index.md) de la wiki de la FIBRA: la lista "
    "de páginas de trimestre y de concepto con un resumen de una línea de cada una. "
    "Úsalo primero para ubicar las páginas relevantes antes de leerlas."
)

_READ_PAGE_DESCRIPTION = (
    "Devuelve el contenido completo de una página de la wiki de la FIBRA. page_name "
    "es un nombre estilo wikilink: una página de trimestre (\"2024-Q1\") o de concepto "
    "(\"plan-crecimiento\"), con o sin corchetes [[ ]] y con o sin sufijo .md. "
    "No se admiten referencias a otras FIBRAs (nombres con \"/\")."
)

_READ_FUNDAMENTALS_DESCRIPTION = (
    "Devuelve las cifras crudas de fundamentals.json para la FIBRA (NOI, AFFO, LTV, "
    "ocupación, CBFIs, deuda, etc.) como JSON, una entrada por período. period es "
    "opcional; si se da, filtra a ese período exacto en formato \"1T2026\". Usa esta "
    "tool cuando necesites un número exacto en vez de una cifra parafraseada en la wiki."
)

_INSTRUCTIONS_SHELL = (
    "Eres un asistente que responde preguntas sobre UNA FIBRA mexicana usando su "
    "wiki de contexto narrativo y sus cifras de fundamentals.json.\n\n"
    "La FIBRA de esta consulta es {ticker}. Responde solo sobre {ticker}: si la "
    "pregunta es sobre otra FIBRA, dilo y no llames a las tools con otro ticker.\n\n"
    "Tienes tres tools de solo lectura:\n"
    "- read_index(ticker): el índice de navegación de la wiki de la FIBRA.\n"
    "- read_page(ticker, page_name): una página de trimestre (p. ej. \"2024-Q1\") o "
    "de concepto (p. ej. \"plan-crecimiento\").\n"
    "- read_fundamentals(ticker, period?): las cifras crudas para la FIBRA, "
    "opcionalmente filtradas por período (formato \"1T2026\").\n\n"
    "Flujo: primero read_index para ubicar páginas candidatas; luego read_page para "
    "leerlas; usa read_fundamentals cuando necesites una cifra exacta. No inventes "
    "datos que no estén en la wiki o en fundamentals.\n\n"
    "Cita cada afirmación con el wikilink de la página de la que proviene, con el "
    "formato [[nombre-de-pagina]] (p. ej. \"según [[2024-Q1]], ...\"). Responde en "
    "español y de forma concisa.\n\n"
    "A continuación están las reglas que gobiernan la wiki (wiki/SCHEMA.md); síguelas "
    "para la Operación: Query.\n\n---\n\n"
)

_TOOL_SCHEMAS: list[dict] = [
    {
        "name": "read_index",
        "description": _READ_INDEX_DESCRIPTION,
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Ticker de la FIBRA de esta consulta."},
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "read_page",
        "description": _READ_PAGE_DESCRIPTION,
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Ticker de la FIBRA de esta consulta."},
                "page_name": {"type": "string", "description": "Nombre de página estilo wikilink."},
            },
            "required": ["ticker", "page_name"],
        },
    },
    {
        "name": "read_fundamentals",
        "description": _READ_FUNDAMENTALS_DESCRIPTION,
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Ticker de la FIBRA de esta consulta."},
                "period": {"type": "string", "description": "Período exacto, formato \"1T2026\". Opcional."},
            },
            "required": ["ticker"],
        },
        "cache_control": {"type": "ephemeral"},
    },
]

_STATUS_CONSULTING = "Consultando la wiki…"

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
        WIKI_QUERY_MAX_TOOL_ITERATIONS; exhausting it without a final answer
        yields ERROR / INCOMPLETE.

        Args:
            request: The wiki query (one FIBRA, one question plus history).

        Returns:
            Iterator[WikiStreamEvent]: The event stream described above. Never
                raises; failures become a terminal ERROR event.
        """
        try:
            system = [{
                "type": "text",
                "text": _INSTRUCTIONS_SHELL.format(ticker=request.ticker) + self._schema_repository.retrieve_data(),
                "cache_control": {"type": "ephemeral"},
            }]
            messages = self._initial_messages(request=request)

            for _iteration in range(WIKI_QUERY_MAX_TOOL_ITERATIONS):
                turn = None
                text_parts: list[str] = []
                for event in self._agent_repository.retrieve_data(
                    system=system,
                    messages=messages,
                    tools=_TOOL_SCHEMAS,
                    model=WIKI_QUERY_MODEL,
                    max_tokens=WIKI_QUERY_MAX_TOKENS,
                ):
                    if event.type == WikiAgentEventType.TEXT_DELTA:
                        text_parts.append(event.text or "")
                        yield WikiStreamEvent(type=WikiStreamEventType.TEXT, text=event.text)
                    elif event.type == WikiAgentEventType.TURN_COMPLETE:
                        turn = event

                if turn is not None and turn.stop_reason == "tool_use":
                    messages.append({"role": "assistant", "content": self._assistant_content(turn=turn)})
                    yield WikiStreamEvent(type=WikiStreamEventType.STATUS, text=_STATUS_CONSULTING)
                    tool_results = [
                        self._dispatch(tool_use=tool_use, request_ticker=request.ticker)
                        for tool_use in turn.tool_uses
                    ]
                    messages.append({"role": "user", "content": tool_results})
                    continue

                answer_text = (turn.text if turn is not None else "").strip()
                if not answer_text:
                    yield self._error_event(
                        category=WikiErrorCategory.INCOMPLETE,
                        message="El modelo terminó el turno sin texto de respuesta.",
                    )
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

    def _initial_messages(self, request: WikiQueryRequest) -> list[dict]:
        """Build the starting message list: collapsed history pairs + the question.

        History is collapsed to plain text, all-or-nothing per (user, assistant)
        pair — a dangling or non-alternating turn is dropped so no tool_use block
        is ever left orphaned.

        Args:
            request: The wiki query carrying prior turns in ``history``.

        Returns:
            list[dict]: Anthropic message dicts, ending with the new user question.
        """
        messages: list[dict] = []
        history = request.history
        for user_msg, assistant_msg in zip(history[::2], history[1::2]):
            if user_msg.role == "user" and assistant_msg.role == "assistant":
                messages.append({"role": "user", "content": user_msg.content})
                messages.append({"role": "assistant", "content": assistant_msg.content})
        messages.append({"role": "user", "content": request.question})
        return messages

    def _assistant_content(self, turn: WikiAgentEvent) -> list[dict]:
        """Rebuild the assistant turn's content blocks (text + tool_use) for replay.

        Args:
            turn: The TURN_COMPLETE event whose stop_reason was "tool_use".

        Returns:
            list[dict]: An optional text block followed by one tool_use block per
                requested tool call, ids preserved so tool_result blocks match.
        """
        content: list[dict] = []
        if turn.text:
            content.append({"type": "text", "text": turn.text})
        for tool_use in turn.tool_uses:
            content.append({
                "type": "tool_use",
                "id": tool_use.id,
                "name": tool_use.name,
                "input": tool_use.input,
            })
        return content

    def _dispatch(self, tool_use: WikiToolUse, request_ticker: str) -> dict:
        """Execute one tool call and return its tool_result content block.

        Enforces ticker scope (case-insensitive) before dispatching, routes by
        tool name to the wiki/fundamentals repositories, turns a bad tool call
        (missing arg, unknown page, cross-FIBRA name) into an ``is_error`` result
        rather than raising, and truncates the payload to
        WIKI_QUERY_MAX_TOOL_RESULT_CHARS.

        Args:
            tool_use: The requested tool call (id, name, input).
            request_ticker: The FIBRA ticker this query is scoped to.

        Returns:
            dict: An Anthropic ``tool_result`` block for ``tool_use.id``.
        """
        tool_ticker = str(tool_use.input.get("ticker", ""))
        if tool_ticker.casefold() != request_ticker.casefold():
            return self._tool_result(
                tool_use_id=tool_use.id,
                content=(
                    f"Esta consulta es solo sobre {request_ticker}; no puedo consultar "
                    f"'{tool_ticker}'. Vuelve a llamar la tool con ticker={request_ticker}."
                ),
                is_error=True,
            )

        try:
            content = self._run_tool(tool_use=tool_use, request_ticker=request_ticker)
            return self._tool_result(tool_use_id=tool_use.id, content=content, is_error=False)
        except (FileNotFoundError, ValueError, KeyError) as exc:
            return self._tool_result(tool_use_id=tool_use.id, content=str(exc), is_error=True)

    def _run_tool(self, tool_use: WikiToolUse, request_ticker: str) -> str:
        """Route a scope-approved tool call to its repository/processor.

        Args:
            tool_use: The requested tool call.
            request_ticker: The FIBRA ticker this query is scoped to.

        Returns:
            str: The raw tool payload (wiki markdown, or fundamentals as JSON).

        Raises:
            FileNotFoundError: If a wiki page or index is missing.
            ValueError: If the page name is malformed (e.g. cross-FIBRA).
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

    def _tool_result(self, tool_use_id: str, content: str, is_error: bool) -> dict:
        """Build a truncated Anthropic tool_result block.

        Args:
            tool_use_id: Id of the tool_use block this result answers.
            content: The tool payload text.
            is_error: Whether this result reports a failed tool call.

        Returns:
            dict: The tool_result block, content capped at
                WIKI_QUERY_MAX_TOOL_RESULT_CHARS.
        """
        if len(content) > WIKI_QUERY_MAX_TOOL_RESULT_CHARS:
            content = content[:WIKI_QUERY_MAX_TOOL_RESULT_CHARS] + "\n… [contenido truncado]"
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": content,
            "is_error": is_error,
        }

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
