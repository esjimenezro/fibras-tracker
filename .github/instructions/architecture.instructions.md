---
applyTo: "modules/**/*.py,ui/**/*.py,scripts/**/*.py"
---

# Architecture rules — fibras-tracker

Verified against the actual codebase, not assumed. Layer flow:

```
ui/pages/ → modules/*/services/ → modules/*/repositories/ + modules/*/processors/ → modules/*/models/, schemas/
```

Each rule below is enforced with zero known exceptions unless its own "Known debt" note says
otherwise.

## Rule 1 — Components never call services or repositories

`ui/components/**` render functions receive only `.models`/`.schemas` instances the page already
fetched. They must never import `modules.*.services` or `modules.*.repositories`.

**Correct** (`ui/components/fundamentals/detail_header.py` pattern):
```python
def render_detail_header(
    record: EnrichedFundamentalsRecord,
    fibra: Fibra,
    prior_year_record: Optional[EnrichedFundamentalsRecord],
) -> None:
    """Render the KPI header. Pure — no service or repository calls inside."""
    ...
```
**Typical violation** (do not let this pattern land):
```python
def render_detail_header(ticker: str) -> None:
    result = FundamentalsDataRetrieverService().run()  # ✗ component fetching its own data
    ...
```
Flag any new `import` of `modules.*.services` or `modules.*.repositories` inside `ui/components/`.

## Rule 2 — Pages call services, never repositories

`ui/pages/**` may only call a `<Module>Service`. Verified with zero exceptions in both
`fundamentals.py` and `portfolio.py` today.

**Correct** (`ui/pages/fundamentals.py`):
```python
@st.cache_data(ttl=300, show_spinner="Cargando datos fundamentales...")
def _load_fundamentals() -> FundamentalsDataRetrieverServiceSchema:
    return FundamentalsDataRetrieverService().run()
```
**Typical violation**:
```python
records = JsonFundamentalsReadRepository().retrieve_data()  # ✗ page bypassing the service layer
```

## Rule 3 — Services: constructor-injected repositories, processors instantiated inside, never raise

A service's `__init__` takes one `Optional[BaseXRepository] = None` parameter per repository
dependency, defaulting to the concrete implementation. Processors are created inside `__init__`,
never passed in. The public `run()`/`stream()` wraps the whole pipeline in
`try/except Exception` and returns a typed `<ServiceName>Schema` — it never lets an exception
escape.

**Correct** — the repo's own reference implementation,
`modules/fundamentals/services/fundamentals_data_retriever_service.py`:
```python
class FundamentalsDataRetrieverService:
    def __init__(
        self,
        fundamentals_repository: Optional[BaseFundamentalsReadRepository] = None,
        market_price_repository: Optional[BaseMarketPriceReadRepository] = None,
        catalog_repository: Optional[BaseCatalogReadRepository] = None,
        inflation_repository: Optional[BaseInflationReadRepository] = None,
    ) -> None:
        self._fundamentals_repository = fundamentals_repository or JsonFundamentalsReadRepository()
        self._market_price_repository = market_price_repository or YFinanceMarketPriceReadRepository()
        self._catalog_repository = catalog_repository or JsonCatalogReadRepository()
        self._inflation_repository = inflation_repository or JsonInflationReadRepository()
        self._fundamentals_processor = FundamentalsProcessor()
        self._annual_processor = AnnualFundamentalsProcessor()
        self._history_processor = FundamentalsHistoryProcessor()
```
**Typical violation**:
```python
def __init__(self, fundamentals_repository: BaseFundamentalsReadRepository):  # ✗ required, no default
    self._fundamentals_repository = fundamentals_repository
    self._processor = FundamentalsProcessor(repository=fundamentals_repository)  # ✗ processor takes a repo

def run(self) -> FundamentalsHistory:  # ✗ returns the raw model, not a schema
    return self._build_history()  # ✗ an exception here reaches the caller
```

## Rule 4 — Repositories: no constructor arguments, one `retrieve_data(...)`

Concrete repository classes take no `__init__` at all (verified: zero `__init__` methods across
every file in `modules/*/repositories/`). Anything dynamic is a parameter of `retrieve_data`.

**Correct** (`modules/wiki/repositories/file_system_wiki_index_read_repository.py` pattern):
```python
class FileSystemWikiIndexReadRepository(BaseWikiIndexReadRepository):
    def retrieve_data(self, ticker: str) -> str:
        ...
```
**Typical violation**:
```python
class FileSystemWikiIndexReadRepository(BaseWikiIndexReadRepository):
    def __init__(self, ticker: str):  # ✗ dynamic value baked into the constructor
        self._ticker = ticker

    def retrieve_data(self) -> str:
        ...
```
Switching JSON → API for any entity must require touching only the concrete repository class —
never `services/`, `processors/`, or `pages/`. Flag any change to a service/processor/page made
"to support a new data source" instead of a change confined to a repository.

## Rule 5 — Processors: stateless, fail loud, no data-source knowledge

No `__init__`, no I/O, no imports of `modules.*.repositories`. Invalid or empty input raises
(usually `ValueError`) rather than silently defaulting.

**Correct** (`modules/portfolio/processors/positions_processor.py`):
```python
if market_price is None:
    raise ValueError(f"No market price found for ticker '{position.ticker}'")
if fibra is None:
    raise ValueError(f"No catalog entry found for ticker '{position.ticker}'")
```
**Typical violation**:
```python
market_price = prices_by_ticker.get(position.ticker, MarketPrice(ticker=position.ticker, price=0.0))
# ✗ silently fabricates a zero price instead of failing loud on missing data
```

## Rule 6 — Models carry no behavior

`modules/*/models/*.py` are plain Pydantic `BaseModel` subclasses: no methods, no
`@computed_field`, no `@field_validator`/`@model_validator`, no `Field(...)` constraints. Verified
— none exist anywhere in this repo. Invalid-input handling belongs in the processor or service
that acts on the model, not in the model itself.

**Correct**:
```python
class WikiQueryRequest(BaseModel):
    tickers: list[str]
    primary_ticker: Optional[str] = None
    question: str
    history: list[WikiChatMessage] = []
```
**Typical violation**:
```python
class WikiQueryRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=1)  # ✗ validation logic in the model

    @field_validator("tickers")
    @classmethod
    def _check_primary(cls, v):  # ✗ a validator method on a model
        ...
```
If a diff needs to reject an invalid model state (e.g. an empty `tickers` list), the fix belongs
in the consuming service, raising before use — see `WikiQueryService.stream()`'s
`if not request.tickers: raise ValueError(...)` guard.

## Rule 7 — Import order and package-level exports

- Every class is exported from its package's `__init__.py` (`__all__`); import the package, not
  the file.
- One import per line.
- Groups, one blank line between: (1) stdlib, (2) third-party, (3) internal — `modules/common/`
  first, then other internal imports, in a stable order.

**Correct**:
```python
import json
from typing import Optional

import streamlit as st

from modules.common.schemas import ServiceStatus
from modules.fundamentals.services import FundamentalsDataRetrieverService
```

### Known architecture debt

`modules/wiki/services/wiki_query_service.py` currently violates Rule 7: the internal-import
block interleaves `modules.fundamentals.repositories(.base)` imports in the middle of a run of
`modules.wiki.repositories.base` imports instead of grouping `modules.fundamentals` before
`modules.wiki` (or otherwise keeping a stable, sorted order). This is **not** the pattern to
copy — treat it as a pre-existing defect. Fix opportunistically if touching that import block;
do not use it as precedent for a new file's import order.
