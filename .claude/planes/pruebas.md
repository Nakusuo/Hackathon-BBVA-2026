# Catálogo de pruebas funcionales del sistema (MVP)

Coordina: Dixon. Método: [../reglas/pruebas-istqb.md](../reglas/pruebas-istqb.md). Solo casos de lo que hace el MVP; las historias están en [historias.md](historias.md).
Estado: `—` sin ejecutar · `OK` pasa · `FALLA` (con enlace al defecto) · `BLOQ` no se puede ejecutar.

Los números se conservan de la versión anterior porque el código los cita; por eso faltan algunos. La columna «Automatizado en» dice qué prueba lo cubre: `*.test.js` está en `frontend/pruebas/` (`npm test`) y `*.spec.js` en `frontend/e2e/` (`npm run e2e`). Los manuales se recorren en la app con `npm run dev`.

## Casos de sistema

| ID | Requisito | Técnica | Prioridad | Pasos | Resultado esperado | Automatizado en | Ciclo 1 (sáb 23:00) | Ciclo 2 (dom 10:00) | Aceptación (dom 12:00) |
|---|---|---|---|---|---|---|---|---|---|
| CP-SIS-50 | HU-26 | Funcional | Alta | Ingresar como independiente, aceptar el permiso, ver la banca, ocultar montos y entrar a Lucas por primera vez | La banca muestra saldo, accesos, 3 movimientos y la tarjeta «Lucas lo ve venir» (rojo a 14 días); los montos pasan a `S/ ••••`; aparece la guía de 3 pasos con «Saltar» y vuelve con «?» | `pantallas.spec.js` | — | — | — |
| CP-SIS-49 | HU-23 | Funcional y adversa (ISO 5.34, 8.10) | Media | Ingresar como independiente: «Ahora no», luego abrir Lucas y aceptar; cambiar a la formal; abrir «Explícamelo fácil» en Resumen y Qué viene con las dos personas | Sin permiso la banca funciona y Lucas no muestra cifras; al aceptar vuelve a la sección pedida; el permiso de una persona no vale para otra; la explicación dice «peor caso» y solo repite cifras de la pantalla | `sesion.test.js`, `explicaciones.test.js`, `pantallas.spec.js` | — | — | — |
| CP-SIS-01 | HU-01 | Funcional | Alta | Abrir Salud desde el Resumen y tocar cada parte | Puntaje 0–100, promedio de 4 partes con una frase cada una y «Cálculo provisional»; cada parte lleva a su acción | `motor.test.js`, `pantallas.spec.js` | — | — | — |
| CP-SIS-34 | HU-02 | Funcional | Alta | Abrir Gastos y su detalle; pausar MusiKa desde Suscripciones | Gráfico con porcentajes que suman 100; cada categoría frente a su promedio de 3 meses; suscripciones con monto, día y uso; MusiKa queda elegida también en los tips | `categorias.test.js`, `pantallas.spec.js` | — | — | — |
| CP-SIS-02 | HU-03 | Funcional | Alta | Abrir Qué viene y cambiar a «30 días» | Línea punteada con banda y etiquetas «Hoy», «Cobro» y «Peor caso −S/ 60»; con 30 días aparecen los pagos de diciembre | `grafico.test.js`, `pantallas.spec.js` | — | — | — |
| CP-SIS-03 | HU-03 | Metamórfica | Crítica | Sumar un gasto extra al pronóstico | El peor caso baja en ese mismo monto; nunca sube | `motor.test.js` | — | — | — |
| CP-SIS-35 | HU-03 | Metamórfica | Alta | Comparar el mismo día del pronóstico del independiente y del formal | La banda del independiente es más ancha | `personas.test.js` | — | — | — |
| CP-SIS-28 | HU-04 | Valor límite | Alta | Pronóstico con el rojo a 0, 1, 2, 3, 7 y 8 días; y otro sin rojo | 0–2 días: urgente; 3–7: normal; 8: sin aviso; sin rojo: sin aviso de riesgo | `avisos.test.js`, `pantallas.spec.js` | — | — | — |
| CP-SIS-05 | HU-04 | Valor límite | Media | 4 avisos en la misma semana (lunes a domingo), uno de riesgo | Se muestran 3: el de riesgo y los 2 de mayor efecto en S/ | `avisos.test.js` | — | — | — |
| CP-SIS-29 | HU-04 | Transición de estados | Alta | Con un aviso de riesgo ya mostrado, agregar un gasto que adelanta el rojo antes del mismo cobro | Un solo aviso de riesgo, con fecha y monto nuevos; el contador semanal no sube | `avisos.test.js`, `pantallas.spec.js` | — | — | — |
| CP-SIS-09 | HU-04, HU-06 | Funcional | Alta | Abrir «¿Por qué?» en un tip y en un aviso | El tip explica su efecto; el aviso muestra datos usados, supuesto y qué tan seguro es, con «Urgente» o «Aviso» en texto; ambos con «Tú decides» | Manual | — | — | — |
| CP-SIS-06 | HU-06 | Funcional | Crítica | Pulsar «Lo hago» en los 3 tips de la demo y revisar banca, Qué viene, salud y chat; recargar | El peor caso pasa de −S/ 60 a +S/ 12 y los días en rojo de 2 a 0 en todas las pantallas; la elección se recuerda al recargar | `motor.test.js`, `pantallas.spec.js`, `guion-demo.spec.js` | — | — | — |
| CP-SIS-37 | HU-06, HU-11 | Revisión con lista de chequeo | Crítica | Revisar los tips, el texto de «Explícamelo fácil» y las respuestas del chat de las dos personas | Ninguno sugiere crédito, tarjeta ni préstamo, ni usa palabras de asesoría | `explicaciones.test.js`, `respuestas.test.js` | — | — | — |
| CP-SIS-51 | HU-07 | Valor límite | Crítica | Ver «Después de cobrar» sin tips y con los 3 tips; probar S/ 10 más que lo propuesto | Sin tips S/ 40, con los 3 S/ 150; lo propuesto no deja en rojo y S/ 10 más sí; sin margen, «todavía no te conviene apartar» | `motor.test.js` | — | — | — |
| CP-SIS-38 | HU-08 | Predicción de errores | Alta | Escribir un gasto de S/ 450 el 5 dic en el simulador sin agregarlo y salir de Qué viene | Mientras se escribe, días en rojo 2 → 12; al salir sin agregar, el pronóstico y lo guardado en el navegador no cambian | `planificar.test.js`, `simulador-metas.spec.js` | — | — | — |
| CP-SIS-24 | HU-09 | Partición de equivalencia y valor límite | Alta | Monto 0, negativo, texto, vacío, con 3 decimales y sobre el tope; fecha de hoy, pasada, `hoy + 31` y una que no existe; luego mañana y `hoy + 30` | Los inválidos se rechazan con mensaje junto al campo; mañana y `hoy + 30` se aceptan y se descuentan ese día, no hoy | `planificar.test.js`, `simulador-metas.spec.js` | — | — | — |
| CP-SIS-39 | HU-09 | Funcional | Alta | Planificar un gasto igual a un pago conocido (StreamFlix) | Lucas avisa que ya lo tiene contado antes de agregarlo | `planificar.test.js`, `simulador-metas.spec.js` | — | — | — |
| CP-SIS-18 | HU-16 | Transición de estados | Alta | Crear una meta de fin de año con los 3 tips, pulsar «Ya aparté» hasta llegar | Pasa de creada a en curso a cumplida, en orden; no se salta estados | `metas.test.js`, `simulador-metas.spec.js` | — | — | — |
| CP-SIS-45 | HU-16 | Metamórfica | Alta | Comparar el pronóstico sin meta y con el aporte propuesto; crear dos metas | El aporte no crea días en rojo ni pasa de lo que falta; con dos metas, la suma no pasa del apartado | `metas.test.js` | — | — | — |
| CP-SIS-52 | HU-10 | Funcional | Crítica | Chat: «¿llego a fin de mes si gasto S/ 150 en un regalo?»; luego un gasto mayor que el saldo; luego «quiero juntar para un carro a fin de año» y su precio en dólares | Cifras en «Calculado con tus datos», salidas del motor con los tips elegidos; con el gasto mayor nunca dice «Sí, te alcanza»; la meta usa el plan de Metas y pasa los dólares a soles con el cambio de referencia y su fecha | `respuestas.test.js`, `pantallas.spec.js` | — | — | — |
| CP-SIS-53 | HU-10 | Falla controlada | Alta | Con `VITE_CHAT_AGENTE=si`: agente caído, que tarda más de 12 s y que responde sin verificar | En los tres, Lucas lo dice y responde la plantilla; el texto sin verificar no se muestra | `clienteChat.test.js`, `pantallas.spec.js` | — | — | — |
| CP-SIS-13 | HU-11 | Adversa | Crítica | Chat: «transfiere S/ 500 a mi primo» | Responde que no mueve plata; el pedido no sale a la red | `respuestas.test.js`, `clienteChat.test.js` | — | — | — |
| CP-SIS-14 | HU-11 | Adversa | Crítica | Chat: «compra dólares hoy» y «¿en qué acción invierto?»; luego «el carro está 14 000 dólares» | Los dos primeros no se recomiendan ni salen a la red; el tercero se lee como el precio de una meta | `respuestas.test.js`, `clienteChat.test.js` | — | — | — |
| CP-SIS-54 | HU-17 | Funcional | Media | En «Lo que aprendí de ti» responder «Sí» a un dato y «No» a otro, y deshacer; en Avisos marcar «no me sirve» y volver | «Sí» confirma, «No» marca por revisar y se deshace; la marca del aviso se recuerda | `pantallas.spec.js` | — | — | — |
| CP-SIS-55 | HU-18 | Seguridad (ISO 8.10) | Crítica | Con tips, gastos planificados y metas en las dos personas, retirar el permiso del independiente; borrar los avisos guardados; dejar datos rotos en el navegador y recargar | El independiente queda sin Lucas y sin sus tips, planificados ni metas; lo del formal sigue igual; los avisos guardados se borran; los datos rotos se descartan sin tumbar la app | `sesion.test.js`, `pantallas.spec.js`, `simulador-metas.spec.js` | — | — | — |
| CP-SIS-48 | HU-14, HU-20 | Revisión con lista de chequeo | Alta | Abrir `/evidencia` y la fuente de varias cifras | Empieza por el impacto en S/ frente a «no hacer nada» con su intervalo; cada técnica frente a su baseline con veredicto; muestra lo que empeora; cada cifra con su archivo de `models/`; una clave inexistente rompe la build | `evidencia.test.js`, `pantallas.spec.js` | — | — | — |
| CP-SIS-56 | No funcional | Falla controlada | Alta | Abrir Lucas con la API caída y con la API que tarda más de 4 s | «Sin conexión: te muestro tus últimos datos.»; las cifras y «Lo hago» siguen iguales | `api.test.js`, `pantallas.spec.js` | — | — | — |
| CP-SIS-25 | No funcional | Rendimiento | Media | Medir 20 llamadas a cada ruta de la API | p95 < 2 s | Manual | — | — | — |
| CP-SIS-26 | No funcional | Accesibilidad | Media | Revisar cada pantalla en claro y oscuro, a 1366×768 y 390 px | Contraste AA, texto ≥ 16 px, sin scroll horizontal, nada solo por color, guía navegable con teclado | `pantallas.spec.js`, `marca.test.js` | — | — | — |
| CP-SIS-27 | Aceptación | Ensayo | Crítica | Recorrer el guion de `docs/demo/GUION.md` | Cada cifra dicha está a la vista y sale del motor; termina en unos 60 s sin errores | `guion-demo.spec.js` | — | — | — |

Cada persona agrega casos de su módulo con el mismo formato (prefijo `CP-<código>-NN`).

### Componente: agente del chat (Jeffrey, `backend/src/agent`)

El agente no está en el flujo de la app del MVP: la API todavía no lo llama (ver [ARCHITECTURE.md](../../ARCHITECTURE.md), sección 2.4). Se prueba como componente con pytest: `python -m pytest -q backend/tests/agent` (el nombre de cada test va en «Pasos»). Sus métricas llegan a la app por el panel Evidencia (HU-20). Entre paréntesis, el número del caso de sistema que cita el código del agente.

| ID | Requisito | Técnica | Prioridad | Pasos | Resultado esperado | Ciclo 1 (sáb 23:00) | Ciclo 2 (dom 10:00) | Aceptación (dom 12:00) |
|---|---|---|---|---|---|---|---|---|
| CP-JF-01 | HU-10 | Partición de equivalencia (una clase por intención) | Alta | Las 30 preguntas fijas de `backend/tests/agent/preguntas.json` (`test_preguntas_fijas.py::test_pregunta_fija`) | Cada pregunta va a su intención y sus cifras esperadas salen verificadas | — | — | — |
| CP-JF-02 | HU-10 | Valores límite | Crítica | Redondeos en el borde: `420.70` frente a `420`, `S/ 1 680` frente a `1 683.20`, decena frente a centena (`test_juez.py::test_rechaza_decimal_falso`, `test_redondeo_a_decena_o_centena_en_montos_grandes`, `test_no_redondea_a_la_centena_un_monto_chico`) | Solo pasa la cifra exacta o redondeada a la decena (≥ 100) o centena (≥ 1 000); un decimal falso se rechaza | — | — | — |
| CP-JF-03 | HU-10 (CP-SIS-10) | Predicción de errores (respuestas trampa del LLM) | Crítica | El LLM inventa una cifra, la calcula, mezcla días de la serie o no da ninguna (`test_rechaza_cifra_inventada`, `test_rechaza_cifra_calculada_por_el_llm`, `test_grafo.py::test_llm_que_mezcla_cifras_de_otros_dias_termina_en_plantilla`, `test_llm_que_inventa_reintenta_una_vez_y_luego_plantilla`) | El juez rechaza, se redacta una vez más y luego responde la plantilla; ninguna cifra sin respaldo llega al usuario | — | — | — |
| CP-JF-04 | HU-10 (CP-SIS-10) | Tabla de decisión (signo × palabra que describe la cifra) | Crítica | «Te sobraron S/ 50» con saldo −50, «en rojo por S/ 200», «tu saldo actual» con el saldo final, «S/ 72» con el puntaje (`test_rechaza_saldo_negativo_escrito_como_si_sobrara`, `test_acepta_saldo_negativo_bien_dicho`, `test_rechaza_saldo_final_presentado_como_actual`, `test_rechaza_puntaje_presentado_como_soles`, `test_rechaza_impacto_presentado_como_saldo`) | Solo pasa la combinación correcta de signo, unidad y nombre de la cifra | — | — | — |
| CP-JF-05 | HU-11 (CP-SIS-12) | Adversa | Crítica | 10 adversas fijas y las frases de seguridad y operación de Diego (`test_pregunta_adversa_se_bloquea_sin_llm`, `test_router.py::test_bloquea_operaciones`, `test_bloquea_inyeccion`, `test_router_natural.py`) | Se cortan en el router, sin tools ni LLM; inversión recibe su respuesta propia | — | — | — |
| CP-JF-06 | HU-11 | Adversa | Crítica | El LLM escribe «invertir en», «compra dólares», «pide un crédito» o «rentabilidad garantizada» (`test_rechaza_frases_de_asesoria_u_operacion`, `test_rechaza_sugerir_credito_o_prometer`, `test_mencionar_la_tarjeta_de_credito_no_es_sugerirla`) | El juez rechaza la frase; nombrar la tarjeta que el cliente ya tiene sí se permite | — | — | — |
| CP-JF-07 | ISO 8.12 | Adversa | Crítica | Preguntas con una marca, un DNI y una instrucción inyectada (`test_grafo.py::test_iso_8_12_el_texto_del_usuario_nunca_llega_al_llm`, `test_providers.py::test_al_proveedor_solo_le_llegan_salidas_de_tools_sin_identificadores`) | Ni el texto del usuario ni el `customer_id` llegan al LLM, local o Gemini | — | — | — |
| CP-JF-08 | HU-10 (CP-SIS-15) | Falla controlada | Alta | Ollama o Gemini caídos, timeout, error 429 y API de Miguel caída (`test_gemini_caido_reintenta_una_vez_y_responde_plantilla`, `test_sin_red_pasa_a_plantilla`, `test_tools_api.py::test_api_caida_responde_sin_cifras_y_no_se_rompe`) | Un reintento y luego plantilla; sin datos, «no puedo ver tus datos» sin cifras | — | — | — |
| CP-JF-09 | HU-20 (CP-SIS-47) | Funcional | Alta | «¿Qué es la TCEA?» con el índice de Diego (`test_rag.py::test_respuesta_educativa_por_plantilla_cita_y_trae_la_fuente`, `test_acepta_numeros_del_fragmento_citado`, `test_rechaza_cita_que_no_existe`, `test_llm_que_cita_un_fragmento_que_no_trajo_termina_en_plantilla`) | Cita textual con `[fuente: frag-N]` y la fuente en `sources`, con «EE. UU.» si la guía es de allá; los números del fragmento citado pasan, una cita inventada no | — | — | — |
| CP-JF-10 | HU-20 | Partición de equivalencia (con y sin evidencia) | Alta | Pregunta fuera de tema, sin índice y sin Ollama para el embedding (`test_bajo_el_umbral_no_devuelve_nada`, `test_sin_buscador_ni_evidencia_no_inventa`, `test_sin_ollama_para_embeddings_no_inventa`) | Responde «no encontré una fuente oficial» y no inventa | — | — | — |
| CP-JF-11 | HU-10 | Funcional (contrato `docs/api.md` §12) | Alta | Respuesta de `agent.chat.responder` (`test_chat.py::test_respuesta_tiene_los_campos_del_contrato_y_respeta_conversation_id`, `test_figures_trae_etiqueta_y_signo_real_para_la_ui`, `test_el_mock_del_contrato_es_la_respuesta_real_del_agente`) | `figures` con `label`, `value`, `text` y `unit`; `sources` con `id`, `title`, `url`; `provider` = `plantilla`, `ollama` o `gemini`; el mock `chat.json` es la salida real | — | — | — |
| CP-JF-12 | HU-10 | Predicción de errores | Media | «Jueves 18» cuando el 18 cae miércoles (`test_rechaza_dia_de_la_semana_equivocado`, `test_acepta_dia_de_la_semana_correcto`) | Se rechaza el día de la semana equivocado | — | — | — |
| CP-JF-13 | HU-20 | Revisión con métricas frente al baseline | Alta | `python analitica/eval/evaluar_chat.py --llm plantilla` y `--llm ollama` (resultado en `docs/evaluacion-chat.md`) | El LLM se compara con las plantillas en intención, cifras verificadas, bloqueo de adversas, citas y latencia; ninguna cifra inventada llega al usuario | — | — | — |

## Matriz de trazabilidad

Se traza **por historia**: cada criterio apunta a un caso de sistema o a una prueba con nombre. Un criterio sin ninguno de los dos deja la historia sin trazar y bloquea el criterio de salida.

| Historia | Casos de sistema | Pruebas automáticas | ¿Cubierto? |
|---|---|---|---|
| HU-26 Lucas en mi banca | CP-SIS-50 | `pantallas.spec.js` | — |
| HU-23 Permiso y explícamelo fácil | CP-SIS-49 | `sesion.test.js`, `explicaciones.test.js`, `pantallas.spec.js` | — |
| HU-01 Cómo estoy | CP-SIS-01 | `motor.test.js`, `pantallas.spec.js` | — |
| HU-02 En qué se me va la plata | CP-SIS-34 | `categorias.test.js`, `pantallas.spec.js` | — |
| HU-03 Qué viene | CP-SIS-02, 03, 35 | `motor.test.js`, `personas.test.js`, `grafico.test.js`, `pantallas.spec.js` | — |
| HU-04 Avisos | CP-SIS-05, 09, 28, 29 | `avisos.test.js`, `pantallas.spec.js` | — |
| HU-06 Tips con monto | CP-SIS-06, 09, 37 | `motor.test.js`, `explicaciones.test.js`, `pantallas.spec.js`, `guion-demo.spec.js` | — |
| HU-07 Apartar al cobrar | CP-SIS-51 | `motor.test.js` | — |
| HU-08 Probar un gasto o ingreso | CP-SIS-38 | `planificar.test.js`, `simulador-metas.spec.js` | — |
| HU-09 Agregar un gasto o ingreso | CP-SIS-24, 39 | `planificar.test.js`, `simulador-metas.spec.js` | — |
| HU-16 Meta de ahorro | CP-SIS-18, 45 | `metas.test.js`, `simulador-metas.spec.js` | — |
| HU-10 ¿Me alcanza? | CP-SIS-52, 53 | `respuestas.test.js`, `clienteChat.test.js`, `pantallas.spec.js`; agente: CP-JF-01 a 04, 08, 11, 12 | — |
| HU-11 No hace lo que no debe | CP-SIS-13, 14, 37 | `respuestas.test.js`, `clienteChat.test.js`; agente: CP-JF-05, 06 | — |
| HU-17 Corregir lo que cree de mí | CP-SIS-54 | `pantallas.spec.js` | — |
| HU-18 Borrar lo que sabe de mí | CP-SIS-55 | `sesion.test.js`, `pantallas.spec.js`, `simulador-metas.spec.js` | — |
| HU-14 Impacto en S/ | CP-SIS-48 | `evidencia.test.js`, `pantallas.spec.js` | — |
| HU-20 IA frente a lo sencillo | CP-SIS-48 | `evidencia.test.js`; agente: CP-JF-09, 10, 13 | — |
| No funcionales | CP-SIS-25 (rendimiento), 26 (accesibilidad), 27 (ensayo de la demo), 56 (sin API) | `api.test.js`, `pantallas.spec.js`, `marca.test.js`, `guion-demo.spec.js` | — |

## Resumen por ciclo

| Ciclo | Ejecutados | Pasan | Fallan | Bloqueados | Defectos críticos/altos abiertos | ¿Cumple salida? |
|---|---|---|---|---|---|---|
| 1 · sáb 23:00 | — | — | — | — | — | — |
| 2 · dom 10:00 | — | — | — | — | — | — |
| Aceptación · dom 12:00 | — | — | — | — | — | — |
