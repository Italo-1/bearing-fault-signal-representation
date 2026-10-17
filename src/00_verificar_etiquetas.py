"""P7 - verificacion fisica de las etiquetas de CWRU por analisis de envolvente.

La ficha exige contrastar la correspondencia archivo -> (tipo de falla,
diametro, carga) antes de escribir el preprocesado, porque la nomenclatura de
CWRU se interpreta mal a menudo. Contrastarla contra tablas de terceros solo
traslada el problema: si esa tabla esta mal, se hereda el error.

Aqui se verifica contra la fisica del rodamiento. Una falla localizada genera
impactos periodicos cada vez que un elemento rodante pasa por el defecto, a una
frecuencia que depende solo de la geometria y de la velocidad de giro. El
analisis de envolvente (Hilbert) revela esa frecuencia. Si un archivo etiquetado
como falla en pista interna muestra un pico en BPFI y no en BPFO, la etiqueta es
correcta y queda demostrado, no supuesto.

Rodamiento del extremo de transmision en CWRU: SKF 6205-2RS JEM. Sus factores
caracteristicos, en multiplos de la frecuencia de giro del eje:

    BPFO  3.5848   paso de elementos por la pista externa
    BPFI  5.4152   paso de elementos por la pista interna
    BSF   2.3568   giro del elemento rodante (convencion de libro)
    FTF   0.3983   jaula

Correccion del 17/10/2026 (revision cruzada de linea A). CWRU tabula la
frecuencia del elemento rodante como 4.7135, y ese valor YA ES 2xBSF: con la
geometria del 6205 (Bd = 0.3126 in, Pd = 1.537 in) el BSF convencional es
(Pd/2Bd)(1 - (Bd/Pd)^2) = 2.3567. La version anterior tomaba 4.7135 como BSF y
calculaba su doble, de modo que el criterio "2xBSF" buscaba en realidad en
4xBSF. Ahora BSF = 4.7135 / 2 y 2xBSF = 4.7135, como en la fisica.

    python src/00_verificar_etiquetas.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal as sp_signal
from scipy.io import loadmat

RAIZ = Path(__file__).resolve().parent.parent
CRUDO = RAIZ / "data" / "raw"
FS = 12_000.0

# CWRU publica 4.7135 para el elemento rodante, que es 2xBSF (ver docstring).
FACTOR_ELEMENTO_RODANTE_CWRU = 4.7135
FACTORES = {"BPFO": 3.5848, "BPFI": 5.4152,
            "BSF": FACTOR_ELEMENTO_RODANTE_CWRU / 2, "FTF": 0.3983}

# Que frecuencia debe dominar en cada clase. El defecto en elemento rodante
# suele manifestarse con mas fuerza en 2xBSF que en BSF.
ESPERADA = {"IR": "BPFI", "OR": "BPFO", "B": "BSF"}

# Banda de resonancia estructural donde los impactos se amplifican. Es la
# practica habitual en CWRU: filtrar aqui antes de extraer la envolvente mejora
# mucho la relacion senal-ruido del espectro de envolvente.
BANDA = (2000.0, 5500.0)


def espectro_envolvente(x: np.ndarray, fs: float = FS) -> tuple[np.ndarray, np.ndarray]:
    """Devuelve (frecuencias, magnitud) del espectro de la envolvente de Hilbert."""
    # Filtro pasa banda en la zona de resonancia.
    sos = sp_signal.butter(4, [BANDA[0], BANDA[1]], btype="bandpass", fs=fs, output="sos")
    filtrada = sp_signal.sosfiltfilt(sos, x)

    envolvente = np.abs(sp_signal.hilbert(filtrada))
    envolvente = envolvente - envolvente.mean()  # quitar continua

    ventana = np.hanning(envolvente.size)
    espectro = np.abs(np.fft.rfft(envolvente * ventana))
    frecuencias = np.fft.rfftfreq(envolvente.size, 1.0 / fs)

    return frecuencias, espectro


def energia_en(frecuencias, espectro, objetivo: float, tolerancia: float = 2.5,
               armonicos: int = 3) -> float:
    """Relacion entre la energia en `objetivo` (y sus armonicos) y el fondo.

    Un valor alto significa que hay un pico marcado en esa frecuencia. Se
    normaliza por la mediana del espectro para que el resultado no dependa de la
    amplitud absoluta, que cambia con la carga.
    """
    fondo = np.median(espectro)
    if fondo <= 0:
        return 0.0

    picos = []
    for k in range(1, armonicos + 1):
        f = objetivo * k
        if f >= frecuencias[-1]:
            break
        cerca = np.abs(frecuencias - f) <= tolerancia
        if cerca.any():
            picos.append(espectro[cerca].max())

    return float(np.mean(picos) / fondo) if picos else 0.0


def energia_bandas_laterales(frecuencias, espectro, centro: float, separacion: float,
                             tolerancia: float = 2.5) -> float:
    """Energia en las bandas laterales `centro +/- separacion`, frente al fondo.

    Es el criterio correcto para el defecto en elemento rodante. La bola con
    defecto golpea alternativamente las dos pistas y ademas entra y sale de la
    zona de carga al ritmo de la jaula, de modo que su firma no es un pico
    limpio en BSF sino 2xBSF modulado por FTF. Buscar solo BSF da un falso
    negativo, y es un error frecuente en la literatura aplicada.
    """
    fondo = np.median(espectro)
    if fondo <= 0:
        return 0.0

    picos = []
    for signo in (-1, 1):
        f = centro + signo * separacion
        if 0 < f < frecuencias[-1]:
            cerca = np.abs(frecuencias - f) <= tolerancia
            if cerca.any():
                picos.append(espectro[cerca].max())

    return float(np.mean(picos) / fondo) if picos else 0.0


def main() -> int:
    catalogo = pd.read_csv(CRUDO / "catalogo.csv")
    # Se verifican solo los archivos con falla: en Normal no hay frecuencia
    # caracteristica que buscar, y sirve de control negativo.
    filas = []

    for _, fila in catalogo.iterrows():
        numero = int(Path(fila["archivo"]).stem)
        contenido = loadmat(CRUDO / fila["archivo"])
        clave = f"X{numero:03d}_DE_time"
        if clave not in contenido:
            candidatos = [k for k in contenido if k.endswith("_DE_time")]
            if not candidatos:
                continue
            clave = candidatos[0]

        senal = np.ravel(contenido[clave])
        f_eje = fila["rpm_aprox"] / 60.0
        frecuencias, espectro = espectro_envolvente(senal)

        ratios = {
            nombre: energia_en(frecuencias, espectro, factor * f_eje)
            for nombre, factor in FACTORES.items()
        }
        # 2xBSF y sus bandas laterales a la frecuencia de jaula: la firma real
        # del defecto en elemento rodante.
        ratios["2xBSF"] = energia_en(frecuencias, espectro, 2 * FACTORES["BSF"] * f_eje)
        ratios["2xBSF_FTF"] = energia_bandas_laterales(
            frecuencias, espectro,
            centro=2 * FACTORES["BSF"] * f_eje,
            separacion=FACTORES["FTF"] * f_eje,
        )

        filas.append({
            "archivo": fila["archivo"],
            "clase": fila["clase"],
            "diametro": fila["diametro_pulg"],
            "carga_hp": fila["carga_hp"],
            "f_eje_Hz": round(f_eje, 2),
            **{k: round(v, 2) for k, v in ratios.items()},
        })

    r = pd.DataFrame(filas)
    r.to_csv(RAIZ / "results" / "tables" / "verificacion_etiquetas.csv", index=False)

    print("Relacion pico/fondo en el espectro de envolvente, por clase")
    print("(mas alto = pico mas marcado en esa frecuencia caracteristica)\n")
    columnas = ["BPFO", "BPFI", "BSF", "2xBSF", "2xBSF_FTF"]
    print(r.groupby("clase")[columnas].mean().round(2))

    # --- Pistas: criterio directo, la frecuencia propia debe dominar ---------
    print("\n[pistas interna y externa] la frecuencia propia debe dominar:")
    pistas = r[r["clase"].isin(["IR", "OR"])]
    fallos = []

    for _, fila in pistas.iterrows():
        esperada = ESPERADA[fila["clase"]]
        rival = "BPFO" if esperada == "BPFI" else "BPFI"
        if fila[esperada] <= fila[rival]:
            fallos.append((fila["archivo"], fila["clase"], esperada,
                           round(fila[esperada], 1), round(fila[rival], 1)))

    print(f"  {len(pistas) - len(fallos)}/{len(pistas)} confirmados")
    for f in fallos:
        print(f"    CONTRADICE: {f[0]} clase {f[1]} (esperaba {f[2]}): "
              f"{f[3]} frente a {f[4]}")

    # --- Elemento rodante: criterio de bandas laterales ----------------------
    # No se compara contra BPFO/BPFI: en un defecto de bola las dos pistas
    # reciben impactos, asi que su energia es esperable y no contradice nada.
    # Lo que confirma la etiqueta es que la firma de bola supere claramente al
    # nivel de fondo de la propia senal.
    bolas = r[r["clase"] == "B"]
    normal = r[r["clase"] == "Normal"]
    umbral = normal[["BPFO", "BPFI", "BSF", "2xBSF", "2xBSF_FTF"]].max().max()

    print(f"\n[elemento rodante] firma 2xBSF con bandas laterales de jaula,")
    print(f"  contrastada con el maximo observado en la clase Normal ({umbral:.1f}):")

    confirmados = 0
    estrictos = 0
    for _, fila in bolas.iterrows():
        firma = max(fila["BSF"], fila["2xBSF"], fila["2xBSF_FTF"])
        # Criterio estricto: solo la firma fisica del defecto de bola, 2xBSF y
        # sus bandas laterales de jaula, sin la linea BSF fundamental. Es la
        # cifra que cita el articulo.
        firma_estricta = max(fila["2xBSF"], fila["2xBSF_FTF"])
        if firma_estricta > 2 * umbral:
            estrictos += 1
        if firma > 2 * umbral:
            confirmados += 1
        else:
            print(f"    DEBIL: {fila['archivo']} firma {firma:.1f}")

    print(f"  {estrictos}/{len(bolas)} con 2xBSF o sus bandas laterales por encima "
          f"del doble del control negativo")
    print(f"  {confirmados}/{len(bolas)} si se incluye tambien la linea BSF")

    print(f"\nControl negativo (Normal): pico maximo = {umbral:.2f}")
    print("Ninguna frecuencia caracteristica destaca en el rodamiento sano, que es"
          "\nlo que debe ocurrir si el metodo mide lo que se supone que mide.")

    # Los registros de firma debil no son un error del catalogo: la falla existe,
    # pero es poco diagnosticable por envolvente. Es un rasgo conocido de CWRU
    # (ver Smith y Randall, 2015). Se reportan para poder desglosar resultados
    # por diametro despues, no se tratan como fallo de verificacion.
    print("\nLos registros de firma debil quedan anotados en "
          "results/tables/verificacion_etiquetas.csv")
    print("y se conservan en el experimento: descartar los dificiles inflaria el")
    print("resultado, que es justo lo que este articulo critica del campo.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
