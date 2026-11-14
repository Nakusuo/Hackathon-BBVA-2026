# Cifras públicas para calibrar y para el pitch

Regla: **ninguna cifra se cita en README, pitch o generador sin fuente original verificada**. Usar 3 o 4 cifras como máximo y documentarlas también en `data/QUALITY.md`.

| Cifra | Valor | Fuente (enlace exacto) | Estado | Uso |
|---|---|---|---|---|
| Peruanos que no cubrirían un mes de ingresos ante una emergencia | 61 % | *pendiente de citar* | Leída por el equipo, falta enlace | Pitch (dolor) + calibrar colchón |
| Ingreso promedio por tipo de trabajo (formal / independiente) | — | INEI (ENAHO) — *pendiente* | Por buscar | Calibrar montos del generador |
| Proporción de trabajadores formales e independientes | — | INEI — *pendiente* | Por buscar | Proporción de arquetipos |
| Calendario de CTS y gratificación | Mayo/nov y jul/dic | MTPE / gob.pe — *pendiente* | Por confirmar | Calendario del generador |

Estados posibles: `Por buscar` → `Por confirmar` → `Verificada (fecha)`.

## Fuentes de datos externos en tiempo real

| Dato | Fuente | Respaldo |
|---|---|---|
| Tipo de cambio PEN/USD | API del BCRP (alternativa: ExchangeRate-API) | Caché → último valor → serie grabada en el repo |

Citar la atribución de la fuente en el README.
