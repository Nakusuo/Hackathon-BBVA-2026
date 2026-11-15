"""RAG por modulos: lectura de PDF y texto, particion en fragmentos, embeddings locales (Ollama) e indice FAISS con busqueda hibrida.
Uso: python -m src.rag.indice   (reconstruye docs/rag/indice)"""
import csv
import json
import os
import re
import time

import faiss
import numpy as np
import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from rank_bm25 import BM25Okapi

from src.comun.rutas import DOCS_RAG, INDICE_RAG, cargar_env

TAM_FRAGMENTO, SOLAPE = 900, 120


def _leer_documento(ruta: str) -> list[tuple[int, str]]:
    """Devuelve [(pagina, texto)]. Los .txt cuentan como una sola pagina."""
    if ruta.endswith(".pdf"):
        r = PdfReader(ruta)
        return [(i + 1, re.sub(r"\s+", " ", (p.extract_text() or ""))) for i, p in enumerate(r.pages)]
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()
    if "Posted at" in texto and "COMUNICADO OFICIAL" in texto:  # pagina web del ENFEN: nos quedamos con el cuerpo del comunicado
        texto = texto[texto.index("COMUNICADO OFICIAL"):]
    return [(1, re.sub(r"\s+", " ", texto))]


def _metadatos_fuentes() -> dict:
    meta = {}
    ruta = os.path.join(DOCS_RAG, "fuentes.csv")
    with open(ruta, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["archivo"]:
                meta[r["archivo"]] = r
    return meta


# Pie de pagina de un sitio web que el PDF trae en cada hoja: no es contenido y repetido 27 veces ocupa espacio y tokens del prompt.
BOILERPLATE = ("Need help \ufb01nding a job", "Need help finding a job")


def depurar(frags: list[dict]) -> tuple[list[dict], list[int]]:
    """Quita los fragmentos repetidos (mismo texto: avisos legales que el PDF repite en cada capitulo) y el pie de pagina de sitio web. Devuelve (fragmentos con ids nuevos 0..n-1, ids originales conservados)."""
    vistos, nuevos, conservados = set(), [], []
    for f in frags:
        t = f["texto"]
        if t in vistos or any(b in t for b in BOILERPLATE):
            continue
        vistos.add(t)
        conservados.append(int(f["id"]))
        nuevos.append({**f, "id": len(nuevos)})
    return nuevos, conservados


def depurar_indice(verbose: bool = True) -> dict:
    """Aplica depurar() al indice ya hecho SIN volver a embeber: los vectores de los fragmentos que se conservan se reutilizan. Es idempotente."""
    with open(os.path.join(INDICE_RAG, "fragmentos.json"), encoding="utf-8") as f:
        frags = json.load(f)
    idx = faiss.read_index(os.path.join(INDICE_RAG, "vectores.faiss"))
    nuevos, conservados = depurar(frags)
    quitados = len(frags) - len(nuevos)
    if quitados:
        v = np.vstack([idx.reconstruct(i) for i in conservados]).astype(np.float32)
        nuevo = faiss.IndexFlatIP(v.shape[1])
        nuevo.add(v)
        faiss.write_index(nuevo, os.path.join(INDICE_RAG, "vectores.faiss"))
        with open(os.path.join(INDICE_RAG, "fragmentos.json"), "w", encoding="utf-8") as f:
            json.dump(nuevos, f, ensure_ascii=False)
        info = json.load(open(os.path.join(INDICE_RAG, "info.json"), encoding="utf-8"))
        info["fragmentos"] = len(nuevos)
        info["depurado"] = {"quitados": quitados, "antes": len(frags), "motivo": "textos repetidos exactos y pie de pagina de sitio web"}
        json.dump(info, open(os.path.join(INDICE_RAG, "info.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    if verbose:
        print(f"{quitados} fragmentos quitados (repetidos o pie de pagina); quedan {len(nuevos)}")
    return {"quitados": quitados, "quedan": len(nuevos)}


def construir_fragmentos() -> list[dict]:
    meta = _metadatos_fuentes()
    corte = RecursiveCharacterTextSplitter(chunk_size=TAM_FRAGMENTO, chunk_overlap=SOLAPE, separators=["\n\n", ". ", " "])
    frags = []
    for modulo in sorted(os.listdir(DOCS_RAG)):
        carpeta = os.path.join(DOCS_RAG, modulo)
        if not os.path.isdir(carpeta) or modulo == "indice":
            continue
        for nombre in sorted(os.listdir(carpeta)):
            if not nombre.endswith((".pdf", ".txt")):
                continue
            clave = f"{modulo}/{nombre}"
            m = meta.get(clave, {})
            if m.get("licencia_nivel", "A") == "C":
                continue
            if clave not in meta and not nombre.startswith("enfen_"):
                continue
            titulo = m.get("titulo") or f"Comunicado Oficial ENFEN {re.search(r'_(\d+)_2026', nombre).group(1)}-2026"
            for pag, texto in _leer_documento(os.path.join(carpeta, nombre)):
                for k, t in enumerate(corte.split_text(texto)):
                    if len(t) < 80:
                        continue
                    frags.append({"id": len(frags), "modulo": modulo, "documento": clave, "titulo": titulo, "institucion": m.get("institucion", "ENFEN"), "pagina": pag,
                                  "contexto": m.get("contexto", "Peru"), "licencia_nivel": m.get("licencia_nivel", "A"), "enlace": m.get("enlace", ""), "texto": t})
    return depurar(frags)[0]


def embeber(textos: list[str], tipo: str = "document", lote: int = 24) -> np.ndarray:
    """Embeddings locales con nomic-embed-text (Ollama). Nunca se manda texto a un servicio externo."""
    cargar_env()
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    modelo = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    vecs = []
    for i in range(0, len(textos), lote):
        entrada = [f"search_{tipo}: {t}" for t in textos[i:i + lote]]
        r = requests.post(f"{host}/api/embed", json={"model": modelo, "input": entrada}, timeout=300)
        r.raise_for_status()
        vecs.extend(r.json()["embeddings"])
    v = np.array(vecs, dtype=np.float32)
    faiss.normalize_L2(v)
    return v


def construir_indice(verbose: bool = True) -> dict:
    t0 = time.time()
    frags = construir_fragmentos()
    if verbose:
        print(f"{len(frags)} fragmentos de {len({f['documento'] for f in frags})} documentos")
    v = embeber([f["texto"] for f in frags])
    idx = faiss.IndexFlatIP(v.shape[1])
    idx.add(v)
    os.makedirs(INDICE_RAG, exist_ok=True)
    faiss.write_index(idx, os.path.join(INDICE_RAG, "vectores.faiss"))
    with open(os.path.join(INDICE_RAG, "fragmentos.json"), "w", encoding="utf-8") as f:
        json.dump(frags, f, ensure_ascii=False)
    info = {"fragmentos": len(frags), "dimension": int(v.shape[1]), "modulos": sorted({f["modulo"] for f in frags}), "segundos": round(time.time() - t0, 1),
            "modelo_embeddings": os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text"), "tam_fragmento": TAM_FRAGMENTO, "solape": SOLAPE}
    with open(os.path.join(INDICE_RAG, "info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    return info


def actualizar_incremental(verbose: bool = True) -> dict:
    """Agrega al indice solo los documentos de docs/rag que todavia no estan (sin volver a calcular los embeddings de los demas)."""
    with open(os.path.join(INDICE_RAG, "fragmentos.json"), encoding="utf-8") as f:
        frags = json.load(f)
    idx = faiss.read_index(os.path.join(INDICE_RAG, "vectores.faiss"))
    conocidos = {x["documento"] for x in frags}
    textos = {x["texto"] for x in frags}   # un fragmento ya presente (aviso legal repetido en otro documento) no se agrega dos veces
    nuevos = [x for x in construir_fragmentos() if x["documento"] not in conocidos and x["texto"] not in textos]
    if nuevos:
        v = embeber([x["texto"] for x in nuevos])
        for i, x in enumerate(nuevos):
            x["id"] = len(frags) + i
        idx.add(v)
        frags += nuevos
        faiss.write_index(idx, os.path.join(INDICE_RAG, "vectores.faiss"))
        with open(os.path.join(INDICE_RAG, "fragmentos.json"), "w", encoding="utf-8") as f:
            json.dump(frags, f, ensure_ascii=False)
        info = json.load(open(os.path.join(INDICE_RAG, "info.json"), encoding="utf-8"))
        info["fragmentos"] = len(frags)
        json.dump(info, open(os.path.join(INDICE_RAG, "info.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    if verbose:
        print(f"{len(nuevos)} fragmentos nuevos de {len({x['documento'] for x in nuevos})} documentos; total {len(frags)}")
    return {"nuevos": len(nuevos), "total": len(frags)}


# Siglas del dominio: el modelo de embeddings casi no sabe que significan ("TCEA" sola rinde menos que "tasa de costo efectivo anual"). Se agrega la forma larga a la consulta.
ACRONIMOS = {"TCEA": "tasa de costo efectivo anual", "TEA": "tasa efectiva anual", "TREA": "tasa de rendimiento efectivo anual", "CTS": "compensacion por tiempo de servicios",
             "AFP": "administradora de fondos de pensiones", "ONP": "oficina de normalizacion previsional", "EPS": "entidad prestadora de salud", "SBS": "Superintendencia de Banca, Seguros y AFP",
             "SMV": "Superintendencia del Mercado de Valores", "BCRP": "Banco Central de Reserva del Peru", "ENFEN": "estudio nacional del fenomeno El Nino", "UIT": "unidad impositiva tributaria"}
_SIGLAS = re.compile(r"\b(" + "|".join(ACRONIMOS) + r")\b", re.I)


def expandir_siglas(consulta: str) -> str:
    """'que es la TCEA' -> 'que es la TCEA (tasa de costo efectivo anual)'. Cada sigla se expande una sola vez."""
    vistas: set[str] = set()

    def reemplazo(m):
        s = m.group(1).upper()
        if s in vistas:
            return m.group(0)
        vistas.add(s)
        return f"{m.group(0)} ({ACRONIMOS[s]})"
    return _SIGLAS.sub(reemplazo, consulta)


_PARTES = re.compile(r"\s+y\s+(?=(?:qu[eé]|cu[aá]l(?:es)?|c[oó]mo|cu[aá]ndo|cu[aá]nto|d[oó]nde|puedo|tengo|debo|me|si)\b)", re.I)


def descomponer(pregunta: str) -> list[str]:
    """Una pregunta compuesta ('que es la TCEA y que derechos tengo si me atraso') se parte en subpreguntas. La original va primero.
    Si no hay mas de una parte, devuelve solo la original."""
    piezas = []
    for trozo in re.split(r"[?¿]+", pregunta):
        for p in _PARTES.split(trozo):
            p = p.strip(" ,;.")
            if len(p.split()) >= 3:
                piezas.append(p)
    return [pregunta] + piezas if len(piezas) > 1 else [pregunta]


class Buscador:
    """Busqueda hibrida: vectores (FAISS) + palabras (BM25) fusionados con RRF, con filtro por modulo.
    Opcionales: multiconsulta (descompone preguntas compuestas y fusiona las listas de cada parte) y MMR (evita fragmentos casi repetidos)."""

    def __init__(self):
        self.idx = faiss.read_index(os.path.join(INDICE_RAG, "vectores.faiss"))
        with open(os.path.join(INDICE_RAG, "fragmentos.json"), encoding="utf-8") as f:
            self.frags = json.load(f)
        self.bm25 = BM25Okapi([self._tok(f["texto"]) for f in self.frags])
        self.modulos = np.array([f["modulo"] for f in self.frags])
        self._qcache: dict[str, np.ndarray] = {}   # la misma pregunta no se vuelve a embeber

    @staticmethod
    def _tok(t: str) -> list[str]:
        return re.findall(r"\w+", t.lower())

    def _vectores_consulta(self, consultas: list[str]) -> np.ndarray:
        faltan = [c for c in dict.fromkeys(consultas) if c not in self._qcache]
        if faltan:
            for c, v in zip(faltan, embeber(faltan, "query")):
                self._qcache[c] = v
        return np.stack([self._qcache[c] for c in consultas])

    def buscar(self, pregunta: str, k: int = 4, modulo: str | list | None = None, modo: str = "hibrido", multiconsulta: bool = False, mmr: float | None = None) -> list[dict]:
        """modo: 'denso' (vectores), 'bm25' (palabras) o 'hibrido' (fusion RRF). Cada resultado trae su similitud coseno (la mayor entre las subpreguntas) para el filtro de relevancia.
        mmr: peso de la relevancia frente a la diversidad (0 a 1); None lo desactiva."""
        mods = [modulo] if isinstance(modulo, str) else modulo
        permitido = np.ones(len(self.frags), bool) if not mods else np.isin(self.modulos, mods)
        consultas = descomponer(pregunta) if multiconsulta else [pregunta]
        consultas = [expandir_siglas(c) for c in consultas]
        Q = self._vectores_consulta(consultas)
        rrf: dict[int, float] = {}
        for qi, texto in enumerate(consultas):
            _, ix = self.idx.search(Q[qi:qi + 1], min(80, len(self.frags)))
            denso = [int(i) for i in ix[0] if i >= 0 and permitido[i]]
            s_bm = np.where(permitido, self.bm25.get_scores(self._tok(texto)), -1)
            palabras = [int(i) for i in np.argsort(-s_bm)[:80] if permitido[i]]
            for lista in ({"denso": [denso], "bm25": [palabras]}.get(modo, [denso, palabras])):
                for r, i in enumerate(lista):
                    rrf[i] = rrf.get(i, 0.0) + 1.0 / (60 + r)
        orden = sorted(rrf, key=rrf.get, reverse=True)
        if mmr is not None and len(orden) > k:
            pool = orden[:max(5 * k, 20)]
            V = np.stack([self.idx.reconstruct(i) for i in pool])
            tope = max(rrf[i] for i in pool)
            rel = np.array([rrf[i] / tope for i in pool])
            elegidos: list[int] = []
            while len(elegidos) < min(k, len(pool)):
                mejor = max((j for j in range(len(pool)) if j not in elegidos), key=lambda j: mmr * rel[j] - (1 - mmr) * max((float(V[j] @ V[e]) for e in elegidos), default=0.0))
                elegidos.append(mejor)
            orden = [pool[j] for j in elegidos]
        sal = []
        for i in orden[:k]:
            sim = float((Q @ self.idx.reconstruct(int(i))).max())
            sal.append({**{k_: v for k_, v in self.frags[i].items() if k_ != "id"}, "fragmento_id": i, "similitud": round(sim, 4)})
        return sal


if __name__ == "__main__":
    print(depurar_indice() if "--depurar" in __import__("sys").argv else construir_indice())
