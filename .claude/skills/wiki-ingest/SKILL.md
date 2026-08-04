---
name: wiki-ingest
description: Ingiere un reporte trimestral nuevo de una FIBRA en su wiki (wiki/<ticker>/), siguiendo la Operación Ingest definida en wiki/SCHEMA.md. Úsalo cuando el usuario pida procesar, ingerir o agregar un trimestre nuevo a la wiki de cualquier FIBRA (FMTY14, DANHOS13, etc.).
argument-hint: "[TICKER] [trimestre, ej. DANHOS13 3T2025]"
---

# Wiki Ingest

Sigue exactamente la Operación **Ingest** definida en `wiki/SCHEMA.md`. Lee ese archivo primero si no lo tienes ya en contexto — es la fuente de verdad de convenciones (naming, wikilinks, frontmatter, capas).

## Argumentos

`$ARGUMENTS` trae dos valores: el ticker de la FIBRA (ej. `DANHOS13`) y el trimestre a ingerir (ej. `3T2025`). El directorio de trabajo es `wiki/<ticker en minúsculas>/` (ej. `wiki/danhos13/`).

Si `wiki/<ticker>/` no existe todavía, **detente y pregunta al usuario** si hay que crear la estructura primero — no la crees sin confirmar.

Localiza el PDF correspondiente en `wiki/<ticker>/raw/` antes de empezar. Si no existe, dilo y detente — no inventes contenido.

## Paso 1 — generar sources/ (mecánico, no LLM)

Instala `pymupdf4llm` si falta (`uv pip install pymupdf4llm`) y corre exactamente:

```python
import pymupdf4llm, pymupdf

doc = pymupdf.open("wiki/<ticker>/raw/<archivo>.pdf")
total_paginas = doc.page_count

md_text = pymupdf4llm.to_markdown("wiki/<ticker>/raw/<archivo>.pdf")
with open("wiki/<ticker>/sources/<YYYY-QN>-source.md", "w") as f:
    f.write(md_text)

print(f"PDF tiene {total_paginas} páginas")
print(f"Markdown generado: {len(md_text.splitlines())} líneas")
```

No leas el PDF tú mismo ni reescribas/limpies el output — guárdalo tal cual sale de la función, incluyendo cualquier ruido cosmético del OCR (es esperado y aceptable, ver `wiki/SCHEMA.md`). Confirma que el número de páginas del PDF quedó cubierto — si tienes cualquier duda sobre si el output está completo, detente y pregunta antes de continuar.

## Restricciones específicas de esta invocación

* Procesa un solo trimestre de una sola FIBRA por invocación, aunque el usuario pase varios argumentos — pregúntale cuál priorizar si manda más de uno.
* No toques `fundamentals.json` ni ningún archivo fuera de `wiki/`.
* Al terminar, resume en el chat qué páginas se crearon/editaron y qué quedó pendiente de confirmar con el usuario.
