"""Prompt shell, tool schemas and canned messages for WikiQueryService.

Pure content (no logic): the text the model is given and the fixed replies the
service returns when a query is out of scope or ungrounded. Kept apart from the
agentic loop so the control flow reads on its own.
"""

READ_INDEX_DESCRIPTION = (
    "Devuelve el índice de navegación (index.md) de la wiki de la FIBRA: la lista "
    "de páginas de trimestre y de concepto con un resumen de una línea de cada una. "
    "Úsalo primero para ubicar las páginas relevantes antes de leerlas."
)

READ_PAGE_DESCRIPTION = (
    "Devuelve el contenido completo de una página de la wiki de la FIBRA. page_name "
    "es un nombre estilo wikilink: una página de trimestre (\"2024-Q1\") o de concepto "
    "(\"plan-crecimiento\"), con o sin corchetes [[ ]] y con o sin sufijo .md. "
    "No se admiten referencias a otras FIBRAs (nombres con \"/\")."
)

READ_FUNDAMENTALS_DESCRIPTION = (
    "Devuelve las cifras crudas de fundamentals.json para la FIBRA (NOI, AFFO, LTV, "
    "ocupación, CBFIs, deuda, etc.) como JSON, una entrada por período. period es "
    "opcional; si se da, filtra a ese período exacto en formato \"1T2026\". Usa esta "
    "tool cuando necesites un número exacto en vez de una cifra parafraseada en la wiki."
)

INSTRUCTIONS_SHELL = (
    "Eres un asistente que responde preguntas sobre UNA FIBRA mexicana usando su "
    "wiki de contexto narrativo y sus cifras de fundamentals.json.\n\n"
    "La FIBRA de esta consulta es {ticker}. Responde solo sobre {ticker}: si la "
    "pregunta es sobre otra FIBRA, dilo y no llames a las tools con otro ticker.\n\n"
    "Tienes tres tools de solo lectura:\n"
    "- read_index(ticker): el índice de navegación de la wiki de la FIBRA.\n"
    "- read_page(ticker, page_name): una página de trimestre (p. ej. \"2024-Q1\") o "
    "de concepto (p. ej. \"plan-crecimiento\").\n"
    "- read_fundamentals(ticker, period?): las cifras crudas para la FIBRA, "
    "opcionalmente filtradas por período (formato \"1T2026\").\n\n"
    "Flujo: primero read_index para ubicar páginas candidatas; luego read_page para "
    "leerlas; usa read_fundamentals cuando necesites una cifra exacta. No inventes "
    "datos que no estén en la wiki o en fundamentals.\n\n"
    "Cita cada afirmación con el wikilink de la página de la que proviene, con el "
    "formato [[nombre-de-pagina]] (p. ej. \"según [[2024-Q1]], ...\"). Responde en "
    "español y de forma concisa.\n\n"
    "A continuación están las reglas que gobiernan la wiki (wiki/SCHEMA.md); síguelas "
    "para la Operación: Query.\n\n---\n\n"
)

STATUS_CONSULTING = "Consultando la wiki…"

# Returned as the answer when the model calls a tool for a different FIBRA.
OUT_OF_SCOPE_MESSAGE = (
    "Esta consulta es solo sobre {ticker}. Para preguntar sobre otra FIBRA, "
    "seleccionala en el menú de arriba."
)

# Returned when the model produced an answer without ever reading the wiki or
# fundamentals for this FIBRA (no successful in-scope tool call).
UNGROUNDED_MESSAGE = (
    "No pude fundamentar una respuesta en la wiki de {ticker} para esta pregunta."
)

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "read_index",
        "description": READ_INDEX_DESCRIPTION,
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Ticker de la FIBRA de esta consulta."},
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "read_page",
        "description": READ_PAGE_DESCRIPTION,
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Ticker de la FIBRA de esta consulta."},
                "page_name": {"type": "string", "description": "Nombre de página estilo wikilink."},
            },
            "required": ["ticker", "page_name"],
        },
    },
    {
        "name": "read_fundamentals",
        "description": READ_FUNDAMENTALS_DESCRIPTION,
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Ticker de la FIBRA de esta consulta."},
                "period": {"type": "string", "description": "Período exacto, formato \"1T2026\". Opcional."},
            },
            "required": ["ticker"],
        },
        "cache_control": {"type": "ephemeral"},
    },
]
