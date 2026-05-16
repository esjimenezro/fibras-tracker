# FIBRAs Tracker

A personal Streamlit application to track a portfolio of Mexican FIBRAs. It fetches live market prices via Yahoo Finance and reads distribution payment history from a local JSON file, computing per-position and portfolio-level metrics from both.

FIBRAs (Fideicomisos de Infraestructura y Bienes Raíces) are the Mexican equivalent of REITs, listed on the BMV (Mexican Stock Exchange).

---

## Features

**Live market prices**
- Prices fetched from Yahoo Finance using the `.MX` suffix (e.g. `FMTY14.MX`)

**Per-position metrics**
- Total purchase cost and current market value (MXN)
- Unrealised return in MXN and as a percentage of cost
- Return per CBFI
- Portfolio weight (share of total market value)
- Total net fiscal distributions received (after 30% ISR withholding)
- Combined return including distributions

**Distribution tracking**
- Separation of fiscal result income and capital reimbursement per payment
- 30% ISR withholding computed automatically on the fiscal component
- Net fiscal income accumulated across all payment dates

**Portfolio aggregates**
- Total invested, total market value, total unrealised return
- Total net distributions received across all positions
- Combined return (capital + distributions)

---

## Architecture

### Layer structure

```
pages/ → services/ → repositories/
               ↕
          processors/
```

- **`pages/`** call services only — no direct repository or data access.
- **`services/`** orchestrate: fetch raw data from repositories, transform it via processors, and return a typed result schema to the page.
- **`repositories/`** handle data access with no business logic. Abstract base classes live in `repositories/base/`; concrete implementations are named `<source>_<entity>_read_repository.py`.
- **`processors/`** contain pure business logic — calculations, aggregations, transformations. They have no knowledge of data sources.
- **`models/`** define Pydantic data contracts. No methods, no computed fields.

### Data transformation pipeline

```
Distribution
  → [DistributionsProcessor] → EnrichedDistribution

Position + MarketPrice + [EnrichedDistribution]
  → [PositionsProcessor] → EnrichedPosition

[EnrichedPosition]
  → [PortfolioProcessor] → Portfolio
```

### Repository pattern

Each entity has an abstract interface in `repositories/base/` that defines the `retrieve_data()` contract. Concrete implementations provide the actual data source (JSON file, Yahoo Finance, etc.). Swapping data sources requires only a new concrete implementation — services, processors, and pages remain untouched.

---

## Project structure

```
fibras-tracker/
├── app.py                      ← Streamlit entry point
├── config.py                   ← file paths and business constants
├── pages/                      ← Streamlit pages (one per module)
│   ├── portfolio.py
│   ├── fundamentals.py
│   └── radar.py
├── modules/
│   └── portfolio/
│       ├── models/             ← Pydantic data contracts (raw + enriched)
│       ├── repositories/       ← data access layer
│       │   └── base/           ← abstract interfaces
│       ├── processors/         ← pure business logic and calculations
│       ├── schemas/            ← service input/output contracts
│       └── services/           ← orchestration layer
├── tests/
│   └── portfolio/              ← unit tests for all three processors
└── data/
    ├── positions.json          ← portfolio holdings
    └── distributions.json      ← distribution payment history
```

---

## Data files

### `data/positions.json`

One entry per FIBRA held in the portfolio.

```json
{
  "positions": [
    {
      "ticker": "FMTY14",
      "name": "Fibra Mty",
      "sector": "Industrial / Offices",
      "cbfis": 1500,
      "average_purchase_cost": 9.58,
      "payment_frequency": "Monthly"
    }
  ]
}
```

| Field | Description |
|---|---|
| `ticker` | BMV ticker without the `.MX` suffix |
| `name` | Full name of the FIBRA |
| `sector` | Market sector |
| `cbfis` | Number of CBFIs (units) currently held |
| `average_purchase_cost` | Broker-reported weighted average cost per CBFI, in MXN |
| `payment_frequency` | `"Monthly"` or `"Quarterly"` |

> **Note:** `average_purchase_cost` is the value reported by your broker and is already cost-adjusted. Do not manually subtract reimbursements from it — those are tracked separately in `distributions.json`.

To add a new position: append a new object to the `"positions"` array.

---

### `data/distributions.json`

One entry per payment event. A FIBRA that pays monthly will have multiple entries.

```json
{
  "distributions": [
    {
      "ticker": "FMTY14",
      "payment_date": "2026-03-06",
      "reimbursement_per_cbfi": 0.0331,
      "fiscal_result_per_cbfi": 0.0483,
      "cbfis_at_time": 1500
    }
  ]
}
```

| Field | Description |
|---|---|
| `ticker` | BMV ticker matching a position in `positions.json` |
| `payment_date` | Date the payment was credited by the broker (`YYYY-MM-DD`) |
| `reimbursement_per_cbfi` | Capital reimbursement per CBFI — not taxable when received |
| `fiscal_result_per_cbfi` | Fiscal result per CBFI — subject to 30% ISR withholding |
| `cbfis_at_time` | CBFIs held at the time of this specific payment |

To record a new distribution: append a new object to the `"distributions"` array.

---

## Business rules

Tax constants are defined in `config.py`:

```python
FISCAL_RESULT_WITHHOLDING_RATE = 0.30  # 30% ISR withholding on fiscal result income
```

### Distributions pipeline (`DistributionsProcessor` → `EnrichedDistribution`)

```
gross_fiscal_result_income = fiscal_result_per_cbfi * cbfis_at_time
net_reimbursement_income   = reimbursement_per_cbfi * cbfis_at_time
gross_income               = gross_fiscal_result_income + net_reimbursement_income
fiscal_result_withholding  = FISCAL_RESULT_WITHHOLDING_RATE * gross_fiscal_result_income
net_fiscal_result_income   = gross_fiscal_result_income - fiscal_result_withholding
net_income                 = gross_income - fiscal_result_withholding
```

`net_fiscal_result_income` is the fiscal component only, net of withholding. `net_income` additionally includes the non-taxable reimbursement. Use `net_fiscal_result_income` — not `net_income` — when aggregating income for return calculations.

### Positions pipeline (`PositionsProcessor` → `EnrichedPosition`)

```
purchase_cost                        = average_purchase_cost * cbfis
market_value                         = market_price * cbfis
return_per_cbfi                      = market_price - average_purchase_cost
return_pct                           = return_per_cbfi / average_purchase_cost
total_return                         = return_per_cbfi * cbfis
total_net_fiscal_result_received     = sum(d.net_fiscal_result_income for d in distributions)
total_return_including_distributions = total_return + total_net_fiscal_result_received
```

### Portfolio aggregation (`PortfolioProcessor` → `Portfolio`)

```
total_purchase_cost               = sum(p.purchase_cost for p in positions)
total_market_value                = sum(p.market_value for p in positions)
total_return                      = total_market_value - total_purchase_cost
total_return_pct                  = total_return / total_purchase_cost
total_net_fiscal_result_received  = sum(p.total_net_fiscal_result_received for p in positions)
total_return_including_distributions = total_return + total_net_fiscal_result_received
positions_share                   = p.market_value / total_market_value  (per position)
last_updated_at                   = max(p.price_updated_at for p in positions)
```

`positions_share` always sums to exactly 1.0 across all positions.

---

## Setup and installation

**Requirements:** Python 3.12+

**Install with uv** (recommended):

```bash
uv sync
```

**Install with pip** (alternative):

```bash
pip install -r requirements.txt
```

**Run the app:**

```bash
uv run streamlit run app.py
# or without uv:
streamlit run app.py
```

Live market prices require an internet connection. If Yahoo Finance is unreachable, the app will display an error returned by `PortfolioDataRetrieverService`.

---

## Development guidelines

### Layer discipline

- `pages/` call services only — never repositories or processors directly.
- `services/` accept optional repository instances in `__init__` (defaulting to the concrete implementations) and instantiate all processors internally.
- `processors/` are stateless and have no external dependencies. They fail loud: `ValueError` is raised on invalid input (e.g. missing market price, empty positions list).
- `repositories/` implement data access only. Business logic belongs in processors.

### Repository naming

```
repositories/base/<base_entity>_read_repository.py   ← abstract interface
repositories/<source>_<entity>_read_repository.py    ← concrete implementation
```

Examples: `json_positions_read_repository.py`, `yfinance_market_price_read_repository.py`.

All concrete repositories take no constructor arguments. Dynamic inputs (such as tickers) are passed at call time via `retrieve_data(...)`.

### Raw → enriched model pattern

Repositories produce **raw** models (`Position`, `Distribution`). Processors produce **enriched** subclasses (`EnrichedPosition`, `EnrichedDistribution`) that inherit from the raw model and add computed fields. Never mix the two in a single layer.

### Docstrings

Google style, mandatory on every class and method:

- Classes: `Attributes:` section listing all fields.
- Methods: `Args:`, `Returns:`, and `Raises:` sections. Processor methods also document the formula for each derived field in the `Returns:` section.

### Linting

```bash
flake8 modules/ tests/
```

Max line length: 200 characters (configured in `.flake8`).

### Testing

```bash
uv run pytest tests/ -v
```

Tests use real Pydantic instances — no mocks, no network calls, no file I/O. Expected values are hardcoded from the business rule formulas. Use `pytest.approx` for all float assertions.

---

## Current status

**Complete:**
- Domain models — raw (`Position`, `Distribution`, `MarketPrice`) and enriched (`EnrichedPosition`, `EnrichedDistribution`, `Portfolio`)
- Repository interfaces (`base/`) and concrete implementations (`json_*`, `yfinance_*`)
- Three processors implementing the full data pipeline
- Typed service output schema (`PortfolioDataRetrieverServiceSchema`)
- Main orchestrator service (`PortfolioDataRetrieverService`)
- Unit test suite — 37 tests covering all three processors

**Next:**
- Streamlit portfolio page (`pages/portfolio.py`) consuming `PortfolioDataRetrieverService`
