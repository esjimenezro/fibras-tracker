# Review instructions

These are review-only rules for automated PR review. They do not describe the project — see
`CLAUDE.md` for architecture, layer responsibilities, naming conventions, and error-handling
conventions; violations of anything documented there are Architecture findings (see below). The
security section below folds in the repo-specific detail from
`.github/instructions/security.instructions.md` (a parallel, uncommitted GitHub Copilot review
config) — treat that file, if present, as extra detail on the same categories, not a separate
checklist.

Review order: Compliance first, always, before anything else below.

## 1. Compliance (check first, always)

Compare the diff against the PR's own description (title + body + linked issue, if any).

- **Report as Important:** any change in the diff that is not mentioned or implied by the PR
  description (scope creep) — e.g. unrelated refactors, drive-by renames, formatting-only changes
  to untouched files, or edits to files the description gives no reason to touch.
- **Report as Important:** anything the PR description promises that the diff does not actually
  implement (e.g. "adds tests for X" with no new/updated test file, "updates README.md" with no
  README change, a described behavior with no corresponding code path).
- A PR description that is missing entirely is itself an Important finding — say so and review the
  diff on its own technical merits for everything below.

## 2. Security (Important)

This repo has **no SQL database and no ORM** — do not raise generic SQL-injection findings.
Persistence is local JSON files (parsed into Pydantic models), a markdown "wiki" tree, and outbound
calls to the Anthropic and Yahoo Finance APIs. Treat each of the following as Important, regardless
of how small the diff is:

- **Injection**:
  - No SQL layer exists — if a diff introduces one (query string, ORM, raw SQL call), flag it as a
    brand-new attack surface requiring parameterized queries.
  - Command injection: flag any new `subprocess`, `os.system`, or `shell=True` call. None exist
    today; if added, arguments must be a list, never a shell-interpolated string built from a
    ticker, filename, or any value tracing back to a data file, PDF, or model output.
  - **Template/HTML injection — this repo's actual injection surface.** Several UI components pass
    raw f-string HTML into Streamlit's `unsafe_allow_html=True`
    (`src/ui/components/common/page_header.py`, `src/ui/components/fundamentals/comparison_table.py`,
    `src/ui/styles/theme.py`). Today every interpolated value there comes from `catalog.json` /
    `fundamentals.json` (developer-controlled). Flag any new `unsafe_allow_html=True` call whose
    interpolated value includes a user-typed string, an LLM-generated string, or anything read
    from `wiki/*/sources/` or `wiki/*/pages/` (transcribed from external PDFs) — e.g.
    `st.markdown(f"<div>{terminal.data.answer_text}</div>", unsafe_allow_html=True)` is Important.
    The safe, already-used pattern is plain `st.markdown(answer_text)` with no
    `unsafe_allow_html` (see `_render_wiki_chat` in `src/ui/pages/fundamentals.py`).
- **Hardcoded credentials/secrets**: `ANTHROPIC_API_KEY` is the only credential, read via
  `os.environ`/`python-dotenv` in `src/config.py` — flag any literal that looks like a key
  (`sk-ant-...`, a bearer token, a password) in source, tests, or fixtures; any new logging near
  `AnthropicWikiAgentReadRepository`/`WikiQueryService` that logs the key or a full request/response
  body instead of just `request_id`/token usage; any credential stored outside `.env` (e.g. a
  committed `.streamlit/secrets.toml`); a non-placeholder value added to `.env.example`.
- **Insecure deserialization**: no `pickle`, no unsafe `yaml.load`, no `eval`/`exec` on external
  content exist today — flag any of these if introduced. The safe pattern already in use is
  parsing `data/*.json` straight into a Pydantic model on read (e.g.
  `[Fibra(**item) for item in data["fibras"]]` in `json_catalog_read_repository.py`), so malformed
  shape is rejected by Pydantic at the boundary. Any new JSON/external-data reader should follow
  the same immediate-validation pattern instead of trusting a raw `dict` downstream.
- **Missing input validation**, especially the one real external-input boundary in this app:
  `tool_use.input` — an arbitrary dict the Anthropic model constructs during the agentic wiki chat
  (`src/modules/wiki/services/wiki_query_service.py`). It is not fully trusted (indirect prompt
  injection via wiki/source-PDF content can steer it) and is used to build filesystem paths under
  `wiki/`. The reference pattern is `src/modules/wiki/repositories/wiki_slug_guard.py::validate_wiki_slug`
  — any new code that turns a `tool_use.input[...]` value, or a Streamlit free-text widget value,
  into a path segment, filename, or shell argument must validate it through an equivalent allowlist
  regex, never a denylist or an ad hoc `.replace("..", "")`. Also flag any change that loosens
  `FileSystemWikiPageReadRepository`'s rejection of `/` in a `page_name`, or any new tool schema in
  `src/modules/wiki/services/_wiki_query_prompt.py` whose `input_schema` accepts a free-form string
  that later reaches a path/subprocess argument/URL without going through this validation.
- **Auth/authorization**: this is a single-user local app with no login/sessions — do not invent a
  missing login system as a finding. The one access-control-adjacent concern is the wiki ticker
  scope guard, `WikiQueryService._has_foreign_ticker` / `WikiQueryRequest.tickers`. Flag any change
  that removes or weakens this membership check, lets a tool call succeed for a ticker outside
  `tickers` without the check running first, or adds a new tool whose dispatch in
  `WikiQueryService._run_tool` doesn't respect the same scope.

## 3. Architecture (Important)

Report as Important any violation of the rules documented in `CLAUDE.md`, in particular:

- Layer bypass: `ui/pages/` calling a repository or processor directly instead of a `services/`
  method; a `service` doing raw data access instead of going through `repositories/`; business
  logic (calculations, aggregations, filters) living in a `ui/components/` or `service` instead of
  a `processors/` module.
- Repository contract breaks: a concrete repository taking constructor arguments instead of
  routing dynamic input through `retrieve_data(...)`; a new repository not implementing its
  `base/` abstract interface.
- Service contract breaks: a `service.run()` that doesn't wrap its pipeline in
  `try/except Exception`, that raises past its own boundary, or that returns something other than
  its typed `<ServiceName>Schema`.
- Model convention breaks: a model in `models/` gaining a method, a computed field, or a
  validator; a processor-derived field added to a raw model instead of an `Enriched<Name>`
  subclass.
- `modules/wiki/` conventions: any file outside
  `src/modules/wiki/repositories/anthropic_wiki_agent_read_repository.py` importing `anthropic`
  directly instead of working with `WikiAgentEvent`/`WikiStreamEvent`/the domain exceptions.
- If the diff shows the *same* pattern handled inconsistently in old vs. new code (e.g. one
  repository following the constructor convention and a new one not), call this out explicitly
  as an inconsistency to resolve, not as something the new code can copy.

## 4. Nits (capped)

Everything else — style preferences, minor naming, docstring wording, import order, missed
`Google`-style docstring fields (mandatory per `CLAUDE.md`), keyword-argument-only calls, etc.

- Report at most **5** nits per review, chosen for highest signal.
- If more than 5 nit-level issues exist, state the total count in the summary
  (e.g. "12 additional minor nits not shown") instead of listing them all.

## 5. Ignore

Do not report on:

- Generated or vendored files, and lockfiles (`uv.lock`).
- Anything already enforced by `flake8` (`.flake8`: `max-line-length = 200`) — line length and
  basic style are CI's job, not the review's.
- Test data fixtures whose only purpose is realistic-looking sample values (not real secrets).

Note: this repo has no CI-enforced formatter, import-sorter, or type checker beyond `flake8`, so
naming conventions, import order/grouping, explicit-keyword-argument calls, and docstring
completeness (all mandatory per `CLAUDE.md`) are **not** covered by tooling — still review them,
subject to the nit cap above.
