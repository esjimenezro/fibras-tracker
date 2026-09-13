# Lint FUNO11 — 2026-09-12 (holístico, historia completa 1T2020–2T2026)

**Alcance y motivación:** durante la ingesta masiva (ticket ESJ-31) ya se corrieron 7 lints de checkpoint anual (`lint-2026-09-12.md` para 2020, y `lint-2026-09-12-2021.md` a `lint-2026-09-12-2026.md` para 2021–2026), cada uno comparando el año recién ingerido contra el año inmediatamente anterior. Esta corrida es distinta: es una relectura completa de `wiki/funo11/` como un solo objeto — las 26 páginas de trimestre, las 5 páginas de concepto completas (no solo su año más reciente), `index.md` y `log.md` — buscando específicamente lo que un checkpoint acotado a un año no puede ver: inconsistencias entre secciones de una misma página de concepto separadas por varios años.

No se aplicó ninguna corrección — el lint solo reporta (ver restricción de la skill `/wiki-lint`).

## 1. Contradicciones entre páginas de concepto y trimestres

Ninguna contradicción factual nueva (los 7 checkpoints ya cubrieron esto año por año, incluyendo las dos evoluciones narrativas ya documentadas explícitamente en 2025: el mecanismo de consolidación de FIBRA NEXT distinto del plan de 2023, y el refinamiento del porcentaje de Mitikah de ~32% a 38%). La relectura completa no encontró casos adicionales.

**Verificado explícitamente por esta corrida (sin hallazgos):** los valores numéricos de `perfil-crediticio.md` (tabla "Serie histórica", 26 filas) se cotejaron contra la prosa de las páginas de trimestre correspondientes en una muestra que cubre los tres años más recientes y los dos trimestres con retrofit de datos (2020-Q3, 2021-Q1) — todos coinciden exactamente, incluyendo los dos casos de cifras retrofiteadas contra `sources/` que documenta la nota de completitud de datos del concepto.

## 2. Páginas de concepto desactualizadas dentro de sí mismas (hallazgo nuevo de esta corrida)

**`pages/concepts/perfil-crediticio.md` — párrafo introductorio y sección "Lectura de la serie" congelados en el checkpoint de su promoción (2023), pese a que la tabla y la lista de trimestres sí se mantuvieron al día en cada checkpoint posterior:**

* El párrafo introductorio afirma "En todos los trimestres cubiertos (**1T2020–4T2023**) FUNO reportó cumplimiento..." — la tabla de la misma página ya cubre hasta 2T2026 (26 trimestres), no 16.
* La sección "Lectura de la serie" describe la trayectoria de LTV y cobertura solo hasta 2023 ("...una tendencia a la baja sostenida durante 2023 (42.0% → 40.1%)") y no menciona ninguno de los desarrollos posteriores que sí están en la tabla y en la lista de bullets: el repunte de LTV a 43.2% en 1T2025, la caída marcada a 37.8% en 4T2025 (el evento más notable de toda la serie, por el desapalancamiento vía consolidación del JV Next Properties), ni la cobertura de servicio de deuda de 1.92x en 2T2026 (máximo histórico de la serie, superando el 1.9x de 4T2021–1T2022).
* Es decir: la síntesis narrativa de esta página de concepto no se reescribió en los checkpoints de 2024, 2025 y 2026 aunque sí se actualizaron mecánicamente la tabla y la lista de trimestres — exactamente el tipo de discrepancia que un checkpoint anual (que solo mira el año que acaba de terminar contra el anterior) no detecta, porque el párrafo "desactualizado" nunca contradice al trimestre más reciente por sí solo, solo a la propia tabla de la misma página.
* Nota: esto no es una violación de la "regla de estabilidad ante backfilling" de `SCHEMA.md` (que protege las secciones `## <Trimestre>` ya escritas) — aplica al párrafo introductorio, que la regla explícitamente permite y espera que se reescriba libremente en cada ingest que toque la página.

**`pages/concepts/mitikah.md` — párrafo introductorio desactualizado de forma menor:** sigue describiendo que "su avance (CapEx invertido, compromiso del coinversionista, fecha estimada de conclusión) se reporta trimestre a trimestre", pero la propia sección `## 1T2026` de la misma página documenta que ese desglose trimestral terminó ese trimestre. Severidad baja — el lector llega a la información correcta si lee la página completa, pero el resumen inicial ya no describe el estado vigente.

## 3. Enlaces bidireccionales rotos (hallazgo nuevo de esta corrida)

`SCHEMA.md` exige enlazar trimestre ↔ concepto "en ambos sentidos". Se verificó programáticamente la dirección concepto→trimestre (sin problemas: los 5 conceptos enlazan correctamente a los 76 trimestres que declaran tocar) y la dirección trimestre→concepto (frontmatter `concepts_touched` vs. wikilinks reales en el cuerpo de las 26 páginas). Se encontraron **3 casos donde `concepts_touched` declara un concepto que el cuerpo de la página nunca enlaza**, aunque el contenido correspondiente sí está presente en prosa:

* **`pages/quarters/2021-Q2.md`** — declara `sostenibilidad-esg` en `concepts_touched`; la sección `## ASG` contiene el texto correspondiente (coincide palabra por palabra con la sección `## 2T2021` de `sostenibilidad-esg.md`) pero termina sin el `Ver [[sostenibilidad-esg]].` que sí llevan las demás secciones de la misma página.
* **`pages/quarters/2021-Q3.md`** — declara `reciclaje-activos`; la página menciona la recompra de CBFIs del trimestre dentro de la sección "Reflexión sobre política de distribución y asignación de capital", pero no hay ninguna mención ni wikilink a `[[reciclaje-activos]]` (el concepto sí tiene una sección `## 3T2021` con ese dato y su propio backlink `[[2021-Q3]]`).
* **`pages/quarters/2022-Q3.md`** — declara `sostenibilidad-esg`; la sección `## Otros reconocimientos` (reconocimiento de Éntrale) coincide con la sección `## 3T2022` de `sostenibilidad-esg.md`, pero de nuevo falta el `Ver [[sostenibilidad-esg]].` de cierre.

En los tres casos el dato es correcto y está en el lugar correcto — es puramente un enlace faltante, no un error de contenido. El patrón (3 de 3 casos son el último `## <sección>` de la página, justo antes del cierre del archivo) sugiere que el wikilink de cierre se omitió al terminar de escribir esas páginas específicas, no un problema sistemático del resto de la wiki.

## 4. Páginas de concepto estancadas / candidatas a reestructurar

Sin cambios respecto a lo ya documentado en los checkpoints de 2025 y 2026 — se consolidan aquí como recordatorio de los watch-items abiertos, no como hallazgos nuevos:

* **`reciclaje-activos.md`** — 10 trimestres consecutivos sin actividad narrativa (2024, 2025, 1T–2T2026). Recomendación ya planteada: evaluar marcar la página como "concepto histórico/inactivo" en frontmatter si Esteban confirma que no hay planes de reactivar la estrategia.
* **`internalizacion-fibra-next.md`** — watch-item abierto sobre si dividirla en dos conceptos (internalización del asesor vs. JV Next Properties/FIBRA NEXT) una vez que esta última desarrolle vida narrativa propia y separable. Con solo 2 trimestres post-culminación (1T–2T2026) sigue siendo prematuro decidir.
* **`mitikah.md`** — desde 1T2026 sin desglose financiero separado; probablemente no reciba actualizaciones trimestrales regulares en adelante salvo desarrollo narrativo nuevo (ej. Fase 2, "TBD" en todos los reportes).

## 5. Temas recurrentes sin página de concepto propia

Ninguno pendiente. Los dos candidatos que surgieron durante la ingesta (nearshoring, Alianza AXA Seguros/Portal Norte) fueron evaluados y retirados explícitamente en checkpoints previos (2023 y 2024) al no sostener continuidad narrativa.

## 6. Confidence

Las 5 páginas de concepto permanecen en `confidence: high` en toda su extensión — no hay párrafos con síntesis inferida por el LLM conectando trimestres sin respaldo textual explícito. Sin páginas que reevaluar.

## 7. Observación de proceso (no es un hallazgo de contenido)

`SCHEMA.md` especifica un archivo por corrida, `lint-YYYY-MM-DD.md`. FUNO11 acumuló 7 corridas de checkpoint anual en la misma fecha (2026-09-12) durante la ingesta masiva, disambiguadas con sufijo de año (`-2021` a `-2026`); este reporte holístico se guarda como `lint-2026-09-12-holistico.md` para no colisionar con esos 8 archivos ya existentes. Se documenta aquí para que quede explícito el motivo del sufijo, no como algo a corregir.

## Resumen

Hallazgos accionables: 3 enlaces bidireccionales faltantes (sección 3) y 2 párrafos de síntesis desactualizados en páginas de concepto (sección 2, uno de severidad media en `perfil-crediticio.md` y uno menor en `mitikah.md`). Todo lo demás verificado sin discrepancias: consistencia completa entre `concepts_touched` y los `quarters:` de cada concepto (26 trimestres, 0 discrepancias), exactitud numérica de la serie de perfil crediticio, ausencia de contradicciones nuevas, y ausencia de páginas `confidence: low`. Las correcciones de estos 5 hallazgos quedan para la sesión de corrección en conjunto con Esteban, conforme a la restricción de esta skill.
