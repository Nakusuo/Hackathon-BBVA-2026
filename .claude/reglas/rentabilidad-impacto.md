# Rentabilidad, impacto e innovación

Responde las tres preguntas que el jurado hará aunque no estén en la rúbrica: **¿por qué un banco pagaría por Lucas?**, **¿qué cambia para los peruanos?** y **¿qué tiene de nuevo?**
Cifras públicas: solo las marcadas como verificadas en [../estadisticas/cifras-publicas.md](../estadisticas/cifras-publicas.md). Evidencia de mercado: [../investigacion/negocio-impacto.md](../investigacion/negocio-impacto.md).

## Verificación del plan (14/11)

| Pregunta | Antes | Problema | Qué cambiamos |
|---|---|---|---|
| ¿Genera ingresos? | «Fideliza y atrae», sin mecanismo | El jurado no ve de dónde sale la plata | 6 palancas, cada una atada a una función y a una métrica (abajo) |
| ¿Genera impacto? | Métricas técnicas (MAE, F1) | Nadie entiende «MAE 312» | Cada cliente simulado termina con **días en rojo evitados**, **S/ apartados** e **intereses evitados** |
| ¿Es innovador? | Diferenciales sueltos | Puede parecer otra app de presupuesto | Cuatro diferenciales defendibles frente a lo que ya existe en Perú (abajo) |
| ¿Es barato? | Sí, pero no se decía | Parece caro por tener IA | El 90 % del valor sale de modelos en CPU; el LLM solo redacta. Costo del hackathon: S/ 0 |
| ¿Se puede construir en 2 días? | 15 módulos DEBE | Riesgo de no tener flujo de punta a punta | Orden «núcleo rentable primero» en [../planes/plan-maestro.md](../planes/plan-maestro.md), sección 2 |

## Cómo gana plata el banco

Lucas gana cuando el cliente **ahorra y llega a fin de mes**, no cuando se endeuda. Esa es la respuesta a «¿no es venta disfrazada?».

| # | Palanca | Función de Lucas | Por qué deja ingreso | Métrica en la demo (simulada) | Métrica de un piloto |
|---|---|---|---|---|---|
| P1 | **Captación de ahorro** | Metas, Sueldo Lucas, colchón | El saldo apartado es fondeo barato que el banco presta (margen financiero) | S/ apartados por cliente al mes | Saldo promedio en apartados |
| P2 | **Principalidad y retención** | Avisos anticipados, resumen de la quincena | Quien recibe su ingreso en el banco y entra cada quincena no se va y usa más productos | Avisos útiles por semana (máx. 3) | Retención a 90 días, % que deposita su ingreso |
| P3 | **Menos mora** | Aviso 3 a 7 días antes del rojo | Cuotas pagadas a tiempo bajan provisiones y costo de cobranza | Días en rojo evitados | Atrasos de más de 8 días frente a un grupo de control |
| P4 | **Atracción con bajo costo** | Lucas en 5 preguntas | Da valor antes de abrir cuenta: embudo de captación sin oficina ni vendedor | Tiempo hasta el primer pronóstico | Conversión de «5 preguntas» a cuenta |
| P5 | **Venta cruzada idónea** | Ofertas genéricas por necesidad e idoneidad | Producto correcto a quien lo necesita: más aceptación, menos reclamos | Precision@3, 0 violaciones de idoneidad | Aceptación y reclamos por oferta |
| P6 | **Menos costo de atención** | Chat con cifras verificadas | «¿Me alcanza?» se responde sin call center | — | Contactos evitados |

**Lo que no decimos:** ningún porcentaje de retención, churn o mora «de Lucas». Con datos sintéticos no se puede probar. Decimos qué mediría un piloto y con qué grupo de control.

### Calculadora de valor (supuestos a la vista)

Se muestra en el pitch como fórmula, con un escenario conservador y cada supuesto etiquetado («fuente» o «supuesto del equipo»):

```
Valor anual ≈ clientes que usan Lucas
            × ( S/ apartados por cliente × 12 × margen del fondeo
              + clientes retenidos de más × margen anual por cliente
              + mora evitada × pérdida por mora )
```

- **S/ apartados por cliente** sale de `make eval` (simulado), no de una suposición.
- Los márgenes y tasas son supuestos visibles que el banco reemplaza con sus números.
- Lo calcula `eval/valor_banco.py` y lo deja en `EVALUATION.md` (tarea MG-13).

### Modelo de ingreso de Lucas

| Opción | Cómo cobra | Encaje |
|---|---|---|
| **B2B2C (elegido)** | Licencia por cliente activo a bancos, cajas municipales y cooperativas, con su catálogo y su marca | Gratis para el usuario final; el banco paga porque gana por P1 a P6 |
| Freemium al usuario | Funciones premium pagadas | Choca con el público objetivo (ingreso justo) |
| Comisión por producto vendido | Pago por cada crédito o tarjeta colocada | Incentivo a vender: contradice las reglas de seguridad. **Descartado** |

## Impacto en los peruanos

Público: trabajadores del sector privado, con foco en **independientes y mixtos**, cuyo ingreso varía y casi ningún banco les arma un plan. Cifras de dolor en [../estadisticas/cifras-publicas.md](../estadisticas/cifras-publicas.md).

Métricas de impacto que produce `make eval` sobre la población sintética (Lucas frente a «no hacer nada» y frente a «apartar 10 % fijo»):

| Métrica | Qué significa para la persona |
|---|---|
| Días en rojo evitados al mes | No quedarse sin plata antes de cobrar |
| S/ de colchón a 3 meses | Aguantar un imprevisto sin pedir prestado |
| Intereses evitados en S/ (TCEA supuesta y visible) | Lo que no paga por cubrir el hueco con deuda cara |
| % que sube de cuadrante en la matriz ahorro × gasto | Pasar de «gastador» o «ingreso justo» a ahorrador |

Inclusión: Lucas en 5 preguntas sirve a quien **todavía no tiene cuenta**, sin pedir datos personales.

## Qué es nuevo

Comparación con lo que hay en Perú: [../investigacion/negocio-impacto.md](../investigacion/negocio-impacto.md), sección «Competencia».

| Diferencial | Qué hace la competencia habitual | Qué hace Lucas |
|---|---|---|
| Pronóstico con banda según tipo de ingreso | Muestra el saldo de hoy o el gasto pasado | Dice cuánto tendrás en 30 días, con rango más ancho si tu ingreso es irregular |
| Sueldo Lucas | Presupuesto pensado para sueldo fijo | Convierte pagos irregulares en un monto quincenal estable |
| LLM que no puede inventar cifras | Chatbot que redacta libre | Cada número sale de una tool y pasa por el juez; si falla, plantilla |
| Valor antes de ser cliente | Hay que abrir cuenta para ver algo | 5 preguntas y ya tienes tu pronóstico |

Además, calendario peruano (quincena, grati, CTS, campañas) dentro del modelo, no como decoración.

## Costo

| Concepto | Hackathon | Si se escala |
|---|---|---|
| Modelos (pronóstico, salud, segmentos, recomendador) | CPU de la laptop | CPU estándar; centavos por cliente al mes |
| LLM | Ollama local o Gemini en nivel gratuito: S/ 0 | Solo redacta; las preguntas frecuentes van por plantilla. `gemini-3.5-flash-lite` de pago cuesta USD 0,30 / 2,50 por millón de tokens de entrada / salida: del orden de USD 0,05 por usuario al mes (estimación del equipo, sin tokens de razonamiento). Un banco también puede usar un modelo propio. Detalle en [../investigacion/gemini-api.md](../investigacion/gemini-api.md) |
| Base de datos | PostgreSQL en Docker | Postgres gestionado del banco |
| Licencias | Todo código abierto | Igual |

Regla de costo: **si una plantilla responde bien, no se llama al LLM**. Se mide el % de respuestas que salen por plantilla.

## Ideas baratas que suben impacto (reutilizan el motor)

| Idea | Qué hace | Reutiliza | Prioridad |
|---|---|---|---|
| **¿Cuánto te cuesta tapar el hueco?** | Si viene un día en rojo, compara el costo en S/ de cada salida (usar el colchón, mover un gasto, tarjeta, préstamo informal) con TCEA supuesta y visible. Educa, no ofrece crédito | Simulador + RAG de deudas | PODRÍA |
| **Métricas de impacto en S/** | Las 4 métricas de arriba en `EVALUATION.md` y en el panel Evidencia | Simulador + `make eval` | DEBE |
| **Calculadora de valor** | Fórmula del banco con supuestos visibles | Salida de `make eval` | DEBE (solo pitch) |
