---
name: wiki-lint
description: Corre un chequeo de salud sobre la wiki de FMTY14 (wiki/fmty14/), siguiendo la Operación Lint definida en wiki/SCHEMA.md. Úsalo cuando el usuario pida revisar, auditar o hacer lint de la wiki, o periódicamente después de varios ingests.
---

# Wiki Lint — FMTY14

Sigue exactamente la Operación **Lint** definida en `wiki/SCHEMA.md`.

## Restricciones específicas de esta invocación

- No requiere argumento.
- Guarda el reporte completo en `wiki/fmty14/outputs/lint-YYYY-MM-DD.md` (usa la fecha de hoy). Agrega solo el puntero en `wiki/fmty14/log.md`, nunca el detalle completo.
- No corrijas nada automáticamente — el lint solo reporta hallazgos; las correcciones a páginas existentes se hacen en sesión aparte con el humano.
