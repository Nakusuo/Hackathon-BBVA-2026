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
| RAG | `src/rag/`, `docs/rag/` (3 833 fragmentos) | Filtro de relevancia, siglas, aviso de fuente extranjera |
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
7. **Serie diaria del pronóstico:** el contrato la pide y **no está entrenada** (el modelo está calibrado en el día 30). Decide con Diego entre entrenar horizontes 1 a 30 o usar la trayectoria estructural del modelo; no inventes una interpolación y la presentes como validada.

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
- Calidad con LLM real: `python eval/qa_agente.py` (una sola corrida, ~17 llamadas). No lo repitas sin necesidad: gasta tokens.
- Si cambias código del agente, vuelve a correr `eval/evaluar_agente.py`, `eval/qa_agente.py` y `eval/generar_docs.py`: la puerta de calidad compara huellas de contenido y marcará FAIL si una evaluación o un informe quedó desfasado.

## Pendientes conocidos (no los ocultes)

Calidad del quechua sin hablante nativo; Google Cloud Translation sin clave propia; 17 de 18 parámetros de eventos simulados son supuestos o parciales; sentimiento sin set independiente; programa de puntos sin piloto (pierde unos S/ 5.5 por usuario al año sin consumo nuevo); la libre disposición de la CTS después de 2026 depende de si se aprueba el proyecto que la amplía (hoy **no es ley**).

## Entregable

Un informe corto con: qué tomaste de cada lado y por qué (con la medición que lo respalda), qué modificaste, resultado de la puerta de calidad y de las dos suites, y lo que quedó pendiente.
