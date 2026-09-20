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
- ~~Real, evidenced duplication of business/presentation logic that had drifted into the UI layer:
  inflation-compounding math implemented three times, and threshold-based traffic-light coloring
  implemented three different ways in `src/modules/fundamentals/`~~ — both ✅ resolved 2026-09-20
  (architecture findings 1-2).
- ~~Defense-in-depth gaps around model-supplied tool arguments in
  `src/modules/wiki/services/wiki_query_service.py`~~ — ✅ resolved 2026-09-20.

**Counts:** Security — 0 Critical, 0 High, 2 Medium (✅ resolved), 3 Low/informational (won't fix).
Architecture — 0 blocking violations, 5 long-term debt items (all 5 ✅ resolved), 4 minor items.
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

## 2. Security audit — ✅ RESUELTO (2026-09-20)

*Run by: `security-auditor` subagent.*

**Status:** both Medium findings (1-2) fixed and verified (`flake8` clean, 226/226 tests passing,
3 new tests added) as of 2026-09-20 — see each finding below. The 3 Low/Informational findings
(3-5) are acknowledged but **won't be fixed**: no actionable path (5), a one-time dependency-advisory
check rather than a code change (3), and a defense-in-depth-only note already covered by existing
guards (4). Left as-is by decision.

### Findings

No Critical or High findings.

**Medium**

1. ✅ **RESUELTO (2026-09-20)** — **Model-supplied tool arguments reach filesystem/equality
   operations without type validation before use** — `src/modules/wiki/services/wiki_query_service.py:306-319`
   (`_run_tool`) and `:241-258` (`_has_foreign_ticker`). `WikiToolUse.input` is a bare `dict` with no
   per-key schema; `_run_tool` calls `.lower()`/`.upper()` directly on whatever the model sent
   without first coercing/validating it's a string. A prompt-injected instruction inside a wiki page
   (indirect injection via third-party PDF transcription) that gets the model to emit a non-string
   `ticker` would raise `AttributeError`, not caught by `_dispatch`'s narrow `except
   (FileNotFoundError, ValueError, KeyError)` — but it is still caught by the outer `except
   Exception` in `stream()`, so not currently exploitable beyond terminating that one query. The
   type boundary is implicit rather than enforced; a future narrowing of that outer catch would turn
   this into an unhandled crash. **Fix applied:** added `WikiQueryService._require_str(tool_use,
   key)`, which type/non-blank-checks a required string argument and raises `ValueError` (caught by
   `_dispatch` into a per-call `is_error` tool result) instead of letting a bad type reach
   `.lower()`/`.upper()`. Used for `ticker` and `page_name` in `_run_tool`. Tests added in
   `tests/wiki/services/test_wiki_query_service.py`
   (`test_non_string_tool_argument_yields_is_error_without_aborting_query`).

2. ✅ **RESUELTO (2026-09-20)** — **`read_fundamentals`'s `period` argument is not run through any
   allowlist** — `wiki_query_service.py:314-319` passes `tool_use.input.get("period")` straight into
   `FundamentalsQueryFilterProcessor.process`, which only does an equality comparison — never
   builds a path, so no path-traversal or authorization impact. Noted only for consistency with the
   validation pattern used for `ticker`/`page_name`. **Fix applied:** `period`, when present, is now
   run through the same `_require_str` type check as `ticker`/`page_name` (values stay unconstrained
   — periods are dynamic labels like "1T2026" — only the type is checked); `period=None` still means
   "no filter" and skips the check.

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

1. ✅ **RESUELTO (2026-09-20)** — **Inflation-compounding logic duplicated three times, two copies
   in the UI layer:** `src/modules/fundamentals/processors/fundamentals_history_processor.py:353-382`
   (`_cagr_inflation`, a CAGR), `src/ui/components/fundamentals/detail_chart.py:184-220`
   (`_compute_inflation_reference`, a full reference series), and
   `src/ui/components/fundamentals/comparison_chart.py:65-92` (`_build_inflation_index`, a base-1000
   index) — three independent implementations of the same compounding loop with three different
   output shapes. `_compute_base_year` (`comparison_chart.py:33-62`) is further non-duplicated
   calculation logic living in the UI layer with no processor equivalent (left as-is — it isn't
   duplicated anywhere, so there was nothing to consolidate). **Fix applied:** three copies reduced
   to two, split along the layer boundary that `ui/components/**` may depend only on
   `modules/*/models`/`schemas`, never on `modules/*/processors` (`.github/instructions/architecture.instructions.md`
   Rule 1) — a single shared `modules/common/processors` utility reachable from both sides was
   considered first and reverted once that boundary was pointed out. Landed instead: (a)
   `InflationIndexProcessor` (`src/modules/common/processors/inflation_index_processor.py`, new
   `modules/common/processors/` package) — a stateless `process(base_year, base_value, rate_years,
   inflation_records)` used only by `FundamentalsHistoryProcessor._cagr_inflation`; and (b)
   `compound_inflation_series`, the same compounding-and-truncation loop kept as a second,
   intentionally separate copy in `ui/components/fundamentals/detail_chart.py`, exported through
   `ui/components/fundamentals/__init__.py` (the same pattern already used there for
   `add_threshold_bands`/`apply_yaxis_format`/`base_layout`) and consumed by both
   `_compute_inflation_reference` (detail_chart) and `_build_inflation_index` (comparison_chart).
   Each call site still builds its own `rate_years`. Investigation while consolidating surfaced that
   the three sites' *conventions* for which years' rates apply already diverged before this fix (the
   CAGR excludes the end year and includes the start year, `detail_chart` only steps through years
   that have an annual record — skipping gap years — while `comparison_chart` walks every calendar
   year) — each site's exact prior numeric behavior was preserved deliberately (verified: existing
   `test_cagr_inflation_computed_correctly` still passes unchanged; a manual equivalence check
   confirmed the UI call sites too) rather than silently unified, since picking one convention would
   change displayed inflation figures and is a product decision, not a duplication cleanup. Each
   function's docstring now states its own convention explicitly, and both `InflationIndexProcessor`
   and `compound_inflation_series` cross-reference each other and explain why they can't merge into
   one. Tests added in `tests/common/processors/test_inflation_index_processor.py` (5 cases: base
   entry, consecutive compounding, arbitrary/repeated `rate_years`, truncation on a missing year,
   empty inflation history); the UI copy has no dedicated tests, consistent with this repo's existing
   UI-component test coverage (none), verified instead by a manual equivalence check against the
   pre-refactor output.

2. ✅ **RESUELTO (2026-09-20)** — **Duplicated/drifted threshold-based traffic-light color/icon
   logic.** `src/modules/portfolio/` components comply cleanly with the `theme.py`-is-the-source-of-truth
   rule (`positions_table.py`, `summary_card.py`). `src/modules/fundamentals/` does not, three
   different ways: `detail_header.py:23-43,128,138,147,156` hardcodes threshold tuples inline
   instead of importing the `OCC_LOWER/UPPER`/`LTV_LOWER/UPPER` constants that already exist in
   `detail_chart.py:12-15`; `detail_chart.py:229-260` (`_add_threshold_bands`) is a second,
   Plotly-specific implementation; `comparison_table.py:88-101,160-185` is a third, with its own
   separate `_THRESHOLD_FULL/_THRESHOLD_WARN` constants on a different scale. The
   `detail_header.py` literals currently happen to match `detail_chart.py`'s constants, but nothing
   enforces that — a future threshold change would silently desync the KPI header from the KPI
   chart/table. **Note:** `comparison_table.py`'s `_THRESHOLD_FULL`/`_THRESHOLD_WARN` (1.0/0.70)
   back a *different* concept — a pass/warn/fail icon on a fraction-of-years-meeting-a-growth-criterion,
   not a KPI-value traffic light — and were left untouched; they were never actually a third copy of
   the same red/yellow/green decision, just a similarly-shaped one on an unrelated scale. **Fix
   applied:** the three implementations that *were* the same decision (given a value, lower, upper,
   and an inverse flag, which of the three zones does it fall in) now all call one shared
   `threshold_zone(value, lower, upper, inverse) -> "positive"|"warning"|"negative"` in
   `src/ui/styles/theme.py`, plus two thin encoders built on it —
   `threshold_emoji` (used by `detail_header._traffic_light`) and `threshold_background` (used by
   `comparison_table._color_bg`). `detail_chart.add_threshold_bands` isn't a per-value classification
   (it draws static background bands from the raw `lower`/`upper` range, no `threshold_zone` call
   fits), but its hardcoded red/yellow/green `rgba(...)` fill strings — which duplicated the same RGB
   triples as `theme.py`'s existing `COLOR_*_BG` constants at a different alpha — now come from a new
   `zone_background(zone, alpha)` helper (also in `theme.py`; `COLOR_POSITIVE_BG`/`COLOR_WARNING_BG`/
   `COLOR_NEGATIVE_BG` are now derived from it, unchanged values). `detail_header.py`'s inline OCC/LTV
   threshold tuples were replaced with the existing `OCC_LOWER`/`OCC_UPPER`/`LTV_LOWER`/`LTV_UPPER`
   imports from `ui.components.fundamentals` (NOI-margin/EBITDA-margin thresholds have no chart
   equivalent to import, so those two stay as local literals — nothing to desync from). Verified: all
   three zone boundaries (`> upper`/`< lower`, both `inverse` values) checked exhaustively against
   both pre-refactor formulas over a value grid — 0 mismatches; `render_detail_header` smoke-called
   directly with a constructed record — no exception. No dedicated tests added (`ui/styles/` and
   `ui/components/` have no existing test coverage in this repo; consistent with that, left
   unchanged).
   **Layering note:** a first attempt at consolidating *inflation-compounding* logic (finding 1,
   above) mistakenly imported a `modules/common/processors` class into `ui/components/`, which the
   user caught and corrected — `ui/components/**` may depend only on `modules/*/models`/`schemas`,
   never `modules/*/processors`. This fix stayed inside `ui/styles/`, so no such boundary applies here.

3. ✅ **RESUELTO (2026-09-20)** — **`FundamentalsHistory`'s shape is inconsistent** (three
   ticker-keyed dicts, two flat lists), forcing `src/ui/pages/fundamentals.py:138-142,169-170` to
   re-derive a per-ticker grouping that `FundamentalsHistoryProcessor._compute_fibra_metrics`
   (`fundamentals_history_processor.py:156`) already builds internally once and discards.
   **Fix applied:** `FundamentalsHistory.annual_records` changed from
   `list[AnnualFundamentalsRecord]` to `dict[str, list[AnnualFundamentalsRecord]]`
   (ticker-keyed, each list year-ascending — matching `latest_by_ticker`/`prior_year_by_ticker`/
   `fibra_metrics`, and matching what the model's own docstring already claimed before this fix,
   a second instance of docstring/implementation drift alongside compliance finding 6).
   `FundamentalsHistoryProcessor.process()` now groups the caller's flat `annual_records` input by
   ticker once and hands each ticker's slice both to `_compute_fibra_metrics` (whose own
   internal `[r for r in annual_records if r.ticker == ticker]` filter is gone — it now takes
   the pre-filtered `ticker_annual_records` directly) and to the `FundamentalsHistory` output.
   `ui/pages/fundamentals.py`'s lines 138-142 (the manual groupby+sort building
   `annual_records_by_ticker`) were deleted entirely; its Comparativa-tab call sites now pass
   `history.annual_records` straight through, and its Detalle-tab line 170 became
   `history.annual_records.get(selected_ticker, [])`. `comparison_table.py`/`comparison_chart.py`
   needed no changes — they already expected this exact `dict[str, list[...]]` shape. Verified:
   full suite green (232/232, one existing test —
   `test_annual_records_passed_through_to_history` — replaced with two that assert the new
   grouped/sorted shape and that a ticker with no complete year is simply absent from the dict);
   an end-to-end run against the real `FundamentalsDataRetrieverService` pipeline and the three
   UI consumers (`render_comparison_table`, `render_comparison_chart`, `render_detail_chart`)
   confirmed no exception and correctly ordered per-ticker groups.

4. ✅ **RESUELTO (2026-09-20)** — **Dead aggregation methods in `DistributionsProcessor`** —
   `total_net_income`, `total_gross_income`, `total_withholding`
   (`src/modules/portfolio/processors/distributions_processor.py:71-102`) had no caller besides their
   own unit tests. **Correction:** the equivalent-totals path is actually `PositionsProcessor`
   (`total_net_fiscal_result_received = sum(d.net_fiscal_result_income for d in distributions)`),
   not `PortfolioProcessor` as originally written above — confirmed by grep, no other reference to
   these three names existed anywhere outside this file and its tests. **Fix applied:** removed
   rather than wired in — beyond being unused, `total_net_income`/`total_gross_income` aggregate
   `net_income`/`gross_income` globally across all positions, which is exactly the pattern
   CLAUDE.md's business-rules section warns against ("Use net_fiscal_result_income, never
   net_income, when aggregating fiscal-result income — net_income includes the non-taxable
   reimbursement component"); wiring dead code back in that contradicts a documented invariant
   would have been worse than deleting it. Removed the three methods and their three tests
   (`test_total_net_income`, `test_total_gross_income`, `test_total_withholding`); the
   `dist_mixed`/`dist_fiscal_only` fixtures they used stay, since other tests in the same file
   still use them. Verified: `grep` confirms zero remaining references anywhere in `src/`/`tests/`;
   full suite green (229/229, down from 232 — exactly the 3 removed tests); `flake8` clean.

5. ✅ **RESUELTO (2026-09-20)** — **Asymmetric test coverage:** `tests/portfolio/` and
   `tests/fundamentals/` only tested `processors/` — no test exercised
   `PortfolioDataRetrieverService`/`FundamentalsDataRetrieverService` directly, while
   `tests/wiki/services/` fully tested both wiki services. These two services are also documented
   as the **reference implementations** for the service pattern, yet were the only two with zero
   direct tests. **Fix applied:** added `tests/portfolio/services/test_portfolio_data_retriever_service.py`
   and `tests/fundamentals/services/test_fundamentals_data_retriever_service.py` (4 tests each),
   following the same constructor-injected-fakes convention as `tests/wiki/services/` (no mocking
   library) — each domain's four repositories get a small hand-built fake, injected via the
   service's existing constructor-injection seam. Coverage per service: (1) a happy path with
   consistent fake data asserting `status=OK` and key assembled-output fields; (2) the
   service-specific ticker-derivation logic that only lives in `run()`, not in any processor —
   portfolio passes `[p.ticker for p in positions]` unmodified, fundamentals passes
   `sorted({r.ticker for r in records})` (deduplicated and sorted) — to the market price
   repository, verified via a fake that logs its calls; (3) a repository raising `FileNotFoundError`
   (matching the real JSON repositories' documented failure mode) becomes `status=ERROR` with
   `error_message` set, never raises past `run()`; (4) a downstream processor `ValueError`
   (`PortfolioProcessor` on empty positions; `FundamentalsHistoryProcessor` on an incomplete year
   producing no `AnnualFundamentalsRecord`) is caught the same way, not just repository-level
   failures. Verified: full suite green (237/237, 8 new); `flake8` clean.

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
documented rules rather than the core layering — real duplication that had drifted into the UI
layer three separate times (inflation math and threshold coloring, both ✅ resolved 2026-09-20), an
inconsistent aggregate-model shape that forced the page to redo processor-internal work (✅ resolved
2026-09-20), dead aggregation code kept alive only by its own tests (✅ resolved 2026-09-20), and an
undocumented asymmetry in service-level test coverage (✅ resolved 2026-09-20). All 5 long-term
debt items are now resolved.
**Counts:** 0 blocking-quality violations · 5 long-term debt items (all 5 ✅ resolved) · 4 minor items.

---

## Suggested next steps

Roughly in priority order:

1. ✅ **RESUELTO (2026-09-20)** — the two Medium security findings in `wiki_query_service.py`
   (type-validate `tool_use.input` before dispatch).
2. ✅ **RESUELTO (2026-09-20)** — inflation-compounding logic (architecture finding 1) and threshold
   traffic-light logic (architecture finding 2) both consolidated.
3. ✅ **RESUELTO (2026-09-20)** — Clean up the `src/ui/pages/radar.py` and Comparativa-component compliance violations (findings 2-5)
   next time either file is touched.
4. ✅ **RESUELTO (2026-09-20)** Address the `Raises:`/docstring-accuracy gaps (compliance findings 6-7) as low-effort doc fixes.
5. ✅ **RESUELTO (2026-09-20)** — `DistributionsProcessor`'s dead methods removed (architecture
   finding 4) and the service-level test-coverage gap closed with a thin service-level test per
   domain (architecture finding 5).
6. ✅ **RESUELTO (2026-09-20)** Investigate what is concurrently writing to `.github/instructions/` and `AGENTS.md` in this
   repo outside of this session, to avoid the review-config setup drifting out of sync with itself.
