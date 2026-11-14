# Reglas de negocio de Lucas

## Usuario y problema

- **Población:** trabajadores dependientes e independientes del sector privado en Perú. Cobran por quincena, con comisiones o con pagos irregulares; usan Yape/Plin y tarjeta; tienen cuotas o deudas.
- **Problema:** no saben si les alcanzará la plata hasta el próximo ingreso ni qué cambio concreto mejora su situación.
- **Decisión:** cuánto gastar o apartar este mes, cuándo reaccionar y qué cambio conviene más.

## Arquetipos (un motor, varias personas)

| Persona | Ingreso | Banda esperada |
|---|---|---|
| Formal con quincena | Estable + gratificación + CTS | Estrecha |
| Base + comisiones | Fijo + variable | Media |
| Independiente (recibo por honorarios) | Pagos irregulares de varios clientes | Ancha |
| Mixto (empleo + extra) | Fijo + extra irregular | Media-ancha |

El arquetipo es **solo para evaluar**. Nunca entra como variable a un modelo.

## Calendario peruano

- Quincena (15 y fin de mes) para formales.
- Gratificación: julio y diciembre. CTS: mayo y noviembre. *(Confirmar en fuente oficial antes de citar.)*
- Feriados con la librería `holidays` (país PE).

## Reglas de seguridad del recomendador (globales, se aplican al final)

1. Nunca sugerir crédito, tarjeta o préstamo a un perfil con colchón < 1 mes o deuda alta.
2. Nunca decir «compra o vende dólares». El tipo de cambio solo se muestra ligado a pagos propios en USD («tienes un pago de US$ 300 en 45 días»).
3. Nunca prometer rentabilidades ni ejecutar operaciones. No existe ninguna tool que mueva dinero.
4. Cada recomendación muestra: **acción · impacto estimado en S/ · por qué (datos usados) · supuestos · confianza (alta/media/baja) · «tú decides»**.
5. Se registra qué datos usó cada recomendación (trazabilidad).
6. Lenguaje de «simulación» y «orientación», nunca de asesoría.
7. Si Lucas menciona un producto, es un **tipo genérico** («cuenta con apartados»), nunca un producto real ni con marca, y solo si ayuda a la meta del usuario y pasa las reglas 1 a 3.
8. Los avisos son pocos y útiles (máximo 3 por semana). Nada de notificaciones de relleno.
9. Inversión solo como educación (tipos, riesgo, plazo) y simulación con tasa supuesta visible. Nunca «invierte en X» ni rentabilidad prometida.
10. Productos de ahorro a plazo o inversión solo con colchón ≥ 3 meses y sin deuda cara.
11. El catálogo de ofertas y promociones es **ficticio o genérico** (`data/catalogo_ofertas.json`). Nunca productos, nombres ni promociones reales de BBVA ni de otro banco. En el pitch: «se conecta al catálogo del banco que integre a Lucas».
12. La memoria del usuario es solo suya (RLS), se puede ver y borrar, y nunca justifica ofrecer crédito a quien no pasa la regla 1.

## Perfil de ahorro y gasto

| | Gasta poco | Gasta mucho |
|---|---|---|
| **Ahorra** | Ahorrador firme → promociones, ahorro e inversión (con idoneidad) | Ahorra pero se le escapa → hormiga y suscripciones |
| **No ahorra** | Ingreso justo → colchón mínimo, Sueldo Lucas | Gastador → metas de ahorro, límites, avisos de riesgo |

Meta del producto: que el usuario suba de cuadrante.

Visión de compañero, fidelización y atracción: [vision-companero.md](vision-companero.md).

## Recomendador (orden del pipeline)

reglas candidatas → puntaje impacto (S/) × facilidad → ajuste por perfil → filtros de seguridad → top 3.

## Chat y verificador de cifras

1. Un solo agente con tools de solo lectura: `get_health`, `get_forecast`, `get_recos`, `simulate`, `get_fx`.
2. El LLM recibe solo las salidas de las tools.
3. Se extraen todos los números de su respuesta; cada uno debe coincidir (con tolerancia de redondeo) con un valor de una tool.
4. Si falla: un reintento; si vuelve a fallar → `TemplateProvider`.
5. La UI marca con ✓ las cifras verificadas.
6. System prompt fijo; defensa contra prompt injection; casos adversos en tests.

Proveedores LLM, en este orden: `OllamaProvider` (por defecto, offline) · `GeminiProvider` (`gemini-3.5-flash-lite` en nivel gratuito, apagado por defecto, se activa con `LLM_PROVIDER=gemini`, clave en `.env`, solo salidas de tools, nunca datos personales) · `TemplateProvider` (siempre disponible). Ante error 429, timeout o sin red: un reintento y luego plantilla. Los embeddings del RAG son siempre locales. Detalle: [../investigacion/gemini-api.md](../investigacion/gemini-api.md).

Regla de costo: si una plantilla responde bien la pregunta, no se llama al LLM.

## Datos y privacidad

- Todo sintético, semilla fija (`--seed`). Comercios ficticios («StreamFlix», «RapiFood»).
- Nunca: nombres, DNI, teléfonos, cuentas reales, marcas reales.
- Pantalla de consentimiento: qué se usa, que son datos sintéticos y que se puede revocar.
- Validación Pydantic de toda entrada (montos ≥ 0, fechas válidas, categorías válidas).

## Marca y UI

- Marca propia «Lucas», paleta propia. Sin logos ni colores de BBVA.
- Contraste AA, texto ≥ 16 px, no depender solo del color.
- Incertidumbre en palabras: «entre S/ 120 y S/ 380».
- Botón «explícamelo fácil».
- Pantallas: Cómo estás · Qué viene · Qué hacer · Chat · Evidencia.

## Fuera de alcance

Ubicación, WhatsApp, app nativa, modo familia, vista para el banco, junta/pandero, plan de deudas con OR-Tools, predicción del tipo de cambio.
