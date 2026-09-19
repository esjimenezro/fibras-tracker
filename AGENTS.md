# AGENTS.md

Project context, architecture, and conventions live in `CLAUDE.md` — read that first for any
implementation work.

## Code Review

When reviewing a pull request in this repo, report findings in three separate, labeled sections,
in this order. Do not merge them into general prose.

1. **PR description compliance**
   - Scope creep: changes present in the diff but not mentioned in the PR description.
   - Unmet promises: behavior the description claims that the diff does not implement, or only
     partially implements.
   - If the description is missing or empty, say so explicitly instead of skipping this section.

2. **Security findings** — per `.github/instructions/security.instructions.md`.
   - For each finding: cite the file and the specific diff line.
   - Categories to check: injection (this repo has no SQL/ORM — the real surface is
     `unsafe_allow_html` HTML construction and command-style calls, not SQL), hardcoded
     credentials/secrets, insecure deserialization, input validation for model-influenced or
     user-supplied values (especially `tool_use.input` in the wiki chat), and the wiki
     ticker-scope guard as this app's closest equivalent to an authorization check.

3. **Architecture findings** — per `.github/instructions/architecture.instructions.md`.
   - For each finding: name the specific rule violated (e.g. "Rule 2 — Pages call services,
     never repositories") and cite the diff line.
   - Do not flag the known, already-documented import-order debt in
     `src/modules/wiki/services/wiki_query_service.py` as a new finding unless the diff makes it
     worse.

Each section stands on its own — a clean result in one section does not excuse skipping the
others.
