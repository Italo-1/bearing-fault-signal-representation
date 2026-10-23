# Signal representation and load transfer in bearing fault classification

Data and code for the article *Signal representation and load transfer in bearing fault classification*, prepared for *Ingenius, Revista de Ciencia y Tecnología* (Universidad Politécnica Salesiana, Ecuador).

Software Engineering, Faculty of Informatics and Electronics, Escuela Superior Politécnica de Chimborazo (ESPOCH), Riobamba, Ecuador.

## What the study does

Four signal representations (time-domain statistics, FFT magnitude, db4 wavelet band energies and STFT spectrogram) are combined with three vector classifiers (SVM-RBF, random forest, multilayer perceptron) and a 2D CNN, and evaluated on the sixteen (training load, test load) pairs of the CWRU drive-end dataset at 12 kHz. Windows are split by source record and by purged contiguous blocks, so no two windows sharing samples fall on opposite sides of a split. The file labels are first checked against the bearing's characteristic frequencies by envelope analysis. The comparison uses Friedman and Nemenyi tests, a three-way ANOVA on cell means, bootstrap intervals for the cross-load drop and an amplitude-normalisation ablation. The editorial revision of October 2026 added a linear mixed model with crossed load effects, a leave-one-load-out jackknife, a per-class and per-direction breakdown, and a nested hyperparameter search that uses training data only (scripts 08 and 09; outputs prefixed `rev_`).

## Repository layout

| Path | Content |
|---|---|
| `src/00_verificar_estructura.py` | Check the variables inside each CWRU `.mat` file |
| `src/00_verificar_etiquetas.py` | Verify the fault labels by envelope analysis (BPFO, BPFI, ball spin frequency) |
| `src/01_download.py` | Download and catalogue the CWRU files |
| `src/02_preprocess.py` | Windowing, record-level split and the four representations |
| `src/03_experiment.py` | 4 × 4 load matrix per representation and classifier, CNN and ablation (`--parte`) |
| `src/04_stats.py` | Friedman-Nemenyi, two-way ANOVA and amplitude ablation |
| `src/05_figures.py` | Figures 1-4 |
| `src/06_revision.py` | Three-way ANOVA on cell means; two-way ANOVA without pseudo-replication |
| `src/07_revision2.py` | Bootstrap intervals for the cross-load drop, ANOVA blocked by load pair, CNN by training load |
| `src/08_revision_editorial.py` | Mixed model with crossed load effects, jackknife by load, F1 by class and direction, recall by subgroup, leakage check and extraction times; `--ajustado` analyses the tuned results |
| `src/09_ajuste_anidado.py` | Nested hyperparameter search on training blocks only; `--por-defecto` must reproduce `resultados_por_fold.csv` exactly |
| `src/run_all.py` | Runs the pipeline in order and logs package versions to `results/logs/` |
| `fieutils/` | Shared signal-representation, statistics and plotting code |
| `results/tables/`, `results/figures/` | Every table and figure reported in the article |
| `paper/Revista_Ingenius_Ecuador/` | LaTeX source (journal template) and compiled manuscript |

## Reproducing the analysis

```bash
pip install -r requirements.txt   # PyTorch with CUDA 12.6: see the note at the top of the file
pip install -e .                  # installs the shared fieutils package
python src/run_all.py
```

`python src/run_all.py --list` prints the steps and `--from 04` resumes from a given step. The CNN step needs a CUDA GPU; the other steps run on CPU. Seed 42 throughout. On a 16-thread laptop CPU with an RTX 4050 the pipeline took about two hours after the download (which took about one more), most of it the nested search of `09_ajuste_anidado.py`. A full rerun from a fresh clone on 21 October 2026 regenerated every table in `results/tables/` byte for byte, apart from the timing columns listed below.

The CWRU Bearing Data Center files are downloaded from Case Western Reserve University by `01_download.py` and are not redistributed here. That download is the only step that needs anything outside this repository.

### What reproduces exactly

- Everything on CPU is identical with seed 42: partition, leakage check, features, SVM-RBF and random forest results, statistics.
- The multilayer perceptron on low-dimensional inputs (time-domain statistics, wavelet energies) also depends on the number of BLAS threads. `09_ajuste_anidado.py` therefore fits it in the main process, as `03_experiment.py` does; run in worker processes with one BLAS thread, 34 of its 320 default results differ.
- The CNN runs on GPU with cuDNN autotuning disabled. A rerun from a fresh clone on the same laptop GPU (RTX 4050) gave identical CNN results; on other GPUs or driver versions the last decimals may differ.
- Timing columns (`segundos_ajuste`, `segundos_prediccion`, `tabla2_costo_computacional.csv`, extraction times in `data/processed/manifiesto.json`) are wall-clock measurements and change from run to run.

### Where each result of the article comes from

| Article | Script | File in `results/tables/` |
|---|---|---|
| Label verification (2.1, supplementary S1) | `00_verificar_etiquetas.py` | `verificacion_etiquetas.csv` |
| Table 1, usable windows | `02_preprocess.py` | `ventanas_por_carga_clase.csv` |
| Table 2, representations | `02_preprocess.py` | `dimension_representaciones.csv` |
| Leakage check, 0 and 320 overlaps (2.2) | `08_revision_editorial.py` | `rev_verificacion_fuga.csv` |
| Extraction times | `02_preprocess.py`, exported by `08` | `rev_tiempos_extraccion.csv` |
| Per-fold results, every cell | `03_experiment.py` | `resultados_por_fold.csv`, `resultados_por_diametro.csv` |
| Table 3, F1 in and out of domain | `04_stats.py` | `tabla1_f1_dentro_fuera.csv` |
| Cross-load drops and intervals (3.2) | `07_revision2.py` | `caidas_ic_bootstrap.csv` |
| Drops leaving one load out (3.2, S4) | `08_revision_editorial.py` | `rev_jackknife_caidas.csv` |
| Direction asymmetry by class (3.2, S5) | `08_revision_editorial.py` | `rev_asimetria_direccion.csv`, `rev_f1_por_clase_carga_prueba.csv` |
| Friedman and Nemenyi (3.3, Figure 4) | `04_stats.py` | `resumen_estadistico.json`, `friedman_tabla_bloques.csv`, `nemenyi_pvalores.csv` |
| Two-way ANOVA on cell means (3.3) | `06_revision.py` | `anova_dos_factores_sin_pseudorreplicacion.csv` |
| Table 4, three-way ANOVA | `06_revision.py` | `anova_tres_factores.csv` |
| ANOVA blocked by pair (3.3) | `07_revision2.py` | `anova_bloqueada_por_par.csv` |
| Mixed model (3.3, S3) | `08_revision_editorial.py` | `rev_modelo_mixto_componentes.csv`, `rev_modelo_mixto_efectos_fijos.csv`, `rev_modelo_mixto_pruebas.csv` |
| Jackknife (3.3, S4) | `08_revision_editorial.py` | `rev_jackknife_por_carga.csv` |
| Nested tuning (3.3, S2) | `09_ajuste_anidado.py`, then `08 --ajustado` | `rev_ajuste_anidado_*.csv` |
| Recall by subgroup (3.4) | `08_revision_editorial.py` | `rev_recall_por_subgrupo.csv` |
| Amplitude ablation (3.5) | `03_experiment.py --parte ablacion`, `04_stats.py` | `ablacion_por_fold.csv`, `ablacion_resumen.csv` |
| Ablation intervals over the twelve pairs (supplementary S6) | `08_revision_editorial.py` | `rev_ablacion_por_par.csv` |
| CNN reference | `03_experiment.py --parte cnn`, `07_revision2.py` | `cnn_por_carga_entrenamiento.csv` |
| Figures 1-4 | `05_figures.py` | `results/figures/` |

## Citation

Archived on Zenodo: [10.5281/zenodo.22907921](https://doi.org/10.5281/zenodo.22907921) (this DOI always resolves to the latest version).
