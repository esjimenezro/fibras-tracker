---
title: Perfil crediticio — LTV y covenants de deuda
created: 2026-09-12
updated: 2026-09-12
quarters: [1T2020, 2T2020, 3T2020, 4T2020, 1T2021, 2T2021, 3T2021, 4T2021, 1T2022, 2T2022, 3T2022, 4T2022, 1T2023, 2T2023, 3T2023, 4T2023, 1T2024, 2T2024, 3T2024, 4T2024, 1T2025, 2T2025, 3T2025, 4T2025, 1T2026, 2T2026]
confidence: high
---

Serie histórica trimestral de LTV (Loan-to-Value) y los cuatro covenants financieros de la deuda de FUNO, tal como se reportan explícitamente en cada informe trimestral: (1) LTV — límite ≤60%; (2) límite de deuda garantizada — límite ≤40%; (3) razón de cobertura de servicio de la deuda — mínimo ≥1.5x; (4) activos totales no gravados — mínimo ≥150%. En todos los trimestres cubiertos (1T2020–2T2026) FUNO reportó cumplimiento ("Cumple") en los cuatro covenants.

Este concepto se promueve a página propia en el checkpoint de lint de 2023, tras haberse documentado como watch-item recurrente en los lints de 2021 y 2022 (tercer año consecutivo con la misma observación, ya con 16 trimestres de historial acumulado).

**Nota sobre completitud de datos:** las cifras de "deuda garantizada" y "activos totales no gravados" de 3T2020 y 1T2021 no estaban recogidas en la prosa original de esas páginas trimestrales (solo LTV y cobertura de servicio de deuda); se verificaron contra el `sources/` mecánico de esos trimestres (dato explícito del reporte, no inferido) y se completaron tanto aquí como en las páginas [[2020-Q3]] y [[2021-Q1]] correspondientes.

## Serie histórica

| Trimestre | LTV | Deuda garantizada (≤40%) | Cobertura serv. deuda (≥1.5x) | Activos no gravados (≥150%) |
|-----------|-----|---------------------------|--------------------------------|-------------------------------|
| 1T2020 | 45.3% | 3.1% | 1.90x | 214.8% |
| 2T2020 | 45.1% (42.9% ex-revolvente) | 2.9% | 1.73x | 213.8% |
| 3T2020 | 45.7% (42.1% ex-revolvente) | 2.8% | 1.58x | 211.0% |
| 4T2020 | 41.2% | 3.1% | 1.56x | 234.9% |
| 1T2021 | 42.7% | 3.0% | 1.54x | 225.7% |
| 2T2021 | 42.0% | 3.0% | 1.70x | 229.6% |
| 3T2021 | 43.0% | 3.0% | 1.79x | 224.2% |
| 4T2021 | 43.5% | 3.1% | 1.9x | 222.7% |
| 1T2022 | 43.5% | 3.4% | 1.9x | 225.0% |
| 2T2022 | 43.9% | 3.5% | 1.87x | 223.3% |
| 3T2022 | 44.2% | 3.6% | 1.83x | 222.6% |
| 4T2022 | 43.1% (post-revaluación mark-to-market) | 2.3% | 1.8x | 223.8% |
| 1T2023 | 42.0% | 2.3% | 1.70x | 229.8% |
| 2T2023 | 40.0% | 2.2% | 1.7x | 242.2% |
| 3T2023 | 40.8% | 2.5% | 1.63x | 236.5% |
| 4T2023 | 40.1% | 2.6% | 1.6x | 241.1% |
| 1T2024 | 40.1% | 2.4% | 1.59x | 241.0% |
| 2T2024 | 41.0% | 2.7% | 1.59x | 237.8% |
| 3T2024 | 42.3% | 2.7% | 1.60x | 229.6% |
| 4T2024 | 42.5% | 2.6% | 1.6x | 226.8% |
| 1T2025 | 43.2% | 3.2% | 1.72x | 226.2% |
| 2T2025 | 42.1% | 3.2% | 1.63x | 223.1% |
| 3T2025 | 42.5% | 3.9% | 1.65x | 233.7% |
| 4T2025 | 37.8% | 4.3% | 1.73x | 260.5% |
| 1T2026 | 38.7% | 4.0% | 1.83x | 253.7% |
| 2T2026 | 38.1% | 4.0% | 1.92x | 257.8% |

Todos los trimestres: cumplimiento ("Cumple") en los cuatro covenants.

## Lectura de la serie

El punto más ajustado de la serie es la cobertura de servicio de deuda en 3T2020 (1.58x) y 1T2021 (1.54x), ambos durante la recuperación post-COVID, acercándose al mínimo de 1.5x sin incumplirlo. Desde 2T2021 la cobertura se recupera de forma sostenida hasta rebasar 1.9x en 4T2021–1T2022. El LTV se mantuvo en un rango relativamente estable (40–46%) a lo largo de 2020–2023, con la caída más notable de ese periodo en 4T2022 asociada a una revaluación mark-to-market del portafolio (ver [[2022-Q4]]) y una tendencia a la baja sostenida durante 2023 (42.0% → 40.1%). El límite de deuda garantizada bajó de forma marcada a partir de 4T2022 (de ~3.5% a ~2.3–2.6%), consistente con el uso de recursos de reciclaje de activos para prepago de deuda garantizada (ver [[reciclaje-activos]]).

A partir de 2024 el LTV revirtió su tendencia a la baja, subiendo de forma gradual de 40.1% (1T2024) a 43.2% (1T2025) conforme se financiaron el CKD Helios y otras inversiones. El evento más notable de toda la serie ocurre en **4T2025**: el LTV cae de forma abrupta a **37.8%** (mínimo histórico), producto del desapalancamiento por la consolidación del JV Next Properties — FUNO transfirió ~US$3,000M de deuda al JV a cambio de ~US$2,300M de capital nuevo consolidado (ver [[internalizacion-fibra-next]]) — y se mantiene en niveles similares durante 1T–2T2026 (38.7%, 38.1%). La razón de cobertura de servicio de deuda también alcanza en **2T2026 su nivel más alto de toda la serie histórica (1.92x)**, superando el 1.9x de 4T2021–1T2022, reflejo tanto del desapalancamiento del JV como de la eliminación de "Honorarios de administración" tras la internalización del asesor.

## Trimestres que tocan este concepto

- [[2020-Q1]] — LTV 45.3%, primer trimestre de la serie, medidas defensivas de liquidez por COVID-19.
- [[2020-Q2]] — LTV 45.1% (42.9% ex-revolvente).
- [[2020-Q3]] — LTV 45.7% (42.1% ex-revolvente), cobertura más ajustada de la serie (1.58x).
- [[2020-Q4]] — LTV 41.2%, mejora significativa.
- [[2021-Q1]] — LTV 42.7%, cobertura 1.54x (mínimo histórico de la serie).
- [[2021-Q2]] — LTV 42.0%.
- [[2021-Q3]] — LTV 43.0%.
- [[2021-Q4]] — LTV 43.5%, refinanciamiento con Bono Sustentable.
- [[2022-Q1]] — LTV 43.5%, primera disposición del crédito sindicado de Mitikah.
- [[2022-Q2]] — LTV 43.9%.
- [[2022-Q3]] — LTV 44.2%, punto más alto de LTV de la serie.
- [[2022-Q4]] — LTV 43.1% tras revaluación mark-to-market; caída marcada en deuda garantizada.
- [[2023-Q1]] — LTV 42.0%, bonos sustentables y prepago de FUNO-18.
- [[2023-Q2]] — LTV 40.0%, recompra de bonos internacionales.
- [[2023-Q3]] — LTV 40.8%.
- [[2023-Q4]] — LTV 40.1%, bono verde y gestión proactiva ante ciclo electoral.
- [[2024-Q1]] — LTV 40.1% (estable), bono sustentable internacional US$600M para prepago de vencimiento 2024.
- [[2024-Q2]] — LTV 41.0% (ligero aumento).
- [[2024-Q3]] — LTV 42.3% (aumento).
- [[2024-Q4]] — LTV 42.5% (estable), bono sustentable internacional US$800M para prepago de bonos 2026.
- [[2025-Q1]] — LTV 43.2% (aumento); refinanciamiento US$800M y nuevos bonos 2032/2037.
- [[2025-Q2]] — LTV 42.1% (mejora); bonos sostenibles locales Ps.12,700M, vida promedio de deuda 8.2 años.
- [[2025-Q3]] — LTV 42.5% (aumento); prepago de Ps.10,000M post-cierre, vida promedio de deuda extendida a 8.5 años.
- [[2025-Q4]] — **LTV 37.8% (caída marcada)**, desapalancamiento por la consolidación del JV Next Properties (transferencia de ~US$3,000M de deuda, ~US$2,300M de capital nuevo consolidado).
- [[2026-Q1]] — LTV 38.7% (ligero aumento); salida del crédito hipotecario Bancomext de Samara (Ps.1,856.4M) como parte de la internalización.
- [[2026-Q2]] — LTV 38.1% (estable); cobertura de servicio de deuda de 1.92x, el nivel más alto de toda la serie histórica.
