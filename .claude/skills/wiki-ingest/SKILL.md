---
name: wiki-ingest
description: Ingiere un reporte trimestral nuevo de FMTY14 en la wiki (wiki/fmty14/), siguiendo la Operación Ingest definida en wiki/SCHEMA.md. Úsalo cuando el usuario pida procesar, ingerir o agregar un trimestre nuevo a la wiki.
argument-hint: "trimestre, ej. 2026T1"
---

# Wiki Ingest — FMTY14

Sigue exactamente la Operación **Ingest** definida en `wiki/SCHEMA.md`. Lee ese archivo primero si no lo tienes ya en contexto — es la fuente de verdad de convenciones (naming, wikilinks, frontmatter, capas).

## Argumento

`$ARGUMENTS` es el trimestre a ingerir, en formato `2026T1`. Localiza el PDF correspondiente en `wiki/fmty14/raw/` antes de empezar. Si no existe, dilo y detente — no inventes contenido.

## Restricciones específicas de esta invocación

- Procesa un solo trimestre por invocación, aunque el usuario pase varios argumentos — pregúntale cuál priorizar si manda más de uno.
- No toques `fundamentals.json` ni ningún archivo fuera de `wiki/`.
- Al terminar, resume en el chat qué páginas se crearon/editaron y qué quedó pendiente de confirmar con el usuario.
