---
name: wiki-query
description: Responde una pregunta narrativa sobre FMTY14 usando la wiki (wiki/fmty14/), siguiendo la Operación Query definida en wiki/SCHEMA.md. Úsalo cuando el usuario pregunte algo tipo "¿por qué...", "¿cómo ha evolucionado...", que requiera contexto narrativo de los reportes.
argument-hint: "<pregunta>"
---

# Wiki Query — FMTY14

Sigue exactamente la Operación **Query** definida en `wiki/SCHEMA.md`.

## Argumento

`$ARGUMENTS` es la pregunta del usuario, tal cual la escribió.

## Restricciones específicas de esta invocación

- Esta skill es de solo lectura — no crea ni edita archivos directamente. Si la respuesta amerita convertirse en página de concepto nueva (paso 4 de Query), ofrécelo al usuario y espera confirmación antes de escribir nada.
- Si `wiki/fmty14/index.md` no tiene páginas relevantes para la pregunta, dilo explícitamente — no inventes una respuesta ni releas todos los PDFs de `sources/` a ciegas.
