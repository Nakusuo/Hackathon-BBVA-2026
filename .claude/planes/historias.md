# Historias de usuario del MVP

Solo lo que hace el MVP que está en `develop`. Cada historia dice en qué pantalla vive, a qué palanca de ingreso se ata (`P#`, ver [rentabilidad-impacto.md](../reglas/rentabilidad-impacto.md)) y qué prueba la cubre. Las pruebas son las de `frontend/pruebas/` (`npm test`) y `frontend/e2e/` (`npm run e2e`); se citan por archivo y por el nombre del test.

Los números se conservan de la versión anterior porque el código y las pruebas ya los citan. Por eso faltan algunos.

## Cómo está armado el MVP

- Lucas vive dentro de **Banco Vértice**, una banca ficticia con datos sintéticos (`frontend/`, React + Vite).
- Todas las cifras de las pantallas, de los avisos y del chat salen del **motor del front** (`frontend/src/motor/`): un pronóstico con banda y un recomendador simples, iguales para las dos personas. Así ninguna pantalla contradice a otra.
- El front también lee la API FastAPI (`backend/src/api/`). Hoy esa API devuelve datos fijos de otra persona (`demo-001`), así que sus respuestas se validan pero no cambian ninguna cifra visible.
- Lo que la persona elige (tips, gastos planificados, metas, avisos vistos, permiso) se guarda en el navegador.

## Personas

| Persona | Quién es | Por qué le importa Lucas |
|---|---|---|
| **Independiente** | Cobra por recibo por honorarios de 2 clientes; el monto cambia cada mes. Es la persona de la demo | No sabe si llega a su próximo cobro; su banda es la más ancha |
| **Formal** | Sueldo fijo por quincena | Llega justo a fin de mes y no sabe dónde se le va la plata |
| **Banco que integra a Lucas** | Equipo de producto que evalúa licenciarlo (lo representa el jurado) | Necesita ver impacto en S/ y por qué pagaría |

Las dos personas cliente se eligen al ingresar y en Más → Preferencias.

## Criterios comunes a todas las historias

Se cumplen siempre; no se repiten en cada historia.

1. Toda cifra de cliente sale del motor del front con los datos de la persona elegida; nunca se escribe a mano en un texto (`frontend/pruebas/personas.test.js`: «las cifras de la vista salen del motor con los datos de esa persona»). Las cifras de Evidencia salen de `models/metricas*.json`.
2. Montos en S/. La incertidumbre se muestra como banda y como «peor caso», que es el borde bajo de la banda.
3. Todo tip, aviso o meta muestra la acción, su efecto en S/, un «¿Por qué?» y «Tú decides».
4. Texto de 16 px o más, contraste AA en claro y oscuro, nada depende solo del color y cada pantalla principal cabe en 1,5 pantallas de celular (`frontend/e2e/pantallas.spec.js`).
5. Funciona sin internet y sin la API. Si la API no responde en 4 s, Lucas dice «Sin conexión: te muestro tus últimos datos.» y las cifras no cambian (`frontend/e2e/pantallas.spec.js`: «si la API se cae, Lucas lo dice y las cifras y "Lo hago" siguen funcionando»).
6. Datos 100 % sintéticos y sin marca ni colores de BBVA (`frontend/pruebas/marca.test.js`).

---

### HU-26 · Encontrar a Lucas dentro de mi banca

> Como **cliente**, quiero que Lucas aparezca en mi banca de siempre y me diga qué ve venir, para no tener que buscarlo.

- Pantallas: `/ingresar`, `/banca` · Palanca: P2
- **Dado** el ingreso a Banco Vértice, **cuando** elijo la persona y entro, **entonces** veo mi banca con saldo, cuentas, accesos y los 3 últimos movimientos, y puedo ocultar los montos.
- **Dado** que Lucas está activo, **entonces** la banca muestra una tarjeta de Lucas antes de los accesos: «Lucas te avisa» si el rojo está a 7 días o menos, y «Lucas lo ve venir» si está más lejos. Si ya no hay rojo, dice que llego a mi cobro.
- **Dado** que es mi primera entrada a Lucas, **entonces** veo una guía de 3 pasos con «Saltar», y la puedo volver a abrir con «?».
- Pruebas: `frontend/e2e/pantallas.spec.js` («ingreso, permiso, banca, Lucas y guía de primera vez», «la banca puede ocultar los montos», «lo importante se ve sin bajar»)

### HU-23 · Dar mi permiso y pedir que me lo expliquen fácil

> Como **cliente**, quiero saber qué datos usa Lucas antes de activarlo y poder pedir una explicación sencilla, para entender sin ser experto.

- Pantallas: `/consentimiento`, Resumen y Qué viene · Palanca: P2
- **Dado** que entro a Lucas sin haber dado permiso, **entonces** veo qué datos usa, para qué, que los datos son sintéticos y cómo retirarlo.
- **Dado** «Ahora no», **entonces** la banca queda sin Lucas; **dado** «Acepto», **entonces** vuelvo a donde iba.
- **Dado** que el permiso es de cada persona, **entonces** el del independiente no vale para el formal.
- **Dado** «Explícamelo fácil» en Resumen o Qué viene, **entonces** la pantalla se explica en frases cortas, con «peor caso» en palabras simples y sin cifras nuevas.
- Pruebas: `frontend/pruebas/sesion.test.js`, `frontend/pruebas/explicaciones.test.js`; `frontend/e2e/pantallas.spec.js` («consentimiento: "Ahora no" deja la banca sin Lucas…», «"Explícamelo fácil" en … explica el peor caso»)

### HU-01 · Saber cómo estoy

> Como **formal**, quiero ver qué tan sana está mi plata y qué la empuja hacia abajo, para saber por dónde empezar.

- Pantalla: Salud (desde el Resumen) · Palanca: P2
- **Dado** una persona, **cuando** abre Salud, **entonces** ve un puntaje de 0 a 100 que es el promedio de 4 partes (colchón, deudas, regularidad del ingreso y control del gasto), con una frase por parte.
- **Dado** una parte del puntaje, **entonces** lleva a la pantalla donde se puede mejorar (tips, apartar al cobrar, próximos pagos o chat).
- **Dado** que elijo tips que evitan días en rojo, **entonces** el puntaje sube y nunca baja.
- La pantalla dice «Cálculo provisional»: es una regla del motor, no el modelo de salud de `backend/src/models/salud.py`.
- Pruebas: `frontend/pruebas/motor.test.js` («la salud sube con cada día en rojo que se evita y es el promedio de sus partes»); `frontend/e2e/pantallas.spec.js` («cada parte de la salud lleva a una acción»)

### HU-02 · Ver en qué se me va la plata

> Como **formal**, quiero ver mis gastos por categoría y mis suscripciones, para cortar lo que no uso.

- Pantallas: Gastos y su detalle · Palanca: P1
- **Dado** una persona, **cuando** abre Gastos, **entonces** ve cuánto gastó en los últimos 30 días en un gráfico circular (hasta 5 categorías más «Otros») con su porcentaje, y los porcentajes suman 100.
- **Dado** el detalle, **entonces** cada categoría se compara con su promedio de 3 meses; una diferencia de hasta S/ 5 se lee «como siempre».
- **Dado** sus suscripciones, **entonces** ve monto, día de cobro y cuánto las usa, y puede pausar la que no usa; esa pausa queda elegida también en los tips.
- El gasto hormiga (café y snacks) es una categoría más.
- Pruebas: `frontend/pruebas/categorias.test.js`; `frontend/e2e/pantallas.spec.js` («Gastos compara cada categoría con el promedio», «MusiKa se pausa desde Suscripciones y queda elegida en los tips»)

### HU-03 · Saber qué viene en los próximos 30 días

> Como **independiente**, quiero ver cuánto tendré cada día hasta mi próximo cobro y qué día podría quedar en rojo, para reaccionar a tiempo.

- Pantalla: Qué viene · Palanca: P3
- **Dado** una persona, **cuando** abre Qué viene, **entonces** ve el saldo esperado con su banda en línea punteada, con etiquetas directas («Hoy», «Cobro», «Peor caso −S/ 60») y la lista de pagos y cobros.
- **Dado** el selector, **entonces** cambia entre «hasta mi cobro» y «30 días».
- **Dado** un gasto extra, **entonces** el peor caso baja en ese mismo monto y nunca sube.
- **Dado** el mismo día, **entonces** la banda del independiente es más ancha que la del formal.
- Pruebas: `frontend/pruebas/motor.test.js` («un gasto extra empeora el peor caso en ese mismo monto»), `frontend/pruebas/personas.test.js` («la banda del independiente es más ancha que la del formal (HU-03)»), `frontend/pruebas/grafico.test.js`; `frontend/e2e/pantallas.spec.js` («el gráfico de Qué viene lleva etiquetas directas…», «Qué viene cambia de periodo…»)

### HU-04 · Que Lucas me avise antes de quedar en rojo

> Como **independiente**, quiero que Lucas me avise días antes de un posible saldo en rojo, para mover un gasto o apartar plata a tiempo.

- Pantallas: bandeja de Avisos (campana), tarjeta de la banca y aviso del Resumen · Palanca: P2, P3
- **Dado** que el peor caso queda en rojo antes del próximo cobro a 3–7 días, **entonces** hay un aviso normal; a 0–2 días, uno urgente; a más de 7, no hay aviso y el riesgo solo se ve en Qué viene y en «Lucas lo ve venir».
- **Dado** que el pronóstico no queda en rojo, **entonces** no hay aviso de riesgo.
- **Dado** 4 avisos en la misma semana (lunes a domingo), **entonces** se ven 3: el de riesgo, que tiene lugar reservado, y los 2 de mayor efecto en S/.
- **Dado** que un gasto nuevo adelanta el rojo antes del mismo cobro, **entonces** se actualiza el mismo aviso y no gasta otro lugar.
- **Dado** un pago, **entonces** solo avisa si hay algo que hacer (por ejemplo, pausar una suscripción que casi no usa).
- **Dado** «¿Por qué?» en un aviso, **entonces** ve los datos usados, el supuesto y qué tan seguro es (alta, media o baja), con «Urgente» o «Aviso» en texto y no solo en color.
- **Dado** el bloque de demo de la bandeja, **entonces** se puede probar la regla sin gastar el tope de la semana real.
- Pruebas: `frontend/pruebas/avisos.test.js` (casos CP-SIS-05, 28 y 29); `frontend/e2e/pantallas.spec.js` («Avisos: …»)

### HU-06 · Recibir tips con monto

> Como **independiente**, quiero cambios concretos con su efecto en S/, para no tener que adivinar qué cambiar.

- Pantalla: Resumen, «Tips para tu día más justo» · Palanca: P1, P3
- **Dado** una persona, **entonces** ve sus tips ordenados de mayor a menor efecto, cada uno con «+S/ X para tu día más justo», «Evitas N días en rojo» y «¿Por qué?».
- **Dado** «Lo hago» en un tip, **entonces** el aviso, el gráfico, la banca, la salud y el chat se recalculan con ese cambio, y queda recordado al volver.
- **Dado** que elige todos sus tips, **entonces** ya no queda en rojo antes del cobro (en la demo: −S/ 60 → +S/ 12, días en rojo 2 → 0).
- **Dado** un tip elegido, **entonces** ve su seguimiento («Llevas 0 de 2 veces en RapiFood hasta el 30 nov»).
- **Dado** cualquier tip o respuesta, **entonces** nunca sugiere crédito, tarjeta ni préstamo.
- Pruebas: `frontend/pruebas/motor.test.js` («cada tip que se activa con "Lo hago" mejora el peor caso, y con todos ya no hay rojo», «las tarjetas de tips no cambian de orden al elegir»), `frontend/pruebas/explicaciones.test.js` («el texto fácil no usa palabras de asesoría ni de crédito»); `frontend/e2e/pantallas.spec.js` («"Lo hago" recalcula el plan en todas las pantallas y se recuerda»)

### HU-07 · Saber cuánto apartar al cobrar

> Como **independiente**, quiero saber cuánto puedo apartar el día que cobro sin volver al rojo, para ahorrar aunque cobre irregular.

- Pantalla: Resumen, tarjeta «Después de cobrar» · Palanca: P1
- **Dado** el próximo cobro, **entonces** Lucas propone el mayor monto, en múltiplos de S/ 10, que no deja en rojo ni en el peor caso del resto de los 30 días; S/ 10 más ya dejaría en rojo.
- **Dado** que no hay margen después del cobro, **entonces** dice «Al cobrar, todavía no te conviene apartar» y no propone nada.
- **Dado** que elige tips, **entonces** lo que puede apartar nunca baja (en la demo: S/ 40 sin tips, S/ 150 con los 3).
- Pruebas: `frontend/pruebas/motor.test.js` («el apartado propuesto no deja en rojo y S/ 10 más ya sí», «sin margen después del cobro no se propone apartar nada», «activar tips nunca reduce lo que se puede apartar»)

### HU-08 · Probar un gasto o un ingreso antes de agregarlo

> Como **independiente**, quiero simular un gasto o un ingreso que se viene y ver cómo cambia mi mes, para decidir con números.

- Pantalla: Qué viene, «Simular un gasto o ingreso» · Palanca: P1, P3
- **Dado** un gasto o ingreso con monto y fecha, **cuando** lo escribo, **entonces** la banda, el peor caso y los días en rojo cambian en vivo (en la demo: S/ 450 el 5 dic, días en rojo 2 → 12).
- **Dado** que el gasto deja en rojo, **entonces** Lucas dice cuánto cabe ese día sin sumar días en rojo o, si nada cabe, cuánto después del cobro.
- **Dado** un ingreso antes del día más justo, **entonces** puede quitar el rojo.
- **Dado** cualquier simulación, **entonces** no se guarda nada hasta «Agregar a mi pronóstico».
- Pruebas: `frontend/pruebas/planificar.test.js` («simular no guarda nada…», «cuánto cabe…», «un ingreso planificado antes del día más justo puede quitar el rojo»); `frontend/e2e/simulador-metas.spec.js` («simulador: …»)

### HU-09 · Agregar un gasto o ingreso que viene

> Como **independiente**, quiero agregar a mi pronóstico un gasto o un ingreso que ya sé que viene, para que Lucas lo tome en cuenta.

- Pantalla: Qué viene, «Agregar a mi pronóstico» · Palanca: P3
- **Dado** un gasto de S/ 450 con fecha entre mañana y hoy + 30 días, **cuando** lo agrego, **entonces** se descuenta ese día exacto (no hoy) y todas las pantallas se recalculan; si deja en rojo, aparece en el aviso del Resumen.
- **Dado** un gasto que coincide con un pago conocido (mismo comercio y monto parecido), **entonces** Lucas avisa que ya lo tiene contado.
- **Dado** un monto 0, negativo, texto, vacío, con más de dos decimales o sobre el tope, **entonces** se rechaza con un mensaje junto al campo.
- **Dado** una fecha de hoy, pasada, a más de 30 días o que no existe, **entonces** se rechaza con un mensaje claro: planificar es solo hacia adelante.
- Pruebas: `frontend/pruebas/planificar.test.js` («un gasto de S/ 450 se descuenta el día exacto, no hoy», «rechaza monto 0…», «rechaza fechas…», «avisa si el gasto ya es un pago conocido…»); `frontend/e2e/simulador-metas.spec.js`

### HU-16 · Crear una meta de ahorro

> Como **cliente**, quiero que Lucas me diga cuánto apartar en cada cobro para llegar a una meta, para ahorrar sin quedar en rojo.

- Pantalla: Metas (desde «Tus metas» del Resumen) · Palanca: P1
- **Dado** un nombre, un monto, lo ya ahorrado y una fecha desde el próximo cobro (por defecto, 31 de diciembre), **entonces** la meta se crea con el aporte por cobro que sale del apartado de HU-07, la fecha en que llegaría y una confianza alta, media o baja.
- **Dado** el aporte propuesto, **entonces** no crea días en rojo y nunca pasa de lo que falta.
- **Dado** varias metas abiertas, **entonces** el apartado se reparte en el orden en que se crearon y la suma no se pasa.
- **Dado** una meta, **entonces** pasa de creada a en curso a cumplida, sin saltarse estados.
- **Dado** que no hay cobros antes de la fecha, **entonces** no promete llegar ni propone aporte.
- Pruebas: `frontend/pruebas/metas.test.js`; `frontend/e2e/simulador-metas.spec.js` («metas: …»)

### HU-10 · Preguntar «¿me alcanza?» en el chat

> Como **formal**, quiero preguntar con mis palabras si llego a fin de mes con un gasto, para no tener que leer gráficos.

- Pantalla: Chat · Palanca: P6
- **Dado** «¿llego a fin de mes si gasto S/ 150 en un regalo?», **entonces** la respuesta usa el motor con los tips elegidos y muestra las cifras en un bloque «Calculado con tus datos».
- **Dado** un gasto mayor que el saldo o un peor caso ya en rojo, **entonces** nunca responde «Sí, te alcanza».
- **Dado** «quiero juntar para un carro a fin de año», **entonces** arma un plan con el mismo cálculo de Metas; si el precio está en dólares, lo pasa a soles con el tipo de cambio de referencia y su fecha, sin recomendar comprar ni vender dólares.
- **Dado** «explícame más» o «¿por qué?», **entonces** explica el cálculo del último tema; si no hay tema, no inventa.
- **Dado** una pregunta que no entiende, **entonces** lo dice sin inventar cifras.
- **Dado** el front con `VITE_CHAT_AGENTE=si`, **entonces** pregunta al agente por `POST /api/v1/chat` y muestra ✓ solo en cifras verificadas; si el agente falla, tarda más de 12 s o no verificó, lo dice y responde con la plantilla. Hoy la API devuelve un mock sin verificar, así que en el MVP siempre responde la plantilla.
- Pruebas: `frontend/pruebas/respuestas.test.js`, `frontend/pruebas/clienteChat.test.js`; `frontend/e2e/pantallas.spec.js` («el chat responde "Calculado con tus datos"…», «si el agente falla, el chat lo dice…», «el chat recuerda la meta…»)

### HU-11 · Confiar en que Lucas no hace lo que no debe

> Como **cliente**, quiero que Lucas no mueva mi plata ni me diga en qué invertir, para confiar en lo que me dice.

- Pantalla: Chat · Palanca: P5
- **Dado** «transfiere S/ 500 a mi primo», **entonces** responde que Lucas no mueve plata.
- **Dado** «compra dólares hoy» o «¿en qué acción invierto?», **entonces** no recomienda; solo ofrece decir cuánto margen tiene hasta su cobro.
- **Dado** cualquiera de esos pedidos, **entonces** no sale a la red, aunque el agente esté encendido.
- **Dado** «el carro está 14 000 dólares», **entonces** lo lee como el precio de una meta, no como un pedido de comprar dólares.
- Pruebas: `frontend/pruebas/respuestas.test.js` («no da asesoría de inversión ni ofrece mover plata», «el precio de una meta en dólares no se confunde con comprar dólares»), `frontend/pruebas/clienteChat.test.js` («pedir comprar dólares o mover plata no sale al servidor»)

### HU-17 · Corregir lo que Lucas cree de mí

> Como **cliente**, quiero decirle a Lucas si un dato o un aviso no es correcto o no me sirve, para que no siga con algo equivocado.

- Pantallas: Lo que aprendí de ti y Avisos · Palanca: P2
- **Dado** cada dato de «Lo que aprendí de ti», **entonces** ve de dónde lo sacó y puede responder «¿Es correcto?»: «Sí» lo confirma y «No» lo marca como por revisar, con «Deshacer».
- **Dado** «útil» o «no me sirve» en un aviso, **entonces** se marca y se recuerda al volver.
- Hoy la respuesta solo queda guardada en el navegador; no cambia los tips siguientes.
- Pruebas: `frontend/e2e/pantallas.spec.js` («Resumen: confirmar lo aprendido desde su bloque», «responder "No" marca el dato como por revisar y se puede deshacer», «Avisos: "útil / no me sirve" se marca y se recuerda al volver»)

### HU-18 · Borrar lo que Lucas sabe de mí

> Como **cliente**, quiero apagar Lucas y borrar lo que recuerda de mí, para tener control sobre mis datos.

- Pantalla: Más → Preferencias → Privacidad · Palanca: P2
- **Dado** «retirar el permiso», **entonces** Lucas se apaga para esa persona y se borran sus tips, sus gastos planificados y sus metas, sin tocar a la otra persona.
- **Dado** «borrar mis avisos guardados», **entonces** se borra el registro de avisos y las respuestas «útil / no me sirve».
- **Dado** que cambio de persona, **entonces** se descartan los tips, lo planificado y las metas de la anterior.
- **Dado** datos rotos guardados en el navegador, **entonces** la app no se cae y los descarta.
- Pruebas: `frontend/pruebas/sesion.test.js`; `frontend/e2e/pantallas.spec.js` («retirar el permiso desde Preferencias apaga Lucas y borra los tips elegidos»), `frontend/e2e/simulador-metas.spec.js` («retirar el permiso olvida lo planificado y las metas», «datos rotos guardados en el navegador no tumban la app»)

### HU-14 · Medir cuánto gana el cliente y cuánto gana el banco

> Como **banco que integra a Lucas**, quiero ver en S/ cuánto mejora cada cliente siguiendo a Lucas y qué significa para mi negocio, para decidir si lo licencio.

- Pantalla: `/evidencia` (Más → Preferencias → Para el jurado); no pide permiso de cliente · Palanca: todas
- **Dado** el panel, **entonces** empieza por el impacto en S/ por cliente de Lucas frente a «no hacer nada», con su intervalo de 95 %, y lo compara con las otras estrategias.
- **Dado** el impacto, **entonces** muestra los supuestos de la simulación y el valor para el banco en el escenario conservador.
- **Dado** cualquier cifra, **entonces** sale de `models/metricas*.json`, con su archivo de origen a la vista; si falta una clave, la build falla en vez de mostrar un número inventado.
- Las métricas se generan con los scripts de `analitica/eval/` sobre los datos sintéticos de `backend/src/generador/`.
- Pruebas: `frontend/pruebas/evidencia.test.js` («cada cifra del panel existe en models/metricas*.json y es un número», «el impacto en S/ es el de Lucas frente a no hacer nada, con su intervalo», «una clave que no existe rompe…»); `frontend/e2e/pantallas.spec.js` («Evidencia: empieza por el impacto en S/…»)

### HU-20 · Ver que la IA le gana a lo sencillo

> Como **banco que integra a Lucas**, quiero ver cada técnica frente a su baseline, para confiar en que la IA aporta.

- Pantalla: `/evidencia` · Palanca: todas
- **Dado** el panel, **entonces** cada técnica muestra su métrica frente a su baseline, con un veredicto calculado según qué dirección es mejor.
- **Dado** el agente y el RAG, **entonces** se muestran su corrida de QA caso por caso, los pedidos prohibidos rechazados (aparte, porque los corta el filtro previo) y el filtro de relevancia del RAG.
- **Dado** las perturbaciones y las alertas de equidad, **entonces** se muestra también lo que empeora.
- Pruebas: `frontend/pruebas/evidencia.test.js` («el veredicto se calcula según qué dirección es mejor», «las perturbaciones muestran también lo que empeora», «el agente con Gemini sale de la corrida de QA…»)
