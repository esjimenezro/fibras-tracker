# FIBRAs Tracker — Context for Claude Code

## What is this project

A personal Python + Streamlit application to track a portfolio of Mexican FIBRAs (Fideicomisos de Infraestructura y Bienes Raíces). FIBRAs are the Mexican equivalent of REITs, listed on the BMV (Mexican Stock Exchange).

## Development principles

- **Small, verifiable features** — never full modules at once
- Confirm each piece works before moving to the next
- Ask before implementing if there is any ambiguity in the requirement
- **Docstrings are mandatory** — every class, method, and function must have a docstring describing its purpose
- **Docstrings follow Google style** — classes document fields under `Attributes:`, methods and functions document parameters under `Args:` and return values under `Returns:`

## Architecture

```
fibras-tracker/
├── app.py                  ← Streamlit entry point (registers pages via st.navigation)
├── config.py               ← paths, titles, business constants (e.g. FISCAL_RESULT_WITHHOLDING_RATE)
├── ui/
│   ├── assets/             ← static files (SVG logo)
│   ├── components/
│   │   ├── common/         ← shared: page_header, error_banner
│   │   └── portfolio/      ← domain: summary_card, positions_table, distributions_chart
│   ├── pages/              ← Streamlit page scripts (one per module)
│   │   ├── home.py
│   │   ├── portfolio.py
│   │   ├── fundamentals.py
│   │   └── radar.py
│   └── styles/
│       └── theme.py        ← color constants, number formatters, CSS injection
├── modules/                ← business logic
│   ├── common/
│   ├── portfolio/
│   │   ├── models/
│   │   │   ├── position.py                  ← raw Position + PaymentFrequency enum
│   │   │   ├── enriched_position.py         ← EnrichedPosition(Position) with computed fields
│   │   │   ├── distribution.py              ← raw Distribution
│   │   │   ├── enriched_distribution.py     ← EnrichedDistribution(Distribution) with computed fields
│   │   │   ├── market_price.py              ← MarketPrice (live price snapshot)
│   │   │   └── portfolio.py                 ← Portfolio + PositionShare (aggregated output)
│   │   ├── repositories/
│   │   │   ├── base/
│   │   │   │   ├── base_positions_read_repository.py
│   │   │   │   ├── base_distributions_read_repository.py
│   │   │   │   └── base_market_price_read_repository.py
│   │   │   ├── json_positions_read_repository.py
│   │   │   ├── json_distributions_read_repository.py
│   │   │   └── yfinance_market_price_read_repository.py
│   │   ├── processors/
│   │   │   ├── distributions_processor.py   ← Distribution → EnrichedDistribution
│   │   │   ├── positions_processor.py       ← Position + MarketPrice + [EnrichedDistribution] → EnrichedPosition
│   │   │   └── portfolio_processor.py       ← [EnrichedPosition] → Portfolio
│   │   ├── schemas/
│   │   │   └── portfolio_schemas.py         ← service input/output contracts
│   │   └── services/
│   │       └── portfolio_data_retriever_service.py  ← main orchestrator
│   ├── fundamentals/
│   └── radar/
└── data/
    ├── positions.json
    ├── distributions.json
    └── historical/
```

## Layer flow

Control flow:

```
pages/ → services/ → repositories/ → data source
               ↕
          processors/
```

Data transformation pipeline (executed inside the service):

```
Distribution      ──[DistributionsProcessor]──▶ EnrichedDistribution
Position + MarketPrice + [EnrichedDistribution]
                  ──[PositionsProcessor]─────▶ EnrichedPosition
[EnrichedPosition]──[PortfolioProcessor]─────▶ Portfolio
```

## UI layer

- `app.py` uses `st.navigation([st.Page("ui/pages/…")])` — pages are **not** auto-discovered; every page must be explicitly registered here.
- Component convention: every component is a pure `render_<component>()` function. Stateless, no `st.session_state`. Receives exactly the typed data it needs; never calls services or repositories.
- Page convention: call `render_page_header()` first → wrap service call in `@st.cache_data(ttl=300)` → check `result.status` and call `render_error_banner()` + `st.stop()` on error → render components section by section with `st.divider()`.
- `theme.py` usage: always import `format_mxn`, `format_mxn_compact`, `format_pct`, `color_return`, `COLOR_POSITIVE/NEGATIVE/NEUTRAL` from here. Never redefine colors or formatters inside components. `load_custom_css()` is called once by `render_page_header()` — do not call it from individual components.

## Layer responsibilities

- `ui/pages/` only calls methods from `services/`. Never touches repos or data directly.
- `services/` orchestrates: fetches data from repos, transforms it via processors, returns a UI-ready result wrapped in a schema.
- `repositories/` implements data access. Abstract interfaces live in `repositories/base/`. Concrete implementations are named `<source>_<entity>_read_repository.py` (e.g. `json_positions_read_repository.py`, `yfinance_market_price_read_repository.py`).
- `processors/` contains pure logic: calculations, aggregations, filters. No knowledge of data sources or services. Processors fail loud — raise `ValueError` on invalid input (e.g. `PositionsProcessor` raises if any position has no matching market price; `PortfolioProcessor` raises on an empty positions list).
- `models/` defines domain entities as Pydantic models. No methods, no computed fields, no validators — pure data contracts. The codebase uses a **raw → enriched** convention: a raw model (e.g. `Distribution`) is paired with an `Enriched<Name>` subclass that inherits from it and adds processor-computed fields. Processors only produce enriched models; repositories only read raw models.
- `schemas/` holds service input/output contracts. Convention for service outputs: `<ServiceName>Schema` with three fields — `status` (a `StrEnum` of `"OK"` / `"ERROR"`), `data` (the success payload, optional), and `error_message` (optional). See `PortfolioDataRetrieverServiceSchema` for the worked example.

## Repository pattern

The goal is that switching the data source (JSON → API) requires no changes to `services/`, `processors/`, or `pages/`. Only a new concrete repository implementation is added. The contract is enforced by the abstract base class.

Repository structure per domain:

- `base/` → one abstract interface file per entity (e.g. `base_positions_read_repository.py`)
- `json_<entity>_read_repository.py` → concrete JSON implementation
- `yfinance_<entity>_read_repository.py` / `api_<entity>_read_repository.py` → other concrete implementations

**Constructor convention:** all concrete repositories take no constructor arguments. Anything dynamic flows through `retrieve_data(...)`. For example, `BaseMarketPriceReadRepository.retrieve_data(tickers: list[str])` takes tickers at call time — not in `__init__` — so the service can resolve all repository defaults uniformly inside `__init__` and pass the runtime ticker list when calling `retrieve_data`.

## Service pattern

A service is the only entry point a `page/` is allowed to call. It:

1. Accepts optional repository instances in `__init__` and defaults each to its concrete implementation when `None` is passed (constructor injection with sensible defaults).
2. Instantiates all processors internally — processors are never injected (they are stateless and have no external dependencies).
3. Exposes a single public method (typically `run()`) that orchestrates the repo → processor pipeline.
4. Wraps the entire pipeline in `try/except Exception` and always returns its typed `<ServiceName>Schema` with either `status=OK` and `data` populated, or `status=ERROR` and `error_message=str(e)`. Exceptions are never silently swallowed.

`PortfolioDataRetrieverService` is the reference implementation.

## Stack

- Python 3.11+
- Streamlit
- Pydantic (models and schemas)
- yfinance (market prices, tickers with `.MX` suffix)
- pandas (transformations)
- Plotly Express (charts in UI components)

## Linting

- **Tool**: flake8
- **Max line length**: 200 characters (`max-line-length = 200` in `.flake8`)

## Code style

**Exports:** every class and model must be exported from its package's `__init__.py`. All imports must reference the package, not the file:
```python
# correct
from modules.fundamentals.models import FundamentalsRecord
# wrong
from modules.fundamentals.models.fundamentals_record import FundamentalsRecord
```

**One import per line:** never combine multiple names on a single `from … import` line:
```python
# correct
from modules.portfolio.models import Position
from modules.portfolio.models import Distribution
# wrong
from modules.portfolio.models import Position, Distribution
```

**Import order** (one blank line between each group):
1. Standard library (`datetime`, `abc`, `json`, …)
2. Third-party (`pydantic`, `pandas`, `streamlit`, …)
3. Internal — `modules/common/` imports first, then other internal imports

**Keyword arguments:** every function/method call must use explicit keyword arguments — never pass values by position:
```python
# correct
render_summary_card(total_purchase_cost=portfolio.total_purchase_cost, total_market_value=portfolio.total_market_value)
EnrichedPosition(ticker="FMTY14", cbfis=100, market_price=12.5)
# wrong
render_summary_card(portfolio.total_purchase_cost, portfolio.total_market_value)
EnrichedPosition("FMTY14", 100, 12.5)
```

## Dependencies notes

- yfinance: use version >=1.0.0. Versions 0.2.x have known compatibility
  issues with Yahoo Finance API and may return "possibly delisted" errors
  even for valid tickers.

## FIBRAs in the portfolio

| Ticker    | Name           | Sector                    | Frequency |
|-----------|----------------|---------------------------|-----------|
| FMTY14    | Fibra Mty      | Industrial / Offices      | Monthly   |
| DANHOS13  | Fibra Danhos   | Mixed-use / Retail        | Quarterly |
| FIBRAPL14 | Fibra Prologis | Industrial / Logistics    | Quarterly |
| FSHOP13   | Fibra Shop     | Retail / Shopping centers | Quarterly |

yfinance tickers: append `.MX` suffix (e.g. `FMTY14.MX`)

## Business rules

Full formula sets are documented in processor docstrings and `README.md`.

Tax constant: `FISCAL_RESULT_WITHHOLDING_RATE = 0.30` lives in `config.py`.

Critical invariants to preserve in any new processor or formula:
- `average_purchase_cost` is the broker-adjusted cost base — never subtract reimbursements from it.
- Use `net_fiscal_result_income`, never `net_income`, when aggregating fiscal result income. `net_income` includes the non-taxable reimbursement component.

## Current project state

Complete:
- Domain models (`modules/portfolio/models/`) — raw + enriched + aggregate
- Repository interfaces (`repositories/base/`) and concrete implementations (`json_*`, `yfinance_*`)
- Processors (`processors/`) — three processors implementing the data pipeline
- Schemas (`schemas/`) — `PortfolioDataRetrieverServiceSchema` and `PortfolioDataRetrieverStatus`
- Main orchestrator service: `PortfolioDataRetrieverService`
- Unit tests (`tests/portfolio/`) — 37 tests covering all three processors
- Processor docstrings — formula-complete Google-style docstrings on all processor classes and methods
- `README.md` — human-readable developer documentation
- Portfolio page (`ui/pages/portfolio.py`) — summary metrics, positions table, allocation pie, distributions chart

Real data populated in `data/positions.json` and `data/distributions.json`.

**Next step**: Fundamentals page (`ui/pages/fundamentals.py`).

## Agreed implementation order

1. ~~Models (`modules/portfolio/models/`)~~ ✓
2. ~~Repository interfaces (`modules/portfolio/repositories/base/`)~~ ✓
3. ~~Concrete repositories (`json_*`, `yfinance_*`)~~ ✓
4. ~~Processors (calculations)~~ ✓
5. ~~Service (orchestrator) + schemas~~ ✓
6. ~~Portfolio page (`ui/pages/portfolio.py`)~~ ✓
7. Models (`modules/fundamentals/models/`)
8. Repository interfaces (`modules/fundamentals/repositories/base/`)
9. Concrete repositories
10. Processors (`modules/fundamentals/processors/`)
11. Service and Schema (`modules/fundamentals/services/` and `modules/fundamentals/schemas/`)
12. Fundamentals page (`ui/pages/fundamentals.py`)

Implement and verify one layer at a time before moving to the next.
