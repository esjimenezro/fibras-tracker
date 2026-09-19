# Copilot instructions — fibras-tracker (FIBRALens)

Personal Streamlit app tracking Mexican FIBRAs (BMV-listed REIT equivalents). No SQL database,
no ORM, no web framework of its own — a layered Python architecture over local JSON files, a
markdown "wiki" tree, and the Anthropic API.

## Review order — do this first, before anything else

1. Read the PR description in full.
2. Compare it against the actual diff, hunk by hunk.
3. **Flag scope creep**: any file touched or behavior changed in the diff that the description
   does not mention. Name the specific file.
4. **Flag unmet promises**: any behavior the description claims that the diff does not implement,
   or implements only partially. Name what's missing.
5. Only after that comparison, move on to correctness, security, and architecture review.
6. If the PR description is missing or empty, say so explicitly instead of silently skipping this
   step.

## Stack

- Python 3.12+, `uv` for dependency management (`pyproject.toml`).
- Streamlit 1.56 — UI.
- Pydantic v2 — domain models and service I/O contracts.
- pandas + Plotly — data wrangling and charts.
- Anthropic SDK — agentic wiki chat (`modules/wiki/`).
- yfinance — live market prices.
- pymupdf — PDF-to-markdown transcription for wiki ingestion (offline tooling, not the running app).
- No database, no ORM. Persistence is `data/*.json` (parsed straight into Pydantic models on read)
  and `wiki/` (a markdown tree — content, not code).
- `flake8`, `max-line-length = 200`. No other linter or formatter is configured.

## Layer architecture

```
ui/pages/ → modules/*/services/ → modules/*/repositories/ + modules/*/processors/ → modules/*/models/, schemas/
```

- **`ui/components/`** — pure `render_*()` functions. Never import `.services` or `.repositories`
  from any module, only `.models`/`.schemas` (typed data the page passes in).
- **`ui/pages/`** — the only layer allowed to call a service. Never imports a repository directly.
- **`modules/*/services/`** — orchestrates repositories + processors. Constructor takes
  `Optional[BaseXRepository] = None` per dependency, defaulting to the concrete implementation
  (`x_repository or ConcreteXRepository()`). Processors are instantiated inside `__init__`, never
  injected. The public entry point (`run()` or `stream()`) wraps everything in
  `try/except Exception` and returns a typed `<ServiceName>Schema` — it never raises.
- **`modules/*/processors/`** — stateless pure logic, no `__init__`, no I/O. Fail loud: raise on
  invalid input instead of silently defaulting or skipping it.
- **`modules/*/repositories/`** — data access only. Concrete classes take **no constructor
  arguments**; anything dynamic is a parameter of `retrieve_data(...)`. One abstract base per
  entity under `repositories/base/`.
- **`modules/*/models/`** — Pydantic domain entities. No methods, no computed fields, no
  validators (not even a `Field(...)` constraint — none exist anywhere in this repo today).
- **`modules/*/schemas/`** — service I/O contracts: `<ServiceName>Schema` with `status`
  (`ServiceStatus.OK`/`ERROR`), `data`, `error_message`.

Full detail, a worked example, and known exceptions:
`.github/instructions/architecture.instructions.md`.

## Naming conventions

- Files: `<source>_<entity>_read_repository.py`, `<name>_processor.py`, `<name>_service.py`,
  `<name>_schema.py` / `<name>_schemas.py`. snake_case throughout.
- Classes: PascalCase matching the file (`JsonCatalogReadRepository`,
  `FundamentalsDataRetrieverService`).
- Every class is exported from its package's `__init__.py` via `__all__`. Import the package,
  never the file:
  - Correct: `from modules.fundamentals.models import FundamentalsRecord`
  - Wrong: `from modules.fundamentals.models.fundamentals_record import FundamentalsRecord`
- One import per line — never combine names on a single `from … import` line.
- Import order, one blank line between groups: (1) standard library, (2) third-party,
  (3) internal (`modules/common/` first, then other internal imports).
- Every function/method call in this codebase's own modules uses explicit keyword arguments —
  never positional:
  - Correct: `EnrichedPosition(ticker="FMTY14", cbfis=100, market_price=12.5)`
  - Wrong: `EnrichedPosition("FMTY14", 100, 12.5)`

## Error handling

- Repositories raise `FileNotFoundError` when a data source is missing, `ValueError` when input
  (e.g. a wiki ticker/page slug) fails validation.
- Processors raise `ValueError` on invalid or empty input — never return a partial or
  silently-defaulted result to paper over bad input.
- Services never raise: the public entry point catches `Exception` and returns
  `status=ServiceStatus.ERROR, error_message=str(exc)` — or, for `WikiQueryService.stream()`, a
  terminal `ERROR` stream event carrying an `error_category`.
- Domain-specific exceptions (`WikiAuthError`, `WikiRateLimitError`, `WikiConnectionError`,
  `WikiAgentError` in `src/modules/wiki/exceptions.py`) wrap third-party SDK exceptions at the one
  module allowed to import that SDK. A third-party exception type must never leak past that
  boundary.

## Testing standards

- No mocking library anywhere in the repo — no `unittest.mock`, no `MagicMock`, no `@patch`.
  Repositories and processors are tested against real Pydantic instances, real committed files
  (`wiki/`, `data/catalog.json`), or a hand-written `_Fake*`/`_Stub*` class — never a generic mock
  object.
- One deliberate exception: `AnthropicWikiAgentReadRepository` — the module's only network
  boundary — is tested with `monkeypatch` on `anthropic.Anthropic`
  (`tests/wiki/repositories/test_anthropic_wiki_agent_read_repository.py`). Flag new mocking
  anywhere else; a hand-written fake belongs there instead.
- `pytest.approx(value, rel=1e-6)` for every float assertion; exact equality for strings, enums,
  and ints.
- Every test function and fixture carries a one-line docstring stating what it verifies or
  returns.
- Test files mirror the module tree: `tests/<module>/<layer>/test_<file>.py`.

## Docstrings

- Mandatory on every class, method, and function.
- Google style: classes document fields under `Attributes:`; methods/functions document
  `Args:`/`Returns:`/`Raises:`.
- Processors additionally document each derived field's formula in the docstring.

## Related instructions

- `.github/instructions/security.instructions.md` — security review checklist.
- `.github/instructions/architecture.instructions.md` — layering rules, worked example, known
  debt.
