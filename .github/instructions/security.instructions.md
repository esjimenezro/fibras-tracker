---
applyTo: "modules/**/*.py,ui/**/*.py,scripts/**/*.py,tests/**/*.py,app.py,config.py"
---

# Security review — fibras-tracker

Act as a security reviewer for this diff. This repo has **no SQL database and no ORM** — do not
raise generic SQL-injection findings. Persistence is local JSON files (parsed into Pydantic
models), a markdown "wiki" tree read/written by the app, and outbound calls to the Anthropic and
Yahoo Finance APIs. Review against the categories below, in order.

## 1. Injection

- **No SQL layer exists.** If a diff introduces one (a query string, an ORM, a raw SQL call),
  flag it as a new attack surface requiring parameterized queries — this is not currently a
  concern anywhere in the code.
- **Command injection**: flag any new `subprocess`, `os.system`, or `shell=True` call. None exist
  today. If added (e.g. for a new ingestion tool), arguments must be a list, never a
  shell-interpolated string built from ticker names, filenames, or any other value that
  ultimately traces back to a data file, PDF, or model output.
- **Template/HTML injection (this repo's actual injection surface)**: several UI components pass
  raw f-string HTML into Streamlit's `unsafe_allow_html=True`
  (`ui/components/common/page_header.py`, `ui/components/fundamentals/comparison_table.py`,
  `ui/styles/theme.py`). Today every interpolated value comes from `catalog.json` or
  `fundamentals.json` — developer-controlled, not runtime user input.

  **Vulnerable** — interpolating text that ultimately comes from a user-typed question or an LLM
  answer into `unsafe_allow_html`:
  ```python
  # DON'T: question or terminal.data.answer_text can contain arbitrary HTML/JS
  st.markdown(f"<div class='answer'>{terminal.data.answer_text}</div>", unsafe_allow_html=True)
  ```
  **Secure** — the pattern this repo already uses for `_render_wiki_chat` in
  `ui/pages/fundamentals.py`: render user/model text through plain `st.markdown(answer_text)`
  (no `unsafe_allow_html`), and reserve `unsafe_allow_html` for strings built entirely from
  trusted, developer-controlled data (catalog names, formatted numbers, static CSS):
  ```python
  text_slot.markdown(terminal.data.answer_text)  # no unsafe_allow_html — Streamlit escapes it
  ```
  Flag any new `unsafe_allow_html=True` call whose interpolated values include a user-typed
  string, an LLM-generated string, or anything read from `wiki/*/sources/` or `wiki/*/pages/`
  (transcribed from external PDFs).

## 2. Hardcoded credentials / secrets

- The only credential in this app is `ANTHROPIC_API_KEY`, read via `os.environ` /
  `python-dotenv`'s `load_dotenv()` in `config.py`. Never hardcoded, never logged — confirm any
  new logging statement near `AnthropicWikiAgentReadRepository` or `WikiQueryService` logs
  `request_id`/token usage, not the key or full request/response bodies.
- Flag any string literal that looks like a key (`sk-ant-...`, a bearer token, a password) in
  source, tests, or fixtures.
- Flag any new file that stores credentials outside `.env` (already gitignored) — e.g. a
  committed `.streamlit/secrets.toml`, a config constant, a test fixture with a real-looking key.
- `.env.example` must only ever contain placeholder values.

## 3. Insecure deserialization

- No `pickle`, no `yaml.load` with an unsafe loader, no `eval`/`exec` on external content exist
  in this repo today. Flag any of these if introduced.
- The safe pattern already in use: every `data/*.json` file is parsed straight into a Pydantic
  model on read (e.g. `modules/common/repositories/json_catalog_read_repository.py`:
  `[Fibra(**item) for item in data["fibras"]]`), so malformed shape is rejected at the boundary
  by Pydantic's own validation rather than trusted blindly downstream. Any new JSON/external-data
  reader should follow the same immediate-validation pattern.

## 4. Input validation / sanitization for external and model-influenced input

This app has one real external-input boundary worth scrutinizing closely: **`tool_use.input`** —
an arbitrary dict the Anthropic model constructs during the agentic wiki chat
(`modules/wiki/services/wiki_query_service.py`). It is not fully trusted: its contents can be
steered by injected text inside a wiki page or a source PDF transcription (indirect prompt
injection), and it is used to build filesystem paths under `wiki/`.

The repo's own correct pattern — `modules/wiki/repositories/wiki_slug_guard.py` — is the
reference for any new code that turns model- or user-supplied text into a path segment:

**Vulnerable** — using a model-supplied value directly in a path:
```python
# DON'T: ticker/page_name could contain "..", "/", or other path-breaking characters
candidate = WIKI_DIR / tool_use.input["ticker"] / "pages" / f"{tool_use.input['page_name']}.md"
```
**Secure** — the actual pattern in `FileSystemWikiPageReadRepository.retrieve_data` /
`validate_wiki_slug`:
```python
_SAFE_SLUG = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?")

def validate_wiki_slug(value: str, *, label: str) -> str:
    if ".." in value or not _SAFE_SLUG.fullmatch(value):
        raise ValueError(f"Unsafe wiki {label} '{value}': expected a simple slug ...")
    return value
```
Any new code that:
- accepts a `tool_use.input[...]` value and uses it to build a path, a filename, or a shell
  argument, or
- accepts a Streamlit widget value (`st.text_input`, `st.chat_input`, `st.selectbox` with
  free-text) and uses it the same way,

must validate it through an equivalent allowlist check before use — never a denylist, never a
raw `.replace("..", "")`.

- `FileSystemWikiPageReadRepository` also rejects any `page_name` containing `/` outright (the
  cross-FIBRA wikilink form is out of scope for that call) — flag any change that loosens this
  without an explicit, reviewed reason.
- Flag any new tool schema (in `modules/wiki/services/_wiki_query_prompt.py`) whose
  `input_schema` accepts a free-form string that later reaches a filesystem path, a subprocess
  argument, or a URL, without a validation step matching the pattern above.

## 5. Authentication / authorization

- This is a single-user local app with no login, no sessions, no multi-tenant data. Classic
  authn/authz findings do not apply — do not invent a missing login system as a finding.
- The one access-control-adjacent concern is the **wiki ticker scope guard** in
  `WikiQueryService._has_foreign_ticker`: it restricts which FIBRA data a given chat turn's tool
  calls may read (`WikiQueryRequest.tickers`). Flag any change that:
  - removes or weakens this membership check,
  - lets a tool call succeed for a ticker outside `tickers` without the check running first, or
  - adds a new tool whose dispatch (in `WikiQueryService._run_tool`) does not respect the same
    scope.
