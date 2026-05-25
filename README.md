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

**Portfolio page (`ui/pages/portfolio.py`)**
- Summary metrics: market value (with unrealised MXN delta), purchase cost, total return %, net distributions, and total return including distributions
- Allocation donut chart showing portfolio weight per FIBRA
- Positions table: per-FIBRA breakdown with colour-coded return columns (green/red)
- Distributions history: stacked bar chart grouped by FIBRA with a monthly/daily granularity toggle, plus a side-by-side summary table showing gross fiscal income, reimbursement, ISR withholding, and net income per period

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

FundamentalsRecord + list[MarketPrice]
  → [FundamentalsProcessor] → EnrichedFundamentalsRecord

list[EnrichedFundamentalsRecord] + list[Fibra]
  → [FundamentalsHistoryProcessor] → FundamentalsHistory
```

### Repository pattern

Each entity has an abstract interface in `repositories/base/` that defines the `retrieve_data()` contract. Concrete implementations provide the actual data source (JSON file, Yahoo Finance, etc.). Swapping data sources requires only a new concrete implementation — services, processors, and pages remain untouched.

---

## Project structure

```
fibras-tracker/
├── app.py                      ← Streamlit entry point (registers pages via st.navigation)
├── config.py                   ← file paths and business constants
├── ui/
│   ├── assets/                 ← static files (SVG logo)
│   ├── components/
│   │   ├── common/             ← shared: page_header, error_banner
│   │   └── portfolio/          ← domain: summary_card, positions_table, distributions_chart
│   ├── pages/                  ← Streamlit page scripts (one per module)
│   │   ├── home.py
│   │   ├── portfolio.py
│   │   ├── fundamentals.py
│   │   └── radar.py
│   └── styles/
│       └── theme.py            ← color constants, number formatters, CSS injection
├── modules/
│   ├── common/
│   │   ├── models/             ← Sector, SectorExposure, Fibra, PaymentFrequency, MarketPrice
│   │   ├── repositories/       ← catalog and market price repositories
│   │   │   └── base/           ← abstract interfaces
│   │   └── schemas/            ← ServiceStatus (shared across all modules)
│   ├── portfolio/
│   │   ├── models/             ← Pydantic data contracts (raw + enriched + aggregate)
│   │   ├── repositories/       ← data access layer
│   │   │   └── base/           ← abstract interfaces
│   │   ├── processors/         ← pure business logic and calculations
│   │   ├── schemas/            ← service input/output contracts
│   │   └── services/           ← orchestration layer
│   ├── fundamentals/
│   │   ├── models/             ← FundamentalsRecord, EnrichedFundamentalsRecord, FundamentalsHistory
│   │   ├── repositories/       ← data access layer
│   │   │   └── base/           ← abstract interfaces
│   │   ├── processors/         ← FundamentalsProcessor, FundamentalsHistoryProcessor
│   │   ├── schemas/            ← FundamentalsDataRetrieverServiceSchema
│   │   └── services/           ← FundamentalsDataRetrieverService
│   └── radar/
├── tests/
│   └── portfolio/              ← unit tests for all three portfolio processors
└── data/
    ├── catalog.json            ← static FIBRA catalog (name, frequency, sector weights)
    ├── positions.json          ← portfolio holdings
    ├── distributions.json      ← distribution payment history
    └── historical/
        └── fundamentals.json   ← quarterly KPI history per FIBRA
```

---

## UI layer

### Directory layout

| Path | Purpose |
|---|---|
| `ui/assets/` | Static files (SVG logo) |
| `ui/components/common/` | Shared components reused across all pages (`page_header`, `error_banner`) |
| `ui/components/<domain>/` | Domain-specific components (`portfolio/summary_card`, `positions_table`, `distributions_chart`) |
| `ui/pages/` | One script per application page; these are the files Streamlit runs |
| `ui/styles/theme.py` | Color constants, number formatters (`format_mxn`, `format_pct`), and CSS injection |

### How to add a new page

1. Create `ui/pages/<name>.py`. Follow the page convention:
   - Call `render_page_header("Title", "icon")` at the top.
   - Wrap the service call in `@st.cache_data(ttl=300)`.
   - Check `result.status`; call `render_error_banner()` + `st.stop()` on error.
   - Render components section by section with `st.divider()`.
2. Register it in `app.py` inside `st.navigation([…])`:
   ```python
   st.Page("ui/pages/<name>.py", title="Page Title", icon="emoji")
   ```

### How to add a new component

1. Create `ui/components/<domain>/<component_name>.py`.
2. Expose a single `render_<component_name>(...)` function.
3. Accept only the typed data the component needs — no service or repository calls inside.
4. Import all formatters and colors from `ui.styles.theme`; never redefine them locally.

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

### `data/catalog.json`

The static FIBRA catalog — source of truth for FIBRA metadata and sector exposure weights.
The catalog drives the `Fibra` domain model and is consumed by both the Portfolio and Fundamentals pipelines.

```json
{
  "sectors": ["Industrial", "Comercial", "Oficinas", "Hotelero", "Hipotecario", "Educativo", "Almacenaje"],
  "fibras": [
    {
      "ticker": "FMTY14",
      "name": "Fibra Mty",
      "payment_frequency": "Monthly",
      "sector_exposure": [
        {"sector": "Industrial", "weight": 0.88},
        {"sector": "Oficinas",   "weight": 0.10},
        {"sector": "Comercial",  "weight": 0.02}
      ]
    }
  ]
}
```

| Field | Description |
|---|---|
| `sectors` | Exhaustive list of valid sector names |
| `ticker` | BMV ticker without the `.MX` suffix |
| `name` | Full display name of the FIBRA |
| `payment_frequency` | `"Monthly"` or `"Quarterly"` |
| `sector_exposure` | List of `{sector, weight}` pairs; weights must sum to 1.0 |
| `sector_exposure[].sector` | Sector name — must be one of the values in `sectors` |
| `sector_exposure[].weight` | Fraction of GLA belonging to this sector (0.0–1.0) |

To add a new FIBRA: append a new object to the `"fibras"` array. All positions and
fundamentals records that reference this ticker will be matched automatically.

---

### `data/historical/fundamentals.json`

Quarterly KPI history per FIBRA, manually populated from each FIBRA's quarterly reports.
All monetary values are in MXN; area values are in m².

```json
{
  "fundamentals": [
    {
      "ticker": "DANHOS13",
      "period": "1T2021",
      "report_date": "2021-03-31",
      "total_revenues": 1026081415,
      "noi": 846464090,
      "ebitda": 661660469,
      "ffo": 583299253,
      "affo": 612406341,
      "distribution_per_cbfi": 0.4,
      "gross_leasable_area_m2": 891800,
      "cbfis_outstanding": 1493866919,
      "total_equity": 59657284544,
      "total_debt": 7453116781,
      "financial_debt": 7453116781,
      "total_assets": 67110401325,
      "occupancy_rate": 0.852,
      "usd_mxn_exchange_rate": null
    }
  ]
}
```

| Field | Description |
|---|---|
| `ticker` | BMV ticker matching a FIBRA in `catalog.json` |
| `period` | Reporting quarter in `QT{YEAR}` format (e.g. `"1T2021"` = Q1 2021) |
| `report_date` | Last day of the quarter covered by the report (`YYYY-MM-DD`) |
| `total_revenues` | Total revenues for the quarter (MXN) |
| `noi` | Net Operating Income for the quarter (MXN) |
| `ebitda` | EBITDA for the quarter (MXN) |
| `ffo` | Funds From Operations for the quarter (MXN) |
| `affo` | Adjusted Funds From Operations for the quarter (MXN) |
| `distribution_per_cbfi` | Distribution declared for the quarter per CBFI (MXN) |
| `gross_leasable_area_m2` | Total gross leasable area at end of period (m²) |
| `cbfis_outstanding` | CBFIs in circulation at end of period |
| `total_equity` | Total stockholders' equity (MXN) |
| `total_debt` | Total financial obligations including lease liabilities (MXN) |
| `financial_debt` | Interest-bearing financial debt only (MXN) — currently equals `total_debt`; will be corrected when accurate data is available |
| `total_assets` | Total assets (MXN) |
| `occupancy_rate` | Occupancy rate as a decimal (e.g. `0.852` = 85.2%) |
| `usd_mxn_exchange_rate` | Exchange rate used in the report, or `null` if not applicable |

To add a new quarterly record: append a new object to the `"fundamentals"` array.

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
sector_contribution(position, s)  = p.market_value × sector_exposure.weight  (per matching sector)
sector_share.weight(sector)       = sum(sector_contribution across all positions) / total_market_value
```

`positions_share` always sums to exactly 1.0 across all positions. Only sectors with a non-zero contribution are included in `sector_shares`; it sums to exactly 1.0 when all positions have `sector_exposure` weights summing to 1.0.

### Fundamentals pipeline (`FundamentalsProcessor` → `EnrichedFundamentalsRecord`)

**Operational metrics:**
```
noi_margin              = noi / total_revenues
ebitda_margin           = ebitda / total_revenues
revenue_per_m2          = total_revenues / gross_leasable_area_m2
affo_per_m2             = affo / gross_leasable_area_m2
```

**Per CBFI:**
```
ffo_per_cbfi            = ffo / cbfis_with_rights
affo_per_cbfi           = affo / cbfis_with_rights
nav_per_cbfi            = total_equity / cbfis_outstanding
```

> **`cbfis_outstanding` vs `cbfis_with_rights`**
> `cbfis_outstanding` is the total CBFIs in circulation at quarter close — used for balance-sheet
> metrics (`market_cap`, `nav_per_cbfi`). `cbfis_with_rights` is the CBFIs that held economic
> rights during the period; it may differ in quarters with mid-period capital raises or buybacks.
> For all existing historical records the two values are equal.

**Capital structure:**
```
ltv                     = financial_debt / total_assets
affo_payout_ratio       = (distribution_per_cbfi × cbfis_outstanding) / affo
```

**Market metrics (null when market_price is None):**
```
market_cap              = market_price × cbfis_outstanding
price_to_ffo            = market_price / ffo_per_cbfi
price_to_affo           = market_price / affo_per_cbfi
dividend_yield          = (distribution_per_cbfi × 4) / market_price
price_to_nav            = market_price / nav_per_cbfi
```

`dividend_yield` annualises the quarterly distribution (×4). For monthly payers the formula remains the same — the declared `distribution_per_cbfi` field stores the quarterly equivalent amount from the quarterly report.

### Fundamentals aggregation (`FundamentalsHistoryProcessor` → `FundamentalsHistory`)

```
records          = all EnrichedFundamentalsRecord sorted by (ticker asc, year asc, quarter asc)
latest_by_ticker = most recent record per ticker, keyed by ticker string.
                   None if no record exists for a catalog ticker.
fibras           = list[Fibra] sourced from the catalog
```

Period sort order is determined by parsing `"QT{YEAR}"` into `(year, quarter)` integer pairs — never lexicographically. Every ticker from the catalog appears as a key in `latest_by_ticker`; tickers with no history have the value `None`.

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
- `modules/common/` — `Sector`, `SectorExposure`, `Fibra`, `PaymentFrequency`, `MarketPrice`, `ServiceStatus`; catalog and market price repositories (`JsonCatalogReadRepository`, `YFinanceMarketPriceReadRepository`)
- `modules/portfolio/` — full pipeline: models (raw + enriched + `Portfolio` with `SectorShare`), repositories, three processors, service, schema
- `modules/fundamentals/` — full pipeline: models (`FundamentalsRecord`, `EnrichedFundamentalsRecord`, `FundamentalsHistory`), repositories, two processors (`FundamentalsProcessor`, `FundamentalsHistoryProcessor`), service, schema
- `data/catalog.json` and `data/historical/fundamentals.json` populated with real data
- Unit test suite — 62 tests: 37 covering all three portfolio processors (`tests/portfolio/`), 25 covering both fundamentals processors (`tests/fundamentals/`)
- Portfolio page (`ui/pages/portfolio.py`) — summary metrics, positions table, allocation chart, distributions history

**Next:**
- Fundamentals page (`ui/pages/fundamentals.py`)
