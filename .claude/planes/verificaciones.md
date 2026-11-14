# Registro de verificaciones

Una fila por veredicto de un juez. Lo más reciente arriba.

| Fecha y hora | Rama o módulo | Juez | Veredicto | Pendientes |
|---|---|---|---|---|
| 2026-11-14 12:15 | `planes/historias.md` | Revisión adversarial | CAMBIOS | C1–C5 críticos y A1–A13 advertencias (detalle abajo) |

## Revisión adversarial de historias (14/11 12:15)

Estado: `abierto` · `resuelto (cómo)` · `descartado (por qué)`.

### Críticos

| ID | Historia | Problema | Estado |
|---|---|---|---|
| C1 | HU-09, HU-05, CP-SIS-24 | HU-09 pide registrar «un gasto que se viene», pero CP-SIS-24 rechaza fechas futuras y `calcular_estado` descarta movimientos posteriores a `hoy` | resuelto: movimientos planificados hasta `hoy + 30` en `app.movimientos_usuario` entran al pronóstico en su fecha; HU-09, CP-SIS-24 y ARCHITECTURE §4.2 y §6.3 actualizados |
| C2 | HU-12 (CP-SIS-17) | Sin autenticación, el `customer_id` viene de la URL: pedir «otro cliente» devuelve sus datos y el criterio no se puede cumplir | resuelto: sesión de demo con token HMAC (`POST /sesion`), rutas `/yo/...` sin parámetro de cliente, 401 sin token o con firma inválida; HU-12, CP-SIS-17 y ARCHITECTURE §1, §5.2, §6 y §7 actualizados |
| C3 | HU-13, HU-05, HU-06 | «Deuda cara» necesita TCEA, que está cifrada en `seguro`; `Perfil` solo trae `nivel_deuda` | resuelto: la ingesta deriva `deuda_cara` y `deuda_cara_tramo` en `app.perfil`, umbrales en `supuestos.yaml`; HU-05, HU-06, HU-13, CP-SIS-08, negocio.md y ARCHITECTURE §4.1, §5.1 y §7 actualizados |
| C4 | HU-14 | El impacto se mide con el mismo pronóstico que elige las recos (circular) y asume 100 % de adherencia | resuelto: decide con datos hasta el mes 9 y se repite sobre las transacciones reales de los meses 10 a 12 con `aplicar_cambios`; adherencia 100 % y simulada; HU-14, plan §5, MG-13, metricas.md, rentabilidad-impacto.md y ARCHITECTURE §4.2 actualizados |
| C5 | HU-21 | La única historia de atracción es DEBERÍA y es lo primero que se recorta, aunque el juez pidió atraer | resuelto: A1 mínimo (5 preguntas → pronóstico, segmento por umbrales, una acción) es DEBE al cierre de la ola 1 y sale del orden de recorte; MAE queda en ola 2. HU-21, plan §2, §5 y §6, visión, CP-SIS-22, tareas (DX-17 / MG-14 / MC-12) actualizados |

### Advertencias

| ID | Historia | Problema | Estado |
|---|---|---|---|
| A1 | HU-04 | Sin regla fuera de la ventana de 3 a 7 días; el guion (27 vs `HOY_DEMO` 14) cae fuera; el `id` del aviso cambia si se mueve el día de riesgo; el límite puede tapar el aviso de la grati; falta el caso negativo | resuelto: ventana 1–2 urgente, 3–7 normal, > 7 sin aviso; semana lunes a domingo; `id` de riesgo = riesgo + próximo ingreso con upsert; lugar reservado para riesgo; `HOY_DEMO` según el guion. HU-04, CP-SIS-05, 28 y 29, ARCHITECTURE §4.1 y §6.2, MG-05, negocio.md, plan §6 y visión actualizados |
| A2 | Criterio común 1 | No es cierto para HU-14, 19, 20, 21 y 24; el monto que dice el usuario en el chat debe entrar a `simulate` o el verificador lo rechaza | resuelto: lista cerrada de fuentes (estado_cliente, eval, bcrp, fragmento RAG); las tools devuelven sus entradas; el juez acepta salidas, entradas, fechas y números del fragmento citado. Criterio común 1, negocio.md, ARCHITECTURE §6.4, JF-03, JF-04, CP-SIS-10, 11 y nuevo 30 actualizados |
| A3 | HU-11, HU-17 | Inyección persistente vía `app.memoria`; una preferencia puede vaciar las recos de ahorro | resuelto: memoria solo con listas cerradas (sin texto libre), tipos protegidos `bajar_deuda_cara` y `colchon_minimo`, filtro de frases prohibidas en el juez. HU-11, HU-17, ARCHITECTURE §4.2 y §6.4, negocio.md, plan §5, JF-04, JF-09, MG-04, CP-SIS-31 y 32 actualizados |
| A4 | HU-07 | Criterio por cliente puede fallar; faltan los casos de sueldo menor a los fijos y sin pago actual; sin caso de sistema | resuelto: elegible por volatilidad (no arquetipo), monto prudente con piso en fijos o alerta `falta_para_fijos`, sin pago apartar 0, criterio agregado con la repetición de HU-14. HU-07, tipo `SueldoLucas`, ARCHITECTURE §4 y §7, MG-07, CP-SIS-33 actualizados |
| A5 | Trazabilidad | Criterios sin caso: HU-06 c3, HU-10 c3, HU-12 c3, HU-13 c3, HU-16 c2, HU-18 c2, HU-19 c2, HU-08 c2 | resuelto: 15 casos nuevos (CP-SIS-34 a 48), CP-SIS-21 ampliado; matriz por historia con regla «cada criterio → caso o test con nombre»; ninguna historia DEBE sin caso |
| A6 | HU-05 | Ola 1 depende de metas (ola 2); la CTS no tiene criterio; «se acerca» sin ventana | abierto |
| A7 | HU-16 | «No crea días en rojo» es imposible para un gastador; faltan aporte no factible, estados cancelada y vencida | abierto |
| A8 | HU-15 | «Sin cambios de hábito» no está definido; los umbrales cambian de cuadrante con ruido | abierto |
| A9 | HU-18 | No está claro si el borrado incluye metas; `lucas_app` no tiene `DELETE` en `respuestas_reco` | abierto |
| A10 | HU-03 | La metamórfica necesita la semilla del bootstrap fija y definir p10, p50 y p90 | abierto |
| A11 | HU-19 | Falta el caso «no encontré fuente» | abierto |
| A12 | Evolución | Ninguna historia cubre la deduplicación en la ingesta | abierto |
| A13 | HU-10 | Falta qué hacer si la plantilla no extrae el monto, si la pregunta está fuera de tema, y la latencia < 8 s | abierto |

Sugerencias (S1–S8): personas mezcladas con cuadrantes, 60 s de HU-01, hormiga sin definir, HU-17 sin candidatos, criterio condicional de HU-08, número de pantallas, HU-20 sin caso, «facilidad» sin definir.
