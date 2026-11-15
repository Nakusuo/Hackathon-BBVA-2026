# Cifras públicas para calibrar y para el pitch

Regla: **ninguna cifra se cita en README, pitch o generador sin fuente original verificada**. Usar 3 o 4 cifras como máximo y documentarlas también en `data/QUALITY.md`.

| Cifra | Valor | Fuente (enlace exacto) | Estado | Uso |
|---|---|---|---|---|
| Adultos que **no** podrían cubrir un gasto imprevisto de un mes de ingresos | 61 % (39 % sí podría), 2026 | [Nota SBS, Encuesta de Capacidades Financieras SBS–CAF 2026](https://www.sbs.gob.pe/noticia/detallenoticia/idnoticia/4016) | Verificada (2026-11-14) | Pitch (dolor) + calibrar colchón |
| Tasa de empleo informal | 69,8 %, abr-2025 a mar-2026 (88,3 % en empresas de 1 a 10 trabajadores) | [INEI, EPEN, informe técnico I trim. 2026, cuadros 1.20 a 1.23](https://www.inei.gob.pe/media/MenuRecursivo/boletines/empleo-nacional-i-trimestre-2026.pdf) | Verificada (2026-11-14) | Pitch + proporción de arquetipos con ingreso irregular |
| Usuarios activos mensuales de Yape | 17,0 M al 30/09/2026 | [Credicorp 6-K 3T26](https://www.sec.gov/Archives/edgar/data/0001001290/000100129026000011/credicorpltdex-9913q26ingls.htm) | Verificada (2026-11-14) | Pitch: el canal digital ya existe |
| Alertas por SMS y app reducen cargos por sobregiro no acordado | −24 %, Reino Unido, 2015 (también bajaron los saldos 17 a 24 %) | [FCA, Occasional Paper 10](https://www.fca.org.uk/publications/occasional-papers/occasional-paper-no-10-message-received-impact-annual-summaries-text) | Verificada (2026-11-14) | Pitch: los avisos funcionan; decir también el efecto en saldos |
| Ingreso promedio por tipo de trabajo (formal / independiente) | — | INEI (ENAHO) — *pendiente* | Por buscar | Calibrar montos del generador |
| Proporción de trabajadores independientes | — | INEI — *pendiente* | Por buscar | Proporción de arquetipos |

**No usar en el pitch** (sin fuente primaria): Global Findex Perú 2024, usuarios de Plin, «gota a gota» (35 % según una nota de prensa), CAC bancario en Perú. Detalle en [../investigacion/negocio-impacto.md](../investigacion/negocio-impacto.md).
| Calendario de CTS y gratificación | Mayo/nov y jul/dic | MTPE / gob.pe — *pendiente* | Por confirmar | Calendario del generador |

Estados posibles: `Por buscar` → `Por confirmar` → `Verificada (fecha)`.

## Fuentes de datos externos en tiempo real

| Dato | Fuente | Respaldo |
|---|---|---|
| Tipo de cambio PEN/USD | API del BCRP (alternativa: ExchangeRate-API) | Caché → último valor → serie grabada en el repo |

Citar la atribución de la fuente en el README.
