# ESJ-14 — Queries entre FIBRAs (índice agregador) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `WikiQueryService` answer questions that cross ≥2 FIBRAs, in both Fundamentales → Detalle (anchored on the selected FIBRA, open to the rest) and Fundamentales → Comparativa (fully open scope, no anchor, no pre-selection).

**Architecture:** `WikiQueryRequest.ticker: str` becomes a `tickers: list[str]` scope guard plus an optional `primary_ticker` anchor for prompt framing; a new `WikiRosterProcessor` joins `catalog.json` with the wiki ticker roster into one formatted roster string consumed both by a new `read_wiki_catalog` tool (runtime discovery) and a generation script that writes a committed `wiki/index.md` (Obsidian navigation). No repository-level cross-FIBRA wikilink parsing is needed — every tool call already carries `ticker` as its own argument.

**Tech Stack:** Python 3.12, Pydantic v2, Streamlit, pytest, flake8.

**Spec:** `docs/superpowers/specs/2026-09-17-cross-fibra-wiki-queries-design.md`

## Global Constraints

- Docstrings are mandatory on every class, method and function (Google style: `Attributes:` on classes, `Args:`/`Returns:`/`Raises:` on methods).
- Every function/method call uses explicit keyword arguments — never positional.
- One import per line; import order (blank line between groups): stdlib, third-party, internal (`modules/common/` first).
- Every class/model is exported from its package's `__init__.py`; import the package, never the file.
- `modules/*/models/` — Pydantic domain entities only: no methods, no computed fields, no validators.
- `modules/*/repositories/` — concrete classes take no constructor arguments; dynamic values flow through `retrieve_data(...)`.
- `modules/*/services/` — wrap the pipeline in `try/except Exception`, always return the typed `<ServiceName>Schema`; never let an exception escape `run()`/`stream()`.
- `flake8`, `max-line-length = 200` (`.flake8`). Run `flake8 modules/ tests/ scripts/` before every commit in this plan.
- Test command: `uv run pytest tests/wiki/ -v` (repo tests wiki content repos/processors against the real committed `wiki/` and `data/catalog.json` — no mocks for those).

---

## Task 1: `WikiQueryRequest` scope-as-a-set + service guard/dispatch fix

**Files:**
- Modify: `modules/wiki/models/wiki_query_request.py`
- Modify: `modules/wiki/services/_wiki_query_prompt.py`
- Modify: `modules/wiki/services/wiki_query_service.py`
- Modify: `tests/wiki/services/test_wiki_query_service.py`
- Modify: `tests/wiki/processors/test_wiki_message_processor.py:20`
- Modify: `ui/pages/fundamentals.py:85`

**Interfaces:**
- Produces: `WikiQueryRequest(tickers: list[str], primary_ticker: Optional[str] = None, question: str, history: list[WikiChatMessage] = [])` — replaces the old `ticker: str` field everywhere in the codebase.
- Produces: `WikiQueryService._has_foreign_ticker(self, turn: WikiAgentEvent, allowed_tickers: list[str]) -> bool` — renamed/generalized from the old `(turn, request_ticker: str)` signature.
- Produces: `WikiQueryService._dispatch(self, tool_use: WikiToolUse) -> dict` and `WikiQueryService._run_tool(self, tool_use: WikiToolUse) -> str` — no longer take `request_ticker`; they read `tool_use.input["ticker"]` directly, so a multi-ticker conversation dispatches each call to its own FIBRA instead of a single service-wide default.

This task fixes a latent bug: today `_run_tool` ignores `tool_use.input["ticker"]` and always uses the service's single `request_ticker` — harmless while `tickers` has exactly one member (the guard already forces them to match), but wrong once a query's scope has ≥2 tickers, since two tool calls in the same conversation can legitimately target different FIBRAs.

- [ ] **Step 1: Update the model**

Replace the full contents of `modules/wiki/models/wiki_query_request.py`:

```python
from typing import Optional

from pydantic import BaseModel

from modules.wiki.models.wiki_chat_message import WikiChatMessage


class WikiQueryRequest(BaseModel):
    """Input contract for one wiki query: an allowed FIBRA scope, one question plus history.

    Attributes:
        tickers: BMV tickers this query may read from (e.g. ["FMTY14",
            "FIBRAPL14"]), at least one. The agent rejects any tool call whose
            ticker is not in this set.
        primary_ticker: The FIBRA the answer should focus on by default, e.g.
            "FMTY14". None when the query has no single focus — a comparison
            across all of ``tickers`` on equal footing.
        question: The user's natural-language question for this turn.
        history: Prior turns for this thread, oldest first. Empty on the first turn.
    """

    tickers: list[str]
    primary_ticker: Optional[str] = None
    question: str
    history: list[WikiChatMessage] = []
```

No constructor call site is fixed yet — that comes in later steps, so nothing imports this successfully until Step 4. That's expected.

- [ ] **Step 2: Update the prompt shell**

In `modules/wiki/services/_wiki_query_prompt.py`, delete the single `INSTRUCTIONS_SHELL` constant and replace it with a header/focus/tools split so the service can compose the primary-vs-comparison framing. Replace everything from `INSTRUCTIONS_SHELL = (` through the end of that constant's closing `)` with:

```python
INSTRUCTIONS_HEADER = (
    "Eres un asistente que responde preguntas sobre FIBRAs mexicanas usando su "
    "wiki de contexto narrativo y sus cifras de fundamentals.json.\n\n"
)

FOCUS_PRIMARY_TEMPLATE = (
    "Esta consulta es principalmente sobre {primary_ticker}. También podés "
    "consultar estas otras FIBRAs cuando la pregunta lo amerite explícitamente "
    "(por ejemplo, para comparar): {tickers}. Si la pregunta es sobre una FIBRA "
    "fuera de esta lista, decilo y no llames a las tools con otro ticker.\n\n"
)

FOCUS_COMPARISON_TEMPLATE = (
    "Esta consulta compara estas FIBRAs en igualdad de condiciones: {tickers}. "
    "Si la pregunta involucra una FIBRA fuera de esta lista, decilo y no llames "
    "a las tools con otro ticker.\n\n"
)

INSTRUCTIONS_TOOLS = (
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
    "formato [[nombre-de-pagina]] (p. ej. \"según [[2024-Q1]], ...\"). Si tu "
    "respuesta involucra más de una FIBRA, cualificá la cita con su ticker en "
    "minúsculas (p. ej. \"según [[fmty14/2024-Q1]], ...\") para que no se confunda "
    "con la página del mismo nombre de otra FIBRA. Responde en español y de forma "
    "concisa.\n\n"
    "A continuación están las reglas que gobiernan la wiki (wiki/SCHEMA.md); síguelas "
    "para la Operación: Query.\n\n---\n\n"
)
```

Also update the two tool descriptions and the two fixed messages so they no longer name a single ticker:

```python
READ_INDEX_DESCRIPTION = (
    "Devuelve el índice de navegación (index.md) de la wiki de la FIBRA: la lista "
    "de páginas de trimestre y de concepto con un resumen de una línea de cada una. "
    "Úsalo primero para ubicar las páginas relevantes antes de leerlas."
)

READ_PAGE_DESCRIPTION = (
    "Devuelve el contenido completo de una página de la wiki de la FIBRA. page_name "
    "es un nombre estilo wikilink: una página de trimestre (\"2024-Q1\") o de concepto "
    "(\"plan-crecimiento\"), con o sin corchetes [[ ]] y con o sin sufijo .md. "
    "No se admiten referencias a otras FIBRAs (nombres con \"/\") — para leer otra "
    "FIBRA, llamá esta misma tool con su propio ticker."
)
```

```python
STATUS_CONSULTING = "Consultando la wiki…"

# Returned as the answer when the model calls a tool for a ticker outside request.tickers.
OUT_OF_SCOPE_MESSAGE = (
    "Esta consulta está limitada a {tickers}. Para consultar otra FIBRA, "
    "seleccionala o agregala a la comparación."
)

# Returned when the model produced an answer without ever reading the wiki or
# fundamentals for the FIBRAs in scope (no successful in-scope tool call).
UNGROUNDED_MESSAGE = (
    "No pude fundamentar una respuesta en la wiki de {tickers} para esta pregunta."
)
```

`READ_FUNDAMENTALS_DESCRIPTION` and `TOOL_SCHEMAS` are unchanged in this step (only their `"ticker"` property descriptions read "Ticker de la FIBRA a consultar." instead of "de esta consulta." — update those three property descriptions in `TOOL_SCHEMAS` to say `"Ticker de la FIBRA a consultar."`).

- [ ] **Step 3: Update the service**

In `modules/wiki/services/wiki_query_service.py`:

1. Replace the import block for `_wiki_query_prompt` (remove `INSTRUCTIONS_SHELL`, `OUT_OF_SCOPE_MESSAGE`, `UNGROUNDED_MESSAGE` stay, add the new names):

```python
from modules.wiki.services._wiki_query_prompt import FOCUS_COMPARISON_TEMPLATE
from modules.wiki.services._wiki_query_prompt import FOCUS_PRIMARY_TEMPLATE
from modules.wiki.services._wiki_query_prompt import INSTRUCTIONS_HEADER
from modules.wiki.services._wiki_query_prompt import INSTRUCTIONS_TOOLS
from modules.wiki.services._wiki_query_prompt import OUT_OF_SCOPE_MESSAGE
from modules.wiki.services._wiki_query_prompt import STATUS_CONSULTING
from modules.wiki.services._wiki_query_prompt import TOOL_SCHEMAS
from modules.wiki.services._wiki_query_prompt import UNGROUNDED_MESSAGE
```

2. In `stream()`, replace the `system = [...]` assembly and the tool-use branch:

```python
try:
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
```

3. Replace `_has_foreign_ticker`, `_dispatch` and `_run_tool` with:

```python
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

    Returns:
        str: The raw tool payload (wiki markdown, or fundamentals as JSON).

    Raises:
        FileNotFoundError: If a wiki page or index is missing.
        ValueError: If the page name is malformed, or the tool name is unknown.
        KeyError: If a required tool argument is absent.
    """
    ticker = tool_use.input["ticker"]
    if tool_use.name == "read_index":
        return self._index_repository.retrieve_data(ticker=ticker.lower())
    if tool_use.name == "read_page":
        return self._page_repository.retrieve_data(
            ticker=ticker.lower(),
            page_name=tool_use.input["page_name"],
        )
    if tool_use.name == "read_fundamentals":
        records = self._fundamentals_filter.process(
            records=self._fundamentals_repository.retrieve_data(),
            ticker=ticker.upper(),
            period=tool_use.input.get("period"),
        )
        return json.dumps(
            [record.model_dump(mode="json") for record in records],
            ensure_ascii=False,
            indent=2,
        )
    raise ValueError(f"Tool desconocida: {tool_use.name}")
```

- [ ] **Step 4: Fix the two remaining `WikiQueryRequest(ticker=...)` call sites**

In `tests/wiki/processors/test_wiki_message_processor.py:20`, change:
```python
return WikiQueryRequest(ticker="DANHOS13", question=question, history=history or [])
```
to:
```python
return WikiQueryRequest(tickers=["DANHOS13"], primary_ticker="DANHOS13", question=question, history=history or [])
```

In `ui/pages/fundamentals.py:85`, change:
```python
request = WikiQueryRequest(ticker=ticker, question=question, history=list(history))
```
to:
```python
request = WikiQueryRequest(
    tickers=[ticker],
    primary_ticker=ticker,
    question=question,
    history=list(history),
)
```
This is the only UI change in this task — Detalle keeps today's exact single-ticker behavior. Widening its scope is Task 4.

- [ ] **Step 5: Update `tests/wiki/services/test_wiki_query_service.py`**

Update the `_request` helper:
```python
def _request(**overrides):
    """Build a WikiQueryRequest with sensible defaults for tests."""
    kwargs = {
        "tickers": ["DANHOS13"],
        "primary_ticker": "DANHOS13",
        "question": "¿por qué subió el apalancamiento?",
    }
    kwargs.update(overrides)
    return WikiQueryRequest(**kwargs)
```

Update every call site that overrode `ticker=`:
- `test_tool_call_with_foreign_ticker_aborts_with_fixed_reply`: change `_request(ticker="DANHOS13")` to `_request()` (already the default) and `OUT_OF_SCOPE_MESSAGE.format(ticker="DANHOS13")` to `OUT_OF_SCOPE_MESSAGE.format(tickers="DANHOS13")`.
- `test_answer_without_any_tool_call_returns_ungrounded_reply`: change `_request(ticker="DANHOS13", question=...)` to `_request(question=...)` and `UNGROUNDED_MESSAGE.format(ticker="DANHOS13")` to `UNGROUNDED_MESSAGE.format(tickers="DANHOS13")`.
- `test_answer_after_only_failed_tool_calls_returns_ungrounded_reply` and any other `UNGROUNDED_MESSAGE.format(ticker="DANHOS13")` / `OUT_OF_SCOPE_MESSAGE.format(ticker="DANHOS13")` occurrences: same `ticker=` → `tickers=` rename (the value stays the string `"DANHOS13"` — a single-ticker scope still renders as just that ticker).

Add two new tests proving the multi-ticker fix, appended after `test_read_page_miss_returns_is_error_with_valid_names`:

```python
def test_multi_ticker_tool_use_dispatches_to_the_ticker_in_the_call(make_service):
    """Two tool calls in one scope route to their own FIBRA, not a single default."""
    agent = _FakeAgentRepository([
        [_turn_tool_use(
            _tool_use("t1", "read_index", ticker="FMTY14"),
            _tool_use("t2", "read_index", ticker="DANHOS13"),
        )],
        [_turn_end("Listo.")],
    ])

    result = make_service(agent).run(
        request=_request(tickers=["FMTY14", "DANHOS13"], primary_ticker=None),
    )

    assert result.status == ServiceStatus.OK
    tool_results = agent.calls[1]["messages"][-1]["content"]
    assert tool_results[0]["is_error"] is False
    assert tool_results[1]["is_error"] is False
    assert tool_results[0]["content"] != tool_results[1]["content"]


def test_tool_call_outside_allowed_tickers_aborts_with_fixed_reply(make_service):
    """A tool call for a ticker outside the allowed set aborts with the fixed reply."""
    agent = _FakeAgentRepository([
        [_turn_tool_use(_tool_use("t1", "read_index", ticker="FUNO11"))],
        [_turn_end("no debería llegar aquí")],
    ])

    result = make_service(agent).run(
        request=_request(tickers=["FMTY14", "DANHOS13"], primary_ticker="FMTY14"),
    )

    assert result.status == ServiceStatus.OK
    assert result.data.answer_text == OUT_OF_SCOPE_MESSAGE.format(tickers="FMTY14, DANHOS13")
    assert len(agent.calls) == 1
```

- [x] **Step 5b (added during code review of ESJ-34): guard against an empty `tickers` scope**

Code review on the PR flagged that `WikiQueryRequest.tickers` is documented as
containing at least one item but nothing enforces it — with `tickers=[]` the
service builds a broken prompt (`"...en igualdad de condiciones: ."`) and, if
the model attempts any tool call, the scope guard treats every ticker as
foreign and returns `OUT_OF_SCOPE_MESSAGE.format(tickers="")` as a normal
`FINAL`/`OK` answer instead of rejecting the invalid request. Fixed in the
service, not the model — this repo's models carry no validators (`Field`
constraints included; none exist anywhere in `modules/*/models/`), so the
"fail loud on invalid input" guard belongs where the request is acted on:

In `modules/wiki/services/wiki_query_service.py`, at the top of the `try`
block in `stream()`:
```python
try:
    if not request.tickers:
        raise ValueError("WikiQueryRequest.tickers must not be empty")
    tickers_label = ", ".join(request.tickers)
```
This raises before any prompt is assembled or the agent is called; the
existing generic `except Exception as exc` at the bottom of `stream()` turns
it into a terminal `ERROR` / `INTERNAL` event like any other internal failure.

Test, added to `tests/wiki/services/test_wiki_query_service.py` (in the
"Terminal errors" section, before `test_iteration_cap_without_answer_yields_incomplete`):
```python
def test_empty_tickers_yields_internal_error_without_calling_the_agent(make_service):
    """An empty tickers scope is a caller bug, not a normal out-of-scope/ungrounded case."""
    agent = _FakeAgentRepository([[_turn_end("no debería llegar aquí")]])

    result = make_service(agent).run(request=_request(tickers=[], primary_ticker=None))

    assert result.status == ServiceStatus.ERROR
    assert "tickers" in result.error_message
    assert len(agent.calls) == 0
```

- [ ] **Step 6: Run the wiki test suite and lint**

Run: `uv run pytest tests/wiki/ -v`
Expected: all tests pass, including the two new ones.

Run: `flake8 modules/ tests/`
Expected: no violations.

- [ ] **Step 7: Commit**

```bash
git add modules/wiki/models/wiki_query_request.py modules/wiki/services/_wiki_query_prompt.py modules/wiki/services/wiki_query_service.py tests/wiki/services/test_wiki_query_service.py tests/wiki/processors/test_wiki_message_processor.py ui/pages/fundamentals.py
git commit -m "feat(wiki): scope WikiQueryRequest to a set of tickers, fix per-call ticker dispatch"
```

---

## Task 2: `WikiRosterProcessor` + `read_wiki_catalog` discovery tool

**Files:**
- Create: `modules/wiki/processors/wiki_roster_processor.py`
- Create: `tests/wiki/processors/test_wiki_roster_processor.py`
- Modify: `modules/wiki/processors/__init__.py`
- Modify: `modules/wiki/services/_wiki_query_prompt.py`
- Modify: `modules/wiki/services/wiki_query_service.py`
- Modify: `tests/wiki/services/test_wiki_query_service.py`

**Interfaces:**
- Consumes: `Fibra` (`modules.common.models`, fields `ticker`, `name`, `sector_exposure: list[SectorExposure]`), `JsonCatalogReadRepository.retrieve_data() -> list[Fibra]` (`modules.common.repositories`), `FileSystemWikiCatalogReadRepository.retrieve_data() -> list[str]` (`modules.wiki.repositories`, already exists).
- Produces: `WikiRosterProcessor().process(fibras: list[Fibra], wiki_tickers: list[str]) -> str`.

- [ ] **Step 1: Write the failing processor test**

Create `tests/wiki/processors/test_wiki_roster_processor.py`:

```python
from modules.common.repositories import JsonCatalogReadRepository
from modules.wiki.processors import WikiRosterProcessor
from modules.wiki.repositories import FileSystemWikiCatalogReadRepository


def test_process_lists_every_wiki_ticker_sorted_with_sector_and_link():
    """Every FIBRA with a wiki gets one sorted line naming its sector(s) and index link."""
    fibras = JsonCatalogReadRepository().retrieve_data()
    wiki_tickers = FileSystemWikiCatalogReadRepository().retrieve_data()

    result = WikiRosterProcessor().process(fibras=fibras, wiki_tickers=wiki_tickers)

    lines = result.split("\n")
    assert len(lines) == len(wiki_tickers)
    assert lines == sorted(lines)
    assert "- FMTY14 — Fibra Mty (" in result
    assert "[[fmty14/index]]" in result


def test_process_returns_empty_string_for_no_wiki_tickers():
    """An empty wiki roster produces an empty string, not a stray newline."""
    fibras = JsonCatalogReadRepository().retrieve_data()

    result = WikiRosterProcessor().process(fibras=fibras, wiki_tickers=[])

    assert result == ""
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/wiki/processors/test_wiki_roster_processor.py -v`
Expected: FAIL — `ModuleNotFoundError` / `ImportError: cannot import name 'WikiRosterProcessor'`.

- [ ] **Step 3: Implement the processor**

Create `modules/wiki/processors/wiki_roster_processor.py`:

```python
from modules.common.models import Fibra


class WikiRosterProcessor:
    """Formats the FIBRA roster used by the cross-FIBRA discovery tool and wiki/index.md.

    Transformation: (list[Fibra], list[str] of lower-case wiki ticker slugs) ->
    a markdown bullet list, one line per FIBRA that has a wiki, sorted by
    ticker. Pure formatting: no I/O, no knowledge of where either input came
    from — the same output feeds both the runtime discovery tool and the
    committed wiki/index.md, so they never drift apart.
    """

    def process(self, fibras: list[Fibra], wiki_tickers: list[str]) -> str:
        """Build one markdown bullet line per FIBRA that has a wiki.

        Args:
            fibras: The full FIBRA catalog (name, sector_exposure per ticker).
            wiki_tickers: Lower-case wiki directory slugs (e.g. ["danhos13",
                "fmty14"]), as returned by BaseWikiCatalogReadRepository.

        Returns:
            str: One line per ticker in ``wiki_tickers``, sorted alphabetically,
                formatted as
                ``"- {TICKER} — {name} ({sector} {weight%}, ...) — [[{slug}/index]]"``.
                Empty string when ``wiki_tickers`` is empty.

        Raises:
            KeyError: If a wiki ticker slug has no matching entry in ``fibras``
                (upper-cased) — the catalog and the wiki roster are expected to
                stay in sync.
        """
        fibras_by_ticker = {fibra.ticker: fibra for fibra in fibras}
        lines = []
        for slug in sorted(wiki_tickers):
            ticker = slug.upper()
            fibra = fibras_by_ticker[ticker]
            sectors = ", ".join(
                f"{exposure.sector.value} {exposure.weight:.0%}"
                for exposure in fibra.sector_exposure
            )
            lines.append(f"- {ticker} — {fibra.name} ({sectors}) — [[{slug}/index]]")
        return "\n".join(lines)
```

- [ ] **Step 4: Export it**

In `modules/wiki/processors/__init__.py`, add the import and `__all__` entry:

```python
from modules.wiki.processors.citation_processor import CitationProcessor
from modules.wiki.processors.fundamentals_query_filter_processor import FundamentalsQueryFilterProcessor
from modules.wiki.processors.wiki_message_processor import WikiMessageProcessor
from modules.wiki.processors.wiki_roster_processor import WikiRosterProcessor


__all__ = [
    "CitationProcessor",
    "FundamentalsQueryFilterProcessor",
    "WikiMessageProcessor",
    "WikiRosterProcessor",
]
```

- [ ] **Step 5: Run the processor tests to verify they pass**

Run: `uv run pytest tests/wiki/processors/test_wiki_roster_processor.py -v`
Expected: PASS.

- [ ] **Step 6: Wire the tool into the prompt shell**

In `modules/wiki/services/_wiki_query_prompt.py`, add a new description near the other `*_DESCRIPTION` constants:

```python
READ_WIKI_CATALOG_DESCRIPTION = (
    "Devuelve la lista de FIBRAs que tienen wiki disponible, cada una con su "
    "nombre, su exposición sectorial y un link a su propio índice. Sin "
    "argumentos. Úsala cuando la pregunta mencione o sugiera otra FIBRA sin "
    "decir cuál, para descubrir qué otras FIBRAs existen antes de decidir si "
    "vale la pena abrir su wiki."
)
```

Replace `INSTRUCTIONS_TOOLS` (from Task 1) with the four-tool version:

```python
INSTRUCTIONS_TOOLS = (
    "Tienes cuatro tools de solo lectura:\n"
    "- read_wiki_catalog(): la lista de FIBRAs con wiki disponible, con nombre y sector.\n"
    "- read_index(ticker): el índice de navegación de la wiki de la FIBRA.\n"
    "- read_page(ticker, page_name): una página de trimestre (p. ej. \"2024-Q1\") o "
    "de concepto (p. ej. \"plan-crecimiento\").\n"
    "- read_fundamentals(ticker, period?): las cifras crudas para la FIBRA, "
    "opcionalmente filtradas por período (formato \"1T2026\").\n\n"
    "Flujo: si la pregunta menciona o sugiere otra FIBRA sin nombrarla, usa primero "
    "read_wiki_catalog para ubicarla; luego read_index para encontrar páginas "
    "candidatas de cada FIBRA en el conjunto permitido; luego read_page para "
    "leerlas; usa read_fundamentals cuando necesites una cifra exacta. No inventes "
    "datos que no estén en la wiki o en fundamentals.\n\n"
    "Cita cada afirmación con el wikilink de la página de la que proviene, con el "
    "formato [[nombre-de-pagina]] (p. ej. \"según [[2024-Q1]], ...\"). Si tu "
    "respuesta involucra más de una FIBRA, cualificá la cita con su ticker en "
    "minúsculas (p. ej. \"según [[fmty14/2024-Q1]], ...\") para que no se confunda "
    "con la página del mismo nombre de otra FIBRA. Responde en español y de forma "
    "concisa.\n\n"
    "A continuación están las reglas que gobiernan la wiki (wiki/SCHEMA.md); síguelas "
    "para la Operación: Query.\n\n---\n\n"
)
```

Append the new tool schema to `TOOL_SCHEMAS` (order does not matter to the API; add it first for readability):

```python
TOOL_SCHEMAS: list[dict] = [
    {
        "name": "read_wiki_catalog",
        "description": READ_WIKI_CATALOG_DESCRIPTION,
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "read_index",
        # ... unchanged, keep the three existing entries below in their current order
    },
    ...
]
```

- [ ] **Step 7: Wire the tool into the service**

In `modules/wiki/services/wiki_query_service.py`:

1. Add imports:
```python
from modules.common.repositories import JsonCatalogReadRepository
from modules.common.repositories.base import BaseCatalogReadRepository
from modules.wiki.processors import WikiRosterProcessor
from modules.wiki.repositories import FileSystemWikiCatalogReadRepository
from modules.wiki.repositories.base import BaseWikiCatalogReadRepository
```

2. Extend `__init__`:
```python
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
```

3. Update `_run_tool` to handle the no-ticker tool first:
```python
def _run_tool(self, tool_use: WikiToolUse) -> str:
    """Route a tool call to its repository/processor and return the raw payload.

    Args:
        tool_use: The requested tool call. Its own ``ticker`` input (not a
            service-wide default) selects which FIBRA's data is read, since a
            multi-ticker query can dispatch different tickers per call.
            ``read_wiki_catalog`` takes no ``ticker`` at all.

    Returns:
        str: The raw tool payload (wiki markdown, roster text, or fundamentals
            as JSON).

    Raises:
        FileNotFoundError: If a wiki page or index is missing.
        ValueError: If the page name is malformed, or the tool name is unknown.
        KeyError: If a required tool argument is absent.
    """
    if tool_use.name == "read_wiki_catalog":
        return self._roster_processor.process(
            fibras=self._catalog_repository.retrieve_data(),
            wiki_tickers=self._wiki_catalog_repository.retrieve_data(),
        )
    ticker = tool_use.input["ticker"]
    if tool_use.name == "read_index":
        return self._index_repository.retrieve_data(ticker=ticker.lower())
    if tool_use.name == "read_page":
        return self._page_repository.retrieve_data(
            ticker=ticker.lower(),
            page_name=tool_use.input["page_name"],
        )
    if tool_use.name == "read_fundamentals":
        records = self._fundamentals_filter.process(
            records=self._fundamentals_repository.retrieve_data(),
            ticker=ticker.upper(),
            period=tool_use.input.get("period"),
        )
        return json.dumps(
            [record.model_dump(mode="json") for record in records],
            ensure_ascii=False,
            indent=2,
        )
    raise ValueError(f"Tool desconocida: {tool_use.name}")
```

- [ ] **Step 8: Write the failing service tests**

In `tests/wiki/services/test_wiki_query_service.py`, add imports:
```python
from modules.common.repositories import JsonCatalogReadRepository
from modules.wiki.repositories import FileSystemWikiCatalogReadRepository
```

Update the `make_service` fixture to wire the two new repositories:
```python
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
            catalog_repository=JsonCatalogReadRepository(),
            wiki_catalog_repository=FileSystemWikiCatalogReadRepository(),
        )
    return _make
```

Append two new tests after the multi-ticker tests from Task 1:
```python
def test_read_wiki_catalog_dispatch_lists_wiki_tickers(make_service):
    """read_wiki_catalog returns the roster without needing a ticker argument."""
    agent = _FakeAgentRepository([
        [_turn_tool_use(_tool_use("t1", "read_wiki_catalog"))],
        [_turn_end("ok")],
    ])

    make_service(agent).run(request=_request())

    tool_result = agent.calls[1]["messages"][-1]["content"][0]
    assert tool_result["is_error"] is False
    assert "FMTY14" in tool_result["content"]
    assert "DANHOS13" in tool_result["content"]


def test_read_wiki_catalog_does_not_trigger_the_scope_guard(make_service):
    """A read_wiki_catalog call (no ticker input) never counts as a foreign-ticker call."""
    agent = _FakeAgentRepository([
        [_turn_tool_use(_tool_use("t1", "read_wiki_catalog"))],
        [_turn_end("Según el catálogo, hay 7 FIBRAs.")],
    ])

    result = make_service(agent).run(request=_request())

    assert result.status == ServiceStatus.OK
    assert result.data.answer_text == "Según el catálogo, hay 7 FIBRAs."
```

- [ ] **Step 9: Run the full wiki suite and lint**

Run: `uv run pytest tests/wiki/ -v`
Expected: all tests pass (existing + Task 1's + these two).

Run: `flake8 modules/ tests/`
Expected: no violations.

- [ ] **Step 10: Commit**

```bash
git add modules/wiki/processors/wiki_roster_processor.py tests/wiki/processors/test_wiki_roster_processor.py modules/wiki/processors/__init__.py modules/wiki/services/_wiki_query_prompt.py modules/wiki/services/wiki_query_service.py tests/wiki/services/test_wiki_query_service.py
git commit -m "feat(wiki): add WikiRosterProcessor and the read_wiki_catalog discovery tool"
```

---

## Task 3: `wiki/index.md` generation script

**Files:**
- Create: `scripts/generate_wiki_root_index.py`
- Create: `wiki/index.md` (generated output, committed)

**Interfaces:**
- Consumes: `JsonCatalogReadRepository`, `FileSystemWikiCatalogReadRepository`, `WikiRosterProcessor` (all from Task 1/2).

- [ ] **Step 1: Write the script**

Create `scripts/generate_wiki_root_index.py`:

```python
"""Regenerate wiki/index.md from catalog.json + the wiki/ directory roster.

Run manually whenever the roster of FIBRAs with a wiki changes (a rare event —
see wiki/SCHEMA.md, "Múltiples FIBRAs"). Not part of the per-quarter ingest.

Usage (from the repo root, so "config" and "modules" resolve on sys.path):
    uv run python -m scripts.generate_wiki_root_index
"""

from config import WIKI_DIR
from modules.common.repositories import JsonCatalogReadRepository
from modules.wiki.processors import WikiRosterProcessor
from modules.wiki.repositories import FileSystemWikiCatalogReadRepository


_HEADER = (
    "# Índice de FIBRAs\n\n"
    "Apunta al `index.md` de cada FIBRA con wiki — no duplica su contenido. "
    "Generado por `scripts/generate_wiki_root_index.py`; no editar a mano.\n\n"
)


def main() -> None:
    """Write wiki/index.md from the current catalog + wiki roster."""
    fibras = JsonCatalogReadRepository().retrieve_data()
    wiki_tickers = FileSystemWikiCatalogReadRepository().retrieve_data()
    roster = WikiRosterProcessor().process(fibras=fibras, wiki_tickers=wiki_tickers)
    (WIKI_DIR / "index.md").write_text(_HEADER + roster + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it and inspect the output**

Run: `uv run python -m scripts.generate_wiki_root_index` (running the file
directly with `uv run python scripts/generate_wiki_root_index.py` fails with
`ModuleNotFoundError: No module named 'config'` — the repo root isn't on
`sys.path` unless invoked as a module from there; `-m` fixes that).
Then: `cat wiki/index.md`
Expected: a header followed by 7 sorted bullet lines, one per FIBRA ticker, each with a sector breakdown and a `[[<slug>/index]]` link — matching the format asserted in `test_wiki_roster_processor.py`.

- [ ] **Step 3: Lint the script**

Run: `flake8 scripts/`
Expected: no violations.

- [ ] **Step 4: Commit**

```bash
git add scripts/generate_wiki_root_index.py wiki/index.md
git commit -m "feat(wiki): generate the root wiki/index.md aggregator from catalog + wiki roster"
```

---

## Task 4: UI — Detalle tab opens scope to every FIBRA with a wiki

**Files:**
- Modify: `ui/pages/fundamentals.py`

**Interfaces:**
- Consumes: `WikiQueryRequest(tickers, primary_ticker, question, history)` (Task 1), `WikiCatalogServiceSchema.data: list[str]` (already returned by the existing `_load_wiki_catalog()`).
- Produces: `_render_wiki_chat(tickers: list[str], primary_ticker: Optional[str], thread_key: str, placeholder: str) -> None` — generalized from the old `_render_wiki_chat(ticker: str)`, reused by Task 5.

- [ ] **Step 1: Generalize `_render_wiki_chat`**

Replace the current `_render_wiki_chat` function body in `ui/pages/fundamentals.py` with:

```python
def _render_wiki_chat(
    tickers: list[str],
    primary_ticker: Optional[str],
    thread_key: str,
    placeholder: str,
) -> None:
    """Render a "Pregúntale a la wiki" chat scoped to one or more FIBRAs.

    Conversation history is kept per ``thread_key`` in
    ``st.session_state["wiki_chat"]`` so switching FIBRA (Detalle) or FIBRA
    combination (Comparativa) preserves each thread independently. The
    WikiQueryService stream is consumed here (never cached): TEXT events grow a
    placeholder, STATUS events show a progress caption, and the terminal
    FINAL/ERROR event renders the answer with its sources line or an inline
    banner keyed by ``error_category``.

    Args:
        tickers: BMV tickers this query may read from.
        primary_ticker: The FIBRA the answer should focus on by default, or
            None for a comparison across all of ``tickers`` on equal footing.
        thread_key: Session-state key identifying this conversation thread (a
            single ticker for Detalle, a sorted combination for Comparativa).
        placeholder: Text shown inside the empty chat input box.
    """
    threads: dict[str, list[WikiChatMessage]] = st.session_state.setdefault("wiki_chat", {})
    history = threads.setdefault(thread_key, [])

    for message in history:
        with st.chat_message(message.role):
            st.markdown(message.content)

    question = st.chat_input(placeholder)
    if not question:
        return

    with st.chat_message("user"):
        st.markdown(question)

    request = WikiQueryRequest(
        tickers=tickers,
        primary_ticker=primary_ticker,
        question=question,
        history=list(history),
    )
    with st.chat_message("assistant"):
        status_slot = st.empty()
        text_slot = st.empty()
        answer = ""
        terminal = None
        for event in WikiQueryService().stream(request=request):
            if event.type == WikiStreamEventType.TEXT:
                answer += event.text or ""
                text_slot.markdown(answer + " ▌")
            elif event.type == WikiStreamEventType.STATUS:
                status_slot.caption(f"🔎 {event.text}")
            elif event.type in (WikiStreamEventType.FINAL, WikiStreamEventType.ERROR):
                terminal = event

        status_slot.empty()
        if terminal is not None and terminal.type == WikiStreamEventType.FINAL:
            text_slot.markdown(terminal.data.answer_text)
            render_citations(citations=terminal.data.citations)
            history.append(WikiChatMessage(role="user", content=question))
            history.append(WikiChatMessage(role="assistant", content=terminal.data.answer_text))
        else:
            text_slot.empty()
            category = terminal.error_category if terminal is not None else WikiErrorCategory.INTERNAL
            st.error(_WIKI_ERROR_MESSAGES.get(category, _WIKI_ERROR_MESSAGES[WikiErrorCategory.INTERNAL]))
```

- [ ] **Step 2: Update the Detalle tab call site**

In the `detalle_tab` block, replace:
```python
    else:
        _render_wiki_chat(ticker=selected_ticker)
```
with:
```python
    else:
        _render_wiki_chat(
            tickers=wiki_catalog.data,
            primary_ticker=selected_ticker,
            thread_key=selected_ticker,
            placeholder=f"Pregunta sobre {selected_ticker}…",
        )
```
`wiki_catalog.data` is already the full list of BMV tickers with a wiki (from the existing `_load_wiki_catalog()` call a few lines above) — no new repository call needed.

- [ ] **Step 3: Manual verification (no automated UI tests exist in this repo)**

Run: `streamlit run app.py`
1. Open Fundamentales → Detalle, pick FMTY14 (or any ticker).
2. Ask a question that plausibly needs another FIBRA, e.g. "¿algo similar le pasó a otra FIBRA industrial?"
3. Confirm the chat does not show the "Esta consulta está limitada a..." fixed reply when the model reads another ticker's wiki, and that the answer stays framed around FMTY14.
4. Ask an ordinary single-FIBRA question and confirm behavior is unchanged from before this task.

- [ ] **Step 4: Commit**

```bash
git add ui/pages/fundamentals.py
git commit -m "feat(wiki): open Detalle's wiki chat scope to every FIBRA with a wiki"
```

---

## Task 5: UI — Comparativa tab open-scope comparative chat, docs update

**Files:**
- Modify: `ui/pages/fundamentals.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `_render_wiki_chat` (Task 4), `WikiCatalogServiceSchema.data: list[str]`.

No selector precedes this chat: the user asks directly about any combination
of the FIBRAs with a wiki (e.g. "¿cuál tiene mayor exposición cambiaria,
FMTY14 o FIBRAPL14?") and the model discovers and reads whichever FIBRAs the
question needs via `read_wiki_catalog` + `read_index` — the same open-scope
mechanism Task 4 gives Detalle, just without a `primary_ticker` anchor. This
was corrected mid-plan: the original design required an `st.multiselect` with
≥2 FIBRAs picked upfront, which the user rejected as inconsistent with
Detalle's own open-scope UX ("debería poder preguntar de cualquier
combinación de las FIBRAs ya habilitadas").

- [ ] **Step 1: Add the open-scope chat to the Comparativa tab**

In the `comparativa_tab` block, after the existing `render_comparison_chart(...)` call, append:

```python
    st.divider()
    st.subheader("💬 Pregúntale a la wiki (comparativo)")
    wiki_catalog = _load_wiki_catalog()
    if wiki_catalog.status == ServiceStatus.ERROR:
        st.error("No se pudo leer el catálogo de wikis.")
        st.caption(wiki_catalog.error_message)
    elif not os.environ.get("ANTHROPIC_API_KEY"):
        st.info(
            "El chat de wiki necesita configurar `ANTHROPIC_API_KEY` en el archivo `.env` "
            "(copiá `.env.example` a `.env` y completá la clave)."
        )
    else:
        st.caption("FIBRAs disponibles: " + ", ".join(wiki_catalog.data))
        _render_wiki_chat(
            tickers=wiki_catalog.data,
            primary_ticker=None,
            thread_key="comparativa",
            placeholder="Pregunta comparando dos o más FIBRAs…",
        )
```

`wiki_catalog.data` is the same cached call Detalle already uses — no new repository call, no pre-selection step, and a single shared thread for the tab (`thread_key="comparativa"`) since there is no user-chosen combination to key on anymore.

- [ ] **Step 2: Update README.md**

At `README.md:103-107`, change:
```
WikiQueryRequest (ticker, question, history)
  → [WikiQueryService] — agentic tool loop over three read-only tools
      (wiki index / wiki page / fundamentals lookup), dispatched through
      AnthropicWikiAgentReadRepository (one call = one model turn)
  → stream of WikiStreamEvent (TEXT / STATUS / terminal FINAL or ERROR)
```
to:
```
WikiQueryRequest (tickers, primary_ticker, question, history)
  → [WikiQueryService] — agentic tool loop over four read-only tools
      (wiki catalog / wiki index / wiki page / fundamentals lookup), dispatched
      through AnthropicWikiAgentReadRepository (one call = one model turn)
  → stream of WikiStreamEvent (TEXT / STATUS / terminal FINAL or ERROR)
```

At `README.md:113`, change "ticker out of scope" to "ticker outside the allowed scope".

At `README.md:236`, replace the Detalle wiki-chat bullet's first sentence to reflect the open scope:
```
4. **💬 Pregúntale a la wiki** — a chat scoped to the selected FIBRA, shown only when `wiki/<ticker>/` exists (checked via `WikiCatalogService().run()`, cached, which returns BMV tickers) and `ANTHROPIC_API_KEY` is set.
```
to:
```
4. **💬 Pregúntale a la wiki** — a chat anchored on the selected FIBRA but scoped to every FIBRA with a wiki (via `read_wiki_catalog`, so the model can discover and read another FIBRA's wiki when a question calls for it), shown only when `wiki/<ticker>/` exists (checked via `WikiCatalogService().run()`, cached, which returns BMV tickers) and `ANTHROPIC_API_KEY` is set.
```

At `README.md:240`, after the existing `render_comparison_chart(...)` bullet, add a third bullet:
```
3. **💬 Pregúntale a la wiki (comparativo)** — shown directly (same `ANTHROPIC_API_KEY`/catalog gating as Detalle), scoped to every FIBRA with a wiki with no default focus (`WikiQueryRequest.primary_ticker = None`) and no FIBRA picker: the user asks about any combination directly and the model discovers which FIBRAs to read via `read_wiki_catalog`. Reuses the same `_render_wiki_chat` helper as Detalle, in a single shared thread (`thread_key="comparativa"`).
```

- [ ] **Step 2: Manual verification**

Run: `streamlit run app.py`
1. Open Fundamentales → Comparativa.
2. Confirm the chat is shown directly, with no FIBRA picker beforehand.
3. Ask a comparative question naming two FIBRAs (e.g. "¿cuál tiene mayor exposición cambiaria, FMTY14 o FIBRAPL14?").
4. Confirm the answer reads naturally as a comparison (no single FIBRA framed as primary) and citations are qualified (`[[fmty14/...]]`, `[[fibrapl14/...]]`) when both are cited.
5. Ask a question about a third combination in the same thread and confirm prior turns don't confuse the answer (a single shared thread, unlike Detalle's per-ticker ones).

- [ ] **Step 3: Commit**

```bash
git add ui/pages/fundamentals.py README.md
git commit -m "feat(wiki): add the comparativo multi-FIBRA wiki chat to the Comparativa tab"
```

---

## Self-Review Notes

- **Spec coverage:** Decisión 1 → Tasks 2–3; Decisión 2 → confirmed as a no-op (documented, no task needed); Decisión 3 → Task 1; Decisión 4 → Tasks 4–5. All four covered.
- **Type consistency:** `WikiQueryRequest.tickers`/`primary_ticker` (Task 1) match the constructor calls in Tasks 4–5 and the `_request()` test helper. `_run_tool`/`_dispatch` signatures (Task 1, extended in Task 2) match every call site. `WikiRosterProcessor.process(fibras=..., wiki_tickers=...)` (Task 2) matches its use in the service (Task 2) and the generation script (Task 3).
- **No placeholders:** every step above ships real code and real assertions; nothing deferred to "add later."
