"""P7 - ajuste anidado de hiperparametros (revision editorial, octubre de 2026).

NO es parte del protocolo original. Es el analisis E6 especificado en la
bitacora de PROTOCOLO.md el 19/10/2026, antes de ejecutarlo, durante la revision por
pares. Sus resultados se reportan AL LADO de
los valores por defecto, que siguen siendo el diseno del protocolo.

Diseno
------
Bucle externo: los 240 modelos del nucleo (4 representaciones x 3
clasificadores x 4 cargas de entrenamiento x 5 folds). El conjunto de
entrenamiento de la celda (i, j) en el fold k son los bloques != k de la carga
i, sea cual sea j (`indices_celda` de 02), asi que cada modelo se ajusta una vez
y predice el bloque k de las cuatro cargas de prueba.

Bucle interno, SOLO con datos de entrenamiento: se deja fuera cada uno de los
4 bloques de entrenamiento de la carga i (las ventanas purgadas ya estan
excluidas, y la purga cubre todas las fronteras entre bloques), se entrena con
los otros 3 y se valida con el que queda. Ni la carga de prueba ni el bloque de
prueba intervienen en la eleccion.

Rejillas, criterio y desempate: los de la bitacora del 19/10 (`REJILLAS` y
`elegir`). Todo lo demas, igual que en `03_experiment.py`.

    python src/09_ajuste_anidado.py --por-defecto   # debe reproducir resultados_por_fold.csv
    python src/09_ajuste_anidado.py --humo          # un (carga, fold) por combinacion: mide el tiempo
    python src/09_ajuste_anidado.py                 # corrida completa, incremental y reanudable
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import accuracy_score, f1_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from fieutils.config import SEMILLA, configurar_log, fijar_semilla

RAIZ = Path(__file__).resolve().parent.parent
PROCESADO = RAIZ / "data" / "processed"
TABLAS = RAIZ / "results" / "tables"

CARGAS = [0, 1, 2, 3]
CLASES = ["Normal", "IR", "B", "OR"]
N_FOLDS = 5
REPRESENTACIONES = ["estadisticos", "fft", "wavelet", "espectrograma"]
# El MLP va al final: si hay que pasar a D2-B (bitacora del 19/10), SVM-RBF y
# Random Forest ya estan completos.
CLASIFICADORES = ["SVM-RBF", "RandomForest", "MLP"]

# Lo que no se ajusta, identico a 03_experiment.py.
ARBOLES = 300
ITERACIONES_MLP = 500

# Rejillas fijadas en la bitacora del 19/10, antes de correr. La primera
# configuracion de cada lista NO es especial: la de por defecto se marca aparte.
REJILLAS = {
    "SVM-RBF": [{"C": c, "factor_gamma": g} for c in [0.1, 1.0, 10.0, 100.0] for g in [0.1, 1.0, 10.0]],
    "RandomForest": [{"max_features": m, "min_samples_leaf": h}
                     for m in ["sqrt", "log2", 0.33] for h in [1, 5]],
    "MLP": [{"alpha": a, "capas": c} for a in [1e-4, 1e-2, 1.0] for c in [(128, 64), (64,)]],
}
POR_DEFECTO = {
    "SVM-RBF": {"C": 1.0, "factor_gamma": 1.0},
    "RandomForest": {"max_features": "sqrt", "min_samples_leaf": 1},
    "MLP": {"alpha": 1e-4, "capas": (128, 64)},
}
EMPATE = 0.001

# Pareja (carga de entrenamiento, fold) de la prueba de humo.
HUMO = (1, 0)

# El MLP se ajusta en el proceso principal, sin joblib. Medido el 20/10: con
# los procesos de joblib (BLAS limitado a un hilo) el MLP por defecto difiere de
# 03 en 34 de 320 filas, todas de estadisticos y wavelet, con |dF1| de hasta
# 0.028; en el proceso principal, como en 03, reproduce las 320 exactamente. Su
# resultado depende del numero de hilos de BLAS. SVM-RBF y Random Forest son
# exactos en paralelo.
SECUENCIALES = {"MLP"}


def procesos(nombre: str, n_jobs: int) -> int:
    return 1 if nombre in SECUENCIALES else n_jobs


def _cargar_preprocess():
    """Importa `02_preprocess.py`, cuyo nombre empieza por digito."""
    ruta = Path(__file__).resolve().parent / "02_preprocess.py"
    spec = importlib.util.spec_from_file_location("preprocess_p7", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


PREPROCESS = _cargar_preprocess()
indices_celda = PREPROCESS.indices_celda


# ---------------------------------------------------------------- estimadores

def construir(nombre: str, config: dict, X_train: np.ndarray):
    """El estimador de 03 con los hiperparametros de `config`.

    gamma = factor x s, con s = 1 / (d * Var(X)) sobre los datos ya escalados del
    ajuste, que es lo que calcula `gamma="scale"`. Con factor 1 se pasa "scale"
    tal cual, para que la configuracion por defecto sea identica a la de 03.
    """
    if nombre == "SVM-RBF":
        if config["factor_gamma"] == 1.0:
            gamma = "scale"
        else:
            escalado = StandardScaler().fit_transform(X_train)
            gamma = config["factor_gamma"] / (escalado.shape[1] * escalado.var())
        return Pipeline([
            ("escalado", StandardScaler()),
            ("modelo", SVC(kernel="rbf", C=config["C"], gamma=gamma,
                           class_weight="balanced", random_state=SEMILLA)),
        ])
    if nombre == "RandomForest":
        # n_jobs=1: el paralelismo va por tareas. No cambia el resultado, que con
        # random_state fijo no depende del numero de procesos.
        return RandomForestClassifier(
            n_estimators=ARBOLES, max_features=config["max_features"],
            min_samples_leaf=config["min_samples_leaf"], class_weight="balanced",
            random_state=SEMILLA, n_jobs=1,
        )
    if nombre == "MLP":
        return Pipeline([
            ("escalado", StandardScaler()),
            ("modelo", MLPClassifier(
                hidden_layer_sizes=config["capas"], alpha=config["alpha"],
                max_iter=ITERACIONES_MLP, early_stopping=False, random_state=SEMILLA)),
        ])
    raise ValueError(f"Clasificador desconocido: {nombre}")


def clave_regularizacion(nombre: str, config: dict, d: int) -> tuple:
    """Orden fijo de desempate: la primera es la mas regularizada."""
    if nombre == "SVM-RBF":
        return (config["C"], config["factor_gamma"])
    if nombre == "RandomForest":
        m = config["max_features"]
        efectivas = {"sqrt": int(np.sqrt(d)), "log2": int(np.log2(d))}.get(m) if isinstance(m, str) \
            else int(m * d)
        return (-config["min_samples_leaf"], max(1, efectivas))
    if nombre == "MLP":
        return (-config["alpha"], sum(config["capas"]))
    raise ValueError(nombre)


def texto(config: dict) -> str:
    return json.dumps({k: (list(v) if isinstance(v, tuple) else v) for k, v in config.items()})


def metricas(y_real, y_pred) -> dict:
    etiquetas = list(range(len(CLASES)))
    por_clase = f1_score(y_real, y_pred, labels=etiquetas, average=None, zero_division=0)
    fila = {
        "exactitud": accuracy_score(y_real, y_pred),
        "f1_macro": f1_score(y_real, y_pred, labels=etiquetas, average="macro", zero_division=0),
    }
    fila.update({f"f1_{c}": v for c, v in zip(CLASES, por_clase)})
    return fila


# --------------------------------------------------------------------- tareas

def tarea_interna(nombre, config, X, y, tr_interno, val_interno):
    """Un ajuste del bucle interno: devuelve el F1-macro de validacion."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        modelo = construir(nombre, config, X[tr_interno])
        modelo.fit(X[tr_interno], y[tr_interno])
    no_converge = (nombre == "MLP"
                   and modelo.named_steps["modelo"].n_iter_ >= ITERACIONES_MLP)
    pred = modelo.predict(X[val_interno])
    f1 = f1_score(y[val_interno], pred, labels=list(range(len(CLASES))),
                  average="macro", zero_division=0)
    return f1, no_converge


def tarea_final(nombre, config, X, y, tr, pruebas):
    """Reajuste con los 4 bloques de entrenamiento y prediccion de las 4 cargas."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        modelo = construir(nombre, config, X[tr])
        marca = time.perf_counter()
        modelo.fit(X[tr], y[tr])
        segundos_ajuste = time.perf_counter() - marca
    salida = {}
    for carga_test, te in pruebas.items():
        marca = time.perf_counter()
        pred = modelo.predict(X[te])
        salida[carga_test] = (pred, segundos_ajuste, time.perf_counter() - marca)
    return salida


def particion_interna(metadatos, tr):
    """Los 4 bloques de entrenamiento como validacion interna, dejando uno fuera."""
    bloques = metadatos["bloque"].to_numpy()[tr]
    return [(tr[bloques != b], tr[bloques == b]) for b in sorted(set(bloques))]


def elegir(nombre: str, medias: dict[str, float], configs: dict[str, dict], d: int):
    """El mayor F1 interno; empate (<= 0.001) para la de por defecto o la mas regularizada."""
    mejor = max(medias.values())
    empatadas = [k for k, v in medias.items() if mejor - v <= EMPATE]
    defecto = texto(POR_DEFECTO[nombre])
    if len(empatadas) == 1:
        return empatadas[0], "maximo"
    if defecto in empatadas:
        return defecto, "empate: por defecto"
    elegida = min(empatadas, key=lambda k: clave_regularizacion(nombre, configs[k], d))
    return elegida, "empate: mas regularizada"


# ------------------------------------------------------------------ corridas

def externos(metadatos, solo_humo: bool):
    pares = [HUMO] if solo_humo else [(c, f) for c in CARGAS for f in range(N_FOLDS)]
    for carga_train, fold in pares:
        tr, _ = indices_celda(metadatos, carga_train, carga_train, fold)
        pruebas = {cp: indices_celda(metadatos, carga_train, cp, fold)[1] for cp in CARGAS}
        yield carga_train, fold, tr, pruebas


def filas_resultado(rep, nombre, carga_train, fold, tr, pruebas, predicciones, y, extra):
    filas = []
    for carga_test, te in pruebas.items():
        pred, seg_ajuste, seg_pred = predicciones[carga_test]
        filas.append({
            "representacion": rep, "clasificador": nombre,
            "carga_train": carga_train, "carga_test": carga_test,
            "distancia_carga": abs(carga_train - carga_test), "fold": fold,
            "n_train": int(tr.size), "n_test": int(te.size),
            **metricas(y[te], pred),
            "segundos_ajuste": seg_ajuste, "segundos_prediccion": seg_pred,
            "en_comparacion": True, **extra,
        })
    return filas


def anidado(rep, nombre, X, y, metadatos, solo_humo, n_jobs, log):
    """Bucle interno completo y reajuste final para una (representacion, clasificador)."""
    configs = {texto(c): c for c in REJILLAS[nombre]}
    lista_ext = list(externos(metadatos, solo_humo))

    tareas, claves = [], []
    for carga_train, fold, tr, _ in lista_ext:
        for k_conf, conf in configs.items():
            for i, (tr_i, val_i) in enumerate(particion_interna(metadatos, tr)):
                tareas.append(delayed(tarea_interna)(nombre, conf, X, y, tr_i, val_i))
                claves.append((carga_train, fold, k_conf, i))
    marca = time.perf_counter()
    internos = Parallel(n_jobs=procesos(nombre, n_jobs))(tareas)
    seg_internos = time.perf_counter() - marca

    validacion = pd.DataFrame(
        [{"representacion": rep, "clasificador": nombre, "carga_train": ct, "fold": f,
          "configuracion": k, "bloque_validacion": i, "f1_interno": f1, "mlp_no_converge": nc}
         for (ct, f, k, i), (f1, nc) in zip(claves, internos)]
    )
    resumen_val = (validacion.groupby(["representacion", "clasificador", "carga_train", "fold",
                                       "configuracion"])
                   .agg(f1_interno_medio=("f1_interno", "mean"),
                        f1_interno_desviacion=("f1_interno", "std"),
                        mlp_no_converge=("mlp_no_converge", "sum")).reset_index())

    elecciones, finales = [], []
    for carga_train, fold, tr, pruebas in lista_ext:
        sub = resumen_val[(resumen_val["carga_train"] == carga_train) & (resumen_val["fold"] == fold)]
        medias = dict(zip(sub["configuracion"], sub["f1_interno_medio"]))
        elegida, motivo = elegir(nombre, medias, configs, X.shape[1])
        elecciones.append({"representacion": rep, "clasificador": nombre, "carga_train": carga_train,
                           "fold": fold, "configuracion_elegida": elegida, "motivo": motivo,
                           "f1_interno_elegida": medias[elegida],
                           "f1_interno_por_defecto": medias[texto(POR_DEFECTO[nombre])],
                           "configuraciones_empatadas": int(sum(
                               max(medias.values()) - v <= EMPATE for v in medias.values()))})
        finales.append(delayed(tarea_final)(nombre, configs[elegida], X, y, tr, pruebas))
    marca = time.perf_counter()
    predicciones = Parallel(n_jobs=procesos(nombre, n_jobs))(finales)
    seg_finales = time.perf_counter() - marca

    filas = []
    for (carga_train, fold, tr, pruebas), pred, elec in zip(lista_ext, predicciones, elecciones):
        filas += filas_resultado(rep, nombre, carga_train, fold, tr, pruebas, pred, y, {
            "configuracion_elegida": elec["configuracion_elegida"], "motivo": elec["motivo"],
            "f1_interno_elegida": elec["f1_interno_elegida"],
        })
    log.info(f"{rep} x {nombre}: {len(tareas)} ajustes internos en {seg_internos:.1f} s, "
             f"{len(finales)} reajustes en {seg_finales:.1f} s.")
    return pd.DataFrame(filas), resumen_val, pd.DataFrame(elecciones), seg_internos + seg_finales


def por_defecto(rep, nombre, X, y, metadatos, n_jobs):
    """Configuracion por defecto, sin bucle interno: debe reproducir 03 exactamente."""
    lista_ext = list(externos(metadatos, solo_humo=False))
    predicciones = Parallel(n_jobs=procesos(nombre, n_jobs))(
        delayed(tarea_final)(nombre, POR_DEFECTO[nombre], X, y, tr, pruebas)
        for _, _, tr, pruebas in lista_ext
    )
    filas = []
    for (carga_train, fold, tr, pruebas), pred in zip(lista_ext, predicciones):
        filas += filas_resultado(rep, nombre, carga_train, fold, tr, pruebas, pred, y, {})
    return pd.DataFrame(filas)


# ---------------------------------------------------------------- escritura

CLAVE = ["representacion", "clasificador", "carga_train", "carga_test", "fold"]


def anexar(df: pd.DataFrame, nombre: str, clave: list[str], log) -> None:
    """Escritura incremental: las filas que coinciden en la clave se reemplazan."""
    if not nombre.startswith("rev_"):
        raise ValueError("09 solo escribe archivos rev_*.")
    ruta = TABLAS / nombre
    if ruta.exists():
        previo = pd.read_csv(ruta)
        df = pd.concat([previo, df], ignore_index=True).drop_duplicates(subset=clave, keep="last")
    df.to_csv(ruta, index=False)
    log.info(f"{nombre}: {len(df)} filas.")


def hechas() -> set[tuple[str, str]]:
    ruta = TABLAS / "rev_ajuste_anidado_por_fold.csv"
    if not ruta.exists():
        return set()
    r = pd.read_csv(ruta)
    cuenta = r.groupby(["representacion", "clasificador"]).size()
    return {k for k, v in cuenta.items() if v == len(CARGAS) * len(CARGAS) * N_FOLDS}


# ----------------------------------------------------------------------- main

def cargar_representaciones(n: int) -> dict[str, np.ndarray]:
    archivos = {"estadisticos": "estadisticos", "fft": "fft", "wavelet": "wavelet",
                "espectrograma": "espectrograma_vector"}
    return {rep: np.load(PROCESADO / f"X_{a}.npy").reshape(n, -1) for rep, a in archivos.items()}


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    modo = analizador.add_mutually_exclusive_group()
    modo.add_argument("--por-defecto", action="store_true")
    modo.add_argument("--humo", action="store_true")
    analizador.add_argument("--clasificadores", nargs="+", default=CLASIFICADORES,
                            choices=CLASIFICADORES)
    analizador.add_argument("--n-jobs", type=int, default=-1)
    args = analizador.parse_args()

    sufijo = "_defecto" if args.por_defecto else ("_humo" if args.humo else "")
    fijar_semilla()
    log = configurar_log(f"09_ajuste_anidado{sufijo}", RAIZ)
    arranque = time.perf_counter()

    metadatos = pd.read_csv(PROCESADO / "metadatos.csv")
    manifiesto = json.loads((PROCESADO / "manifiesto.json").read_text(encoding="utf-8"))
    if manifiesto["semilla"] != SEMILLA:
        raise RuntimeError("El preprocesado se genero con otra semilla.")
    y = metadatos["clase"].map({c: i for i, c in enumerate(CLASES)}).to_numpy()
    representaciones = cargar_representaciones(len(metadatos))
    combinaciones = [(rep, clf) for clf in args.clasificadores for rep in REPRESENTACIONES]
    log.info(f"Semilla {SEMILLA}. Modo {sufijo or 'completo'}. {len(combinaciones)} combinaciones.")

    if args.por_defecto:
        original = pd.read_csv(TABLAS / "resultados_por_fold.csv")
        comparaciones = []
        for rep, clf in combinaciones:
            nuevo = por_defecto(rep, clf, representaciones[rep], y, metadatos, args.n_jobs)
            unido = nuevo[CLAVE + ["f1_macro"]].merge(
                original[CLAVE + ["f1_macro"]], on=CLAVE, suffixes=("_reorganizado", "_original"),
                how="left", validate="one_to_one")
            unido["diferencia"] = unido["f1_macro_reorganizado"] - unido["f1_macro_original"]
            maxima = unido["diferencia"].abs().max()
            log.info(f"{rep} x {clf}: {len(unido)} filas, |diferencia| maxima = {maxima:.3g}.")
            comparaciones.append(unido)
        tabla = pd.concat(comparaciones, ignore_index=True)
        tabla["reproduce"] = tabla["diferencia"].abs() <= 1e-9
        anexar(tabla, "rev_ajuste_anidado_verificacion_defecto.csv", CLAVE, log)
        fallan = int((~tabla["reproduce"]).sum())
        log.info(f"Verificacion por defecto: {len(tabla) - fallan} de {len(tabla)} filas reproducen "
                 f"03 con |diferencia| <= 1e-9.")
        log.info(f"Terminado en {(time.perf_counter() - arranque) / 60:.1f} min.")
        return 0 if fallan == 0 else 1

    if args.humo:
        tiempos = {}
        for rep, clf in combinaciones:
            *_, segundos = anidado(rep, clf, representaciones[rep], y, metadatos, True, args.n_jobs, log)
            tiempos[(rep, clf)] = segundos
        total = sum(tiempos.values()) * len(CARGAS) * N_FOLDS
        log.info("Prueba de humo: un (carga, fold) de 20 por combinacion, en paralelo como la corrida.")
        for (rep, clf), s in tiempos.items():
            log.info(f"  {rep} x {clf}: {s:.1f} s -> proyeccion x20 = {s * 20 / 60:.1f} min")
        por_clf = {c: sum(s for (r, k), s in tiempos.items() if k == c) * 20 / 3600 for c in args.clasificadores}
        log.info(f"Proyeccion por clasificador (h): { {k: round(v, 2) for k, v in por_clf.items()} }")
        log.info(f"Proyeccion total: {total / 3600:.2f} h (umbral de D2-B: 8 h).")
        return 0

    ya = hechas()
    for rep, clf in combinaciones:
        if (rep, clf) in ya:
            log.info(f"{rep} x {clf}: ya completa en rev_ajuste_anidado_por_fold.csv, se salta.")
            continue
        filas, validacion, elecciones, _ = anidado(
            rep, clf, representaciones[rep], y, metadatos, False, args.n_jobs, log)
        # Validacion y elecciones antes que los resultados: una combinacion solo
        # cuenta como hecha cuando sus 80 filas de resultados estan escritas.
        anexar(validacion, "rev_ajuste_anidado_validacion_interna.csv",
               ["representacion", "clasificador", "carga_train", "fold", "configuracion"], log)
        anexar(elecciones, "rev_ajuste_anidado_configuraciones.csv",
               ["representacion", "clasificador", "carga_train", "fold"], log)
        anexar(filas, "rev_ajuste_anidado_por_fold.csv", CLAVE, log)
        log.info(f"Acumulado: {(time.perf_counter() - arranque) / 60:.1f} min.")

    log.info(f"Ajuste anidado terminado en {(time.perf_counter() - arranque) / 60:.1f} min.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
