# Confronto Robyn vs Meridian su `dt_simulated_weekly` — risultati del run

Questo file contiene i **numeri** del confronto: configurazione dei due run,
tabella di sintesi e output grezzi. La lettura dei risultati e le conseguenze
per la scelta del framework stanno nel testo della tesi; qui c'è solo quanto
serve a rifare il confronto e a controllare le cifre.

Protocollo completo: [`protocollo_confronto.md`](protocollo_confronto.md).
Notebook: [`colab_robyn_demo.ipynb`](colab_robyn_demo.ipynb),
[`colab_meridian_demo.ipynb`](colab_meridian_demo.ipynb).

## Configurazione dei run

Run del 02/07/2026. Entrambi su `dt_simulated_weekly`, il dataset simulato
distribuito insieme a Robyn: nessun dato aziendale è coinvolto.

| | Robyn | Meridian |
|---|---|---|
| Versione | 3.12.x (CRAN) | google-meridian |
| Ambiente | Colab CPU | Colab GPU T4 |
| Durata | ~1–1,5 h | ~20 min |
| Campionamento | 2000 iterazioni × 5 trial | 4 catene × 1000 draw |
| Validazione | ts_validation, train_size ~80% | holdout ultime 21 settimane |
| Modello riportato | `3_1638_1`, miglior NRMSE test tra i vincitori dei cluster | posterior unico |

## Tabella di sintesi

| Criterio | Robyn (3_1638_1) | Meridian (national) | Lettura |
|---|---|---|---|
| R² test (ultime ~21 sett.) | **0.983** | **0.847** | Robyn nettamente migliore |
| R² train | 0.945 | 0.935 | equivalenti |
| Errore test (secondario) | NRMSE 0.041 | MAPE 12.1% / wMAPE 12.1% | non confrontabili tra loro |
| ROAS tv | 2.93 | 7.84 (IC90: 4.88–11.70) | **punto Robyn FUORI dall'IC** |
| ROAS ooh | 0.59 | 1.11 (IC90: 0.24–2.94) | dentro l'IC |
| ROAS print | 5.24 | 8.67 (IC90: 0.59–22.43) | dentro l'IC (IC amplissimo) |
| ROAS facebook | 0.81 | 2.47 (IC90: 0.30–8.39) | dentro l'IC |
| ROAS search | 0.34 | 1.70 (IC90: 0.27–4.91) | dentro l'IC (al limite inferiore) |
| Ordinamento canali per ROAS | print > tv > fb > ooh > search | print > tv > fb > search > ooh | quasi identico (scambio in coda) |
| decomp.rssd | 0.463 | n/d (non usa questo criterio) | alto: fit e "business fit" in tensione |
| Selezione modello | 7 candidati, scelta per NRMSE test | posterior unico | grado di libertà dell'analista |
| Tempo di run | ~1–1,5 h (CPU, 1 core) | ~20 min (GPU T4) | |

Nota: `mape = 0` nell'output di Robyn indica solo l'assenza di calibrazione
con esperimenti, non un errore nullo.

## Dati grezzi

### `robyn_metrics.csv` — 7 candidati, ordinati per NRMSE test

| solID | R² train | R² val | R² test | NRMSE test | decomp.rssd |
|---|---|---|---|---|---|
| 3_1638_1 (selezionato) | 0.945 | 0.966 | 0.983 | 0.0413 | 0.463 |
| 4_1893_1 | 0.942 | 0.963 | 0.981 | 0.0431 | 0.393 |
| 3_1875_1 | 0.940 | 0.963 | 0.979 | 0.0452 | 0.378 |
| 3_1923_1 | 0.939 | 0.962 | 0.978 | 0.0467 | 0.334 |
| 4_1590_1 | 0.938 | 0.939 | 0.978 | 0.0473 | 0.313 |
| 4_1053_1 | 0.933 | 0.937 | 0.975 | 0.0504 | 0.309 |
| 2_1480_1 | 0.930 | 0.937 | 0.973 | 0.0517 | 0.311 |

### ROAS per canale

| Canale | Robyn roi_total | Robyn effect share | Robyn spend share | Meridian ROI medio | Meridian IC 90% |
|---|---|---|---|---|---|
| tv | 2.93 | 47.2% | 21.3% | 7.84 | 4.88–11.70 |
| ooh | 0.59 | 27.5% | 61.9% | 1.11 | 0.24–2.94 |
| print | 5.24 | 21.2% | 5.3% | 8.67 | 0.59–22.43 |
| facebook | 0.81 | 1.9% | 3.1% | 2.47 | 0.30–8.39 |
| search | 0.34 | 2.2% | 8.5% | 1.70 | 0.27–4.91 |

### `meridian_metrics.csv`

| Metrica | Train | Test | Tutto |
|---|---|---|---|
| R² | 0.935 | 0.847 | 0.928 |
| MAPE | 5.9% | 12.1% | 6.5% |
| wMAPE | 5.5% | 12.1% | 6.2% |

## Cosa non è stato eseguito

I run di stabilità con seed 43 e 44 su entrambi i framework (criterio d del
protocollo) non sono stati eseguiti. La variabilità tra run ripetuti di Robyn
non è quindi quantificata in questo confronto, e il confronto sui tempi vale
per un run singolo per framework.
