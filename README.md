# Signal representation and load transfer in bearing fault classification

Data and code for the article *Signal representation and load transfer in bearing fault classification*, prepared for *Ingenius, Revista de Ciencia y Tecnología* (Universidad Politécnica Salesiana, Ecuador).

Software Engineering, Faculty of Informatics and Electronics, Escuela Superior Politécnica de Chimborazo (ESPOCH), Riobamba, Ecuador.

## What the study does

Four signal representations (time-domain statistics, FFT magnitude, db4 wavelet band energies and STFT spectrogram) are combined with three vector classifiers (SVM-RBF, random forest, multilayer perceptron) and a 2D CNN, and evaluated on the sixteen (training load, test load) pairs of the CWRU drive-end dataset at 12 kHz. Windows are split by source record and by purged contiguous blocks, so no two windows sharing samples fall on opposite sides of a split. The file labels are first checked against the bearing's characteristic frequencies by envelope analysis. The comparison uses Friedman and Nemenyi tests, a three-way ANOVA on cell means, bootstrap intervals for the cross-load drop and an amplitude-normalisation ablation.

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

`python src/run_all.py --list` prints the steps and `--from 04` resumes from a given step. The CNN step needs a CUDA GPU; the other steps run on CPU. Seed 42 throughout.

The CWRU Bearing Data Center files are downloaded from Case Western Reserve University by `01_download.py` and are not redistributed here.

## Citation

Archived on Zenodo: [10.5281/zenodo.22907921](https://doi.org/10.5281/zenodo.22907921) (this DOI always resolves to the latest version).
