# Instrucciones de envío — P7

> Archivo pedido por `propuesta_planificación_sugerida.pdf`, §6 («Paquete de
> entrega por artículo»). Lo usa el responsable académico, que es quien realiza
> el envío; no el practicante.

- **Revista:** Ingenius, Revista de Ciencia y Tecnología (Universidad
  Politécnica Salesiana, Cuenca, Ecuador). eISSN 1390-860X, pISSN 1390-650X.
- **URL del sistema de envío:** OJS en https://ingenius.ups.edu.ec
- **Todo lo que se sube está listo en `paper/envio/`:**
  - **Archivo principal:** `articulo_p7.pdf` (la revista pide el PDF como
    archivo original cuando el manuscrito viene de LaTeX). **Anonimizado** en el
    texto y en las propiedades del archivo (campo *Author* vacío).
  - **Código fuente:** `articulo_p7_fuente_latex.zip` — `.tex`, `.bib`, `.bbl`,
    `ingenius.cls`, archivos de configuración y figuras; solo lo que LaTeX lee
    al compilar. Probado: compila por sí solo y da el mismo PDF. Sin datos que
    identifiquen a los autores.
  - **Figuras sueltas:** `figuras/fig1_p7.pdf` … `fig4_p7.pdf`, vectoriales.
  - **Carta en el formato oficial de Ingenius (obligatoria):**
    `Cover_Letter_INGENIUS_P7.docx`, en "Archivos complementarios" del OJS.
    Generada con `paper/llenar_carta_ingenius.py` sobre la plantilla oficial
    (`paper/evidencia/Cover_Letter_Revista_INGENIUS_2025.docx`, normas §3.1.1).
    **Completar a mano antes de subir:** día y mes, número de documento de
    identidad de cada autor y las tres firmas.
  - **Comentarios para el editor:** el texto de `paper/cover_letter.md`, pegado
    en el cuadro de comentarios del OJS. Lleva el DOI para el editor.
  - **Título:** la plantilla oficial limita cada título a 80 caracteres. La carta
    ya lleva los títulos cortos; el manuscrito tiene que llevar los mismos
    (`\titulo` y `\tituloa` del `.tex`).
  - Para regenerar la carpeta tras cualquier cambio: recompilar el `.tex` y
    volver a copiar; los auxiliares (`.aux`, `.log`, `.bbl` viejo) no se suben.
- **¿Cobra APC?** No. Evidencia guardada en `JOURNAL.md` y en
  `paper/evidencia/` (HTML de la página de acceso abierto, capturado el
  24/08/2026). Licencia CC BY-NC-SA 4.0.
- **Autores en orden, con afiliación y ORCID.** Los tres comparten afiliación:
  Facultad de Informática y Electrónica, Escuela Superior Politécnica de
  Chimborazo (ESPOCH), Riobamba, Ecuador.

  | # | Nombre | Correo | ORCID |
  |---|---|---|---|
  | 1 | Italo Javier Tenempaguay Granizo | italo.tenempaguay@espoch.edu.ec | https://orcid.org/0009-0001-5753-4279 |
  | 2 | Juan Pablo Aviles Esparza | juan.aviles@espoch.edu.ec | https://orcid.org/0009-0007-0058-8069 |
  | 3 | Isaac David Torres Paredes | isaac.torres@espoch.edu.ec | https://orcid.org/0009-0001-7057-9316 |

- **Autor de correspondencia:** Isaac David Torres Paredes —
  isaac.torres@espoch.edu.ec
- **Categorías / keywords a seleccionar en el formulario:** bearing fault
  diagnosis, data leakage, domain shift, Friedman test, signal representation,
  vibration analysis.
- **Revisores sugeridos:** la revista no los pide.
- **Repositorio de código:** https://github.com/Italo-1/bearing-fault-signal-representation
- **DOI de Zenodo:**
  - **De concepto (el que se cita): 10.5281/zenodo.22907921** — apunta siempre
    a la última versión del repositorio.
  - De la versión v1.0.0: 10.5281/zenodo.22907922 — fija esa instantánea.
- **El DOI NO va en el manuscrito de revisión.** El registro de Zenodo muestra
  el usuario de GitHub (`Italo-1`) y el nombre del primer autor, así que citarlo
  desanonimiza el artículo igual que la URL. El PDF dice que el DOI se retiene
  por la revisión ciega; **el DOI se le da al editor en la carta de
  presentación**. Al aceptarse, sustituir la frase de la sección *Data
  availability* del `.tex` por la que está anotada en el comentario justo
  encima de ella.
- **Notas:**
  - **Revisión doble ciego.** El archivo tiene que estar anonimizado *también en
    las propiedades del PDF*, no solo en el texto. Comprobar antes de subir.
  - **Los datos de autoría de la tabla de arriba NO van en el manuscrito**: se
    escriben en el formulario del OJS. El `.tex` lleva `\autores{}` vacío y
    `\apellido{Anonymous et al.}` justamente para eso. Solo hay que rellenar
    `\autores` y `\adscripcionautor` si la revista pide una versión no anónima
    tras la aceptación (la línea 15 del `.tex` lo deja anotado).
  - **Declaración de uso de IA obligatoria**, y va en la carta de presentación,
    no en el cuerpo del artículo. Ya está redactada ahí.
  - **Sin urgencia de calendario.** Convocatoria abierta todo el año; el cierre
    del n.º 37 (enero de 2027) es el 15 de noviembre de 2026. Es el artículo de
    los cinco que más margen tiene.
  - Extensión admitida: 4 000 a 6 500 palabras. Citas en IEEE.
  - Comprobación inicial de hasta 4 semanas; segunda fase de 4 semanas mínimo.
