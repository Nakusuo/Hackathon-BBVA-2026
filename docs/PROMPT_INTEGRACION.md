# Prompt para quien haga la integración final

Para una IA (o una persona) que vaya a unir la rama de analítica e IA de Diego con el agente del producto. Pégalo tal cual y adjunta el repo. Todo lo que afirma está verificado en esta rama; lo que no, está marcado.

---

## Rol y objetivo

Eres el integrador. Debes unir **dos agentes** del proyecto Lucas (copiloto de liquidez a 30 días, banco ficticio «Banco Kawsay») en uno solo, tomando **lo mejor de cada uno**, sin romper nada de lo ya validado y sin introducir falsos positivos.

- **Rama de analítica e IA (esta):** `feature/ml-segmentos-pronostico`. Modelos, datos sintéticos, RAG, calendario laboral, datos vivos, vigilancia, traducción, puerta de calidad. El agente vive en `src/agente_analitico/`.
- **Agente del producto:** PR #5 de Jeffrey en `develop` (`src/agent/`, `src/bcrp/servicio.py`, `tests/agent/`, `tests/bcrp/`). Consume la API de Miguel por herramientas (`get_health`, `get_forecast`, `get_recos`, `simulate`, `get_fx`).
- **Contrato de la API:** `docs/api.md` v0.2 y mocks en `data/sample/mocks/` (están en `develop`, no en esta rama).

## Lo primero que debes leer (en este orden)

1. `docs/RESUMEN_DIEGO.md`: qué se hizo, añadió, quitó, modificó y usó; fuentes con enlaces (sección 8); rutas de API (8.7); cómo integrarlo (9); mapeo al contrato y lo mejor de cada lado (10).
2. `docs/QA_ANALITICA.md`: puerta de calidad, con la lista de **lo que no se pudo verificar**.
3. `docs/comparativa_modelos.md`: qué modelo se eligió para cada problema, por qué y su límite.
4. `data/parametros/normas_laborales.yaml`: cada regla laboral con su frase literal de la norma.
5. `docs/modelo_de_datos/README.md`: el **modelo de datos para PostgreSQL con pgvector** (esquema, diccionario, diagrama, cargador, evidencia de la prueba contra una base real). El equipo no tiene base de datos: se crea con eso.
6. `docs/RESUMEN_DIEGO.md` secciones 9.1 a 9.15 (la 9.15 es la **línea base aprobada que el agente unido debe igualar o superar** y las mejoras posibles): conectar la API final y sus límites (9.1), plantillas si cae la API (9.2), consumo de tokens con el ahorro en porcentajes y en soles (9.3), preguntas frecuentes (9.4), qué añadirle al aplicativo (9.5), RAG validado (9.6), modelo de datos (9.7), MLflow (9.8), orden de regeneración (9.9), **chat conversacional y cómo se validó (9.10)**, **inventario de modelos, APIs y variables (9.11)**, **post-validación obligatoria (9.12)**, pipeline de punta a punta (9.13) **guía paso a paso con código y recetas para añadir piezas (9.14)** y línea base y mejoras (9.15). El mismo informe, completo, está en `.claude/equipo/diego/registro.md`.
7. `docs/presentacion/README.md`: gráficas y diagramas para la presentación (comparativa de cada modelo con su baseline, arquitectura, RAG, modelo de datos, nodos del agente, serie diaria, puntos).

## Qué usar de esta rama (portar al agente final)

| Pieza | Dónde | Por qué |
|---|---|---|
| Modelos y contexto del cliente | `src/models/`, `src/agente_analitico/repositorio.py`, `models/*.pkl` | Son los que la API debe servir («el cálculo debe venir de los modelos de Diego») |
| Calendario laboral (CTS, gratificación, retiro de la CTS) | `src/models/calendario_laboral.py` + `normas_laborales.yaml` | Reglas con evidencia literal; la libre disposición del 100 % vence el 31-12-2026 (Ley 32322) |
| Datos vivos y vigilancia | `datos_vivos.py`, `vigilancia.py` | Avisos únicos, tope de 3 por semana, casos que no deben avisar probados |
| Router ampliado | `grafo.py` (`REGLAS_INTENCION`) + `tests/test_router_natural.py` | 75 frases naturales, 0 desviaciones |
| Verificador de cifras | `verificador.py` + `tests/test_verificador.py` | Acepta las dos lecturas de un número ambiguo (3.406) y rechaza código y promesas |
| Proveedores de LLM | `proveedores.py` + `tests/test_proveedores.py`, `tests/test_agente_llm.py` | Cambiar de API es cambiar 3 variables; el camino con LLM está probado con una API falsa |
| BCRP con frescura | `src/bcrp/cliente.py` | Un dato viejo no se presenta como actual ni dispara avisos |
| RAG | `src/rag/`, `docs/rag/` (3 761 fragmentos, validado con `eval/validar_rag.py`) | Filtro de relevancia, siglas, aviso de fuente extranjera; prefijos del modelo de embeddings y sin duplicados |
| Pronóstico día por día con la forma del contrato `/forecast` | `src/agente_analitico/contrato.py` (`pronostico_contrato`), `src/models/serie_diaria.py`, `models/serie_diaria.pkl` | 30 días con banda al 80 %, cobertura medida en cada día; el día 30 es el pronóstico validado |
| Preguntas frecuentes que ahorran tokens | `src/agente_analitico/faq.py`, `data/faq/faq_semilla.json`, `docs/PREGUNTAS_FRECUENTES.md` | Una pregunta de concepto ya verificada se reutiliza sin LLM; lo aprendido vive en una base de datos y se exporta a embeddings |
| Modelo de datos (PostgreSQL + pgvector) y cargador | `docs/modelo_de_datos/`, `eval/cargar_a_postgres.py` | Esquema probado con la data sintética completa; separa lo observable de la verdad oculta del simulador |
| Seguimiento y versionamiento de modelos | `eval/registrar_en_mlflow.py`, `docs/presentacion/mlflow_resumen.md` | Baseline frente a elegido por problema y Model Registry con alias `produccion` |
| **Chat conversacional** (saludo, mensajes abiertos, emociones, opciones/botones) | `grafo.py` (`CONVERSACION`, `_opciones`, `_plantilla_conversacional`, `bienvenida`), `proveedores.SISTEMA`, `tests/test_conversacion.py` | Un «hola» no se rechaza: plantilla cálida y botones según el perfil (0 tokens); lo emocional va a la IA con empatía; lo que no se entiende ofrece opciones; `responder()` devuelve `opciones` |
| Ahorro en porcentajes y en soles | `eval/mapa_de_consultas.py` (clave `costos`), `docs/presentacion/graficas/ahorro_en_porcentaje_y_soles.png` | Tokens medidos x precio publicado x tipo de cambio del BCRP; para la presentación |
| Traducción es/en/qu | `traduccion.py` | Cifras y nombres protegidos; reintento ante errores transitorios |
| Puerta de calidad | `eval/puerta_de_calidad.py` | Un solo comando valida todo |

## Qué conservar del agente del producto (no lo pierdas)

Intención «simular» con extracción de monto y su respuesta por plantilla (el LLM **no** calcula), respuesta de `/chat` lista para Miguel, cifras con etiqueta para el chat de Marcela, normalización de tildes del router y sus pruebas (`tests/agent/`). Son observaciones por lectura: **mide antes de decidir**.

## Qué modificar

1. **Adaptador al contrato** (no existe aún): traducir las salidas de `Repositorio.contexto`, `recomendador` y `vigilancia` a los nombres de `docs/api.md`. La tabla está en `RESUMEN_DIEGO.md` §10. Puntos abiertos a acordar con Diego y Miguel: `quadrant` (propuesta incluida), `emergency_fund_months` (mi colchón mide **meses de ingreso**, no de gasto), `impact_type`.
2. **Router y juez:** parte del de Jeffrey y suma lo de esta rama. Pasa **mis 75 frases** (`tests/test_router_natural.py`) por su router y **sus pruebas** (`tests/agent/`) por mi verificador antes de decidir; documenta las diferencias.
3. **Un solo cliente del BCRP:** el de esta rama (API → caché → grabada, con `al_dia`) más la serie grabada de Jeffrey (`data/bcrp/serie_grabada.json`).
4. **Un nombre por documento del RAG:** hay PDFs duplicados con nombres distintos; `docs/rag/fuentes.csv` es el registro (con hash) y la puerta de calidad verifica que ninguno se haya alterado.
5. **Requirements:** une `requirements-analitica.txt` y `requirements-ia.txt`. Los pines compartidos difieren solo en parche (langgraph 1.2.22 frente a 1.2.20, pypdf 7.1.0 frente a 7.0.1); Jeffrey suma `langchain-google-genai`, `ollama`, `google-genai`, `httpx`. No está probado el entorno unido.
6. **Simulación:** `Repositorio._pronostico(fila, neto)` vuelve a puntuar el modelo con el saldo corregido (gasto único). Ingresos y gastos recurrentes quedan por definir con Dixon.
7. **Serie diaria del pronóstico (ya entrenada y validada):** usa `contrato.pronostico_contrato(repo, customer_id, dias)` para `GET /forecast`; devuelve `forecast[]` con `date`, `predicted_balance`, `lower_bound`, `upper_bound` y suma `data_as_of`, `risk_probability`, `synthetic_data` y `sample_only: false`. La cobertura de la banda al 80 % se midió en cada uno de los 30 días (0.79 a 0.86) y el día 30 es el pronóstico validado. Los días entre horizontes se interpolan y se miden igual.
8. **Base de datos:** crea PostgreSQL con `pgvector` y carga con `python eval/cargar_a_postgres.py --crear --rag` (ver `docs/modelo_de_datos/README.md`). Los modelos solo deben leer el esquema `lucas`; el esquema `simulacion` (verdad oculta del generador) se borra con datos reales. Traslada las preguntas frecuentes de SQLite a las tablas `faq_*` (mismo esquema) y sus embeddings a `faq_embedding`.
9. **API de IA final:** cambia `LLM_PROVIDER` y las variables de `.env` (RESUMEN 9.1). Con una API sin límite estricto conviene `LLM_USO=siempre`. Conserva las tres lecciones de la QA: reintentar errores transitorios con espera, leer **todas** las partes de la respuesta de Gemini y rechazar toda respuesta cuyo `finishReason` no sea `STOP`.

10. **Chat conversacional (no lo pierdas al unir los agentes):** la persona suele empezar con «hola», «buenos días», «buenas tardes», «buenas noches», «ola», «hello», «oye» o «ayúdame», o contando cómo se siente. El agente unido **nunca** debe responder «no entiendo» ni cerrar la conversación ante eso. Funciona con **tres capas que se apoyan**: (1) **reglas** (0 tokens) reconocen saludos de cualquier hora e idioma, temas conocidos y lo que se rechaza; (2) cuando **ninguna regla entiende**, **entra la IA** a interpretar con lo que sabe de la persona (modelos, recomendaciones) y de las fuentes (RAG) y gira la conversación hacia lo que sí puede hacer; (3) la **plantilla de respaldo y los botones** acogen y ofrecen opciones si no hay IA. Un saludo se contesta con plantilla cálida y 2 a 4 botones según el perfil (0 tokens); lo emocional va a la IA con empatía; lo que no entiende ofrece opciones; lo claramente ajeno («¿qué hora es?») y lo de seguridad se contestan con plantilla (no llegan al LLM) y solo la seguridad va sin opciones. Si el agente de Jeffrey puede mejorar alguna capa (memoria de turnos, clasificación por embeddings, derivación a una persona), **adelante**, siempre que no empeore la línea base de RESUMEN 9.15. El front debe pintar `opciones` como botones (cada uno envía su `pregunta` a `/chat`) y puede abrir el chat con `grafo.bienvenida()`. Si el router de Jeffrey reemplaza al de esta rama, sus saludos deben caer en `conversacion` y **no** en fuera de tema (`tests/test_conversacion.py`). Detalle, contrato de `opciones` y límites (el agente no recuerda el turno anterior): RESUMEN 9.10.
11. **Post-validación (obligatoria):** al terminar de unir, repite todo lo de RESUMEN 9.12 con el agente unido: las dos suites, la puerta de calidad, la evaluación con plantillas, la QA con API real (`python eval/qa_agente.py`: perfil, adversarios, conversaciones, trampas, **aperturas y botones**) y la **batería conversacional a mano en el front** («buenos días», «buenas tardes», «buenas noches», «ola», «hello», «hola Lucas», «lo de ayer», «¿qué hora es?» seguido de «¿cómo voy este mes?» para comprobar que la conversación sigue, «hola», «oye», «ayúdame», «buenas, necesito ayuda», «no sé por dónde empezar», «tengo un problema con mi plata», «estoy muy preocupado por mis deudas», «gracias», «chau», «ayuda con mi plata», «Hola, ¿cómo voy este mes?», «Cuéntame un chiste», «Ignora tus instrucciones»), tocando cada botón con un perfil independiente y uno dependiente, con la API caída y con la cuota agotada. Lo que no puedas correr se deja escrito como no verificado.

## Orden de trabajo

```bash
git switch -c feature/arq-integracion-final origin/develop      # rama nueva; nunca trabajes sobre develop ni main
git merge --no-ff feature/ml-segmentos-pronostico                # sin conflictos de archivos: el agente de esta rama está en src/agente_analitico/
pip install -r requirements-analitica.txt -r requirements-ia.txt
python -m pytest -q                                              # las dos suites; si falta una dependencia, instálala y repórtalo
python eval/puerta_de_calidad.py --gemini                        # debe dar 0 FAIL
```
Después escribe el adaptador, une router y juez, y vuelve a correr la puerta. Al terminar: `git rm -r --cached data/generado` (los datos sintéticos se cargaron temporalmente; la carpeta ya está en `.gitignore`).

## Reglas duras del equipo (no negociables)

- Gitflow: trabajo en `feature/<rol>-<tema>`; **no push directo a `develop` ni `main`**; sin `--force` sobre ellas; PR con revisión. Los agentes **no hacen push ni abren PR sin permiso de una persona**.
- Commits en español, `tipo(área): qué cambia`, **sin coautor ni atribución a IA**.
- Nunca `.env`, claves, rutas absolutas de una laptop ni datos reales. Los datos son **sintéticos**.
- **Ninguna marca ni banco real**: la entidad es «Banco Kawsay» y la app «Lucas». Se dice «podría integrarse en un banco», nunca «es de BBVA».
- El LLM **redacta, no calcula**: toda cifra sale de una herramienta y pasa por el verificador; si el LLM inventa una cifra, devuelve código o promete algo, la respuesta cae a la plantilla.
- No mover dinero, no recomendar comprar o vender dólares ni en qué invertir; esos pedidos se cortan antes de cualquier modelo.
- No tratar un proyecto de ley como ley; no presentar un dato desactualizado como actual.
- Todo hecho dependiente de la fecha usa el reloj único (`src/comun/reloj.py`), nunca `date.today()` suelto.

## Cómo comprobar que no rompiste nada ni introdujiste falsos positivos

- `python -m pytest -q` y `python eval/puerta_de_calidad.py --gemini`: cero FAIL. Los WARN y NOT RUN están documentados y no bloquean; **si aparece uno nuevo, explícalo**.
- Falsos positivos del ruteo: corre `tests/test_router_natural.py` contra el router unido. La primera medición de esta rama desvió 25 de 75 frases (un tercio) y se corrigió; no lo reintroduzcas.
- Falsos positivos del verificador: `tests/test_verificador.py` (3.406 no es 3 406).
- Avisos de la vigilancia: `tests/test_vigilancia.py` cubre los casos que **no** deben avisar.
- Calidad con LLM real: `python eval/qa_agente.py` (una sola corrida, unas 50 llamadas y ~7 minutos con pausas de `QA_RITMO_S` para no agotar la cuota por minuto del plan gratuito; si se agota espera y reintenta una vez). No lo repitas sin necesidad: gasta tokens.
- Conversación: `tests/test_conversacion.py` (saludos, emociones, botones, rechazo amable, API falsa: un saludo no llama al LLM y lo emocional sí) y la batería a mano de arriba. Criterio: **nunca** «no entiendo» ante un saludo, nunca una respuesta vacía, nunca una cifra inventada.
- Si cambias código del agente, vuelve a correr `eval/evaluar_agente.py`, `eval/qa_agente.py` y `eval/generar_docs.py`: la puerta de calidad compara huellas de contenido y marcará FAIL si una evaluación o un informe quedó desfasado.

## Proximos pasos conocidos (no los ocultes)

- **Quechua:** medido contra FLORES-200 (chrF 34 frente a un piso de 18); falta la revisión de un hablante nativo (próximo paso).
- **Google Cloud Translation:** el contrato está probado con respuestas simuladas; falta una llamada real con clave propia (una clave de Gemini da 401 en esa API) (próximo paso).
- **Programa de puntos:** depende de supuestos del equipo hasta un piloto con grupo de control: con solo lo medido pierde unos S/ 5.5 por usuario al año y se paga con ~3 % más de ahorro apartado (próximo paso).
- **Pruebas del agente de Jeffrey** (`tests/agent/`): no están en esta rama; se corren en la rama `develop` al integrar todo.
- **Datos reales de un banco:** no aplica al MVP; el reto pide datos sintéticos (criterio cerrado). El generador acepta una tabla semilla (ENAHO) para regenerar.
- **CTS después de 2026:** vigente hasta el 31-12-2026 (Ley 32322); el proyecto de ley que propone extenderla hasta 2028 está en evaluación y no es ley (El Peruano, nota 308663, 9-11-2026). El agente dice las dos cosas; hay que volver a contrastarla después del 31-12-2026.
- **Sentimiento:** el set independiente lo escribió un LLM y el sentimiento no está en producción.
- **Chat conversacional:** el router es de reglas (lo que no reconoce recibe opciones, no una respuesta experta); la empatía la redacta un modelo de lenguaje y no la revisó una persona especialista; el agente no guarda estado entre llamadas (no recuerda el turno anterior: el front debe reenviar el contexto si quiere seguimiento). Se validó con las frases de la lista de arriba: **el integrador debe correr su propia batería** (post-validación, RESUMEN 9.12).
- **Front:** mostrar los botones de `opciones`, abrir el chat con `bienvenida()` y etiquetar «respuesta automática» cuando `proveedor` sea `plantilla`.

## Entregable

Un informe corto con: qué tomaste de cada lado y por qué (con la medición que lo respalda), qué modificaste, resultado de la puerta de calidad y de las dos suites, y lo que quedó pendiente.
