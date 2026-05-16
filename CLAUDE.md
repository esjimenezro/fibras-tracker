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
├── app.py                  ← Streamlit entry point
├── config.py               ← global constants (paths, titles)
├── pages/                  ← Streamlit front-end (one page per module)
│   ├── portfolio.py
│   ├── fundamentals.py
│   └── radar.py
├── modules/                ← business logic
│   ├── common/
│   ├── portfolio/
│   │   ├── models/          ← domain entities (Position, Distribution, Portfolio)
│   │   ├── repositories/
│   │   │   ├── base/        ← abstract interfaces (ABC)
│   │   │   ├── json_positions_read_repository.py
│   │   │   └── json_distributions_read_repository.py
│   │   ├── processors/
│   │   ├── schemas/         ← future input/output contracts
│   │   └── services/
│   ├── fundamentals/
│   └── radar/
└── data/
    ├── positions.json
    ├── distributions.json
    └── historical/
```

## Layer flow

```
pages/ → services/ → repositories/ → data source
               ↕
          processors/
```

- `pages/` only calls methods from `services/`. Never touches repos or data directly.
- `services/` orchestrates: fetches data from the repo, transforms it with the processor, returns a UI-ready result.
- `repositories/` implements data access. Abstract interfaces live in `repositories/base/`. Concrete implementations are named `json_<entity>_read_repository.py`, `api_<entity>_read_repository.py`, etc.
- `processors/` contains pure logic: calculations, aggregations, filters. No knowledge of data sources.
- `models/` defines domain entities as Pydantic models. No methods, no computed fields, no validators — pure data contracts.
- `schemas/` reserved for future input/output contracts between layers.

## Repository pattern

The goal is that switching the data source (JSON → API) requires no changes to `services/`, `processors/`, or `pages/`. Only a new concrete repository implementation is added. The contract is enforced by `schemas/`.

Repository structure per domain:

- `base/` → one abstract interface file per entity (e.g. `base_positions_read_repository.py`)
- `json_<entity>_read_repository.py` → concrete JSON implementation
- `api_<entity>_read_repository.py` → future API implementation

## Stack

- Python 3.11+
- Streamlit
- Pydantic (schemas and validation)
- yfinance (market prices, tickers with `.MX` suffix)
- pandas (transformations)

## Linting

- **Tool**: flake8
- **Max line length**: 200 characters (`max-line-length = 200` in `.flake8`)

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

## Data files

### `data/positions.json`

```json
{
  "positions": [
    {
      "ticker": "FMTY14",
      "name": "Fibra Mty",
      "sector": "Industrial / Offices",
      "cbfis": 1500,
      "average_purchase_price": 9.58,
      "payment_frequency": "Monthly"
    }
  ]
}
```

### `data/distributions.json`

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

Distribution fields:

- `payment_date`: date the payment was credited by the broker
- `reimbursement_per_cbfi`: capital reimbursement (not taxable when received)
- `fiscal_result_per_cbfi`: fiscal result (subject to 30% ISR withholding)
- `cbfis_at_time`: CBFIs held at the time of payment

## Current project state

- `data/positions.json` and `data/distributions.json` populated with real data
- Domain models implemented in `modules/portfolio/models/`
- Base read repository interfaces implemented in `modules/portfolio/repositories/base/`
- JSON read repositories implemented in `modules/portfolio/repositories/`
- **Next step**: processors (calculations)

## Agreed implementation order

1. ~~Models (`modules/portfolio/models/`)~~ ✓
2. ~~Repository interfaces (`modules/portfolio/repositories/base/`)~~ ✓
3. ~~JSON repository implementations~~ ✓
4. Processors (calculations)
5. Service
6. Page (UI)

Implement and verify one layer at a time before moving to the next.