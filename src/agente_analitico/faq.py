"""Preguntas frecuentes: respuestas verificadas que se reutilizan SIN llamar al LLM (cero tokens), y lo que el agente aprende de lo que se le pregunta, guardado en una base de datos.

Dos fuentes, en este orden:
1. La semilla `data/faq/faq_semilla.json` (versionada): preguntas de concepto con su respuesta armada por plantilla desde las fuentes oficiales del RAG, con sus citas. La genera `eval/generar_faq.py`.
2. Lo aprendido, en SQLite (`faq.db`): cuando el LLM contesta una pregunta de concepto y el verificador la aprueba, la respuesta se guarda y la siguiente persona del mismo nivel que pregunte lo mismo la
   recibe sin gastar tokens. El esquema es estandar (tablas `faq_aprendida`, `faq_preguntas_vistas`, `faq_contadores`) y pasa tal cual a Postgres, junto a pgvector del equipo.

Solo se reutilizan respuestas que NO dependen de la persona: pregunta de concepto (intencion «educacion») con evidencia correcta del RAG, sin cifras propias (todo numero de la respuesta sale de las fuentes
citadas), sin el departamento ni el id del cliente. De la pregunta solo se guardan palabras que existen en el corpus del RAG (un nombre propio escrito en la pregunta nunca llega a la base), sin digitos.
Una respuesta guardada deja de usarse si el indice del RAG cambia (se vuelve a aprender con las fuentes nuevas).

Para mejorar con embeddings: `exportar_para_embeddings()` deja las preguntas y respuestas aprendidas en JSONL, listas para vectorizar con el mismo modelo del RAG (nomic-embed-text) y agregarlas al indice
como un modulo «faq» o usarlas para encontrar preguntas parecidas por significado y no solo por palabras."""
import hashlib
import json
import os
import re
import sqlite3
import unicodedata
from contextlib import closing

from src.comun import reloj
from src.comun.rutas import ruta

INTENCIONES = ("educacion",)   # solo preguntas de concepto: no dependen de los datos de la persona
UMBRAL_PARECIDO = 0.8          # similitud de Jaccard entre las palabras de dos preguntas para considerarlas la misma
MAX_APRENDIDAS = 500           # tope de la tabla: las menos preguntadas se descartan primero
VACIAS = {"que", "como", "cual", "cuales", "cuando", "donde", "quien", "para", "por", "con", "sin", "los", "las", "una", "uno", "unos", "unas", "del", "mis", "tus", "sus", "mas", "muy", "hay", "ser", "esta",
          "este", "esto", "eso", "puedo", "puede", "tengo", "tiene", "debo", "hago", "hacer", "algo", "sobre", "segun", "favor", "podrias", "quiero", "saber", "explicame", "dime", "necesito", "entre", "desde", "hasta"}
SEMILLA = ruta("data", "faq", "faq_semilla.json")
ESQUEMA = """
CREATE TABLE IF NOT EXISTS faq_aprendida (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabras TEXT NOT NULL,            -- palabras significativas de la pregunta (solo del corpus del RAG), ordenadas
    nivel TEXT NOT NULL,               -- nivel de la persona (el tono cambia por nivel)
    respuesta TEXT NOT NULL,           -- respuesta verificada, sin datos de la persona
    fragmentos TEXT NOT NULL,          -- JSON: las fuentes citadas (titulo, pagina, enlace, licencia, texto)
    huella_indice TEXT NOT NULL,       -- indice del RAG con el que se armo
    veces INTEGER NOT NULL DEFAULT 1,  -- cuantas veces se pregunto o se reutilizo
    aprendida_el TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS faq_preguntas_vistas (
    palabras TEXT NOT NULL, intencion TEXT NOT NULL, veces INTEGER NOT NULL DEFAULT 1, PRIMARY KEY (palabras, intencion)
);
CREATE TABLE IF NOT EXISTS faq_contadores (nombre TEXT PRIMARY KEY, valor INTEGER NOT NULL DEFAULT 0);
"""
_VOCABULARIO = None
_HUELLA_INDICE = None


def _carpeta() -> str:
    return os.environ.get("LUCAS_FAQ_DIR") or ruta("data", "generado", "faq")


def _bd():
    """Conexion a la base de datos de preguntas frecuentes (se crea con su esquema si no existe)."""
    os.makedirs(_carpeta(), exist_ok=True)
    con = sqlite3.connect(os.path.join(_carpeta(), "faq.db"), timeout=10)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    return con


def _sumar(con, nombre: str, n: int = 1) -> None:
    con.execute("INSERT INTO faq_contadores (nombre, valor) VALUES (?, ?) ON CONFLICT(nombre) DO UPDATE SET valor = valor + ?", (nombre, n, n))


def _sin_tildes(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def _vocabulario() -> set:
    """Palabras que aparecen en el corpus del RAG: lo unico que puede quedar guardado de una pregunta."""
    global _VOCABULARIO
    if _VOCABULARIO is None:
        try:
            with open(ruta("docs", "rag", "indice", "fragmentos.json"), encoding="utf-8") as f:
                _VOCABULARIO = {w for r in json.load(f) for w in re.findall(r"[a-z]{3,}", _sin_tildes(r["texto"]))}
        except (OSError, ValueError):
            _VOCABULARIO = set()
    return _VOCABULARIO


def huella_indice() -> str:
    """Identifica el indice del RAG con el que se armo una respuesta: si cambia, la respuesta guardada deja de usarse."""
    global _HUELLA_INDICE
    if _HUELLA_INDICE is None:
        try:
            with open(ruta("docs", "rag", "indice", "fragmentos.json"), "rb") as f:
                _HUELLA_INDICE = hashlib.sha256(f.read()).hexdigest()[:16]
        except OSError:
            _HUELLA_INDICE = "sin_indice"
    return _HUELLA_INDICE


def normalizar(pregunta: str, solo_corpus: bool = False) -> frozenset:
    """Palabras significativas de la pregunta: sin tildes, sin digitos, sin palabras vacias. Con solo_corpus se quedan solo las que existen en el corpus del RAG."""
    pal = {w for w in re.findall(r"[a-z]{3,}", _sin_tildes(pregunta)) if w not in VACIAS}
    if solo_corpus:
        v = _vocabulario()
        pal = {w for w in pal if w in v}
    return frozenset(pal)


def _parecido(a: frozenset, b: frozenset) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _semilla() -> list:
    try:
        with open(SEMILLA, encoding="utf-8") as f:
            return json.load(f).get("entradas", [])
    except (OSError, ValueError):
        return []


def buscar(pregunta: str, nivel: str, cuenta: bool = True) -> dict | None:
    """Respuesta guardada para esta pregunta (misma pregunta o muy parecida) y este nivel, o None. Devuelve {'respuesta', 'fragmentos', 'origen', 'similitud'}."""
    p = normalizar(pregunta)
    if not p:
        return None
    mejor, sim_mejor = None, 0.0
    with closing(_bd()) as con:
        for f in con.execute("SELECT * FROM faq_aprendida WHERE nivel = ? AND huella_indice = ?", (nivel, huella_indice())):
            s = _parecido(p, frozenset(f["palabras"].split()))
            if s >= UMBRAL_PARECIDO and s > sim_mejor:
                mejor, sim_mejor = ("aprendida", f), s
        if mejor is None:
            for e in _semilla():
                if e.get("huella_indice") == huella_indice():
                    s = _parecido(p, frozenset(e["palabras"]))
                    if s >= UMBRAL_PARECIDO and s > sim_mejor:
                        mejor, sim_mejor = ("semilla", e), s
        if mejor is None:
            return None
        origen, e = mejor
        if cuenta:
            _sumar(con, "respondidas_sin_llm")
            if origen == "aprendida":
                con.execute("UPDATE faq_aprendida SET veces = veces + 1 WHERE id = ?", (e["id"],))
            con.commit()
        frag = json.loads(e["fragmentos"]) if origen == "aprendida" else e["fragmentos"]
        return {"respuesta": e["respuesta"], "fragmentos": frag, "origen": origen, "similitud": round(sim_mejor, 2)}


def _numeros(texto: str) -> set:
    return {n.replace(",", "") for n in re.findall(r"\d[\d.,]*", texto)}


def _es_reutilizable(est: dict, respuesta: str) -> bool:
    """La respuesta no puede depender de la persona: nada de cifras que no vengan de las fuentes citadas, ni su departamento ni su id."""
    fuentes = " ".join(r["texto"] + " " + str(r.get("titulo", "")) + " " + str(r["pagina"]) for r in est["rag"])
    if _numeros(respuesta) - _numeros(fuentes):
        return False
    ctx = est["ctx"]
    return str(ctx["departamento"]).lower() not in respuesta.lower() and est["customer_id"] not in respuesta


def registrar(est: dict, respuesta: str) -> str:
    """Se llama al terminar una respuesta. Cuenta la consulta y, si corresponde, aprende. Devuelve que paso: 'aprendida', 'ya_estaba', 'no_aplica' o 'no_reutilizable'. Nunca rompe la respuesta."""
    if est.get("intencion") not in INTENCIONES:
        return "no_aplica"
    try:
        palabras = normalizar(est.get("pregunta", ""), solo_corpus=True)
        with closing(_bd()) as con:
            _sumar(con, "consultas_de_concepto")
            if est.get("rag_estado") != "correcto" or not est.get("rag"):
                _sumar(con, "sin_evidencia_en_las_fuentes")   # lo que las fuentes no responden: senal para agregar documentos
                con.commit()
                return "no_aplica"
            if palabras and not re.search(r"\d", est.get("pregunta", "")):
                con.execute("INSERT INTO faq_preguntas_vistas (palabras, intencion, veces) VALUES (?, ?, 1) ON CONFLICT(palabras, intencion) DO UPDATE SET veces = veces + 1",
                            (" ".join(sorted(palabras)), est["intencion"]))
            proveedor = est.get("proveedor")
            if proveedor in ("plantilla", "faq", None):
                con.commit()
                return "no_aplica"
            if not palabras or re.search(r"\d", est.get("pregunta", "")) or not est.get("veredicto", {}).get("ok", False):
                con.commit()
                return "no_reutilizable"
            nivel = est["ctx"]["nivel"]
            for f in con.execute("SELECT palabras FROM faq_aprendida WHERE nivel = ? AND huella_indice = ?", (nivel, huella_indice())):
                if _parecido(palabras, frozenset(f["palabras"].split())) >= UMBRAL_PARECIDO:
                    con.commit()
                    return "ya_estaba"
            if not _es_reutilizable(est, respuesta):
                con.commit()
                return "no_reutilizable"
            frag = [{k: r[k] for k in ("documento", "titulo", "pagina", "enlace", "licencia_nivel", "texto") if k in r} | {"similitud": r.get("similitud", 1.0)} for r in est["rag"]]
            con.execute("INSERT INTO faq_aprendida (palabras, nivel, respuesta, fragmentos, huella_indice, veces, aprendida_el) VALUES (?, ?, ?, ?, ?, 1, ?)",
                        (" ".join(sorted(palabras)), nivel, respuesta, json.dumps(frag, ensure_ascii=False), huella_indice(), str(reloj.hoy())))
            con.execute("DELETE FROM faq_aprendida WHERE id NOT IN (SELECT id FROM faq_aprendida ORDER BY veces DESC, id DESC LIMIT ?)", (MAX_APRENDIDAS,))
            con.commit()
            return "aprendida"
    except Exception:  # noqa: BLE001 - aprender es un extra: un fallo aqui jamas debe afectar la respuesta
        return "no_aplica"


def frecuentes(n: int = 10) -> list:
    """Preguntas de concepto mas hechas (las que mas tokens ahorran), para una pantalla de preguntas frecuentes o para decidir que fuentes agregar. Completa con las de la semilla."""
    with closing(_bd()) as con:
        guardadas = {f["palabras"] for f in con.execute("SELECT palabras FROM faq_aprendida")}
        out = [{"pregunta_normalizada": f["palabras"], "veces": f["veces"], "intencion": f["intencion"], "respuesta_guardada": f["palabras"] in guardadas, "origen": "aprendida"}
               for f in con.execute("SELECT palabras, intencion, veces FROM faq_preguntas_vistas ORDER BY veces DESC, palabras LIMIT ?", (n,))]
    out += [{"pregunta": e["pregunta"], "origen": "semilla", "fuente": e["fragmentos"][0]["titulo"]} for e in _semilla()[: max(n - len(out), 0)]]
    return out[:n]


def estadisticas() -> dict:
    with closing(_bd()) as con:
        c = {r["nombre"]: r["valor"] for r in con.execute("SELECT nombre, valor FROM faq_contadores")}
        aprendidas = con.execute("SELECT COUNT(*) FROM faq_aprendida").fetchone()[0]
    c = {"consultas_de_concepto": 0, "respondidas_sin_llm": 0, "sin_evidencia_en_las_fuentes": 0} | c
    return {**c, "preguntas_aprendidas": aprendidas, "preguntas_de_la_semilla": len(_semilla()),
            "fraccion_sin_llm": (c["respondidas_sin_llm"] / c["consultas_de_concepto"]) if c["consultas_de_concepto"] else None}


def exportar_para_embeddings(destino: str | None = None) -> str:
    """Deja en JSONL (una linea por pregunta) lo aprendido y la semilla, listo para vectorizar con el mismo modelo del RAG (nomic-embed-text) y agregarlo al indice como modulo «faq»
    o para buscar preguntas parecidas por significado. Cada linea: id, pregunta (palabras normalizadas o la original de la semilla), respuesta, fuentes y nivel."""
    destino = destino or os.path.join(_carpeta(), "faq_para_embeddings.jsonl")
    filas = [{"id": f"semilla-{i}", "pregunta": e["pregunta"], "respuesta": e["respuesta"], "fuentes": [{"titulo": x["titulo"], "pagina": x["pagina"], "enlace": x.get("enlace", "")} for x in e["fragmentos"][:1]],
              "nivel": None, "veces": None, "huella_indice": e.get("huella_indice")} for i, e in enumerate(_semilla())]
    with closing(_bd()) as con:
        for f in con.execute("SELECT * FROM faq_aprendida ORDER BY veces DESC, id"):
            filas.append({"id": f"aprendida-{f['id']}", "pregunta": f["palabras"], "respuesta": f["respuesta"], "fuentes": [{"titulo": x["titulo"], "pagina": x["pagina"], "enlace": x.get("enlace", "")}
                                                                                                                     for x in json.loads(f["fragmentos"])[:1]],
                          "nivel": f["nivel"], "veces": f["veces"], "huella_indice": f["huella_indice"]})
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        for r in filas:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return destino
