---
name: wiki-lint
description: Corre un chequeo de salud sobre la wiki de una FIBRA (wiki/<ticker>/), siguiendo la Operación Lint definida en wiki/SCHEMA.md. Úsalo cuando el usuario pida revisar, auditar o hacer lint de la wiki de cualquier FIBRA, o periódicamente después de varios ingests.
argument-hint: "[TICKER]"
---

# Wiki Lint

Sigue exactamente la Operación **Lint** definida en `wiki/SCHEMA.md`.

## Argumentos

`$ARGUMENTS` trae el ticker de la FIBRA a auditar. Si no se especifica y hay más de una FIBRA con wiki, pregunta cuál (o si son todas) antes de continuar.

## Restricciones específicas de esta invocación

- Guarda el reporte completo en `wiki/<ticker>/outputs/lint-YYYY-MM-DD.md` (usa la fecha de hoy). Agrega solo el puntero en `wiki/<ticker>/log.md`, nunca el detalle completo.
- No corrijas nada automáticamente — el lint solo reporta hallazgos; las correcciones a páginas existentes se hacen en sesión aparte con el humano.
