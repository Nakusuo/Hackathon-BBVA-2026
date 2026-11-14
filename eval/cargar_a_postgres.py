"""Carga la data sintetica (y, si se pide, el RAG con sus vectores) a PostgreSQL con el esquema de docs/modelo_de_datos/schema_postgres.sql.
Usa COPY (rapido: ~3,3 millones de movimientos en un par de minutos) y al final VERIFICA que cada tabla tenga las mismas filas que su archivo Parquet.
Los vectores del RAG salen del indice FAISS ya hecho: no se vuelve a llamar a Ollama.
Uso:
    python eval/cargar_a_postgres.py --dsn postgresql://usuario:clave@host:5432/lucas --crear          # crea el esquema y carga la data sintetica
    python eval/cargar_a_postgres.py --dsn ... --rag                                                    # ademas, carga el RAG (fuentes, fragmentos y vectores)
    python eval/cargar_a_postgres.py --plan                                                             # solo muestra que se cargaria (no necesita base de datos)
La cadena de conexion tambien puede venir de la variable de entorno DATABASE_URL. Nunca se escribe una clave en el repositorio."""
import argparse
import csv
import glob
import json
import math
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pyarrow.parquet as pq  # noqa: E402

DATOS = os.path.join(RAIZ, "data", "generado")
ESQUEMA_SQL = os.path.join(RAIZ, "docs", "modelo_de_datos", "schema_postgres.sql")
COLUMNAS_CLIENTE = ["customer_id", "rango_edad", "region", "departamento", "tipo_trabajo", "frecuencia_ingreso", "personas_a_cargo", "deuda_total", "n_creditos", "cuota_mensual", "tcea_promedio",
                    "colchon_meses", "antiguedad_cliente_meses", "meta_ahorro", "paga_en_usd"]
COLUMNAS_VERDAD = ["customer_id", "arquetipo", "subtipo", "segmento", "perfil_ahorro_real", "perfil_gasto_real", "necesidad_oculta", "prob_acepta_reco", "cambio_patron", "peso_muestral", "ingreso_base",
                   "gasto_ratio", "ahorro_tasa", "fraccion_efectivo", "traspaso_inflacion", "planilla", "tiene_alquiler", "alquiler_share", "tiene_deuda", "cuota_share", "saldo_inicial", "ahorro_inicial",
                   "acceso_credito_informal", "tasa_credito_informal", "pos_cambio_patron", "factor_cambio_ingreso", "heterogeneidad_consumo", "lote"]
COLUMNAS_TX = ["movimiento_id", "customer_id", "transaction_id", "fecha_hora", "monto", "moneda", "monto_pen", "tipo", "categoria", "comercio", "glosa", "canal", "saldo"]
COLUMNAS_TX_VERDAD = ["movimiento_id", "es_recurrente", "es_atipico", "es_suscripcion_duplicada"]
DINERO = {"monto", "monto_pen", "saldo", "ingresos", "gastos", "saldo_cierre", "ahorro_movido", "gasto_deuda", "gasto_fijo", "gasto_hormiga", "gasto_variable", "ingreso_extraordinario", "ingreso_financiero",
          "ingreso_operativo", "saldo_fin", "saldo_min", "deuda_total", "cuota_mensual", "meta_ahorro"}
FECHA = {"fecha", "inicio", "fin"}


def _valor(v, col):
    """Parquet a un valor de Postgres: NaN y None a NULL, dinero a 2 decimales, fechas sin hora donde la columna es DATE."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if col in DINERO:
        return round(float(v), 2)
    if col in FECHA and hasattr(v, "date"):
        return v.date()
    if col in ("tcea_promedio",):
        return round(float(v), 3)
    if col in ("colchon_meses",):
        return round(float(v), 2)
    return v


def _filas(archivo: str, columnas: list[str], lote: int = 100_000):
    pf = pq.ParquetFile(archivo)
    for b in pf.iter_batches(batch_size=lote, columns=columnas):
        cols = {c: b.column(c).to_pylist() for c in columnas}
        for i in range(b.num_rows):
            yield {c: cols[c][i] for c in columnas}


def _contar(patron: str) -> int:
    return sum(pq.ParquetFile(a).metadata.num_rows for a in glob.glob(patron))


def plan() -> list[tuple[str, int]]:
    return [("lucas.cliente", _contar(os.path.join(DATOS, "clientes.parquet"))), ("simulacion.cliente_verdad", _contar(os.path.join(DATOS, "clientes.parquet"))),
            ("lucas.contexto_diario", _contar(os.path.join(DATOS, "contexto_diario.parquet"))), ("lucas.evento", _contar(os.path.join(DATOS, "eventos.parquet"))),
            ("lucas.macro_mensual", _contar(os.path.join(DATOS, "macro_mensual.parquet"))), ("lucas.saldo_diario", _contar(os.path.join(DATOS, "saldo_diario", "*.parquet"))),
            ("lucas.panel_mensual", _contar(os.path.join(DATOS, "panel_mensual", "*.parquet"))), ("lucas.mensaje", _contar(os.path.join(DATOS, "mensajes", "*.parquet"))),
            ("lucas.transaccion", _contar(os.path.join(DATOS, "transacciones", "*.parquet"))), ("simulacion.transaccion_verdad", _contar(os.path.join(DATOS, "transacciones", "*.parquet"))),
            ("simulacion.calidad_etiqueta", _contar(os.path.join(DATOS, "etiquetas_calidad", "*.parquet")))]


def copiar(con, tabla: str, columnas: list[str], filas) -> int:
    n = 0
    with con.cursor() as cur, cur.copy(f"COPY {tabla} ({', '.join(columnas)}) FROM STDIN") as cp:
        for f in filas:
            cp.write_row([f[c] for c in columnas])
            n += 1
    return n


def cargar_datos(con) -> None:
    t0 = time.time()

    def reportar(tabla, n):
        print(f"  {tabla}: {n:,} filas ({time.time() - t0:.0f} s)", flush=True)

    cl = os.path.join(DATOS, "clientes.parquet")
    reportar("lucas.cliente", copiar(con, "lucas.cliente", COLUMNAS_CLIENTE, ({c: _valor(f[c], c) for c in COLUMNAS_CLIENTE} for f in _filas(cl, COLUMNAS_CLIENTE))))
    reportar("simulacion.cliente_verdad", copiar(con, "simulacion.cliente_verdad", COLUMNAS_VERDAD, ({c: _valor(f[c], c) for c in COLUMNAS_VERDAD} for f in _filas(cl, COLUMNAS_VERDAD))))
    cd = ["fecha", "dia_semana", "dia_mes", "mes", "fuerza_covid_confinamiento", "fuerza_covid_reapertura", "fuerza_covid_segunda_ola", "fuerza_protestas_2022_2023", "fuerza_nino_costero_2023"]
    reportar("lucas.contexto_diario", copiar(con, "lucas.contexto_diario", cd, ({c: _valor(f[c], c) for c in cd} for f in _filas(os.path.join(DATOS, "contexto_diario.parquet"), cd))))
    ev = ["evento_id", "nombre", "tipo", "inicio", "fin", "estado", "fuente"]
    reportar("lucas.evento", copiar(con, "lucas.evento", ev, ({c: (_f(f[c]) if c in FECHA else f[c]) for c in ev} for f in _filas(os.path.join(DATOS, "eventos.parquet"), ev))))
    mm = ["mes", "ipc_var_mensual", "ipc_relativo", "tasa_referencia_bcrp", "tipo_cambio_venta"]
    reportar("lucas.macro_mensual", copiar(con, "lucas.macro_mensual", mm, ({c: _valor(f[c], c) for c in mm} for f in _filas(os.path.join(DATOS, "macro_mensual.parquet"), mm))))
    sd = ["customer_id", "fecha", "ingresos", "gastos", "saldo_cierre", "en_rojo"]
    reportar("lucas.saldo_diario", copiar(con, "lucas.saldo_diario", sd, ({c: _valor(f[c], c) for c in sd} for a in sorted(glob.glob(os.path.join(DATOS, "saldo_diario", "*.parquet"))) for f in _filas(a, sd))))
    pm = ["customer_id", "mes", "ahorro_movido", "gasto_deuda", "gasto_fijo", "gasto_hormiga", "gasto_variable", "ingreso_extraordinario", "ingreso_financiero", "ingreso_operativo", "n_transacciones",
          "saldo_fin", "saldo_min", "dias_en_rojo"]
    reportar("lucas.panel_mensual", copiar(con, "lucas.panel_mensual", pm, ({c: _valor(f[c], c) for c in pm} for a in sorted(glob.glob(os.path.join(DATOS, "panel_mensual", "*.parquet"))) for f in _filas(a, pm))))
    ms = ["customer_id", "fecha_hora", "texto", "sentimiento"]
    reportar("lucas.mensaje", copiar(con, "lucas.mensaje", ms, (f for a in sorted(glob.glob(os.path.join(DATOS, "mensajes", "*.parquet"))) for f in _filas(a, ms))))
    # movimientos y su verdad con el MISMO movimiento_id (la clave la pone este cargador, en orden de archivo)
    leidas = ["customer_id", "transaction_id", "fecha_hora", "monto", "moneda", "monto_pen", "tipo", "categoria", "comercio", "glosa", "canal", "saldo", "es_recurrente", "es_atipico", "es_suscripcion_duplicada"]
    contador = [0]

    def movimientos():
        for a in sorted(glob.glob(os.path.join(DATOS, "transacciones", "*.parquet"))):
            for f in _filas(a, leidas):
                contador[0] += 1
                yield {"movimiento_id": contador[0], **{c: _valor(f[c], c) for c in leidas}}
    flags = bytearray()   # tres banderas por movimiento (3 bytes por fila): su movimiento_id es la posicion + 1

    def solo_lucas():
        for f in movimientos():
            flags.extend((f["es_recurrente"], f["es_atipico"], f["es_suscripcion_duplicada"]))
            yield f
    n = copiar(con, "lucas.transaccion", COLUMNAS_TX, solo_lucas())
    reportar("lucas.transaccion", n)
    with con.cursor() as cur, cur.copy("COPY simulacion.transaccion_verdad (movimiento_id, es_recurrente, es_atipico, es_suscripcion_duplicada) FROM STDIN") as cp:
        for i in range(n):
            cp.write_row([i + 1, bool(flags[3 * i]), bool(flags[3 * i + 1]), bool(flags[3 * i + 2])])
    reportar("simulacion.transaccion_verdad", n)
    cq = ["transaction_id", "tipo_problema"]
    reportar("simulacion.calidad_etiqueta", copiar(con, "simulacion.calidad_etiqueta", cq, (f for a in sorted(glob.glob(os.path.join(DATOS, "etiquetas_calidad", "*.parquet"))) for f in _filas(a, cq))))
    with con.cursor() as cur:   # la secuencia queda despues del ultimo id cargado
        cur.execute("SELECT setval(pg_get_serial_sequence('lucas.transaccion', 'movimiento_id'), (SELECT max(movimiento_id) FROM lucas.transaccion))")   # el proximo id sigue al ultimo cargado
        cur.execute("ANALYZE")
    con.commit()


def _f(v):
    """Las fechas de eventos.parquet vienen como texto AAAA-MM-DD."""
    from datetime import date
    return date.fromisoformat(str(v)[:10]) if v is not None else None


def cargar_rag(con) -> None:
    import faiss
    ix = os.path.join(RAIZ, "docs", "rag", "indice")
    frags = json.load(open(os.path.join(ix, "fragmentos.json"), encoding="utf-8"))
    idx = faiss.read_index(os.path.join(ix, "vectores.faiss"))
    hashes = {r["archivo"]: r for r in csv.DictReader(open(os.path.join(RAIZ, "docs", "rag", "fuentes.csv"), encoding="utf-8")) if r["archivo"]}
    fuentes = {}
    for f in frags:
        if f["documento"] not in fuentes:
            h = hashes.get(f["documento"], {})
            fuentes[f["documento"]] = {"documento": f["documento"], "modulo": f["modulo"], "titulo": f["titulo"], "institucion": f.get("institucion"), "contexto": f.get("contexto"),
                                       "licencia_nivel": f["licencia_nivel"], "enlace": f.get("enlace"), "sha256": h.get("sha256") or None, "fecha_consulta": h.get("fecha_consulta") or None}
    cf = ["documento", "modulo", "titulo", "institucion", "contexto", "licencia_nivel", "enlace", "sha256", "fecha_consulta"]
    copiar(con, "lucas.rag_fuente", cf, fuentes.values())
    with con.cursor() as cur, cur.copy("COPY lucas.rag_fragmento (id, documento, modulo, pagina, texto, embedding) FROM STDIN") as cp:
        for f in frags:
            v = idx.reconstruct(int(f["id"]))
            cp.write_row([f["id"], f["documento"], f["modulo"], f["pagina"], f["texto"], "[" + ",".join(f"{x:.7f}" for x in v) + "]"])
    con.commit()
    print(f"  RAG: {len(fuentes)} fuentes y {len(frags)} fragmentos con su vector de {idx.d} dimensiones")


def verificar(con) -> bool:
    ok = True
    print("Verificacion (filas en la base frente a filas del Parquet):")
    for tabla, esperado in plan():
        with con.cursor() as cur:
            cur.execute(f"SELECT count(*) FROM {tabla}")
            n = cur.fetchone()[0]
        marca = "OK " if n == esperado else "MAL"
        ok &= n == esperado
        print(f"  [{marca}] {tabla}: {n:,} (Parquet {esperado:,})")
    return ok


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", default=os.environ.get("DATABASE_URL"))
    ap.add_argument("--crear", action="store_true", help="ejecuta docs/modelo_de_datos/schema_postgres.sql antes de cargar")
    ap.add_argument("--rag", action="store_true", help="carga tambien las fuentes, los fragmentos y los vectores del RAG")
    ap.add_argument("--plan", action="store_true", help="solo muestra que se cargaria")
    ap.add_argument("--solo-rag", action="store_true", help="vuelve a cargar solo el RAG (por ejemplo tras depurar o reindexar): vacia sus tablas y las llena de nuevo")
    a = ap.parse_args()
    if a.plan:
        for t, n in plan():
            print(f"{t}: {n:,} filas")
        return 0
    if not a.dsn:
        print("falta --dsn o la variable DATABASE_URL")
        return 2
    import psycopg
    with psycopg.connect(a.dsn, autocommit=False) as con:
        if a.crear:
            with con.cursor() as cur:
                cur.execute(open(ESQUEMA_SQL, encoding="utf-8").read())
            con.commit()
            print("esquema creado")
        if a.solo_rag:
            with con.cursor() as cur:
                cur.execute("TRUNCATE lucas.rag_fragmento, lucas.rag_fuente CASCADE")
            cargar_rag(con)
            with con.cursor() as cur:
                cur.execute("SELECT count(*) FROM lucas.rag_fragmento")
                n = cur.fetchone()[0]
            esperado = len(json.load(open(os.path.join(RAIZ, "docs", "rag", "indice", "fragmentos.json"), encoding="utf-8")))
            print(f"  [{'OK ' if n == esperado else 'MAL'}] lucas.rag_fragmento: {n:,} (indice {esperado:,})")
            return 0 if n == esperado else 1
        cargar_datos(con)
        if a.rag:
            cargar_rag(con)
        return 0 if verificar(con) else 1


if __name__ == "__main__":
    sys.exit(main())
