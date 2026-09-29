# Robyn a verità nota — risultati

**Ramo 2 — ANCHE IL MODELLO CONTA.** Rapporto **0,2431** = quota attribuita ai media 4,4995% /
quota vera 18,5066%. La previsione dichiarata, ramo 1, è **smentita**, e proprio dal ramo che la
pre-registrazione (§7) indicava come smentita.

Il ramo l'ha stampato lo script dell'ultima cella del notebook (`robyn_riepilogo.csv`, colonna
`ramo`). Qui è stato ricalcolato in modo indipendente da `robyn_roas.csv`, e torna alla quarta
cifra.

---

## Le quattro avvertenze, accanto a ogni cifra che segue

1. **Robyn è nazionale.** Le 20 regioni sono sommate, quindi manca la dimensione geografica che nel
   panel di Meridian dovrebbe aiutare l'identificazione. Il confronto è fra due impianti diversi,
   non fra due stimatori sulla stessa informazione.
2. **Robyn restituisce stime puntuali.** Non esiste l'equivalente della copertura: si confrontano solo
   il livello e l'ordinamento.
3. **La scelta fra i candidati di Pareto è un grado di libertà dell'analista**, ed è parte del
   confronto (Sezione 4.6).
4. **Il mondo è uno solo.** Non si generalizza.

---

## Le tre ore, e che cosa prova l'ordine

| Che cosa | Quando | Fonte |
|---|---|---|
| Inizio del run | 22 settembre 2026, 22:16:11 CEST | `robyn_riepilogo.csv` |
| Fine del run | 22 settembre 2026, 22:43:25 CEST | `robyn_riepilogo.csv` |
| Commit della pre-registrazione | 23 settembre 2026, 00:11:11 CEST (22:11:11 UTC) | commit `5f1c234`, entrato in `main` con il merge `14dccad` |

**La pre-registrazione è stata committata dopo il run.** La regola che la voleva committata prima non
è stata rispettata, e lo dice `preregistrazioni/NOTA_tempi_N1_Robyn_2026-09-22.md`. Il testo della
pre-registrazione non è stato cambiato.

**Che cosa prova che le regole precedono i numeri.** Una prova su file c'è, anche se non in git.
Sono le date dei file sul computer di Giacomo:

- il notebook eseguito, `colab_robyn_mondo42.ipynb` (sha256 `c246f1b49ebbbcbc…`, identico a quello
  committato), è nella cartella Download **dalle 21:50 CEST del 22 settembre**, 26 minuti prima
  dell'inizio del run. Il notebook contiene tutto ciò che decide il ramo: le soglie 1,5 · 1,8 · 2,6,
  la previsione «ramo 1», il criterio di scelta del modello, i range degli iperparametri e la
  definizione della quota. **Non contiene il testo intero della pre-registrazione**, per esempio
  l'elenco del §8;
- il prompt del 22 settembre, che fissa la stessa regola e la stessa previsione, ha una copia sul
  Desktop datata 21:24 CEST.

Una data di file vale meno di un commit, e lo si scrive.

---

## La quota attribuita ai media

| Definizione | Valore | Rapporto su 18,5066% |
|---|---:|---:|
| **A — quella della regola:** somma di `xDecompAgg` dei sette canali / 855.534 candidature osservate | **4,4995%** | **0,2431** |
| F — somma di `xDecompPerc`, sul dipendente fittato | 4,4915% | 0,2427 |
| Somma degli `effect_share` dei sette canali | 100% per costruzione | — |
| *Meridian in D0, stesso mondo 42* | *41,83%* | *2,26* |

In candidature: Robyn attribuisce ai sette canali **38.494,5** candidature, il vero è **158.330,7**.
F è un po' più bassa di A perché il totale fittato da Robyn (857.044,6) supera quello osservato di
1.510,6 candidature (+0,18%).

La somma degli `effect_share` vale 100% perché Robyn li calcola come quota fra i soli canali pagati.
La quota «sul fittato» è la definizione F. Il prompt del 22 settembre chiedeva la somma degli
`effect_share` intendendo la F; la pre-registrazione (§5) aveva già corretto il punto.

Avvertenze 1 e 4: un mondo solo, un impianto nazionale contro uno geografico.

---

## Per canale

ROI = contributo × 40 EUR / spesa. Il contributo vero e il ROI vero vengono da
`griglia/griglia_D0_osservativo_canali.csv`, righe con `seed_mondo = 42` (colonna `vero` in EUR, divisa
per 40).

| Canale | Spesa (EUR) | Contributo vero (cand.) | Contributo Robyn (cand.) | ROI vero | ROI Robyn | Robyn / vero | ROI Meridian D0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Google Ads | 1.271.280,34 | 47.585,7 | 13.739,0 | 1,4973 | 0,4323 | 0,289 | 4,8868 |
| Meta Ads | 958.416,12 | 38.933,8 | 11.012,7 | 1,6249 | 0,4596 | 0,283 | 5,1174 |
| LinkedIn Ads | 511.507,45 | 11.247,5 | 3.979,6 | 0,8796 | 0,3112 | 0,354 | 1,5545 |
| Indeed | 550.109,09 | 34.607,8 | 9.475,1 | 2,5164 | 0,6890 | 0,274 | 1,4159 |
| Subito Lavoro | 168.043,16 | 12.112,7 | 100,5 | 2,8832 | 0,0239 | 0,008 | 1,2273 |
| Jooble | 68.577,96 | 4.326,0 | 151,6 | 2,5232 | 0,0884 | 0,035 | 1,2653 |
| Altre job board | 139.863,12 | 9.517,1 | 36,1 | 2,7218 | 0,0103 | 0,004 | 1,2236 |
| **Totale** | **3.667.797,24** | **158.330,7** | **38.494,5** | | | | |

La spesa nel CSV di Robyn coincide al centesimo con quella della griglia. Avvertenza 2: sono stime
puntuali, senza intervallo.

---

## Ordinamento

`rho` di Spearman fra ROI stimato e ROI vero, sui sette canali:

| | `rho` |
|---|---:|
| Robyn | **−0,6071** (−17/28) |
| Regola «spesa inversa», ricalcolata dal file | +0,6429 (18/28) |
| Meridian in D0, stesso mondo | −0,8214 |

Anche Robyn capovolge l'ordine, ma per un'altra strada. Il dato che segue è descrittivo e non
seleziona rami:

- **fra i quattro canali di spesa maggiore l'ordine di Robyn è quello vero**: Indeed, Meta, Google,
  LinkedIn. Tutti e quattro sono sottostimati nella stessa misura, fra 0,27 e 0,35 volte il vero;
- **ai tre canali più piccoli dà quasi zero**, fra lo 0,4% e il 3,5% del ROI vero, e sono proprio
  quelli con il ROI vero più alto (fra 2,52 e 2,88). Da qui viene il `rho` negativo;
- Meridian invece sbaglia proprio fra i quattro grandi: mette Indeed, che è primo, in fondo.

Avvertenza 4: un mondo solo.

---

## Il modello scelto

Regola del §4: fra i vincitori dei cluster, `nrmse_test` minimo, senza guardare la quota.

- Vincitori dei cluster: 5. Scelto **`5_1794_1`** (cluster 4), `nrmse_test` **0,0719**. Gli altri
  quattro hanno fra 0,1604 e 0,1665. Nessun pari merito, quindi i criteri di spareggio non sono
  serviti. La riga 0 della regola (nessun modello selezionabile) non è scattata.
- Candidati di Pareto: 105. Diciannove hanno `nrmse_test` sotto 0,10: il modello scelto non è un caso
  isolato.

| Metrica | Train | Validazione | Test |
|---|---:|---:|---:|
| R² | 0,9216 | 0,9261 | 0,9481 |
| NRMSE | 0,0508 | 0,0747 | 0,0719 |

`decomp.rssd` 0,1214 · `train_size` effettivo 0,8065.

Avvertenza 3: la scelta fra i candidati di Pareto è un grado di libertà dell'analista. Qui l'ha fatta
una regola fissata prima.

---

## La configurazione usata

È quella del §3 della pre-registrazione, eseguita dal notebook committato:

- Robyn **3.12.1** da CRAN;
- dati `mondo42_nazionale.csv`, con impronta verificata dal notebook: sha256 LF `75b74de7…`, identico
  a `0f9a40e`;
- `dep_var_type = "conversion"`, sette spese come `paid_media_spends` e `paid_media_vars`;
- `context_vars`: stagionalita, domanda_clienti, ricerche_candidati;
- `prophet_vars = c("trend", "season")`, `prophet_country = "IT"`. Secondo la nota del §3 della
  pre-registrazione, senza `"holiday"` il paese viene ignorato;
- adstock geometrico. Range uguali per i sette canali: `alphas` 0,5–3, `gammas` 0,3–1, `thetas`
  0–0,3;
- `train_size` 0,79–0,81, `iterations` 2000, `trials` 5, `ts_validation = TRUE`,
  `add_penalty_factor = FALSE`, `seed` 42, nessuna calibrazione.

**Che cosa manca dal pacchetto consegnato.** Il notebook metteva nello zip anche la cartella
`robyn_output/` con l'onepager del modello scelto. Lo zip arrivato (`robyn_verita_nota_risultati.zip`,
sha256 `7133dd2420f16026…`) contiene solo i sette CSV, conservati in `risultati_run/`. Al ramo
l'onepager non serve.

---

## Dove finisce l'effetto dei media — descrittivo, non seleziona rami

Scomposizione del modello scelto, in quota delle 855.534 candidature osservate:

| Componente | Candidature | Quota |
|---|---:|---:|
| trend (Prophet) | 812.304,0 | 94,95% |
| season (Prophet) | 739,9 | 0,09% |
| stagionalita | 3.738,0 | 0,44% |
| domanda_clienti | 16.877,4 | 1,97% |
| ricerche_candidati | −15.109,2 | −1,77% |
| intercetta | 0,0 | 0,00% |
| **tutto ciò che non è media** | **818.550,1** | **95,68%** |
| i sette canali | 38.494,5 | 4,50% |

Nel mondo vero la parte non media vale **81,49%** (697.203,3 candidature). Circa 14 punti di effetto
dei media finiscono nel trend di Prophet.

Tre fatti, verificati sui file e **nessuno usato per scegliere o cambiare il ramo**:

1. **`ricerche_candidati` ha il segno opposto al vero.** Nel generatore entra con coefficiente
   positivo (`coef_vero` 0,22 in `dati_simulati/verita/parametri_generazione.json`, versione
   committata). In Robyn il coefficiente è −0,0281 e il contributo −15.109,2.
2. **Il range di `theta` non contiene il decadimento vero di due canali.** Nel generatore il tasso
   di decadimento settimanale (`adstock_lambda`) vale 0,5 per Meta e 0,7 per LinkedIn, fuori da 0–0,3.
   Subito Lavoro sta sul bordo (0,3); Google (0,2), Indeed (0,15), Jooble (0,1) e Altre job board
   (0,15) sono dentro. Il generatore usa l'adstock geometrico normalizzato, Robyn quello non
   normalizzato: confrontabile è solo il tasso di decadimento. Il range è stato fissato nella
   pre-registrazione, che dice che non viene dalla verità: è **un limite dichiarato prima, non un
   errore trovato dopo**. Quanto pesi sul risultato non si sa senza un altro run, e un altro run
   non cambierebbe il ramo (§8, punto 3).
3. **Il trend assorbe più della baseline vera.** Il generatore ha un livello e un trend lineare di
   baseline. Il trend di Prophet, che è più flessibile, prende anche parte della variazione che la
   spesa condivide con la stagionalità della domanda.

---

## Conseguenze per il testo della tesi

Sono proposte da approvare, non modifiche già fatte.

- **Sezione 6.5.** Due frasi vanno riviste, perché ora il confronto esiste:
  - «Robyn non è stato messo alla prova su quel mondo, e non si può quindi dire se avrebbe fatto
    meglio o peggio; è uno degli sviluppi della Sezione 7.5»;
  - la chiusura del paragrafo su PyMC-Marketing: la sovra-attribuzione, la mancata copertura e il
    residuo sarebbero «proprietà dei dati e del loro disegno, non del software che li stima». Il
    ramo 2 dice che sul livello anche il modello conta.
- **Proposta di righe per il Capitolo 7** (§9.4 della pre-registrazione). Il ramo 2 va nei limiti:
  fuori dal blocco 7.3, che non si tocca.

  > Sullo stesso mondo simulato, Robyn configurato come nel demo ufficiale attribuisce ai media il
  > 4,5% delle candidature contro un valore vero del 18,5%, circa un quarto, mentre Meridian ne
  > attribuisce 2,26 volte tanto. I due strumenti sbagliano in direzioni opposte: l'errore sul livello
  > non è soltanto una proprietà del regime osservazionale, ma dipende anche da come il modello divide
  > la variazione fra la baseline e i media. Il confronto riguarda un mondo solo e due impianti
  > diversi, uno nazionale e uno geografico, e limita la generalità del risultato senza giudicare un
  > software rispetto all'altro.

---

## File

- `risultati_run/`: i sette CSV del run, identici al byte a quelli dello zip consegnato;
- pre-registrazione: `preregistrazioni/PREREGISTRAZIONE_ROBYN_verita_nota.md` (commit `5f1c234`);
- notebook: `confronto_robyn_verita_nota/colab_robyn_mondo42.ipynb` (commit `5f1c234`);
- dati: `confronto_robyn_verita_nota/mondo42_nazionale.csv` (commit `0f9a40e`).

*File dei risultati, scritto il 23 settembre 2026 dopo che il ramo era stato stampato.*
