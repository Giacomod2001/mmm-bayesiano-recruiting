# Protocollo di confronto Robyn vs Meridian sul dataset demo di Robyn

Materiale per la tesi: disegno del benchmark, criteri di valutazione e limiti
metodologici. I due notebook (`colab_robyn_demo.ipynb`, `colab_meridian_demo.ipynb`)
implementano esattamente questo protocollo.

## 1. Obiettivo e dataset

L'obiettivo è confrontare Robyn (Meta) e Meridian (Google) sullo stesso input,
per motivare la scelta del framework adottato nella pipeline della tesi. Il
banco di prova, suggerito dal relatore, è `dt_simulated_weekly`: il dataset
demo ufficiale di Robyn con 208 settimane nazionali (23/11/2015 – 11/11/2019),
KPI `revenue`, cinque canali paid (tv, ooh, print, facebook, search — per
facebook e search sono disponibili anche impression e clic come variabili di
esposizione), un canale organico (`newsletter`) e due variabili di contesto
(`competitor_sales_B`, `events`).

Due caveat da dichiarare esplicitamente in tesi. Primo: il dataset è simulato
dal team di Robyn, quindi il processo generatore dei dati riflette le ipotesi
funzionali di Robyn (adstock geometrico, saturazione Hill); un buon risultato
di Robyn su questi dati è in parte "vantaggio di casa", e il confronto va
letto come test di robustezza di Meridian fuori dalle proprie ipotesi, non
come gara neutrale. Secondo: i dati sono nazionali, mentre il punto di forza
dichiarato di Meridian è la modellazione geo-gerarchica; qui Meridian gioca in
modalità national, cioè nella configurazione a lui meno favorevole. Entrambi i
punti rendono il confronto conservativo rispetto alla scelta di Meridian fatta
nella pipeline di questo progetto (che è geo-level).

## 2. Disegno del confronto (parità di condizioni)

Stessi dati e stessa finestra per entrambi: tutte le 208 settimane, nessun
periodo di warmup asimmetrico. Stesse variabili con lo stesso ruolo: i cinque
canali paid con la variabile di esposizione dove disponibile (facebook_I,
search_clicks_P) e la spesa per il calcolo del ROAS; newsletter come media
organico (con adstock/saturazione in entrambi i framework); competitor_sales_B
e events come controlli (events, categorica, diventa dummy in Meridian; Robyn
la gestisce nativamente).

Finestra di test comune: le ultime ~21 settimane (10%). In Robyn si ottiene
fissando `train_size = c(0.79, 0.81)` con `ts_validation = TRUE` (train ~80%,
validation il penultimo ~10%, test l'ultimo ~10%; l'intervallo stretto invece
del valore fisso 0.8 aggira un bug di `hyper_collector` con estremi identici —
il valore effettivo del modello selezionato è nella colonna `train_size` di
`robyn_metrics.csv`); in Meridian passando a `ModelSpec` un
`holdout_id` sulle stesse 21 settimane finali, che esclude il KPI dal training
e abilita le metriche out-of-sample di `predictive_accuracy`.

Tre asimmetrie inevitabili, da dichiarare: (1) Robyn "consuma" un ulteriore
10% di dati come validation per la selezione degli iperparametri, mentre
Meridian non ha ricerca di iperparametri e allena sul 90% — è una differenza
strutturale tra i due approcci, non un difetto del protocollo; (2) Meridian
raccomanda un holdout bilanciato nel tempo, qui si usa una finestra finale per
comparabilità con Robyn; (3) la stagionalità è modellata da Prophet in Robyn e
dall'intercetta tempo-variante a knot (~1 al mese) in Meridian — equivalenti
funzionali ma non identici.

Nessuna calibrazione sperimentale per nessuno dei due (niente lift test nel
dataset): Robyn senza `calibration_input`, Meridian con prior di default.

## 3. Criteri di valutazione

**(a) Accuratezza predittiva out-of-sample** — criterio primario, sull'ultimo
10%. Metrica comune: R² sul test (`rsq_test` in Robyn, riga Test di
`predictive_accuracy` in Meridian). Metriche secondarie, non direttamente
confrontabili tra loro ma utili nel commento: NRMSE test (Robyn), MAPE e wMAPE
test (Meridian). Nota: un R² test simile con dati simulati è attendibile; la
differenza va commentata solo se ampia (> 0.05–0.10).

**(b) Plausibilità di ROAS e decomposizione** — confronto per canale tra
`roi_total` di Robyn (stima puntuale della soluzione selezionata) e il
posterior di Meridian (media e intervallo di credibilità al 90%). Domande
guida: l'ordinamento dei canali per ROAS coincide? Le stime puntuali di Robyn
cadono dentro gli intervalli di Meridian? Le quote di effetto (effect share)
sono coerenti con le quote di spesa in modo sensato? Robyn offre in più
`decomp.rssd` (distanza tra quota di spesa e quota di effetto) come criterio
di selezione: va discusso come scelta di design, perché incorpora
un'assunzione di business (effetto ~ spesa) che Meridian non impone.

**(c) Curve di risposta** — confronto qualitativo tra le curve di saturazione
(onepager di Robyn vs `plot_response_curves` di Meridian): concavità, punto di
saturazione, canali che saturano prima. Rilevante perché è l'input diretto
dell'ottimizzazione di budget, cioè della parte decisionale della tesi.

**(d) Stabilità tra run** — tre run per framework (seed 42/43/44). Per Robyn
si misura la variabilità del ROAS per canale tra le soluzioni selezionate nei
tre run; per Meridian la variabilità tra posterior (attesa quasi nulla a
convergenza raggiunta, R-hat < 1.05). Qui emerge la differenza più citata in
letteratura: Robyn restituisce un fronte di Pareto di modelli tra cui
l'analista sceglie (grado di libertà soggettivo), Meridian un unico posterior
con incertezza quantificata.

**(e) Costo e usabilità** — tempo di run (Robyn ~40–60 min su CPU con 2000
iterazioni × 5 trial; Meridian ~15–30 min su GPU T4), requisiti hardware,
ergonomia dell'output (onepager automatici di Robyn vs summary/visualizer di
Meridian), trasparenza dell'incertezza (bootstrap vs posterior bayesiano).

## 4. Tabella di sintesi da compilare

| Criterio | Robyn | Meridian | Note |
|---|---|---|---|
| R² test (ultime 21 sett.) | `rsq_test` | R² riga Test | metrica comune |
| Errore test (secondario) | NRMSE test | MAPE / wMAPE test | non confrontabili tra loro |
| ROAS per canale | punto (sol. selezionata) | media + IC 90% | punto Robyn dentro IC? |
| Ordinamento canali per ROAS | — | — | coincide? |
| Stabilità tra 3 seed | sd ROAS tra run | sd ROAS tra run | |
| Tempo di run | ~40–60 min CPU | ~15–30 min GPU | |
| Selezione modello | Pareto + scelta analista | posterior unico | grado di libertà |
| Incertezza | bootstrap/cluster | credibilità bayesiana | |

## 5. Differenze strutturali (per il capitolo metodologico)

Robyn: regressione ridge con trasformazioni adstock/Hill, iperparametri
ottimizzati con Nevergrad (evolutivo multi-obiettivo su NRMSE e decomp.rssd),
stagionalità via Prophet, selezione finale tra i modelli del fronte di Pareto.
Meridian: modello bayesiano gerarchico stimato con MCMC (NUTS), adstock
geometrico e saturazione Hill come parametri con prior, stagionalità via
intercetta tempo-variante a knot, incertezza nativa nel posterior, supporto a
prior informativi da lift test (non usato qui, ma usato nella pipeline della
tesi con i ROAS di piattaforma scontati).

Conclusione attesa del capitolo: il confronto sul demo di Robyn misura
soprattutto accuratezza e stabilità in condizioni favorevoli a Robyn; la
scelta di Meridian nella pipeline si difende con gli intervalli di credibilità
sui ROAS, la calibrazione via prior e la struttura geo-gerarchica, dimensioni
che questo benchmark nazionale non può premiare per costruzione.

## 6. Fonti

- Demo ufficiale Robyn: https://github.com/facebookexperimental/Robyn/blob/main/demo/demo.R
- Dataset: https://rdrr.io/cran/Robyn/man/dt_simulated_weekly.html
- Robyn `robyn_run` / ts_validation: https://rdrr.io/cran/Robyn/man/robyn_run.html
- Meridian holdout: https://developers.google.com/meridian/docs/advanced-modeling/holdout-observations
- Meridian model fit: https://developers.google.com/meridian/docs/post-modeling/model-fit
- Meridian ModelSpec: https://developers.google.com/meridian/reference/api/meridian/model/spec/ModelSpec
