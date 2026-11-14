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
    return frags


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
    nuevos = [x for x in construir_fragmentos() if x["documento"] not in conocidos]
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


class Buscador:
    """Busqueda hibrida: vectores (FAISS) + palabras (BM25) fusionados con RRF, con filtro por modulo."""

    def __init__(self):
        self.idx = faiss.read_index(os.path.join(INDICE_RAG, "vectores.faiss"))
        with open(os.path.join(INDICE_RAG, "fragmentos.json"), encoding="utf-8") as f:
            self.frags = json.load(f)
        self.bm25 = BM25Okapi([self._tok(f["texto"]) for f in self.frags])
        self.modulos = np.array([f["modulo"] for f in self.frags])

    @staticmethod
    def _tok(t: str) -> list[str]:
        return re.findall(r"\w+", t.lower())

    def buscar(self, pregunta: str, k: int = 4, modulo: str | list | None = None, modo: str = "hibrido") -> list[dict]:
        """modo: 'denso' (vectores), 'bm25' (palabras) o 'hibrido' (fusion RRF). Cada resultado trae su similitud coseno para el filtro de relevancia."""
        mods = [modulo] if isinstance(modulo, str) else modulo
        permitido = np.ones(len(self.frags), bool) if not mods else np.isin(self.modulos, mods)
        q = embeber([pregunta], "query")
        sc, ix = self.idx.search(q, min(80, len(self.frags)))
        rango_denso = {int(i): r for r, i in enumerate(ix[0]) if permitido[i]}
        s_bm = np.where(permitido, self.bm25.get_scores(self._tok(pregunta)), -1)
        rango_bm = {int(i): r for r, i in enumerate(np.argsort(-s_bm)[:80]) if permitido[i]}
        if modo == "denso":
            orden = list(rango_denso)
        elif modo == "bm25":
            orden = list(rango_bm)
        else:
            rrf = {}
            for rangos in (rango_denso, rango_bm):
                for i, r in rangos.items():
                    rrf[i] = rrf.get(i, 0.0) + 1.0 / (60 + r)
            orden = sorted(rrf, key=rrf.get, reverse=True)
        sal = []
        for i in orden[:k]:
            sim = float(q[0] @ self.idx.reconstruct(int(i)))
            sal.append({**{k_: v for k_, v in self.frags[i].items() if k_ != "id"}, "fragmento_id": i, "similitud": round(sim, 4)})
        return sal


if __name__ == "__main__":
    print(construir_indice())
