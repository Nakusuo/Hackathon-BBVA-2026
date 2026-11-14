# Visión: Lucas como compañero bancario

Feedback del juez (14/11/2026): la IA no es el problema; tiene que ser **el compañero bancario** del cliente. Debe atacar necesidades reales de los **clientes actuales (fidelización)** y de los **futuros clientes (atracción)**. No basta una demo cosmética ni un chatbot genérico. Tiene que innovar y ser atractivo para el público y para el jurado.

Esto **no cambia** el problema principal (liquidez a 30 días). Cambia **cómo se presenta y qué se prioriza**.

## Compañero frente a chatbot genérico

Ejercicio inverso: cómo hacer un chatbot financiero genérico, y lo contrario de cada cosa.

| Chatbot genérico | Lucas compañero |
|---|---|
| Espera a que le preguntes | **Se adelanta**: avisa días antes del problema |
| Consejos de manual («ahorra más») | Acción concreta con monto en S/ calculado sobre tus datos |
| Inventa cifras | Toda cifra sale de código y lleva ✓ |
| No sabe cuándo cobras | Conoce tu quincena, tus clientes, tu grati y tu CTS |
| Igual para todos | Distinto para formal, comisionista, independiente y mixto |
| Te vende productos | Solo menciona un producto si te ayuda y pasa las reglas de seguridad |
| Una pantalla de chat | El chat es una puerta más; el valor está en avisos, plan y simulador |

## Trabajos que Lucas resuelve (JTBD)

- **Funcional:** «Cuando me entra un pago irregular, quiero saber cuánto puedo usar y cuánto apartar, para no llegar en rojo al siguiente.»
- **Emocional:** dormir tranquilo sabiendo que llego a la quincena.
- **Social:** no tener que pedirle prestado a la familia ni a un prestamista.

## Ideas priorizadas

Cada idea reutiliza el motor (pronóstico, simulador, recomendador) y tiene métrica frente a una alternativa sencilla. Ninguna es cosmética.

### Fidelización (clientes actuales)

| # | Idea | Qué hace | Baseline | Métrica | Prioridad |
|---|---|---|---|---|---|
| F1 | **Avisos anticipados** | Lucas avisa 3 a 7 días antes de un posible saldo en rojo, solo si la probabilidad supera un umbral | Alerta cuando el saldo baja de un monto fijo | Precision, recall y días de anticipación | DEBE |
| F2 | **Sueldo Lucas** | Para independientes y mixtos: convierte ingresos irregulares en un monto quincenal estable sugerido; lo que sobra va al colchón | Apartar 10 % fijo / no hacer nada | Días en rojo simulados y colchón a 3 meses | DEBE |
| F3 | **Plan de grati y CTS** | Cuando llega la grati o la CTS, propone un reparto (colchón, deuda cara, meta) con impacto en el puntaje | Gastarla igual que un mes normal | Cambio del puntaje de salud y deuda simulada | PODRÍA |
| F4 | **Resumen de la quincena** | «Subiste de 52 a 58 porque cancelaste una suscripción». Progreso real, sin medallas vacías | — | Componentes del puntaje que cambiaron | DEBERÍA |

### Atracción (futuros clientes)

| # | Idea | Qué hace | Baseline | Métrica | Prioridad |
|---|---|---|---|---|---|
| A1 | **Lucas en 5 preguntas** | Alguien sin historial responde 5 datos (tipo de ingreso, frecuencia, gastos fijos, deudas, colchón) y recibe su pronóstico usando lo aprendido de perfiles parecidos | Promedio de toda la población | MAE con 0, 1 y 3 meses de historia | DEBE versión mínima (ola 1); comparación de MAE DEBERÍA |
| A2 | **Plata del negocio y plata de la casa** | Separa gastos del negocio y del hogar para independientes, un segmento poco atendido | Diccionario de comercios | F1 por categoría | DEBERÍA |

### Impacto (para todos)

| # | Idea | Qué hace | Baseline | Métrica | Prioridad |
|---|---|---|---|---|---|
| I1 | **Impacto en S/** | Cada cliente simulado termina con días en rojo evitados, colchón e intereses evitados | No hacer nada / 10 % fijo | S/ y días por cliente | DEBE |
| I2 | **¿Cuánto te cuesta tapar el hueco?** | Ante un día en rojo, compara en S/ usar el colchón, mover un gasto, tarjeta o préstamo informal (TCEA supuesta y visible). Educa, no ofrece crédito | Sin comparación | Intereses evitados simulados | PODRÍA |

A1 es el gancho de atracción: el valor llega **antes** de abrir una cuenta. También es un reto técnico real (arranque en frío).

## Valor para el banco (para el pitch, sin pantalla propia)

Palancas de ingreso, calculadora, modelo B2B2C, costo e impacto: [rentabilidad-impacto.md](rentabilidad-impacto.md).

- **Gana cuando el cliente ahorra:** metas y Sueldo Lucas traen fondeo barato al banco.
- **Fidelización:** el cliente vuelve porque Lucas le avisa a tiempo y le ahorra plata medible.
- **Atracción:** A1 da valor a quien todavía no es cliente.
- **Oferta responsable:** si Lucas detecta una necesidad (por ejemplo, una meta de ahorro), puede mostrar un **tipo de producto genérico** («cuenta con apartados»), nunca un producto real con marca, y solo si pasa las reglas de seguridad de [negocio.md](negocio.md).
- **Honestidad:** no inventamos cifras de retención ni de churn. Mostramos indicadores simulados (días en rojo evitados, colchón ganado) y decimos que el impacto en el negocio se valida en un piloto.

## Supuesto más arriesgado

Que la persona **actúe** según el aviso. Con datos sintéticos no se puede probar. Lo simulamos (qué pasa si sigue la recomendación) y en el pitch lo planteamos como lo primero que mediría un piloto.

## Cómo se ve en la demo (atractivo para el público)

1. Arranca un independiente: llega un **aviso** «el jueves podrías quedar en rojo», 3 a 7 días antes.
2. Lucas propone su **Sueldo Lucas**: «usa S/ 1 200 por quincena; aparta S/ 380 de este pago».
3. El simulador mueve la banda y el día de riesgo desaparece.
4. Cambio de público: alguien **sin historial** responde 5 preguntas y ve su pronóstico.
5. Evidencia: cada idea frente a su baseline.

## Lo que no hacemos

- Gamificación vacía (medallas, rachas sin efecto en la plata).
- Recomendar productos reales o con marca.
- Un chat que contesta de todo. El chat solo responde sobre la plata del usuario y con tools.
