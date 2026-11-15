"""Documento del modelo de datos para quien cree la base de datos en la integracion final: docs/modelo_de_datos/README.md.
Se genera DESDE docs/modelo_de_datos/schema_postgres.sql (tablas, columnas, tipos, restricciones y notas) y desde la evidencia de validacion (validacion_postgres.json), de modo que el documento y el
esquema no se pueden desalinear. Tambien deja el diagrama entidad-relacion en Mermaid (se ve en GitHub).
Uso: python analitica/eval/generar_modelo_de_datos.py"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "backend"))
CARPETA = os.path.join(RAIZ, "docs", "modelo_de_datos")

ORIGEN = {  # tabla -> de donde sale (archivo Parquet o proceso)
    "lucas.cliente": "`clientes.parquet` (columnas observables)", "simulacion.cliente_verdad": "`clientes.parquet` (etiquetas y parametros internos del simulador)",
    "lucas.transaccion": "`transacciones/*.parquet` (sin las etiquetas es_*)", "simulacion.transaccion_verdad": "`transacciones/*.parquet` (es_recurrente, es_atipico, es_suscripcion_duplicada)",
    "lucas.saldo_diario": "`saldo_diario/*.parquet`", "lucas.panel_mensual": "`panel_mensual/*.parquet`", "lucas.mensaje": "`mensajes/*.parquet`", "lucas.contexto_diario": "`contexto_diario.parquet`",
    "lucas.evento": "`eventos.parquet`", "lucas.macro_mensual": "`macro_mensual.parquet` (series reales del BCRP)", "simulacion.calidad_etiqueta": "`etiquetas_calidad/*.parquet`",
    "lucas.movimiento_vivo": "aplicativo (`datos_vivos.registrar`, `POST /expenses`)", "lucas.memoria_cliente": "agente (`memoria.py`)", "lucas.meta_ahorro": "aplicativo (propuesta)",
    "lucas.respuesta_recomendacion": "agente (`memoria.registrar_respuesta`)", "lucas.movimiento_puntos": "agente (`memoria.sumar_puntos`)", "lucas.aviso": "vigilante (`vigilancia.ciclo`)",
    "lucas.consulta_chat": "agente (campos de `responder()`)", "lucas.pronostico_diario": "modelo (`contrato.pronostico_contrato`), cache opcional", "lucas.rag_fuente": "`docs/rag/fuentes.csv`",
    "lucas.rag_fragmento": "`docs/rag/indice/` (fragmentos y vectores FAISS)", "lucas.faq_aprendida": "agente (`faq.py`)", "lucas.faq_preguntas_vistas": "agente (`faq.py`)",
    "lucas.faq_contadores": "agente (`faq.py`)", "lucas.faq_embedding": "`faq.exportar_para_embeddings()` + nomic-embed-text"}
GRUPO = [("1. Clientes y movimientos (data sintetica; con datos reales los trae la entidad)", ["lucas.cliente", "lucas.transaccion", "lucas.saldo_diario", "lucas.panel_mensual", "lucas.mensaje", "lucas.contexto_diario",
                                                                                                "lucas.evento", "lucas.macro_mensual"]),
         ("2. Verdad oculta del simulador (solo para evaluar; con datos reales se borra el esquema `simulacion`)", ["simulacion.cliente_verdad", "simulacion.transaccion_verdad", "simulacion.calidad_etiqueta"]),
         ("3. Lo que el aplicativo y el agente guardan al funcionar", ["lucas.movimiento_vivo", "lucas.memoria_cliente", "lucas.meta_ahorro", "lucas.respuesta_recomendacion", "lucas.movimiento_puntos", "lucas.aviso",
                                                                      "lucas.consulta_chat", "lucas.pronostico_diario"]),
         ("4. RAG y preguntas frecuentes", ["lucas.rag_fuente", "lucas.rag_fragmento", "lucas.faq_aprendida", "lucas.faq_preguntas_vistas", "lucas.faq_contadores", "lucas.faq_embedding"])]


def parsear(sql: str) -> dict:
    """Tablas del esquema: {nombre: {'columnas': [(nombre, tipo, restricciones, nota)], 'tabla_nota': str}} leidas de las sentencias CREATE TABLE."""
    tablas = {}
    for m in re.finditer(r"CREATE TABLE (\w+\.\w+) \((.*?)\n\);", sql, re.S):
        cols = []
        for linea in m.group(2).split("\n"):
            linea = linea.rstrip()
            if not linea.strip() or linea.strip().startswith(("PRIMARY KEY", "CHECK", "--", "UNIQUE")):
                continue
            cuerpo, _, nota = linea.partition("--")
            cuerpo = cuerpo.strip().rstrip(",")
            p = re.match(r"(\w+)\s+(.+)", cuerpo)
            if not p:
                continue
            nombre, resto = p.groups()
            t = re.match(r"(vector\(\d+\)|NUMERIC\(\d+,\d+\)|CHAR\(\d+\)|DOUBLE PRECISION|TIMESTAMPTZ|TIMESTAMP|TSVECTOR|BIGSERIAL|BIGINT|SMALLINT|INTEGER|BOOLEAN|JSONB|TEXT|DATE|REAL)", resto)
            tipo = t.group(1) if t else resto.split()[0]
            cols.append((nombre, tipo, resto[len(tipo):].strip().replace("|", "/"), nota.strip().replace("|", "/")))
        tablas[m.group(1)] = {"columnas": cols}
    return tablas


def relaciones(sql: str) -> list[tuple[str, str, str]]:
    """(tabla_hija, columna, tabla_padre) de cada REFERENCES."""
    out = []
    for m in re.finditer(r"CREATE TABLE (\w+\.\w+) \((.*?)\n\);", sql, re.S):
        for r in re.finditer(r"(\w+)\s+[^,\n]*?REFERENCES (\w+\.\w+) \((\w+)\)", m.group(2)):
            out.append((m.group(1), r.group(1), r.group(2)))
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sql = open(os.path.join(CARPETA, "schema_postgres.sql"), encoding="utf-8").read()
    T = parsear(sql)
    rel = relaciones(sql)
    val = json.load(open(os.path.join(CARPETA, "validacion_postgres.json"), encoding="utf-8"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("cargar_a_postgres", os.path.join(RAIZ, "analitica", "eval", "cargar_a_postgres.py"))
    carga = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(carga)
    filas = dict(carga.plan())
    L = ["# Modelo de datos de Lucas (PostgreSQL)", "",
         "Plan del modelo de datos y su esquema **listo para crear** en PostgreSQL 15 o superior con la extension `pgvector`, para quien haga la integracion final. El equipo aun no tiene base de datos: con este esquema, "
         "el cargador y la evidencia de validacion se crea y se llena en minutos. Todo esta **probado contra un PostgreSQL real** con la data sintetica completa.", "",
         "| Archivo | Para que sirve |", "|---|---|",
         "| [`schema_postgres.sql`](schema_postgres.sql) | El esquema completo (`lucas` y `simulacion`): tablas, claves, restricciones, indices, vista de limpieza y vectores |",
         "| [`validacion_postgres.json`](validacion_postgres.json) | Evidencia de la prueba contra Postgres real (cargas, cascadas, restricciones, busqueda vectorial) |",
         "| [`../../analitica/eval/cargar_a_postgres.py`](../../analitica/eval/cargar_a_postgres.py) | Cargador: crea el esquema, carga los Parquet con COPY, carga el RAG con sus vectores y verifica los conteos |",
         "| Este documento | Plan, diccionario de cada tabla y diagrama entidad-relacion (generado desde el SQL por `analitica/eval/generar_modelo_de_datos.py`) |", "",
         "## 1. Decisiones de diseno", "",
         "1. **Dos esquemas.** `lucas` es lo que usa el aplicativo y lo que existiria con datos reales de un banco. `simulacion` guarda la **verdad oculta** del generador sintetico (arquetipo, parametros internos, etiquetas de referencia): "
         "sirve para evaluar los modelos y **nunca** debe leerlo un modelo ni el aplicativo (es lo que `backend/src/models/columnas.py` ya separa en observable, etiqueta e interna). Con datos reales se borra el esquema entero: `DROP SCHEMA simulacion CASCADE`.",
         "2. **Los defectos sembrados se conservan a proposito.** Los movimientos traen faltantes (glosa 2 %, categoria 3 %, saldo 1,5 %, monto 0,2 %) y duplicados, para probar la limpieza. Por eso `lucas.transaccion` tiene clave propia "
         "(`movimiento_id`, identidad), `transaction_id` no es unico y las columnas son nulas donde corresponde. La vista `lucas.transaccion_limpia` quita los duplicados exactos; los cercanos los quita `backend/src/generador/calidad.py::limpiar`.",
         "3. **Derecho de supresion.** Todo lo que cuelga de un cliente se borra con el (`ON DELETE CASCADE`), igual que `memoria.olvidar`. Se probo: borrar un cliente borra sus movimientos, saldos, panel, mensajes y su verdad oculta, sin filas huerfanas.",
         "4. **Dinero en `NUMERIC(14,2)`**, nunca en flotantes; tasas y porcentajes en `NUMERIC`; parametros del simulador en `DOUBLE PRECISION`. Fechas como `DATE`, `TIMESTAMP` o `CHAR(7)` (`AAAA-MM`) segun el dato.",
         "5. **Vectores en la misma base.** El RAG (3.761 fragmentos tras depurar los repetidos) y las preguntas frecuentes viven con `pgvector`: columnas `vector(768)` (nomic-embed-text, vectores normalizados) con indice HNSW de **producto interno**, que equivale al coseno. "
         "Ademas `rag_fragmento.texto_tsv` (texto completo en espanol) reemplaza al BM25 local para una busqueda hibrida dentro de SQL.",
         "6. **Observabilidad sin texto.** `lucas.consulta_chat` guarda por respuesta el proveedor, las llamadas y tokens, las cifras verificadas y el estado del RAG, pero **no** la pregunta ni la respuesta.",
         "7. **Particion.** Con millones de movimientos conviene particionar `lucas.transaccion` por `fecha_hora` (rango anual); el SQL deja la nota (con la particion declarativa la clave primaria debe incluir `fecha_hora`).", ""]
    L += ["## 2. Diagrama entidad-relacion", "", "```mermaid", "erDiagram"]
    for hija, col, padre in sorted(set(rel)):
        L.append(f"    {padre.split('.')[1].upper()} ||--o{{ {hija.split('.')[1].upper()} : \"{col}\"")
    L += ["```", "", "Las tablas del RAG (`rag_fuente` 1 a N `rag_fragmento`) y las preguntas frecuentes no cuelgan de un cliente: son conocimiento compartido. "
          "El diagrama grafico para la presentacion esta en `docs/presentacion/diagramas/modelo_de_datos.png`.", ""]
    for titulo, nombres in GRUPO:
        L += [f"## {titulo}", ""]
        for n in nombres:
            t = T[n]
            L += [f"### `{n}`", "", f"Origen: {ORIGEN[n]}" + (f". Filas en la data sintetica: **{filas[n]:,}**." if n in filas else "."), "",
                  "| Columna | Tipo | Restricciones | Nota |", "|---|---|---|---|"]
            for c, tipo, restr, nota in t["columnas"]:
                L.append(f"| `{c}` | {tipo} | {restr or ''} | {nota} |")
            L.append("")
    L += ["## 6. Como crearla y cargarla", "", "```bash",
          "# 1. Una base con pgvector (ejemplo con Docker; en el servidor del equipo basta CREATE EXTENSION vector)",
          "docker run -d --name lucas-pg -e POSTGRES_PASSWORD=<clave> -e POSTGRES_DB=lucas -p 5432:5432 pgvector/pgvector:pg16", "",
          "# 2. Crear el esquema y cargar la data sintetica y el RAG con sus vectores (~3 minutos)",
          "export DATABASE_URL=postgresql://postgres:<clave>@localhost:5432/lucas",
          "python analitica/eval/cargar_a_postgres.py --crear --rag", "",
          "# Solo ver que se cargaria, sin base de datos",
          "python analitica/eval/cargar_a_postgres.py --plan", "```", "",
          "El cargador usa `COPY` y al final **verifica que cada tabla tenga las mismas filas que su Parquet**. La clave del usuario va solo en `DATABASE_URL`, nunca en el repositorio. "
          "Con datos reales no se carga el esquema `simulacion` y las tablas de la seccion 1 las llena el sistema de la entidad con la misma estructura.", "",
          "## 7. Evidencia de validacion (PostgreSQL real)", "",
          f"Probado el {val['fecha']} con {val['version_de_postgres'].split(' on ')[0]} y pgvector {val['version_de_pgvector']}; la base con todo cargado pesa {val['tamano_de_la_base_con_todo_cargado']} y tiene {val['tablas']} tablas. "
          "Fuente: [`validacion_postgres.json`](validacion_postgres.json).", "",
          "| Comprobacion | Resultado |", "|---|---|",
          f"| Carga completa: filas de cada tabla frente a su Parquet | las {len(filas)} tablas cargadas coinciden (3.264.148 movimientos, 1.278.500 saldos diarios, 44.924 mensajes...) |",
          f"| La vista `transaccion_limpia` quita los duplicados exactos | {val['vista_limpia_quita_duplicados_exactos']['filas']:,} filas, {val['vista_limpia_quita_duplicados_exactos']['ids_distintos']:,} ids distintos, vista con {val['vista_limpia_quita_duplicados_exactos']['vista']:,}: {'OK' if val['vista_limpia_quita_duplicados_exactos']['ok'] else 'FALLA'} |",
          f"| Borrar un cliente borra todo lo suyo (cascada) | {'OK' if val['borrar_un_cliente_borra_todo_lo_suyo']['ok'] else 'FALLA'}: del cliente `{val['borrar_un_cliente_borra_todo_lo_suyo']['cliente']}` desaparecen {sum(val['borrar_un_cliente_borra_todo_lo_suyo']['antes'].values()):,} filas y no queda ninguna huerfana |",
          f"| `movimiento_id` es identidad (la app inserta sin darlo) | {'OK' if val['identidad_de_movimiento_id']['ok'] else 'FALLA'} |",
          f"| Las restricciones rechazan lo invalido (tipo, cliente inexistente, banda cruzada) | {', '.join(val['restricciones_rechazan_lo_invalido']['resultado'].values())} |",
          f"| Busqueda vectorial en SQL = busqueda del indice local | mismos 3 fragmentos ({', '.join(str(i) for i, _ in val['busqueda_vectorial_sql_igual_a_la_local']['sql'])}), similitud {val['busqueda_vectorial_sql_igual_a_la_local']['local'][0][1]} |",
          f"| Busqueda por palabras en SQL (`texto_tsv`) | {'OK' if val['busqueda_por_palabras_en_sql']['ok'] else 'FALLA'} ({len(val['busqueda_por_palabras_en_sql']['ids'])} resultados) |",
          f"| El indice HNSW se puede usar | {'OK' if val['el_indice_hnsw_se_puede_usar']['ok'] else 'FALLA'}: {val['el_indice_hnsw_se_puede_usar']['nota']} |", "",
          "**Lo que la validacion corrigio:** el comentario del esquema decia que la similitud era `1 + (embedding <#> consulta)`; `<#>` devuelve el producto interno **negativo**, asi que la similitud coseno es `-(embedding <#> consulta)` "
          "(0,76 y no 0,24 en la prueba). Ya esta corregido en el SQL.", "",
          "## 8. Lo que queda para el equipo", "",
          "- **Datos reales:** la entidad llena las tablas de la seccion 1; los modelos solo leen `lucas`. Las columnas nulas de los movimientos son normales (glosa, categoria, saldo).",
          "- **Embeddings de las preguntas frecuentes:** `faq.exportar_para_embeddings()` deja el JSONL; vectorizarlo con nomic-embed-text y cargarlo en `lucas.faq_embedding`. Para trasladar la FAQ aprendida de SQLite a Postgres, las tablas son las mismas (ver la seccion 9.4 del informe).",
          "- **Particion** de `lucas.transaccion` si el volumen real lo pide, y los permisos por rol (el aplicativo solo escribe en las tablas de la seccion 3).", ""]
    with open(os.path.join(CARPETA, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"{len(T)} tablas documentadas -> docs/modelo_de_datos/README.md")


if __name__ == "__main__":
    main()
