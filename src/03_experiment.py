"""P7 - matriz 4x4 de cargas por representacion y clasificador.

Entrena y evalua. No resume, no interpreta y no dibuja: escribe los resultados
crudos por fold en `results/tables/` y ahi termina. El analisis vive en
`04_stats.py` y las figuras en `05_figures.py`.

Diseno
------
El protocolo describia 4 representaciones x 4 clasificadores, pero ese diseno no
existe: una CNN 2D sobre 6 energias wavelet o 12 estadisticos no tiene sentido,
porque no hay estructura local que convolucionar. El diseno real es:

    Nucleo inferencial   3 clasificadores de vector x 4 representaciones,
                         balanceado, sobre 16 celdas y 5 folds. 960 ajustes.
    Fila de referencia   CNN 2D sobre el espectrograma de 64x64, 16 celdas y
                         5 folds. 80 ajustes. FUERA de la comparacion
                         estadistica: no existe para las otras tres
                         representaciones y un diseno desbalanceado rompe tanto
                         Friedman como el ANOVA.
    Ablacion             estadisticos y FFT sobre ventana normalizada en RMS,
                         con SVM-RBF y Random Forest, solo en las 12 celdas
                         fuera de diagonal. 240 ajustes.

Para que el espectrograma entre en el nucleo se usa su version vectorizada en
rejilla 16x64, es decir 1 024 dimensiones. La rejilla no es cuadrada a
proposito: conserva el eje del tiempo -2.67 ms por columna, entre 2.3 y 3.5
columnas por impacto- y reduce solo el de frecuencia. Una rejilla cuadrada de
la misma dimension (32x32) dejaria 5.33 ms por columna, menos de dos columnas
por periodo BPFI, y borraria el tren de impactos, que es la firma que
`nperseg = 64` existe para resolver. (Corregido el 20/10/2026: decia 10.67 ms,
que corresponde a 16 columnas; ver 02_preprocess.py.)

Particion
---------
`indices_celda` se importa de `02_preprocess.py`, que es donde esta definida. No
se reimplementa aqui: dos definiciones de la particion es una de mas.

Escalado
--------
`StandardScaler` va dentro del pipeline, asi que se ajusta solo con el fold de
entrenamiento. Random Forest no lo lleva porque es invariante a la escala.

    python src/03_experiment.py --parte clasicos    # CPU, horario de trabajo
    python src/03_experiment.py --parte cnn         # GPU, al cerrar el dia
    python src/03_experiment.py --parte ablacion    # CPU
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from tqdm import tqdm

from fieutils.config import SEMILLA, configurar_log, fijar_semilla

RAIZ = Path(__file__).resolve().parent.parent
PROCESADO = RAIZ / "data" / "processed"
TABLAS = RAIZ / "results" / "tables"

CARGAS = [0, 1, 2, 3]
CLASES = ["Normal", "IR", "B", "OR"]
N_FOLDS = 5

# Hiperparametros fijos, declarados y no ajustados: son el diseno del
# protocolo, con valores convencionales identicos en las 16 celdas. El ajuste
# es posible sin fuga, con validacion interna sobre los bloques de
# entrenamiento, y se hizo en la revision editorial (09_ajuste_anidado.py), cuyos
# resultados se reportan junto a estos, no en su lugar. (Corregido el 20/10/2026:
# el argumento anterior, que sacar la validacion del entrenamiento cambiaria el
# tamano de muestra entre celdas, ya se declaro invalido en la ronda 1.)
ARBOLES = 300
CAPAS_MLP = (128, 64)
ITERACIONES_MLP = 500
EPOCAS_CNN = 30
LOTE_CNN = 64
LR_CNN = 1e-3


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

def construir_clasificador(nombre: str):
    """Pipeline listo para ajustar. El escalador se ajusta solo con el train.

    MLPClassifier no tiene `class_weight`, asi que es el unico de los tres que
    no compensa el desbalance de la clase Normal. (Corregido el 22/10/2026: decia
    que tampoco acepta `sample_weight`, pero su `fit` si lo admite en
    scikit-learn 1.9, la version usada; el protocolo lo entrena sin ponderar.) Se
    declara en el manuscrito; la metrica primaria es F1-macro, que ya trata las
    cuatro clases por igual.
    """
    if nombre == "SVM-RBF":
        return Pipeline([
            ("escalado", StandardScaler()),
            ("modelo", SVC(kernel="rbf", gamma="scale", class_weight="balanced",
                           random_state=SEMILLA)),
        ])
    if nombre == "RandomForest":
        return RandomForestClassifier(
            n_estimators=ARBOLES, class_weight="balanced",
            random_state=SEMILLA, n_jobs=-1,
        )
    if nombre == "MLP":
        return Pipeline([
            ("escalado", StandardScaler()),
            ("modelo", MLPClassifier(
                hidden_layer_sizes=CAPAS_MLP, max_iter=ITERACIONES_MLP,
                early_stopping=False, random_state=SEMILLA)),
        ])
    raise ValueError(f"Clasificador desconocido: {nombre}")


# ------------------------------------------------------------------- metricas

def metricas_fold(y_real: np.ndarray, y_pred: np.ndarray) -> dict:
    etiquetas = list(range(len(CLASES)))
    por_clase = f1_score(y_real, y_pred, labels=etiquetas, average=None, zero_division=0)
    fila = {
        "exactitud": accuracy_score(y_real, y_pred),
        "f1_macro": f1_score(y_real, y_pred, labels=etiquetas, average="macro", zero_division=0),
    }
    fila.update({f"f1_{clase}": valor for clase, valor in zip(CLASES, por_clase)})
    return fila


def desglose_diametro(meta_test: pd.DataFrame, y_real, y_pred) -> list[dict]:
    """Acierto por (clase, diametro). Es la covariable guardada en 02.

    Los registros OR de 0.014 pulg y B de 0.021 pulg tienen firma vibratoria
    debil, medida en la verificacion por envolvente. Si el clasificador falla
    ahi, este desglose lo demuestra en lugar de dejarlo como un resultado
    inexplicable en la discusion.
    """
    tabla = meta_test.copy()
    tabla["acierto"] = (np.asarray(y_real) == np.asarray(y_pred))
    filas = []
    for (clase, diametro), grupo in tabla.groupby(["clase", "diametro_pulg"], sort=True):
        filas.append({
            "clase": clase,
            "diametro_pulg": float(diametro),
            "n": int(len(grupo)),
            "recall": float(grupo["acierto"].mean()),
        })
    return filas


# ------------------------------------------------------------ bucle clasico

def correr_clasicos(
    metadatos: pd.DataFrame,
    y: np.ndarray,
    representaciones: dict[str, np.ndarray],
    clasificadores: list[str],
    celdas: list[tuple[int, int]],
    log,
    en_comparacion: bool,
) -> tuple[list[dict], list[dict]]:
    filas, filas_diametro = [], []
    total = len(representaciones) * len(clasificadores) * len(celdas) * N_FOLDS

    barra = tqdm(total=total, desc="ajustes", unit="fit", ncols=80)
    for nombre_repr, X in representaciones.items():
        for nombre_clf in clasificadores:
            for carga_train, carga_test in celdas:
                for fold in range(N_FOLDS):
                    tr, te = indices_celda(metadatos, carga_train, carga_test, fold)

                    modelo = construir_clasificador(nombre_clf)
                    marca = time.perf_counter()
                    modelo.fit(X[tr], y[tr])
                    segundos_ajuste = time.perf_counter() - marca

                    marca = time.perf_counter()
                    y_pred = modelo.predict(X[te])
                    segundos_prediccion = time.perf_counter() - marca

                    comun = {
                        "representacion": nombre_repr,
                        "clasificador": nombre_clf,
                        "carga_train": carga_train,
                        "carga_test": carga_test,
                        "distancia_carga": abs(carga_train - carga_test),
                        "fold": fold,
                    }
                    filas.append({
                        **comun,
                        "n_train": int(tr.size),
                        "n_test": int(te.size),
                        **metricas_fold(y[te], y_pred),
                        "segundos_ajuste": segundos_ajuste,
                        "segundos_prediccion": segundos_prediccion,
                        "en_comparacion": en_comparacion,
                    })
                    for desglose in desglose_diametro(metadatos.iloc[te], y[te], y_pred):
                        filas_diametro.append({**comun, **desglose})

                    barra.update(1)
            log.info(f"{nombre_repr} x {nombre_clf}: {len(celdas) * N_FOLDS} ajustes hechos.")
    barra.close()

    return filas, filas_diametro


# ----------------------------------------------------------------- CNN 2D

def construir_cnn(n_clases: int = 4):
    """CNN 2D pequena sobre espectrogramas de 64x64 en un canal.

    Tres bloques convolucionales con normalizacion por lotes, agrupacion global
    y una capa lineal. Es deliberadamente modesta: con unas 1 200 imagenes de
    entrenamiento por celda, una red mayor memorizaria.
    """
    from torch import nn

    def bloque(entrada, salida):
        return nn.Sequential(
            nn.Conv2d(entrada, salida, 3, padding=1),
            nn.BatchNorm2d(salida),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )

    return nn.Sequential(
        bloque(1, 32), bloque(32, 64), bloque(64, 128),
        nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(128, n_clases),
    )


def entrenar_cnn(X_train, y_train, X_test, dev, log):
    """Entrena un numero fijo de epocas y devuelve las predicciones.

    Sin early stopping a proposito. No hay conjunto de validacion: sacarlo del
    entrenamiento reduciria el tamano de muestra frente a los clasificadores de
    vector y romperia la comparabilidad entre celdas, y usar el bloque de prueba
    para elegir la epoca seria fuga. El numero de epocas es el mismo en las 16
    celdas y se declara.
    """
    import torch
    from torch import nn

    modelo = construir_cnn(len(CLASES)).to(dev)

    conteo = np.bincount(y_train, minlength=len(CLASES)).astype(float)
    pesos = torch.tensor(
        (conteo.sum() / (len(CLASES) * np.maximum(conteo, 1))), dtype=torch.float32, device=dev
    )
    criterio = nn.CrossEntropyLoss(weight=pesos)
    optimizador = torch.optim.Adam(modelo.parameters(), lr=LR_CNN)

    xt = torch.tensor(X_train, dtype=torch.float32, device=dev).unsqueeze(1)
    yt = torch.tensor(y_train, dtype=torch.long, device=dev)
    usar_amp = dev.type == "cuda"
    escalador = torch.amp.GradScaler("cuda", enabled=usar_amp)

    modelo.train()
    for _epoca in range(EPOCAS_CNN):
        orden = torch.randperm(xt.size(0), device=dev)
        for comienzo in range(0, xt.size(0), LOTE_CNN):
            indices = orden[comienzo:comienzo + LOTE_CNN]
            optimizador.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda", enabled=usar_amp):
                perdida = criterio(modelo(xt[indices]), yt[indices])
            escalador.scale(perdida).backward()
            escalador.step(optimizador)
            escalador.update()

    modelo.eval()
    predichas = []
    with torch.no_grad():
        xe = torch.tensor(X_test, dtype=torch.float32, device=dev).unsqueeze(1)
        for comienzo in range(0, xe.size(0), LOTE_CNN):
            with torch.amp.autocast("cuda", enabled=usar_amp):
                salida = modelo(xe[comienzo:comienzo + LOTE_CNN])
            predichas.append(salida.argmax(1).cpu().numpy())

    del modelo, xt, yt
    if dev.type == "cuda":
        torch.cuda.empty_cache()

    return np.concatenate(predichas)


def correr_cnn(metadatos, y, X, celdas, log) -> tuple[list[dict], list[dict]]:
    import torch

    from fieutils.config import dispositivo

    dev = dispositivo(verboso=True)
    filas, filas_diametro = [], []

    barra = tqdm(total=len(celdas) * N_FOLDS, desc="CNN 2D", unit="fit", ncols=80)
    for carga_train, carga_test in celdas:
        for fold in range(N_FOLDS):
            # Se refija la semilla en cada ajuste para que la inicializacion no
            # dependa del orden en que se recorren las celdas.
            fijar_semilla(SEMILLA)
            torch.manual_seed(SEMILLA)

            tr, te = indices_celda(metadatos, carga_train, carga_test, fold)

            marca = time.perf_counter()
            y_pred = entrenar_cnn(X[tr], y[tr], X[te], dev, log)
            segundos = time.perf_counter() - marca

            comun = {
                "representacion": "espectrograma_cnn",
                "clasificador": "CNN2D",
                "carga_train": carga_train,
                "carga_test": carga_test,
                "distancia_carga": abs(carga_train - carga_test),
                "fold": fold,
            }
            filas.append({
                **comun,
                "n_train": int(tr.size),
                "n_test": int(te.size),
                **metricas_fold(y[te], y_pred),
                "segundos_ajuste": segundos,
                "segundos_prediccion": np.nan,
                "en_comparacion": False,
            })
            for desglose in desglose_diametro(metadatos.iloc[te], y[te], y_pred):
                filas_diametro.append({**comun, **desglose})

            barra.update(1)
        log.info(f"CNN celda ({carga_train},{carga_test}): {N_FOLDS} folds hechos.")
    barra.close()

    return filas, filas_diametro


# --------------------------------------------------------------------- salida

def anexar(filas: list[dict], nombre: str, log) -> None:
    """Escribe o amplia un CSV de resultados sin perder lo ya calculado.

    Las tres partes se lanzan por separado -las clasicas en horario de trabajo y
    la CNN al cerrar el dia-, asi que la segunda no puede pisar a la primera.
    Las filas que coincidan en la clave se reemplazan.
    """
    if not filas:
        return
    nuevo = pd.DataFrame(filas)
    ruta = TABLAS / f"{nombre}.csv"

    if ruta.exists():
        previo = pd.read_csv(ruta)
        clave = [c for c in ["representacion", "clasificador", "carga_train",
                             "carga_test", "fold", "clase", "diametro_pulg"]
                 if c in nuevo.columns and c in previo.columns]
        combinado = pd.concat([previo, nuevo], ignore_index=True)
        combinado = combinado.drop_duplicates(subset=clave, keep="last")
    else:
        combinado = nuevo

    combinado.to_csv(ruta, index=False)
    log.info(f"{ruta.name}: {len(combinado)} filas ({len(nuevo)} nuevas o actualizadas).")


# ----------------------------------------------------------------------- main

def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument(
        "--parte", choices=["clasicos", "cnn", "ablacion", "todo"], default="todo",
        help="clasicos y ablacion van en CPU; cnn ocupa la GPU y se lanza al cerrar el dia.",
    )
    args = analizador.parse_args()

    fijar_semilla()
    TABLAS.mkdir(parents=True, exist_ok=True)
    log = configurar_log(f"03_experiment_{args.parte}", RAIZ)
    arranque = time.perf_counter()

    metadatos = pd.read_csv(PROCESADO / "metadatos.csv")
    manifiesto = json.loads((PROCESADO / "manifiesto.json").read_text(encoding="utf-8"))
    if manifiesto["semilla"] != SEMILLA:
        raise RuntimeError("El preprocesado se genero con otra semilla.")

    y = metadatos["clase"].map({c: i for i, c in enumerate(CLASES)}).to_numpy()
    if np.isnan(y.astype(float)).any():
        raise ValueError("Hay clases en metadatos.csv fuera de CLASES.")

    celdas_todas = [(i, j) for i in CARGAS for j in CARGAS]
    celdas_fuera = [(i, j) for i, j in celdas_todas if i != j]

    log.info(
        f"Semilla {SEMILLA}. {len(metadatos)} ventanas, "
        f"{int((~metadatos['purgada']).sum())} utilizables. Parte: {args.parte}."
    )

    if args.parte in ("clasicos", "todo"):
        representaciones = {
            nombre: np.load(PROCESADO / f"X_{archivo}.npy")
            for nombre, archivo in [
                ("estadisticos", "estadisticos"),
                ("fft", "fft"),
                ("wavelet", "wavelet"),
                ("espectrograma", "espectrograma_vector"),
            ]
        }
        representaciones["espectrograma"] = representaciones["espectrograma"].reshape(
            len(metadatos), -1
        )
        log.info("Nucleo inferencial: 4 representaciones x 3 clasificadores x 16 celdas x 5 folds.")
        filas, diametros = correr_clasicos(
            metadatos, y, representaciones,
            ["SVM-RBF", "RandomForest", "MLP"], celdas_todas, log, en_comparacion=True,
        )
        anexar(filas, "resultados_por_fold", log)
        anexar(diametros, "resultados_por_diametro", log)

    if args.parte in ("cnn", "todo"):
        X_cnn = np.load(PROCESADO / "X_espectrograma.npy")
        log.info("Fila de referencia: CNN 2D sobre 64x64, 16 celdas x 5 folds.")
        filas, diametros = correr_cnn(metadatos, y, X_cnn, celdas_todas, log)
        anexar(filas, "resultados_por_fold", log)
        anexar(diametros, "resultados_por_diametro", log)

    if args.parte in ("ablacion", "todo"):
        representaciones = {
            "estadisticos_rmsnorm": np.load(PROCESADO / "X_estadisticos_rmsnorm.npy"),
            "fft_rmsnorm": np.load(PROCESADO / "X_fft_rmsnorm.npy"),
        }
        log.info(
            "Ablacion de amplitud: 2 representaciones x 2 clasificadores x "
            "12 celdas fuera de diagonal x 5 folds."
        )
        filas, _diametros = correr_clasicos(
            metadatos, y, representaciones,
            ["SVM-RBF", "RandomForest"], celdas_fuera, log, en_comparacion=False,
        )
        anexar(filas, "ablacion_por_fold", log)

    log.info(f"Parte '{args.parte}' terminada en {(time.perf_counter() - arranque) / 60:.1f} min.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
