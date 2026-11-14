# Casos de uso de Lucas

Versión 1.0 · 2026-11-14 · Responsable: Michael (arquitectura)

## Índice

1. [Propósito y alcance](#1-propósito-y-alcance)
2. [Actores](#2-actores)
3. [Diagrama](#3-diagrama)
4. [Fichas](#4-fichas)
   [CU-01](#cu-01--consultar-mi-estado-financiero) ·
   [CU-02](#cu-02--consultar-pronóstico-a-30-días) ·
   [CU-03](#cu-03--recibir-avisos-anticipados) ·
   [CU-04](#cu-04--obtener-recomendaciones) ·
   [CU-05](#cu-05--simular-un-cambio) ·
   [CU-06](#cu-06--registrar-un-movimiento) ·
   [CU-07](#cu-07--conversar-con-lucas) ·
   [CU-08](#cu-08--gestionar-meta-de-ahorro) ·
   [CU-09](#cu-09--controlar-mis-datos) ·
   [CU-10](#cu-10--probar-lucas-sin-ser-cliente) ·
   [CU-11](#cu-11--evaluar-impacto-y-evidencia) ·
   [CU-12](#cu-12--validar-sesión)
5. [Matriz de trazabilidad](#5-matriz-de-trazabilidad)
6. [Rutas por definir](#6-rutas-por-definir)

## 1. Propósito y alcance

Este documento modela con casos de uso UML lo que Lucas hace para cada actor. Responde a una sola pregunta del cliente: «¿cuánto puedo gastar o ahorrar este mes sin quedarme en rojo antes de mi próximo ingreso, y qué cambio me conviene más?». Sirve como entregable para el jurado y como referencia común para backend, front, IA y pruebas: cada flujo dice qué hace el actor, qué responde Lucas y qué pasa cuando algo sale distinto.

La fuente de verdad son las historias de [historias.md](../.claude/planes/historias.md). Si un caso y una historia chocan, manda la historia. Las 25 historias se agrupan en 11 casos de objetivo de usuario más un caso incluido (CU-12). La [matriz](#5-matriz-de-trazabilidad) dice dónde quedó cada historia y con qué casos de prueba de [pruebas.md](../.claude/planes/pruebas.md) se verifica. Las rutas citadas salen de [ARCHITECTURE.md](../ARCHITECTURE.md) §5–6; las que todavía no existen se marcan «por definir».

**Cómo leer una ficha**

- Los pasos del flujo principal van numerados. Un flujo alterno `4a` sale del paso 4 y vuelve al flujo principal salvo que diga otra cosa. Una excepción `E2.1` sale del paso 2 y termina el caso.
- `[Ola 2]` marca lo que no es del núcleo y se puede recortar sin romper el caso. `[Debería]` marca lo que solo entra si el núcleo funciona.
- Las reglas se citan como `S#` (seguridad del recomendador) y `C#` (chat y verificador), según su número en [negocio.md](../.claude/reglas/negocio.md). Los umbrales viven en `config/supuestos.yaml` y aquí nunca se escriben como cifra.
- Todas las fichas cumplen además los criterios comunes de las historias: cada cifra sale de una herramienta, los montos van en S/ con incertidumbre en palabras, toda recomendación muestra acción, impacto, por qué, supuestos, confianza y «tú decides», contraste AA y funcionamiento sin red.

## 2. Actores

| Actor | Tipo | Descripción |
|---|---|---|
| Cliente | Principal, abstracto | Persona con cuenta y movimientos en el banco. Lo concretan tres actores que heredan sus casos |
| Independiente | Principal (hereda de Cliente) | Cobra por recibo por honorarios, con pagos irregulares de varios clientes |
| Formal | Principal (hereda de Cliente) | Sueldo por quincena, gratificación y CTS |
| Comisionista o mixto | Principal (hereda de Cliente) | Fijo más variable, o empleo más un ingreso extra |
| Persona sin historial | Principal | Todavía no es cliente. No tiene sesión y Lucas no guarda nada suyo |
| Banco que integra a Lucas | Principal | Equipo de producto que evalúa licenciar Lucas. En la demo lo representa el jurado |
| Motor LLM | Secundario (sistema) | Redacta las respuestas del chat. Ollama local por defecto, Gemini apagado y plantillas siempre disponibles |
| BCRP | Secundario (sistema) | Fuente del tipo de cambio. Sin red se usa la serie grabada |

PostgreSQL no es un actor: forma parte de Lucas.

## 3. Diagrama

![Diagrama de casos de uso de Lucas](diagramas/casos-uso.svg)

Fuente: [diagramas/casos-uso.puml](diagramas/casos-uso.puml).

- `<<include>>`: el caso siempre ejecuta al otro. CU-01 a CU-09 incluyen CU-12 porque todos necesitan saber quién es el cliente. CU-07 incluye CU-05 cuando la pregunta es «¿me alcanza?».
- `<<extend>>`: el caso agrega comportamiento opcional a otro en un punto de extensión.
- `<<debería>>`: caso de borde punteado; solo se construye si el núcleo funciona.

## 4. Fichas

### CU-01 · Consultar mi estado financiero

| Campo | Valor |
|---|---|
| Actor principal | Cliente |
| Actores secundarios | — |
| Historias | HU-01, HU-02, HU-15 |
| Módulos y palanca | D3, D4, D5, D11, D13 · P1, P2 |
| Ola y prioridad | Ola 1 · DEBE (el cuadrante de HU-15 es ola 2) |
| Ruta | `GET /yo/estado` |
| Precondiciones | El cliente eligió su persona y tiene sesión válida. Tiene 12 meses de movimientos |
| Disparador | El cliente abre la pantalla Cómo estás |
| Postcondición de éxito | El cliente ve su puntaje, qué lo empuja hacia abajo, sus pagos recurrentes y su gasto hormiga |
| Garantía mínima | Nunca se muestran datos de otro cliente ni cifras que no salgan de `estado_cliente` |
| Puntos de extensión | `resumen-quincena` en el paso 4; `negocio-casa` en el paso 6 |

**Flujo principal**

1. El cliente abre Cómo estás.
2. Lucas valida la sesión (incluye CU-12).
3. Lucas calcula el estado del cliente a partir de sus movimientos.
4. Lucas muestra un puntaje de 0 a 100, sus componentes y una frase por componente.
5. Lucas lista los pagos que se repiten, con monto, frecuencia y próxima fecha.
6. Lucas muestra el total del gasto hormiga del mes en S/ y su peso frente al ingreso.
7. `[Ola 2]` Lucas muestra el cuadrante del cliente (ahorrador firme, se le escapa, ingreso justo o gastador) con su descripción.
8. El cliente decide por dónde empezar; puede pasar a CU-04.

**Flujos alternos**

- **5a.** Hay un cargo duplicado en el mismo periodo: Lucas lo marca como duplicado en la lista.
- **7a.** `[Ola 2]` El cliente lleva dos meses seguidos sin cambios de hábito: el cuadrante no cambia.

**Extensiones** `[Debería]`

- **Ver resumen de quincena** (HU-22), en `resumen-quincena`: al cierre de una quincena, Lucas muestra el cambio del puntaje y el componente que lo movió («subiste de 52 a 58 porque cancelaste una suscripción»).
- **Separar negocio y casa** (HU-25), en `negocio-casa`: Lucas etiqueta cada gasto del independiente como negocio o casa y muestra el total de cada uno.

**Excepciones**

- **E2.1.** La sesión no es válida: Lucas responde 401 y no muestra datos (CU-12).

**Reglas de negocio**

- Si un componente mejora (por ejemplo, baja la cuota frente al ingreso), el puntaje recalculado no baja.
- La pantalla responde en menos de 60 s desde que se elige la persona.

**Casos de prueba:** CP-SIS-01, CP-SIS-34, CP-SIS-44; tests de componente DI-07 (monotonicidad), DI-04 (F1 ≥ 0,85 en recurrentes) y DI-13 (estabilidad del cuadrante).

### CU-02 · Consultar pronóstico a 30 días

| Campo | Valor |
|---|---|
| Actor principal | Cliente |
| Actores secundarios | — |
| Historias | HU-03 |
| Módulos y palanca | D6 · P3 |
| Ola y prioridad | Ola 1 · DEBE |
| Ruta | `GET /yo/estado` |
| Precondiciones | Sesión válida |
| Disparador | El cliente abre la pantalla Qué viene |
| Postcondición de éxito | El cliente sabe cuánto tendrá cada día hasta su próximo ingreso y qué día podría quedar en rojo |
| Garantía mínima | La incertidumbre siempre se muestra; nunca un saldo futuro como cifra exacta |

**Flujo principal**

1. El cliente abre Qué viene.
2. Lucas valida la sesión (incluye CU-12).
3. Lucas pronostica el saldo diario de los próximos 30 días con su banda.
4. Lucas muestra el gráfico del saldo esperado con la banda, en S/ y con la incertidumbre en palabras («entre S/ 120 y S/ 380»).
5. Lucas marca el día de riesgo con su confianza en palabras (alta, media o baja).
6. El cliente decide si reacciona: probar un cambio (CU-05) o registrar un gasto que viene (CU-06).

**Flujos alternos**

- **5a.** No hay día de riesgo en los 30 días: Lucas muestra solo el saldo con su banda.
- **6a.** El cliente registra un gasto nuevo (CU-06) y vuelve a Qué viene: el pronóstico se recalcula con ese gasto (vuelve al paso 3).

**Excepciones**

- **E2.1.** La sesión no es válida: Lucas responde 401 y no muestra datos (CU-12).

**Reglas de negocio**

- Un gasto nuevo hace bajar el saldo pronosticado y nunca lo sube (por ejemplo, un gasto de S/ 200).
- Con ingresos parecidos, la banda de un independiente es más ancha que la de un formal.
- Un día de riesgo a más de 7 días solo se ve en esta pantalla, sin aviso (ver CU-03).

**Casos de prueba:** CP-SIS-02, CP-SIS-03, CP-SIS-35.

### CU-03 · Recibir avisos anticipados

| Campo | Valor |
|---|---|
| Actor principal | Cliente |
| Actores secundarios | BCRP |
| Historias | HU-04, HU-05, HU-24 |
| Módulos y palanca | D8, BCRP · P1, P2, P3, P6 |
| Ola y prioridad | Ola 1 · DEBE (HU-24 es Debería; el plan completo de grati y CTS es PODRÍA) |
| Ruta | `GET /yo/estado` (la API guarda los avisos) |
| Precondiciones | Sesión válida. Lucas conoce los avisos previos del cliente |
| Disparador | El cliente entra a Lucas |
| Postcondición de éxito | El cliente ve, antes de que pase, el riesgo o el evento que le conviene atender, con monto y acción |
| Garantía mínima | Repetir la consulta no duplica avisos ni gasta el límite semanal |

**Flujo principal**

1. El cliente entra a Lucas.
2. Lucas valida la sesión (incluye CU-12).
3. Lucas calcula la probabilidad de quedar en rojo antes del próximo ingreso y el día de riesgo.
4. La probabilidad supera el umbral de `config/supuestos.yaml` y el día de riesgo cae entre 3 y 7 días: Lucas arma un aviso normal con el monto en riesgo y su confianza.
5. Lucas junta los eventos de la semana (lunes a domingo, hora de Lima) y deja 3: el de riesgo, que tiene lugar reservado, y los 2 de mayor impacto en S/.
6. La API guarda los avisos con un identificador fijo por evento, sin duplicarlos.
7. Lucas muestra cada aviso con acción, impacto en S/, por qué, supuestos, confianza y «tú decides».
8. El cliente decide: mover un gasto, apartar plata, probar un cambio (CU-05) o no hacer nada.

**Flujos alternos**

- **3a.** Llega un ingreso «gratificación de julio» o CTS (por ejemplo, registrado en CU-06): Lucas arma un aviso con un reparto propuesto en S/ entre colchón, deuda cara y meta.
  - **3a1.** El cliente tiene `deuda_cara`: lo propuesto para la deuda no pasa del piso de su `deuda_cara_tramo`.
  - **3a2.** El cliente no tiene deuda cara: el reparto no tiene esa parte.
  - **3a3.** Se acerca el 28 de julio: el aviso menciona la subida de gasto esperada.
- **3b.** `[Debería]` El cliente tiene un pago propio en USD: Lucas consulta el tipo de cambio al BCRP y arma un aviso con el monto en S/, el tipo de cambio y su fecha, sin recomendar comprar ni vender.
  - **3b1.** No hay red: Lucas usa el último valor o la serie grabada y lo dice en el aviso.
- **4a.** El día de riesgo cae a 1 o 2 días: el aviso es urgente.
- **4b.** El día de riesgo cae a más de 7 días: no hay aviso; el riesgo solo se ve en CU-02.
- **4c.** La probabilidad no supera el umbral: no hay aviso de riesgo.
- **6a.** El cliente recarga la pantalla, o un movimiento nuevo mueve el día de riesgo antes del mismo próximo ingreso: Lucas actualiza el mismo aviso (fecha y monto) y no gasta otro lugar de la semana.

**Excepciones**

- **E2.1.** La sesión no es válida: Lucas responde 401 y no muestra datos (CU-12).

**Reglas de negocio**

- S8: máximo 3 avisos por semana, con lugar reservado para el de riesgo; nada de avisos de relleno.
- S2: el tipo de cambio solo se muestra ligado a pagos propios en USD.
- Solo la API guarda avisos. El simulador y las tools del chat los leen pero no los escriben.

**Casos de prueba:** CP-SIS-04, CP-SIS-05, CP-SIS-23, CP-SIS-28, CP-SIS-29, CP-SIS-36.

### CU-04 · Obtener recomendaciones

| Campo | Valor |
|---|---|
| Actor principal | Cliente |
| Actores secundarios | — |
| Historias | HU-06, HU-07, HU-13, HU-17 |
| Módulos y palanca | D7, D9, D14 · P1, P2, P3, P5 |
| Ola y prioridad | Ola 1 · DEBE («no me sirve» de HU-17 es ola 2) |
| Ruta | `GET /yo/estado`; marcar «no me sirve»: por definir |
| Precondiciones | Sesión válida |
| Disparador | El cliente abre la pantalla Qué hacer |
| Postcondición de éxito | El cliente tiene 3 acciones con monto que mejoran su mes y sabe por qué se las propone Lucas |
| Garantía mínima | Ninguna tarjeta rompe las reglas de seguridad S1, S7 y S10, pase lo que pase en los pasos anteriores |

**Flujo principal**

1. El cliente abre Qué hacer.
2. Lucas valida la sesión (incluye CU-12).
3. Lucas arma las recomendaciones candidatas, las puntúa por impacto en S/ × facilidad, las ajusta al perfil y aplica los filtros de seguridad al final.
4. Lucas muestra 3 tarjetas ordenadas por impacto × facilidad, cada una con «¿por qué?».
5. El cliente abre «¿por qué?» en una tarjeta.
6. Lucas muestra la acción, el impacto en S/, los datos usados, los supuestos, la confianza y «tú decides».
7. El cliente decide; puede probar la acción antes en CU-05.

**Flujos alternos**

- **3a.** El cliente tiene colchón menor a 1 mes o `nivel_deuda` alto: ninguna tarjeta sugiere crédito, tarjeta ni préstamo.
- **3b.** La volatilidad del ingreso, calculada de sus transacciones y nunca del arquetipo, supera el umbral: Lucas incluye el **Sueldo Lucas**, un monto quincenal prudente según sus quincenas malas, y cuánto apartar del pago actual.
  - **3b1.** El monto prudente no cubre sus gastos fijos por quincena: Lucas no muestra un Sueldo Lucas que lo deje en rojo. Muestra «en tus quincenas malas te faltan S/ X para tus fijos» y una recomendación para bajar fijos o armar colchón.
  - **3b2.** No hubo pago desde la última quincena: apartar es S/ 0 y Lucas dice cuántos días le alcanza el colchón.
- **3c.** El cliente tiene colchón de 3,00 meses o más y no tiene deuda cara: Lucas puede incluir una oferta de ahorro o inversión. Con 2,99 meses no hay ofertas de inversión.
- **3d.** El cliente tiene colchón de 3,2 meses y `nivel_deuda` bajo, pero `deuda_cara` (por ejemplo, una tarjeta con TCEA sobre el umbral): no hay ofertas de inversión ni de ahorro a plazo, y la primera tarjeta propone bajar esa deuda.
- **3e.** El cliente es *gastador*: recibe metas de ahorro (CU-08) en lugar de ofertas de inversión.
- **3f.** `[Ola 2]` El cliente pidió en el chat que no le hablen de un tipo de recomendación (CU-07, alterno 4d): Qué hacer deja de mostrar ese tipo.
- **6a.** `[Ola 2]` El cliente marca la tarjeta como «no me sirve»: Lucas guarda la respuesta; al recargar Qué hacer, esa recomendación no vuelve y aparece otra.
- **6b.** `[Ola 2]` El cliente tiene deuda cara y pide no ver la tarjeta de bajar esa deuda: la tarjeta sigue, porque es un tipo protegido igual que el colchón mínimo. Ninguna exclusión hace entrar una recomendación de crédito.

**Excepciones**

- **E2.1.** La sesión no es válida: Lucas responde 401 y no muestra datos (CU-12).

**Reglas de negocio**

- Orden del recomendador: candidatas → impacto (S/) × facilidad → ajuste por perfil → filtros de seguridad → top 3.
- S1: nunca crédito, tarjeta ni préstamo con colchón menor a 1 mes o deuda alta.
- S4 y S5: cada recomendación muestra sus seis campos y registra qué datos usó.
- S7 y S11: toda oferta es un tipo de producto genérico del catálogo ficticio, nunca un producto real o con marca.
- S10: ahorro a plazo o inversión solo con colchón de 3 meses o más y sin deuda cara.
- S12: «bajar deuda cara» y «colchón mínimo» no se pueden excluir con una preferencia.
- El Sueldo Lucas se valida en CU-11: en los clientes con ingreso irregular, repetir sus cambios sobre los meses 10 a 12 deja menos días en rojo que «no hacer nada» y que «apartar 10 % fijo», con intervalo, y la persona de la demo también mejora.

**Casos de prueba:** CP-SIS-07, CP-SIS-08, CP-SIS-09, CP-SIS-20, CP-SIS-32, CP-SIS-33, CP-SIS-37, CP-SIS-42, CP-SIS-43, CP-SIS-46.

### CU-05 · Simular un cambio

| Campo | Valor |
|---|---|
| Actor principal | Cliente |
| Actores secundarios | — |
| Historias | HU-08 |
| Módulos y palanca | D9, D11 · P1, P3 |
| Ola y prioridad | Ola 1 · DEBE |
| Ruta | `POST /yo/simular` |
| Precondiciones | Sesión válida |
| Disparador | El cliente abre el simulador, o CU-07 lo incluye ante una pregunta «¿me alcanza?» |
| Postcondición de éxito | El cliente ve cómo cambia su mes con el cambio y decide con números |
| Garantía mínima | No se guarda nada en la base hasta que el cliente agregue el movimiento (CU-06) |

**Flujo principal**

1. El cliente abre el simulador.
2. Lucas valida la sesión (incluye CU-12).
3. El cliente elige uno o más cambios; por ejemplo, cancelar 1 suscripción y bajar el delivery 20 %.
4. Lucas recalcula el estado con esos cambios, con el mismo cálculo que las pantallas y sin escribir nada.
5. Lucas muestra la banda nueva frente a la actual y el día de riesgo, si sigue.
6. El cliente decide; si quiere que un movimiento cuente, lo agrega en CU-06.

**Flujos alternos**

- **1a.** Lo incluye CU-07: los cambios llegan desde la pregunta del cliente, y la herramienta `simulate` los devuelve en su salida para que el verificador acepte sus montos. Sigue en el paso 4 y devuelve el resultado al chat.
- **5a.** El cambio alcanza: el día de riesgo desaparece.

**Excepciones**

- **E2.1.** La sesión no es válida: Lucas responde 401 y no simula (CU-12).
- **E3.1.** Un cambio no es válido (monto negativo o categoría inexistente): Lucas lo rechaza con un mensaje claro y no simula.

**Reglas de negocio**

- El simulador lee los avisos previos pero no guarda avisos.

**Casos de prueba:** CP-SIS-06, CP-SIS-38.

### CU-06 · Registrar un movimiento

| Campo | Valor |
|---|---|
| Actor principal | Cliente |
| Actores secundarios | — |
| Historias | HU-09 |
| Módulos y palanca | D9, D11 · P3 |
| Ola y prioridad | Ola 1 · DEBE |
| Ruta | `POST /yo/movimientos` |
| Precondiciones | Sesión válida |
| Disparador | El cliente quiere agregar un ingreso extra o un gasto que Lucas no conoce |
| Postcondición de éxito | El movimiento queda guardado y todas las pantallas lo toman en cuenta |
| Garantía mínima | Un movimiento inválido no se guarda |

**Flujo principal**

1. El cliente abre «agregar movimiento».
2. Lucas valida la sesión (incluye CU-12).
3. El cliente indica si es gasto o ingreso, el monto, la fecha y el comercio o descripción.
4. Lucas valida que el monto sea mayor que 0 y que la fecha no pase de hoy + 30 días.
5. Lucas revisa si el movimiento coincide con una recurrente ya detectada.
6. Lucas guarda el movimiento.
7. Todas las pantallas se recalculan con el movimiento nuevo.

**Flujos alternos**

- **3a.** La fecha es hoy o pasada: el movimiento se guarda como historia.
- **3b.** Es un gasto con fecha dentro de los próximos 30 días (por ejemplo, S/ 450): el pronóstico lo descuenta ese día exacto y no hoy. Si deja el saldo en rojo, aparece el día de riesgo (CU-02 y CU-03).
- **3c.** Es un ingreso «gratificación de julio» o CTS: además se dispara el aviso de reparto (CU-03, alterno 3a).
- **5a.** Coincide con una recurrente (mismo comercio y monto parecido): Lucas avisa, antes de guardarlo, que ya lo tiene contado; el cliente decide si lo guarda igual.

**Excepciones**

- **E4.1.** El monto es 0, negativo o texto: Lucas lo rechaza con un mensaje claro.
- **E4.2.** La fecha no es válida: Lucas la rechaza con un mensaje claro.
- **E4.3.** La fecha está a más de 30 días: Lucas la rechaza con un mensaje claro.

**Reglas de negocio**

- Toda entrada pasa por validación Pydantic (montos, fechas y categorías válidas).

**Casos de prueba:** CP-SIS-24, CP-SIS-39.
