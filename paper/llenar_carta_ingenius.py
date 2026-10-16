#!/usr/bin/env python
"""P7 - rellena la carta de presentacion en el formato oficial de Ingenius.

Las normas de Ingenius (seccion 3.1.1) exigen la presentacion y cover letter
"segun el formato establecido" (https://goo.gl/XAc9a3), que es la plantilla
`paper/evidencia/Cover_Letter_Revista_INGENIUS_2025.docx`. Se sube al OJS en
"Archivos complementarios", firmada por todos los autores.

Este script la rellena con todo lo que se puede rellenar desde el proyecto.
Quedan A MANO, a proposito, los numeros de documento de identidad, las firmas y
el dia y mes del envio: son datos personales de cada autor y no se escriben en
ningun archivo del repositorio.

    python paper/llenar_carta_ingenius.py

Salida: paper/envio/Cover_Letter_INGENIUS_P7.docx
"""

from __future__ import annotations

from pathlib import Path

import docx

RAIZ = Path(__file__).resolve().parent
PLANTILLA = RAIZ / "evidencia" / "Cover_Letter_Revista_INGENIUS_2025.docx"
SALIDA = RAIZ / "envio" / "Cover_Letter_INGENIUS_P7.docx"

# La plantilla limita cada titulo a 80 caracteres con espacios. Si se cambia el
# titulo, hay que cambiarlo tambien en el .tex (\titulo y \tituloa).
TITULO_ES = ("Representación de señal y transferencia entre cargas en fallas "
             "de rodamientos")
TITULO_EN = ("Signal representation and load transfer in bearing fault "
             "classification")

AUTORES = [
    ("Italo Javier Tenempaguay Granizo",
     "Conceptualización, Metodología, Software, Análisis formal, "
     "Investigación, Curación de datos, Visualización, Escritura – borrador "
     "original"),
    ("Juan Pablo Aviles Esparza", "Validación, Análisis formal"),
    ("Isaac David Torres Paredes",
     "Conceptualización, Supervisión, Administración de proyecto, Escritura – "
     "revisión y edición"),
]
ROR_ESPOCH = ("https://ror.org/02zyw2q61 (Escuela Superior Politécnica de "
              "Chimborazo)")

# Resumen y abstract: copia literal de articulo_p7.tex (216 y 213 palabras,
# dentro del rango 210-230 que fija la plantilla).
RESUMEN = (
    "Las comparaciones entre representaciones de señal para el diagnóstico de "
    "fallas en rodamientos suelen reportarse bajo una sola condición de "
    "operación, donde la exactitud satura y aporta poca información. Este "
    "trabajo mide el comportamiento de cuatro representaciones cuando la carga "
    "de prueba difiere de la de entrenamiento. Se combinaron estadísticos "
    "temporales, magnitud FFT, energías de banda wavelet db4 y espectrograma "
    "STFT con tres clasificadores de vector sobre los dieciséis pares (carga de "
    "entrenamiento, carga de prueba) del conjunto CWRU a 12 kHz, con cinco "
    "pliegues por celda y semilla fija. La división se hizo por registro de "
    "origen y por bloques contiguos purgados, evitando fuga por solape. Dentro "
    "de una misma carga, donde la partición comparte registros, las cuatro "
    "superaron 0,95 de F1-macro, de modo que la comparación habitual no "
    "discrimina. Entre cargas la caída media osciló entre 0,074 para el "
    "espectrograma y 0,153 para los estadísticos, con intervalos de confianza "
    "solapados. La prueba de Friedman ómnibus sobre los doce pares fuera de la "
    "diagonal no rechazó, mientras que las tres pruebas por clasificador "
    "rechazaron y discreparon en el orden. Un ANOVA exploratorio sitúa la "
    "interacción representación-clasificador por encima de todo efecto "
    "principal. Una ablación de normalización de amplitud no mejoró la "
    "transferencia y la degradó con Random Forest. La elección de "
    "representación interactúa con el clasificador.")
ABSTRACT = (
    "Comparisons of signal representations for bearing fault diagnosis are "
    "usually reported under a single operating condition, where accuracy "
    "saturates and the comparison carries little information. This work "
    "measures how four representations behave when the test load differs from "
    "the training load. Time-domain statistics, FFT magnitude, db4 wavelet band "
    "energies and STFT spectrogram were combined with three vector classifiers "
    "over the sixteen (training load, test load) pairs of the CWRU drive-end "
    "dataset at 12 kHz, with five folds per cell and a fixed seed. The split "
    "was performed by source record and by purged contiguous blocks, so that no "
    "two windows sharing samples fall on opposite sides. Within a single load, "
    "where the split shares records, all four exceeded 0.95 macro-F1, so the "
    "usual comparison does not discriminate between them. Across loads the "
    "mean drop ranged from 0.074 for the spectrogram to 0.153 for time-domain "
    "statistics, with overlapping bootstrap intervals. The omnibus Friedman "
    "test over the twelve off-diagonal pairs did not reject, while the three "
    "per-classifier tests each did and disagreed on the ranking. An exploratory "
    "three-way ANOVA on the cell means places the representation by classifier "
    "interaction above every main effect. An amplitude-normalisation ablation "
    "did not improve transfer and degraded it with Random Forest. "
    "Representation choice interacts with the classifier rather than defining "
    "a general ordering.")
PALABRAS_CLAVE = ("análisis de vibraciones, desplazamiento de dominio, "
                  "diagnóstico de fallas en rodamientos, fuga de datos, "
                  "prueba de Friedman, representación de señal")
KEYWORDS = ("bearing fault diagnosis, data leakage, domain shift, Friedman "
            "test, signal representation, vibration analysis")

USO_IA = (
    "Se utilizó Claude (Anthropic), bajo la supervisión y revisión directa de "
    "los autores, con tres fines: (1) escribir y depurar el código de "
    "procesamiento de señal, clasificación, análisis estadístico y generación "
    "de figuras descrito en la sección de Materiales y métodos; (2) contrastar "
    "cada referencia bibliográfica con su fuente original; y (3) redactar y "
    "revisar el texto del manuscrito a partir del diseño experimental y los "
    "resultados de los autores. Ninguna herramienta de inteligencia artificial "
    "figura como autora, ninguna se utilizó para generar o alterar datos o "
    "resultados, y ninguna figura se produjo con software de generación de "
    "imágenes. Todo el código fue ejecutado por los autores y cada cifra "
    "reportada se verificó contra esa ejecución. Los autores asumen la plena "
    "responsabilidad del contenido del manuscrito.")


def reemplazar(parrafo, texto: str, cursiva: bool | None = None) -> None:
    """Deja `texto` en el primer run del parrafo y borra el resto, conservando
    el formato (fuente, tamano, negrita) del primer run de la plantilla."""
    runs = parrafo.runs
    if not runs:
        parrafo.add_run(texto)
        return
    runs[0].text = texto
    if cursiva is not None:
        runs[0].italic = cursiva
    for r in runs[1:]:
        r._element.getparent().remove(r._element)


def celda(c, texto: str, cursiva: bool | None = None) -> None:
    reemplazar(c.paragraphs[0], texto, cursiva)
    for p in c.paragraphs[1:]:
        p._element.getparent().remove(p._element)


def celda_tabla(c, texto: str, negrita: bool) -> None:
    """Celda de las tablas de autores y ROR, con el formato uniforme de la
    plantilla (Times New Roman 10). A diferencia de `celda`, vacia el parrafo
    entero: la fila de ejemplo de la tabla ROR trae un hipervinculo, que no es
    un run y `reemplazar` no lo borraria; y las filas vacias de la plantilla no
    tienen runs de los que heredar la fuente."""
    from docx.shared import Pt
    p = c.paragraphs[0]
    for hijo in list(p._p):
        if not hijo.tag.endswith("}pPr"):
            p._p.remove(hijo)
    for extra in c.paragraphs[1:]:
        extra._element.getparent().remove(extra._element)
    run = p.add_run(texto)
    run.font.name = "Times New Roman"
    run.font.size = Pt(10)
    run.bold = negrita


def exigir(condicion: bool, mensaje: str) -> None:
    if not condicion:
        raise SystemExit(f"ABORTA: {mensaje}. La plantilla no es la esperada.")


def main() -> None:
    for nombre, t in (("español", TITULO_ES), ("inglés", TITULO_EN)):
        exigir(len(t) <= 80, f"el título en {nombre} tiene {len(t)} caracteres")
    for nombre, t in (("resumen", RESUMEN), ("abstract", ABSTRACT)):
        n = len(t.split())
        exigir(210 <= n <= 230, f"el {nombre} tiene {n} palabras")

    d = docx.Document(str(PLANTILLA))
    P = d.paragraphs

    exigir(P[2].text.startswith("Título en español"), "P2 no es el título ES")
    reemplazar(P[2], TITULO_ES)
    exigir(P[3].text.startswith("Title in English"), "P3 no es el título EN")
    reemplazar(P[3], TITULO_EN)

    exigir(P[6].text.startswith("Nombre autor 1"), "P6 no es la línea de autores")
    reemplazar(P[6], ", ".join(a for a, _ in AUTORES))

    t0 = d.tables[0]
    celda(t0.rows[1].cells[0], RESUMEN)
    celda(t0.rows[1].cells[1], ABSTRACT, cursiva=True)
    celda(t0.rows[2].cells[0], f"Palabras clave: {PALABRAS_CLAVE}")
    celda(t0.rows[2].cells[1], f"Keywords: {KEYWORDS}", cursiva=True)

    exigir(P[17].text.startswith("Entidad"), "P17 no es Entidad")
    reemplazar(P[17], "Entidad: No aplica. El trabajo no recibió financiamiento "
                      "externo.")

    # Titulo y autoria dentro del texto fijo de la presentacion.
    exigir("lleva por título" in P[43].text, "P43 no es la presentación")
    ultimo = P[43].runs[-1]
    ultimo.text = (f"para su publicación. El original lleva por título "
                   f"“{TITULO_EN}” (en español: “{TITULO_ES}”), cuya autoría "
                   f"corresponde a {', '.join(a for a, _ in AUTORES[:-1])} y "
                   f"{AUTORES[-1][0]}.")

    exigir(P[57].text.startswith("Sí:"), "P57 no es la casilla de IA")
    reemplazar(P[57], "Sí: _X_   No: ___")
    exigir(set(P[59].text) == {"_"}, "P59 no es la primera línea de IA")
    reemplazar(P[59], USO_IA)
    reemplazar(P[60], "")
    reemplazar(P[61], "")

    # Tablas de contribuciones (CRediT) y de ROR: tres autores, se quitan las
    # dos filas "autor (4)" que trae la plantilla.
    for indice, valores in ((1, [c for _, c in AUTORES]),
                            (2, [ROR_ESPOCH] * len(AUTORES))):
        t = d.tables[indice]
        for fila, (nombre, valor) in zip(t.rows[1:], zip([a for a, _ in AUTORES],
                                                          valores)):
            celda_tabla(fila.cells[0], nombre, negrita=True)
            celda_tabla(fila.cells[1], valor, negrita=False)
        for fila in list(t.rows[1 + len(AUTORES):]):
            fila._tr.getparent().remove(fila._tr)

    exigir(P[94].text.startswith("En ____(ciudad)"), "P94 no es la fecha")
    P[94].runs[0].text = "En Riobamba, a los ____ días del mes de ______ "
    P[94].runs[-1].text = " 2026"

    # Bloques de firma: nombre de cada autor; documento y firma, a mano.
    bloques = [i for i, p in enumerate(P) if p.text == "Nombre y apellido de los autores"]
    exigir(len(bloques) == 3, f"se esperaban 3 bloques de firma, hay {len(bloques)}")
    for i, (nombre, _) in zip(bloques, AUTORES):
        reemplazar(P[i], nombre)
        reemplazar(P[i + 1], "Documento de identidad: ____________________")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    d.save(str(SALIDA))
    print(f"Escrito {SALIDA}")
    print("A mano: día y mes, números de documento de identidad y firmas.")


if __name__ == "__main__":
    main()
