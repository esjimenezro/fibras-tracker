---
name: wiki-query
description: Responde una pregunta narrativa sobre una FIBRA usando su wiki (wiki/<ticker>/), siguiendo la Operación Query definida en wiki/SCHEMA.md. Úsalo cuando el usuario pregunte algo tipo "¿por qué...", "¿cómo ha evolucionado...", sobre cualquier FIBRA con wiki (FMTY14, DANHOS13, etc.).
argument-hint: "[TICKER] <pregunta>"
---

# Wiki Query

Sigue exactamente la Operación **Query** definida en `wiki/SCHEMA.md`.

## Argumentos

`$ARGUMENTS` trae el ticker de la FIBRA y la pregunta del usuario, tal cual la escribió. Si no se especifica ticker y hay más de una FIBRA con wiki, pregunta a cuál se refiere antes de continuar.

## Restricciones específicas de esta invocación

- Esta skill es de solo lectura — no crea ni edita archivos directamente. Si la respuesta amerita convertirse en página de concepto nueva (paso 4 de Query), ofrécelo al usuario y espera confirmación antes de escribir nada.
- Si `wiki/<ticker>/index.md` no tiene páginas relevantes para la pregunta, dilo explícitamente — no inventes una respuesta ni releas todos los PDFs de `sources/` a ciegas.
