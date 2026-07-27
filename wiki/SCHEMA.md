# wiki/SCHEMA.md — FibraLens Wiki (piloto FMTY14)

Este archivo gobierna cómo se mantiene la wiki. Se co-evoluciona con el tiempo: si detectas un error recurrente o una convención que falta, propón un cambio a este archivo antes de seguir ingiriendo.

## Propósito

Esta wiki NO duplica los datos numéricos que ya viven en `fundamentals.json` (NOI, AFFO, LTV, ocupación, etc. trimestre por trimestre — eso ya está resuelto por otro pipeline). Esta wiki captura el **contexto narrativo** que los números no cuentan por sí solos: qué dijo la administración, por qué se movió una cifra, qué eventos ocurrieron ese trimestre, cómo se conecta un trimestre con los anteriores.

Alcance v1: solo FMTY14. Sin vector DB, sin RAG — navegación por `index.md`.

## Convención de idioma

* **Contenido narrativo (cuerpo de las páginas de trimestre y de concepto): siempre en español.** Los PDFs fuente están en español, y las páginas citan o parafrasean directamente comentarios de la administración — traducir al escribir introduce riesgo de matiz y complica verificar la página contra el PDF original. No traducir al ingerir.
* **Estructura técnica (nombres de carpeta, claves de frontmatter, slugs de archivo): siempre en inglés**, por consistencia con el resto del repo (`models/`, `repositories/`, campos como `ticker`, `report_date`, `cbfis_with_rights`, etc.).
  * Los *valores* de frontmatter respetan el formato mexicano cuando aplica (ej. `quarter: 1T2024`, no `quarter: Q1-2024`).
  * Los slugs de concepto usan inglés cuando existe un término técnico común (`affo-trend`), y español cuando el término no tiene un equivalente más claro en inglés (`ocupacion`, `concentracion-inquilinos`). Ante la duda, preferir el término que el propio reporte usa más.
* `index.md` **y** `log.md`: encabezados de sección (`## Trimestres`, `## Conceptos`) y resúmenes de una línea en español, ya que son para navegación humana. El formato de fecha en `log.md` es ISO (`YYYY-MM-DD`) independientemente del idioma.

## Naming y referencias cruzadas

* **Nombres de archivo**: kebab-case. Páginas de concepto usan el slug en inglés/español según la regla de idioma de arriba (`affo-trend.md`, `concentracion-inquilinos.md`). Páginas de trimestre usan el código `YYYY-QN.md` (ej. `2024-Q1.md`) — mismo trimestre que `quarter: 1T2024` en frontmatter, pero en formato ordenable alfabéticamente.
* **Referencias cruzadas entre páginas de la wiki** (trimestre ↔ concepto): usar `[[wikilinks]]` (ej. `[[affo-trend]]`, `[[2024-Q1]]`), no rutas relativas de markdown — esto es lo que permite que Obsidian (u otra herramienta compatible) resuelva el grafo de la wiki automáticamente.
* **Referencias a la fuente** (`raw/`): siempre enlazar de vuelta al PDF original con ruta relativa estándar de markdown, no wikilink — ej. `[reporte 1T2024](../../raw/1T2024.pdf)`. Esto distingue una página de la wiki (que se navega vía wikilink) de un documento fuente (que se cita con un link normal).

## Estructura de directorios

```
wiki/
  fmty14/
    raw/                  # PDFs trimestrales tal cual, INMUTABLE
    sources/              # conversión fiel de cada PDF a markdown (1:1, sin síntesis)
    pages/
      quarters/           # una página por trimestre
      concepts/           # páginas temáticas que persisten a través de trimestres
    outputs/              # reportes de lint fechados (detalle completo)
    index.md
    log.md
  SCHEMA.md               # este archivo
```

## Extensión futura: múltiples FIBRAs

`index.md` y `log.md` son **por FIBRA, no globales** — cada FIBRA es su propia mini-wiki independiente bajo `wiki/<ticker>/` (fuentes, páginas, bitácora propios). Cuando se agregue una segunda FIBRA (ej. DANHOS13), se repite la misma estructura bajo `wiki/danhos13/`, sin tocar la de FMTY14.

Un `wiki/index.md` agregador a nivel raíz (que solo apunte a los `index.md` de cada FIBRA, sin duplicar su contenido) es una extensión deliberadamente diferida — no se justifica con una sola FIBRA activa, y probablemente tenga más sentido cuando el módulo Radar (comparativa entre FIBRAs) lo necesite, no antes. Esta es una decisión consciente, no un olvido.

## Capas y su mutabilidad

* **raw/** — inmutable. Nunca se edita ni se resume con pérdida. Fuente de verdad definitiva del contenido original.
* **sources/** — transcripción fiel y completa del PDF a markdown (`sources/YYYY-QN.md`), incluyendo tablas. Es determinística (una función 1:1 de `raw/`, sin síntesis ni interpretación), por lo que es barata de regenerar si se pierde y no requiere el mismo escrutinio que `pages/`. **Autoridad numérica:** cualquier cifra en `sources/` es solo para verificación cruzada — `fundamentals.json` es la única fuente de verdad para cálculos o citas numéricas (pasó por validación de identidad contable, conversión de unidades y correcciones que `sources/` no tiene). Si un número difiere entre ambos, `fundamentals.json` gana.
* **pages/** — el LLM la escribe y mantiene por completo, sintetizando a partir de `sources/` (no releyendo el PDF cada vez). El humano la lee y guía énfasis, no la edita a mano.
* **outputs/** — reportes de lint fechados, uno por corrida (`lint-YYYY-MM-DD.md`). Son un registro histórico, no se editan retroactivamente — si algo cambia, se corre un lint nuevo.
* **SCHEMA.md** — co-evoluciona con el humano.

## Tipos de página

### 1. Página de trimestre — `pages/quarters/YYYY-QN.md`

Una por cada reporte trimestral ingerido. Frontmatter:

```yaml
---
ticker: FMTY14
quarter: 1T2024
report_date: 2024-03-31
source_file: raw/1T2024.pdf
source_md: sources/2024-Q1.md
concepts_touched: [affo-trend, ocupacion]
created: 2026-07-26
updated: 2026-07-26
---
```

`created` es cuándo se escribió la página (normalmente = fecha de ingest); `updated` es la última vez que se tocó (ej. un trimestre futuro corrige algo de este).

Contenido: resumen narrativo del trimestre — qué dijo la administración, eventos relevantes (adquisiciones, refinanciamientos, cambios de portafolio, emisiones), y cualquier explicación textual de variación que el reporte mencione explícitamente (nunca inferida por el LLM).

### 2. Página de concepto — `pages/concepts/<slug>.md`

Hilo narrativo continuo de un tema a través de múltiples trimestres. Se **edita in place** cada vez que un trimestre nuevo lo toca — nunca se duplica. Frontmatter:

```yaml
---
title: Tendencia de AFFO/FFO
created: 2025-11-10
updated: 2026-07-26
quarters: [4T2023, 1T2024, ...]
confidence: high
---
```

`created` es la primera vez que el tema apareció como página propia; `updated` es la última edición (el trimestre más reciente que lo tocó). `confidence` distingue qué tan directa es la síntesis: `high` cuando el texto del reporte lo afirma explícitamente, `medium`/`low` cuando es una lectura del LLM conectando varios trimestres sin que ningún reporte lo haya dicho así de forma explícita. No aplica a páginas de trimestre — esas nunca infieren (ver regla de contenido arriba), siempre son `high` por definición.

**Regla de estabilidad ante backfilling** (relevante porque los trimestres se ingieren empezando por el más reciente y rellenando hacia atrás, no en orden cronológico): las secciones `## <Trimestre>` de una página de concepto narran **solo** lo que ese trimestre aportó — nunca lo caracterizan como "primera vez que ocurre esto", "el patrón comenzó aquí", "acumulado desde X" o cualquier síntesis que dependa de saber qué pasó (o no pasó) en trimestres *anteriores* aún no ingeridos. Esa clase de afirmación de tendencia solo puede vivir en el **párrafo introductorio** del concepto (antes de la primera sección `##`), porque ese párrafo se reescribe libremente en cada ingest que toca la página — a diferencia de las secciones por trimestre, que una vez escritas deberían poder quedar intactas cuando se inserta un trimestre más antiguo antes. Si al ingerir un trimestre nuevo se descubre que el párrafo intro ya no describe bien el patrón (ej. lo que parecía "la primera vez" no lo era), se corrige el intro, no las secciones por trimestre ya escritas.

## Regla: página nueva vs. editar existente

No hay lista fija de conceptos. Al ingerir un trimestre:

1. Revisa `index.md` (sección Conceptos) para ver si el tema ya tiene página.
2. Si existe → edítala, agrega la entrada nueva, actualiza `updated` y `quarters`.
3. Si no existe → evalúa si es (a) un tema que probablemente reaparezca en trimestres futuros (candidato a página de concepto nueva) o (b) un evento aislado de un solo trimestre (queda solo en la página de ese trimestre, sin página de concepto).
4. Ante la duda, no crear página de concepto todavía — es más barato promover un tema de "solo en la página del trimestre" a "página de concepto propia" en un ingest futuro, que deshacer una página duplicada.

## index.md

Catálogo de navegación, organizado en dos secciones:

```markdown
## Trimestres
- [[2024-Q1]] — <resumen de una línea>

## Conceptos
- [[affo-trend]] — <resumen de una línea, actualizado a 1T2024>
```

Se actualiza en cada ingest. Al responder una query, se lee este archivo primero para decidir qué páginas abrir.

## log.md

Bitácora cronológica, append-only, un renglón por evento. Solo se registran mutaciones a la wiki (ingest, lint) — las queries no se loguean, ya que son solo lectura y no cambian el estado de la wiki. El detalle completo de un lint vive en `outputs/`, no aquí — `log.md` solo apunta a él:

```markdown
## [2026-07-26] ingest | 1T2024 FMTY14
## [2026-07-26] lint | ver outputs/lint-2026-07-26.md
```

## Operación: Ingest

Uno a la vez (no batch), con el humano involucrado en cada paso:

1. Lee el PDF en `raw/` y genera su transcripción fiel completa en `sources/YYYY-QN.md` (incluye tablas; sin síntesis, sin interpretación).
2. A partir de `sources/`, comenta los puntos narrativos clave con el humano; el humano guía énfasis.
3. Escribe/actualiza la página de trimestre en `pages/quarters/`.
4. Identifica y actualiza (o crea) las páginas de concepto correspondientes en `pages/concepts/`, siguiendo la regla de arriba. Enlaza entre página de trimestre y páginas de concepto usando `[[wikilinks]]` en ambos sentidos.
5. Actualiza `index.md`.
6. Agrega entrada a `log.md`.

Invocable directamente vía `/wiki-ingest` — ver `.claude/skills/wiki-ingest/SKILL.md`.

## Operación: Query

1. Lee `index.md` para identificar páginas candidatas.
2. Abre esas páginas (trimestre y/o concepto según aplique) y sintetiza una respuesta. Si se necesita verificar una cifra o releer el texto exacto de un trimestre, consulta `sources/` en vez de reabrir el PDF.
3. Cita las páginas de la wiki de las que viene cada afirmación usando `[[wikilinks]]` (ej. "según [[2024-Q1]]...").
4. Si la respuesta es lo bastante valiosa como para persistir (una comparación, un análisis nuevo), ofrecer guardarla como página de concepto nueva.

Invocable directamente vía `/wiki-query` — ver `.claude/skills/wiki-query/SKILL.md`.

## Operación: Lint (periódica, no en cada ingest)

Revisar:

* Contradicciones entre páginas de concepto y trimestres más recientes.
* Páginas de concepto que ya no se han tocado en muchos trimestres (posible tema estancado o que debió fusionarse con otro).
* Temas mencionados en múltiples trimestres que aún no tienen página de concepto propia (candidatos a promover).
* Afirmaciones desactualizadas que un trimestre más reciente ya contradice.
* Páginas de concepto con `confidence: low` que ya acumularon suficientes trimestres como para reevaluar si suben a `medium`/`high`.

El detalle completo se guarda en `outputs/lint-YYYY-MM-DD.md` (aunque no haya hallazgos, para dejar rastro de que se corrió). `log.md` solo agrega el puntero a ese archivo, no el contenido.

Invocable directamente vía `/wiki-lint` — ver `.claude/skills/wiki-lint/SKILL.md`.
