# FIBRAs Tracker — Context for Claude Code

## What is this project

A personal Python + Streamlit application (branded **FIBRALens**) to track and analyze Mexican
FIBRAs (Fideicomisos de Infraestructura y Bienes Raíces — the Mexican equivalent of REITs, listed
on the BMV). It tracks a personal portfolio (positions, distributions, live prices) and a
fundamentals history (quarterly KPIs per FIBRA, with annual aggregation and inflation-adjusted
growth analysis).

Full formula sets, data-file schemas, and feature descriptions live in `README.md`. This file
holds the architecture, conventions, and current state.

## Development principles

- **Small, verifiable features** — never full modules at once. Confirm each piece works before the next.
- Ask before implementing if there is any ambiguity in the requirement.
- **Docstrings are mandatory** — every class, method, and function. Google style: classes document
  fields under `Attributes:`; methods/functions document `Args:` and `Returns:` (processors also
  document each derived field's formula).

## Architecture

```
fibras-tracker/
├── app.py                  ← Streamlit entry point (registers pages via st.navigation)
├── config.py               ← paths, FIBRALens branding, FISCAL_RESULT_WITHHOLDING_RATE
├── ui/
│   ├── assets/             ← static files (SVG logo)
│   ├── components/
│   │   ├── common/         ← shared: page_header, error_banner
│   │   ├── portfolio/      ← summary_card, positions_table, distributions_chart, sector_chart
│   │   └── fundamentals/   ← detail_header, detail_chart, comparison_table, comparison_chart
│   ├── pages/              ← home.py, portfolio.py, fundamentals.py, radar.py
│   └── styles/
│       └── theme.py        ← color constants, number formatters, CSS injection
├── modules/                ← business logic
│   ├── common/
│   │   ├── models/         ← Fibra, Sector, SectorExposure, PaymentFrequency; MarketPrice; InflationRecord
│   │   ├── repositories/   ← json_catalog, yfinance_market_price, json_inflation (+ base/ interfaces)
│   │   └── schemas/        ← ServiceStatus (shared StrEnum: OK / ERROR)
│   ├── portfolio/
│   │   ├── models/         ← Position, EnrichedPosition, Distribution, EnrichedDistribution,
│   │   │                     Portfolio (+ PositionShare, SectorShare)
│   │   ├── repositories/   ← json_positions, json_distributions (+ base/)
│   │   ├── processors/     ← distributions_processor, positions_processor, portfolio_processor
│   │   ├── schemas/        ← PortfolioDataRetrieverServiceSchema
│   │   └── services/       ← portfolio_data_retriever_service
│   ├── fundamentals/
│   │   ├── models/         ← FundamentalsRecord, EnrichedFundamentalsRecord,
│   │   │                     AnnualFundamentalsRecord, FibraMetrics, FundamentalsHistory
│   │   ├── repositories/   ← json_fundamentals (+ base/)
│   │   ├── processors/     ← fundamentals_processor, annual_fundamentals_processor,
│   │   │                     fundamentals_history_processor
│   │   ├── schemas/        ← FundamentalsDataRetrieverServiceSchema
│   │   └── services/       ← fundamentals_data_retriever_service
│   └── radar/              ← (empty — reserved)
├── tests/
│   ├── portfolio/          ← 37 tests (all three portfolio processors)
│   └── fundamentals/       ← 86 tests (all three fundamentals processors)
└── data/
    ├── catalog.json        ← static FIBRA catalog (name, frequency, sector weights)
    ├── positions.json      ← portfolio holdings
    ├── distributions.json  ← distribution payment history
    ├── fundamentals.json   ← quarterly KPI history per FIBRA
    └── inflation.json      ← annual Mexican inflation (INPC) history
```

## Layer flow

Control flow:

```
pages/ → services/ → repositories/ → data source
            ↓
         processors/
```

Data transformation pipelines (executed inside the services):

```
# Portfolio
Distribution                                   ──[DistributionsProcessor]─▶ EnrichedDistribution
Position + MarketPrice + Fibra + [EnrichedDistribution]
                                               ──[PositionsProcessor]─────▶ EnrichedPosition
[EnrichedPosition]                             ──[PortfolioProcessor]─────▶ Portfolio

# Fundamentals
[FundamentalsRecord] + [MarketPrice]           ──[FundamentalsProcessor]──────▶ [EnrichedFundamentalsRecord]
[EnrichedFundamentalsRecord]                   ──[AnnualFundamentalsProcessor]─▶ [AnnualFundamentalsRecord]
[EnrichedFundamentalsRecord] + [Fibra]
  + [AnnualFundamentalsRecord] + [InflationRecord]
                                               ──[FundamentalsHistoryProcessor]▶ FundamentalsHistory
```

## Layer responsibilities

- `ui/pages/` — only calls methods from `services/`. Never touches repositories or data directly.
- `services/` — orchestrates: fetches from repos, transforms via processors, returns a UI-ready
  result wrapped in a schema.
- `repositories/` — data access only. Abstract interfaces in `repositories/base/`; concrete
  implementations named `<source>_<entity>_read_repository.py`.
- `processors/` — pure logic (calculations, aggregations, filters). No knowledge of data sources.
  Fail loud: raise `ValueError` on invalid input (e.g. `PositionsProcessor` if a position has no
  matching price/catalog entry; `PortfolioProcessor` on empty positions).
- `models/` — Pydantic domain entities. No methods, no computed fields, no validators. **raw →
  enriched** convention: a raw model (e.g. `Distribution`) is paired with an `Enriched<Name>`
  subclass adding processor-computed fields. Processors produce enriched models; repositories read
  raw models. (`AnnualFundamentalsRecord`, `FibraMetrics`, `FundamentalsHistory` are aggregate
  outputs, not enriched subclasses.)
- `schemas/` — service input/output contracts. Output convention: `<ServiceName>Schema` with
  `status` (`ServiceStatus`), `data` (optional payload), `error_message` (optional).

## Repository pattern

Switching the data source (JSON → API) must require no changes to `services/`, `processors/`, or
`pages/` — only a new concrete repository. Structure per domain: `base/` holds one abstract
interface per entity; concrete implementations are `json_<entity>_read_repository.py`,
`yfinance_<entity>_read_repository.py`, etc.

**Constructor convention:** concrete repositories take no constructor arguments. Anything dynamic
flows through `retrieve_data(...)` — e.g. `BaseMarketPriceReadRepository.retrieve_data(tickers)`.

## Service pattern

A service is the only entry point a `page/` may call. It:

1. Accepts optional repository instances in `__init__`, defaulting each to its concrete
   implementation when `None` (constructor injection with sensible defaults).
2. Instantiates all processors internally (processors are stateless, never injected).
3. Exposes a single public `run()` that orchestrates the repo → processor pipeline.
4. Wraps the whole pipeline in `try/except Exception`, always returning its typed
   `<ServiceName>Schema` (`status=OK` + `data`, or `status=ERROR` + `error_message`). Exceptions
   are never silently swallowed.

`PortfolioDataRetrieverService` and `FundamentalsDataRetrieverService` are the reference implementations.

## UI layer conventions

- `app.py` registers every page explicitly via `st.navigation([st.Page("ui/pages/…")])` — pages are
  not auto-discovered.
- **Page convention:** call `render_page_header()` first → wrap the service call in
  `@st.cache_data(ttl=300)` → check `result.status` and call `render_error_banner()` + `st.stop()`
  on error → render components section by section.
- **Component convention:** every component is a pure `render_<component>()` function. Stateless, no
  `st.session_state`, receives exactly the typed data it needs, never calls services/repositories.
- **theme.py:** always import `format_mxn`, `format_mxn_compact`, `format_pct`, `color_return`,
  `COLOR_POSITIVE/NEGATIVE/NEUTRAL` from here — never redefine colors/formatters in components.
  `load_custom_css()` is called once by `render_page_header()`; do not call it elsewhere.

## Stack

- Python 3.12+
- Streamlit, Pydantic (models + schemas), pandas, Plotly
- yfinance (market prices; tickers with `.MX` suffix). Use yfinance >=1.0.0 — 0.2.x has known Yahoo
  Finance API compatibility issues ("possibly delisted" errors on valid tickers).

## Linting

flake8, `max-line-length = 200` (`.flake8`).

## Code style

**Exports:** every class/model must be exported from its package's `__init__.py`. Imports reference
the package, not the file:
```python
from modules.fundamentals.models import FundamentalsRecord   # correct
from modules.fundamentals.models.fundamentals_record import FundamentalsRecord  # wrong
```

**One import per line:** never combine names on a single `from … import` line.

**Import order** (one blank line between groups): 1) standard library, 2) third-party,
3) internal — `modules/common/` first, then other internal imports.

**Keyword arguments:** every function/method call uses explicit keyword arguments — never positional:
```python
EnrichedPosition(ticker="FMTY14", cbfis=100, market_price=12.5)   # correct
EnrichedPosition("FMTY14", 100, 12.5)                              # wrong
```

## FIBRAs in scope

| Ticker    | Name           | Sector                    | Frequency |
|-----------|----------------|---------------------------|-----------|
| FMTY14    | Fibra Mty      | Industrial / Offices      | Monthly   |
| DANHOS13  | Fibra Danhos   | Mixed-use / Retail        | Quarterly |
| FIBRAPL14 | Fibra Prologis | Industrial / Logistics    | Quarterly |
| FSHOP13   | Fibra Shop     | Retail / Shopping centers | Quarterly |

yfinance tickers append `.MX` (e.g. `FMTY14.MX`).

## Business rules — critical invariants

Tax constant: `FISCAL_RESULT_WITHHOLDING_RATE = 0.30` lives in `config.py`. Full formula sets are in
the processor docstrings and `README.md`. Invariants to preserve in any new processor/formula:

- `average_purchase_cost` is the broker-adjusted cost base — never subtract reimbursements from it.
- Use `net_fiscal_result_income`, never `net_income`, when aggregating fiscal-result income
  (`net_income` includes the non-taxable reimbursement component).
- `dividend_yield` annualises the quarterly distribution (`distribution_per_cbfi * 4 / market_price`).
- `ltv` uses `financial_debt / total_assets` (interest-bearing debt), **not** `total_debt`.
- Per-CBFI ratios use `cbfis_with_rights`; `nav_per_cbfi` and `market_cap` use `cbfis_outstanding`.
- Annual distribution sums (`distribution_per_cbfi_annual`, `total_distribution_annual`) use a
  **partial sum** — sum of non-null quarters, null only if all four are null — because monthly
  payers may not report every quarter. All other annual sums are strict (null if any quarter null).

## Current project state

Complete:
- `modules/common/` — `Fibra`/`Sector`/`SectorExposure`/`PaymentFrequency`, `MarketPrice`,
  `InflationRecord`, `ServiceStatus`; JSON catalog/inflation + yfinance price repositories.
- `modules/portfolio/` — full pipeline: raw + enriched models, `Portfolio` (with `PositionShare`,
  `SectorShare`), repositories, three processors, service, schema.
- `modules/fundamentals/` — full pipeline: `FundamentalsRecord`, `EnrichedFundamentalsRecord`,
  `AnnualFundamentalsRecord`, `FibraMetrics`, `FundamentalsHistory`; repository; three processors
  (`FundamentalsProcessor`, `AnnualFundamentalsProcessor`, `FundamentalsHistoryProcessor`); service,
  schema.
- UI — Portfolio page (summary, positions table, allocation donuts, distributions chart) and
  Fundamentals page (Detalle tab: KPI detail header + unified KPI_CONFIG chart; Comparativa tab:
  evaluative table + normalized comparison chart).
- Unit tests — 123: 37 in `tests/portfolio/`, 86 in `tests/fundamentals/` (all five processors).
- Real data in all five `data/*.json` files. Formula-complete processor docstrings. `README.md`.

**Next step:** Radar page (`ui/pages/radar.py`) — currently a "Próximamente" placeholder.

## Data files overview

Detail (fields, units, how to add entries) lives in `README.md`.

- `data/catalog.json` — static FIBRA catalog: name, payment frequency, sector-exposure weights.
- `data/positions.json` — portfolio holdings (ticker, CBFIs, average purchase cost).
- `data/distributions.json` — distribution payment history (reimbursement / fiscal result per CBFI).
- `data/fundamentals.json` — quarterly KPI history per FIBRA.
- `data/inflation.json` — annual Mexican inflation (INPC) history, for growth-vs-inflation analysis.
