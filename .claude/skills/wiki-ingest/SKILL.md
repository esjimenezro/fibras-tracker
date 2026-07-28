---
name: wiki-ingest
description: Ingiere un reporte trimestral nuevo de FMTY14 en la wiki (wiki/fmty14/), siguiendo la Operación Ingest definida en wiki/SCHEMA.md. Úsalo cuando el usuario pida procesar, ingerir o agregar un trimestre nuevo a la wiki.
argument-hint: "trimestre, ej. 1T2024"
---

# Wiki Ingest — FMTY14

Sigue exactamente la Operación **Ingest** definida en `wiki/SCHEMA.md`. Lee ese archivo primero si no lo tienes ya en contexto — es la fuente de verdad de convenciones (naming, wikilinks, frontmatter, capas).

## Argumento

`$ARGUMENTS` es el trimestre a ingerir, en formato `1T2024`. Localiza el PDF correspondiente en `wiki/fmty14/raw/` antes de empezar. Si no existe, dilo y detente — no inventes contenido.

## Paso 1 — generar sources/ (mecánico, no LLM)

Instala `pymupdf4llm` si falta (`uv pip install pymupdf4llm`) y corre exactamente:

```python
import pymupdf4llm
md_text = pymupdf4llm.to_markdown("wiki/fmty14/raw/<archivo>.pdf")
with open("wiki/fmty14/sources/<YYYY-QN>-source.md", "w") as f:
    f.write(md_text)
```

No leas el PDF tú mismo ni reescribas/limpies el output — guárdalo tal cual sale de la función, incluyendo cualquier ruido cosmético del OCR (es esperado y aceptable, ver `wiki/SCHEMA.md`).

## Restricciones específicas de esta invocación

* Procesa un solo trimestre por invocación, aunque el usuario pase varios argumentos — pregúntale cuál priorizar si manda más de uno.
* No toques `fundamentals.json` ni ningún archivo fuera de `wiki/`.
* Al terminar, resume en el chat qué páginas se crearon/editaron y qué quedó pendiente de confirmar con el usuario.
