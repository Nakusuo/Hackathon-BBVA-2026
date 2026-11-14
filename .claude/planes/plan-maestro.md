# PLAN MAESTRO — «Lucas», copiloto de plata

**Hackathon BBVA · AI Financial Life · 14–15 de noviembre de 2026**

> **Principio rector (bases):** la mejor solución no es la más compleja, sino la que convierte datos e IA en una decisión financiera más clara, segura y demostrablemente útil.

---

## 0. Cambios respecto al brief del 13/11 (por las bases finales)

Las bases finales cambian varias cosas del brief. Hay que tenerlas presentes:

| Brief del 13/11 | Bases finales | Qué hacemos |
|---|---|---|
| Pesos: valor ingeniería 25, técnica 25, IA 25, escalabilidad 15, demo 10 | **Valor 15 · IA y analítica 25 · Calidad técnica 25 · Producto y UX 15 · Innovación 10 · Demo 10** | La escalabilidad ya no tiene peso propio. Suben Producto/UX y Valor. Rigor + baseline + tests es el 50 %. |
| Lucas como app amplia (perfil, pronóstico, chat, alertas, ubicación…) | «Elijan **un problema principal** y **una población usuaria** definida» | Un problema central y los módulos le sirven a ese problema. |
| Chat con LangGraph: analista + pronóstico + estratega | **No hay puntos extra por usar más agentes, modelos o servicios**; cada técnica se compara con una alternativa sencilla | Un solo agente con herramientas. Se pueden sumar más solo si se mide que aportan. |
| «OpenAI si hay clave» | BBVA **no da** API keys, créditos cloud ni GPU. Un LLM externo solo se usa si las reglas lo permiten y **sin datos personales** | Capa de LLM intercambiable: **Ollama local** como base, API propia opcional y **fallback a plantillas** siempre. |
| Lucas «encaja como agente propio del banco (como Blue)» | **Prohibido** usar marcas o interfaces bancarias como si fuera un producto oficial | Marca propia «Lucas», sin logos ni colores de BBVA. En el pitch se habla de «podría integrarse», nunca de «es de BBVA». |
| Escalabilidad como criterio | Prueba de evolución sorpresa (ingresos variables, duplicados, explicabilidad) | Diseño modular y escenarios difíciles en el generador **desde el día 1**. |
| Ubicación, WhatsApp, modo familia | Datos no confidenciales y privacidad penalizada si hay riesgo | **Fuera del alcance.** |

---

## 1. Problema, usuario y decisión

**Población:** trabajadores **dependientes e independientes del sector privado** en Perú que necesitan manejar mejor sus finanzas: cobran por quincena, con comisiones o con pagos irregulares de clientes; usan Yape/Plin y tarjeta, y tienen cuotas o deudas.

**Problema principal: liquidez a 30 días.** No saben con anticipación si les alcanzará la plata ni qué cambio concreto mejora su situación. Ven su saldo de hoy, pero no el de la próxima quincena o el próximo pago. El problema es más agudo en los independientes, porque su ingreso varía.
*(Contexto: según el equipo, el 61 % de los peruanos no cubriría un mes de ingresos ante una emergencia; la cifra se leyó en la fuente. Citar la fuente exacta en el README. La guía nombra el ámbito dos veces: «predicción de liquidez» e «ingresos variables» en la prueba sorpresa.)*

**Arquetipos (un solo motor, varias personas):**
| Persona | Ingreso | Qué muestra en la demo |
|---|---|---|
| Empleado formal con quincena | Estable + gratificación + CTS | Banda estrecha; foco en ahorro y suscripciones |
| Empleado con base + comisiones | Fijo + variable | Banda media; meses buenos y malos |
| Independiente con recibo por honorarios | Pagos irregulares de varios clientes | Banda ancha; «día de riesgo» y colchón |
| Mixto (empleo + trabajo extra) | Fijo + extra irregular | Separar la plata del extra; qué apartar |

La demo empieza con una persona y cambia a otra: mismo motor, distinta incertidumbre.

**Decisión a mejorar:**
> «¿Cuánto puedo gastar o ahorrar este mes sin quedarme en rojo antes de mi próximo ingreso, y qué cambio me conviene más?»

**Criterios de éxito (medibles):**
1. El pronóstico de saldo a 30 días tiene **menor MAE** que el baseline (promedio móvil) en el set de test, y sus bandas al 80 % cubren entre el 75 % y el 85 % de los casos reales.
2. El 100 % de las cifras que dice el chat se pueden rastrear hasta una herramienta (verificador).
3. Un usuario de prueba llega al «día de riesgo» y a una recomendación accionable en **menos de 60 segundos** (tiempo hasta insight).
4. Se detectan las recurrentes y suscripciones duplicadas con F1 ≥ 0,85 sobre etiquetas sintéticas.

5. La banda del pronóstico es más ancha para los independientes que para los dependientes y aun así mantiene su cobertura. Así se demuestra que el modelo refleja la incertidumbre real y no un promedio.

### Cómo se integran los ámbitos de la guía (aporte del equipo)
Un problema principal y las demás piezas como apoyo, no como problemas aparte:

| Ámbito | Rol en Lucas | Decisión que mejora | Métrica frente a una alternativa sencilla | Escenario difícil |
|---|---|---|---|---|
| **Predicción de liquidez** | **Problema principal** | Cuánto gastar o apartar y cuándo reaccionar | MAE, MAPE y cobertura de la banda frente a promedio móvil o estacional | Ingresos irregulares, datos incompletos |
| Clasificación de gastos | Alimenta los datos | Separar «plata del negocio» y «plata de la casa» (independientes y mixtos) | F1 por categoría frente a un diccionario de comercios | Categorías ambiguas, datos incompletos |
| Recurrentes y suscripciones | Aporta lo comprometido al pronóstico | Qué cancelar o consolidar | Precision, recall y F1 frente a la regla «mismo comercio y monto cada 30 días» | Suscripciones duplicadas, cambios de precio |
| Planificación de ahorro | Salida dentro de «Qué hacer» | Cuánto apartar cada quincena sin quedarse corto | Probabilidad de cumplir la meta frente a una regla fija del 10 % | Cambios de patrón de gasto |
| Simulación de escenarios | Salida «¿qué pasa si?» | «¿Qué pasa si pierdo un cliente o sube mi cuota?» | Exactitud frente a un cálculo exacto en hoja de cálculo | Ingresos variables |
| Recomendaciones explicables | Capa final transversal | Qué hacer con fundamento, límites y confianza | Groundedness: todas las cifras salen de código | — |
| Alertas de anomalías | Solo si sobra tiempo | Revisar un movimiento inusual (solo avisa, no opera) | Precision, recall y falsos positivos frente a un umbral fijo | Transacciones atípicas |
| Educación financiera | Botón «explícamelo fácil» y costo real de las cuotas | Entender una deuda o una compra a cuotas | Fidelidad de las respuestas y casos adversos | — |

**Si el equipo quiere validar la elección:** cada persona puntúa de 1 a 5 cada opción en cuatro preguntas (¿dolor real y delimitado?, ¿medible con un baseline en dos días?, ¿se ve en la demo?, ¿lo podemos construir con lo que dominamos?) y gana la suma más alta. Alternativas: recurrentes + anomalías (más fácil de medir, menos distintiva) o educación financiera (muy inclusiva, más difícil de medir).

**Fuera del producto:** prometer rentabilidades, ejecutar operaciones, predecir el tipo de cambio o decir «compra dólares». Las recomendaciones son orientación educativa y simulación con supuestos claros. **La decisión siempre es de la persona.**

---

## 2. Alcance del MVP (MoSCoW)

### DEBE (núcleo de la demo)
| # | Módulo | Pantalla |
|---|---|---|
| D1 | **Generador de datos sintéticos** con calendario peruano y escenarios difíciles | (dataset) |
| D2 | **Motor**: categorías, gasto fijo y variable, gasto hormiga, recurrentes | Cómo estás |
| D3 | **Salud financiera** con un puntaje transparente (0–100, con sus componentes visibles) | Cómo estás |
| D4 | **Pronóstico de saldo a 30 días** con banda de incertidumbre y «día de riesgo» | Qué viene |
| D5 | **Recomendador híbrido**: 3 acciones con impacto en S/, el «¿por qué?», límites y confianza | Qué hacer |
| D6 | **Simulador «qué pasaría si»**, que reutiliza el pronóstico | Qué hacer |
| D7 | **Chat con herramientas + verificador de cifras** (el modelo explica, no calcula), con fallback | Chat |
| D8 | **Panel «cómo sabemos que funciona»**: baseline contra modelo, cobertura y % de cifras verificadas | Evidencia |

### DEBERÍA
- Perfiles por cluster (K-Prototypes) que ajustan la prioridad y el tono de las recomendaciones.
- Detector de suscripciones duplicadas (ya prepara la prueba de evolución).
- Formulario «agrega un gasto o una meta» que recalcula todo en vivo.
- Tipo de cambio del BCRP con caché y un valor grabado de respaldo. Solo genera alertas con contexto («tienes un pago de US$ 300 en 45 días»).
- Pantalla de consentimiento y botón «explícamelo fácil».

### PODRÍA (solo si sobra tiempo)
- Explicación contrafactual: «para subir de 55 a 70 tendrías que…».
- Alerta de movimiento atípico (Isolation Forest).
- Prueba de equipo rojo en vivo (el chat bloquea una prompt injection).

### NO AHORA
Ubicación, WhatsApp real, app nativa, modo familia, vista para el banco, junta/pandero, plan de deudas con OR-Tools.

---

## 3. Arquitectura

Las bases piden separar **ingesta/preparación**, **lógica analítica/IA** e **interacción**.

```
┌──────────────────────── 1. INGESTA / PREPARACIÓN ────────────────────────┐
│ generator/ (semilla fija) → CSV/Parquet → validación Pydantic → DuckDB   │
│ fx_service (BCRP → caché → último valor → serie grabada)                 │
└───────────────────────────────────┬──────────────────────────────────────┘
┌──────────────────────── 2. LÓGICA ANALÍTICA / IA ────────────────────────┐
│ engine:   categorías · recurrentes · métricas · calendario PE            │
│ health:   puntaje transparente por componentes                           │
│ forecast: baseline (promedio móvil) vs modelo + banda (bootstrap)        │
│ profile:  K-Prototypes (k fijado por silueta/estabilidad)                │
│ recommender: reglas → puntaje impacto×facilidad → ajuste por perfil      │
│              → reglas de seguridad globales                              │
│ assistant: 1 agente LLM + tools (las cifras SOLO salen de tools)         │
│ verifier: cada número de la respuesta debe estar en la salida de tools   │
│           → si no, se reescribe o se usa la plantilla (fallback)         │
└───────────────────────────────────┬──────────────────────────────────────┘
┌──────────────────────── 3. INTERACCIÓN ──────────────────────────────────┐
│ FastAPI (REST) ← UI: Cómo estás · Qué viene · Qué hacer · Chat · Evidencia│
└──────────────────────────────────────────────────────────────────────────┘
```

**Stack:** Python 3.11 · pandas/DuckDB · scikit-learn · `kmodes` · statsmodels · SciPy · `holidays` · FastAPI + Pydantic · pytest.
**UI:** Streamlit si el equipo es pequeño o falta tiempo; React + Recharts si alguien lo domina. Se decide en la primera hora y no se cambia después.
**LLM:** interfaz `LLMProvider` con tres implementaciones: `OllamaProvider` (por defecto, offline), `APIProvider` (opcional, con clave propia en `.env`) y `TemplateProvider` (fallback sin LLM). La demo tiene que funcionar **con la red apagada**.

---

## 4. Datos sintéticos

### Decisión: generador propio + BD local, calibrado con cifras públicas
- **No usamos un dataset público de transacciones como base.** No hay uno peruano a nivel de transacción (INEI, SBS y BCRP publican encuestas y agregados). Los de Kaggle no tienen quincena, gratificación, CTS ni nuestros escenarios difíciles, y habría que revisar la licencia de cada uno.
- **El generador propio cubre lo que piden las bases:** semilla, escenarios difíciles, controles de calidad y particiones sin fuga. Además permite responder a la prueba sorpresa en minutos.
- **Almacenamiento:** el generador escribe Parquet y lo carga en **DuckDB** (`data/lucas.duckdb`). Los gastos y metas que el usuario agrega en vivo van a una tabla aparte en la misma BD. Postgres no hace falta.
- **Calibración:** 3 o 4 cifras públicas verificadas en su fuente original (por ejemplo, el 61 % sin colchón de un mes, el ingreso promedio por tipo de trabajo, la proporción de formales e independientes), documentadas en `QUALITY.md`.
- **Opcional:** un dataset público con licencia citada, solo como prueba externa del detector de recurrentes o de anomalías. Nunca como base.

### Esquema (contrato recomendado por las bases + calendario)
| Campo | Tipo | Nota |
|---|---|---|
| `customer_id` | str | ficticio (`C0001`) |
| `transaction_id` | str | único |
| `fecha_hora` | datetime | 12 meses |
| `monto` | float | positivo; el signo lo da `tipo` |
| `moneda` | PEN / USD | |
| `tipo` | ingreso / gasto / transferencia | |
| `categoria` | str | alimentación, transporte, delivery, suscripción, cuota, servicios… |
| `comercio` | str | **ficticio** (p. ej., «StreamFlix», «RapiFood») |
| `canal` | yape / plin / tarjeta / efectivo | |
| `saldo` | float | opcional |
| `es_recurrente` | bool | **etiqueta** para evaluar |
| `es_atipico` | bool | **etiqueta** para evaluar |

Tabla `clientes`: `customer_id`, rango de edad, tipo de trabajo (formal/independiente), frecuencia de ingreso, personas a cargo, deuda total, colchón en meses, arquetipo (**solo para evaluar; nunca entra al modelo**).

**Nunca:** nombres, DNI, teléfonos, cuentas reales ni marcas reales.

### Generador (simulación por reglas y arquetipos)
- Los 4 arquetipos de la sección 1 (formal quincenal, base + comisiones, independiente con recibo por honorarios, mixto). A cada uno se le agregan variaciones de deuda, dependientes y nivel de ahorro.
- Calendario peruano: quincena, gratificación (julio y diciembre), CTS (mayo y noviembre) y feriados con `holidays` (PE). *(Confirmar el calendario de CTS y gratificación en una fuente oficial antes de citarlo.)*
- **Escenarios difíciles obligatorios:** ingresos irregulares, suscripciones duplicadas, cambio de patrón a mitad de año, datos incompletos (faltantes y duplicados inyectados) y transacciones atípicas.
- Volumen sugerido: alrededor de 500 clientes × 12 meses. Justificarlo con la estabilidad de las métricas y sus intervalos.
- **Semilla fija** y un parámetro `--seed`. Cualquiera regenera exactamente el mismo dataset.

### Controles de calidad (`data/QUALITY.md`, generado por script)
Volumen, cobertura temporal, distribución de montos, % de faltantes, duplicados, casos extremos, proporción por arquetipo y contraste con una o dos cifras públicas verificadas.

### Particiones sin fuga de datos
- **Pronóstico:** walk-forward temporal (entrenar meses 1–9, validar 10, test 11–12).
- **Recurrentes/atípicos:** dividir **por cliente** (GroupKFold), no por transacción.
- **Clusters:** sin etiquetas. El arquetipo se usa solo después, para medir la pureza (ARI).

**Honestidad:** con datos sintéticos, un pronóstico, un cluster o un detector puede «descubrir» justo lo que sembramos en el generador. Por eso se hacen **pruebas con perturbaciones**: más ruido, otra semilla, cambio de patrón no sembrado durante el entrenamiento y faltantes extra, y se reporta cuánto empeoran las métricas. Lo decimos en el README y en el pitch.

---

## 5. Inteligencia: cada técnica con su baseline

| Módulo | Técnica | Baseline sencillo | Métrica |
|---|---|---|---|
| Recurrentes | Agrupar por comercio + periodicidad (desviación de intervalos) + tolerancia de monto | «Mismo comercio ≥ 3 veces» | Precision, recall, F1 |
| Duplicadas | Recurrentes de la misma categoría y cliente que se solapan | — | Precision |
| Pronóstico | Saldo = ingresos esperados por calendario − fijos conocidos + variable (regresión/ETS); banda por **bootstrap por bloques de residuos** | Promedio móvil de 3 meses | MAE, MAPE, cobertura de la banda |
| Salud financiera | Puntaje ponderado: colchón, ratio de deuda, gasto fijo/ingreso, volatilidad del ingreso, ahorro | — (es transparente por diseño) | Coherencia: monotonicidad en tests |
| Perfiles | K-Prototypes (columnas mixtas), k por codo, silueta y estabilidad entre semillas | Reglas por umbral (ingreso irregular + colchón bajo) | Silueta, estabilidad, ARI contra arquetipo |
| Recomendador | Reglas candidatas → puntaje impacto (S/) × facilidad → ajuste por perfil → filtros de seguridad | Top 3 reglas fijas iguales para todos | Ahorro simulado en S/, % que evita el día en rojo, revisión por segmento |
| Chat | 1 agente con tools (`get_health`, `get_forecast`, `get_recos`, `simulate`, `get_fx`) | Respuestas con plantillas | Groundedness (% de cifras verificadas), exactitud en 20–30 preguntas fijas, tasa de bloqueo en casos adversos |
| Atípicos (Podría) | Isolation Forest por cliente | z-score robusto con umbral | Precision, tasa de falsos positivos |

### Reglas de seguridad del recomendador (globales)
- Nunca sugerir un crédito, una tarjeta o un préstamo a un perfil con colchón < 1 mes o deuda alta.
- Nunca decir «compra o vende dólares». Solo dar contexto del tipo de cambio ligado a pagos propios en USD.
- Cada recomendación muestra: **acción · impacto estimado en S/ · por qué (datos usados) · supuestos · confianza (alta/media/baja) · «tú decides»**.
- Se registra qué datos usó cada recomendación (trazabilidad).

### Verificador de cifras (diferencial)
1. El LLM recibe solo las salidas de las tools.
2. Se extraen todos los números de su respuesta.
3. Cada número debe coincidir (con tolerancia de redondeo) con un valor de una tool.
4. Si falla: se reintenta una vez y, si vuelve a fallar, se usa `TemplateProvider`.
5. La UI marca las cifras verificadas con ✓.

---

## 6. Experiencia de usuario (flujo de la demo)

1. **Consentimiento** (datos sintéticos, qué se usa y que se puede revocar). Se elige una persona: primero el independiente con recibo por honorarios y al final se cambia al empleado con quincena para contrastar las bandas.
2. **Cómo estás:** salud 58/100 con sus componentes; gastos por categoría; gasto hormiga S/ X; «tienes 2 suscripciones de streaming».
3. **Qué viene:** gráfico de saldo con banda → «riesgo de quedar en rojo el 27, unos días antes de la quincena (confianza media)».
4. **Qué hacer:** 3 tarjetas de recomendación → botón «¿por qué?» → simulador: «cancelo una suscripción y bajo el delivery 20 %» → la banda se mueve y el día de riesgo desaparece.
5. **Chat:** «¿llego a fin de mes si gasto S/ 150 en un regalo?» → respuesta con cifras ✓.
6. **En vivo:** se agrega un gasto en el formulario → todo se recalcula.
7. **Evidencia:** panel con baseline contra modelo y % verificado.

**Accesibilidad:** contraste AA, texto mínimo de 16 px, no depender solo del color, botón «explícamelo fácil» e incertidumbre explicada con palabras («entre S/ 120 y S/ 380»).

---

## 7. Seguridad y controles mínimos

- Secretos en `.env` (nunca en el repo) y `.env.example` con valores ficticios. Revisar con `git grep` antes de entregar.
- Validación Pydantic de todas las entradas (montos ≥ 0, fechas, categorías válidas).
- Manejo de errores: el timeout del LLM y del FX lleva a fallback, y la UI nunca se rompe.
- Medir la latencia por endpoint (objetivo: < 2 s sin LLM y < 8 s con LLM local).
- Defensa contra prompt injection: el system prompt fijo, las tools son de solo lectura y no existe ninguna tool que mueva dinero.
- Documentar la versión del modelo, los prompts relevantes y las dependencias con versión fija (`requirements.txt`).
- Atribución de librerías y de la fuente de FX (BCRP / ExchangeRate-API).
- Sin logos ni colores de BBVA y sin aparentar ser una app oficial.

---

## 8. Preparación para la prueba de evolución

| Cambio sorpresa probable | Ya preparado |
|---|---|
| Ingresos variables | Arquetipo «independiente irregular» + banda por bootstrap |
| Movimientos duplicados | Inyección en el generador + deduplicación en la ingesta, con test |
| Recomendación que debe ser explicable | Cada reco ya trae por qué, supuestos y confianza |
| Otro (desconocido) | Generador parametrizable + recomendador basado en reglas fáciles de agregar + `make test` en < 1 min |

Protocolo: (1) se lee el cambio, (2) se agrega el escenario al generador, (3) se escribe el test que falla, (4) se arregla, (5) se muestra el antes y el después en el panel de evidencia.

---

## 9. Estructura del repositorio

```
lucas/
├── README.md              # problema, usuario, solución, cómo ejecutar, requisitos
├── ARCHITECTURE.md        # diagrama, componentes, modelos, dependencias, salvaguardas
├── EVALUATION.md          # baseline vs modelo, métricas, intervalos, errores
├── PROMPTS.md             # prompts, versión del modelo, fallback
├── .env.example
├── Makefile               # make data | make test | make eval | make run
├── requirements.txt
├── data/
│   ├── generator.py
│   ├── dictionary.md
│   ├── QUALITY.md
│   └── sample/            # dataset pequeño versionado
├── src/
│   ├── ingest/            # validación, limpieza, dedup
│   ├── engine/            # categorías, recurrentes, calendario
│   ├── models/            # health, forecast, profile, anomalies
│   ├── recommender/
│   ├── assistant/         # providers, tools, verifier
│   ├── fx/                # BCRP + caché + respaldo
│   └── api/               # FastAPI
├── app/                   # UI
├── eval/                  # scripts que generan EVALUATION.md
├── tests/                 # unit + adversos + preguntas fijas del chat
└── demo/                  # guion, video de respaldo, capturas
```

**Regla de las bases:** el trabajo del evento debe distinguirse. Commits pequeños y frecuentes desde el sábado, y atribución de cualquier código reutilizado.

---

## 10. Roles (ajustar a quienes somos)

| Rol | Responsable de | Entregable |
|---|---|---|
| **Datos** | Generador, calidad, splits, dictionary.md | `make data` + QUALITY.md |
| **ML / Analítica** | Recurrentes, pronóstico, salud, perfiles, baselines | `make eval` + EVALUATION.md |
| **IA / Chat** | Providers, tools, verificador, preguntas fijas y adversas | Chat con ✓ + tests |
| **Backend** | FastAPI, validaciones, FX, recomendador, latencia | API + tests |
| **Frontend / UX** | Las 5 pantallas, simulador, accesibilidad | UI demo |
| **PM / Pitch** (puede ser compartido) | README, ARCHITECTURE, guion, video de respaldo, tiempos | Pitch ensayado |

Sincronización corta (10 min) en cada checkpoint: qué está hecho, qué bloquea y qué se recorta.

---

## 11. Cronograma

*(Ajustar a los horarios que publique la organización.)*

### Día 1 — sábado 14
| Bloque | Objetivo | Hecho cuando… |
|---|---|---|
| 1.ª hora | Cerrar usuario, decisión, criterios y stack; crear repo y esqueleto; contratos (esquema y endpoints) | Repo con estructura, `.env.example`, esquema acordado |
| Mañana | Generador v1 + ingesta + motor; **baselines primero**; mock de la UI con datos falsos | `make data` funciona; UI navega las 5 pantallas |
| Tarde | Pronóstico + banda, salud, recomendador v1, tools del chat; conectar API ↔ UI | **Primer flujo funcional de punta a punta** |
| Noche | Escenarios difíciles, verificador, fallback, primeros tests | Demo completa con datos sintéticos, aunque sea fea |

### Día 2 — domingo 15
| Bloque | Objetivo | Hecho cuando… |
|---|---|---|
| Mañana temprano | `make eval`: baseline contra modelo, intervalos, errores; panel de evidencia | EVALUATION.md con números reales |
| Mañana | Pulir UX, perfiles (si hay tiempo), FX con respaldo, prueba de evolución | Congelar funcionalidades |
| Mediodía | **Congelamiento de código.** README, ARCHITECTURE, PROMPTS; grabar el video de respaldo | Entrega completa en el repo |
| Tarde | 3 ensayos cronometrados del pitch y simulacro de preguntas | 10:00 min exactos |

**Regla de recorte:** si a mitad del día 1 el flujo de punta a punta no funciona, se recorta todo lo que sea «Debería» hasta que funcione.

---

## 12. Pitch (10 min + 3 de preguntas)

| Min | Contenido |
|---|---|
| 0:00–1:00 | Persona y dolor: «faltan 5 días para la quincena y no sabe si llega» |
| 1:00–2:00 | Decisión que mejoramos y criterios de éxito; por qué no es otro chatbot |
| 2:00–6:00 | **Demo en vivo** (flujo de la sección 6) |
| 6:00–8:00 | Evidencia: baseline contra modelo, cobertura de la banda, % de cifras verificadas, errores conocidos |
| 8:00–9:00 | Arquitectura en 3 capas, seguridad, privacidad, fallback offline |
| 9:00–10:00 | Límites y supuestos (datos sintéticos, clusters circulares, no es asesoría) y siguiente paso |

**Preguntas probables del jurado:** ¿por qué no basta con reglas? ¿Cómo evitan que el LLM invente cifras? ¿Qué pasa sin internet? ¿Cómo saben que los datos son plausibles? ¿Qué harían con datos reales y con consentimiento? Preparar una respuesta de 20 segundos para cada una.

---

## 13. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| Sin LLM disponible o lento | Ollama con modelo pequeño ya descargado + TemplateProvider |
| WiFi cae en la demo | Todo local; FX con serie grabada; video de respaldo |
| Alcance demasiado grande | MoSCoW estricto, flujo de punta a punta primero, regla de recorte |
| Métricas «demasiado buenas» por datos sintéticos | Decirlo; pruebas con perturbaciones; mostrar errores; escenarios difíciles; intervalos por bootstrap |
| Parecer app de BBVA | Marca Lucas propia, paleta propia, sin logos |
| El LLM inventa números | Verificador + reintento + fallback; medirlo y mostrarlo |
| Sonar a asesoría regulada | Lenguaje de «simulación/orientación», supuestos visibles, «tú decides» |

---

## 14. Preguntas para la organización (hacerlas hoy temprano)

1. ¿Se autoriza un LLM externo con clave propia (sin datos personales)? ¿O solo modelos locales?
2. ¿Hay un dataset común o lo generamos nosotros?
3. ¿Se pueden usar APIs públicas (BCRP) durante la demo?
4. Formato de entrega (repo público o privado, hora de cierre) y confirmación de 10 + 3 min.
5. ¿Se activa la prueba de evolución? ¿Cuándo y con qué peso?
6. ¿Se pueden traer modelos y dependencias descargados de antemano?

---

## 15. Checklist de salida (bases, sección 09)

- [ ] Problema y usuario definidos (sección 1)
- [ ] Datos legales y reproducibles (`make data`, semilla, QUALITY.md)
- [ ] MVP ejecutable (`make run`, también offline)
- [ ] IA/ML aporta valor medido (EVALUATION.md)
- [ ] Baseline y casos adversos (tests + preguntas adversas del chat)
- [ ] Seguridad y explicabilidad (verificador, reglas, «¿por qué?», `.env`)
- [ ] README y arquitectura
- [ ] Demo ensayada (3 veces + video de respaldo)
- [ ] Entrega completa (repo accesible al jurado)
