"""Carpeta de presentacion y documentacion: todas las graficas y diagramas que sirven para la presentacion final y para la documentacion, en un solo lugar (docs/presentacion/).
Todo sale de models/*.json (nada escrito a mano) y de los grafos reales del agente (app.get_graph()), de modo que lo que se muestra es lo que se ejecuta.
Las graficas de comparacion de modelos (modelo elegido frente a su baseline) las genera eval/comparativa_modelos.py en docs/presentacion/modelos/.
Paleta validada con el validador del skill dataviz (azul, naranja y verde azulado: separacion para daltonismo y contraste >= 3:1); el gris es neutro y va con trazo discontinuo y etiqueta directa.
Uso: python eval/construir_presentacion.py   ->  docs/presentacion/graficas/, docs/presentacion/diagramas/ y docs/presentacion/README.md"""
import json
import os
import sys
import textwrap
import warnings
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
warnings.filterwarnings("ignore")
os.environ.setdefault("LLM_PROVIDER", "plantillas")

SUPERFICIE, TINTA, TINTA_2 = "#fcfcfb", "#0b0b0b", "#52514e"
AZUL, NARANJA, VERDE, GRIS = "#2a78d6", "#c8641a", "#2a9d8f", "#8c8b86"
SALIDA = os.path.join(RAIZ, "docs", "presentacion")
G, D = os.path.join(SALIDA, "graficas"), os.path.join(SALIDA, "diagramas")
MODELOS = os.path.join(RAIZ, "models")


def J(nombre: str) -> dict:
    with open(os.path.join(MODELOS, nombre), encoding="utf-8") as f:
        return json.load(f)


def base(titulo: str, subtitulo: str, fuente: str, figsize=(9.2, 4.9), paneles=1):
    fig, axs = plt.subplots(1, paneles, figsize=figsize, dpi=200, facecolor=SUPERFICIE)
    axs = [axs] if paneles == 1 else list(axs)
    for ax in axs:
        ax.set_facecolor(SUPERFICIE)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            ax.spines[lado].set_color("#c9c8c2")
        ax.tick_params(colors=TINTA_2, labelsize=9)
        ax.grid(axis="y", color="#e6e5e0", linewidth=0.8, zorder=0)
    fig.text(0.015, 0.965, titulo, fontsize=14, fontweight="bold", color=TINTA, va="top")
    fig.text(0.015, 0.915, subtitulo, fontsize=9.5, color=TINTA_2, va="top")
    fig.text(0.015, 0.012, f"Datos sinteticos · fuente: {fuente}", fontsize=8, color=TINTA_2)
    return fig, axs


def guardar(fig, carpeta: str, nombre: str) -> str:
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    fig.savefig(ruta, facecolor=SUPERFICIE)
    plt.close(fig)
    return os.path.relpath(ruta, RAIZ).replace(os.sep, "/")


def etiqueta_final(ax, x, y, texto, color, dy=0.0, ha="left"):
    ax.text(x, y + dy, texto, color=TINTA, fontsize=9, va="center", ha=ha, fontweight="bold",
            bbox=dict(facecolor=SUPERFICIE, edgecolor="none", pad=1.5))
    ax.plot([x], [y], marker="o", markersize=5, color=color, zorder=5)


# ------------------------------------------------------------------------------------------------------------------------------------ graficas de modelos y valor
def serie_diaria_por_dia() -> str:
    S = J("metricas_serie_diaria.json")
    pd_ = S["por_dia"]
    dias = [r["dia"] for r in pd_["serie_diaria"]]
    fig, (a1, a2) = base("Pronostico dia por dia: cubre lo prometido en cada uno de los 30 dias",
                         "Banda al 80 % (izquierda: cobertura, objetivo 0.80) y error medio sobre el ingreso mensual (derecha, menor es mejor)",
                         "models/metricas_serie_diaria.json", figsize=(11.5, 4.9), paneles=2)
    est = {"serie_diaria": (AZUL, "-", "Serie diaria"), "recta_al_dia_30": (GRIS, (0, (4, 3)), "Recta al dia 30"), "promedio_movil_3_meses": (NARANJA, "-", "Promedio movil 3 meses")}
    for k, (col, ls, nom) in est.items():
        c = [r["cobertura_80"] for r in pd_[k]]
        e = [r["mae_rel_ingreso"] for r in pd_[k]]
        a1.plot(dias, c, color=col, linestyle=ls, linewidth=2.2 if k == "serie_diaria" else 1.6, zorder=3)
        a2.plot(dias, e, color=col, linestyle=ls, linewidth=2.2 if k == "serie_diaria" else 1.6, zorder=3)
        etiqueta_final(a1, 30.6, c[-1], nom, col)
        etiqueta_final(a2, 30.6, e[-1], nom, col)
    a1.axhline(0.80, color=TINTA_2, linewidth=1.0, linestyle=(0, (2, 3)), zorder=2)
    a1.text(1, 0.808, "objetivo 0.80", fontsize=8.5, color=TINTA_2)
    for ax, y in ((a1, "Cobertura de la banda al 80 %"), (a2, "Error medio / ingreso mensual")):
        ax.set_xlim(1, 41)
        ax.set_xlabel("Dia del pronostico", color=TINTA_2, fontsize=9)
        ax.set_ylabel(y, color=TINTA_2, fontsize=9)
    a1.set_ylim(0.55, 0.95)
    fig.subplots_adjust(left=0.07, right=0.985, top=0.80, bottom=0.14, wspace=0.28)
    return guardar(fig, G, "serie_diaria_cobertura_y_error_por_dia.png")


def serie_diaria_ejemplo(repo) -> str:
    from src.agente_analitico.contrato import pronostico_contrato
    elegido = None
    for cid in repo.clientes.index[:300]:
        c = pronostico_contrato(repo, cid, hoy=repo.fecha.date())
        if c and c["first_risk_date"] and 0.35 <= c["risk_probability"] <= 0.9 and min(x["lower_bound"] for x in c["forecast"]) < 0 < max(x["upper_bound"] for x in c["forecast"]):
            elegido = c
            break
    c = elegido or pronostico_contrato(repo, repo.clientes.index[0], hoy=repo.fecha.date())
    f = c["forecast"]
    x = list(range(1, len(f) + 1))
    fig, (ax,) = base("Asi ve el cliente su saldo de los proximos 30 dias",
                      "Linea = saldo esperado; banda = rango en el que cae el saldo 8 de cada 10 veces. Cliente sintetico; el pronostico no es un saldo garantizado",
                      "src/agente_analitico/contrato.py (respuesta del endpoint /forecast)")
    ax.fill_between(x, [v["lower_bound"] for v in f], [v["upper_bound"] for v in f], color=AZUL, alpha=0.18, linewidth=0, zorder=2)
    ax.plot(x, [v["predicted_balance"] for v in f], color=AZUL, linewidth=2.4, zorder=4)
    ax.axhline(0, color=TINTA, linewidth=1.0, zorder=3)
    ax.text(1, 0, " saldo 0", fontsize=8.5, color=TINTA_2, va="bottom")
    if c["first_risk_date"]:
        d0 = date.fromisoformat(f[0]["date"])
        dr = (date.fromisoformat(c["first_risk_date"]) - d0).days + 1
        ax.axvline(dr, color=NARANJA, linewidth=1.6, linestyle=(0, (4, 3)), zorder=3)
        ax.text(dr + 0.4, ax.get_ylim()[1] * 0.92, f"primer dia de riesgo\n{c['first_risk_date']}\n(probabilidad {c['risk_probability']:.0%})", color=TINTA, fontsize=9, va="top",
                bbox=dict(facecolor=SUPERFICIE, edgecolor="none", pad=1.5))
    ax.set_xlim(1, 30)
    ax.set_xlabel("Dias desde el cierre de datos", color=TINTA_2, fontsize=9)
    ax.set_ylabel("Saldo (S/)", color=TINTA_2, fontsize=9)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.82, bottom=0.14)
    return guardar(fig, G, "serie_diaria_ejemplo_de_un_cliente.png")


def politicas_de_ahorro() -> str:
    t = J("metricas_impacto.json")["tabla"]
    filas = [("Lucas + ahorro automatico", "lucas_mas_ahorro_ajustado", AZUL), ("Lucas solo", "lucas", AZUL), ("No hacer nada", "nada", GRIS), ("10 % fijo, ajustado", "diez_fijo_ajustado", GRIS)]
    fig, (a1, a2) = base("Lucas evita los dias en rojo y, con ahorro automatico, tambien forma colchon",
                         "Reproduccion contrafactual 2024 a 2025 sobre 500 clientes sinteticos. A la izquierda menor es mejor; a la derecha mayor es mejor",
                         "models/metricas_impacto.json", figsize=(11.5, 4.9), paneles=2)
    for ax, clave, fmt, nota in ((a1, "dias_en_rojo_por_cliente_mes", ".2f", "Dias en rojo por cliente al mes"), (a2, "colchon_final_meses_de_ingreso", ".2f", "Colchon final (meses de ingreso)")):
        y = list(range(len(filas)))[::-1]
        vals = [t[k][clave] for _, k, _ in filas]
        barras = ax.barh(y, vals, color=[c for _, _, c in filas], height=0.56, zorder=3)
        barras[0].set_hatch("////")
        barras[0].set_edgecolor("#a9c8f0")
        ax.set_yticks(y)
        ax.set_yticklabels([n for n, _, _ in filas], fontsize=9.5, color=TINTA)
        ax.set_xlim(0, max(vals) * 1.35)
        for yy, v in zip(y, vals):
            ax.text(v + max(vals) * 0.02, yy, f"{v:{fmt}}", va="center", fontsize=10, color=TINTA, fontweight="bold")
        ax.set_xlabel(nota, color=TINTA_2, fontsize=9)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", color="#e6e5e0", linewidth=0.8, zorder=0)
    fig.text(0.015, 0.055, f"Prueba de estres (no se recomienda): apartar dinero bloqueado sin recortar el gasto deja {t['diez_fijo']['dias_en_rojo_por_cliente_mes']:.1f} dias en rojo al mes (10 % fijo) y "
             f"{t['lucas_ahorro_guiado']['dias_en_rojo_por_cliente_mes']:.1f} (ahorro guiado por excedente). Por eso Lucas usa una reserva que se puede usar.", fontsize=8.5, color=TINTA_2)
    fig.subplots_adjust(left=0.19, right=0.97, top=0.80, bottom=0.17, wspace=0.55)
    return guardar(fig, G, "politica_de_ahorro_dias_en_rojo_y_colchon.png")


def puntos_a_futuro() -> str:
    pf = J("metricas_valor.json")["proyeccion_a_futuro"]
    est = [("solo_lo_medido", "Solo lo medido", GRIS, (0, (4, 3))), ("prudente", "Prudente", VERDE, "-"), ("base", "Base", AZUL, "-"), ("optimista", "Optimista", NARANJA, "-")]
    fig, (ax,) = base("Programa de puntos: cuando se paga, por usuario que entra",
                      "Neto acumulado por usuario (S/). Supuestos de conducta del equipo, sin piloto: sirven para ver que debe cumplirse, no para prometer un resultado",
                      "models/metricas_valor.json (proyeccion_a_futuro)")
    for k, nom, col, ls in est:
        e = pf["escenarios"][k]["por_anio"]
        x = [r["anio"] for r in e]
        y = [r["neto_acumulado"] for r in e]
        ax.plot(x, y, color=col, linestyle=ls, linewidth=2.2, marker="o", markersize=4.5, zorder=3)
        etiqueta_final(ax, x[-1] + 0.08, y[-1], f"{nom}  S/ {y[-1]:,.0f}", col)
    ax.axhline(0, color=TINTA, linewidth=1.0, zorder=2)
    ax.set_xlim(1, pf["supuestos_generales"]["anos"] + 1.7)
    ax.set_xticks(range(1, pf["supuestos_generales"]["anos"] + 1))
    ax.set_xlabel("Anio desde el inicio del programa", color=TINTA_2, fontsize=9)
    ax.set_ylabel("Neto acumulado por usuario (S/)", color=TINTA_2, fontsize=9)
    s = pf["escenarios"]
    fig.text(0.015, 0.055, f"Solo con lo medido pierde S/ {-s['solo_lo_medido']['por_anio'][0]['neto_por_usuario_que_entra']:.2f} por usuario al anio. Se paga con {pf['ahorro_adicional_necesario_para_pagarse_en_el_anio_1']:.1%} mas de ahorro apartado "
             f"o {pf['consumo_adicional_necesario_para_pagarse_en_n_anios']['1']:.1%} mas de consumo con tarjeta o QR.", fontsize=8.5, color=TINTA_2)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.82, bottom=0.17)
    return guardar(fig, G, "programa_de_puntos_proyeccion_a_futuro.png")


def eleccion_de_k() -> str:
    seg = J("metricas.json")["segmentacion"]
    ks = sorted(int(k) for k in seg["tabla_k"])
    sil = [seg["tabla_k"][str(k)]["silueta_gower"] for k in ks]
    est = [seg["tabla_k"][str(k)]["estabilidad_ari"] for k in ks]
    fig, (ax,) = base("Segmentacion: por que k = %d segmentos" % seg["k"],
                      "Se elige el k de mayor silueta entre los que superan estabilidad 0.60 al remuestrear (K-Prototypes, variables numericas y categoricas)",
                      "models/metricas.json (segmentacion.tabla_k)")
    ax.plot(ks, sil, color=AZUL, linewidth=2.2, marker="o", zorder=3)
    ax.plot(ks, est, color=NARANJA, linewidth=2.2, marker="s", zorder=3)
    ax.axhline(0.60, color=TINTA_2, linewidth=1.0, linestyle=(0, (2, 3)), zorder=2)
    ax.text(ks[0], 0.615, "umbral de estabilidad 0.60", fontsize=8.5, color=TINTA_2)
    ax.axvline(seg["k"], color=TINTA, linewidth=1.2, zorder=2)
    ax.text(seg["k"] + 0.06, max(max(sil), max(est)) * 0.98, "elegido", fontsize=9.5, fontweight="bold", color=TINTA)
    etiqueta_final(ax, ks[-1] + 0.1, sil[-1], "Silueta de Gower", AZUL)
    etiqueta_final(ax, ks[-1] + 0.1, est[-1], "Estabilidad (ARI)", NARANJA)
    ax.set_xlim(ks[0], ks[-1] + 1.6)
    ax.set_xticks(ks)
    ax.set_xlabel("Numero de segmentos (k)", color=TINTA_2, fontsize=9)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.82, bottom=0.14)
    return guardar(fig, G, "segmentacion_eleccion_de_k.png")


def calendario_laboral() -> str:
    from src.generador.contexto import cargar_yaml
    c = cargar_yaml("normas_laborales.yaml")
    fin = date.fromisoformat(c["libre_disposicion"]["vigente_hasta"])
    prop = c["libre_disposicion"]["proyecto_en_evaluacion"]
    meses = [(2026, m) for m in range(1, 13)] + [(2027, m) for m in range(1, 13)]
    pos = {mm: i for i, mm in enumerate(meses)}
    fig, (ax,) = base("Calendario laboral que Lucas vigila: gratificacion, CTS y la fecha que vence",
                      "Reglas contrastadas con documentos oficiales (cada una tiene su frase literal verificada por pruebas). Fechas limite de deposito: dia %d" % c["gratificacion"]["dia_limite"],
                      "data/parametros/normas_laborales.yaml", figsize=(11.5, 4.2))
    ax.set_ylim(0, 4)
    ax.grid(axis="y", visible=False)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    for (a, m), i in pos.items():
        for nombre, mm_list, y, col in (("Gratificacion", c["gratificacion"]["meses"], 3.0, AZUL), ("CTS (deposito)", c["cts"]["meses_deposito"], 2.0, NARANJA)):
            if m in mm_list:
                ax.plot([i + 0.5], [y], marker="o", markersize=11, color=col, zorder=4)
                ax.text(i + 0.5, y + 0.38, f"15 {['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'][m - 1]}", ha="center", fontsize=8.5, color=TINTA)
    i_fin = pos[(fin.year, fin.month)] + fin.day / 31
    ax.barh(1.0, i_fin, left=0, height=0.5, color=VERDE, zorder=3)
    ax.barh(1.0, len(meses) - i_fin, left=i_fin, height=0.5, color=GRIS, alpha=0.55, zorder=3)
    ax.text(i_fin / 2, 1.0, "CTS: libre disposicion del 100 %", ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
    ax.text(i_fin + (len(meses) - i_fin) / 2, 1.0, "solo hasta 50 %", ha="center", va="center", color=TINTA, fontsize=9.5, fontweight="bold")
    ax.axvline(i_fin, color=TINTA, linewidth=1.4, zorder=5)
    ax.text(i_fin + 0.1, 3.75, f"vence el {fin.day} dic {fin.year}", fontsize=9.5, fontweight="bold", color=TINTA, va="top")
    ax.text(len(meses) - 0.1, 0.25, f"Proyecto de ley en evaluacion ({prop['expediente'].split(' ')[-1]}) propone ampliarla hasta {prop['plazo_propuesto'][:4]}: todavia no es ley", ha="right", fontsize=8.5, color=TINTA_2)
    ax.set_xticks([i + 0.5 for i in range(len(meses))])
    ax.set_xticklabels([f"{['E','F','M','A','M','J','J','A','S','O','N','D'][m - 1]}\n{a if m == 1 else ''}" for a, m in meses], fontsize=8.5)
    ax.set_xlim(0, len(meses))
    ax.text(0.2, 3.72, "Gratificacion", color=AZUL, fontsize=9, va="top", fontweight="bold")
    ax.text(0.2, 2.72, "CTS (deposito)", color=NARANJA, fontsize=9, va="top", fontweight="bold")
    fig.subplots_adjust(left=0.03, right=0.985, top=0.80, bottom=0.17)
    return guardar(fig, G, "calendario_laboral_2026_2027.png")


# ------------------------------------------------------------------------------------------------------------------------------------ diagramas
def caja(ax, x, y, w, h, texto, color, tam=9, relleno="#ffffff", negrita=False, envolver=26):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.018", linewidth=1.6, edgecolor=color, facecolor=relleno, zorder=3))
    ax.text(x + w / 2, y + h / 2, textwrap.fill(texto, envolver), ha="center", va="center", fontsize=tam, color=TINTA, fontweight="bold" if negrita else "normal", zorder=4)


def flecha(ax, p, q, color=TINTA_2, estilo="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=11, linewidth=1.3, color=color, linestyle=estilo, connectionstyle=f"arc3,rad={rad}", zorder=2))


def arquitectura() -> str:
    fig, ax = plt.subplots(figsize=(12.5, 7.4), dpi=200, facecolor=SUPERFICIE)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])   # los ejes ocupan toda la figura: las coordenadas de cajas y textos coinciden
    fig.text(0.015, 0.975, "Arquitectura de Lucas: de los datos a una respuesta verificada", fontsize=15, fontweight="bold", color=TINTA, va="top")
    fig.text(0.015, 0.935, "Los modelos calculan; el LLM solo redacta; un verificador determinista rechaza cualquier cifra que no venga de una herramienta", fontsize=10, color=TINTA_2, va="top")
    capas = [("DATOS", 0.80, [("Generador sintetico\n500 clientes, 3.3 M movimientos", AZUL), ("BCRP: IPC y tipo de cambio\n(tiempo real)", VERDE), ("ENFEN: El Nino\n(tiempo real)", VERDE), ("Normas laborales y fuentes oficiales\n(RAG nivel A)", VERDE)]),
             ("MODELOS", 0.62, [("Segmentacion\nK-Prototypes", AZUL), ("Pronostico 30 dias y serie diaria\nLightGBM + conformal", AZUL), ("Alerta de rojo y dia de riesgo\nclasificador calibrado", AZUL), ("Politica de ahorro y puntos\nreproduccion contrafactual", AZUL)]),
             ("CONOCIMIENTO", 0.44, [("RAG\nFAISS + BM25 + CRAG", NARANJA), ("Calendario laboral\ngratificacion, CTS", NARANJA), ("Datos vivos\nmovimientos nuevos", NARANJA), ("Vigilancia\nmax. 3 avisos por semana", NARANJA)])]
    xs = [0.05, 0.285, 0.52, 0.755]
    for nombre, y, cajas in capas:
        fig.text(0.015, y + 0.062, nombre, fontsize=9, color=TINTA_2, fontweight="bold")
        for x, (t, col) in zip(xs, cajas):
            caja(ax, x, y - 0.03, 0.21, 0.115, t, col, tam=8.6)
    for y0, y1 in ((0.77, 0.715), (0.59, 0.535)):
        for x in xs:
            flecha(ax, (x + 0.105, y0), (x + 0.105, y1))
    # agente
    fig.text(0.015, 0.317, "AGENTE (LangGraph)", fontsize=9, color=TINTA_2, fontweight="bold")
    pasos = [("Router\nreglas + seguridad", 0.05), ("Herramientas\ncifras con respaldo", 0.235), ("Verificador\nnumeros y prohibiciones", 0.42), ("LLM redacta\nGemini u otra API", 0.605), ("Verificador\nde nuevo", 0.79)]
    for t, x in pasos:
        caja(ax, x, 0.215, 0.16, 0.115, t, VERDE, tam=8.6, relleno="#f3faf8")
    for (_, a), (_, b) in zip(pasos, pasos[1:]):
        flecha(ax, (a + 0.16, 0.2725), (b, 0.2725))
    for x in (0.285, 0.52, 0.755):
        flecha(ax, (x + 0.105, 0.41), (min(max(x, 0.235), 0.74) + 0.08, 0.335), color=NARANJA, rad=0.0)
    caja(ax, 0.20, 0.07, 0.27, 0.095, "Si el LLM falla o inventa una cifra: plantilla determinista", GRIS, tam=8.6)
    caja(ax, 0.52, 0.07, 0.27, 0.095, "Traduccion es / en / qu con cifras y nombres protegidos", GRIS, tam=8.6)
    flecha(ax, (0.68, 0.213), (0.35, 0.168), color=GRIS, estilo=(0, (4, 3)))
    flecha(ax, (0.87, 0.213), (0.70, 0.168), color=GRIS)
    caja(ax, 0.82, 0.07, 0.15, 0.095, "API REST y app\n(integracion final)", AZUL, tam=8.6, relleno="#eef4fc")
    flecha(ax, (0.79, 0.1175), (0.82, 0.1175))
    fig.text(0.015, 0.012, "Datos sinteticos. Azul = modelos propios · verde = fuentes oficiales y agente · naranja = conocimiento del dominio · gris = salvaguardas", fontsize=8, color=TINTA_2)
    return guardar(fig, D, "arquitectura_del_sistema.png")


def grafo_agente(repo, buscador, modo: str) -> str:
    from src.agente_analitico.grafo import construir_grafo
    g = construir_grafo(repo, buscador, modo).get_graph()
    nodos = list(g.nodes)
    aristas = [(e.source, e.target, bool(e.conditional)) for e in g.edges]
    prof = {"__start__": 0}
    cola = ["__start__"]
    while cola:   # profundidad por recorrido en anchura: los retornos (ciclos) no cuentan
        u = cola.pop(0)
        for a, b, _ in aristas:
            if a == u and b not in prof:
                prof[b] = prof[u] + 1
                cola.append(b)
    for n in nodos:
        prof.setdefault(n, max(prof.values()) + 1)
    capas = {}
    for n in nodos:
        capas.setdefault(prof[n], []).append(n)
    fig, ax = plt.subplots(figsize=(13.5, 2.0 + 1.25 * max(len(v) for v in capas.values())), dpi=200, facecolor=SUPERFICIE)
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])   # los ejes ocupan toda la figura: las coordenadas de cajas y textos coinciden
    fig.text(0.012, 0.975, f"Grafo del agente ({modo.replace('_', ' ')}): {len(nodos)} nodos, {len(aristas)} conexiones", fontsize=14, fontweight="bold", color=TINTA, va="top")
    fig.text(0.012, 0.925, "Generado desde app.get_graph() de LangGraph, el mismo grafo que se ejecuta. Linea continua = paso fijo; discontinua = decision segun el estado", fontsize=9.5, color=TINTA_2, va="top")
    W, H = 0.082, 0.085
    xy = {}
    nmax = max(len(v) for v in capas.values())
    for d, lst in capas.items():
        x = 0.03 + d * (0.94 - W) / max(capas)
        for i, n in enumerate(lst):
            xy[n] = (x, 0.82 - (i + 0.5) * (0.74 / nmax) - H / 2 + (nmax - len(lst)) * (0.74 / nmax) / 2)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    for a, b, cond in aristas:
        (xa, ya), (xb, yb) = xy[a], xy[b]
        retorno = prof[b] <= prof[a]
        p = (xa + W if not retorno else xa + W / 2, ya + H / 2 if not retorno else ya + (H if yb >= ya else 0))
        q = (xb if not retorno else xb + W / 2, yb + H / 2 if not retorno else yb + (0 if yb >= ya else H))
        flecha(ax, p, q, color=NARANJA if cond else TINTA_2, estilo=(0, (4, 3)) if cond else "-", rad=0.25 if retorno else (0.08 if cond else 0.0))
    for n, (x, y) in xy.items():
        especial = n in ("__start__", "__end__")
        caja(ax, x, y, W, H, n.strip("_") if especial else n, GRIS if especial else VERDE, tam=8.2, relleno="#eeeeea" if especial else "#f3faf8", negrita=especial)
    fig.text(0.012, 0.012, "Naranja discontinuo = salto condicional (por ejemplo, el verificador decide si reintenta, usa la plantilla o termina)", fontsize=8, color=TINTA_2)
    return guardar(fig, D, f"grafo_{modo}.png")



def ahorro_de_tokens(buscador) -> str:
    import importlib.util
    spec = importlib.util.spec_from_file_location("mapa_de_consultas", os.path.join(RAIZ, "eval", "mapa_de_consultas.py"))
    mp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mp)
    M = mp.generar(buscador)
    C = {f["n"]: f for f in M["consultas"]}
    por = {}
    for f in M["consultas"]:
        por.setdefault(f["camino"], []).append(f["n"])
    fig, ax = plt.subplots(figsize=(13.5, 9.0), dpi=200, facecolor=SUPERFICIE)
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.text(0.015, 0.975, "Como optimizamos tokens: la ruta de cada consulta", fontsize=15, fontweight="bold", color=TINTA, va="top")
    fig.text(0.015, 0.94, "Lo generico se responde con plantillas (0 tokens); solo lo nuevo llega al agente de IA, y llega con 3 fragmentos recuperados por embeddings, no con el corpus", fontsize=10, color=TINTA_2, va="top")
    # entrada
    ax.add_patch(FancyBboxPatch((0.015, 0.40), 0.27, 0.49, boxstyle="round,pad=0.01,rounding_size=0.015", linewidth=1.6, edgecolor=GRIS, facecolor="#ffffff", zorder=3))
    ax.text(0.03, 0.865, "Entrada: un parrafo de consultas", fontsize=10, fontweight="bold", color=TINTA, va="top", zorder=4)
    y = 0.825
    for f in M["consultas"]:
        linea = textwrap.fill(f"{f['n']}. {f['consulta']}", 40)
        ax.text(0.03, y, linea, fontsize=8.6, color=TINTA, va="top", zorder=4)
        y -= 0.052 if "\n" not in linea else 0.07
    # router
    caja(ax, 0.315, 0.575, 0.115, 0.14, "Router de reglas\n(detecta el tema)\n0 tokens", AZUL, tam=8.6, negrita=True, relleno="#eef4fc", envolver=16)
    flecha(ax, (0.285, 0.645), (0.315, 0.645))
    # carriles
    carriles = [("herramientas_y_plantilla", "Tema conocido: los modelos calculan y una PLANTILLA redacta", "0 tokens", AZUL, 0.775, "pronostico, calendario, tipo de cambio, nivel, tasas, El Nino, ofertas"),
                ("plantilla_fija", "Seguridad, fuera de alcance o fuera de tema: PLANTILLA fija", "0 tokens", GRIS, 0.665, "operaciones, instrucciones internas, codigo, chistes"),
                ("preguntas_frecuentes", "Pregunta de concepto ya respondida y verificada: PREGUNTAS FRECUENTES", "0 tokens", VERDE, 0.555, "misma pregunta, mismo nivel, con sus citas")]
    for clave, titulo, tok, col, yy, nota in carriles:
        ns = por.get(clave, [])
        ax.add_patch(FancyBboxPatch((0.47, yy), 0.51, 0.085, boxstyle="round,pad=0.008,rounding_size=0.012", linewidth=1.6, edgecolor=col, facecolor="#ffffff", zorder=3))
        ax.text(0.485, yy + 0.068, titulo, fontsize=9, fontweight="bold", color=TINTA, va="top", zorder=4)
        ax.text(0.485, yy + 0.03, f"{nota}  ·  consultas: {', '.join(map(str, ns)) or 'ninguna'}", fontsize=8.2, color=TINTA_2, va="top", zorder=4)
        ax.text(0.965, yy + 0.068, tok, fontsize=9.5, fontweight="bold", color=col if col != GRIS else TINTA_2, va="top", ha="right", zorder=4)
        flecha(ax, (0.43, 0.645), (0.47, yy + 0.0425), color=col, rad=0.0)
    # carril de IA con RAG
    ns = por.get("rag_y_ia", [])
    ax.add_patch(FancyBboxPatch((0.47, 0.23), 0.51, 0.30, boxstyle="round,pad=0.008,rounding_size=0.012", linewidth=1.8, edgecolor=NARANJA, facecolor="#fffaf5", zorder=3))
    ax.text(0.485, 0.515, "Pregunta de concepto NUEVA: agente de IA con RAG", fontsize=9, fontweight="bold", color=TINTA, va="top", zorder=4)
    ax.text(0.965, 0.515, f"~{M['tokens_por_llamada_medidos_en_la_qa']['entrada'] + M['tokens_por_llamada_medidos_en_la_qa']['salida']:,} tokens", fontsize=9.5, fontweight="bold", color=NARANJA, va="top", ha="right", zorder=4)
    ax.text(0.485, 0.485, f"consulta {', '.join(map(str, ns))}: «{C[ns[0]]['consulta']}»" if ns else "", fontsize=8.2, color=TINTA_2, va="top", zorder=4)
    flecha(ax, (0.43, 0.62), (0.47, 0.40), color=NARANJA)
    paso = [("1. Chunks\ncorpus troceado una vez: 900 caracteres, solape 120", AZUL), ("2. Embeddings\nla pregunta se vectoriza (search_query, 768 dim) y se compara con los de los chunks", VERDE),
            ("3. Top-3 con filtro\nsimilitud 0.70 o mas; si ninguno sirve, no contesta", NARANJA), ("4. LLM redacta\nsolo con 3 fragmentos y los datos; sin ids ni zona", VERDE),
            ("5. Verificador\ncada cifra con respaldo; si pasa, se guarda en preguntas frecuentes", NARANJA)]
    w, g = 0.084, 0.0105
    for i, (t, col) in enumerate(paso):
        x = 0.482 + i * (w + g)
        caja(ax, x, 0.345, w, 0.105, t, col, tam=6.6, envolver=15)
        if i:
            flecha(ax, (x - g, 0.3975), (x, 0.3975))
    rag = M["rag"]
    if rag:
        ax.text(0.485, 0.315, "Lo que el RAG devolvio de verdad para esa pregunta:", fontsize=8.2, fontweight="bold", color=TINTA, va="top", zorder=4)
        for k, f in enumerate(rag["fragmentos"]):
            ax.text(0.485, 0.29 - k * 0.025, f"{k + 1}. {textwrap.shorten(f['titulo'], 62)} (pag. {f['pagina']}), similitud {f['similitud']:.2f}, ~{f['tokens_estimados']} tokens", fontsize=7.8, color=TINTA_2, va="top", zorder=4)
    # balance de tokens
    ax.add_patch(FancyBboxPatch((0.015, 0.045), 0.965, 0.14, boxstyle="round,pad=0.008,rounding_size=0.012", linewidth=1.6, edgecolor=TINTA_2, facecolor="#ffffff", zorder=3))
    ax.text(0.03, 0.17, "Balance de este parrafo", fontsize=10, fontweight="bold", color=TINTA, va="top", zorder=4)
    n = len(M["consultas"])
    ax.text(0.03, 0.135, f"Sin ruteo (las {n} consultas al LLM): {n} llamadas x ~{M['tokens_por_llamada_medidos_en_la_qa']['entrada'] + M['tokens_por_llamada_medidos_en_la_qa']['salida']:,} = ~{M['todo_al_llm']:,} tokens", fontsize=9.2, color=TINTA, va="top", zorder=4)
    ax.text(0.03, 0.105, f"Con ruteo: 1 llamada (la pregunta nueva) = ~{M['con_ruteo']:,} tokens, {M['ahorro']:.0%} menos. Y si el LLM tuviera que leer todo el corpus: ~{M['tokens_del_corpus_completo']:,} tokens por consulta; "
            f"con el RAG recibe ~{M['tokens_de_los_3_fragmentos']:,}.", fontsize=9.2, color=TINTA, va="top", zorder=4)
    ax.text(0.03, 0.078, chr(10).join(textwrap.wrap("Si la API cae, la consulta 5 se responde con la plantilla y las mismas citas. " + M["nota"], 190)), fontsize=7.8, color=TINTA_2, va="top", zorder=4)
    fig.text(0.015, 0.015, "Datos sinteticos · router, RAG y tokens medidos de verdad (eval/mapa_de_consultas.py) · politica LLM_USO=ahorro", fontsize=8, color=TINTA_2)
    return guardar(fig, D, "agente_ahorro_de_tokens.png")


def rag_arquitectura() -> str:
    info = json.load(open(os.path.join(RAIZ, "docs", "rag", "indice", "info.json"), encoding="utf-8"))
    val, rag = J("metricas_rag_validacion.json"), J("metricas_rag.json")
    frags = json.load(open(os.path.join(RAIZ, "docs", "rag", "indice", "fragmentos.json"), encoding="utf-8"))
    chars = sum(len(f["texto"]) for f in frags)
    pct = 1 - (3 * chars / len(frags)) / chars
    mejor = max(rag["recuperacion"].values(), key=lambda x: x["recall@4"])
    fig, ax = plt.subplots(figsize=(13.5, 8.6), dpi=200, facecolor=SUPERFICIE)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])   # los ejes ocupan toda la figura: las coordenadas de cajas y textos coinciden
    fig.text(0.015, 0.975, "RAG: de las fuentes oficiales a una respuesta con citas", fontsize=15, fontweight="bold", color=TINTA, va="top")
    fig.text(0.015, 0.94, "Troceado, embeddings e indice se hacen una vez y en local; cada pregunta solo recupera los fragmentos que sirven, no el corpus", fontsize=10, color=TINTA_2, va="top")
    fig.text(0.015, 0.89, "INGESTA (una vez, todo local)", fontsize=9.5, color=TINTA_2, fontweight="bold")
    paso = [("Fuentes oficiales\n%d documentos, nivel A (normas y textos oficiales o de libre uso), con hash SHA-256" % len({f["documento"] for f in frags}), AZUL),
            ("Texto por pagina\nPDF y texto plano; cada fragmento guarda titulo, pagina, enlace y licencia", AZUL),
            ("Troceado\n%d caracteres, solape %d; corta por parrafo, oracion y palabra. %s fragmentos sin repetidos" % (info["tam_fragmento"], info["solape"], f"{info['fragmentos']:,}"), AZUL),
            ("Embeddings\n%s (Ollama, local)\nprefijo «search_document:», %d dimensiones, normalizados" % (info["modelo_embeddings"], info["dimension"]), VERDE),
            ("Indice\nFAISS IndexFlatIP (exacto, = coseno) + BM25 de palabras. Opcional: pgvector HNSW + tsvector", VERDE)]
    x0, w, g = 0.015, 0.18, 0.017
    for i, (t, col) in enumerate(paso):
        x = x0 + i * (w + g)
        caja(ax, x, 0.725, w, 0.135, t, col, tam=8.2, envolver=30)
        if i:
            flecha(ax, (x - g, 0.7925), (x, 0.7925))
    fig.text(0.015, 0.665, "CONSULTA (cada pregunta)", fontsize=9.5, color=TINTA_2, fontweight="bold")
    q = [("Pregunta del cliente\nsin datos personales en la busqueda", GRIS), ("Expansion de siglas\nTCEA se convierte en «tasa de costo efectivo anual»", NARANJA),
         ("Embedding de la pregunta\nprefijo «search_query:» (distinto del de documento)", VERDE), ("Busqueda\ndensa top-3 (o hibrida con BM25 y RRF) con filtro de modulo", VERDE),
         ("Filtro de relevancia (CRAG)\nsimilitud 0.70 o mas; si ninguno sirve, no contesta", NARANJA)]
    for i, (t, col) in enumerate(q):
        x = x0 + i * (w + g)
        caja(ax, x, 0.50, w, 0.135, t, col, tam=8.2, envolver=30)
        if i:
            flecha(ax, (x - g, 0.5675), (x, 0.5675))
    flecha(ax, (0.9, 0.725), (0.5, 0.64), color=GRIS, estilo=(0, (4, 3)))
    fig.text(0.015, 0.44, "RESPUESTA", fontsize=9.5, color=TINTA_2, fontweight="bold")
    r = [("Fragmentos al prompt\n~%.0f tokens: %.1f %% menos que pegar el corpus (~%.1f millones)" % (3 * chars / len(frags) / 4, pct * 100, chars / 4 / 1e6), AZUL), ("LLM redacta\nsolo con lo recuperado y los datos del cliente; nunca calcula", VERDE),
         ("Verificador\ncada cifra debe venir de una herramienta o de la fuente", NARANJA), ("Respuesta con citas\ntitulo, pagina, enlace y nivel de licencia; «Tu decides»", AZUL),
         ("Si la API cae\nplantilla determinista con la misma fuente", GRIS)]
    for i, (t, col) in enumerate(r):
        x = x0 + i * (w + g)
        caja(ax, x, 0.275, w, 0.135, t, col, tam=8.2, envolver=30)
        if i < 4:
            flecha(ax, (x + w, 0.3425), (x + w + g, 0.3425))
    flecha(ax, (x0 + 4 * (w + g) + w / 2, 0.50), (x0 + w / 2, 0.41), color=NARANJA)
    fig.text(0.015, 0.225, "APRENDIZAJE (menos tokens)", fontsize=9.5, color=TINTA_2, fontweight="bold")
    caja(ax, 0.015, 0.075, 0.30, 0.125, "Preguntas frecuentes\nuna respuesta verificada se guarda (SQLite o Postgres) y se reutiliza sin LLM: 0 tokens", VERDE, tam=8.2, relleno="#f3faf8")
    caja(ax, 0.345, 0.075, 0.30, 0.125, "Exportacion a embeddings\nJSONL listo para vectorizar con el mismo modelo y buscar preguntas por significado", AZUL, tam=8.2)
    caja(ax, 0.675, 0.075, 0.31, 0.125, "Lo que las fuentes no responden\nse cuenta para saber que documentos agregar al RAG", NARANJA, tam=8.2)
    flecha(ax, (0.315, 0.1375), (0.345, 0.1375))
    flecha(ax, (0.645, 0.1375), (0.675, 0.1375))
    pie = ("Validado (eval/validar_rag.py): %d fragmentos = %d vectores, re-embeber una muestra da el mismo vector (coseno minimo %.4f), %d duplicados, cada fragmento se recupera a si mismo (%.0f %% en los 3 primeros). "
             "Recall@4 con filtro de modulo: %.3f en 34 preguntas. Datos sinteticos y fuentes oficiales." % (val["embeddings"]["fragmentos"], val["embeddings"]["vectores"], val["embeddings"]["reembebido_con_prefijo_de_documento"]["coseno_minimo"],
                                                                                                          val["chunks"]["duplicados_exactos"], 100 * val["autorrecuperacion"]["el_fragmento_esta_en_los_3_primeros"], mejor["recall@4"]))
    fig.text(0.015, 0.035, chr(10).join(textwrap.wrap(pie, 175)), fontsize=8, color=TINTA_2, va="center")
    return guardar(fig, D, "rag_arquitectura.png")


def modelo_de_datos_diagrama() -> str:
    import importlib.util
    spec = importlib.util.spec_from_file_location("cargar_a_postgres", os.path.join(RAIZ, "eval", "cargar_a_postgres.py"))
    carga = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(carga)
    filas = dict(carga.plan())
    val = json.load(open(os.path.join(RAIZ, "docs", "modelo_de_datos", "validacion_postgres.json"), encoding="utf-8"))

    def n(t):
        v = filas.get(t)
        return "" if v is None else f"\n{v / 1e6:.1f} M filas" if v >= 1e6 else f"\n{v:,} filas"
    fig, ax = plt.subplots(figsize=(13.5, 8.4), dpi=200, facecolor=SUPERFICIE)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])   # los ejes ocupan toda la figura: las coordenadas de cajas y textos coinciden
    fig.text(0.015, 0.975, "Modelo de datos de Lucas en PostgreSQL con pgvector: 25 tablas", fontsize=15, fontweight="bold", color=TINTA, va="top")
    fig.text(0.015, 0.94, "Esquema lucas (lo que usa el aplicativo) y esquema simulacion (la verdad oculta del simulador, que se borra con datos reales). Todo lo de un cliente se borra con el (derecho de supresion).", fontsize=10, color=TINTA_2, va="top")
    caja(ax, 0.40, 0.55, 0.20, 0.10, "lucas.cliente\ncustomer_id (clave)" + n("lucas.cliente"), AZUL, tam=9, negrita=True)
    hijos_datos = [("lucas.transaccion", 0.03, 0.80), ("lucas.saldo_diario", 0.215, 0.80), ("lucas.panel_mensual", 0.40, 0.80), ("lucas.mensaje", 0.585, 0.80)]
    for t, x, y in hijos_datos:
        caja(ax, x, y, 0.165, 0.08, t + n(t), AZUL, tam=8.2, envolver=34)
        flecha(ax, (x + 0.0825, y), (0.5, 0.65), rad=0.0)
    fig.text(0.03, 0.905, "Datos del cliente (sinteticos hoy, reales manana)", fontsize=9, color=TINTA_2, fontweight="bold")
    app = [("lucas.movimiento_vivo", 0.03, 0.34), ("lucas.memoria_cliente", 0.215, 0.34), ("lucas.meta_ahorro", 0.40, 0.34), ("lucas.respuesta_recomendacion", 0.585, 0.34), ("lucas.movimiento_puntos", 0.03, 0.22),
           ("lucas.aviso", 0.215, 0.22), ("lucas.consulta_chat", 0.40, 0.22), ("lucas.pronostico_diario", 0.585, 0.22)]
    for t, x, y in app:
        caja(ax, x, y, 0.17, 0.08, t, VERDE, tam=8, envolver=34)
        flecha(ax, (x + 0.085, y + 0.08), (0.5, 0.55), color=VERDE)
    fig.text(0.03, 0.445, "Lo que guardan el aplicativo y el agente al funcionar", fontsize=9, color=TINTA_2, fontweight="bold")
    sim = [("simulacion.cliente_verdad", 0.785, 0.80), ("simulacion.transaccion_verdad", 0.785, 0.69), ("simulacion.calidad_etiqueta", 0.785, 0.58)]
    for t, x, y in sim:
        caja(ax, x, y, 0.20, 0.08, t + n(t), GRIS, tam=8, envolver=40)
    flecha(ax, (0.785, 0.84), (0.60, 0.62), color=GRIS, estilo=(0, (4, 3)))
    flecha(ax, (0.785, 0.73), (0.115, 0.80), color=GRIS, estilo=(0, (4, 3)), rad=-0.3)
    fig.text(0.785, 0.905, "Verdad oculta (solo evaluar)", fontsize=9, color=TINTA_2, fontweight="bold")
    comp = [("lucas.contexto_diario", 0.79, 0.44), ("lucas.evento", 0.79, 0.35), ("lucas.macro_mensual", 0.79, 0.26)]
    for t, x, y in comp:
        caja(ax, x, y, 0.19, 0.07, t + (n(t).replace("\n", " · ") if t in filas else ""), NARANJA, tam=8)
    fig.text(0.79, 0.525, "Contexto compartido (BCRP, calendario)", fontsize=9, color=TINTA_2, fontweight="bold")
    caja(ax, 0.03, 0.045, 0.18, 0.07, "lucas.rag_fuente\n21 documentos", AZUL, tam=8)
    caja(ax, 0.235, 0.045, 0.27, 0.07, "lucas.rag_fragmento\nvector(768) HNSW + tsvector", AZUL, tam=8)
    flecha(ax, (0.21, 0.08), (0.235, 0.08))
    caja(ax, 0.53, 0.045, 0.24, 0.07, "lucas.faq_* (3 tablas) y faq_embedding\npreguntas frecuentes y vectores", VERDE, tam=8)
    fig.text(0.79, 0.12, "Probado contra %s\ncon pgvector %s: carga completa,\ncascadas, restricciones y busqueda vectorial" % (val["version_de_postgres"].split(" (")[0], val["version_de_pgvector"]), fontsize=8, color=TINTA_2, va="top")
    fig.text(0.015, 0.012, "Esquema: docs/modelo_de_datos/schema_postgres.sql · cargador: eval/cargar_a_postgres.py · datos sinteticos", fontsize=8, color=TINTA_2)
    return guardar(fig, D, "modelo_de_datos.png")


# ------------------------------------------------------------------------------------------------------------------------------------ indice
ARCHIVOS = [  # (ruta relativa a docs/presentacion, que mensaje defiende)
    ("modelos/comparativa_modelos.png", "Panel general: para cada problema, el modelo elegido (azul rayado) frente a sus baselines y alternativas (gris). Por que cada modelo."),
    ("modelos/01_segmentacion.png", "Segmentacion: K-Prototypes recupera los arquetipos reales que K-means y las reglas 2x2 no."),
    ("modelos/02_saldo_30_dias.png", "Pronostico a 30 dias: menos error que el promedio movil y banda al 80 % que de verdad cubre el 80 %."),
    ("modelos/03_alerta_rojo.png", "Alerta de saldo en rojo: mejor PR-AUC que una regla simple (evento raro)."),
    ("modelos/04_dia_de_riesgo.png", "Dia de riesgo: error en dias del modelo frente a las alternativas."),
    ("modelos/05_proyeccion_mensual_error.png", "Proyeccion mensual de ingresos, gastos y neto: error frente a baselines."),
    ("modelos/06_proyeccion_mensual_cobertura.png", "Proyeccion mensual: cobertura de la banda al 80 %."),
    ("modelos/07_glosas.png", "Categoria de cada movimiento (glosa): el modelo supera al diccionario."),
    ("modelos/08_gastos_recurrentes.png", "Gastos fijos y suscripciones duplicadas: periodicidad y monto superan a la regla de tres veces el mismo comercio."),
    ("modelos/09_atipicos.png", "Movimientos atipicos: IsolationForest frente al z-score robusto."),
    ("modelos/10_sentimiento.png", "Sentimiento: en un set independiente el modelo entrenado supera al lexico; el lexico solo parecia bueno con frases de su propio autor. No esta en produccion."),
    ("modelos/11_politica_de_ahorro.png", "Politica de ahorro: Lucas + ahorro automatico evita dias en rojo y forma colchon; apartar a ciegas empeora la caja."),
    ("modelos/12_agente.png", "Arquitectura del agente: agente unico y multiagente miden igual; se usa el mas simple y auditable."),
    ("modelos/13_rag.png", "Recuperacion de fuentes (RAG): recall@4 con filtro de modulo para cada configuracion."),
    ("modelos/14_serie_diaria.png", "Serie diaria del pronostico: mejor que la recta al dia 30 y que el promedio movil, con la banda medida en cada uno de los 30 dias."),
    ("graficas/serie_diaria_cobertura_y_error_por_dia.png", "La banda al 80 % cubre entre 0.79 y 0.86 en los 30 dias; el error es menor que el de las dos lineas base en cada dia."),
    ("graficas/serie_diaria_ejemplo_de_un_cliente.png", "Lo que ve un cliente: su saldo esperado, la banda y el primer dia de riesgo (contrato del endpoint /forecast)."),
    ("graficas/politica_de_ahorro_dias_en_rojo_y_colchon.png", "Impacto: dias en rojo evitados y colchon formado por cada politica, con la prueba de estres del ahorro bloqueado."),
    ("graficas/programa_de_puntos_proyeccion_a_futuro.png", "Rentabilidad del programa de puntos a 5 anios: cuando se paga y con que supuestos (sin piloto, no es una promesa)."),
    ("graficas/segmentacion_eleccion_de_k.png", "Por que 5 segmentos: mayor silueta entre los k con estabilidad suficiente."),
    ("graficas/calendario_laboral_2026_2027.png", "El agente conoce gratificacion y CTS y avisa que la libre disposicion del 100 % de la CTS vence el 31 de diciembre de 2026."),
    ("diagramas/arquitectura_del_sistema.png", "Arquitectura: modelos calculan, el LLM solo redacta, un verificador determinista cuida cada cifra; salvaguardas si el LLM falla."),
    ("diagramas/agente_ahorro_de_tokens.png", "Como optimizamos tokens: un parrafo de consultas, el router, plantillas, preguntas frecuentes y solo lo nuevo al agente de IA con RAG (chunks, embeddings, top-3), con tokens medidos."),
    ("mapa_de_consultas.json", "Los datos de ese ejemplo: intencion y camino de cada consulta, fragmentos que devolvio el RAG y tokens."),
    ("diagramas/rag_arquitectura.png", "RAG de punta a punta: fuentes, troceado 900/120, embeddings nomic-embed-text, indice, consulta con filtro de relevancia, verificador, citas y preguntas frecuentes que ahorran tokens."),
    ("diagramas/modelo_de_datos.png", "Modelo de datos de PostgreSQL con pgvector: 25 tablas en dos esquemas (lucas y simulacion), probado con la data sintetica completa."),
    ("diagramas/grafo_agente_unico.png", "Nodos del agente unico (LangGraph), dibujado desde el grafo real."),
    ("diagramas/grafo_multiagente.png", "Nodos del multiagente (supervisor), dibujado desde el grafo real."),
    ("diagramas/grafo_agente_unico.md", "El mismo grafo en Mermaid (se ve en GitHub); fuente: app.get_graph().draw_mermaid()."),
    ("diagramas/grafo_multiagente.md", "El mismo grafo del multiagente en Mermaid."),
    ("mlflow_resumen.md", "Seguimiento con MLflow: cada comparacion (baseline frente a elegido) como corrida y cada modelo de produccion registrado con alias produccion."),
]


def escribir_indice() -> None:
    filas = "\n".join(f"| `{r}` | {m} |" for r, m in ARCHIVOS)
    txt = ("# Presentacion y documentacion: graficas y diagramas\n\n"
           "Esta carpeta reune **todas las graficas, diagramas y artefactos generados** para la presentacion final y para la documentacion que pidan los organizadores. "
           "Nada esta dibujado a mano: salen de `models/*.json` y de los grafos reales del agente. Se regeneran con `python eval/comparativa_modelos.py` (modelos) y `python eval/construir_presentacion.py` (el resto).\n\n"
           "**Como usarlas en la presentacion:** una imagen por diapositiva; el titulo de cada grafica ya dice el mensaje. En las de modelos, azul rayado = el modelo elegido y gris = su baseline o alternativa descartada: "
           "es la respuesta a «por que este modelo». Todo es con datos sinteticos y lo dice en el pie de cada imagen.\n\n"
           "| Archivo | Que mensaje defiende |\n|---|---|\n" + filas + "\n\n"
           "Tablas y explicacion de cada eleccion (con su limite): `docs/comparativa_modelos.md`. Informe completo: `docs/RESUMEN_DIEGO.md`. QA: `docs/QA_ANALITICA.md`.\n")
    with open(os.path.join(SALIDA, "README.md"), "w", encoding="utf-8") as f:
        f.write(txt)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from src.agente_analitico.repositorio import Repositorio
    from src.rag.indice import Buscador
    hechos = [serie_diaria_por_dia(), politicas_de_ahorro(), puntos_a_futuro(), eleccion_de_k(), calendario_laboral(), arquitectura(), rag_arquitectura(), modelo_de_datos_diagrama()]
    repo, b = Repositorio(), Buscador()
    hechos.append(serie_diaria_ejemplo(repo))
    hechos.append(ahorro_de_tokens(b))
    for modo in ("agente_unico", "multiagente"):
        hechos.append(grafo_agente(repo, b, modo))
    escribir_indice()
    print(f"{len(hechos)} figuras nuevas + indice en docs/presentacion/")
    for h in hechos:
        print("  ", h)


if __name__ == "__main__":
    main()
