"""P7 - segmentado, particion y las cuatro representaciones de senal.

Convierte los 40 registros crudos de CWRU en ventanas etiquetadas mas las
matrices de caracteristicas que consume `03_experiment.py`. No entrena nada y no
estandariza nada: el escalado se ajusta dentro del pipeline de 03, solo sobre el
fold de entrenamiento.

Tres decisiones gobiernan este script y las tres estan justificadas en el README.

1. SELECCION DE CANAL ANCLADA AL NUMERO DE ARCHIVO. `99.mat` trae dos registros
   y el criterio habitual -la primera clave terminada en _DE_time- devuelve el
   equivocado, con lo que la senal de 1 HP quedaria etiquetada como 2 HP. Como
   la carga es el eje del experimento, el error desplazaria una columna entera
   de la matriz 4x4 sin producir ninguna senal de alarma.

2. PARTICION POR BLOQUES CONTIGUOS PURGADOS. Las ventanas de un registro llevan
   50 % de solape y repartirlas al azar entre entrenamiento y prueba infla el
   resultado. Fuera de la diagonal la separacion es por registro de origen, que
   es lo que exige el protocolo. En la diagonal no puede serlo: CWRU aporta un
   unico registro sano por carga, asi que Normal no admite division por
   registro. Se adopta una regla unica para las 16 celdas: cinco bloques
   contiguos por registro, descartando la ventana frontera de cada bloque
   interno. Con paso 1024 y ventana 2048, descartar una sola ventana basta para
   que dos bloques distintos no compartan ni una muestra. La diagonal queda como
   referencia declarada y no entra en la inferencia, que se limita a los 12
   pares fuera de diagonal.

3. EL DIAMETRO DE FALLA SE GUARDA COMO COVARIABLE. Los registros OR de 0.014" y
   B de 0.021" tienen firma vibratoria debil, medida en la verificacion por
   envolvente del 22/08. Si el clasificador falla ahi, la explicacion ya esta
   documentada y se puede desglosar el resultado en lugar de improvisar en la
   discusion.

Ablacion de normalizacion de amplitud
-------------------------------------
El espectrograma se normaliza por imagen a [0, 1] y la wavelet devuelve energia
relativa: las dos son invariantes a la amplitud POR CONSTRUCCION. Los
estadisticos temporales y la magnitud FFT conservan la escala absoluta, que es
justo lo que escala con la carga. Comparar los cuatro tal cual confirmaria la
hipotesis por el preprocesado y no por la representacion. Este script genera
ademas las dos representaciones dependientes de amplitud calculadas sobre la
ventana normalizada en RMS, para que 03 pueda separar los dos efectos. El
alcance de la ablacion queda fijado ANTES de ver resultados: SVM-RBF y Random
Forest sobre las 12 celdas fuera de diagonal.

    python src/02_preprocess.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat

from fieutils import signal_repr, tablas
from fieutils.config import SEMILLA, configurar_log, fijar_semilla

RAIZ = Path(__file__).resolve().parent.parent
CRUDO = RAIZ / "data" / "raw"
PROCESADO = RAIZ / "data" / "processed"
TABLAS = RAIZ / "results" / "tables"

# Parametros del protocolo. Cualquier cambio aqui obliga a regenerar todo y a
# anotarlo con fecha en la bitacora del README.
FS = 12_000.0
VENTANA = 2048
SOLAPE = 0.5
PASO = int(VENTANA * (1.0 - SOLAPE))
N_BLOQUES = 5
NIVELES_WAVELET = 5

# nperseg fija la resolucion en frecuencia (fs/nperseg) y, por el mismo
# compromiso, la resolucion en tiempo. Se elige 64 a proposito y se pasa de
# forma explicita: en una senal de rodamiento la falla no produce un pico
# espectral en BPFO ni BPFI, sino que excita la resonancia estructural de
# 2-5.5 kHz, y la frecuencia caracteristica aparece como la TASA DE REPETICION
# de esos impactos, en el eje del tiempo. Con nperseg = 64 el salto entre tramas
# es de 2.67 ms y los impactos ocurren cada 6.2 ms (BPFI) a 9.3 ms (BPFO): el
# tren de impactos queda resuelto. Con nperseg = 512 se ganarian 23.4 Hz por bin
# pero quedarian 7 tramas con saltos de 21 ms, que borrarian la firma.
NPERSEG_STFT = 64

# Dos rejillas a partir de la MISMA STFT. La rejilla solo fija el tamano de la
# imagen; no crea ni destruye resolucion espectral, que la fija nperseg.
TAMANO_ESPECTROGRAMA = 64  # entrada de la CNN 2D, cuadrada

# Rejilla (frecuencias, tramas) de la version vectorizada que entra en el nucleo
# inferencial. NO es cuadrada, y el motivo esta medido: la STFT nativa es de
# 33x63, de modo que 64 columnas conservan el eje temporal intacto -2.67 ms por
# columna, entre 2.3 y 3.5 columnas por impacto- mientras que una rejilla
# cuadrada de la misma dimension total (32x32) dejaria 5.33 ms por columna,
# menos de dos columnas por periodo BPFI (6.2 ms), y borraria el tren de
# impactos, que es justo la firma que nperseg = 64 existe para resolver.
# (Corregido el 17/10/2026: decia 10.67 ms, que corresponde a 16 columnas.) La frecuencia se reduce a la mitad, 375 Hz, con la resonancia de
# 2-5.5 kHz repartida en unas 9 de las 16 filas. Los 1024 valores resultantes
# quedan ademas junto a los 1025 de la FFT, lo que reduce el confuso de
# dimensionalidad en lugar de agravarlo.
REJILLA_VECTOR = (16, 64)

CARGAS = [0, 1, 2, 3]
CLASES = ["Normal", "IR", "B", "OR"]

# El bucle de la wavelet y el del espectrograma van fila a fila; se trocean solo
# para poder informar del avance y acotar el pico de memoria.
LOTE = 1024


# --------------------------------------------------------------- carga de datos

def leer_canal(ruta: Path) -> np.ndarray:
    """Devuelve el canal DE del registro, anclado al numero de archivo.

    Ver el punto 1 de la cabecera: la seleccion por posicion o por orden
    alfabetico devuelve el canal equivocado en `99.mat`.
    """
    numero = int(ruta.stem)
    contenido = loadmat(ruta)
    esperada = f"X{numero:03d}_DE_time"

    if esperada not in contenido:
        disponibles = [k for k in contenido if k.endswith("_DE_time")]
        raise KeyError(
            f"{ruta.name}: no existe la clave {esperada}. Canales DE presentes: "
            f"{disponibles}. No se continua: seleccionar por posicion es el error "
            f"que este anclaje existe para evitar."
        )

    return np.ravel(contenido[esperada]).astype(np.float64)


def asignar_bloques(n_ventanas: int) -> tuple[np.ndarray, np.ndarray]:
    """Reparte las ventanas de un registro en N_BLOQUES tramos contiguos.

    Devuelve (bloque, purgada). `purgada` marca la primera ventana de cada
    bloque interno, que es la unica que solapa con el bloque anterior: con paso
    1024 y ventana 2048, la ventana m y la m+2 ya no comparten ninguna muestra.
    """
    indices = np.arange(n_ventanas)
    bloque = np.minimum(indices * N_BLOQUES // max(n_ventanas, 1), N_BLOQUES - 1)

    purgada = np.zeros(n_ventanas, dtype=bool)
    purgada[1:] = bloque[1:] != bloque[:-1]
    return bloque, purgada


def construir_ventanas(catalogo: pd.DataFrame, log) -> tuple[np.ndarray, pd.DataFrame]:
    """Segmenta los 40 registros y arma la tabla de metadatos por ventana."""
    trozos, filas = [], []

    for _, fila in catalogo.iterrows():
        senal = leer_canal(CRUDO / fila["archivo"])
        ventanas = signal_repr.segmentar(senal, VENTANA, SOLAPE)
        n = ventanas.shape[0]
        if n == 0:
            raise ValueError(f"{fila['archivo']}: registro mas corto que la ventana.")

        bloque, purgada = asignar_bloques(n)
        trozos.append(ventanas)

        for i in range(n):
            filas.append({
                "archivo": fila["archivo"],
                "clase": fila["clase"],
                "diametro_pulg": fila["diametro_pulg"],
                "carga_hp": int(fila["carga_hp"]),
                "rpm_nominal": int(fila["rpm_aprox"]),
                "indice_ventana": i,
                "muestra_inicio": i * PASO,
                "bloque": int(bloque[i]),
                "purgada": bool(purgada[i]),
            })

        log.info(
            f"{fila['archivo']:>8}  {fila['clase']:<6} {fila['diametro_pulg']:.3f} pulg  "
            f"{fila['carga_hp']} HP  {senal.size:>7} muestras  {n:>4} ventanas  "
            f"({int(purgada.sum())} purgadas)"
        )

    metadatos = pd.DataFrame(filas)
    metadatos.insert(0, "id_ventana", np.arange(len(metadatos)))
    return np.vstack(trozos), metadatos


# ------------------------------------------------------------ representaciones

def por_lotes(funcion, X: np.ndarray, etiqueta: str, log, **kwargs) -> np.ndarray:
    """Aplica una representacion en trozos, informando del avance."""
    salidas, inicio = [], time.perf_counter()
    for comienzo in range(0, X.shape[0], LOTE):
        salidas.append(funcion(X[comienzo:comienzo + LOTE], **kwargs))
        log.info(f"  {etiqueta}: {min(comienzo + LOTE, X.shape[0])}/{X.shape[0]}")
    resultado = np.concatenate(salidas, axis=0).astype(np.float32)
    log.info(f"  {etiqueta}: forma {resultado.shape} en {time.perf_counter() - inicio:.1f} s")
    return resultado


def normalizar_rms(X: np.ndarray) -> np.ndarray:
    """Divide cada ventana por su valor eficaz. Base de la ablacion.

    Tras esto el descriptor `rms` vale exactamente 1 en todas las ventanas y
    `desv_std` queda proxima a 1: la informacion de amplitud desaparece, que es
    precisamente el efecto que la ablacion aisla.
    """
    rms = np.sqrt(np.mean(X**2, axis=1, keepdims=True))
    return np.divide(X, rms, out=np.zeros_like(X), where=rms > 1e-12)


def espectrogramas(ventanas: np.ndarray, tamano: int, etiqueta: str, log):
    """Espectrogramas de un tamano de imagen dado. Devuelve (imagenes, info).

    `info` sale de la propia funcion con `devolver_info=True`, no de una
    reconstruccion aparte: son los parametros efectivos que se vuelcan al
    manifiesto y que el manuscrito tiene que declarar.
    """
    salidas, info, inicio = [], None, time.perf_counter()
    for comienzo in range(0, ventanas.shape[0], LOTE):
        imagenes, info = signal_repr.espectrograma_stft(
            ventanas[comienzo:comienzo + LOTE], fs=FS, tamano=tamano,
            nperseg=NPERSEG_STFT, devolver_info=True,
        )
        salidas.append(imagenes)
        log.info(f"  {etiqueta}: {min(comienzo + LOTE, ventanas.shape[0])}/{ventanas.shape[0]}")

    resultado = np.concatenate(salidas, axis=0).astype(np.float32)
    log.info(f"  {etiqueta}: forma {resultado.shape} en {time.perf_counter() - inicio:.1f} s")
    return resultado, info, time.perf_counter() - inicio


def espectrogramas_rejilla(ventanas: np.ndarray, rejilla: tuple[int, int], etiqueta: str, log):
    """Espectrogramas en una rejilla (frecuencias, tramas) no cuadrada.

    `espectrograma_stft` solo produce imagenes cuadradas, y aqui hace falta
    conservar el eje del tiempo reduciendo el de la frecuencia. El calculo es el
    mismo que hace la libreria -misma STFT, misma escala en dB, misma
    normalizacion por imagen- y se reutiliza su propio remuestreador para que
    las dos versiones del espectrograma salgan de un pipeline identico y solo se
    diferencien en la rejilla de salida.

    Se toca un nombre privado de `fieutils` (`_redimensionar`) a proposito, en
    lugar de copiar el codigo, para que un cambio en la libreria no deje aqui
    una copia divergente. **Peticion anotada para la sesion maestra:** si
    `espectrograma_stft` aceptase `tamano` como tupla, esta funcion sobraria.
    """
    from scipy import signal as sp_signal

    from fieutils.signal_repr import _redimensionar, parametros_stft

    alto, ancho = rejilla
    info = parametros_stft(VENTANA, FS, nperseg=NPERSEG_STFT)
    imagenes, inicio = [], time.perf_counter()

    for indice, fila in enumerate(ventanas):
        _f, _t, Z = sp_signal.stft(
            fila, fs=FS, nperseg=info["nperseg"], noverlap=info["noverlap"]
        )
        magnitud = 20 * np.log10(np.abs(Z) + 1e-12)
        img = _redimensionar(magnitud, alto, ancho)
        rango = img.max() - img.min()
        imagenes.append((img - img.min()) / rango if rango > 1e-12 else np.zeros_like(img))

        if (indice + 1) % LOTE == 0 or indice + 1 == len(ventanas):
            log.info(f"  {etiqueta}: {indice + 1}/{len(ventanas)}")

    resultado = np.array(imagenes).astype(np.float32)
    log.info(f"  {etiqueta}: forma {resultado.shape} en {time.perf_counter() - inicio:.1f} s")
    return resultado, info, time.perf_counter() - inicio


def generar_representaciones(ventanas: np.ndarray, log) -> tuple[dict, dict, dict]:
    """Devuelve (representaciones, info_stft, segundos_por_representacion).

    Los tiempos alimentan la Tabla 2 de costo computacional del manuscrito, que
    suma extraccion mas entrenamiento.
    """
    reps, segundos = {}, {}
    log.info("Representaciones primarias")

    marca = time.perf_counter()
    reps["estadisticos"] = signal_repr.estadisticos_temporales(ventanas).astype(np.float32)
    segundos["estadisticos"] = time.perf_counter() - marca

    marca = time.perf_counter()
    reps["fft"] = signal_repr.magnitud_fft(ventanas).astype(np.float32)
    segundos["fft"] = time.perf_counter() - marca

    marca = time.perf_counter()
    reps["wavelet"] = por_lotes(
        signal_repr.wavelet_db4, ventanas, "wavelet", log,
        niveles=NIVELES_WAVELET, solo_energia=True,
    )
    segundos["wavelet"] = time.perf_counter() - marca

    # Misma STFT, dos rejillas. La cuadrada de 64x64 alimenta la CNN 2D; la de
    # 16x64 (1024 dimensiones) es la que entra en la comparacion estadistica
    # junto a las otras tres representaciones, que son vectores.
    reps["espectrograma"], info, segundos["espectrograma"] = espectrogramas(
        ventanas, TAMANO_ESPECTROGRAMA, "espectrograma 64x64", log
    )
    reps["espectrograma_vector"], info_vector, segundos["espectrograma_vector"] = (
        espectrogramas_rejilla(
            ventanas, REJILLA_VECTOR,
            f"espectrograma {REJILLA_VECTOR[0]}x{REJILLA_VECTOR[1]}", log,
        )
    )
    if info != info_vector:
        raise RuntimeError(
            "Las dos imagenes no salen de la misma STFT: "
            f"{info} frente a {info_vector}. El tamano de imagen no debe alterar "
            "los parametros espectrales."
        )

    log.info(f"  estadisticos: forma {reps['estadisticos'].shape}")
    log.info(f"  fft: forma {reps['fft'].shape}")
    log.info(f"  STFT efectiva: {info}")

    log.info("Representaciones de la ablacion (ventana normalizada en RMS)")
    ventanas_norm = normalizar_rms(ventanas)

    marca = time.perf_counter()
    reps["estadisticos_rmsnorm"] = signal_repr.estadisticos_temporales(ventanas_norm).astype(np.float32)
    segundos["estadisticos_rmsnorm"] = time.perf_counter() - marca

    marca = time.perf_counter()
    reps["fft_rmsnorm"] = signal_repr.magnitud_fft(ventanas_norm).astype(np.float32)
    segundos["fft_rmsnorm"] = time.perf_counter() - marca

    log.info(f"  estadisticos_rmsnorm: forma {reps['estadisticos_rmsnorm'].shape}")
    log.info(f"  fft_rmsnorm: forma {reps['fft_rmsnorm'].shape}")

    return reps, info, segundos


# --------------------------------------------------------------- verificaciones

def indices_celda(metadatos: pd.DataFrame, carga_train: int, carga_test: int, fold: int):
    """Indices de entrenamiento y prueba de una celda de la matriz 4x4.

    Esta funcion es la definicion operativa de la particion y `03_experiment.py`
    debe importarla en lugar de reimplementarla.
    """
    util = ~metadatos["purgada"].values
    train = np.flatnonzero(
        util & (metadatos["carga_hp"].values == carga_train) & (metadatos["bloque"].values != fold)
    )
    test = np.flatnonzero(
        util & (metadatos["carga_hp"].values == carga_test) & (metadatos["bloque"].values == fold)
    )
    return train, test


def verificar_particion(metadatos: pd.DataFrame, log) -> list[str]:
    """Comprueba celda por celda que no hay fuga de informacion entre ventanas.

    La tabla de riesgos del README promete esta verificacion aqui. Se comprueba
    lo que de verdad importa: que ninguna ventana de entrenamiento comparta
    muestras con ninguna ventana de prueba del mismo registro. Fuera de la
    diagonal es trivial porque los archivos son distintos; se comprueba igual,
    porque el coste es nulo y un fallo silencioso ahi arruinaria el articulo.
    """
    errores = []
    inicio = metadatos["muestra_inicio"].values
    fin = inicio + VENTANA
    archivo = metadatos["archivo"].values
    clase = metadatos["clase"].values

    for carga_train in CARGAS:
        for carga_test in CARGAS:
            for fold in range(N_BLOQUES):
                tr, te = indices_celda(metadatos, carga_train, carga_test, fold)

                if tr.size == 0 or te.size == 0:
                    errores.append(
                        f"celda ({carga_train},{carga_test}) fold {fold}: particion vacia."
                    )
                    continue

                faltan_tr = set(CLASES) - set(clase[tr])
                faltan_te = set(CLASES) - set(clase[te])
                if faltan_tr or faltan_te:
                    errores.append(
                        f"celda ({carga_train},{carga_test}) fold {fold}: clases ausentes "
                        f"(train {sorted(faltan_tr)}, test {sorted(faltan_te)})."
                    )

                comunes = set(archivo[tr]) & set(archivo[te])
                if carga_train != carga_test and comunes:
                    errores.append(
                        f"celda ({carga_train},{carga_test}): archivos compartidos entre "
                        f"cargas distintas {sorted(comunes)}. Imposible salvo error de catalogo."
                    )

                # El bloque de prueba es contiguo dentro de cada registro, asi que
                # basta comparar contra su intervalo envolvente.
                for nombre in comunes:
                    en_te = te[archivo[te] == nombre]
                    en_tr = tr[archivo[tr] == nombre]
                    solapa = (inicio[en_tr] < fin[en_te].max()) & (fin[en_tr] > inicio[en_te].min())
                    if solapa.any():
                        errores.append(
                            f"celda ({carga_train},{carga_test}) fold {fold}, {nombre}: "
                            f"{int(solapa.sum())} ventanas de entrenamiento comparten muestras "
                            f"con el bloque de prueba. FUGA."
                        )

    log.info(
        f"Verificacion de particion: {len(CARGAS)**2 * N_BLOQUES} combinaciones "
        f"celda-fold revisadas, {len(errores)} problemas."
    )
    return errores


def verificar_coherencia(ventanas, metadatos, reps, log) -> list[str]:
    errores = []
    if ventanas.shape[0] != len(metadatos):
        errores.append("ventanas y metadatos no tienen el mismo numero de filas.")
    for nombre, matriz in reps.items():
        if matriz.shape[0] != len(metadatos):
            errores.append(f"{nombre}: {matriz.shape[0]} filas frente a {len(metadatos)}.")
        if not np.isfinite(matriz).all():
            errores.append(f"{nombre}: contiene valores no finitos.")

    # Una ventana nunca puede cruzar el limite de su registro.
    for nombre, grupo in metadatos.groupby("archivo"):
        if not np.array_equal(grupo["indice_ventana"].values, np.arange(len(grupo))):
            errores.append(f"{nombre}: los indices de ventana no son consecutivos desde 0.")

    log.info(f"Verificacion de coherencia: {len(errores)} problemas.")
    return errores


# ----------------------------------------------------------------------- salida

def escribir_tablas(metadatos: pd.DataFrame, reps: dict[str, np.ndarray], info_stft: dict) -> None:
    util = metadatos[~metadatos["purgada"]]

    conteo = util.pivot_table(
        index="clase", columns="carga_hp", values="id_ventana", aggfunc="count"
    ).reindex(CLASES)
    conteo.columns = [f"{c} HP" for c in conteo.columns]
    conteo.index.name = "Clase"
    tablas.exportar(
        conteo, TABLAS, "ventanas_por_carga_clase",
        caption=(
            "Ventanas utilizables de 2048 muestras con 50 por ciento de solape, por "
            "clase y condicion de carga, tras descartar las ventanas frontera entre "
            "bloques."
        ),
        etiqueta="tab:ventanas", decimales=0,
    )

    paso_ms = (info_stft["nperseg"] - info_stft["noverlap"]) / FS * 1000
    duracion_ms = VENTANA / FS * 1000

    def resolucion_efectiva(alto: int, ancho: int) -> str:
        """Resolucion real de la imagen, no la de la STFT que la origina.

        Redimensionar no crea resolucion, pero reducir si la destruye: la
        efectiva es la peor de las dos rejillas, la de la STFT y la de la
        imagen, eje por eje. Declararlo importa porque decide si el tren de
        impactos, de 6.2 a 9.3 ms, sigue representado o no.
        """
        df = max(info_stft["delta_f_hz"], (FS / 2) / alto)
        dt = max(paso_ms, duracion_ms / ancho)
        return f"{df:.1f} Hz / {dt:.2f} ms"

    dimension = pd.DataFrame([
        {"Representacion": "Estadisticos temporales",
         "Dimension": reps["estadisticos"].shape[1],
         "Resolucion": "--", "Invariante a la amplitud": "no",
         "En la comparacion": "si"},
        {"Representacion": "Magnitud FFT",
         "Dimension": reps["fft"].shape[1],
         "Resolucion": f"{FS / VENTANA:.2f} Hz", "Invariante a la amplitud": "no",
         "En la comparacion": "si"},
        {"Representacion": "Wavelet db4 (energia relativa)",
         "Dimension": reps["wavelet"].shape[1],
         "Resolucion": "banda diadica", "Invariante a la amplitud": "si",
         "En la comparacion": "si"},
        {"Representacion": (
            f"Espectrograma STFT ({REJILLA_VECTOR[0]}x{REJILLA_VECTOR[1]})"),
         "Dimension": int(np.prod(reps["espectrograma_vector"].shape[1:])),
         "Resolucion": resolucion_efectiva(*REJILLA_VECTOR),
         "Invariante a la amplitud": "si", "En la comparacion": "si"},
        {"Representacion": (
            f"Espectrograma STFT "
            f"({TAMANO_ESPECTROGRAMA}x{TAMANO_ESPECTROGRAMA}), entrada de la CNN"),
         "Dimension": int(np.prod(reps["espectrograma"].shape[1:])),
         "Resolucion": resolucion_efectiva(TAMANO_ESPECTROGRAMA, TAMANO_ESPECTROGRAMA),
         "Invariante a la amplitud": "si", "En la comparacion": "no"},
    ]).set_index("Representacion")
    tablas.exportar(
        dimension, TABLAS, "dimension_representaciones",
        caption=(
            "Dimension, resolucion efectiva y dependencia de la amplitud absoluta de "
            f"cada representacion. La STFT usa nperseg = {info_stft['nperseg']} muestras, "
            f"lo que da {info_stft['delta_f_hz']:.1f} Hz por banda y "
            f"{info_stft['n_tramas']} tramas separadas {paso_ms:.2f} ms. La banda de "
            "frecuencia localiza la resonancia estructural de 2 a 5.5 kHz que excita la "
            "falla, y el paso temporal resuelve la tasa de repeticion de los impactos, "
            "de 6.2 ms para BPFI a 9.3 ms para BPFO a 1797 rpm, que es donde reside la "
            "firma. La resolucion declarada es la de la imagen, no la de la STFT que la "
            "origina: la version vectorizada usa una rejilla de "
            f"{REJILLA_VECTOR[0]}x{REJILLA_VECTOR[1]} que conserva el eje temporal y "
            "reduce solo el de frecuencia, porque una rejilla cuadrada de la misma "
            "dimension dejaria 10.67 ms por columna y borraria el tren de impactos. "
            "La wavelet devuelve energia relativa por banda y el espectrograma se "
            "normaliza por imagen, de modo que ambas descartan la escala; los "
            "estadisticos y la FFT la conservan. La imagen de 64x64 alimenta la CNN 2D "
            "y queda fuera de la comparacion estadistica."
        ),
        etiqueta="tab:representaciones", decimales=0,
    )


def escribir_manifiesto(
    metadatos: pd.DataFrame,
    reps: dict[str, np.ndarray],
    info_stft: dict,
    segundos_repr: dict,
    segundos: float,
) -> None:
    import pywt
    import scipy

    paso_muestras = info_stft["nperseg"] - info_stft["noverlap"]
    manifiesto = {
        "generado_por": "src/02_preprocess.py",
        "semilla": SEMILLA,
        "fs_hz": FS,
        "ventana_muestras": VENTANA,
        "solape": SOLAPE,
        "paso_muestras": PASO,
        "n_bloques": N_BLOQUES,
        "ventanas_totales": int(len(metadatos)),
        "ventanas_purgadas": int(metadatos["purgada"].sum()),
        "ventanas_utilizables": int((~metadatos["purgada"]).sum()),
        "wavelet": {"ondicula": "db4", "niveles": NIVELES_WAVELET, "solo_energia": True},
        "espectrograma": {
            # Parametros efectivos devueltos por la propia funcion, no
            # reconstruidos aparte.
            **info_stft,
            "paso_ms": paso_muestras / FS * 1000,
            "duracion_ventana_ms": VENTANA / FS * 1000,
            "rejilla_cnn": [TAMANO_ESPECTROGRAMA, TAMANO_ESPECTROGRAMA],
            "rejilla_vector": list(REJILLA_VECTOR),
            "escala": "dB, normalizado por imagen a [0, 1]",
            "periodo_impactos_ms": {
                "BPFO_1797rpm": round(1000 / (3.5848 * 1797 / 60), 2),
                "BPFI_1797rpm": round(1000 / (5.4152 * 1797 / 60), 2),
            },
        },
        "fft": {"bins": int(reps["fft"].shape[1]), "resolucion_frecuencia_hz": FS / VENTANA},
        "segundos_extraccion": {k: round(v, 2) for k, v in segundos_repr.items()},
        "ablacion": {
            "representaciones": ["estadisticos_rmsnorm", "fft_rmsnorm"],
            "alcance_fijado_antes_de_resultados": (
                "SVM-RBF y Random Forest sobre las 12 celdas fuera de diagonal"
            ),
        },
        "versiones": {
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "pandas": pd.__version__,
            "pywavelets": pywt.__version__,
        },
        "segundos_ejecucion": round(segundos, 1),
    }
    (PROCESADO / "manifiesto.json").write_text(
        json.dumps(manifiesto, indent=2, ensure_ascii=True), encoding="utf-8"
    )


# ------------------------------------------------------------------------- main

def main() -> int:
    fijar_semilla()
    PROCESADO.mkdir(parents=True, exist_ok=True)
    TABLAS.mkdir(parents=True, exist_ok=True)
    log = configurar_log("02_preprocess", RAIZ)
    arranque = time.perf_counter()

    catalogo = pd.read_csv(CRUDO / "catalogo.csv")
    log.info(f"Catalogo: {len(catalogo)} registros. Semilla {SEMILLA}.")

    log.info("Segmentado por registro")
    ventanas, metadatos = construir_ventanas(catalogo, log)
    utilizables = int((~metadatos["purgada"]).sum())
    log.info(
        f"Ventanas: {len(metadatos)} totales, {int(metadatos['purgada'].sum())} purgadas, "
        f"{utilizables} utilizables."
    )

    reps, info_stft, segundos_repr = generar_representaciones(ventanas, log)

    errores = verificar_coherencia(ventanas, metadatos, reps, log)
    errores += verificar_particion(metadatos, log)
    if errores:
        log.error("PROBLEMAS DETECTADOS - no se escribe nada:")
        for e in errores[:20]:
            log.error(f"  - {e}")
        if len(errores) > 20:
            log.error(f"  ... y {len(errores) - 20} mas.")
        return 1

    np.save(PROCESADO / "ventanas.npy", ventanas.astype(np.float32))
    for nombre, matriz in reps.items():
        np.save(PROCESADO / f"X_{nombre}.npy", matriz)
    metadatos.to_csv(PROCESADO / "metadatos.csv", index=False)

    escribir_tablas(metadatos, reps, info_stft)
    escribir_manifiesto(metadatos, reps, info_stft, segundos_repr, time.perf_counter() - arranque)

    util = metadatos[~metadatos["purgada"]]
    log.info("Ventanas utilizables por clase y carga:")
    tabla_conteo = util.pivot_table(
        index="clase", columns="carga_hp", values="id_ventana", aggfunc="count"
    ).reindex(CLASES)
    for linea in tabla_conteo.to_string().splitlines():
        log.info("  " + linea)

    log.info(f"Escrito en {PROCESADO} en {time.perf_counter() - arranque:.1f} s.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
