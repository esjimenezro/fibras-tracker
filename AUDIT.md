# Repository audit — fibras-tracker (FIBRALens)

**Date:** 2026-09-19
**Scope:** whole repository at its current state (not a PR diff), produced by running the three
read-only subagents in `.claude/agents/` (`compliance-auditor`, `security-auditor`,
`architecture-auditor`) in parallel and consolidating their reports below.

## Executive summary

Overall the codebase is in good health relative to its own documented conventions (`CLAUDE.md`,
`README.md`, and the parallel `.github/instructions/` docs). No critical or high-severity security
issues, no blocking architecture violations. Findings cluster in three places:

- The less-exercised UI corners — `src/ui/pages/radar.py` (placeholder page) and the Comparativa-tab
  fundamentals components — account for most compliance violations (cross-file/private imports,
  positional args, local color constants instead of `theme.py`).
- Real, evidenced duplication of business/presentation logic that has drifted into the UI layer:
  inflation-compounding math implemented three times, and threshold-based traffic-light coloring
  implemented three different ways in `src/modules/fundamentals/` (vs. clean centralization in
  `src/modules/portfolio/`).
- Defense-in-depth gaps around model-supplied tool arguments in `src/modules/wiki/services/wiki_query_service.py`
  (currently non-exploitable — absorbed by an outer catch-all — but implicit rather than intentional).

**Counts:** Security — 0 Critical, 0 High, 2 Medium, 3 Low/informational.
Architecture — 0 blocking violations, 5 long-term debt items, 4 minor items.
Compliance — 5 clear rule violations, 3 documentation-completeness gaps, 1 naming nit,
1 already-known/acknowledged debt item, 3 minor nits.

Also note: `.github/instructions/architecture.instructions.md` now exists (it did not when this
review setup was first put together earlier in this session) — something else appears to be
concurrently writing setup/instruction files into this repo. Worth checking what that is.

---

## 1. Compliance audit — ✅ RESUELTO (2026-09-20)

*Run by: `compliance-auditor` subagent.*

**Status:** all 12 findings below (5 clear violations, 2 docstring-accuracy gaps, 1 naming nit,
1 already-documented debt item, 3 minor nits) have been fixed and verified (`flake8` clean,
223/223 tests passing) as of 2026-09-20. The "Verified compliant" section was already clean and
required no changes.

### Findings

#### Clear violations — import/code-style (CLAUDE.md "Code style")

1. ✅ **RESUELTO** — **One-import-per-line broken in 4 of 11 base repository interfaces.**
   - `src/modules/common/repositories/base/base_market_price_read_repository.py:1`
   - `src/modules/fundamentals/repositories/base/base_fundamentals_read_repository.py:1`
   - `src/modules/portfolio/repositories/base/base_distributions_read_repository.py:1`
   - `src/modules/portfolio/repositories/base/base_positions_read_repository.py:1`
   - All four write `from abc import ABC, abstractmethod` on one line. The other 7
     `base_*_read_repository.py` files correctly split this onto two lines — these 4 are outliers
     against the majority pattern.

2. ✅ **RESUELTO** — **`src/ui/pages/radar.py:3`** imports `render_page_header` from the file
   (`ui.components.common.page_header`) instead of the package (`ui.components.common`), unlike
   every other page.

3. ✅ **RESUELTO** — **`src/ui/pages/radar.py:5`** calls `render_page_header("Radar", "🔍")` with positional args instead
   of `page_title=`/`page_icon=` keywords, unlike every other page.

4. ✅ **RESUELTO** — **Cross-file, non-package imports of another component's internals:**
   - `src/ui/components/fundamentals/comparison_table.py:9-12` imports `LTV_LOWER`, `LTV_UPPER`,
     `OCC_LOWER`, `OCC_UPPER` directly from the `detail_chart` file.
   - `src/ui/components/fundamentals/comparison_chart.py:12-15` imports `_add_threshold_bands`,
     `_apply_yaxis_format`, `_base_layout` (all underscore-private) and `KPI_CONFIG` the same way.
   - None of these six names are exported from `src/ui/components/fundamentals/__init__.py`.

#### Clear violation — UI theming (CLAUDE.md "UI layer conventions")

5. ✅ **RESUELTO** — **`src/ui/components/fundamentals/comparison_table.py:19-23`** defines local color constants
   (`_GREEN_BG`, `_YELLOW_BG`, `_RED_BG`, `_GRAY_BG`) instead of adding background-tint variants to
   `src/ui/styles/theme.py`.

#### Docstring accuracy (mandatory Google-style docstrings)

6. ✅ **RESUELTO** — **Docstring contradicts implementation** —
   `src/modules/fundamentals/processors/fundamentals_history_processor.py`: `Args:` (lines 47-53)
   describe `annual_records`/`inflation_records` as optional with defaults, but the signature has
   no defaults and the body raises `ValueError` if either is falsy/empty. Never bites in practice
   (the service always supplies non-empty lists), but the docstring is factually wrong.

7. ✅ **RESUELTO** — **Missing `Raises:` sections despite raising**, inconsistent with sibling repositories that do
   document it:
   - `src/modules/portfolio/repositories/json_positions_read_repository.py:11-16` (raises
     `FileNotFoundError` at line 18)
   - `src/modules/portfolio/repositories/json_distributions_read_repository.py:11-16` (same)
   - `src/modules/common/repositories/yfinance_market_price_read_repository.py:14-23,27-36` (`_fetch`
     raises `ValueError` at line 40)
   - Contrast: `json_catalog_read_repository.py`, `json_inflation_read_repository.py`,
     `json_fundamentals_read_repository.py` all correctly document `Raises:`.

#### Naming/structure nit

8. ✅ **RESUELTO** — **`src/modules/radar/repositories/base.py`** is an empty flat module instead of a `base/`
   sub-package (the convention every other populated domain follows). Not a functional bug — Radar
   is documented as reserved/empty — but the placeholder itself already deviates from the pattern
   it will need once populated.

#### Already-documented debt (confirmed present, not new)

9. ✅ **RESUELTO** — `src/modules/wiki/services/wiki_query_service.py:28-38` import-order violation — was
   acknowledged in `.github/instructions/architecture.instructions.md` and `AGENTS.md`; fixed, and
   both acknowledgment notes removed since the debt no longer exists.

#### Minor nits

10. ✅ **RESUELTO** — `src/modules/wiki/services/wiki_query_service.py:119-120` — `run()`'s docstring still said "one
    FIBRA" (pre-ESJ-14 language); `stream()`'s docstring two methods below correctly says "an
    allowed FIBRA scope."
11. ✅ **RESUELTO** — Cosmetic import-grouping inconsistency: `fundamentals_data_retriever_service.py`/
    `portfolio_data_retriever_service.py` insert an extra blank line between `modules.common.*`
    and domain-own imports; `src/ui/pages/fundamentals.py` keeps internal imports as one block. Neither
    was explicitly disallowed by CLAUDE.md, but the two styles coexisted undecided — standardized on
    the single-block style and documented the rule explicitly in CLAUDE.md.
12. ✅ **RESUELTO** — `data/results/descargar_fmty.py`, `descargar_fnova.py`, `descargar_fibrapl_en.py` — offline PDF
    downloader scripts live in a location (`data/results/`) not mentioned in CLAUDE.md's documented
    tree. Harmless, just undocumented — added to the CLAUDE.md architecture tree.

### Verified compliant (no deviation found)

- All business-rule invariants (average_purchase_cost, net_fiscal_result_income vs. net_income,
  dividend_yield, ltv, cbfis_with_rights vs. cbfis_outstanding, partial-sum vs. strict-sum annual
  aggregation) match CLAUDE.md/README.md exactly.
- Catalog/portfolio scope (7 catalog FIBRAs, 4 held positions) matches the documented table.
- Zero `__init__` methods across every concrete/abstract repository — full compliance with the
  no-constructor-arguments rule.
- Models are behavior-free everywhere; raw→enriched pairs correctly subclassed; aggregate models
  correctly flat.
- Service pattern matched exactly by all four reference/production services.
- `src/src/modules/wiki/` anthropic-isolation, ticker casing, and scope-guard behavior all as documented.
- Package exports (`__all__`) present everywhere inspected.
- Testing conventions (no mocking except the one documented exception) respected; 223 tests
  collected, matching the documented count.
- `flake8` clean.

---

## 2. Security audit

*Run by: `security-auditor` subagent.*

### Findings

No Critical or High findings.

**Medium**

1. **Model-supplied tool arguments reach filesystem/equality operations without type validation
   before use** — `src/modules/wiki/services/wiki_query_service.py:306-319` (`_run_tool`) and
   `:241-258` (`_has_foreign_ticker`). `WikiToolUse.input` is a bare `dict` with no per-key schema;
   `_run_tool` calls `.lower()`/`.upper()` directly on whatever the model sent without first
   coercing/validating it's a string. A prompt-injected instruction inside a wiki page (indirect
   injection via third-party PDF transcription) that gets the model to emit a non-string `ticker`
   would raise `AttributeError`, not caught by `_dispatch`'s narrow `except (FileNotFoundError,
   ValueError, KeyError)` — but it is still caught by the outer `except Exception` in `stream()`,
   so not currently exploitable beyond terminating that one query. The type boundary is implicit
   rather than enforced; a future narrowing of that outer catch would turn this into an unhandled
   crash. **Fix direction:** validate `tool_use.input` shape (string type, non-empty) before
   dispatch, independent of the existing `validate_wiki_slug` path-shape check.

2. **`read_fundamentals`'s `period` argument is not run through any allowlist** —
   `wiki_query_service.py:314-319` passes `tool_use.input.get("period")` straight into
   `FundamentalsQueryFilterProcessor.process`, which only does an equality comparison — never
   builds a path, so no path-traversal or authorization impact. Noted only for consistency with the
   validation pattern used for `ticker`/`page_name`.

**Low / Informational**

3. **Dependency:** `pymupdf==1.27.2.3` parses PDFs from third-party investor-relations sites
   (`data/results/descargar_*.py`). MuPDF has had memory-safety CVEs tied to malformed PDF parsing
   historically. URLs are fixed/developer-chosen; the *content* is external. Worth a one-time check
   against the MuPDF/pymupdf advisory database before ingesting new quarterly reports.
4. **`WikiQueryRequest.tickers`/`primary_ticker`** have no format constraint at the Pydantic layer.
   Safe today because every call site builds `tickers` from `WikiCatalogService` (trusted,
   filesystem-derived), and `_has_foreign_ticker` re-checks membership per tool call regardless.
   Flagged as defense-in-depth only.
5. **`src/ui/components/fundamentals/citations.py:13`** renders `[[{citation}]]` via plain
   `st.markdown` where `citation` is regex-extracted from LLM output grounded in wiki content
   (indirect-injection surface). The regex excludes `]`, preventing the citation from closing out
   of `[[...]]` to form a markdown link — no injection possible today. No `unsafe_allow_html` used.
   No actionable fix; already follows the repo's documented-secure pattern.

### Not found (checked, nothing to report)

- No hardcoded credentials/secrets anywhere (the one `sk-ant-test` string is an explicit test
  fixture). `.env` git-ignored, `.env.example` empty placeholder.
- No path-traversal bypass: every filesystem read incorporating an externally/model-influenced
  value runs through `wiki_slug_guard.validate_wiki_slug`.
- No wiki ticker scope-guard bypass: `_has_foreign_ticker` runs before dispatch and aborts the
  whole turn on any out-of-scope ticker; UI call sites only ever pass trusted, filesystem-derived
  ticker lists.
- No command injection / `eval`/`exec`/`subprocess`/`pickle`/unsafe `yaml.load` anywhere in the repo.
- No insecure deserialization: every `data/*.json` reader parses straight into a Pydantic model.
- No injection via `unsafe_allow_html`: all five call sites interpolate only developer-controlled
  constants or catalog/fundamentals-derived values; the one place LLM/user chat content is
  rendered correctly avoids `unsafe_allow_html`.
- No insecure session/token handling: `st.session_state` holds only chat message history; logging
  near the Anthropic call logs only `request_id`/token counts.
- Dependency pinning looks current: `yfinance==1.2.0` satisfies the documented `>=1.0.0`
  requirement; `streamlit`, `pandas`, `plotly`, `pydantic`, and checked transitive pins are recent,
  non-EOL versions. Still worth a routine `pip-audit` pass as hygiene.

### Summary

Low residual risk. A small, single-user, no-auth Streamlit app with a genuinely narrow external-input
surface, and the codebase consistently applies its own guard patterns (Pydantic validation on every
JSON read, `wiki_slug_guard` on every model-influenced filesystem read, the Anthropic key never
leaving its `.env`/`src/config.py` boundary, no `unsafe_allow_html` on LLM-generated text). The two
Medium findings are defense-in-depth gaps in argument *type* validation in `wiki_query_service.py`,
not currently exploitable. **Counts:** Critical 0 · High 0 · Medium 2 · Low/Informational 3.

---

## 3. Architecture audit

*Run by: `architecture-auditor` subagent.*

**Architecture-rules source:** `.github/instructions/architecture.instructions.md` exists (a
well-maintained, codebase-verified rules doc) and is consistent with `CLAUDE.md` and
`.github/copilot-instructions.md` — no contradictions found between them. Verification performed:
full read of `src/modules/`, `src/ui/`, `src/config.py`; `flake8` clean; full test suite 223/223 passed.

### Findings

#### Long-term debt (worth tracking)

1. **Inflation-compounding logic duplicated three times, two copies in the UI layer:**
   `src/modules/fundamentals/processors/fundamentals_history_processor.py:353-382` (`_cagr_inflation`,
   a CAGR), `src/ui/components/fundamentals/detail_chart.py:184-220` (`_compute_inflation_reference`,
   a full reference series), and `src/ui/components/fundamentals/comparison_chart.py:65-92`
   (`_build_inflation_index`, a base-1000 index) — three independent implementations of the same
   compounding loop with three different output shapes. `_compute_base_year`
   (`comparison_chart.py:33-62`) is further non-duplicated calculation logic living in the UI
   layer with no processor equivalent. **Direction:** extract one shared inflation-index utility
   and have all three call sites consume its pre-shaped output.

2. **Duplicated/drifted threshold-based traffic-light color/icon logic.** `src/modules/portfolio/`
   components comply cleanly with the `theme.py`-is-the-source-of-truth rule
   (`positions_table.py`, `summary_card.py`). `src/modules/fundamentals/` does not, three different
   ways: `detail_header.py:23-43,128,138,147,156` hardcodes threshold tuples inline instead of
   importing the `OCC_LOWER/UPPER`/`LTV_LOWER/UPPER` constants that already exist in
   `detail_chart.py:12-15`; `detail_chart.py:229-260` (`_add_threshold_bands`) is a second,
   Plotly-specific implementation; `comparison_table.py:88-101,160-185` is a third, with its own
   separate `_THRESHOLD_FULL/_THRESHOLD_WARN` constants on a different scale. The
   `detail_header.py` literals currently happen to match `detail_chart.py`'s constants, but nothing
   enforces that — a future threshold change would silently desync the KPI header from the KPI
   chart/table. **Direction:** add a shared threshold→color/icon helper to `src/ui/styles/` and have all
   three call it.

3. **`FundamentalsHistory`'s shape is inconsistent** (three ticker-keyed dicts, two flat lists),
   forcing `src/ui/pages/fundamentals.py:138-142,169-170` to re-derive a per-ticker grouping that
   `FundamentalsHistoryProcessor._compute_fibra_metrics` (`fundamentals_history_processor.py:156`)
   already builds internally once and discards. **Direction:** expose the pre-grouped/sorted
   `annual_records` shape from the processor, or add a small tested processor method the page calls
   instead of inlining groupby/sort.

4. **Dead aggregation methods in `DistributionsProcessor`** — `total_net_income`,
   `total_gross_income`, `total_withholding`
   (`src/modules/portfolio/processors/distributions_processor.py:71-102`) have no caller besides their
   own unit tests; `PortfolioProcessor.process()` computes the equivalent totals independently via
   a different, already-correct path. **Direction:** remove them and their tests, or wire them into
   the service pipeline if there's a near-term use planned.

5. **Asymmetric test coverage:** `tests/portfolio/` and `tests/fundamentals/` only test
   `processors/` — no test exercises `PortfolioDataRetrieverService`/
   `FundamentalsDataRetrieverService` directly, while `tests/wiki/services/` fully tests both wiki
   services. These two services are also documented as the **reference implementations** for the
   service pattern, yet are the only two with zero direct tests. **Direction:** add a thin
   service-level test per domain, or explicitly document the coverage decision.

#### Minor

6. `wiki_query_service.py:33` import-order violation — already documented as known debt in
   `architecture.instructions.md`; confirmed still present, unchanged, no action needed beyond
   what's already prescribed.
7. `src/modules/wiki/repositories/wiki_slug_guard.py` is a pure-logic module living under
   `repositories/` (reads like a `processors/`-shaped helper) and isn't exported through the
   package `__init__.py` — both its consumers and its test import it from the submodule path
   directly. Low severity, purely structural; correctly used everywhere it appears.
8. `src/modules/radar/repositories/base.py` is a single empty file rather than a `base/` package,
   unlike every other domain. Not live debt (Radar is an explicit placeholder), but the eventual
   implementation should conform to the `base/` package shape from the start.
9. `WikiQueryService`'s class docstring claims the service owns "tool-result truncation," but it's
   actually implemented in `WikiMessageProcessor.tool_result()` (architecturally correct — the
   docstring wording just overstates the service's own responsibility).

### What checked out clean

- Zero layer violations: no `src/ui/components/` file imports a service/repository; no `src/ui/pages/`
  file imports a repository/processor directly.
- 100% compliance with the no-constructor-arguments rule across every concrete repository.
- `PortfolioDataRetrieverService`/`FundamentalsDataRetrieverService` are exact matches for the
  documented reference-implementation shape.
- All models are behavior-free; all processors stateless, fail loud, and have zero repository
  imports.
- Only `anthropic_wiki_agent_read_repository.py` imports `anthropic`.
- All five JSON repositories raise `FileNotFoundError` identically on a missing file.
- The "esta FIBRA aún no tiene wiki" guard remains exactly the simple, unreachable branch CLAUDE.md
  describes.
- `flake8` clean; 223/223 tests passing.
- Package-export convention respected everywhere except the one function noted above (finding 7).

### Summary

Genuinely good architectural health relative to its own documented rules: hard layering boundaries
are followed with zero exceptions across all four domains, and both reference-implementation
services match their documented pattern exactly. Debt is concentrated at the *edges* of the
documented rules rather than the core layering — real duplication that has drifted into the UI
layer three separate times (inflation math, threshold coloring), an inconsistent aggregate-model
shape forcing the page to redo processor-internal work, dead aggregation code kept alive only by
its own tests, and an undocumented asymmetry in service-level test coverage.
**Counts:** 0 blocking-quality violations · 5 long-term debt items · 4 minor items.

---

## Suggested next steps

Roughly in priority order:

1. Decide on the two Medium security findings in `wiki_query_service.py` (type-validate
   `tool_use.input` before dispatch) — small, contained fix.
2. Consolidate the threshold traffic-light logic and inflation-compounding logic
   (architecture findings 1-2) — both are real duplication with a documented drift risk.
3. Clean up the `src/ui/pages/radar.py` and Comparativa-component compliance violations (findings 2-5)
   next time either file is touched.
4. Address the `Raises:`/docstring-accuracy gaps (compliance findings 6-7) as low-effort doc fixes.
5. Decide the fate of `DistributionsProcessor`'s dead methods and the service-level test-coverage
   gap (architecture findings 4-5) — both are judgment calls, not obvious bugs.
6. Investigate what is concurrently writing to `.github/instructions/` and `AGENTS.md` in this
   repo outside of this session, to avoid the review-config setup drifting out of sync with itself.
