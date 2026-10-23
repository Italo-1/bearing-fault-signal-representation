"""P7 - analisis anadidos en la revision editorial (envio 14195, octubre de 2026).

NO es parte del protocolo original. Son los analisis E1-E5 especificados en la
bitacora de PROTOCOLO.md el 19/10/2026, antes de ejecutar ninguno, en respuesta
a la decision del editor del 19/10. Todo lo que sale de aqui es exploratorio o
de sensibilidad; lo confirmatorio sigue siendo el Friedman principal de 04.

No entrena ningun clasificador. Lee `resultados_por_fold.csv`,
`resultados_por_diametro.csv`, `data/processed/metadatos.csv` y
`manifiesto.json`, y escribe SOLO archivos nuevos con prefijo `rev_` en
`results/tables/`: ninguna tabla existente se toca (sus SHA-256 del 19/10 estan
en `revision_editorial/`).

    E1  modelo mixto con efectos aleatorios cruzados de carga de entrenamiento y
        carga de prueba, con p por bootstrap parametrico de la razon de
        verosimilitudes (D1, punto 1)
    E2  jackknife dejando una carga fuera (D1, puntos 1 y 2)
    E3  F1 por clase y asimetria por direccion de la transferencia (punto 5)
    E4  recall por subgrupo de clase y diametro (punto 7, trazabilidad)
    E5  verificacion de fuga recalculada y tiempos de extraccion (punto 8)
    E7  ablacion con el par como unidad (anadido el 22/10 tras la revision
        adversarial; sensibilidad de la tabla de 04, que usa pliegues)

Con `--ajustado` aplica las mismas funciones (Friedman, caidas, ANOVA bloqueada
y modelo B de E1) a `rev_ajuste_anidado_por_fold.csv`, que escribe
`09_ajuste_anidado.py`, y lo vuelca en `rev_ajuste_anidado_estadistica.csv`.
Ademas escribe dos tablas descriptivas anadidas el 21/10 (no estaban nombradas
en la especificacion del 19/10, no prueban nada): el ajuste al lado de los
valores por defecto (`rev_ajuste_anidado_comparacion.csv`) y las
configuraciones elegidas (`rev_ajuste_anidado_hiperparametros.csv`).

    C:\\lineaB\\.venv\\Scripts\\python.exe src/08_revision_editorial.py
    C:\\lineaB\\.venv\\Scripts\\python.exe src/08_revision_editorial.py --b-bootstrap 10
    C:\\lineaB\\.venv\\Scripts\\python.exe src/08_revision_editorial.py --ajustado
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
import statsmodels.formula.api as smf
from joblib import Parallel, delayed
from statsmodels.formula.api import ols

from fieutils import stats as fstats
from fieutils.config import SEMILLA, configurar_log

RAIZ = Path(__file__).resolve().parent.parent
TABLAS = RAIZ / "results" / "tables"
PROCESADO = RAIZ / "data" / "processed"

CARGAS = [0, 1, 2, 3]
REPRESENTACIONES = ["estadisticos", "fft", "wavelet", "espectrograma"]
CLASIFICADORES = ["SVM-RBF", "RandomForest", "MLP"]
NOMBRES = {
    "estadisticos": "Statistical",
    "fft": "FFT",
    "wavelet": "Wavelet db4",
    "espectrograma": "STFT spectrogram",
}

# El modelo mixto se ajusta sobre F1 x 100 (puntos porcentuales). La razon de
# verosimilitudes no cambia con un reescalado lineal de la respuesta, pero
# statsmodels avisa de "frontera" cuando una varianza baja de 0.01 en valor
# absoluto, y en escala de F1 todas lo hacen. Las varianzas se devuelven en la
# escala original de F1.
ESCALA = 100.0

# Componentes de varianza del modelo mixto (E1). Cada uno es un efecto aleatorio
# con todos sus niveles, y el grupo es unico: el diseno es cruzado, no anidado.
VC_CARGAS = {
    "carga_train": "0 + C(carga_train)",
    "carga_test": "0 + C(carga_test)",
}
VC_REPR = {
    "repr:carga_train": "0 + C(representacion):C(carga_train)",
    "repr:carga_test": "0 + C(representacion):C(carga_test)",
}
VC_CLF = {
    "clf:carga_train": "0 + C(clasificador):C(carga_train)",
    "clf:carga_test": "0 + C(clasificador):C(carga_test)",
}
VC_RC = {
    "rc:carga_train": "0 + C(representacion):C(clasificador):C(carga_train)",
    "rc:carga_test": "0 + C(representacion):C(clasificador):C(carga_test)",
}

# Orden fijo de simplificacion si un modelo no es estimable (bitacora 19/10).
# Modelo A: completo; paso 3, sin las interacciones de la representacion.
# Modelo B: completo; paso 1, sin las del clasificador; paso 2, sin las de R x C.
# Despues del paso 2, R x C queda sin modelo mixto.
PASOS_A = [
    ("completo", {**VC_CARGAS, **VC_REPR}),
    ("paso 3: sin repr x carga", dict(VC_CARGAS)),
]
PASOS_B = [
    ("completo", {**VC_CARGAS, **VC_REPR, **VC_CLF, **VC_RC}),
    ("paso 1: sin clf x carga", {**VC_CARGAS, **VC_REPR, **VC_RC}),
    ("paso 2: sin rc x carga", {**VC_CARGAS, **VC_REPR}),
]

# Avisos de statsmodels que cuentan como "no converge" segun la bitacora del
# 19/10 (Hessiana no definida positiva o fallo del optimizador). "Retrying ...
# with lbfgs" no lo es: es el cambio de optimizador previsto. "The MLE may be on
# the boundary" tampoco: es una varianza estimada en cero, que con 4 niveles se
# espera, y se registra aparte.
AVISOS_FALLO = ("not positive definite", "Gradient optimization failed",
                "MixedLM optimization failed", "singular")
AVISO_FRONTERA = "on the boundary"


def _cargar_preprocess():
    """Importa `02_preprocess.py`, cuyo nombre empieza por digito."""
    ruta = Path(__file__).resolve().parent / "02_preprocess.py"
    spec = importlib.util.spec_from_file_location("preprocess_p7", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# ------------------------------------------------------------------ datos base

def nucleo(r: pd.DataFrame) -> pd.DataFrame:
    return r[(r["en_comparacion"] == True)  # noqa: E712
             & r["representacion"].isin(REPRESENTACIONES)
             & r["clasificador"].isin(CLASIFICADORES)].copy()


def medias_celda(r: pd.DataFrame, cargas: list[int] = CARGAS) -> pd.DataFrame:
    """144 medias (repr x clf x par fuera de diagonal), F1 promediado entre folds."""
    n = nucleo(r)
    n = n[(n["carga_train"] != n["carga_test"])
          & n["carga_train"].isin(cargas) & n["carga_test"].isin(cargas)]
    celdas = (n.groupby(["representacion", "clasificador", "carga_train", "carga_test"])
              ["f1_macro"].mean().reset_index())
    celdas["par"] = celdas["carga_train"].astype(str) + "_" + celdas["carga_test"].astype(str)
    return celdas


def medias_par(celdas: pd.DataFrame) -> pd.DataFrame:
    """48 medias (repr x par): ademas se promedian los tres clasificadores."""
    return (celdas.groupby(["representacion", "carga_train", "carga_test", "par"])
            ["f1_macro"].mean().reset_index())


# ---------------------------------------------------------- E1: modelo mixto

def _ajustar(formula: str, datos: pd.DataFrame, vc: dict, reml: bool):
    """MixedLM con un unico grupo y componentes de varianza cruzados."""
    datos = datos.assign(grupo=1, y=datos["f1_macro"] * ESCALA)
    with warnings.catch_warnings(record=True) as capturados:
        warnings.simplefilter("always")
        modelo = smf.mixedlm(formula, datos, groups="grupo", re_formula="0", vc_formula=vc)
        res = modelo.fit(reml=reml)
    avisos = [str(a.message) for a in capturados]
    fallo = (not res.converged) or any(f in a for a in avisos for f in AVISOS_FALLO)
    frontera = any(AVISO_FRONTERA in a for a in avisos)
    return res, fallo, frontera, avisos


def _varianzas(res) -> dict[str, float]:
    """Varianza de cada componente por nombre: statsmodels los ordena alfabeticamente."""
    return dict(zip(res.model.exog_vc.names, np.asarray(res.vcomp)))


def _matrices_vc(datos: pd.DataFrame, vc: dict) -> dict[str, np.ndarray]:
    return {k: np.asarray(patsy.dmatrix(f, datos, return_type="matrix")) for k, f in vc.items()}


def _replica(y: np.ndarray, datos: pd.DataFrame, f_nula: str, f_alt: str, vc: dict):
    d = datos.assign(f1_macro=y / ESCALA)
    nula, fallo_n, _, _ = _ajustar(f_nula, d, vc, reml=False)
    alt, fallo_a, _, _ = _ajustar(f_alt, d, vc, reml=False)
    if fallo_n or fallo_a:
        return np.nan
    return max(0.0, 2.0 * (alt.llf - nula.llf))


def prueba_lr_bootstrap(datos, f_nula, f_alt, vc, b, log, n_jobs=-1):
    """LR con ML y p por bootstrap parametrico simulando desde el modelo nulo."""
    nula, fallo_n, _, _ = _ajustar(f_nula, datos, vc, reml=False)
    alt, fallo_a, _, _ = _ajustar(f_alt, datos, vc, reml=False)
    if fallo_n or fallo_a:
        return None
    lr = max(0.0, 2.0 * (alt.llf - nula.llf))

    # Simulacion: y* = X beta + sum_k Z_k u_k + e, con u_k ~ N(0, sigma2_k) y
    # e ~ N(0, escala), todo desde el ajuste ML del modelo nulo (en escala x100).
    X = np.asarray(patsy.dmatrix(f_nula.split("~")[1], datos, return_type="matrix"))
    media = X @ np.asarray(nula.fe_params)
    zs = _matrices_vc(datos, vc)
    varianzas = _varianzas(nula)
    rng = np.random.default_rng(SEMILLA)
    simuladas = []
    for _ in range(b):
        y = media + rng.normal(0.0, np.sqrt(nula.scale), len(datos))
        for k in sorted(zs):
            z = zs[k]
            y = y + z @ rng.normal(0.0, np.sqrt(max(varianzas[k], 0.0)), z.shape[1])
        simuladas.append(y)

    marca = time.perf_counter()
    lrs = Parallel(n_jobs=n_jobs)(
        delayed(_replica)(y, datos, f_nula, f_alt, vc) for y in simuladas
    )
    lrs = np.asarray(lrs, dtype=float)
    validas = lrs[~np.isnan(lrs)]
    p = (1 + np.sum(validas >= lr)) / (validas.size + 1)
    log.info(f"  bootstrap: B = {b}, validas = {validas.size}, {time.perf_counter() - marca:.1f} s")
    return {
        "LR": lr, "gl_nominales": int(alt.k_fe - nula.k_fe), "p_bootstrap": p,
        "B": b, "replicas_validas": int(validas.size),
        "p_fiable": bool(validas.size >= 0.9 * b),
        "llf_nula": nula.llf, "llf_alternativa": alt.llf,
    }


def modelo_mixto(datos, nombre, f_nula, f_alt, pasos, b, log):
    """Recorre el orden fijo de simplificacion y prueba con el primer modelo estimable."""
    componentes, fijos, pruebas = [], [], []
    for paso, vc in pasos:
        reml, fallo_reml, frontera, avisos = _ajustar(f_alt, datos, vc, reml=True)
        _, fallo_ml_a, _, avisos_ml = _ajustar(f_alt, datos, vc, reml=False)
        _, fallo_ml_n, _, avisos_nula = _ajustar(f_nula, datos, vc, reml=False)
        log.info(f"Modelo {nombre}, {paso}: fallo REML = {fallo_reml}, fallo ML alternativo = "
                 f"{fallo_ml_a}, fallo ML nulo = {fallo_ml_n}, frontera = {frontera}.")
        for etiqueta, lista in [("REML", avisos), ("ML alternativo", avisos_ml), ("ML nulo", avisos_nula)]:
            for a in sorted(set(lista)):
                log.info(f"  aviso ({etiqueta}): {a}")
        if fallo_reml or fallo_ml_a or fallo_ml_n:
            continue

        for k, var in _varianzas(reml).items():
            componentes.append({"modelo": nombre, "simplificacion": paso, "componente": k,
                                "varianza_reml": var / ESCALA**2})
        componentes.append({"modelo": nombre, "simplificacion": paso, "componente": "residuo",
                            "varianza_reml": reml.scale / ESCALA**2})
        for termino, valor in reml.fe_params.items():
            fijos.append({"modelo": nombre, "simplificacion": paso, "termino": termino,
                          "estimacion_reml": valor / ESCALA,
                          "error_estandar": reml.bse_fe[termino] / ESCALA})

        log.info(f"Modelo {nombre}: estimable en '{paso}'. LR con bootstrap parametrico.")
        prueba = prueba_lr_bootstrap(datos, f_nula, f_alt, vc, b, log)
        if prueba is None:
            continue
        pruebas.append({"modelo": nombre, "simplificacion": paso,
                        "termino": f_alt.split("~")[1].strip(), "nula": f_nula.split("~")[1].strip(),
                        "convergencia": "si", "frontera": frontera, **prueba})
        return componentes, fijos, pruebas

    pruebas.append({"modelo": nombre, "simplificacion": "ninguna estimable",
                    "termino": f_alt.split("~")[1].strip(), "nula": f_nula.split("~")[1].strip(),
                    "convergencia": "no"})
    return componentes, fijos, pruebas


def e1_modelo_mixto(r, b, log, solo_b=False):
    celdas = medias_celda(r)
    pares = medias_par(celdas)
    comp, fij, pru = [], [], []
    if not solo_b:
        log.info("=== E1. Modelo A: efecto de la representacion sobre las 48 medias ===")
        c, f, p = modelo_mixto(pares, "A", "y ~ 1", "y ~ C(representacion)", PASOS_A, b, log)
        comp += c; fij += f; pru += p
    log.info("=== E1. Modelo B: termino R x C sobre las 144 medias ===")
    c, f, p = modelo_mixto(
        celdas, "B", "y ~ C(representacion) + C(clasificador)",
        "y ~ C(representacion) * C(clasificador)", PASOS_B, b, log,
    )
    comp += c; fij += f; pru += p
    return pd.DataFrame(comp), pd.DataFrame(fij), pd.DataFrame(pru)


# ------------------------------------------------------------- E2: jackknife

def friedman_de(tabla_pares: pd.DataFrame) -> fstats.ResultadoFriedman:
    tabla = tabla_pares.pivot(index="par", columns="representacion", values="f1_macro")
    return fstats.friedman_nemenyi(tabla[REPRESENTACIONES].rename(columns=NOMBRES))


def caidas(r: pd.DataFrame, cargas: list[int]) -> dict[str, float]:
    """F1 medio en la diagonal de `cargas` menos F1 medio de sus pares fuera de diagonal."""
    n = nucleo(r)
    salida = {}
    for rep in REPRESENTACIONES:
        sub = n[(n["representacion"] == rep)
                & n["carga_train"].isin(cargas) & n["carga_test"].isin(cargas)]
        dentro = sub[sub["carga_train"] == sub["carga_test"]]["f1_macro"].mean()
        fuera = (sub[sub["carga_train"] != sub["carga_test"]]
                 .groupby(["carga_train", "carga_test"])["f1_macro"].mean().mean())
        salida[rep] = dentro - fuera
    return salida


def anova_bloqueada(celdas: pd.DataFrame) -> pd.Series:
    """El modelo de `07_revision2.py`: par como bloque, R x C fijo."""
    d = celdas.assign(representacion=celdas["representacion"].map(NOMBRES))
    tabla = sm.stats.anova_lm(
        ols("f1_macro ~ C(representacion)*C(clasificador) + C(par)", data=d).fit(), typ=2)
    return tabla.loc["C(representacion):C(clasificador)"]


def resumen_cargas(r: pd.DataFrame, cargas: list[int], etiqueta: str) -> list[dict]:
    """Todo lo que el jackknife recalcula para un subconjunto de cargas."""
    filas = []

    def fila(analisis, nivel, estadistico, valor):
        filas.append({"carga_excluida": etiqueta, "analisis": analisis, "nivel": nivel,
                      "estadistico": estadistico, "valor": valor})

    celdas = medias_celda(r, cargas)
    pares = medias_par(celdas)
    n_pares = pares["par"].nunique()

    principal = friedman_de(pares)
    fila("friedman_principal", "", "N", n_pares)
    fila("friedman_principal", "", "chi2", principal.estadistico)
    fila("friedman_principal", "", "p", principal.p_valor)
    fila("friedman_principal", "", "W_kendall", principal.estadistico / (n_pares * 3))
    for rep, rango in principal.rangos_medios.items():
        fila("friedman_principal", rep, "rango_medio", rango)

    for clf in CLASIFICADORES:
        res = friedman_de(celdas[celdas["clasificador"] == clf])
        fila(f"friedman_{clf}", "", "chi2", res.estadistico)
        fila(f"friedman_{clf}", "", "p", res.p_valor)
        fila(f"friedman_{clf}", "", "p_bonferroni_x3", min(1.0, 3 * res.p_valor))
        fila(f"friedman_{clf}", "", "W_kendall", res.estadistico / (n_pares * 3))
        for rep, rango in res.rangos_medios.items():
            fila(f"friedman_{clf}", rep, "rango_medio", rango)

    rc = anova_bloqueada(celdas)
    fila("anova_bloqueada_RxC", "", "F", rc["F"])
    fila("anova_bloqueada_RxC", "", "gl", rc["df"])
    fila("anova_bloqueada_RxC", "", "p", rc["PR(>F)"])

    for rep, caida in caidas(r, cargas).items():
        fila("caida", NOMBRES[rep], "caida", caida)
    return filas


def comprobar_completo(filas: list[dict], log) -> None:
    """La fila con las 4 cargas debe reproducir lo ya publicado a 4 decimales."""
    d = pd.DataFrame(filas)
    publicado = json.loads((TABLAS / "resumen_estadistico.json").read_text(encoding="utf-8"))
    bloqueada = pd.read_csv(TABLAS / "anova_bloqueada_por_par.csv", index_col=0)
    caidas_pub = pd.read_csv(TABLAS / "caidas_ic_bootstrap.csv").set_index("Representation")

    def valor(analisis, estadistico, nivel=""):
        sel = d[(d["analisis"] == analisis) & (d["estadistico"] == estadistico) & (d["nivel"] == nivel)]
        return float(sel["valor"].iloc[0])

    esperados = [
        ("friedman_principal", "chi2", "", publicado["friedman_principal"]["chi2"]),
        ("friedman_principal", "p", "", publicado["friedman_principal"]["p_valor"]),
        ("anova_bloqueada_RxC", "F", "", bloqueada.loc["C(representacion):C(clasificador)", "F"]),
        ("anova_bloqueada_RxC", "p", "", bloqueada.loc["C(representacion):C(clasificador)", "PR(>F)"]),
    ]
    for rep, rango in publicado["friedman_principal"]["rangos_medios"].items():
        esperados.append(("friedman_principal", "rango_medio", rep, rango))
    for clf, res in publicado["friedman_por_clasificador"].items():
        esperados.append((f"friedman_{clf}", "chi2", "", res["chi2"]))
        esperados.append((f"friedman_{clf}", "p", "", res["p_valor"]))
    for rep, fila in caidas_pub.iterrows():
        esperados.append(("caida", "caida", rep, fila["Drop"]))

    malos = [(a, e, n, v, valor(a, e, n)) for a, e, n, v in esperados
             if round(valor(a, e, n), 4) != round(v, 4)]
    if malos:
        for m in malos:
            log.error(f"No reproduce lo publicado: {m}")
        raise RuntimeError("La fila 'completo' del jackknife no reproduce las tablas publicadas.")
    log.info(f"Fila 'completo': {len(esperados)} valores publicados reproducidos a 4 decimales.")


def criterio_jackknife(filas: list[dict], log) -> list[dict]:
    """Criterio fijado el 19/10: cambia el primer o el ultimo puesto, o el signo
    de la diferencia entre dos caidas."""
    d = pd.DataFrame(filas)
    salida = []

    def extremos(sub):
        orden = sub.sort_values("valor")
        bajo, alto = orden["valor"].iloc[0], orden["valor"].iloc[-1]
        primeros = sorted(orden[orden["valor"] == bajo]["nivel"])
        ultimos = sorted(orden[orden["valor"] == alto]["nivel"])
        return "/".join(primeros), "/".join(ultimos)

    analisis_rangos = ["friedman_principal"] + [f"friedman_{c}" for c in CLASIFICADORES]
    for analisis in analisis_rangos:
        base = d[(d["carga_excluida"] == "ninguna") & (d["analisis"] == analisis)
                 & (d["estadistico"] == "rango_medio")]
        primero_b, ultimo_b = extremos(base)
        for L in CARGAS:
            sub = d[(d["carga_excluida"] == str(L)) & (d["analisis"] == analisis)
                    & (d["estadistico"] == "rango_medio")]
            primero, ultimo = extremos(sub)
            cambia = (primero != primero_b) or (ultimo != ultimo_b)
            salida.append({"carga_excluida": str(L), "analisis": "criterio",
                           "nivel": analisis, "estadistico": "cambia_primero_o_ultimo",
                           "valor": float(cambia)})
            if cambia:
                log.info(f"  {analisis} sin {L} HP: primero {primero_b} -> {primero}, "
                         f"ultimo {ultimo_b} -> {ultimo}.")

    base = d[(d["carga_excluida"] == "ninguna") & (d["analisis"] == "caida")].set_index("nivel")["valor"]
    for L in CARGAS:
        sub = d[(d["carga_excluida"] == str(L)) & (d["analisis"] == "caida")].set_index("nivel")["valor"]
        for a, b in itertools.combinations(base.index, 2):
            cambia = np.sign(base[a] - base[b]) != np.sign(sub[a] - sub[b])
            salida.append({"carga_excluida": str(L), "analisis": "criterio",
                           "nivel": f"{a} - {b}", "estadistico": "cambia_signo_diferencia_caidas",
                           "valor": float(cambia)})
            if cambia:
                log.info(f"  caidas sin {L} HP: cambia el signo de {a} - {b} "
                         f"({base[a] - base[b]:+.4f} -> {sub[a] - sub[b]:+.4f}).")
    return salida


def e2_jackknife(r, log):
    log.info("=== E2. Jackknife dejando una carga fuera ===")
    filas = resumen_cargas(r, CARGAS, "ninguna")
    comprobar_completo(filas, log)
    for L in CARGAS:
        filas += resumen_cargas(r, [c for c in CARGAS if c != L], str(L))
    filas += criterio_jackknife(filas, log)
    largo = pd.DataFrame(filas)

    caidas_ancho = (largo[largo["analisis"] == "caida"]
                    .pivot(index="nivel", columns="carga_excluida", values="valor"))
    caidas_ancho.columns = [f"caida_sin_{c}" if c != "ninguna" else "caida_completo"
                            for c in caidas_ancho.columns]
    sin = caidas_ancho[[f"caida_sin_{L}" for L in CARGAS]]
    caidas_ancho["minimo_jackknife"] = sin.min(axis=1)
    caidas_ancho["maximo_jackknife"] = sin.max(axis=1)
    caidas_ancho.index.name = "representacion"
    return largo, caidas_ancho.reset_index()


# ------------------------------------------------- E3: clase y direccion

def e3_clase_direccion(r, log):
    log.info("=== E3. F1 por clase y asimetria por direccion (descriptivo) ===")
    n = nucleo(r)
    n["f1_sin_Normal"] = n[["f1_IR", "f1_B", "f1_OR"]].mean(axis=1)
    n["en_diagonal"] = n["carga_train"] == n["carga_test"]
    metricas = ["f1_macro", "f1_Normal", "f1_sin_Normal"]

    por_carga = []
    for clf, sub in [("todos", n)] + [(c, n[n["clasificador"] == c]) for c in CLASIFICADORES]:
        g = (sub.groupby(["representacion", "carga_test", "en_diagonal"])[metricas]
             .mean().reset_index())
        g.insert(1, "clasificador", clf)
        g["filas"] = sub.groupby(["representacion", "carga_test", "en_diagonal"]).size().values
        por_carga.append(g)
    por_carga = pd.concat(por_carga, ignore_index=True)

    asim = []
    for clf, sub in [("todos", n)] + [(c, n[n["clasificador"] == c]) for c in CLASIFICADORES]:
        medias = sub.groupby(["representacion", "carga_train", "carga_test"])[metricas].mean()
        for rep in REPRESENTACIONES:
            filas_rep = []
            for i, j in itertools.combinations(CARGAS, 2):
                hacia_menor = medias.loc[(rep, j, i)]
                hacia_mayor = medias.loc[(rep, i, j)]
                fila = {"representacion": rep, "clasificador": clf, "par": f"{i}-{j}"}
                fila.update({f"asimetria_{m}": hacia_menor[m] - hacia_mayor[m] for m in metricas})
                filas_rep.append(fila)
            media = {"representacion": rep, "clasificador": clf, "par": "media"}
            media.update({f"asimetria_{m}": np.mean([f[f"asimetria_{m}"] for f in filas_rep])
                          for m in metricas})
            macro, sin_n = media["asimetria_f1_macro"], media["asimetria_f1_sin_Normal"]
            concentra = abs(sin_n) < 0.5 * abs(macro) and (sin_n == 0 or np.sign(sin_n) == np.sign(macro))
            media["lectura"] = ("se concentra en la clase Normal" if concentra
                                else "no la explica la clase Normal")
            asim += filas_rep + [media]
            if clf == "todos":
                log.info(f"  {rep}: asimetria media F1-macro {macro:+.4f}, sin Normal "
                         f"{sin_n:+.4f}, Normal {media['asimetria_f1_Normal']:+.4f} -> {media['lectura']}.")
    return por_carga, pd.DataFrame(asim)


# --------------------------------------------------- E4: recall por subgrupo

# Cifras del manuscrito enviado el 18/10 (seccion "Performance by fault diameter").
CIFRAS_MANUSCRITO = {
    ("global", "", "Normal", 0.0): 0.994,
    ("global", "", "IR", 0.014): 0.587,
    ("global", "", "B", 0.021): 0.786,
    ("global", "", "IR", 0.021): 0.823,
    ("global", "", "IR", 0.007): 0.832,
    ("global", "", "OR", 0.014): 0.849,
    ("representacion", "fft", "IR", 0.014): 0.836,
    ("representacion", "espectrograma", "IR", 0.014): 0.485,
    ("representacion", "estadisticos", "IR", 0.014): 0.494,
    ("representacion", "wavelet", "IR", 0.014): 0.533,
}


def e4_recall_subgrupo(log):
    log.info("=== E4. Recall por subgrupo (fuera de diagonal, nucleo, sin CNN) ===")
    d = pd.read_csv(TABLAS / "resultados_por_diametro.csv")
    d = d[d["clasificador"].isin(CLASIFICADORES) & d["representacion"].isin(REPRESENTACIONES)
          & (d["carga_train"] != d["carga_test"])].copy()
    d["aciertos"] = d["recall"] * d["n"]

    filas = []
    for nivel, columna in [("global", None), ("representacion", "representacion"),
                           ("clasificador", "clasificador")]:
        claves = ([columna] if columna else []) + ["clase", "diametro_pulg"]
        g = d.groupby(claves).agg(recall_media_simple=("recall", "mean"),
                                  aciertos=("aciertos", "sum"), n_ventanas=("n", "sum"),
                                  filas=("recall", "size")).reset_index()
        g["recall_ponderado_n"] = g["aciertos"] / g["n_ventanas"]
        g.insert(0, "nivel", nivel)
        g.insert(1, "valor_nivel", g[columna] if columna else "")
        filas.append(g.drop(columns=[c for c in [columna, "aciertos"] if c]))
    tabla = pd.concat(filas, ignore_index=True)

    tabla["cifra_manuscrito"] = [
        CIFRAS_MANUSCRITO.get((f.nivel, f.valor_nivel, f.clase, round(f.diametro_pulg, 3)), np.nan)
        for f in tabla.itertuples()
    ]
    con_cifra = tabla.dropna(subset=["cifra_manuscrito"])
    if len(con_cifra) != len(CIFRAS_MANUSCRITO):
        raise RuntimeError("No se encontraron todas las cifras del manuscrito en la tabla.")
    for agregacion in ["recall_media_simple", "recall_ponderado_n"]:
        tabla[f"coincide_{agregacion}"] = np.where(
            tabla["cifra_manuscrito"].isna(), np.nan,
            (tabla[agregacion].round(3) == tabla["cifra_manuscrito"]).astype(float))
        aciertos = int(tabla[f"coincide_{agregacion}"].sum())
        log.info(f"  {agregacion}: reproduce {aciertos} de {len(CIFRAS_MANUSCRITO)} cifras del manuscrito.")
    return tabla


# ---------------------------------------------------------- E5: exportaciones

def contar_solapes(metadatos, indices_celda, ventana, purga: bool) -> pd.DataFrame:
    """Solapes entre entrenamiento y prueba del mismo registro, por celda y fold.

    (a) ventanas de entrenamiento que comparten muestras con el bloque de prueba
        de su registro, con la definicion de `verificar_particion` de 02;
    (b) pares (ventana de entrenamiento, ventana de prueba) que se solapan.
    Sin purga, `purgada` se trata como falso en todas las filas (contrafactual).
    """
    meta = metadatos if purga else metadatos.assign(purgada=False)
    inicio = meta["muestra_inicio"].to_numpy()
    fin = inicio + ventana
    archivo = meta["archivo"].to_numpy()
    filas = []
    for ct in CARGAS:
        for cp in CARGAS:
            for fold in range(5):
                tr, te = indices_celda(meta, ct, cp, fold)
                a = b = 0
                for nombre in set(archivo[tr]) & set(archivo[te]):
                    en_tr = tr[archivo[tr] == nombre]
                    en_te = te[archivo[te] == nombre]
                    envolvente = (inicio[en_tr] < fin[en_te].max()) & (fin[en_tr] > inicio[en_te].min())
                    a += int(envolvente.sum())
                    pares = ((inicio[en_tr][:, None] < fin[en_te][None, :])
                             & (fin[en_tr][:, None] > inicio[en_te][None, :]))
                    b += int(pares.sum())
                filas.append({"carga_train": ct, "carga_test": cp, "fold": fold,
                              "con_purga": purga, "ventanas_train_solapadas": a,
                              "pares_solapados": b})
    return pd.DataFrame(filas)


def e5_exportaciones(log):
    log.info("=== E5. Verificacion de fuga recalculada y tiempos de extraccion ===")
    pre = _cargar_preprocess()
    metadatos = pd.read_csv(PROCESADO / "metadatos.csv")
    fuga = pd.concat([contar_solapes(metadatos, pre.indices_celda, pre.VENTANA, purga)
                      for purga in (True, False)], ignore_index=True)
    totales = fuga.groupby("con_purga")[["ventanas_train_solapadas", "pares_solapados"]].sum()
    log.info(f"  totales sobre las 80 combinaciones celda-fold:\n{totales.to_string()}")
    con = totales.loc[True]
    sin = totales.loc[False]
    if con.sum() != 0:
        raise RuntimeError("Hay solapes con la purga: la particion tiene fuga.")
    medidas_320 = [c for c in totales.columns if sin[c] == 320]
    if medidas_320:
        log.info(f"  El manuscrito dice 320 sin purga: lo reproduce {medidas_320}.")
    else:
        log.warning("  Ninguna medida da 320 sin purga: hay que corregir la frase del manuscrito.")

    manifiesto = json.loads((PROCESADO / "manifiesto.json").read_text(encoding="utf-8"))
    tiempos = pd.DataFrame(
        [{"representacion": k, "segundos_extraccion": v} for k, v in manifiesto["segundos_extraccion"].items()]
    )
    tiempos["fuente"] = "data/processed/manifiesto.json, ultima ejecucion de 02_preprocess.py (no remedido)"
    tiempos["versiones"] = json.dumps(manifiesto["versiones"])
    # Son tiempos de reloj de la maquina que ejecuto 02: no se reproducen en
    # otra corrida, asi que se comparan con los del envio del 18/10 solo como
    # informacion. (Hasta el 21/10 esto era un error y paraba la reproduccion
    # desde cero; el manuscrito revisado ya no cita estos tiempos.)
    enviados = {"espectrograma_vector": 5.96, "fft": 0.27}
    for k, v in enviados.items():
        medido = manifiesto["segundos_extraccion"][k]
        log.info(f"  Tiempo de extraccion de {k}: {medido} s en esta corrida ({v} s en la del envio).")
    return fuga, tiempos


# ------------------------------------------- E7: ablacion con el par como unidad

def e7_ablacion_por_par(r, log):
    """Ablacion de amplitud remuestreando los 12 pares, no los 60 pliegues.

    Anadido el 22/10/2026 tras la revision adversarial (no estaba en la
    especificacion del 19/10): `04_stats.py` calcula el IC y el delta de Cliff
    sobre 60 diferencias por pliegue, como fijo el protocolo, pero los pliegues
    de una celda comparten cuatro quintas partes del entrenamiento. Aqui se
    promedian los 5 pliegues de cada par y se remuestrean los 12 pares. Es una
    sensibilidad de la tabla publicada, no la sustituye.
    """
    log.info("=== E7. Ablacion de amplitud con el par como unidad (sensibilidad) ===")
    ablacion = pd.read_csv(TABLAS / "ablacion_por_fold.csv")
    clave = ["carga_train", "carga_test"]
    filas = []
    for original, normalizada in [("estadisticos", "estadisticos_rmsnorm"), ("fft", "fft_rmsnorm")]:
        for clf in ["SVM-RBF", "RandomForest"]:
            a = (r[(r["representacion"] == original) & (r["clasificador"] == clf)
                   & (r["carga_train"] != r["carga_test"])]
                 .groupby(clave)["f1_macro"].mean().rename("f1_original"))
            b = (ablacion[(ablacion["representacion"] == normalizada) & (ablacion["clasificador"] == clf)]
                 .groupby(clave)["f1_macro"].mean().rename("f1_rmsnorm"))
            par = pd.concat([a, b], axis=1, join="inner")
            if len(par) != 12:
                raise RuntimeError(f"Ablacion {original}/{clf}: {len(par)} pares, se esperaban 12.")
            dif = (par["f1_rmsnorm"] - par["f1_original"]).to_numpy()
            valor, li, ls = fstats.ic_bootstrap(dif, semilla=SEMILLA)
            delta, magnitud = fstats.cliffs_delta(par["f1_rmsnorm"].to_numpy(), par["f1_original"].to_numpy())
            filas.append({"representacion": NOMBRES[original], "clasificador": clf,
                          "diferencia_media": valor, "ic95_inferior": li, "ic95_superior": ls,
                          "delta_cliff": delta, "magnitud": magnitud, "n_pares": len(par)})
            log.info(f"  {original} x {clf}: {valor:+.4f} [{li:+.4f}, {ls:+.4f}], delta {delta:+.3f}")
    return pd.DataFrame(filas)


# ---------------------------------------------------- resultados del ajuste

def estadistica_ajustada(log, b):
    """Las mismas pruebas sobre los resultados de `09_ajuste_anidado.py`."""
    ruta = TABLAS / "rev_ajuste_anidado_por_fold.csv"
    r = pd.read_csv(ruta)
    esperadas = len(REPRESENTACIONES) * len(CLASIFICADORES) * 16 * 5
    presentes = r.groupby(["representacion", "clasificador"]).size()
    log.info(f"{ruta.name}: {len(r)} filas (completo = {esperadas}).\n{presentes.to_string()}")
    completos = [c for c in CLASIFICADORES
                 if all(presentes.get((rep, c), 0) == 80 for rep in REPRESENTACIONES)]
    if completos != CLASIFICADORES:
        raise RuntimeError(f"Ajuste anidado incompleto: solo {completos} completos. Decidir D2-B "
                           "explicitamente antes de analizar; nunca se analiza a medias.")

    filas = resumen_cargas(r, CARGAS, "ninguna")
    salida = pd.DataFrame(filas).drop(columns="carga_excluida")
    salida.insert(0, "fuente", "ajuste_anidado")
    for f in salida[salida["estadistico"].isin(["chi2", "p", "p_bonferroni_x3", "F"])].itertuples():
        log.info(f"  {f.analisis} {f.estadistico} = {f.valor:.4g}")
    for f in salida[salida["estadistico"] == "rango_medio"].itertuples():
        log.info(f"  {f.analisis} rango medio {f.nivel} = {f.valor:.3f}")

    comp, fij, pru = e1_modelo_mixto(r, b, log, solo_b=True)
    extra = []
    for f in pru.to_dict("records"):
        for k in ["LR", "p_bootstrap", "B", "replicas_validas"]:
            if k in f:
                extra.append({"fuente": "ajuste_anidado", "analisis": "modelo_mixto_B_RxC",
                              "nivel": f["simplificacion"], "estadistico": k, "valor": f[k]})
    for f in comp.to_dict("records"):
        extra.append({"fuente": "ajuste_anidado", "analisis": "modelo_mixto_B_componentes",
                      "nivel": f["componente"], "estadistico": "varianza_reml",
                      "valor": f["varianza_reml"]})
    return pd.concat([salida, pd.DataFrame(extra)], ignore_index=True), pru


def resumen_f1(r: pd.DataFrame) -> pd.DataFrame:
    """F1 en la diagonal, fuera de ella (media de los 12 pares) y caida, por repr x clf."""
    n = nucleo(r)
    filas = []
    for (rep, clf), sub in n.groupby(["representacion", "clasificador"]):
        dentro = sub[sub["carga_train"] == sub["carga_test"]]["f1_macro"].mean()
        fuera = (sub[sub["carga_train"] != sub["carga_test"]]
                 .groupby(["carga_train", "carga_test"])["f1_macro"].mean().mean())
        filas.append({"representacion": rep, "clasificador": clf, "f1_dentro": dentro,
                      "f1_fuera": fuera, "caida": dentro - fuera})
    return pd.DataFrame(filas)


def comparacion_defecto(log) -> pd.DataFrame:
    """Valores por defecto (diseno del protocolo) al lado del ajuste anidado. Descriptivo."""
    defecto = resumen_f1(pd.read_csv(TABLAS / "resultados_por_fold.csv"))
    ajustado = resumen_f1(pd.read_csv(TABLAS / "rev_ajuste_anidado_por_fold.csv"))
    tabla = defecto.merge(ajustado, on=["representacion", "clasificador"],
                          suffixes=("_defecto", "_ajustado"), validate="one_to_one")
    for m in ["f1_dentro", "f1_fuera", "caida"]:
        tabla[f"{m}_diferencia"] = tabla[f"{m}_ajustado"] - tabla[f"{m}_defecto"]
    for clf, sub in tabla.groupby("clasificador"):
        orden_d = list(sub.sort_values("f1_fuera_defecto", ascending=False)["representacion"])
        orden_a = list(sub.sort_values("f1_fuera_ajustado", ascending=False)["representacion"])
        log.info(f"  {clf}: orden por F1 fuera de diagonal, defecto {orden_d} -> ajustado {orden_a}")
    return tabla


def hiperparametros_elegidos() -> pd.DataFrame:
    """Cuantas veces se eligio cada configuracion, de los 20 modelos externos por repr x clf."""
    c = pd.read_csv(TABLAS / "rev_ajuste_anidado_configuraciones.csv")
    tabla = (c.groupby(["clasificador", "representacion", "configuracion_elegida"])
             .agg(veces=("fold", "size"),
                  por_maximo=("motivo", lambda m: int((m == "maximo").sum())),
                  por_empate_defecto=("motivo", lambda m: int((m == "empate: por defecto").sum())),
                  por_empate_regularizada=("motivo", lambda m: int((m == "empate: mas regularizada").sum())),
                  f1_interno_medio=("f1_interno_elegida", "mean"))
             .reset_index())
    defecto = {"SVM-RBF": '{"C": 1.0, "factor_gamma": 1.0}',
               "RandomForest": '{"max_features": "sqrt", "min_samples_leaf": 1}',
               "MLP": '{"alpha": 0.0001, "capas": [128, 64]}'}
    tabla["es_por_defecto"] = tabla["configuracion_elegida"] == tabla["clasificador"].map(defecto)
    return tabla.sort_values(["clasificador", "representacion", "veces"], ascending=[True, True, False])


# ---------------------------------------------------------------------- main

def escribir(df: pd.DataFrame, nombre: str, log) -> None:
    ruta = TABLAS / nombre
    if not nombre.startswith("rev_"):
        raise ValueError("08 solo escribe archivos rev_*.")
    df.to_csv(ruta, index=False)
    log.info(f"Escrito {nombre} ({len(df)} filas).")


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("--b-bootstrap", type=int, default=999,
                            help="replicas del bootstrap parametrico (999 en el analisis; 10 para medir)")
    analizador.add_argument("--ajustado", action="store_true",
                            help="analizar rev_ajuste_anidado_por_fold.csv en lugar de los valores por defecto")
    args = analizador.parse_args()

    log = configurar_log("08_revision_editorial" + ("_ajustado" if args.ajustado else ""), RAIZ)
    arranque = time.perf_counter()
    log.info(f"Semilla {SEMILLA}. Bootstrap parametrico con B = {args.b_bootstrap}.")

    if args.ajustado:
        estadistica, _ = estadistica_ajustada(log, args.b_bootstrap)
        escribir(estadistica, "rev_ajuste_anidado_estadistica.csv", log)
        log.info("=== Ajuste anidado frente a los valores por defecto (descriptivo) ===")
        escribir(comparacion_defecto(log), "rev_ajuste_anidado_comparacion.csv", log)
        escribir(hiperparametros_elegidos(), "rev_ajuste_anidado_hiperparametros.csv", log)
        log.info(f"Terminado en {(time.perf_counter() - arranque) / 60:.1f} min.")
        return 0

    r = pd.read_csv(TABLAS / "resultados_por_fold.csv")
    medir = args.b_bootstrap < 999
    sufijo = f"_B{args.b_bootstrap}" if medir else ""

    comp, fij, pru = e1_modelo_mixto(r, args.b_bootstrap, log)
    if medir:
        log.info(f"Modo de medida (B = {args.b_bootstrap}): E1 se escribe con sufijo {sufijo} "
                 "y no se ejecutan E2-E5.")
        escribir(pru, f"rev_modelo_mixto_pruebas{sufijo}.csv", log)
        log.info(f"Terminado en {(time.perf_counter() - arranque) / 60:.1f} min.")
        return 0
    escribir(comp, "rev_modelo_mixto_componentes.csv", log)
    escribir(fij, "rev_modelo_mixto_efectos_fijos.csv", log)
    escribir(pru, "rev_modelo_mixto_pruebas.csv", log)

    largo, caidas_ancho = e2_jackknife(r, log)
    escribir(largo, "rev_jackknife_por_carga.csv", log)
    escribir(caidas_ancho, "rev_jackknife_caidas.csv", log)

    por_carga, asim = e3_clase_direccion(r, log)
    escribir(por_carga, "rev_f1_por_clase_carga_prueba.csv", log)
    escribir(asim, "rev_asimetria_direccion.csv", log)

    escribir(e4_recall_subgrupo(log), "rev_recall_por_subgrupo.csv", log)

    fuga, tiempos = e5_exportaciones(log)
    escribir(fuga, "rev_verificacion_fuga.csv", log)
    escribir(tiempos, "rev_tiempos_extraccion.csv", log)

    escribir(e7_ablacion_por_par(r, log), "rev_ablacion_por_par.csv", log)

    log.info(f"08_revision_editorial.py terminado en {(time.perf_counter() - arranque) / 60:.1f} min.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
