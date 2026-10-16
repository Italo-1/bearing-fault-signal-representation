# Cover letter — *Ingenius, Revista de Ciencia y Tecnología*

**To:** Editor-in-Chief, *Ingenius*, Universidad Politécnica Salesiana, Cuenca, Ecuador
**Manuscript:** "Signal representation and load transfer in bearing fault classification"
**Date:** [DD/MM/2026]

Dear Editor,

We submit for consideration in *Ingenius* the manuscript titled above. The work
measures what happens to four vibration signal representations — time-domain
statistics, FFT magnitude, db4 wavelet band energies and STFT spectrogram — when
the load at test time differs from the load at training time. Four
representations were crossed with three vector classifiers over the sixteen
(training load, test load) pairs of the CWRU drive-end dataset at 12 kHz, five
folds per cell, with the split performed by source record and, within a record,
by purged contiguous blocks, so that no two windows sharing samples fall on
opposite sides of the partition. Within a single load all four representations
exceed 0.95 macro-F1, which is the regime in which such comparisons are usually
reported and in which they separate nothing. Across loads the mean drop ranges
from 0.074 to 0.153, but the bootstrap intervals overlap, the omnibus Friedman
test does not reject (χ² = 5.20, p = 0.158), and the three per-classifier tests
each reject while placing a different representation first. The
representation × classifier interaction is the largest term of the factorial
model and survives entering the load pair as a block. An ablation dividing each
window by its RMS value, specified before the data were split, failed to improve
transfer and degraded it with Random Forest, which contradicts the mechanism
usually offered for the advantage of amplitude-invariant representations. The
conclusion is a negative one, reported as such: representation and classifier
have to be chosen together, because a recommendation drawn from one classifier
does not carry to another.

The manuscript belongs in *Ingenius* for reasons of subject and of method. Fault
diagnosis in rotating machinery is a line the journal has published repeatedly,
and the manuscript builds on four of those articles rather than citing them in
passing: the feed-forward network fed with time-domain descriptors of Contreras
Urgilés et al. (No. 21, 2019), which is the precedent for the statistical
representation used here; the multifactorial ANOVA of Llanes-Cedeño et al.
(No. 22, 2019), whose reporting of sums of squares, F, p and effect size is the
standard the statistical section follows; the comparison of two stator-lamination
measurement methods by Salazar et al. (No. 7, 2012); and the Daubechies
db4 decomposition of Gómez et al. (No. 30, 2023), which is the reason db4 rather
than another wavelet family was chosen. The journal's readership of mechanical
and electrical engineering is the audience for a result about how a measurement
choice behaves when operating conditions change, which is a maintenance
question before it is a machine-learning one. The work is computational and uses
a public dataset, without instrumentation of our own; we state this plainly in
the limitations, together with the fact that each fault condition in that dataset
corresponds to a single physical bearing, which makes the degradation reported
here a lower bound.

The manuscript is original, has not been published previously in any form, and
is not under consideration by any other journal; it will not be submitted
elsewhere while under review by *Ingenius*. All authors have read and approved
the submission and agree to its content, and their contributions are declared in
CRediT format in the manuscript. The authors declare no conflict of interest.
No funding supported this work beyond the resources of the participating
institution. The CWRU records are public and cited as such; the analysis code,
the per-fold results and the scripts that generate every table and figure are
deposited in a public repository, archived on Zenodo with the DOI
10.5281/zenodo.22907921, so that every figure in the manuscript can be
regenerated from the raw files. Because that record identifies the authors, the
DOI has been withheld from the anonymized manuscript and is given here for the
editor only; we will add it to the data availability statement upon acceptance.

Regarding the journal's policy on artificial intelligence, we declare the
following. Claude, an assistant developed by Anthropic, was used under the direct
supervision and review of the authors for three purposes: to write and debug the
signal-processing, classification, statistical-analysis and figure-generation
code described in the Materials and Methods section; to check each bibliographic
reference against its original source; and to draft and revise manuscript text
from the authors' own experimental design and results. No artificial intelligence
tool is listed as an author, none was used to generate or alter data or results,
and no figure was produced by image-generating software. All code was executed by
the authors and every reported number was traced back to that execution. The
authors take full responsibility for the content of the manuscript.

Yours sincerely,

Isaac David Torres Paredes, on behalf of the authors
Facultad de Informática y Electrónica, Escuela Superior Politécnica de
Chimborazo (ESPOCH), Riobamba, Ecuador
isaac.torres@espoch.edu.ec
