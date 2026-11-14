"""Descarga fuentes oficiales abiertas (PDF para el RAG, informes de calibracion y series del BCRP).

Cada archivo queda con su hash y su estado en un CSV. Lo que falla se registra, no se oculta.
Uso: python -m src.datos_publicos.descargar
"""
import csv
import hashlib
import html as html_lib
import json
import os
import re
import shutil
import sys
from datetime import date

import requests

from src.comun.rutas import DATA_RAW, DOCS_FUENTES, DOCS_RAG

CABECERAS = {"User-Agent": "analitica-hackathon/1.0"}
MAX_MB = 40
HOY = date.today().isoformat()

# modulo, archivo, titulo, institucion, url, nivel_licencia, contexto, nivel_lectura
RAG = [
    ("deudas", "sbs_res_3274_2017_conducta_mercado.pdf", "Reglamento de Gestion de Conducta de Mercado (Res. SBS 3274-2017)", "SBS",
     "https://www.bn.com.pe/transparenciabn/transparencia-financiera/Res-SBS-3274-2017-Reglamento-Gestion-Conducta-Mercado.pdf", "A", "Peru", "intermedio"),
    ("derechos", "ds_016_2024_jus_reglamento_ley_29733.pdf", "Reglamento de la Ley 29733 (DS 016-2024-JUS)", "Congreso / ANPD",
     "https://cdn.www.gob.pe/uploads/document/file/7756037/6554453-reglamento-de-la-ley-n-29733.pdf", "A", "Peru", "intermedio"),
    ("salud_financiera", "cfpb_su_dinero_sus_metas_kit.pdf", "Su dinero, sus metas: kit de herramientas", "CFPB",
     "https://files.consumerfinance.gov/f/201603_cfpb_your-money-your-goals_toolkit_spanish.pdf", "A", "EE. UU.", "basico"),
    ("deudas", "cfpb_folleto_credito.pdf", "Folleto de credito (Su dinero, sus metas)", "CFPB",
     "https://files.consumerfinance.gov/f/documents/cfpb_your-money-your-goals_credit_booklet_cobrand_es.pdf", "A", "EE. UU.", "basico"),
    ("deudas", "cfpb_folleto_atrasado_pagos.pdf", "Folleto: atrasado en los pagos", "CFPB",
     "https://files.consumerfinance.gov/f/documents/bcfp_your-money-goals_behind-on-bills_booklet_es_print.pdf", "A", "EE. UU.", "basico"),
    ("deudas", "cfpb_plan_accion_deudas.pdf", "Plan de accion para deudas", "CFPB",
     "https://files.consumerfinance.gov/f/documents/cfpb_YMYG_toolkit_spanish_debt_action_plan_ADA3.21.pdf", "A", "EE. UU.", "basico"),
    ("derechos", "banco_mundial_buenas_practicas_proteccion_consumidor_2017.pdf", "Good Practices for Financial Consumer Protection (2017)", "Banco Mundial",
     "https://documents1.worldbank.org/curated/en/492761513113437043/pdf/Good-practices-for-financial-consumer-protection-2017-edition.pdf", "A", "internacional", "intermedio"),
    ("contexto", "mef_plan_estrategico_inclusion_financiera.pdf", "Plan Estrategico Multisectorial de la Politica Nacional de Inclusion Financiera", "MEF",
     "https://www.mef.gob.pe/contenidos/archivos-descarga/Plan_Estrategico_Multisectorial_PEM.pdf", "A", "Peru", "intermedio"),
    # Calendario laboral (CTS y gratificaciones): normas y guias oficiales del Estado peruano, verificadas el 2026-11-14
    ("laboral", "tuo_cts_ds_001_97_tr.pdf", "TUO de la Ley de Compensacion por Tiempo de Servicios (DS 001-97-TR)", "MTPE",
     "https://cdn.www.gob.pe/uploads/document/file/229267/TUO_Compensacion_por_Tiempo_de_Servicios_-_D.S_001-97-TR.pdf", "A", "Peru", "intermedio"),
    ("laboral", "mtpe_guia_cts.pdf", "Guia de Compensacion por Tiempo de Servicios", "MTPE",
     "https://cdn.www.gob.pe/uploads/document/file/8050277/6757898-guia_compensacion_tiempo_servicios.pdf", "A", "Peru", "basico"),
    ("laboral", "mtpe_guia_gratificaciones.pdf", "Guia de gratificaciones por Fiestas Patrias y Navidad en el regimen laboral general", "MTPE",
     "https://cdn.www.gob.pe/uploads/document/file/3321103/guia_gratificaciones.pdf", "A", "Peru", "basico"),
    ("laboral", "ley_30334_bonificacion_extraordinaria.pdf", "Ley 30334: bonificacion extraordinaria sobre las gratificaciones", "Congreso",
     "https://www2.congreso.gob.pe/sicr/cendocbib/con4_uibd.nsf/655742D28BB4292C05257EF400058AC6/$FILE/30334.pdf", "A", "Peru", "intermedio"),
    ("derechos", "ley_29571_codigo_proteccion_consumidor.pdf", "Codigo de Proteccion y Defensa del Consumidor (Ley 29571)", "Indecopi",
     "https://consumidor.gob.pe/wp-content/uploads/2020/07/Codigo-de-Proteccion-y-Defensa-del-Consumidor-2023-1.pdf.pdf", "A", "Peru", "intermedio"),
    ("deudas", "sbs_res_6523_2013_tarjetas.pdf", "Reglamento de Tarjetas de Credito y Debito (Res. SBS 6523-2013)", "SBS",
     "https://intranet2.sbs.gob.pe/dv_int_cn/718/v10.0/Adjuntos/6523-2013.R.pdf", "A", "Peru", "intermedio"),
]

# Normas publicadas como pagina oficial (no PDF): se guarda el texto de la norma. modulo, archivo, titulo, institucion, url, marcador de inicio, marcador de fin
NORMAS_WEB = [
    ("laboral", "ley_32322_cts_libre_disposicion.txt", "Ley 32322: retiro de la CTS (100 % hasta el 31-12-2026 y regla permanente del 50 %)", "El Peruano (norma oficial)",
     "https://busquedas.elperuano.pe/dispositivo/NL/2397811-1", "LEY Nº 32322", "DISPOSICIÓN COMPLEMENTARIA FINAL ÚNICA"),
]

# Nivel C: se registran y enlazan, pero no se descargan ni entran al RAG hasta confirmar su licencia (regla de docs/investigacion/rag-fuentes.md).
PENDIENTES_LICENCIA = [
    ("fenomeno_el_nino", "Plan familiar de emergencia ante lluvias y El Nino", "Ministerio de Vivienda", "https://ww3.vivienda.gob.pe/grd/documentos/PLAN-FAMILIAR.pdf", "C", "Peru",
     "Guia educativa; confirmar licencia o reemplazar por un texto normativo"),
    ("ahorro", "Cartilla de educacion economica para profesores de 5.o de secundaria", "BCRP", "https://www.bcrp.gob.pe/docs/Proyeccion-Institucional/sala-economia/cartillas/cartilla-profesores-5-secundaria.pdf", "A",
     "Peru", "El sitio bloquea la descarga automatica (anti-bot); bajarla a mano. Las condiciones del BCRP permiten reproducir citando la fuente"),
]

# carpeta, archivo, titulo, institucion, url, uso
FUENTES = [
    ("inei", "inei_empleo_nacional_i_trim_2026.pdf", "Informe tecnico: Situacion del mercado laboral, I trimestre 2026", "INEI",
     "https://www.inei.gob.pe/media/MenuRecursivo/boletines/empleo-nacional-i-trimestre-2026.pdf", "Calibrar ingresos e informalidad"),
]

# El BCRP (cartilla de 5.o de secundaria) bloquea la descarga automatica con anti-bot: bajarla a mano si se necesita.
ENFEN = range(15, 21)

# codigo BCRP, archivo, descripcion, periodo
BCRP = [
    ("PD04637PD", "tc_interbancario_compra_diario", "Tipo de cambio interbancario, compra (S/ por US$), diario", "2019-1-1/2025-12-31"),
    ("PD04638PD", "tc_interbancario_venta_diario", "Tipo de cambio interbancario, venta (S/ por US$), diario", "2019-1-1/2025-12-31"),
    ("PN01271PM", "ipc_lima_var_mensual", "IPC Lima Metropolitana, variacion % mensual", "2019-1/2025-12"),
    ("PN01273PM", "ipc_lima_var_12m", "IPC Lima Metropolitana, variacion % en 12 meses", "2019-1/2025-12"),
    ("PD04722MM", "tasa_referencia_bcrp", "Tasa de referencia de la politica monetaria del BCRP (%)", "2019-1/2025-12"),
    ("PN07819NM", "tasas_bancarias_mn_promedio", "Tasas de interes activas y pasivas promedio de empresas bancarias en MN (% efectivo anual)", "2019-1/2025-12"),
]


def _sha(ruta_archivo: str) -> str:
    h = hashlib.sha256()
    with open(ruta_archivo, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _bajar_pdf(url: str, destino: str) -> tuple[str, str, int]:
    """Devuelve (estado, detalle, bytes). Estado: ok, existente o error."""
    if os.path.isfile(destino) and os.path.getsize(destino) > 1000:
        return "existente", "", os.path.getsize(destino)
    try:
        r = requests.get(url, headers=CABECERAS, timeout=60, stream=True)
        r.raise_for_status()
        total = 0
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "wb") as f:
            for bloque in r.iter_content(1 << 16):
                total += len(bloque)
                if total > MAX_MB * (1 << 20):
                    raise ValueError(f"supera {MAX_MB} MB")
                f.write(bloque)
        with open(destino, "rb") as f:
            if f.read(5) != b"%PDF-":
                raise ValueError("la respuesta no es un PDF")
        return "ok", "", total
    except Exception as e:  # se registra el motivo y se sigue con la siguiente fuente
        if os.path.isfile(destino):
            os.remove(destino)
        return "error", str(e)[:120], 0


def descargar_rag() -> list[dict]:
    filas = []
    for modulo, archivo, titulo, inst, url, nivel, contexto, lectura in RAG:
        destino = os.path.join(DOCS_RAG, modulo, archivo)
        estado, detalle, nbytes = _bajar_pdf(url, destino)
        filas.append({"modulo": modulo, "archivo": f"{modulo}/{archivo}", "titulo": titulo, "institucion": inst, "enlace": url,
                      "fecha_consulta": HOY, "licencia_nivel": nivel, "contexto": contexto, "nivel_lectura": lectura,
                      "estado": estado, "detalle": detalle, "mb": round(nbytes / (1 << 20), 2),
                      "sha256": _sha(destino) if estado != "error" else ""})
        print(f"[rag] {estado:9s} {archivo} {filas[-1]['mb']} MB {detalle}")
    return filas


def _texto_de_pagina(html_crudo: str) -> str:
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", html_crudo)
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", t))).strip()


def descargar_normas_web() -> list[dict]:
    """Normas oficiales que se publican como pagina (El Peruano): se guarda solo el texto de la norma entre dos marcadores."""
    filas = []
    for modulo, archivo, titulo, inst, url, ini, fin in NORMAS_WEB:
        destino = os.path.join(DOCS_RAG, modulo, archivo)
        estado, detalle = "existente", ""
        if not (os.path.isfile(destino) and os.path.getsize(destino) > 500):
            try:
                r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
                r.raise_for_status()
                t = _texto_de_pagina(r.text)
                if ini not in t or fin not in t:
                    raise ValueError("no se encontraron los marcadores de la norma")
                cuerpo = t[t.index(ini):t.index(fin, t.index(ini))]
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                with open(destino, "w", encoding="utf-8") as f:
                    f.write(f"{titulo}\nFuente oficial: {url}\nConsultada el {HOY}\n\n{cuerpo}\n")
                estado = "ok"
            except Exception as e:  # se registra el motivo y se sigue
                estado, detalle = "error", str(e)[:120]
        filas.append({"modulo": modulo, "archivo": f"{modulo}/{archivo}", "titulo": titulo, "institucion": inst, "enlace": url, "fecha_consulta": HOY, "licencia_nivel": "A",
                      "contexto": "Peru", "nivel_lectura": "intermedio", "estado": estado, "detalle": detalle, "mb": round(os.path.getsize(destino) / (1 << 20), 3) if estado != "error" else 0,
                      "sha256": _sha(destino) if estado != "error" else ""})
        print(f"[norma] {estado:9s} {archivo} {detalle}")
    return filas


def descargar_fuentes() -> list[dict]:
    filas = []
    for carpeta, archivo, titulo, inst, url, uso in FUENTES:
        destino = os.path.join(DOCS_FUENTES, carpeta, archivo)
        estado, detalle, nbytes = _bajar_pdf(url, destino)
        filas.append({"carpeta": carpeta, "archivo": f"{carpeta}/{archivo}", "titulo": titulo, "institucion": inst, "enlace": url,
                      "fecha_consulta": HOY, "uso": uso, "estado": estado, "detalle": detalle, "mb": round(nbytes / (1 << 20), 2),
                      "sha256": _sha(destino) if estado != "error" else ""})
        print(f"[fuente] {estado:9s} {archivo} {filas[-1]['mb']} MB {detalle}")
    return filas


def descargar_enfen() -> list[dict]:
    """El ENFEN publica cada comunicado como pagina web: se guarda su texto con el enlace de origen."""
    import html
    import re

    filas = []
    for n in ENFEN:
        url = f"https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-{n}-2026/"
        destino = os.path.join(DOCS_FUENTES, "enfen", f"enfen_comunicado_{n}_2026.txt")
        try:
            r = requests.get(url, headers=CABECERAS, timeout=60)
            r.raise_for_status()
            try:
                crudo = r.content.decode("utf-8")
            except UnicodeDecodeError:  # la pagina declara UTF-8 pero puede servir Latin-1
                crudo = r.content.decode("cp1252", errors="replace")
            t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", crudo)
            t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip()
            if "magnitud" not in t:
                raise ValueError("la pagina no trae el texto del comunicado")
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            with open(destino, "w", encoding="utf-8") as f:
                f.write(f"Fuente: {url}\nConsulta: {HOY}\n\n{t}\n")
            estado, detalle = "ok", f"{len(t)} caracteres"
        except Exception as e:
            estado, detalle = "error", str(e)[:120]
        filas.append({"carpeta": "enfen", "archivo": f"enfen/enfen_comunicado_{n}_2026.txt", "titulo": f"Comunicado Oficial ENFEN N.o {n}-2026",
                      "institucion": "ENFEN", "enlace": url, "fecha_consulta": HOY, "uso": "Escenario El Nino 2026",
                      "estado": estado, "detalle": detalle, "mb": 0, "sha256": _sha(destino) if estado == "ok" else ""})
        print(f"[enfen] {estado:9s} comunicado {n} {detalle}")
    return filas


def descargar_bcrp() -> list[dict]:
    filas = []
    os.makedirs(os.path.join(DATA_RAW, "bcrp"), exist_ok=True)
    for codigo, nombre, descripcion, periodo in BCRP:
        url = f"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codigo}/json/{periodo}/esp"
        destino = os.path.join(DATA_RAW, "bcrp", f"{nombre}.json")
        try:
            r = requests.get(url, headers=CABECERAS, timeout=60)
            r.raise_for_status()
            datos = r.json()
            n = len(datos.get("periods", []))
            with open(destino, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False)
            estado, detalle = "ok", f"{n} observaciones"
        except Exception as e:
            estado, detalle = "error", str(e)[:120]
        filas.append({"codigo": codigo, "archivo": f"bcrp/{nombre}.json", "descripcion": descripcion, "enlace": url,
                      "fecha_consulta": HOY, "estado": estado, "detalle": detalle})
        print(f"[bcrp] {estado:9s} {codigo} {detalle}")
    return filas


def _csv(ruta_csv: str, filas: list[dict]) -> None:
    if not filas:
        return
    os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)


def main() -> int:
    filas = descargar_rag() + descargar_normas_web()
    for modulo, titulo, inst, url, nivel, contexto, nota in PENDIENTES_LICENCIA:
        filas.append({"modulo": modulo, "archivo": "", "titulo": titulo, "institucion": inst, "enlace": url, "fecha_consulta": HOY, "licencia_nivel": nivel,
                      "contexto": contexto, "nivel_lectura": "basico", "estado": "pendiente", "detalle": nota, "mb": 0, "sha256": ""})
    for n in ENFEN:  # comunicados del ENFEN: textos oficiales de caracter administrativo (nivel A, DL 822 art. 9), guardados como texto
        origen = os.path.join(DOCS_FUENTES, "enfen", f"enfen_comunicado_{n}_2026.txt")
        destino = os.path.join(DOCS_RAG, "fenomeno_el_nino", f"enfen_comunicado_{n}_2026.txt")
        if os.path.isfile(origen):
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            shutil.copyfile(origen, destino)
            filas.append({"modulo": "fenomeno_el_nino", "archivo": f"fenomeno_el_nino/enfen_comunicado_{n}_2026.txt", "titulo": f"Comunicado Oficial ENFEN N.o {n}-2026",
                          "institucion": "ENFEN", "enlace": f"https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-{n}-2026/", "fecha_consulta": HOY, "licencia_nivel": "A",
                          "contexto": "Peru", "nivel_lectura": "basico", "estado": "ok", "detalle": "texto de la pagina oficial", "mb": 0, "sha256": _sha(destino)})
    _csv(os.path.join(DOCS_RAG, "fuentes.csv"), filas)
    _csv(os.path.join(DOCS_FUENTES, "fuentes.csv"), descargar_fuentes() + descargar_enfen())
    _csv(os.path.join(DOCS_FUENTES, "bcrp_series.csv"), descargar_bcrp())
    return 0


if __name__ == "__main__":
    sys.exit(main())
