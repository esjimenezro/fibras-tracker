# ESJ-14 — Queries entre FIBRAs (índice agregador)

**Linear:** [ESJ-14](https://linear.app/esjimenezro/issue/ESJ-14/roadmap-34-queries-entre-fibras-indice-agregador)
**Depende de:** ESJ-13 (módulo de consulta a la wiki, single-FIBRA — Done), ESJ-12/ESJ-27 (las 7 FIBRAs del catálogo ya tienen wiki completa — Done)
**Fecha:** 2026-09-17

## Contexto

ESJ-13 construyó `WikiQueryService`: un loop agéntico de tool-calling (`read_index`,
`read_page`, `read_fundamentals`) que responde preguntas en lenguaje natural sobre
**una** FIBRA, embebido en Fundamentales → Detalle. Un guard de servicio
(`_has_foreign_ticker`) aborta la consulta si el modelo intenta una tool call para
un ticker distinto al de `WikiQueryRequest.ticker`; `FileSystemWikiPageReadRepository`
rechaza además cualquier `page_name` con `/` (forma cualificada cross-FIBRA).
`wiki/SCHEMA.md` ya anticipaba extender esto ("Múltiples FIBRAs" / "Extensión
futura") una vez hubiera ≥3-4 FIBRAs activas en la wiki — condición ya cumplida:
las 7 FIBRAs del catálogo (FMTY14, DANHOS13, FIBRAPL14, FSHOP13, FUNO11, FNOVA17,
NEXT25) tienen wiki completa desde ESJ-27.

Este documento define cómo extender el servicio para responder preguntas que
crucen ≥2 FIBRAs, y qué es el "índice agregador" mencionado en el roadmap.

## Objetivo

Permitir dos experiencias nuevas, ambas sobre el mismo `WikiQueryService`:

1. **Fundamentales → Detalle:** el usuario, mirando una FIBRA, pregunta algo tipo
   "¿pasó algo similar en otra FIBRA?" sin nombrar cuál — el modelo debe poder
   descubrir y consultar otras FIBRAs de la wiki cuando lo juzgue relevante,
   mientras la respuesta sigue anclada a la FIBRA seleccionada.
2. **Fundamentales → Comparativa:** el usuario elige explícitamente ≥2 FIBRAs y
   pregunta de forma comparativa entre ellas, sin foco por defecto en ninguna.

## No objetivos

- Resolución de wikilinks cross-FIBRA a nivel de repositorio de archivos (ver
  Decisión 2 — no hace falta).
- Cambios a `fundamentals.json`, al módulo Radar, o a la Operación Ingest/Lint de
  la wiki.
- Un buscador semántico o vector DB — se mantiene la navegación por índice que ya
  usa el resto de la wiki.

## Decisiones de diseño

### Decisión 1 — Forma del "índice agregador"

El roadmap (`wiki/SCHEMA.md`) preveía un `wiki/index.md` raíz hecho a mano, igual
que las demás páginas de la wiki. Pero a diferencia de una página de trimestre o
de concepto (que sintetizan narrativa desde un PDF, con juicio editorial), el
índice raíz solo necesita listar, por cada FIBRA con wiki: ticker, nombre,
sector(es) y un link a su propio `index.md` — datos que **ya existen** en
`catalog.json` (fuente de verdad de nombre/sector) y en el roster de
`FileSystemWikiCatalogReadRepository` (qué tickers tienen wiki). No hay síntesis
que requiera guía humana; es un join mecánico.

Por eso el índice agregador tiene **dos consumidores del mismo formateo**, nunca
mantenido a mano:

- Un **tool en runtime**, `read_wiki_catalog()`, que el modelo llama para
  descubrir qué otras FIBRAs existen antes de decidir si vale la pena abrir su
  wiki.
- Un **archivo committeado** `wiki/index.md`, generado por un script
  (`scripts/generate_wiki_root_index.py`), para navegación humana en Obsidian
  (wikilinks cualificados a cada `index.md` por FIBRA). Se regenera a mano solo
  cuando cambia el roster de FIBRAs con wiki — evento raro, ya cerrado con
  ESJ-27 para las 7 actuales.

Ambos se alimentan de un único processor nuevo, `WikiRosterProcessor`, evitando
que el tool y el archivo diverjan en formato.

### Decisión 2 — Sin resolución de wikilinks cross-FIBRA en el repositorio

Cada tool call (`read_index`, `read_page`, `read_fundamentals`) ya recibe
`ticker` como argumento **separado** de `page_name`. Para pedir una página de
otra FIBRA, el modelo simplemente llama `read_page(ticker="FIBRAPL14",
page_name="2024-Q1")` — no necesita (ni debe) empaquetar el ticker dentro de
`page_name` con la forma `[[fibrapl14/2024-Q1]]`. Esa forma cualificada solo es
necesaria dentro del **texto de la respuesta final**, para que una cita como
`[[2024-Q1]]` no sea ambigua entre dos FIBRAs que comparten nombre de página —
es una instrucción de prompt, no un cambio de repositorio.

`FileSystemWikiPageReadRepository` no se toca. El guard que hoy rechaza `/` en
`page_name` sigue vigente (sigue siendo una forma de llamada inválida).

Se verificó que `CitationProcessor._WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")`
ya captura `/` sin cambios, y `render_citations` solo hace `join` de strings —
las citas cualificadas funcionan sin tocar ninguno de los dos.

### Decisión 3 — Scope como conjunto, no como igualdad

`WikiQueryRequest.ticker: str` se reemplaza por:

```python
tickers: list[str]                      # conjunto permitido (≥1) para tool calls
primary_ticker: Optional[str] = None    # ancla de la respuesta; None = comparación pura
```

- **Single-FIBRA (comportamiento de hoy, sin cambios observables):**
  `tickers=[T]`, `primary_ticker=T`.
- **Detalle, scope abierto (nuevo):** `tickers=<las FIBRAs con wiki>`,
  `primary_ticker=<FIBRA seleccionada>`.
- **Comparativa (nuevo):** `tickers=<N FIBRAs elegidas por el usuario>`,
  `primary_ticker=None`.

El guard (`_has_foreign_ticker`) pasa de comparar contra un único ticker a
comprobar membresía case-insensitive en `tickers`. Los mensajes fijos
(`OUT_OF_SCOPE_MESSAGE`, `UNGROUNDED_MESSAGE`) se generalizan para nombrar el
conjunto en vez de un solo ticker.

**Hallazgo importante (bug latente que este cambio expone):** hoy
`WikiQueryService._run_tool` ignora `tool_use.input["ticker"]` y siempre usa el
`request_ticker` único del servicio para decidir qué repositorio golpear — funciona
por casualidad porque en el mundo single-FIBRA ambos son siempre iguales (el
guard ya lo garantiza). En un mundo multi-ticker esto ya no es válido: dos tool
calls de la misma conversación pueden apuntar a FIBRAs distintas. `_run_tool`
debe enrutar usando `tool_use.input["ticker"]` (ya validado por el guard como
miembro de `tickers`), no un ticker único del request.

No se agrega validación cruzada `primary_ticker ∈ tickers` en el modelo — por
convención del repo (`modules/*/models/` no llevan validadores); las dos
llamadas de construcción (`ui/pages/fundamentals.py`) son responsables de armar
el request correctamente.

### Decisión 4 — UX

- **Detalle:** sin controles nuevos. El hilo de conversación se sigue
  guardando por FIBRA seleccionada (`st.session_state["wiki_chat"][primary_ticker]`);
  el request ahora manda como `tickers` el roster completo de FIBRAs con wiki.
- **Comparativa:** hoy no existe ningún selector de FIBRAs — la tabla y el chart
  siempre muestran las 7 juntas (`ui/pages/fundamentals.py`, `comparativa_tab`).
  Se agrega un `st.multiselect` (opciones = tickers con wiki, vía la
  `_load_wiki_catalog()` ya cacheada) que exige ≥2 selecciones antes de mostrar
  el chat. El hilo se guarda con clave `tuple(sorted(tickers))`, así cambiar la
  selección abre un hilo nuevo en vez de arrastrar contexto de otra combinación.
- El helper privado `_render_wiki_chat` (en `ui/pages/fundamentals.py`, no es un
  componente — sigue la convención de que las páginas orquestan, los
  componentes no llaman servicios) se generaliza para aceptar `tickers`,
  `primary_ticker`, una clave de hilo y el placeholder del `chat_input`, y lo
  reusan ambas tabs.

## Arquitectura resultante

```
modules/wiki/
  models/wiki_query_request.py         ← tickers + primary_ticker (Decisión 3)
  processors/
    wiki_roster_processor.py           ← NUEVO (Decisión 1)
  services/
    _wiki_query_prompt.py              ← instrucciones multi-ticker + tool nueva
    wiki_query_service.py              ← guard por conjunto, dispatch por tool_use.input["ticker"],
                                          nueva tool read_wiki_catalog
scripts/
  generate_wiki_root_index.py          ← NUEVO (Decisión 1)
wiki/
  index.md                             ← NUEVO, generado (Decisión 1)
ui/pages/fundamentals.py               ← Detalle: scope abierto; Comparativa: multiselect + chat
```

Ningún cambio en `modules/wiki/repositories/` (Decisión 2), ni en
`modules/fundamentals/`, ni en `modules/common/`.

## Testing

- `tests/wiki/services/test_wiki_query_service.py`: actualizar todos los
  `_request(...)` a `tickers`/`primary_ticker`; agregar casos para conjunto de
  ≥2 tickers (dispatch a la FIBRA correcta por tool call, guard con conjunto,
  mensajes generalizados, nueva tool `read_wiki_catalog`).
- `tests/wiki/processors/test_wiki_message_processor.py`: actualizar el único
  `WikiQueryRequest(ticker=...)` restante.
- `tests/wiki/processors/test_wiki_roster_processor.py`: nuevo, contra
  `catalog.json` real + el roster real de `wiki/`.
- Verificación manual en la app (Streamlit) para ambos flujos de UI — no hay
  test automatizado de UI en este repo.

## Fases de implementación

Ver plan detallado: `docs/superpowers/plans/2026-09-17-cross-fibra-wiki-queries.md`.
Cada fase es un sub-issue de ESJ-14 en Linear, siguiendo el patrón de ESJ-13.

1. Fase 1 — Modelo `tickers`/`primary_ticker` + guard por conjunto + fix de
   dispatch por `tool_use.input["ticker"]`.
2. Fase 2 — `WikiRosterProcessor` + tool `read_wiki_catalog`.
3. Fase 3 — Script `generate_wiki_root_index.py` + `wiki/index.md` committeado.
4. Fase 4 — UI Detalle: scope abierto a las 7 FIBRAs.
5. Fase 5 — UI Comparativa: multiselect + chat comparativo.
