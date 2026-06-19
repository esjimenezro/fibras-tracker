# FIBRAs Tracker

A personal Streamlit application (branded **FIBRALens**) to track and analyze Mexican FIBRAs. It fetches live market prices via Yahoo Finance, reads distribution and position history from local JSON files, and maintains a quarterly fundamentals history per FIBRA — computing per-position, portfolio-level, and fundamental metrics from all three, plus inflation-adjusted growth analysis.

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
- Allocation donut charts: portfolio weight per FIBRA and per sector (sectors below 2% grouped into "Otros")
- Positions table: per-FIBRA breakdown with colour-coded return columns (green/red)
- Distributions history: stacked bar chart grouped by FIBRA, plus per-period expanders showing gross fiscal income, reimbursement, ISR withholding, and net income

**Fundamentals analysis**
- Quarterly KPI history per FIBRA, enriched into operational margins, per-m² and per-CBFI ratios, capital structure (LTV, payout), and market multiples (P/FFO, P/AFFO, dividend yield, P/NAV)
- Annual aggregation of complete years (all four quarters), with partial-sum handling for distributions
- Per-FIBRA growth metrics: AFFO/CBFI, distribution, revenue, and NAV CAGRs, year-over-year growth counts, and distribution growth vs. Mexican inflation

**Fundamentals page (`ui/pages/fundamentals.py`)**
- **Detalle tab** — per-FIBRA KPI dashboard (operation/debt, generation/distribution per CBFI, market valuation, contract predictability) with traffic-light icons and year-over-year deltas, plus a unified indicator chart with a Trimestral/Anual toggle, threshold bands, and an inflation reference line
- **Comparativa tab** — cross-FIBRA evaluative table (Propósito / Predictibilidad / Contratos) and a multi-FIBRA comparison chart with direct and normalized (base-1000) modes

---

## Architecture

### Layer structure

```
pages/ → services/ → repositories/
            ↓
         processors/
```

- **`pages/`** call services only — no direct repository or data access.
- **`services/`** orchestrate: fetch raw data from repositories, transform it via processors, and return a typed result schema to the page.
- **`repositories/`** handle data access with no business logic. Abstract base classes live in `repositories/base/`; concrete implementations are named `<source>_<entity>_read_repository.py`.
- **`processors/`** contain pure business logic — calculations, aggregations, transformations. They have no knowledge of data sources.
- **`models/`** define Pydantic data contracts. No methods, no computed fields.

### Data transformation pipeline

**Portfolio**

```
Distribution
  → [DistributionsProcessor] → EnrichedDistribution

Position + MarketPrice + Fibra + list[EnrichedDistribution]
  → [PositionsProcessor] → EnrichedPosition

list[EnrichedPosition]
  → [PortfolioProcessor] → Portfolio  (with PositionShare + SectorShare)
```

**Fundamentals**

```
list[FundamentalsRecord] + list[MarketPrice]
  → [FundamentalsProcessor] → list[EnrichedFundamentalsRecord]

list[EnrichedFundamentalsRecord]
  → [AnnualFundamentalsProcessor] → list[AnnualFundamentalsRecord]

list[EnrichedFundamentalsRecord] + list[Fibra]
    + list[AnnualFundamentalsRecord] + list[InflationRecord]
  → [FundamentalsHistoryProcessor] → FundamentalsHistory  (with per-FIBRA FibraMetrics)
```

### Repository pattern

Each entity has an abstract interface in `repositories/base/` that defines the `retrieve_data()` contract. Concrete implementations provide the actual data source (JSON file, Yahoo Finance, etc.). Swapping data sources requires only a new concrete implementation — services, processors, and pages remain untouched.

---

## Project structure

```
fibras-tracker/
├── app.py                      ← Streamlit entry point (registers pages via st.navigation)
├── config.py                   ← file paths, FIBRALens branding, business constants
├── ui/
│   ├── assets/                 ← static files (SVG logo)
│   ├── components/
│   │   ├── common/             ← shared: page_header, error_banner
│   │   ├── portfolio/          ← summary_card, positions_table, distributions_chart, sector_chart
│   │   └── fundamentals/       ← detail_header, detail_chart, comparison_table, comparison_chart
│   ├── pages/                  ← Streamlit page scripts (one per module)
│   │   ├── home.py
│   │   ├── portfolio.py
│   │   ├── fundamentals.py
│   │   └── radar.py            ← placeholder ("Próximamente")
│   └── styles/
│       └── theme.py            ← color constants, number formatters, CSS injection
├── modules/
│   ├── common/
│   │   ├── models/             ← Sector, SectorExposure, Fibra, PaymentFrequency, MarketPrice, InflationRecord
│   │   ├── repositories/       ← catalog, market price, and inflation repositories
│   │   │   └── base/           ← abstract interfaces
│   │   └── schemas/            ← ServiceStatus (shared across all modules)
│   ├── portfolio/
│   │   ├── models/             ← Position, EnrichedPosition, Distribution, EnrichedDistribution,
│   │   │                         Portfolio (PositionShare, SectorShare)
│   │   ├── repositories/       ← data access layer
│   │   │   └── base/           ← abstract interfaces
│   │   ├── processors/         ← DistributionsProcessor, PositionsProcessor, PortfolioProcessor
│   │   ├── schemas/            ← PortfolioDataRetrieverServiceSchema
│   │   └── services/           ← PortfolioDataRetrieverService
│   ├── fundamentals/
│   │   ├── models/             ← FundamentalsRecord, EnrichedFundamentalsRecord,
│   │   │                         AnnualFundamentalsRecord, FibraMetrics, FundamentalsHistory
│   │   ├── repositories/       ← data access layer
│   │   │   └── base/           ← abstract interfaces
│   │   ├── processors/         ← FundamentalsProcessor, AnnualFundamentalsProcessor,
│   │   │                         FundamentalsHistoryProcessor
│   │   ├── schemas/            ← FundamentalsDataRetrieverServiceSchema
│   │   └── services/           ← FundamentalsDataRetrieverService
│   └── radar/                  ← (empty — reserved)
├── tests/
│   ├── portfolio/              ← unit tests for all three portfolio processors (37 tests)
│   └── fundamentals/           ← unit tests for all three fundamentals processors (86 tests)
└── data/
    ├── catalog.json            ← static FIBRA catalog (name, frequency, sector weights)
    ├── positions.json          ← portfolio holdings
    ├── distributions.json      ← distribution payment history
    ├── fundamentals.json       ← quarterly KPI history per FIBRA
    └── inflation.json          ← annual Mexican inflation (INPC) history
```

---

## UI layer

### Directory layout

| Path | Purpose |
|---|---|
| `ui/assets/` | Static files (SVG logo) |
| `ui/components/common/` | Shared components reused across all pages (`page_header`, `error_banner`) |
| `ui/components/portfolio/` | `summary_card`, `positions_table`, `distributions_chart`, `sector_chart` |
| `ui/components/fundamentals/` | `detail_header`, `detail_chart`, `comparison_table`, `comparison_chart` |
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

### Fundamentals page structure

The fundamentals page (`ui/pages/fundamentals.py`) calls `FundamentalsDataRetrieverService().run()` and renders two tabs:

**Detalle tab**
1. A FIBRA selectbox.
2. `render_detail_header(record, fibra, prior_year_record)` — four KPI sections (operation & debt; generation & distribution per CBFI; market valuation; distribution predictability), with traffic-light icons on threshold metrics (margins, occupancy, LTV) and year-over-year deltas on FFO/AFFO per CBFI and NAV.
3. `render_detail_chart(records, annual_records, inflation_records)` — a single **KPI_CONFIG**-driven indicator selector plus a Trimestral/Anual radio toggle. KPI_CONFIG is one dictionary that defines every selectable indicator (label, quarterly/annual source fields, chart `kind`, format, thresholds). Three chart kinds are rendered: `single` (one line, optional threshold bands and inflation reference), `combined` (multi-line with a Total/Margen/Por CBFI mode toggle), and `dual_axis` (two Y-axes).

**Comparativa tab**
1. `render_comparison_table(latest_by_ticker, fibras, fibra_metrics, annual_records)` — an HTML evaluative table grouped into three supercolumns: **Propósito** (constant / growing / vs-inflation distribution), **Predictibilidad** (NAV, revenue, AFFO per-CBFI growth; payout ratio; occupancy; LTV), and **Contratos** (WALE, top tenant, top-10 tenants). FIBRAs with fewer than three complete annual years are greyed and suffixed with `*`.
2. `render_comparison_chart(annual_records, fibras, inflation_records)` — a multi-FIBRA, multi-indicator chart. Direct indicators (payout ratio, LTV, occupancy) plot raw values; normalized indicators (distribution, AFFO, revenue, NAV per CBFI) rebase every series to **1000** at a common base year, and distribution adds an inflation reference line.

---

## Data files

### `data/positions.json`

One entry per FIBRA held in the portfolio.

```json
{
  "positions": [
    {
      "ticker": "FMTY14",
      "cbfis": 1500,
      "average_purchase_cost": 9.586
    }
  ]
}
```

| Field | Description |
|---|---|
| `ticker` | BMV ticker without the `.MX` suffix; matches a FIBRA in `catalog.json` |
| `cbfis` | Number of CBFIs (units) currently held |
| `average_purchase_cost` | Broker-reported weighted average cost per CBFI, in MXN |

> **Note:** Name, payment frequency, and sector exposure are not stored here — they are resolved from `catalog.json` by ticker during enrichment. `average_purchase_cost` is the value reported by your broker and is already cost-adjusted. Do not manually subtract reimbursements from it — those are tracked separately in `distributions.json`.

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
      "reimbursement_total": 49.65,
      "fiscal_result_total": 72.45
    }
  ]
}
```

| Field | Description |
|---|---|
| `ticker` | BMV ticker matching a position in `positions.json` |
| `payment_date` | Date the payment was credited by the broker (`YYYY-MM-DD`) |
| `reimbursement_total` | Total capital reimbursement received in MXN — not taxable when received |
| `fiscal_result_total` | Total fiscal result income received in MXN — subject to 30% ISR withholding |

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
      "tenant_concentration_basis": "ingresos_totales",
      "sector_exposure": [
        {"sector": "Industrial", "weight": 0.80},
        {"sector": "Oficinas",   "weight": 0.19},
        {"sector": "Comercial",  "weight": 0.01}
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
| `tenant_concentration_basis` | *(optional)* methodology each FIBRA uses to report tenant concentration — e.g. `"ingresos_totales"`, `"renta_fija"`, `"renta_neta_efectiva"`. Used for context on the `top_tenant_pct` / `top10_tenants_pct` fundamentals fields |
| `sector_exposure` | List of `{sector, weight}` pairs; weights must sum to 1.0 |
| `sector_exposure[].sector` | Sector name — must be one of the values in `sectors` |
| `sector_exposure[].weight` | Fraction of GLA belonging to this sector (0.0–1.0) |

To add a new FIBRA: append a new object to the `"fibras"` array. All positions and
fundamentals records that reference this ticker will be matched automatically.

---

### `data/fundamentals.json`

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
      "cbfis_with_rights": 1493866919,
      "total_equity": 59657284544,
      "total_debt": 7453116781,
      "financial_debt": 5730000000,
      "total_assets": 67110401325,
      "occupancy_rate": 0.852,
      "usd_mxn_exchange_rate": null,
      "wale": null,
      "top_tenant_pct": null,
      "top10_tenants_pct": null
    }
  ]
}
```

Every field except `ticker`, `period`, and `report_date` is optional; any field whose value is unknown for a given quarter is set to `null`, and the processor propagates `null` through any derived metric that depends on it.

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
| `cbfis_outstanding` | Total CBFIs in circulation at quarter close — used for balance-sheet metrics (`nav_per_cbfi`, `market_cap`) |
| `cbfis_with_rights` | CBFIs that held economic rights during the period — used for per-CBFI flow ratios (FFO/AFFO/revenue/NOI/EBITDA per CBFI, `total_distribution`). May differ from `cbfis_outstanding` in quarters with mid-period capital raises or buybacks; equal for all current records |
| `total_equity` | Total stockholders' equity / NAV (MXN) |
| `total_debt` | Total financial obligations including lease liabilities (MXN) |
| `financial_debt` | Interest-bearing financial debt only (MXN) — used for `ltv`, **not** `total_debt`. Some historical records still mirror `total_debt`; will be corrected as accurate data becomes available |
| `total_assets` | Total assets (MXN) |
| `occupancy_rate` | Occupancy rate as a decimal (e.g. `0.852` = 85.2%) |
| `usd_mxn_exchange_rate` | USD/MXN exchange rate at period end, or `null` if not reported |
| `wale` | Weighted Average Lease Expiry in years, or `null` where not reported |
| `top_tenant_pct` | Concentration of the largest single tenant as a decimal, over the base named by the catalog's `tenant_concentration_basis` |
| `top10_tenants_pct` | Cumulative concentration of the top 10 tenants as a decimal, over the same base |

To add a new quarterly record: append a new object to the `"fundamentals"` array.

---

### `data/inflation.json`

Annual Mexican inflation history (year-over-year change of the INPC, December to December), used by the fundamentals pipeline to compute inflation-adjusted distribution growth.

```json
{
  "metadata": {
    "source": "INEGI / Banxico",
    "methodology": "Variación anual del INPC, diciembre a diciembre",
    "base": "2ª quincena julio 2018 para 2016 en adelante; INEGI histórico para 2010-2015"
  },
  "inflation": [
    {"year": 2010, "annual_inflation": 0.044},
    {"year": 2025, "annual_inflation": 0.0369}
  ]
}
```

| Field | Description |
|---|---|
| `metadata` | Free-form provenance block (`source`, `methodology`, `base`); not parsed by the model |
| `inflation[].year` | Calendar year |
| `inflation[].annual_inflation` | Year-over-year inflation as a decimal (e.g. `0.0421` = 4.21%) |

Only the `inflation` array is read (into `InflationRecord`). To extend the series, append a `{year, annual_inflation}` object. Coverage must span the full range of complete fundamentals years for `cagr_inflation` to be computed for a FIBRA.

---

## Business rules

Tax constants are defined in `config.py`:

```python
FISCAL_RESULT_WITHHOLDING_RATE = 0.30  # 30% ISR withholding on fiscal result income
```

### Distributions pipeline (`DistributionsProcessor` → `EnrichedDistribution`)

```
gross_fiscal_result_income = fiscal_result_total
net_reimbursement_income   = reimbursement_total
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
cbfis_per_m2            = cbfis_outstanding / gross_leasable_area_m2
```

**Per CBFI:**
```
ffo_per_cbfi            = ffo / cbfis_with_rights
affo_per_cbfi           = affo / cbfis_with_rights
revenue_per_cbfi        = total_revenues / cbfis_with_rights
noi_per_cbfi            = noi / cbfis_with_rights
ebitda_per_cbfi         = ebitda / cbfis_with_rights
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
affo_payout_ratio       = distribution_per_cbfi / affo_per_cbfi
total_distribution      = distribution_per_cbfi × cbfis_with_rights
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
records              = all EnrichedFundamentalsRecord sorted by (ticker asc, year asc, quarter asc)
latest_by_ticker     = most recent record per ticker; None if the ticker has no record
prior_year_by_ticker = record for the same quarter one year before the latest; None if absent
fibra_metrics        = per-FIBRA FibraMetrics, keyed by ticker (see below)
fibras               = list[Fibra] sourced from the catalog
annual_records       = list[AnnualFundamentalsRecord] (passed through from the annual processor)
inflation_records    = list[InflationRecord] (passed through, full inflation history)
```

Period sort order is determined by parsing `"QT{YEAR}"` into `(year, quarter)` integer pairs — never lexicographically. Every ticker from the catalog appears as a key in `latest_by_ticker`, `prior_year_by_ticker`, and `fibra_metrics`; tickers with no history map to `None` (or a `FibraMetrics` with `periods_count = 0`).

### Per-FIBRA metrics (`FibraMetrics`, one per ticker inside `fundamentals_history.fibra_metrics`)

Computed from the full quarterly series plus the annual records and inflation history.

```
periods_count   = number of records for the ticker
years_of_history = (last_year + (last_quarter - 1)/4) - (first_year + (first_quarter - 1)/4)
                   (0 when periods_count is 0 or 1)
```

**AFFO growth** (all `None` when fewer than 4 records exist, or any source value is `None`,
or `years_of_history` is 0):
```
affo_first, affo_latest             = AFFO (MXN) in the earliest / most recent record
cagr_affo_total       = (affo_latest / affo_first) ** (1 / years_of_history) - 1
affo_per_cbfi_first, affo_per_cbfi_latest
cagr_affo_per_cbfi    = (affo_per_cbfi_latest / affo_per_cbfi_first) ** (1 / years_of_history) - 1
```

**Annual counts** (all `None` when no annual data; year-over-year counts skip the first year and any
`None` pair):
```
total_annual_years           = number of complete years (all four quarters present)
years_with_distribution      = count of years where distribution_per_cbfi_annual is not None and > 0
years_distribution_grew      = count of YoY increases in distribution_per_cbfi_annual
years_affo_per_cbfi_grew     = count of YoY increases in affo_per_cbfi_annual
years_nav_per_cbfi_grew      = count of YoY increases in the nav_per_cbfi Q4 snapshot
years_revenue_per_cbfi_grew  = count of YoY increases in revenue_per_cbfi_annual
```

**Annual CAGRs** (all `None` when fewer than 2 annual records, a boundary value is `None`, or
`years = last_year - first_year` is 0):
```
cagr_distribution_per_cbfi = (last / first) ** (1 / years) - 1   over distribution_per_cbfi_annual
cagr_revenue_per_cbfi      = (last / first) ** (1 / years) - 1   over revenue_per_cbfi_annual
cagr_inflation             = (Π (1 + annual_inflation[y]) for y in [first_year, last_year)) ** (1/years) - 1
                             (None if any year in the range is missing from inflation_records)
distribution_vs_inflation  = cagr_distribution_per_cbfi - cagr_inflation
```

`cagr_inflation` is the geometric mean annual inflation across the FIBRA's complete-year span;
`distribution_vs_inflation` is the headline "did distributions beat inflation?" figure used by the
Comparativa tab.

### Annual aggregation (`AnnualFundamentalsProcessor` → `AnnualFundamentalsRecord`)

Only years with all four quarters (Q1–Q4) present for a given ticker are included; incomplete years are omitted entirely.

**Partial-sum fields** (sum of the non-null quarters; null **only if all four quarters are None**):
```
distribution_per_cbfi_annual = partial sum of quarterly distribution_per_cbfi
total_distribution_annual    = partial sum of quarterly total_distribution
```

The two distribution fields use a partial sum because monthly payers may not report `distribution_per_cbfi` in every quarter; a single missing quarter should not nullify the annual total.

**Strict-sum fields** (null if **any** quarter value is None; integer-sourced fields cast to `int`):
```
ffo_per_cbfi_annual          = sum of quarterly ffo_per_cbfi
affo_per_cbfi_annual         = sum of quarterly affo_per_cbfi
revenue_per_cbfi_annual      = sum of quarterly revenue_per_cbfi
total_revenues_annual        = sum of quarterly total_revenues   (int)
noi_annual                   = sum of quarterly noi              (int)
noi_per_cbfi_annual          = sum of quarterly noi_per_cbfi
ebitda_annual                = sum of quarterly ebitda           (int)
ebitda_per_cbfi_annual       = sum of quarterly ebitda_per_cbfi
ffo_annual                   = sum of quarterly ffo              (int)
affo_annual                  = sum of quarterly affo             (int)
```

**Recomputed margins** (computed from annual sums, not averaged from quarterly margins; null if denominator is None or zero):
```
noi_margin_annual    = noi_annual / total_revenues_annual
ebitda_margin_annual = ebitda_annual / total_revenues_annual
```

**Q4 snapshot fields** (value taken from the Q4 record; passed through as-is):
```
nav_per_cbfi, ltv, occupancy_rate, wale, top_tenant_pct, top10_tenants_pct,
gross_leasable_area_m2, cbfis_outstanding, cbfis_per_m2
```

**Average fields** (null if any quarter value is None):
```
affo_payout_ratio_avg = mean of quarterly affo_payout_ratio
```

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
- `modules/common/` — `Sector`, `SectorExposure`, `Fibra`, `PaymentFrequency`, `MarketPrice`, `InflationRecord`, `ServiceStatus`; catalog, market price, and inflation repositories (`JsonCatalogReadRepository`, `YFinanceMarketPriceReadRepository`, `JsonInflationReadRepository`)
- `modules/portfolio/` — full pipeline: models (raw + enriched + `Portfolio` with `PositionShare` and `SectorShare`), repositories, three processors, service, schema
- `modules/fundamentals/` — full pipeline: models (`FundamentalsRecord`, `EnrichedFundamentalsRecord`, `AnnualFundamentalsRecord`, `FibraMetrics`, `FundamentalsHistory`), repository, three processors (`FundamentalsProcessor`, `AnnualFundamentalsProcessor`, `FundamentalsHistoryProcessor`), service, schema
- All five `data/*.json` files populated with real data
- Unit test suite — 123 tests: 37 covering all three portfolio processors (`tests/portfolio/`), 86 covering all three fundamentals processors (`tests/fundamentals/`)
- Portfolio page (`ui/pages/portfolio.py`) — summary metrics, positions table, FIBRA + sector allocation donuts, distributions history
- Fundamentals page (`ui/pages/fundamentals.py`) — Detalle tab (KPI detail header + unified KPI_CONFIG indicator chart) and Comparativa tab (evaluative table + normalized comparison chart)

**Next:**
- Radar page (`ui/pages/radar.py`) — currently a "Próximamente" placeholder
