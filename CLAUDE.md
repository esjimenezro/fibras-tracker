# FIBRAs Tracker — Context for Claude Code

## What is this project

A personal Python + Streamlit application to track a portfolio of Mexican FIBRAs (Fideicomisos de Infraestructura y Bienes Raíces). FIBRAs are the Mexican equivalent of REITs, listed on the BMV (Mexican Stock Exchange).

## Development principles

- **Small, verifiable features** — never full modules at once
- Confirm each piece works before moving to the next
- Ask before implementing if there is any ambiguity in the requirement

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
│   │   ├── repositories/
│   │   ├── processors/
│   │   ├── services/
│   │   └── schemas/
│   ├── fundamentals/
│   └── radar/
└── data/
    ├── portfolio.json
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
- `repositories/` implements data access. Each domain has a `base.py` with an abstract interface (ABC).
- `processors/` contains pure logic: calculations, aggregations, filters. No knowledge of data sources.
- `schemas/` defines data contracts between layers using Pydantic.

## Repository pattern

The goal is that switching the data source (JSON → API) requires no changes to `services/`, `processors/`, or `pages/`. Only a new concrete repository implementation is added. The contract is enforced by `schemas/`.

Repository structure per domain:

- `base.py` → abstract interface (ABC)
- `json_repo.py` → concrete implementation for JSON files
- `api_repo.py` → future implementation for external APIs

## Stack

- Python 3.11+
- Streamlit
- Pydantic (schemas and validation)
- yfinance (market prices, tickers with `.MX` suffix)
- pandas (transformations)

## FIBRAs in the portfolio

| Ticker    | Name           | Sector                    | Frequency |
|-----------|----------------|---------------------------|-----------|
| FMTY14    | Fibra Mty      | Industrial / Offices      | Monthly   |
| DANHOS13  | Fibra Danhos   | Mixed-use / Retail        | Quarterly |
| FIBRAPL14 | Fibra Prologis | Industrial / Logistics    | Quarterly |
| FSHOP13   | Fibra Shop     | Retail / Shopping centers | Quarterly |

yfinance tickers: append `.MX` suffix (e.g. `FMTY14.MX`)

## Data structure — portfolio.json

```json
{
  "posiciones": [
    {
      "ticker": "FMTY14",
      "nombre": "Fibra Mty",
      "sector": "Industrial / Offices",
      "cbfis": 1500,
      "precio_promedio_compra": 9.58,
      "frecuencia_pago": "Monthly",
      "distribuciones": [
        {
          "fecha_pago": "2026-03-06",
          "monto_por_cbfi_reembolso": 0.0331,
          "monto_por_cbfi_resultado": 0.0483,
          "cbfis_al_momento": 1500
        }
      ]
    }
  ]
}
```

Distribution fields:

- `fecha_pago`: date the payment was credited by the broker
- `monto_por_cbfi_reembolso`: capital reimbursement (not taxable when received)
- `monto_por_cbfi_resultado`: fiscal result (subject to 30% ISR withholding)
- `cbfis_al_momento`: CBFIs held at the time of payment

## Current project state

- Directory structure created with empty files
- `portfolio.json` populated with real portfolio data
- No layer has any implementation yet
- **Next step**: define Pydantic schemas in `modules/portfolio/schemas/`

## Agreed implementation order

1. Schemas (`modules/portfolio/schemas/`)
2. Repository interface (`modules/portfolio/repositories/base.py`)
3. JSON repository implementation
4. Processors (calculations)
5. Service
6. Page (UI)

Implement and verify one layer at a time before moving to the next.