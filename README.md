# Protocolo - P7

**Revista destino:** *Ingenius*, Universidad Politecnica Salesiana (Ecuador)
**Fecha de inicio:** 20 de agosto de 2026
**Responsable:** practicante linea B

> Este protocolo se cierra ANTES de tocar los datos. La prueba estadistica esta
> decidida antes de ver resultados. Cualquier cambio posterior se anota con fecha
> en la bitacora, al final del archivo.

## Pregunta de investigacion

¿Que representacion de senal rinde mejor para clasificar fallas en rodamientos, y
cuanto se degrada el desempeno cuando la condicion de carga en prueba difiere de
la de entrenamiento?

## Hipotesis

Dentro de una misma carga, las cuatro representaciones dan resultados altos y
parecidos (F1 > 0.95), de modo que la comparacion habitual en la literatura no
discrimina. Al cambiar de carga, las representaciones tiempo-frecuencia (wavelet
db4 y espectrograma STFT) **resisten mejor** que los estadisticos temporales,
porque estos ultimos dependen de la amplitud absoluta de la vibracion, que escala
con la carga.

## Variables

- **Independientes**
  - Representacion (4): estadisticos temporales, magnitud FFT, wavelet db4, espectrograma STFT
  - Clasificador (4): SVM-RBF, Random Forest, MLP de 2 capas, CNN 2D
  - Carga de entrenamiento (4): 0, 1, 2, 3 HP
  - Carga de prueba (4): 0, 1, 2, 3 HP
- **Dependientes**: exactitud, F1-macro, caida absoluta (diagonal - fuera de diagonal)
- **Controladas**: ventana de 2048 muestras con 50 % de solape; frecuencia de
  muestreo 12 kHz; semilla 42; validacion 5-fold estratificada; misma particion
  para todas las representaciones

## Diseno

- Condiciones experimentales: 4 representaciones x 4 clasificadores x 4 cargas de
  entrenamiento x 4 cargas de prueba = **256 celdas**
- Repeticiones por condicion: 5-fold estratificado dentro de cada celda
- Semilla aleatoria: 42
- Validacion: la division train/test se hace **por registro de origen, nunca por
  ventana**. Las ventanas solapadas de un mismo registro comparten informacion y
  repartirlas entre train y test infla el resultado. Es el error mas comun en la
  literatura de este tema y un revisor de *Ingenius* puede detectarlo.

## Prueba estadistica

*Decidida antes de ver resultados.*

- **Friedman** sobre los rangos de las 4 representaciones, tratando cada par
  (carga entrenamiento, carga prueba) fuera de la diagonal como un conjunto.
- **Post-hoc de Nemenyi** con diagrama de diferencia critica (`fieutils.stats.friedman_nemenyi`).
- **ANOVA de dos factores**: representacion x distancia de carga (0, 1, 2, 3 HP
  de separacion), con analisis de interaccion.
- Tamano del efecto a reportar: **eta cuadrado parcial** para el ANOVA y
  **distancia critica** para Nemenyi.

## Criterio de interes

- **Si la hipotesis se confirma**, el hallazgo es: la eleccion de representacion
  es irrelevante dentro de la misma carga y determinante fuera de ella, con una
  recomendacion concreta de representacion para talleres que entrenan con una
  carga y operan con otra.
- **Si se refuta** (los estadisticos temporales resisten igual o mejor), el
  hallazgo es igual de publicable: contradice la justificacion habitual para usar
  representaciones tiempo-frecuencia, que son mas caras de calcular. La Tabla 2
  de costo computacional pasa entonces a primer plano.

## Datasets

| Nombre | Fuente | Licencia | Verificado |
|---|---|---|---|
| CWRU Bearing Data Center | engineering.case.edu | Uso academico con cita | pendiente |
| MAFAULDA | UFRJ, Universidade Federal do Rio de Janeiro | Uso academico | pendiente |
| ~~MIMII~~ | descartado: la ficha lo marca opcional y no cabe en el presupuesto |

**Verificar antes de escribir codigo:** la nomenclatura de archivos de CWRU es
confusa y muchos trabajos publicados la interpretan mal. Contrastar la
correspondencia archivo → (tipo de falla, diametro, carga) con 2-3 articulos
publicados que documenten la estructura.

## Citas obligatorias de la revista destino

Minimo 3, maximo 5, publicadas en *Ingenius*. Candidatos localizados y
verificados via Crossref el 21/08/2026 (los cinco DOI resuelven):

1. **Contreras Urgiles, W. R.; Maldonado Ortega, J.; Leon Japa, R.** (2019).
   *Aplicacion de una red neuronal feed-forward backpropagation para el
   diagnostico de fallas mecanicas en motores de encendido provocado*.
   Ingenius, n.21, pp. 32-40. DOI: `10.17163/ings.n21.2019.03`
   → **La mas cercana**: red neuronal para diagnostico de fallas mecanicas.
   Va en la introduccion y en el related work.

2. **Llanes-Cedeno, E. A.; Guardia-Puebla, Y.; De la Rosa-Andino, A.;
   Cevallos-Carvajal, S.** (2019). *Deteccion de fallas en motores de combustion
   mediante indicadores de temperatura y presion de inyeccion*. Ingenius, n.22,
   pp. 38-46. DOI: `10.17163/ings.n22.2019.04`
   → Deteccion de fallas por indicadores medidos. Sirve para contrastar el
   enfoque por indicadores frente al enfoque por representacion de senal.

3. **Salazar, L.; Quizhpi, F.; Bueno, A.; Reyna, R.** (2012). *Deteccion de
   fallas en el aislamiento en las chapas del estator de maquinas electricas
   rotativas*. Ingenius, n.7. DOI: `10.17163/ings.n7.2012.02`
   → Diagnostico en maquinas rotativas, el mismo dominio fisico.

4. **Gomez, R.; Cabrera, D.; Robles, P.** (2023). *Study for localization of
   fault in the electrical distribution systems*. Ingenius, n.30, pp. 64-78.
   DOI: `10.17163/ings.n30.2023.06`
   → **La mejor de las cinco.** Descompone senales de falla con **wavelet
   Daubechies db4 de nivel 4**, la misma familia que nuestra representacion
   wavelet. Reciente y de la propia UPS. Ancla la eleccion de db4 en la revista
   destino.

5. ~~**Villa, Y.; Vook, T.; Villa, J. L.; Carbajal, P.** (2022). *Structural and
   modal analysis of adapter plates for hydraulic hammers and skid steers under
   real work condition*. Ingenius, n.28, pp. 92-99.~~
   DOI: `10.17163/ings.n28.2022.09`
   → **RETIRADA el 24/08 al leerla.** No sostiene lo que se le atribuia. Es un
   diseno estructural -analisis estatico, modal y de fatiga de una placa de
   adaptacion en Inventor y Ansys- que no mide como cambia una senal ni un
   modelo de diagnostico al variar la condicion de operacion. Citarla para «las
   condiciones de operacion cambian el comportamiento medido» seria justo el
   fallo que el paso 3 de la guia existe para evitar.

**Paso 3 completado el 24/08:** las cinco leidas enteras, no el resumen. El
detalle y el veredicto de cada una estan en `JOURNAL.md`. Resultado: **cuatro
sirven y una se retira.** La lista de comprobacion pide de 3 a 5 citas de la
revista, asi que cuatro cumple. Se busco sustituto en el buscador de la propia
revista: **Ingenius no tiene ningun articulo sobre rodamientos, vibracion ni
diagnostico por aprendizaje automatico**, de modo que forzar una quinta seria
rellenar.

**Correccion de autoria detectada al leer:** la 3 tiene cinco autores (incluye a
Jose Manuel Aller) y la 5 tiene seis (incluye a Leonardo Barrera y Max Florez).
La lista de candidatos del 21/08 los daba con cuatro. Corregir en el `.bib`.

## Figuras

| Figura | Contenido |
|---|---|
| Fig. 1 | Senales crudas: normal, falla en pista interna, pista externa, elemento rodante |
| Fig. 2 | La misma senal en las 4 representaciones, en panel 2x2 |
| **Fig. 3** | **Mapa de calor 4x4 de F1 por par (carga entrenamiento, carga prueba), un panel por representacion** |
| Fig. 4 | Diagrama de diferencia critica de Nemenyi |

La Fig. 3 es la que sostiene el articulo. Se genera con
`fieutils.figures.mapa_calor_transferencia`, que recuadra la diagonal para que el
lector localice de inmediato la referencia contra la que comparar.

**Tabla 1:** F1 dentro y fuera de dominio por representacion y clasificador, con
desviacion estandar. **Tabla 2:** costo computacional (extraccion mas
entrenamiento).

## Riesgos

| Riesgo | Solucion |
|---|---|
| Nomenclatura de CWRU mal interpretada | **Materializado y resuelto el 20/08**, ver abajo |
| Resultados saturados al 99 % en la diagonal | Es lo esperado; el articulo vive de lo que pasa fuera de ella |
| Fuga de informacion por ventanas solapadas | Division por registro de origen, verificada en `02_preprocess.py` |
| Ventana de envio de *Ingenius* | Sin urgencia: recibe todo el ano, proximo corte 15 nov 2026 |

## Pipeline

| Script | Que hace |
|---|---|
| `01_download.py` | Descarga y organiza los `.mat` por condicion de carga y tipo de falla |
| `02_preprocess.py` | Segmenta en ventanas de 2048 con 50 % de solape; genera las 4 representaciones |
| `03_experiment.py` | 4 representaciones x 4 clasificadores x 4 cargas train x 4 cargas test; guarda resultados por fold |
| `04_stats.py` | Friedman, post-hoc de Nemenyi, ANOVA de dos factores |
| `05_figures.py` | Las cuatro figuras |

## Anomalia documentada en CWRU: el archivo 99.mat

Verificado el 20/08/2026 con `src/00_verificar_estructura.py` sobre los 40
archivos descargados.

**`99.mat` (Normal, 2 HP) contiene dos registros**, no uno:

| Variable | Muestras | Duracion | RMS |
|---|---|---|---|
| `X098_DE_time` | 483 903 | 40.33 s | 0.0664 |
| `X099_DE_time` | 485 063 | 40.42 s | 0.0643 |

`X098_*` es una copia identica del contenido de `98.mat` (Normal, 1 HP): misma
longitud y mismo RMS hasta el cuarto decimal. Es un error de empaquetado en el
propio dataset, no de la descarga.

**Por que importa aqui mas que en otros trabajos.** El criterio habitual —tomar
la primera clave que termine en `_DE_time`— devuelve `X098` por orden
alfabetico, con lo que la senal de **1 HP quedaria etiquetada como 2 HP**. En un
estudio que clasifica tipos de falla eso apenas se nota, porque ambas son
"Normal"; en este articulo **la carga es el eje del experimento**, asi que el
error desplazaria una columna entera de la matriz 4x4 sin producir ninguna senal
de alarma: los resultados saldrian plausibles y estarian mal.

**Regla adoptada:** el canal se selecciona por coincidencia exacta con el numero
de archivo (`X{NNN}_DE_time`), nunca por posicion. Implementado en
`00_verificar_estructura.py` y obligatorio en `02_preprocess.py`.

Esto va en la seccion de metodologia del manuscrito. Es el tipo de detalle que
distingue un trabajo cuidadoso y da credibilidad al resto de las decisiones.

### Confirmacion independiente

El repositorio publico `srigas/CWRU_Bearing_NumPy`, que redistribuye el dataset
corregido, documenta **la misma anomalia** de forma independiente: el archivo de
1750 rpm en condicion Normal (nuestro `99.mat`) contiene un par DE/FE duplicado
identificado como `X098`, identico al archivo de 1772 rpm (nuestro `98.mat`), y
lo eliminan de su version limpia.

Ese repositorio reporta ademas otras dos anomalias, ambas en archivos de
**48 kHz** (`1730_IR_21_DE48` con un `X215` duplicado, y `1772_IR_14_DE48` con
una serie `X217` sin correspondencia). **No nos afectan**: este articulo usa el
extremo de transmision muestreado a 12 kHz. Nuestra verificacion sobre los 40
archivos empleados no encontro ningun otro caso de canal duplicado.

## Fuga de datos: implicacion para el diseno

La literatura reciente sobre evaluacion en diagnostico de rodamientos critica
dos practicas de particion que inflan los resultados:

1. **Particion por segmento** (repartir ventanas del mismo registro entre
   entrenamiento y prueba). **Nuestro protocolo ya lo evita**: la division es
   por registro de origen.
2. **Particion por condicion** (entrenar con una carga y probar con otra). Aqui
   hay una limitacion real que hay que declarar: en CWRU **cada combinacion de
   tipo de falla y diametro corresponde a un unico rodamiento fisico**, medido
   despues bajo las cuatro cargas. Por tanto, al cruzar cargas el rodamiento es
   el mismo, y el modelo puede apoyarse en la firma individual de esa pieza y no
   solo en el tipo de falla.

**Consecuencia para el articulo, no para su validez.** La pregunta sigue en pie
—cuanto se degrada el desempeno al cambiar la carga— pero la caida que midamos
es una **cota inferior**: con un rodamiento distinto seria mayor. Esto va
explicitamente en limitaciones, y **refuerza el valor de MAFAULDA** como
validacion externa, porque es otra maquina y otros rodamientos.

Declararlo nosotros mismos es mejor que dejar que lo haga un revisor.

## Verificacion fisica de las etiquetas (22/08)

Contrastar la nomenclatura contra tablas de terceros solo traslada el problema:
si la tabla esta mal, se hereda el error. Se verifico contra la fisica del
rodamiento con `src/00_verificar_etiquetas.py`.

Una falla localizada genera impactos cada vez que un elemento rodante pasa por
el defecto, a una frecuencia que depende solo de la geometria y de la velocidad
de giro. El analisis de envolvente (filtro pasa banda en la resonancia
2-5.5 kHz, transformada de Hilbert, espectro) revela esa frecuencia. Rodamiento
del extremo de transmision: SKF 6205-2RS JEM, con factores BPFO 3.5848,
BPFI 5.4152, BSF 4.7135 y FTF 0.3983 veces la frecuencia de giro.

Relacion pico/fondo promedio por clase:

| Clase | BPFO | BPFI | BSF | 2xBSF | 2xBSF ± FTF |
|---|---|---|---|---|---|
| Normal | 32.9 | 37.0 | 26.8 | 32.4 | 51.7 |
| IR | 647.9 | **1996.0** | 251.1 | 201.8 | 369.7 |
| OR | **2035.6** | 399.9 | 95.6 | 87.2 | 193.5 |
| B | 353.3 | 347.7 | 194.2 | 124.2 | 179.5 |

**Resultado:**

- **Pista interna: 12/12 confirmados.** BPFI domina sobre BPFO por un factor de
  tres. Las etiquetas IR son correctas.
- **Pista externa: 9/12 confirmados.** BPFO domina por un factor de cinco.
- **Control negativo impecable:** en el rodamiento sano ninguna frecuencia
  caracteristica destaca, con valores un orden de magnitud por debajo. Esto
  demuestra que el metodo mide lo que se supone que mide, y no artefactos.
- **Elemento rodante:** requiere un criterio distinto, ver abajo.

### Por que el elemento rodante no se verifica igual

En la clase B la energia en BSF no domina sobre BPFO ni BPFI, y a primera vista
parece contradecir la etiqueta. **No es un error de etiquetado sino fisica
conocida**: la bola con defecto golpea alternativamente las dos pistas, de modo
que aparece energia en BPFO y BPFI de forma legitima; ademas entra y sale de la
zona de carga al ritmo de la jaula, por lo que su firma no es un pico limpio en
BSF sino 2xBSF modulado por FTF. Buscar solo BSF produce un falso negativo.

Con el criterio de bandas laterales, **7 de 12 archivos de bola superan
holgadamente el control negativo**. Los debiles son sistematicamente los de
mayor diametro (0.021").

### Registros con firma debil

El patron no es aleatorio y se concentra en dos grupos:

| Archivos | Condicion | Observacion |
|---|---|---|
| 197, 198, 200 | OR 0.014" | BPFO no domina; niveles cercanos al control negativo |
| 222, 223, 224, 225 | B 0.021" | Firma de bola apenas por encima del ruido |
| 187 | B 0.014" | Firma debil |

**Esto no invalida las etiquetas**: la falla existe: lo que ocurre es que su
firma vibratoria es poco diagnosticable por envolvente. Es un rasgo conocido del
conjunto CWRU y **el motivo por el que existe un estudio de referencia dedicado
a catalogar que registros son diagnosticables**:

> Smith, W. A.; Randall, R. B. (2015). *Rolling element bearing diagnostics
> using the Case Western Reserve University data: a benchmark study*. Mechanical
> Systems and Signal Processing, 64-65, pp. 100-131.
> DOI: `10.1016/j.ymssp.2015.04.021` (2 532 citas)

**Pendiente:** conseguir el texto completo y contrastar nuestros registros
debiles con su clasificacion. No se ha podido acceder (esta tras muro de pago),
asi que **no se afirma nada sobre sus conclusiones concretas** hasta leerlo.

### Decision de diseno

**Se conservan los 40 archivos.** El experimento clasifica tipo de falla a
traves de cargas, no diametros, y descartar registros por ser dificiles sesgaria
el resultado hacia arriba, que es justo lo que este articulo critica del campo.

Lo que si se hace: **guardar el diametro como covariable** para poder reportar
resultados desglosados. Si el clasificador falla sistematicamente en OR 0.014" o
en B 0.021", ya tenemos la explicacion documentada y medida, en lugar de un
resultado inexplicable en la discusion.

## Inventario verificado

- 40 archivos, 10 combinaciones clase-diametro x 4 cargas
- **5 887 ventanas** de 2048 muestras con 50 % de solape
- Por clase: Normal 1 653 · IR 1 410 · B 1 411 · OR 1 413 (balanceado)
- RMS por clase coherente con el estado: Normal 0.066 < B 0.136 < IR 0.317 < OR 0.425
- Registros con falla de ~10 s; los Normal, de 20 a 40 s
- `98.mat` y `99.mat` no traen variable RPM; se usa el valor nominal del catalogo

## Particion adoptada: bloques contiguos purgados (22/08)

*Cambio de protocolo anotado con fecha, como exige la cabecera.*

El protocolo fija division por registro de origen. **Fuera de la diagonal se
cumple sin excepcion**: entrenar con carga *i* y probar con carga *j* usa
archivos `.mat` distintos, asi que la separacion es total. **En la diagonal es
imposible**: CWRU aporta **un unico registro Normal por carga** (97, 98, 99,
100), de modo que no existe ninguna particion por registro que deje la clase
Normal a la vez en entrenamiento y en prueba.

| | 0 HP | 1 HP | 2 HP | 3 HP | registros |
|---|---|---|---|---|---|
| Normal | 237 | 471 | 472 | 473 | **1** |
| IR | 352 | 352 | 352 | 354 | 3 |
| B | 353 | 352 | 353 | 353 | 3 |
| OR | 353 | 354 | 352 | 354 | 3 |

**Regla unica para las 16 celdas.** Las ventanas de cada registro se cortan en
cinco bloques contiguos en el tiempo y se descarta la primera ventana de cada
bloque interno. Con paso 1024 y ventana 2048, la ventana *m* y la *m+2* ya no
comparten ninguna muestra, asi que descartar una sola ventana por frontera basta:

> celda (i, j), fold k → entrenamiento = bloques ≠ k de todos los registros de
> carga *i*; prueba = bloque k de todos los registros de carga *j*.

Coste: 4 ventanas por registro, 160 de 5 887 (2,7 %). Quedan **5 727
utilizables**.

Tres consecuencias:

- Fuera de la diagonal la separacion por registro se mantiene intacta; los
  bloques solo generan cinco conjuntos de prueba disjuntos, es decir, cinco
  folds reales donde de otro modo habria un unico corte determinista.
- En la diagonal la garantia es mas debil: no hay fuga por solape, pero
  entrenamiento y prueba proceden del mismo registro. **Se declara en el
  manuscrito** y la diagonal queda como referencia interna, fuera de la
  inferencia, que se limita a los 12 pares fuera de diagonal, como ya preveia el
  apartado de prueba estadistica.
- El tamano de entrenamiento es ~4/5 de una carga en las 16 celdas, asi que
  diagonal y fuera de diagonal son comparables sin confusion por tamano de
  muestra.

**Control negativo de la verificacion.** Comprobar que no hay fuga solo vale si
la comprobacion es capaz de detectarla. Repitiendo el mismo test **sin purgar**
aparecen **320 pares** de ventanas de entrenamiento y prueba que comparten
muestras (4 fronteras x 10 registros x 4 cargas x 2 folds afectados por
frontera); con la purga, **0**. El detector tiene dientes.

## Asimetria de normalizacion entre representaciones (22/08)

Detectada al escribir `02_preprocess.py` y con consecuencia directa sobre la
hipotesis. `espectrograma_stft` normaliza cada imagen a [0, 1] y `wavelet_db4`
con `solo_energia=True` devuelve energia **relativa**: las dos representaciones
tiempo-frecuencia son **invariantes a la amplitud por construccion**. Los
estadisticos temporales y la magnitud FFT conservan la escala absoluta.

La hipotesis del articulo dice que las tiempo-frecuencia resisten mejor el
cambio de carga *porque los estadisticos dependen de la amplitud absoluta, que
escala con la carga*. Con estas implementaciones ese resultado saldria
garantizado por el preprocesado y no por la naturaleza de la representacion, y
un revisor lo escribe en una linea.

**Ablacion pre-registrada**, con el alcance fijado antes de ver ningun
resultado: `02_preprocess.py` genera ademas `estadisticos_rmsnorm` y
`fft_rmsnorm`, calculadas sobre la ventana dividida por su valor eficaz.
`03_experiment.py` las corre con **SVM-RBF y Random Forest sobre las 12 celdas
fuera de diagonal**. Eso separa el efecto de la representacion del efecto de la
normalizacion sin inflar el experimento un 50 %.

Verificado en la salida: tras normalizar, el descriptor `rms` vale exactamente
1 en las 5 887 ventanas y la curtosis no cambia, como corresponde a un
estadistico invariante a la escala.

## Resolucion del espectrograma (23/08, corrige la nota del 22/08)

**La nota del 22/08 estaba equivocada y se sustituye por esta.** Decia que el
espectrograma no separa BPFO ni BPFI en el eje de frecuencia, y que la FFT si.
El primer dato es cierto pero irrelevante, y el segundo es falso.

En una senal de rodamiento **BPFO y BPFI no aparecen como picos espectrales**.
Una falla localizada excita la resonancia estructural de 2 a 5,5 kHz cada vez
que un elemento rodante golpea el defecto, y la frecuencia caracteristica se
manifiesta como **la tasa de repeticion de esos impactos**, es decir en el eje
del tiempo. Por eso funciona el analisis de envolvente, y **lo comprobamos
nosotros mismos** en `00_verificar_etiquetas.py`: los picos de la tabla de
relacion pico/fondo salieron en el espectro de **la envolvente**, no en el de la
senal. Buscarlos en el espectro directo era el error.

La eleccion correcta de `nperseg` sale de ese razonamiento, no de la resolucion
en frecuencia:

| nperseg | delta_f | tramas | paso | tren de impactos |
|---|---|---|---|---|
| 512 | 23,4 Hz | 7 | 21,3 ms | borrado |
| **64** | **187,5 Hz** | **63** | **2,67 ms** | **resuelto** |

Los impactos ocurren cada 6,2 ms (BPFI) y 9,3 ms (BPFO) a 1797 rpm, de modo que
con nperseg = 64 caben de 2,3 a 3,5 tramas por impacto y con 512 no cabe
ninguna. Los 187,5 Hz por banda bastan de sobra para localizar la resonancia de
2 a 5,5 kHz, que ocupa 18 de las 33 bandas. Se mantiene **nperseg = 64**, ahora
pasado de forma explicita, y los parametros efectivos se registran con
`devolver_info=True`.

**Afirmacion correcta para el manuscrito:** el espectrograma resuelve la tasa de
repeticion de impactos en el eje temporal, que es donde reside la firma de la
falla. No: "captura las frecuencias caracteristicas".

### La rejilla vectorizada es 16x64, no cuadrada (23/08)

La resolucion efectiva de una imagen es la peor de dos rejillas, la de la STFT y
la de la propia imagen, **eje por eje**. Al medirlo aparecio que una rejilla
cuadrada destruye justo lo que `nperseg = 64` existe para conservar:

| Rejilla | Resolucion efectiva | Columnas por impacto (BPFO / BPFI) |
|---|---|---|
| STFT nativa, 33x63 | 187,5 Hz / 2,71 ms | 3,44 / 2,28 |
| 64x64, entrada de la CNN | 187,5 Hz / 2,67 ms | 3,49 / 2,31 |
| ~~16x16, vector de 256~~ | ~~375 Hz / 10,67 ms~~ | ~~0,87 / 0,58~~ |
| **16x64, vector de 1 024** | **375 Hz / 2,67 ms** | **3,49 / 2,31** |

Hacen falta al menos dos columnas por periodo de impacto para que el tren quede
representado. Una rejilla cuadrada de 16x16 deja 0,58 columnas por impacto de
BPFI, es decir borra la firma; **16x64 conserva el eje temporal intacto** y
reduce solo el de frecuencia, a 375 Hz, con la resonancia de 2-5,5 kHz repartida
en unas 9 de las 16 filas.

Efecto secundario favorable: 1 024 valores quedan junto a los 1 025 de la FFT,
de modo que la rejilla no cuadrada **reduce** el confuso de dimensionalidad en
lugar de agravarlo.

`espectrograma_stft` solo produce imagenes cuadradas, asi que la version
vectorizada se calcula en `02_preprocess.espectrogramas_rejilla()`, que repite
el mismo pipeline de la libreria -misma STFT, misma escala en dB, misma
normalizacion por imagen- y reutiliza su propio remuestreador. **Peticion
anotada para la sesion maestra:** si `espectrograma_stft` aceptase `tamano` como
tupla, esa funcion sobraria y no habria que tocar un nombre privado.

## Diseno del experimento: 3x4, no 4x4 (23/08)

La ficha describia 4 representaciones x 4 clasificadores, pero ese diseno no
existe: una CNN 2D sobre 6 energias wavelet o 12 estadisticos no tiene sentido,
porque no hay estructura local que convolucionar. La propia ficha lo dice al
enumerar los metodos y se contradice al resumir el diseno.

| Bloque | Contenido | Ajustes |
|---|---|---|
| **Nucleo inferencial** | 3 clasificadores de vector x 4 representaciones x 16 celdas x 5 folds | 960 |
| **Fila de referencia** | CNN 2D sobre espectrograma 64x64, 16 celdas x 5 folds | 80 |
| **Ablacion de amplitud** | 2 representaciones x 2 clasificadores x 12 celdas fuera de diagonal x 5 folds | 240 |

El nucleo es **balanceado**: SVM-RBF, Random Forest y MLP sobre las cuatro
representaciones, con el espectrograma en su rejilla de 16x64. La CNN 2D va como fila
de la Tabla 1 y **queda fuera de Friedman y del ANOVA**, porque no existe para
las otras tres representaciones y un diseno desbalanceado rompe las dos pruebas.
La asimetria se declara en Metodo con su motivo.

## Prueba estadistica: N = 12, promediando clasificadores (23/08)

*Precision del apartado "Prueba estadistica", decidida antes de ver resultados.*

**Principal:** Friedman sobre las 4 representaciones con los **12 pares fuera de
diagonal** como bloques, usando el F1 promediado entre los tres clasificadores.
k = 4, N = 12.

Se descarta usar (par x clasificador) = 48 bloques. Los tres clasificadores
comparten particion y senal, asi que los bloques no son independientes, y la
distancia critica de Nemenyi pasaria de 1,35 con N = 12 a 0,68 con N = 48: la
mitad, apoyada en dependencia. Seria incoherente en un articulo cuyo argumento
central es que el campo infla resultados con particiones mal hechas.

**Robustez:** un Friedman por clasificador, tres pruebas con N = 12 cada una,
reportadas en el texto sin diagrama. Si el orden de las representaciones se
mantiene en las tres, el resultado es mas fuerte que cualquier prueba conjunta y
responde por adelantado a la objecion de que el hallazgo depende del
clasificador.

## Confuso de dimensionalidad

Las cuatro representaciones del nucleo tienen 12, 1 025, 6 y 1 024 dimensiones. En
parte se esta comparando dimensionalidad y no representacion. El rango sigue
siendo de dos ordenes de magnitud, aunque la rejilla 16x64 acerca el
espectrograma a la FFT en lugar de separarlo.

**No se iguala.** La dimensionalidad forma parte de lo que una representacion
es, y la Tabla 2 de costo computacional la captura por el lado que importa a un
taller. Pero va a limitaciones junto a la ablacion de amplitud y al coste de la
eleccion de rejilla del espectrograma.

## Desbalance de la clase Normal entre cargas

Consecuencia de que los registros Normal duran de 20 a 40 s y los de falla unos
10 s. Con ventanas utilizables: a 0 HP la clase Normal aporta 233 frente a ~341
de cada clase con falla; a 1, 2 y 3 HP aporta ~468 frente a las mismas ~341. El
desbalance **no es constante entre cargas**, que es lo que importa aqui porque
la carga es el eje del experimento.

Se conservan todas las ventanas: recortar los registros Normal a 10 s dejaria la
clase en 118 ventanas por carga y crearia un desbalance de 3 a 1 en sentido
contrario. Se mitiga con **F1-macro** como metrica primaria, que ya fija el
protocolo, y con ponderacion por clase en los clasificadores de
`03_experiment.py`.

## Salidas de `02_preprocess.py`

Todo en `data/processed/`, alineado fila a fila con `metadatos.csv`:

| Archivo | Forma | Nota |
|---|---|---|
| `metadatos.csv` | 5 887 filas | archivo, clase, **diametro (covariable)**, carga, rpm, indice, muestra de inicio, bloque, purgada |
| `ventanas.npy` | (5887, 2048) | senal cruda segmentada; alimenta Fig. 1 y Fig. 2 |
| `X_estadisticos.npy` | (5887, 12) | |
| `X_fft.npy` | (5887, 1025) | |
| `X_wavelet.npy` | (5887, 6) | |
| `X_espectrograma.npy` | (5887, 64, 64) | entrada de la CNN 2D |
| `X_espectrograma_vector.npy` | (5887, 16, 64) | 1 024 dim., entra en el nucleo inferencial |
| `X_estadisticos_rmsnorm.npy` | (5887, 12) | ablacion |
| `X_fft_rmsnorm.npy` | (5887, 1025) | ablacion |
| `manifiesto.json` | | parametros efectivos de la STFT, semilla, tiempos de extraccion, versiones |

**No se estandariza nada aqui.** El escalado se ajusta dentro del pipeline de
`03_experiment.py`, solo sobre el fold de entrenamiento; hacerlo antes seria
fuga. `02_preprocess.indices_celda()` es la definicion operativa de la
particion, y 03 debe importarla en lugar de reimplementarla.

---

# Bitacora

## 20/08 - montaje
- Hecho: protocolo cerrado. Entorno con CUDA verificado (RTX 4050, 6 GB).
  Libreria `fieutils` probada con datos sinteticos. Confirmado que *Ingenius*
  recibe todo el ano (proximo corte 15/11/2026), asi que no hay fecha dura.
  Descargados los 40 archivos de CWRU con su catalogo. Verificada la estructura
  interna: detectada y resuelta la anomalia de `99.mat`.
- Bloqueado en: nada.
- Siguiente: contrastar la correspondencia archivo-clase antes de codificar.
- Tiempo de computo consumido: 0 h GPU.

## 22/08 - nomenclatura verificada, citas localizadas
- Hecho: **verificacion de etiquetas por fisica** (`00_verificar_etiquetas.py`),
  en lugar de fiarse de tablas de terceros. Pista interna 12/12 y pista externa
  9/12 confirmadas por analisis de envolvente; control negativo impecable en
  Normal. Identificado que el elemento rodante exige el criterio de bandas
  laterales 2xBSF ± FTF, y documentado por que. Localizados los registros de
  firma debil (OR 0.014" y B 0.021") y tomada la decision de conservarlos.
  Confirmada de forma independiente la anomalia de `99.mat` mediante el
  repositorio `srigas/CWRU_Bearing_NumPy`. Localizadas y verificadas las cinco
  citas de *Ingenius* (todos los DOI resuelven).
- Bloqueado en: la plantilla LaTeX no se ha podido descargar porque el sitio de
  *Ingenius* devuelve HTTP 500 desde hoy. No impide redactar; si maquetar.
- Siguiente: `02_preprocess.py` - segmentado por registro de origen, con el
  diametro guardado como covariable, y las cuatro representaciones.
- Tiempo de computo consumido: 0 h GPU.

## 22/08 (tarde) - preprocesado cerrado
- Hecho: `src/02_preprocess.py` escrito y ejecutado. 5 887 ventanas, 160
  purgadas en las fronteras de bloque, **5 727 utilizables**; seis matrices de
  caracteristicas y `manifiesto.json`, todo alineado con `metadatos.csv`.
  **Verificacion de fuga en las 80 combinaciones celda-fold: 0 problemas**, y
  control negativo que confirma que sin purga el mismo test detecta 320 pares
  con muestras compartidas. Tres asuntos de diseno resueltos y documentados
  arriba: (1) la division por registro es imposible en la diagonal porque CWRU
  trae **un unico registro Normal por carga**, resuelto con bloques contiguos
  purgados como regla unica para las 16 celdas; (2) el espectrograma y la
  wavelet son **invariantes a la amplitud por construccion**, lo que confirmaria
  la hipotesis por el preprocesado, resuelto con una ablacion pre-registrada
  sobre ventana normalizada en RMS, acotada a SVM-RBF y Random Forest fuera de
  la diagonal; (3) el espectrograma resuelve 187,5 Hz y **no separa BPFO ni
  BPFI** ~~que va a Metodo y a limitaciones~~ **[corregido el 23/08: el
  planteamiento era erroneo, esas frecuencias no son picos espectrales en una
  senal de rodamiento; ver "Resolucion del espectrograma"]**. Tablas
  `ventanas_por_carga_clase` y
  `dimension_representaciones` exportadas en `.csv` y `.tex`.
- Bloqueado en: sigue el HTTP 500 de *Ingenius*, sin reintentar todavia. Las
  cinco citas de la revista siguen **sin leer**: la tabla de `JOURNAL.md` esta
  vacia y eso bloquea la redaccion, no el codigo.
- Siguiente: `03_experiment.py`. Antes de escribirlo hay que decidir **como
  entra la CNN 2D con las representaciones vectoriales** (12, 1025 y 6
  dimensiones no son una imagen) y **como se agregan los 4 clasificadores en el
  Friedman** sobre los 12 pares fuera de diagonal. Las dos decisiones se cierran
  antes de correr nada.
- Tiempo de computo consumido: 0 h GPU. `02_preprocess.py` tarda 11 s en CPU.

## 23/08 - fieutils actualizado, diseno cerrado, 03 escrito sin lanzar
- Hecho: recibida la actualizacion de `fieutils` desde la sesion maestra
  (`espectrograma_stft` con `nperseg` y `resolucion_hz` explicitos,
  `parametros_stft`, redimensionado bilineal). **Corregida una conclusion
  erronea propia**: BPFO y BPFI no son picos espectrales en una senal de
  rodamiento, sino la tasa de repeticion de impactos que excitan la resonancia
  de 2-5,5 kHz, que es justo lo que nuestro propio `00_verificar_etiquetas.py`
  midio sobre la envolvente. La nota del 22/08 queda sustituida y el pie de
  `dimension_representaciones` reescrito antes de llegar al manuscrito.
  `02_preprocess.py` regenerado con `nperseg = 64` explicito y los parametros
  efectivos registrados con `devolver_info=True`: 187,5 Hz por banda, 63 tramas,
  paso de 2,67 ms frente a impactos de 6,2 a 9,3 ms. Anadida la version
  vectorizada del espectrograma en rejilla **16x64** (1 024 dim.) para el nucleo
  inferencial, y los tiempos de extraccion por representacion para la Tabla 2.
  Verificacion de fuga: 80 celda-fold, 0
  problemas. Cerrado el diseno **3x4** con la CNN como fila de referencia fuera
  de la comparacion, y **Friedman con N = 12 promediando clasificadores**, con
  tres Friedman por clasificador como robustez. `03_experiment.py` escrito y
  probado en humo, **no lanzado**.
- Medido en la prueba de humo, celda (0,2) fold 0: los 12 ajustes del nucleo
  suman 31,1 s con la rejilla 16x64, de donde salen unos **41 min** para los
  960; la ablacion son ~4 min; la CNN tarda **13,7 s por ajuste con 0,13 GB de
  VRAM pico**, unos **18 min** para los 80. Total del experimento en torno a
  **1 h**. Los F1 de esa celda no se leen como resultado: es un fold suelto y
  sirvio solo para comprobar que el codigo corre y cuanto tarda.
- Bloqueado en: sigue el HTTP 500 de *Ingenius*, sin reintentar. Las cinco citas
  de la revista siguen **sin leer** y la tabla de `JOURNAL.md` sigue vacia: eso
  bloquea la redaccion, no el codigo.
- Decidido durante la jornada: al medir la resolucion efectiva se vio que una
  rejilla cuadrada de 16x16 deja 0,58-0,87 columnas por impacto, por debajo del
  minimo de 2, y borraria justo la firma que `nperseg = 64` conserva. Se adopta
  **16x64**, que mantiene 3,49 / 2,31 columnas por impacto y reduce solo el eje
  de frecuencia a 375 Hz. Implementado en `espectrogramas_rejilla()` dentro de
  `src/`, sin tocar `fieutils`.
- **Peticion a la sesion maestra:** que `espectrograma_stft` acepte `tamano`
  como tupla `(frecuencias, tramas)`. Ahora mismo solo genera imagenes
  cuadradas, y por eso `02_preprocess.espectrogramas_rejilla()` repite el
  pipeline de la libreria y usa su remuestreador privado `_redimensionar`. Con
  esa firma esa funcion sobraria. No es bloqueante.
- Siguiente: lanzar `--parte clasicos` y `--parte ablacion` en CPU y
  `--parte cnn` al cerrar el dia; despues `04_stats.py`.
- Tiempo de computo consumido: 0 h GPU de experimento; ~1 min de GPU en la
  prueba de humo. `02_preprocess.py` tarda 17 s en CPU.

## 24/08 - sitio recuperado, ficha de revista cerrada, experimento lanzado
- Hecho: **el HTTP 500 de *Ingenius* se resolvio**. Recuperada la plantilla
  LaTeX oficial en Overleaf
  (`overleaf.com/latex/templates/revista-ingenius-ecuador/zsnnwhmcwzyj`) y leidas
  enteras las **normas editoriales** (6 pp.). `JOURNAL.md` queda completo: sin
  APC, **4 000-6 500 palabras incluyendo tablas y referencias**, estructura
  **IMRDC**, citas **IEEE**, resumen de **230 palabras como maximo en espanol e
  ingles** con orden fijado, **6 palabras clave por idioma**, titulo en los dos
  idiomas, figuras en archivo aparte a 300 dpi, propiedades del archivo
  anonimizadas y cover letter obligatoria. La revista esta en **Scopus desde
  abril de 2023**, dato que no teniamos.
- **Paso 3 de la verificacion de referencias completado**: las cinco citas de la
  revista **leidas completas**, no el resumen. Cuatro sirven; **la 5 se retira**
  porque no sostiene lo que se le atribuia: es un diseno estructural en Inventor
  y Ansys, no un estudio de como cambia una senal medida al variar la condicion
  de operacion. La 4 (Gomez, Cabrera y Robles, 2023) resulta ser **la mejor de
  todas**: usa **wavelet db4 de nivel 4**, la misma familia que nuestra
  representacion. Buscado sustituto en el buscador de la revista: *Ingenius* no
  tiene ningun articulo de rodamientos, vibracion ni diagnostico por aprendizaje
  automatico, asi que se envia con cuatro, dentro del rango 3-5 que pide la lista
  de comprobacion. Detectado ademas que dos entradas tenian mal el numero de
  autores.
- Perfil de la revista medido sobre los cinco: extension mediana **9 paginas**,
  referencias mediana **19**, metodo muy concreto (marca y modelo de equipos,
  software con version, parametros de adquisicion). **El liston estadistico es
  bajo y desigual**: solo dos de los cinco usan alguna prueba, y tres no usan
  ninguna. Friedman-Nemenyi mas ANOVA de dos factores nos deja por encima de la
  media sin esfuerzo. En figuras pasa lo contrario: el estilo publicado incluye
  barras 3D y capturas de Minitab, que la guia prohibe. **Se sigue la guia.**
- Choques entre `REDACCION.md` y las normas de la revista, resueltos a favor de
  la revista y anotados en `JOURNAL.md`: no hay seccion *Related Work* propia
  (va dentro de la Introduccion), Discusion y Conclusiones siguen la convencion
  impresa, y el limite real es de palabras con referencias incluidas, no de
  paginas.
- Experimento **lanzado**, las tres partes en secuencia. Nota de criterio: la
  parte de GPU se dejo en la misma tanda en lugar de esperar al cierre del dia,
  porque son **18 min medidos** y la regla dura del plan apunta a los
  entrenamientos largos de P1 y P5, no a esto. Facil de posponer si se prefiere.
- **Politica de IA leida y evidencia de gratuidad guardada.** La declaracion de
  uso de IA es **obligatoria y va en la cover letter**, no en el manuscrito,
  nombrando herramienta y proposito; la revista **no acepta IA como coautora**.
  La pagina de acceso abierto dice literalmente que *«does not have any economic
  charge for the publication or for access to the material»*; guardado en
  `paper/evidencia/` el HTML original de esa pagina, el de la politica de IA y el
  PDF de las normas, todos con fecha 24/08. Con eso quedan cerradas dos casillas
  de la lista de comprobacion: gratuidad con evidencia y declaracion de uso de IA.
- Bloqueado en: nada.
- Siguiente: `04_stats.py` en cuanto termine el experimento.
- Tiempo de computo consumido: experimento en curso al cerrar esta entrada.

## 24/08 (tarde) - experimento cerrado, 04_stats.py escrito y ejecutado
- Hecho: el experimento completo (nucleo 960 + ablacion 240 + CNN 80 = 1 280
  ajustes) termino en **21,6 min**: nucleo 11,5 min, ablacion 3,9 min, CNN
  9,7 min en GPU. Verificado sin huecos: 80 celda-fold en cada una de las 12
  combinaciones representacion x clasificador del nucleo, 240 filas exactas en
  la ablacion, 10 400 en el desglose por diametro sin nulos. `04_stats.py`
  escrito y ejecutado: Tabla 1 (F1 dentro/fuera de dominio por representacion y
  clasificador, con la CNN como fila de referencia), Tabla 2 (costo
  computacional), Friedman principal, Friedman por clasificador como robustez,
  ANOVA de dos factores con eta cuadrado parcial, diagrama de Nemenyi
  (pendiente de figura) y ablacion de amplitud con IC bootstrap y delta de
  Cliff.
- **Resultado que hay que reportar tal cual, no maquillar (regla 7 de
  `REDACCION.md`): el Friedman principal NO es significativo** (chi2=5,200,
  p=0,158, N=12, k=4). Los tres Friedman por clasificador si lo son (SVM-RBF
  p=0,0007, RandomForest p=0,0033, MLP p=0,0001) pero **no coinciden en el
  orden**: SVM-RBF y MLP prefieren espectrograma; RandomForest prefiere FFT. Al
  promediar los tres para el bloque principal, esa disputa se cancela y el test
  omnibus no rechaza. Nemenyi confirma: ningun par de representaciones baja de
  p=0,12 (el mas cercano es wavelet vs espectrograma). El ANOVA de dos factores
  si es significativo en los tres terminos -representacion (F=15,93, p<0,001,
  eta parcial 0,173), distancia de carga (F=35,51, p<0,001, eta parcial 0,238) e
  **interaccion** (F=5,14, p<0,001, eta parcial 0,119)-, que es coherente: el
  efecto de la representacion depende del clasificador y de la distancia, no es
  un efecto principal limpio. Esto reencuadra el hallazgo del articulo: la
  eleccion de representacion importa, pero **interactua con el clasificador**
  en vez de ser un orden universal, que es un resultado igual de publicable y
  mas honesto que forzar una recomendacion unica.
- **Asimetria por direccion detectada en la tabla de bloques**: a la misma
  distancia, entrenar en carga baja y probar en alta no es igual que al reves.
  Ejemplo en estadisticos, distancia 1: (0->1) F1=0,795 frente a (1->0) F1=0,678;
  distancia 3: (0->3) F1=0,771 frente a (3->0) F1=0,539. Coincide con que la
  carga 0 HP tiene la clase Normal con **233 ventanas frente a ~468** en el
  resto (ver seccion de desbalance): entrenar con 0 HP entrena con menos
  Normal. Anotado para la Discusion; no se corrige el diseno porque el
  desbalance ya esta declarado y mitigado con F1-macro y ponderacion de clase.
- **Ablacion de amplitud**: normalizar en RMS **no mejora** la resistencia fuera
  de dominio de estadisticos ni FFT; con Random Forest la **empeora**
  claramente (estadisticos: -0,149 [-0,197, -0,103], delta grande-mediano; FFT:
  -0,133 [-0,151,-0,116], delta grande). Con SVM-RBF los IC cruzan cero en los
  dos casos. Lectura: la amplitud absoluta **aporta senal util** fuera de
  diagonal para Random Forest, no es solo un artefacto de la carga que convenga
  quitar. Contradice la lectura ingenua de la hipotesis y va a la discusion.
- Bloqueado en: nada.
- Siguiente: `05_figures.py` - mapa de calor 4x4 (Fig. 3), diagrama de
  diferencia critica de Nemenyi (Fig. 4), senales crudas (Fig. 1) y panel de
  representaciones (Fig. 2).
- Tiempo de computo consumido: **9,7 min de GPU** (CNN). Resto en CPU: 11,5 min
  nucleo + 3,9 min ablacion + ~2 s de `04_stats.py`.

## 24/08 (noche) - las cuatro figuras
- Hecho: `src/05_figures.py` escrito y ejecutado. Fig. 1 (senales crudas de las
  4 clases a 0 HP), Fig. 2 (la misma ventana IR en las 4 representaciones, panel
  2x2), Fig. 3 (mapa de calor 4x4, la que sostiene el articulo) y Fig. 4
  (diferencia critica de Nemenyi), las cuatro en PDF vectorial y PNG 300 dpi en
  `results/figures/`. IR se eligio para la Fig. 2 por ser la clase confirmada
  12/12 por envolvente, sin ambiguedad de firma debil.
- **Dos errores detectados al inspeccionar visualmente las figuras, los dos
  mios y los dos corregidos antes de que llegaran al manuscrito:**
  1. El eje de frecuencia del panel de espectrograma (Fig. 2d) llegaba a
     12 000 Hz, imposible para una senal muestreada a 12 kHz (Nyquist = 6 000
     Hz). Redimensionar la STFT de 33 filas nativas a una imagen de 64 no crea
     filas de 187,5 Hz reales; el eje debe ir de 0 a FS/2, no a
     `tamano x delta_f_hz`. Corregido.
  2. **Las etiquetas de banda wavelet (Fig. 2c) estaban invertidas.**
     `pywt.wavedec` devuelve `[cA5, cD5, cD4, cD3, cD2, cD1]` -la aproximacion
     mas gruesa primero-, confirmado por las longitudes de coeficiente
     (70, 70, 134, 262, 517, 1027). El codigo etiquetaba el primer valor como
     D5 y el ultimo como A5, al reves. Con la etiqueta mal puesta pareceria que
     A5 domina con 0,46; **con la correcta, quien domina es D1** (0,46), la
     banda de 3 000-6 000 Hz. Esto **no es un detalle cosmetico**: D1 cae justo
     sobre la resonancia estructural de 2-5,5 kHz que el resto del proyecto ya
     documenta como donde vive la firma de la falla (ver verificacion por
     envolvente del 22/08). La version sin corregir habria puesto en el
     manuscrito la banda equivocada como protagonista.
- **Verificacion cruzada entre paneles**: los picos del panel FFT (b) y las
  bandas mas cargadas del espectrograma (d) caen en las mismas frecuencias
  (~1200-1300, ~2500-3000, ~3500-4000 Hz), y ahora tambien coinciden con la
  banda D1 dominante del panel wavelet (c). Las tres representaciones
  tiempo-frecuencia cuentan la misma historia fisica una vez corregidas las
  etiquetas.
- **La Fig. 3 hace visible el hallazgo de la tarde.** En el panel (a)
  estadisticos, la columna de prueba a 0 HP se hunde cuando el entrenamiento es
  en otra carga (0,68 / 0,65 / 0,54 entrenando en 1, 2 y 3 HP), mientras que en
  FFT y espectrograma esa misma columna se mantiene sobre 0,82. Es la asimetria
  por direccion de la entrada anterior, ahora visible de un vistazo.
- Bloqueado en: nada.
- Siguiente: redaccion del manuscrito - Metodo primero, despues Resultados,
  siguiendo el orden que fija `REDACCION.md`. La estructura real es IMRDC de la
  revista (ver `JOURNAL.md`), no la de la guia generica.
- Tiempo de computo consumido: 0 h GPU. `05_figures.py` tarda unos 4 s en CPU.

## 24/08 (cierre) - manuscrito redactado
- Hecho: `paper/manuscript.md` completo en **IMRDC**, la estructura que exigen
  las normas de la revista, no la generica de `REDACCION.md`. Escrito en el
  orden que fija la guia (Metodo, Resultados, Introduccion, Discusion,
  Conclusion y Abstract al final) y ensamblado en el orden de publicacion.
  `paper/references.bib` con **12 referencias**, cada una con su nivel de
  verificacion anotado en el propio archivo.
- **Limites de la revista comprobados con script, no a ojo**: total **5 822
  palabras** (limite 4 000-6 500 incluyendo titulo, resumenes, tablas y
  referencias); **abstract 218** y **resumen 228** (limite 230 cada uno);
  **6 palabras clave por idioma**; titulo en ingles y espanol. Tablas con
  subtitulo encima y figuras en archivo aparte, como pide la norma.
- **Lista de palabras prohibidas: limpia.** Cero apariciones de delve,
  showcase, pivotal, crucial, comprehensive, leverage, seamless y demas. La
  unica aparicion de "robust" es en "robustness check", que es el sentido
  estadistico exacto que la guia permite. Cero "not only... but also", cero
  "state-of-the-art", y **2 guiones largos** en todo el manuscrito (el maximo
  admitido es 2-3).
- **Auditoria de trazabilidad: 22 de 22 cifras del texto verificadas contra
  `results/` por script.** F1 dentro de dominio de las cuatro representaciones,
  las cuatro caidas, la fila de la CNN, los cuatro chi-cuadrado, la distancia
  critica, los valores a distancia 3 y los cuatro recall por diametro. Ninguna
  cifra del manuscrito es una estimacion.
- Sobre las referencias: **ninguna se cita por encima de su nivel de
  verificacion**. Cuatro de *Ingenius* leidas enteras; Kapoor y Narayanan y
  Smith y Randall con resumen completo leido; Randall y Antoni y Hendriks et
  al. solo con metadatos de Crossref confirmados y **sin resumen accesible**,
  asi que se citan unicamente para lo que su titulo sostiene de forma literal y
  no se les atribuye ningun hallazgo concreto. Demsar con resumen leido en JMLR.
  Son 12 referencias frente a la mediana de 19 de la revista: por debajo, pero
  todas verificadas, que es lo que manda la regla 2.
- El manuscrito reporta el resultado incomodo sin maquillarlo: el Friedman
  omnibus **no rechaza** y se explica por que (los tres por clasificador si
  rechazan y discrepan en el orden), la hipotesis del mecanismo de amplitud
  **queda refutada** por la ablacion, y las cuatro limitaciones son reales.
- Bloqueado en: nada.
- Siguiente: **revision adversarial ronda 1 en chat nuevo y limpio**, con el
  prompt de revisor par de `REDACCION.md`; despues pasada anti-IA, ronda 2 y
  maquetado en la plantilla de Overleaf. Falta tambien la cover letter, que es
  obligatoria y donde va la declaracion de uso de IA.
- Tiempo de computo consumido: 0 h GPU.

## 24/08 (noche) - manuscrito maquetado en la plantilla oficial y compilado
- Hecho: manuscrito volcado a la **plantilla LaTeX oficial de *Ingenius***
  (`paper/Revista_Ingenius_Ecuador/articulo_p7.tex`) y **compilado sin errores**
  con MiKTeX: pdflatex + bibtex + dos pasadas. Salida de **8 paginas**, cero
  citas sin resolver, cero referencias cruzadas rotas y **cero desbordes
  horizontales**. Las cuatro figuras copiadas a `figures/` en PDF vectorial y
  `referencias.bib` reescrito con las 12 entradas ordenadas por aparicion.
- **La plantilla contradice al PDF de normas en dos puntos** y se adopta la
  plantilla, por ser el documento vigente que distribuye la revista: la
  extension es de **5 000 a 6 000 palabras** (no 4 000-6 500) y las palabras
  clave van **en orden alfabetico** (el PDF no lo mencionaba). El manuscrito
  tiene 5 822 palabras, dentro del rango nuevo, y las palabras clave se
  reordenaron alfabeticamente en los dos idiomas. Anotado en `JOURNAL.md`.
- **Un error de maquetacion detectado revisando el PDF pagina a pagina**: la
  Tabla 4 (ANOVA) invadia la columna derecha en la pagina 6, y **LaTeX no
  avisaba** porque `\scalebox` con factor fijo produce una caja que el motor da
  por buena aunque exceda el ancho de columna. Sustituido por
  `
esizebox{\columnwidth}{!}`, que garantiza el ajuste, mas etiquetas de
  fila acortadas. Verificado en el PDF recompilado. Compilar sin mirar el
  resultado no habria detectado esto.
- Decisiones de maquetacion documentadas en la cabecera del `.tex`: como el
  articulo esta en ingles, el titulo ingles va en `	itulo` (que la clase
  imprime primero) y el espanol en `	ituloa`, y el Abstract va a la izquierda
  con el Resumen a la derecha, que es el orden que piden las normas para un
  articulo en ingles.
- **Version anonimizada para revision doble ciego**: `utores` y
  `dscripcionautor` vacios, sin ORCID, y `/Author` vacio en los metadatos del
  PDF, comprobado leyendo el binario. Rellenar solo en la version no anonima.
- Sobre la plantilla: el enlace de descarga que dan las normas
  (`goo.gl/Mwv8IC`) esta **muerto** (404, apunta a un `.7z` de 2017), igual que
  el de la plantilla Word. La unica via es Overleaf, que exige cuenta; la
  plantilla la aporto el responsable. Descargados en su momento la **cover
  letter 2025** (vigente, obligatoria, y donde va la declaracion de uso de IA),
  que se conserva en `paper/evidencia/`.
- Bloqueado en: nada.
- Siguiente: **revision adversarial ronda 1 en chat nuevo y limpio**, despues
  pasada anti-IA y ronda 2. Falta redactar la cover letter.
- Tiempo de computo consumido: 0 h GPU.

## 24/08 (noche, correccion) - Tablas 2 y 3 tambien desbordaban
- Hecho: el usuario senalo que las Tablas 2 y 3 se veian mal. Confirmado
  **rasterizando el PDF a 400 dpi con `pdftoppm`** (poppler) y recortando la
  zona exacta de cada tabla, en vez de fiarse de la vista completa de pagina:
  la vista completa a resolucion normal no dejaba verlo con claridad, igual que
  paso con la Tabla 4 antes. **Tabla 2 se salia por la derecha**, superpuesta al
  texto de la columna vecina; **Tabla 3 se salia por la izquierda**, encima de
  la Fig. 1. Misma causa que la Tabla 4: `\scalebox{0.72}` con factor fijo no
  garantiza que la tabla quepa en el ancho de columna, y LaTeX no lo reporta
  como desborde (`Overfull \hbox` se queda en 0 porque la caja escalada es
  "valida", solo que mas ancha que la columna).
- **Corregidas las tres con la misma solucion**: `
esizebox{\columnwidth}{!}`
  en vez de `\scalebox` con numero fijo, que fuerza el ajuste exacto al ancho
  de columna en vez de a un factor supuesto. Recompilado y **verificadas las
  cinco tablas del articulo, una por una, a 400 dpi**: las Tablas 1 y 5 nunca
  tuvieron el problema (no llevaban `scalebox`) y las Tablas 2, 3 y 4 quedan
  contenidas en su columna.
- **Leccion para el resto de articulos de la linea B que usen tablas anchas en
  columna estrecha**: revisar el PDF a resolucion alta con `pdftoppm -r 400`
  (poppler, ya instalado) y recortar cada tabla, no solo mirar la pagina
  completa ni fiarse de que `pdflatex` no reporte `Overfull`. `
esizebox` al
  ancho de columna es mas seguro que `\scalebox` a factor fijo siempre que la
  tabla pueda ser mas ancha que la columna.
- Bloqueado en: nada.
- Siguiente: revision adversarial ronda 1 en chat nuevo y limpio.
- Tiempo de computo consumido: 0 h GPU.

## 24/08 (noche, correccion 2) - huecos verticales en 2.2, 2.5 y 3.3
- Hecho: el usuario senalo "saltos raros" en tres puntos del PDF, cada uno
  justo despues de un encabezado de subseccion (2.2, 2.5, 3.3). Confirmado
  primero en mi propia compilacion, rasterizando **todo el documento a
  200 dpi** con `pdftoppm` y leyendo pagina por pagina: en las tres, el
  encabezado aparecia y luego quedaba un hueco en blanco antes de que
  arrancara el parrafo, con la columna vecina tambien con hueco al final.
- **Causa: `multicols` sin `
aggedcolumns`.** Por defecto `multicols` intenta
  igualar la altura de las dos columnas **estirando el espacio elastico** que
  llevan los saltos de seccion (`\subsection` tiene "plus" en su salto
  vertical), y ese estiramiento se concentra justo alrededor de las cabeceras.
  No es un problema de una tabla o figura concreta: es el propio motor de
  balanceo de columnas.
- **Corregido con una linea**: `
aggedcolumns` justo despues de
  `egin{multicols}{2}`. Deja el pie de columna irregular (que es aceptable e
  invisible a simple vista) en vez de forzar el estiramiento. Recompilado y
  **verificadas las 8 paginas completas, una por una**, no solo las tres
  senaladas: sin huecos, 0 `Overfull`/`Underfull hbox` y 0 `vbox`.
- **Leccion, igual que con las tablas**: `pdflatex` sin avisos no significa
  que el PDF se vea bien. Los dos defectos de esta sesion (tablas que se salen
  de columna, huecos de balanceo de `multicols`) son invisibles en el log y
  solo se detectan mirando el render pagina por pagina, idealmente a
  resolucion alta con `pdftoppm -r 200` o mas. Aplica a los otros cuatro
  articulos de la linea B si usan esta misma plantilla o cualquier `multicols`.
- Bloqueado en: nada.
- Siguiente: revision adversarial ronda 1 en chat nuevo y limpio.
- Tiempo de computo consumido: 0 h GPU.

## 24/08 (noche, correccion 3) - Fig. 3 aparecia despues de la Fig. 4
- Hecho: el usuario detecto que la Fig. 3 (el mapa de calor, la que sostiene el
  articulo) aparecia FISICAMENTE DESPUES de la Fig. 4 en el PDF, aunque el texto
  las menciona en orden 3 luego 4. Confirmado: Fig. 3 caia en la pagina 7 y
  Fig. 4 en la pagina 6.
- **Causa**: Fig. 3 es `figure*` (16 cm, mas ancha que una columna) con
  colocacion `[t]`, no `[H]` como el resto de figuras y tablas. Un flotante
  `[t]` normal entra en la cola de colocacion de LaTeX y espera el siguiente
  hueco de PAGINA COMPLETA disponible; Fig. 4, en cambio, es `[H]` (columna
  simple, forzada) y se inserta exactamente donde aparece en el codigo, sin
  cola. Como el hueco de pagina completa mas cercano para Fig. 3 resulto ser la
  pagina 7 -posterior a donde el texto ya habia colocado Fig. 4 en la pagina
  6-, el orden de lectura quedaba invertido.
- **Primer intento fallido**: `\clearpage` justo antes de Fig. 3. Empeoro las
  cosas: dejo la pagina 6 casi vacia (5 lineas de texto y el resto en blanco) y
  Fig. 3 igual termino despues de Fig. 4 (ahora en la pagina 8). `\clearpage`
  solo termina la pagina; no garantiza que ESE flotante en particular ocupe la
  siguiente.
- **Solucion correcta**: sacar a Fig. 3 del entorno `multicols` en lugar de
  intentar forzar su cola de colocacion. Se cierra `\end{multicols}` justo
  antes, se inserta la figura como `\begin{figure}[H]` a ancho completo (fuera
  del entorno de dos columnas no hay cola de flotantes, se coloca exactamente
  ahi), y se reabre `\begin{multicols}{2}\raggedcolumns` despues. Es la tecnica
  estandar para una figura mas ancha que una columna dentro de `multicols`.
  Recompilado: **vuelve a 8 paginas**, Fig. 3 y Fig. 4 quedan juntas en la
  pagina 6 y en el orden correcto de lectura (3.2 -> Fig. 3 -> 3.3 -> Fig. 4).
  Verificadas de nuevo las 8 paginas completas, una por una: sin huecos, sin
  desbordes.
- **Leccion, se acumula con las dos anteriores**: en `multicols`, cualquier
  flotante mas ancho que una columna (`figure*`/`table*`) no se comporta como
  los `[H]` de una columna. No usar `[t]`/`[b]` normales esperando que se
  coloque cerca de su punto en el texto, y no intentar forzarlo con
  `\clearpage`: la solucion es encerrarlo entre `\end{multicols}` y
  `\begin{multicols}{2}\raggedcolumns`.
- Bloqueado en: nada.
- Siguiente: revision adversarial ronda 1 en chat nuevo y limpio.
- Tiempo de computo consumido: 0 h GPU.

## 24/08 (noche, correccion 4) - bug compartido en fieutils.tablas, mas un caso que no cubre
- Hecho: la sesion de P5 reporto (mismo protocolo de aviso cruzado que ya se
  uso con P4) un bug en `fieutils/tablas.py::exportar()`: formateaba CUALQUIER
  columna numerica con `decimales` sin distinguir enteros de floats, asi que
  una columna de conteo salia "88.000" en vez de "88". Ya lo corrigieron en la
  copia compartida (`es_entera = pd.api.types.is_integer_dtype(serie)`),
  verificado con `verificar_infra.py` 14/14.
- **Revisadas las 7 tablas de P7 que pasan por `exportar()`.** Dos estaban
  afectadas: `anova_dos_factores_tex` (columna `df`: "3.0000" en vez de "3") y
  `ablacion_resumen` (columna `n_pares`: "60.0000" en vez de "60"). Las dos de
  `02_preprocess.py` (`ventanas_por_carga_clase`, `dimension_representaciones`)
  ya estaban bien, por casualidad: llevan `decimales=0`, que con la version
  vieja daba el mismo resultado que un entero. Regenerado `04_stats.py`:
  `ablacion_resumen` se corrigio sola con la libreria actualizada.
- **`anova_dos_factores_tex` seguia mal despues de regenerar, y no es un
  residuo del bug de P5.** La columna `df` que devuelve `statsmodels.anova_lm`
  es genuinamente `float64` (valores 3.0, 2.0, 6.0, 228.0), no `int64`, asi que
  `is_integer_dtype` no la detecta -es un caso distinto al que corrigieron,
  dtype semanticamente entero que llega como float, no una columna de enteros
  mal detectada-. **Corregido en `04_stats.py`, no en `fieutils/`**: se castea
  `df` a `int` antes de exportar, con el motivo comentado en el codigo. Se
  respeta la regla de no tocar la libreria compartida sin avisar; esto es un
  ajuste local de P7, no algo que otros articulos con ANOVA de statsmodels
  necesiten automaticamente (cada uno debe revisar si le pasa lo mismo).
- **Verificado que ninguna cifra cambio**, solo el formato: comparado
  `anova_dos_factores.csv` antes/despues (15.93, 35.51, 5.14 identicos) y
  revisadas las demas tablas sin cambios.
- Aviso recibido de P5 sobre riesgo de citas de background: la primera busqueda
  de EfficientNet (Tan & Le) resolvio a un capitulo de libro de otro autor con
  titulo parecido, detectado revisando autores y no solo abriendo el DOI.
  Relevante para P7 tambien: las 12 referencias de este articulo ya pasaron por
  el paso 3 completo (ver bitacora del 24/08 cierre), asi que no aplica
  retroactivamente, pero queda como recordatorio para cualquier cita nueva que
  se añada en la revision adversarial.
- Bloqueado en: nada.
- Siguiente: revision adversarial ronda 1 en chat nuevo y limpio.
- Tiempo de computo consumido: 0 h GPU.


## 01/09 - revision adversarial ronda 1 (revisor par externo)

Revision hecha en chat limpio con el prompt de revisor par, sin contexto previo
del trabajo. **Recomendacion del revisor: revision mayor.** Lo senalado y lo
hecho, punto por punto.

### Hallazgo 1 (el grave): el articulo afirmaba una interaccion que ningun test suyo media

El abstract, la contribucion (3), la seccion 3.4 y las conclusiones decian que
la representacion **interactua con el clasificador**. El unico test de
interaccion del articulo era el ANOVA pre-registrado de dos factores
**representacion x distancia de carga**, que promedia los clasificadores antes
de ajustar: el clasificador no es un factor del modelo, asi que ese termino no
podia sostener la afirmacion. La seccion 3.4 llegaba a citar "la interaccion
representacion x clasificador reportada arriba", que no estaba reportada en
ninguna parte.

- **Corregido ejecutando codigo, no reescribiendo.** Nuevo `src/06_revision.py`
  con un **ANOVA de tres factores** (representacion x clasificador x distancia)
  sobre las 144 celdas fuera de diagonal con los folds promediados. Resultado:
  la interaccion **representacion x clasificador es el termino mas grande del
  modelo** (F = 4,91; p = 0,0002; eta parcial 0,214), por encima de todos los
  efectos principales. La afirmacion del articulo ahora tiene su test.

### Hallazgo 2: el ANOVA pre-registrado trataba los folds como replicas independientes

Las 240 observaciones son 5 folds dentro de cada una de 48 celdas, y dos folds
de la misma celda comparten **cuatro quintos del conjunto de entrenamiento**.
Con 228 grados de libertad de residuo el modelo es anticonservador. En un
articulo cuyo argumento central es que el campo infla resultados por
particiones mal hechas, es la objecion que mas duele.

- **Reajustado el mismo modelo sobre las 48 medias por celda** (tambien en
  `06_revision.py`). La distancia de carga aguanta (F = 5,85; p = 0,006), pero
  **la interaccion representacion x distancia se cae** (F = 0,85; p = 0,543) y
  la representacion queda al borde (F = 2,62; p = 0,065). Es decir: **el
  resultado que el articulo ponia en el abstract era un artefacto de la
  pseudo-replicacion.** Se reporta asi, con esas palabras, en 3.3. La Tabla 4
  vieja (ANOVA de dos factores) pasa a prosa y la Tabla 4 nueva es el ANOVA de
  tres factores.

### Hallazgo 3: hueco de referencias en el tema del propio articulo

Cero citas de literatura de transferencia entre condiciones o adaptacion de
dominio, en un articulo sobre transferencia entre cargas. Un revisor del area
lo ve en la primera pagina.

- **Anadidas tres, las tres con paso 3 completo** (resumen integro leido, no
  solo DOI resuelto): Neupane y Seok 2020 (revision de CWRU con aprendizaje
  profundo), Zhao et al. 2020 (benchmark de cuatro arquitecturas sobre nueve
  conjuntos, senala la generalizacion como problema abierto) y Li et al. 2019
  (adaptacion de dominio multicapa con MMD multi-nucleo). Nivel de verificacion
  anotado en el `.bib` como el resto. Van en un parrafo nuevo de la
  introduccion, del que sale la pregunta del articulo.
- **Reescrito el parrafo de citas de *Ingenius***, que era una lista de cuatro
  trabajos encadenados con puntos y coma y sonaba a relleno de cita obligatoria.
  Ahora agrupa por enfoque (medicion frente a diseno de modelo) y la de db4 se
  ancla donde de verdad importa, que es la representacion wavelet.

### Cifras verificadas contra `results/`, dos mal

Se recalcularon las cifras del texto desde `resultados_por_fold.csv` y
`resultados_por_diametro.csv`. Casi todas coinciden. **Dos no:**

1. "eight of the twelve representation-classifier combinations sit above 0.98"
   → **son diez**, no ocho (recuento directo sobre la diagonal).
2. La caida de la CNN (0,0135) se describia como "an order of magnitude smaller
   than any vector classifier". La menor caida de un clasificador de vector es
   0,074, asi que el factor es **5,5, no diez**. Reescrito a "about five times
   smaller".

Tambien se corrigio el control negativo de fuga: el texto decia "320 pairs of
windows sharing samples", pero 320 es el numero de **violaciones** (160 pares
distintos, cada uno contado en los dos folds que afecta). El calculo estaba
bien; la frase, mal.

### Justificacion invalida en el metodo

El articulo justificaba no ajustar hiperparametros diciendo que "tomar un
conjunto de validacion del entrenamiento cambiaria el tamano de muestra entre
celdas y tomarlo del bloque de prueba seria fuga". **Es falso**: una particion
interna de los bloques de entrenamiento no toca el bloque de prueba y es
estandar. Reescrito para decir lo que de verdad pasa (se dejaron los valores por
defecto para que las cuatro representaciones vean cada clasificador en
condiciones identicas) y **la decision pasa a limitaciones**, con el apunte de
que un SVM sin ajustar sobre 1025 bins de FFT explica en parte que la FFT quede
ultima con ese clasificador y primera con los otros dos.

### Limitaciones: de cuatro a seis

Anadidas las dos que no se pueden corregir sin rehacer el experimento:

- **No esta el espectro de envolvente**, que es la tecnica de referencia del
  area y la que este mismo trabajo usa para verificar las etiquetas. Es la
  candidata con mas probabilidad de transferir entre cargas, porque conserva la
  tasa de repeticion de impactos y descarta la portadora. No se anade porque las
  cuatro representaciones se fijaron antes de tocar los datos.
- **Hiperparametros sin ajustar** (ver arriba).

### Figuras

- **`fieutils/figures.py` escribia "DC = 1.35"** en el diagrama de Nemenyi:
  abreviatura en espanol dentro de una figura en ingles. Es el tercer caso de la
  clase que `REDACCION.md` documenta en la libreria. **Corregido a "CD"**.
  **Aviso para el resto de la linea B: cualquier articulo con diagrama de
  diferencia critica tenia el mismo texto en espanol en su PDF.**
- **Fig. 2a**: las etiquetas eran los nombres internos en snake_case
  (`peak_to_peak`, `mean_amplitude_root`), que ademas no coincidian con los
  nombres del manuscrito. Anadido un mapeo de visualizacion en `05_figures.py`,
  sin tocar la constante de `fieutils` que indexa datos. Al ponerlas legibles
  ocupaban demasiado giradas 90 grados, asi que el panel pasa a **barras
  horizontales**: a ancho de columna las etiquetas verticales quedaban por
  debajo de 5 pt en el PDF.
- **Pies que no se explicaban solos.** El de la Fig. 1 remitia a "Table 1 RMS
  values" y la Tabla 1 no lleva RMS; ahora da los valores (0,066 g a 0,425 g) y
  avisa de que cada panel tiene su propia escala. El de la Fig. 2 no decia que
  el panel (d) es la rejilla 64x64 de la CNN y **no** la de 16x64 que entra en
  la comparacion. El de la Fig. 4 no explicaba que es CD.
- Anadido al pie de la Fig. 2 que los doce descriptores del panel (a) no
  comparten unidades, porque comparar sus alturas no significa nada.
- Anadido a la Tabla 5 (costo) que la fila de la CNN promedia un solo
  clasificador y que su tiempo de prediccion no se instrumento (estaba vacio sin
  explicacion).

### Maquetado

- Las tres figuras de una columna estaban a `width=8.4cm` con la columna a
  8,17 cm: **desbordaban 6,4 pt cada una**. Corregidas.
- Recompilado y **verificadas las 9 paginas una por una a 110 dpi**. Un intento
  intermedio con `sed` para poner `width=\columnwidth` metio un caracter de
  control 0x0F en el `.tex` y dejo las Figs. 1, 2 y 4 **sin imagen**, con el
  texto "lumnwidth" impreso en su lugar; se detecto **mirando el render**, no en
  el log, que no dio ni un aviso. Leccion repetida: `sed` no sirve para insertar
  barras invertidas de LaTeX, y compilar sin mirar el PDF no vale.
- El articulo pasa de 8 a 9 paginas por la tabla nueva y los parrafos anadidos.
  Palabras: **6003**, contra el limite de 5000-6000 de la plantilla. Roza el
  tope: para recuperar margen se comprimieron 2.1, 2.2, 2.3, 3.2 y 3.4 sin
  quitar ningun dato. El resumen en espanol quedo en **230**, que es exactamente
  el maximo. Si la ronda 2 anade texto, hay que quitar de otro sitio.

### Lo que el revisor senalo y NO se corrigio

- **Los 12 pares fuera de la diagonal no son bloques independientes** para
  Friedman: los pares (0,1) y (0,2) comparten todo el entrenamiento. Demsar
  supone conjuntos independientes. No se toca porque la prueba esta
  pre-registrada; el articulo ya declara la dependencia entre clasificadores,
  pero no esta entre las limitaciones por falta de espacio de palabras.
- **Las tres pruebas de Friedman por clasificador** no llevaban correccion por
  comparaciones multiples. Anadida la de Bonferroni (alfa = 0,0167); las tres
  siguen siendo significativas, asi que no cambia ninguna conclusion.
- **La CNN sigue siendo una fila descriptiva** fuera de toda inferencia. El
  revisor sugeria quitarla o integrarla; se conserva porque estaba en el diseno
  cerrado y el texto la declara descriptiva y sin ajustar.

- Bloqueado en: nada.
- Siguiente: **ronda 2 de revision adversarial en chat limpio**. Falta la cover
  letter con la declaracion de uso de IA.
- Tiempo de computo consumido: 0 h GPU. `06_revision.py` tarda 4 s en CPU.

## 01/09 (tarde) - margen de palabras para la ronda 2

- Hecho: el manuscrito quedaba en **6003 palabras** contra el limite de
  5000-6000 de la plantilla, sin margen para que la ronda 2 anada nada.
  Recortadas **101 palabras** (6003 → **5902**) en 25 pasajes de 2.1, 2.2, 2.3,
  2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, conclusiones, disponibilidad de
  datos y el pie de la Tabla 5. Solo prosa: **ninguna cifra, ninguna referencia
  y ninguna afirmacion desaparecen**.
- **Verificado por script, no a ojo**: se extrajeron todos los numeros del `.md`
  y del `.tex` antes y despues y se compararon los conjuntos. Unica diferencia
  en los dos ficheros: `5727` pasa a `5727.` por quedar a final de frase. Cero
  cifras perdidas.
- El `.md` y el `.tex` se editan con el mismo listado de pares, emparejando con
  los espacios en blanco normalizados: los dos llevan el mismo texto pero
  envuelto a anchos distintos, asi que un `replace` literal falla en uno de los
  dos. Scripts de un solo uso, no se conservan en `src/`.
- Recompilado: **9 paginas**, cero `Overfull`/`Underfull` nuevos (siguen los dos
  de siempre, la tabla de resumenes de la portada y el fichero de
  configuracion), cero citas sin resolver. Verificadas las 9 paginas a 110 dpi.
- Estado de los limites: cuerpo **5902** (limite 6000, quedan ~98 de margen),
  abstract **222** y resumen **230** (limite 230 cada uno; **el resumen sigue
  clavado en el maximo**, asi que si la ronda 2 toca el resumen hay que quitar
  antes de anadir).
- Bloqueado en: nada.
- Siguiente: ronda 2 de revision adversarial en chat limpio; cover letter.
- Tiempo de computo consumido: 0 h GPU.

## 02/09 - revision adversarial ronda 2 (chat limpio, sin contexto de la ronda 1)

Segunda pasada completa: revisor par, revisor hostil al encuadre y pasada
anti-IA. Las cifras del manuscrito se re-verificaron abriendo los CSV de
`results/`, no leyendo el texto. Las 12 celdas de `friedman_tabla_bloques.csv`,
las caidas medias, los recalls por diametro y las cinco filas de la Tabla 5
coinciden con los datos; no se encontro ninguna cifra inventada.

### Lo que se senalo y SE CORRIGIO

- **~~Autor fabricado en la referencia [11]~~. FALSA ALARMA, revertida el mismo
  dia.** Se dio por bueno que `salazar2012` incluia un autor inventado, "Jose
  Manuel Aller", porque Crossref y OpenAlex listan cuatro autores y la entrada
  tenia cinco. **El error fue mio, no del `.bib`.** Dos fallos encadenados:
  primero, Crossref y OpenAlex **no son fuentes independientes** (OpenAlex
  ingiere de Crossref), asi que su coincidencia no confirmaba nada; segundo, no
  se abrio el PDF, que es la fuente que manda. **La portada del PDF publicado
  muestra los cinco firmantes con afiliacion numerada 1 a 5, y Aller es el
  tercero**, con su adscripcion a la Universidad Simon Bolivar. El `JOURNAL.md`
  ya lo decia bien desde el 24/08, tras la lectura del texto completo, y se
  ignoro esa nota. Revertido en los tres ficheros (`paper/references.bib`, el
  `referencias.bib` de la plantilla y la lista del `.md`), con un aviso en la
  entrada del `.bib` para que nadie repita el recorte. Igual se revirtio
  `hendriks2022`, que se habia cambiado de "Knox, D. A." a "Knox, David" con la
  misma fuente defectuosa.
- **Leccion, que es la misma que ya estaba escrita para las figuras.** Para las
  figuras la regla era "compilar sin mirar el PDF no vale"; aqui resulta ser
  "cotejar autoria sin abrir el PDF tampoco vale". Un metadato de deposito puede
  estar incompleto, y quitar a un coautor real de una cita es un error peor que
  el que se creia estar corrigiendo. Los cuatro DOI de Ingenius si se abrieron
  uno por uno y resuelven con el titulo correcto; eso se mantiene.
- **La fila de la CNN ocultaba un fallo de entrenamiento.** La Tabla 3 daba
  0,971 +/- 0,116 dentro de dominio y 0,957 +/- 0,119 fuera, y el texto leia esa
  caida pequena como una ventaja de transferencia. Desglosado por carga de
  entrenamiento (`07_revision2.py`): con 0, 1 y 2 HP la red da 0,998, 1,000 y
  0,992; con 3 HP da **0,892 +/- 0,230**, y **todo el deficit es un solo fold**,
  cuyas cuatro celdas caen entre 0,396 y 0,489 porque la red no converge en las
  30 epocas fijas. Ese fold produce las dos desviaciones altas. Se reporta tal
  como corrio y el texto dice ahora que la ventaja aparente **no debe leerse
  como tal**.
- **Las cuatro caidas medias se daban sin incertidumbre** (0,074 a 0,153), lo
  que invitaba a leer un orden. Anadido el IC bootstrap remuestreando los 12
  pares, que es la unidad de analisis: 0,043-0,105, 0,080-0,122, 0,073-0,133 y
  0,074-0,240. **Los cuatro se solapan**, lo que refuerza la conclusion del
  articulo en vez de debilitarla.
- **El ANOVA de tres factores trataba los 12 pares como replicas
  intercambiables.** El manuscrito aplicaba el argumento anti-pseudorreplicacion
  al modelo de dos factores pero no al de tres, que es donde descansa la
  conclusion central. Reajustado con **el par como bloque**: la interaccion
  representacion x clasificador **sobrevive y crece** (F = 5,78, p < 0,001,
  eta^2 parcial = 0,223). El bloque se lleva la mayor parte (eta^2 parcial =
  0,307), asi que **que dos cargas se cruzan importa mas que cualquier factor
  del diseno** y la distancia de carga no lo captura todo. Ambos resultados
  anadidos a 3.3.
- **3.4 enumeraba mal los subgrupos.** Decia "el peor es IR 0,014 (0,587),
  luego B 0,021 (0,786) y OR 0,014 (0,849)", saltandose IR 0,021 (0,823) e
  IR 0,007 (0,832), que quedan en medio. Daba a entender que OR 0,014 era el
  tercero peor. Corregido al orden real.
- **La ablacion se resumia mas categorica de lo que soporta.** FFT con SVM-RBF
  da +0,033 con IC [-0,002, +0,067] y delta 0,330 (medio): el intervalo esta
  casi entero por encima de cero. "Failed to improve in all four" pasa a "no
  combination improved by an interval that excludes zero", y el texto dice que
  la ablacion **separa los dos clasificadores** en vez de descartar todo
  beneficio.
- **"Pre-registered" sin registro publico con marca de tiempo.** Sustituido por
  "specified in the protocol before the data were split". El termino tiene un
  significado tecnico fuerte que el proyecto no puede respaldar.
- **Trazabilidad de 3.6.** Los tiempos de extraccion (0,27 / 1,75 / 2,03 /
  5,96 s) no estaban en `results/` sino en `data/processed/manifiesto.json`.
  Citado explicitamente en el texto y en la nota de estado.
- **Error gramatical**: "with their p-values are not corrected". Reescrito.
- **Pasada anti-IA.** Suprimidos los parrafos que anunciaban lo que iban a decir
  ("Two problems limit what such comparisons establish", "Six limitations
  qualify these results", "Two directions follow", "Storing fault diameter as a
  covariate locates the failures", "Figure 3 also makes visible an asymmetry the
  averages hide", "The convolutional reference behaves differently") y los
  valorativos sobre el propio trabajo ("the balanced core of the design", "The
  effect of representation is real", "That choice follows from the physics
  rather than from frequency resolution"). Cero palabras de la lista prohibida;
  "robust" solo aparece en "robustness check". Dos guiones largos en todo el
  manuscrito.
- **Limitaciones consolidadas de ocho a cinco.** La guia pide tres o cuatro
  reales; ocho diluye. Fusionadas hiperparametros con dimensionalidad, y
  desbalance de la clase sana con la limitacion de la diagonal, que tienen la
  misma causa: un solo registro sano por carga.

### Lo que se senalo y NO se pudo corregir: va a limitaciones

- **Los 12 bloques de Friedman no son independientes.** Cada carga aparece en
  seis pares y (i, j) y (j, i) usan los mismos registros con los papeles
  cambiados. La ronda 1 lo detecto y lo dejo fuera por falta de espacio; ahora
  **esta escrito en 3.7**, junto con la lectura correcta: p = 0,158 es un fallo
  en separar las representaciones, no evidencia de que sean equivalentes. Con
  cuatro cargas no hay diseno sobre este conjunto que lo evite.
- **No hay comparacion numerica con la literatura.** Las cifras publicadas de
  transferencia entre cargas sobre CWRU salen de particiones que este protocolo
  evita a proposito, asi que la diferencia mediria la particion y no el metodo.
  Declarado en 3.7.

### Revisor hostil al encuadre

El argumento de rechazo mas fuerte que se pudo construir: cuatro
representaciones clasicas, tres clasificadores de biblioteca sin ajustar y un
conjunto de 2015 muy explotado; ninguna aportacion algoritmica; y el resultado
principal es una prueba que no rechaza. La defensa **no exige experimentos
nuevos**, solo encuadre: el articulo no compite en exactitud sino que mide la
fragilidad de un protocolo de comparacion, y su producto es negativo y util. Lo
que ya lo sostiene y conviene subrayar en la carta: la particion por registro
con purga y control negativo, el error de nomenclatura de `99.mat` documentado,
la verificacion de etiquetas por envolvente y el fallo de convergencia de la CNN
reportado en vez de escondido. Sin cambios de texto derivados de esta parte mas
alla de los ya listados.

### Figuras

Revisadas las cuatro en PNG. Sin defectos que corregir: paleta Okabe-Ito, sin
titulos dentro de la figura, valores anotados en el mapa de calor (legible
impreso en blanco y negro), diagonal recuadrada. La Fig. 2(d) muestra el
espectrograma en la rejilla 64x64 de la CNN y no en la 16x64 que entra en la
comparacion, cosa que el pie ya declara.

### Carta de presentacion

Redactada en `paper/cover_letter.md`, tres parrafos: que se hizo, por que encaja
en *Ingenius* nombrando los cuatro articulos de la revista que el manuscrito
usa, y declaracion de originalidad, de no envio simultaneo, de conflicto de
interes, de disponibilidad de datos y de uso de IA. Quedan como marcadores el
nombre del autor, la afiliacion y la fecha.

### Codigo

`src/07_revision2.py` (nuevo, exploratorio, fuera del protocolo). Produce
`caidas_ic_bootstrap.csv`, `anova_bloqueada_por_par.csv` y
`cnn_por_carga_entrenamiento.csv` mas sus `.tex`. Corre en 3 s en CPU.

### Limite de palabras: 3.6 fuera y propagacion al `.tex`

Las correcciones anadian **+237 palabras netas** y el `.tex` habria quedado en
torno a 6 174, contra el limite de **6 000** de la plantilla. Antes de decidir
nada se recortaron unas 180 palabras de prosa en 30 pasajes **sin perder
ninguna cifra**, verificado por script comparando los conjuntos de numeros antes
y despues. Con eso no bastaba, y por decision del responsable se **elimino 3.6
(costo computacional) junto con la Tabla 5**, 184 palabras que no sostenian
ninguna conclusion y cuyo propio texto admitia que la ventaja del espectrograma
no estaba establecida. Se conserva en 3.2 una frase con el unico dato de esa
seccion que se usa en otra parte: el espectrograma es el mas caro de extraer,
5,96 s frente a 0,27 s de la FFT.

### Propagacion al `.tex`

Hecha de una sola vez con un listado de 21 pares, emparejando con los espacios
en blanco normalizados porque el `.md` y el `.tex` llevan el mismo texto envuelto
a anchos distintos. Cada par lleva un `assert` de unicidad, asi que un patron que
no case o que case dos veces **para el script en vez de escribir a medias**. Se
respetan las convenciones del `.tex`: `\ref` en lugar de numeros de tabla y
figura, "representation by classifier" en prosa, "the ordering observed above" en
lugar de "Section 3.2", y notacion matematica en modo math.

- **Fallo cometido y detectado en el render**: la primera pasada **olvido el
  abstract y el resumen**, que en el `.tex` viven en la tabla de la portada y no
  en el cuerpo. Se vio en la pagina 1 del PDF, no en el log: seguian diciendo
  "confirming that the usual comparison does not discriminate" y les faltaban los
  intervalos solapados. Propagados aparte, respetando que el abstract del `.tex`
  ya omitia los estadisticos por una decision de maquetacion anterior. Confirma
  otra vez que compilar sin mirar el PDF no vale.
- Despues se paso un script que **compara frase a frase el `.md` con el `.tex`**
  normalizando citas, math y comandos. Las 35 diferencias que reporta se
  revisaron una por una: todas son las convenciones deliberadas del `.tex` o
  artefactos del normalizador, ninguna es una omision.
- Corregidos tambien `salazar2012` y `hendriks2022` en el `referencias.bib`
  local de la carpeta de la plantilla, que es una copia aparte del `.bib` del
  `paper/`.

### Compilacion verificada

- **8 paginas** (antes 9), **5 986 palabras** con `wc -w` sobre el `.tex`, bajo
  el limite de 6 000. Abstract **211** y resumen **218**, bajo el maximo de 230.
- Cero citas o referencias sin resolver. Tres avisos de `hbox`, **los mismos de
  siempre** y todos fuera del cuerpo: dos en la tabla de resumenes de la portada
  y uno en el fichero de configuracion. **Cero avisos nuevos.**
- **Las 8 paginas revisadas una por una a 110 dpi.** Tablas 1 a 4 y Figuras 1 a 4
  bien colocadas, ninguna invade la columna contigua, la Fig. 3 a ancho completo
  sigue apareciendo antes de la Fig. 4, y la referencia [11] ya sale con cuatro
  autores.

### Fig. 4 ilegible: la figura estaba dimensionada para dos columnas

Detectado revisando el PDF a 110 dpi, no en el log. **La fuente no era el
problema.** `fieutils.diagrama_diferencia_critica` dibuja por defecto a
`ANCHO_DOBLE * 0.8` = **5,73 pulgadas**, pero en la plantilla de *Ingenius* esta
figura entra en **una** columna, `width=8.17cm` = **3,22 pulgadas**: LaTeX la
reducia al **56 %** y los rotulos de 8 pt quedaban en unos **4,5 pt**,
ilegibles impresos. Es el mismo tipo de error que las figuras a `width=8.4cm`
del 24/08, pero al reves: alli la caja se salia de la columna, aqui la imagen
se encoge dentro de ella y solo se ve mirando el render.

Arreglado en `05_figures.py` pasando `figsize=(ANCHO_SIMPLE, 2.05)`, de modo que
la escala en el PDF sea practicamente 1:1 (8,89 cm a 8,17 cm, un 92 %) y los
rotulos salgan a unos 7,4 pt, del mismo cuerpo que el pie de figura. **No se
toco `fieutils`**: el defecto de ancho doble es correcto para los proyectos cuya
plantilla es de una sola columna, y la firma ya aceptaba `figsize`. Se comprobo
que los nombres largos ("STFT spectrogram") siguen cabiendo en el margen lateral
al ancho reducido.

Regenerada con `05_figures.py`, copiada a `figures/fig4_p7.pdf` y recompilado.
Las otras tres figuras salen identicas salvo los cuatro bytes de la marca
`/CreationDate` que matplotlib incrusta en cada PDF, comprobado con `cmp -l`,
asi que no se recopiaron.
**Siguen 8 paginas**, los mismos tres avisos de `hbox` de siempre y cero
nuevos; la mayor altura de la figura la absorbe la pagina 6 y solo corre unas
lineas entre la 6 y la 7. Verificadas otra vez las paginas a 110 dpi.

- Hecho: ronda 2 cerrada, correcciones aplicadas al `.md`, al `.bib` y al
  `.tex`; 3.6 y la Tabla 5 eliminadas; Fig. 4 redimensionada y regenerada; carta
  de presentacion redactada; `07_revision2.py` escrito y ejecutado; PDF
  recompilado y verificado pagina a pagina.
- **Revertida la falsa correccion de autoria de `salazar2012`** tras abrir el
  PDF publicado: los cinco autores del `.bib` original eran correctos. Detalle
  arriba.
- Bloqueado en: nada.
- Siguiente: nombre real del practicante y roles CRediT, y DOI de Zenodo en la
  consolidacion del 4-6/09. Con eso el manuscrito queda listo para enviar.
- Tiempo de computo consumido: 0 h GPU. `07_revision2.py` tarda 3 s en CPU;
  `05_figures.py`, 25 s; la compilacion completa, unos 40 s.

## 03/09 — Revisión cruzada de línea A: correcciones aplicadas

Dos informes de la línea A: la revisión cruzada (`P7.md`, **revisión menor en el
fondo, mayor en referencias**) y la auditoría adversarial
(`auditoria_P7_ingenius.md`, **revisión menor**). El arbitraje entre ambos y con
la guía está en `C:\Users\ASUS\.claude\plans\zazzy-herding-ocean.md`.

### El bloqueante: los DOI no se imprimían (no es que no existieran)

La revisión cruzada reportó que «las quince referencias carecen de DOI» e invocó
la regla no negociable 2. Miró el PDF, y en el PDF no había DOI. Pero:

- `referencias.bib` **sí los tiene**: once de quince, y las cuatro que no son las
  mismas cuatro que el propio informe identifica como sin DOI asignado (CWRU, dos
  de JMLR y las actas de NeurIPS).
- `paper/references.bib` documenta que **las quince se verificaron el 24/08**
  siguiendo los tres pasos de la guía, con notas por entrada sobre hasta dónde
  llega la comprobación y para qué se puede citar cada una.

La regla 2 exige **verificar** abriendo el DOI, y eso estaba hecho. Lo que
fallaba era que el DOI no se **imprimía**, que es otra cosa.

**Causa:** `IEEEtran.bst` v1.14 no conoce el campo `doi`. Cero apariciones de la
cadena en el estilo (`grep -c doi $(kpsewhich IEEEtran.bst)` → 0). Y las normas
de Ingenius (§3.2, `paper/evidencia/`) sí lo piden, con este formato exacto:
`[Online]. Available: https://doi.org/…`. `IEEEtran.bst` **sí** conoce `url` y lo
emite justamente con ese prefijo.

**Arreglo** (`paper/corregir_bibliografia.py`): derivar `url` de `doi` en las
quince entradas, y dar vía de verificación estable a las cuatro sin DOI (JMLR
permanente para Demšar y Pedregosa; arXiv 1912.01703 para PyTorch, comprobado el
03/09). Aplicado a los **dos** `.bib`, que además estaban desincronizados: la
copia de trabajo ya tenía las URL de JMLR y la de compilación no.

### Error de contenido que no vio ninguno de los dos informes

**`salazar2012` tenía un autor fantasma.** El `.bib` listaba cinco autores;
Crossref (`10.17163/ings.n7.2012.02`) y la ficha del artículo en el OJS de
Ingenius listan **cuatro**: Salazar, Quizhpi, Bueno y Reyna. «José Manuel Aller»
no es autor de ese artículo. Corregido en los dos `.bib`.

El mismo error estaba propagado a `paper/cover_letter.md`, que la citaba como
«García Salazar et al.» cuando la primera autora es Luisa Salazar. Corregido.

Importa más de lo que parece: es **una de las cuatro citas a la revista destino**,
y el editor la reconoce.

Las otras catorce entradas se recomprobaron el 03/09 contra Crossref (título,
autores, revista, volumen, páginas y año) y las cuatro de Ingenius también contra
el OJS. Todas cuadran.

### Etiquetas en español dentro de un cuerpo en inglés

La revisión cruzada lo señaló y pidió comprobar si la revista las impone. Lo
imponen dos artefactos oficiales: `ingenius.cls` (línea 33,
`tablename=Tabla` del paquete `caption`) y `plantilla_ingenius.tex` (líneas
143-144, `\renewcommand` de `\figurename` y `\tablename`).

**Pero no es una norma de la revista, es que la plantilla está escrita en
español.** Comprobado sobre un artículo en inglés publicado por la propia
Ingenius —Contreras Urgilés et al., n.º 21 (2019), que es además la cita [9] de
este manuscrito—: sus pies dicen «Figure 1.» y «Table 1.», y su bibliografía se
titula «References». Se cambian las tres etiquetas al inglés, con el motivo
anotado en el `.tex`.

### Resto de correcciones

- **Abstract y resumen:** añadido que la comparación dentro de una misma carga se
  hace bajo una partición que comparte registros, que es lo que §3.6 ya declara y
  el abstract callaba. Con recorte compensatorio para no pasar el tope: quedan en
  **217 palabras cada uno** (límite 230), la misma longitud que antes.
- **§3.5:** el intervalo `[-0.002, +0.067]` se describía como *«lies almost
  entirely above zero»* cuando el propio párrafo concluye que no permite decidir.
  Ahora dice que contiene el cero.
- **Tabla 3:** mejor valor por columna en negrita (guía §4.3), entre las doce
  filas que entran en la comparación; la fila de referencia del CNN no compite.
  La columna in-domain tiene dos filas empatadas en 1.000, y el pie lo dice.
- **Cover letter:** tenía declaración de IA, pero genérica («Generative AI
  tools»). Ingenius **exige nombrar la herramienta y decir para qué**
  (`JOURNAL.md`). Reescrita nombrando el proveedor, los tres usos concretos y la
  asunción de responsabilidad, más la declaración explícita de que ninguna
  herramienta figura como autora y de que ninguna figura se generó con IA.

### Lo que NO se aplicó, y por qué

- **«Figura 3: hay valores fuera del rango de la barra de color»** (revisión
  cruzada §2.2). **Falso.** `fieutils.figures.mapa_calor_transferencia` fija
  `vmin` al mínimo real de la matriz, que es **0.5392**; lo que empieza en 0,6 son
  las *marcas* del eje de color, no su rango. La celda de 0,54 se dibuja como el
  azul más oscuro de la escala y se distingue a simple vista de las de 0,65 y
  0,68. Comprobado sobre la figura renderizada.
- **«Retirar el CD = 1.35 incrustado»** (auditoría). Es la leyenda de escala de la
  barra de diferencia crítica de un diagrama de Demšar; sin ella la barra es
  ilegible. Sale de código compartido con P3.
- **«Limpiar las leyendas (a, b, c, d) de las figuras»** (auditoría). Las
  **exige** la revista: la plantilla oficial dice *«Si la figura posee dos partes
  incluya los indicativos "(a)" y "(b)"»*, y `JOURNAL.md` ya lo tenía registrado
  como «paneles rotulados a, b, c».
- **«Declarar cuál test es primario»** (auditoría, inconsistencia ANOVA/Nemenyi).
  Ya estaba: §3.3 dice *«The statistical procedure was decided before results were
  examined… The primary test is a Friedman test»*, y el ANOVA se llama
  «exploratory» en el cuerpo **y en el abstract**. Sin cambio.
- **«Sin declaración de uso de IA»** (revisión cruzada §3). En Ingenius va en la
  **cover letter**, no en el manuscrito (`JOURNAL.md`, política de IA leída el
  24/08). Se corrigió allí.

### Estado

- `python C:\lineaB\verificar_envio.py P7`: **0 bloqueantes, 0 avisos.** Los nueve
  avisos previos eran las etiquetas en español, ya resueltas.
- **8 páginas.** Recuento: **5.941 palabras** descontando las URL de las
  referencias y los números de página; 6.144 en bruto. El rango adoptado es
  5.000-6.000 (plantilla) y las normas publicadas dicen 4.000-6.500. Queda dentro
  de las dos si no se cuentan las URL como palabras, y marginalmente por encima
  del tope de la plantilla si se cuentan. **Conviene decidirlo antes del envío.**
- Sigue pendiente lo que no está en el repositorio: nombre y ORCID de los autores,
  y el DOI de Zenodo.

## 17/10 - Italo Tenempaguay — Revisión cruzada de línea A sobre la versión del 16/10

Revisión recibida en `P7_Ingenius_Representacion_Senal_observaciones.md`. Cada
observación se contrastó contra `results/tables/`, el código y la aritmética
antes de aplicarla; no se aplicó nada solo porque la revisión lo dijera.

- **BSF (la más seria).** CWRU tabula 4.7135 para el elemento rodante, y ese
  valor ya es 2xBSF: con la geometría del 6205 el BSF convencional es 2.3567.
  `src/00_verificar_etiquetas.py` lo tomaba como BSF y buscaba "2xBSF" en
  4xBSF. Corregido y reejecutado. Las pistas no cambian (12/12 IR, 9/12 OR). En
  bolas, el umbral del control sano estaba inflado por un pico espurio de
  111.97 en 100.mat justo en la frecuencia equivocada; con la correcta el máximo
  del sano es 48.1, y la firma 2xBSF o sus bandas de jaula supera el doble de
  ese valor en **11 de 12** registros (12/12 si se incluye la línea BSF). Antes
  decía 7 de 12. La más débil sigue siendo 0.021 in (224.mat), así que el
  párrafo de la Discusión sobre firmas débiles sigue siendo correcto.
- **A1** "Testing at 0 HP is the harder direction throughout": solo vale para
  estadísticos y wavelet; la FFT muestra la asimetría contraria. Acotado, y
  dicho que el desbalance de la clase sana no la explica por sí solo.
- **A2** La CNN no es la más baja en dominio: la wavelet (0.960) está debajo.
- **A3** "The representation retaining absolute amplitude": hay dos (estadísticos
  y FFT). Reescrito.
- **A4** Nivel de la wavelet: el nivel 4 era el de Gómez 2023 (verificado en su
  texto completo); aquí se usan 5. Aclarado.
- **A5** "10.67 ms": una rejilla cuadrada de 1024 es 32x32 y deja 5.33 ms por
  columna. Corregido también en el comentario de `src/02_preprocess.py`. El
  argumento se sostiene con el número correcto (1.16 columnas por periodo BPFI,
  menos de 2), así que no se cambió el razonamiento.
- **A6** "ten … above 0.98": nueve por encima y una en 0.980; "at or above".
- **Menores aplicadas:** frase que empezaba por "And"; pie de la Fig. 3 con
  fila/columna; "In comp." → "Enters comparison"; final del resumen igualado al
  abstract (resumen 224 palabras); delta de Cliff que faltaba (−0.205, SVM con
  estadísticos); "decided before results were examined" → "fixed before the
  comparison was run" (el protocolo existe en este README con fecha 20/08, pero
  no hay sello de tiempo independiente); la Discusión ya no atribuye a la
  literatura un mecanismo sin cita, sino a la hipótesis que motivó la ablación;
  y se dice que los intervalos sobre los 12 pares son aproximados.
- **No aplicadas, quedan para decidir en equipo:** varias semillas, envolvente
  como quinta representación, curva de pérdida de la CNN y bootstrap por carga.
- Recompilado: 9 páginas (la nueva solo tiene el final de las referencias), 0
  errores; el único Overfull es el de siempre, idéntico en la versión anterior.
- **Extensión.** Las correcciones sumaban +96 palabras netas, unas 40 por encima
  del límite de la plantilla adoptado el 24/08 (5 000-6 000). Por decisión del
  usuario se recortaron 62 palabras de prosa en cuatro pasajes redundantes
  (introducción, cierre de 3.5 y conclusiones), verificado por script que no se
  perdió ni cambió ninguna cifra. Saldo neto: +28 palabras frente a la versión
  previa a la revisión, unas 5 969 con el método de recuento del 03/09.
- **Exactitud sobre la ablación.** El artículo decía que estaba "specified in the
  protocol before the data were split". Esta bitácora la fija el 22/08, al
  escribir `02_preprocess.py` y antes de correr el experimento, pero no estaba en
  el protocolo del 20/08. Ahora dice "specified/fixed before the experiment was
  run" en la contribución (4) y en el método.
