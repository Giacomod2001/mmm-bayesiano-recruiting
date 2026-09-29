# Pre-registrazione — N1: Meridian con meno nodi. La baseline flessibile decide il livello, l'ordine dei canali, o nessuno dei due?

**22 settembre 2026.** Scritta prima di qualunque fit di N1: al momento in cui questo documento entra
in git non esiste un solo numero di N1, né su Drive né altrove. Qualunque risultato va in un file
separato, `RISULTATI_N1_nodi_<data>.md`, scritto dopo.

---

## 1. Domanda

La flessibilità della baseline temporale di Meridian determina quanto il modello sovra-attribuisce ai
media **e** quanto bene ordina i canali? Sugli otto mondi, non su uno.

**Da dove viene.** Oggi la sensibilità ai nodi è misurata su un mondo solo. L'Appendice A in bozza
(`Tesi_Appendice_A_bozza.md`, Sezione A.2, righe 1–3) riporta sul mondo 42, con 3, 6 e 12 nodi per
trimestre (24, 48, 96 nodi), una quota stimata di 57,9%, 47,6% e 41,9% e un rapporto stimato/vero di
3,13×, 2,57× e 2,26×. Nessuno ha mai guardato che cosa fanno i nodi all'**ordine** dei canali. Sui
dati di D0, intanto, Meridian ordina i canali peggio di una regola che non usa alcun modello (§4.2).
Uno stimatore senza baseline temporale (M0: NNLS con effetti fissi di regione) arriva a +0,66, poco
più della regola. La baseline a 96 nodi è l'indiziato: può assorbire una parte del segnale che
spetterebbe ai media.

## 2. Disegno

**Dati.** Il mondo **base** (osservativo) di ciascuno degli otto semi — 42, 101, 102, 103, 104, 105,
106, 107 — cioè gli stessi dati di D0. Nessuna modifica al generatore, nessun disegno sperimentale
sulla spesa, nessun flag del generatore.

**Tre livelli nuovi di nodi.** `KNOTS_PER_QUARTER` = **1**, **3**, **6**. Il numero di nodi lo calcola
la CELLA 9 del notebook congelato `colab_end_to_end.ipynb`:
`N_KNOTS = min(N_SETTIMANE, max(1, int(round(N_SETTIMANE / 13.0 * KNOTS_PER_QUARTER))))`.
Con 104 settimane dà **8, 24 e 48 nodi**. Il runner R8 ripete lo stesso calcolo dopo il fit e si ferma
se `N_KNOTS` non torna.

**Il livello 12 (96 nodi) è D0.** È già nel repository, in `griglia/griglia_D0_osservativo.csv` e
`griglia/griglia_D0_osservativo_canali.csv`: non si rifà, si riusa. Il livello 1 è il più vicino a
M0, che non ha baseline temporale: è il test diretto dell'ipotesi.

**25 fit.** Tre livelli × otto mondi = 24 fit, più **1 fit di replica** (§3). Numerazione e ordine,
fissati adesso:

| n | run | nodi/trim. | nodi |
|---|---|---:|---:|
| 1 | `N1_k12_replica_m0042` | 12 | 96 |
| 2–9 | `N1_k01_m0042`, poi 101, 102, …, 107 | 1 | 8 |
| 10–17 | `N1_k03_m0042`, poi 101, 102, …, 107 | 3 | 24 |
| 18–25 | `N1_k06_m0042`, poi 101, 102, …, 107 | 6 | 48 |

Prima la replica, poi il livello 1, poi il 3, poi il 6. Dentro ogni livello il mondo 42 va per primo.

**Tutto il resto identico alla griglia.** keep 2.000, 4 catene, adapt 500, burnin 500, **seme MCMC 42
su tutti i mondi**, `revenue_per_kpi` 40,0, prior ROI LogNormale(0,2; 0,9) di riferimento, stagionalità
a 4 decimali.

**Generatore e runner.** Il generatore è ricostruito da `main` del repository pubblico, più la catena
A, più G1…G4, più G6: impronta **`8f86eb032d0113c0`**. G6 qui non si usa, ma l'impronta resta quella
dei notebook D12 e D13. Il runner è **R8** (`runner_R8_griglia.py`), che supporta già
`--knots-per-quarter`.

**Impronta dei dati, a ogni run.** L'impronta attesa dell'`InputData` di ogni run è quella di D0
dello stesso mondo, letta da `griglia/griglia_D0_osservativo.csv`, colonna `impronta_input_data`.
Se un'impronta differisce, i dati non sono quelli di D0 e la riga è un'anomalia.

**Cartella su Drive nuova: `MMM_griglia_N1`.** Nessuna cartella esistente si tocca.

## 3. Il cancello di replica, prima di tutto il resto

Il fit n. 1 è `KNOTS_PER_QUARTER` = 12 sul mondo 42, cioè una replica esatta di D0. La pipeline è
deterministica: D0 ha riprodotto lo studio osservativo alla quarta cifra
(`griglia/griglia_D0_osservativo_verifiche.csv`, «IDENTICO allo studio osservativo (2.2348)»). Valori
attesi, dalla riga del mondo 42 di `griglia/griglia_D0_osservativo.csv`:

| campo | atteso | come si confronta |
|---|---|---|
| `rapporto_mediana` | 2,2348 | uguale a 4 decimali (\|differenza\| ≤ 0,00005) |
| `pit` | 0,000125 | uguale a 6 decimali |
| `impronta_input_data` | `b3215553829a` | identica |
| `n_knots` | 96 | identico |

Il notebook applica la stessa regola `identico_osservativo` usata per D0. Controlla quindi anche
`rapporto_ci05` 1,6048, `rapporto_ci95` 2,9857 e `dentro` 0, e la configurazione del fit riga per riga.

**Regola del cancello, esaustiva:**

| # | Condizione | Esito |
|---|---|---|
| 1 | il runner non ha scritto nessuna riga (processo morto, runtime caduto) oppure ha scritto una riga con `esito` diverso da `ok` (errore tecnico) | **NESSUN NUMERO**: nessun altro fit parte. Al rilancio si ritenta la replica, e solo quella. Un errore tecnico non è un risultato |
| 2 | tutti i campi della tabella sopra coincidono, e la configurazione del fit coincide | **REPLICA RIUSCITA**: partono i 24 fit, nell'ordine del §2 |
| 3 | altrimenti | **CI SI FERMA.** La pipeline non è più quella di D0, e i confronti con D0 non valgono. Nessun altro fit parte, né ora né al rilancio. Si scrive che cosa differisce |

Il fit di replica **non entra nelle regole del §5**: il livello 12 delle regole è D0, letto dal file.

## 4. Metriche

### 4.1 Per ogni livello di nodi, sugli otto mondi

- **`E`** = `quota_media_stimata_pct` − `quota_media_vera_pct`, in punti percentuali. Si calcola
  dalle due colonne del CSV principale, scritte a due decimali.
- `rapporto_mediana`, `C_tot` e PIT. `C_tot` conta i mondi in cui l'intervallo al 90% sul totale
  contiene il vero (colonna `dentro` = 1). Lo script lo confronta anche con `pit` fra 0,05 e 0,95, e
  riporta qualunque disaccordo.
- **`rho`** = colonna `rho_spearman` del file `_canali.csv`. È la correlazione di rango fra il ROI
  stimato e il ROI vero, per mondo.
- R-hat, ESS e divergenze.

**Ammissibilità.** Si usa il criterio della Sezione 4.7, con due cancelli: (1) il prior non contiene
la risposta; (2) R-hat ≤ 1,1 ed ESS ≥ 100 su `roi_m` e `beta_m`. Le divergenze si riportano e da sole
non squalificano. Un run non ammissibile si riporta col suo numero **e non si rifà**.

### 4.2 I due riferimenti, fissati adesso e riportati accanto a ogni `rho`

**Riferimento «spesa inversa» = 17/28 = +0,6071.** È la regola senza modello: ordinare i canali per
spesa crescente. È stato **ricalcolato il 22 settembre da `griglia/griglia_D0_osservativo_canali.csv`**
(colonne `spesa` e `roi_vero`), come correlazione di rango di Spearman fra −`spesa` e `roi_vero`,
mondo per mondo. Coincide con il +0,607 del prompt. Minimo +0,3214, massimo +0,7857, positivo in 8
mondi su 8. **È questo il valore che si usa, e non si cambia.**

**Riferimento del caso = 13/56 = +0,2321.** È il 90° percentile del nullo di permutazione usato per
M0: la distribuzione della **mediana su otto mondi** di `rho` fra la verità e un ordinamento casuale
di sette canali. Si ottiene con 10.000 replicazioni e il seme 20260918 (`confronto_M0.py`, funzione
`nullo`), ed è stato ricalcolato il 22 settembre con lo stesso risultato.

**D0 sugli otto mondi, dal file** (è il livello 12, e la riga zero di ogni tabella dei risultati):

| Mondo | `E` (punti) | `rho` Meridian | dentro | `rho` «spesa inversa» | k/28 |
|---|---:|---:|---:|---:|---:|
| 42 | +23,32 | −0,8214 | 0 | +0,6429 | 18 |
| 101 | +27,28 | +0,3214 | 0 | +0,6429 | 18 |
| 102 | +22,53 | +0,2143 | 0 | +0,5714 | 16 |
| 103 | +29,50 | +0,0357 | 0 | +0,3214 | 9 |
| 104 | +28,91 | −0,1071 | 0 | +0,6071 | 17 |
| 105 | +18,39 | +0,1071 | 0 | +0,5714 | 16 |
| 106 | +19,30 | −0,1071 | 0 | +0,6071 | 17 |
| 107 | +11,84 | −0,3571 | 0 | +0,7857 | 22 |
| **mediana** | **+22,925** | **−0,0357** | **`C_tot` 0** | **+0,6071** | 34/56 |

### 4.3 Aritmetica esatta, perché nessun risultato cada su un arrotondamento

- **Livello.** `E` e `ΔE` si calcolano in **centesimi di punto interi**, perché le due colonne del
  CSV hanno due decimali. La mediana è la media dei due valori centrali. Il confronto con ±5,0 punti
  (±500 centesimi) è esatto, senza virgola mobile.
- **Ordine.** Con sette canali senza pari merito, `rho` = 1 − 6·Σd²/336 è sempre un multiplo esatto
  di 1/28. Per ogni mondo si ricava l'intero `k` = arrotondamento di 28·`rho`. L'errore della colonna
  a quattro decimali è al massimo 0,0014, lontanissimo da 0,5. La mediana si scrive in cinquantaseiesimi,
  come `M56` = 2 × mediana dei `k`. I confronti diventano **A se `M56` ≥ 34** (cioè ≥ 17/28) e **B se
  `M56` > 13** (cioè > 13/56).
- Se per un mondo 28·`rho` dista più di 0,01 da un intero, c'è un pari merito. In quel caso si
  confronta in virgola mobile contro 17/28 e 13/56, e lo si scrive.

## 5. Regole di decisione — due regole, entrambe esaustive, prima riga che corrisponde

### 5.1 Su quali mondi si leggono

La lettura principale usa i **mondi ammissibili** del livello (§4.1), che sono `N`. È la convenzione
della griglia: «numero riportato, fuori dai conteggi principali». Accanto si riporta la stessa lettura
su **tutti** i mondi arrivati in fondo, ammissibili o no, ma quella non seleziona i rami.

- Un fit morto senza riga, o con `esito` diverso da `ok`, non ha numeri: non è fra gli `N`.
- La soglia di conteggio «6 mondi su 8» vale per `N` = 8. Se `N` < 8, si usa la stessa formula del
  notebook della griglia, `soglia = int(6/8 · N + 0,5)`: 5 per `N` = 7 e per `N` = 6, 4 per `N` = 5.
- Il riferimento di D0 per il mondo `w` è sempre la riga di D0 dello stesso mondo. Su D0 tutti e otto
  i mondi sono ammissibili.
- Un `ΔE_w` esattamente uguale a zero non conta né fra i positivi né fra i negativi.

### 5.2 Regola principale, sul LIVELLO

Per ogni mondo ammissibile `w`: **`ΔE_w = E_w(1 nodo/trim.) − E_w(D0)`**. Si leggono la mediana sugli
`N` mondi e il conteggio dei segni.

| # | Condizione | Ramo |
|---|---|---|
| 0 | `N` < 5 al livello 1 | **NON LEGGIBILE**: troppi pochi mondi ammissibili. Si riportano le cifre e non si scrive nessuna conclusione sul livello |
| 1 | mediana di `ΔE` ≥ **+5,0** **e** `ΔE` > 0 in almeno **6 mondi su 8** (o la soglia del §5.1) | **MENO NODI, PIÙ SOVRASTIMA**: la configurazione a 96 nodi è la più favorevole fra quelle provate, e il fattore 2,2 della tesi è la stima meno sfavorevole |
| 2 | mediana di `ΔE` ≤ **−5,0** **e** `ΔE` < 0 in almeno **6 mondi su 8** (o la soglia del §5.1) | **MENO NODI, MENO SOVRASTIMA**: la baseline flessibile gonfia i media |
| 3 | altrimenti | **IL LIVELLO NON DIPENDE IN MODO NETTO DAI NODI** nell'intervallo provato |

### 5.3 Regola secondaria, sull'ORDINE

Si usa la mediana di `rho` al livello **1 nodo per trimestre**, sugli `N` mondi ammissibili.

| # | Condizione | Ramo |
|---|---|---|
| 0 | `N` < 5 al livello 1 | **NON LEGGIBILE**: si riportano le cifre e non si scrive nessuna conclusione sull'ordine |
| A | mediana di `rho` ≥ **+0,6071** (17/28, il riferimento «spesa inversa» ricalcolato) | **CON LA BASELINE RIGIDA MERIDIAN ORDINA ALMENO COME LA REGOLA EMPIRICA** |
| B | mediana di `rho` > **+0,2321** (13/56) | **MEGLIO DEL CASO, NON MEGLIO DELLA REGOLA EMPIRICA** |
| C | altrimenti | **ANCHE CON LA BASELINE RIGIDA L'ORDINE NON SI DISTINGUE DAL CASO**: non è la baseline a nascondere la graduatoria |

**La riga 0 è un'aggiunta al testo del prompt**, ed è l'unica. Senza, con meno di cinque mondi le
righe 1 e 2 non potrebbero scattare e la regola darebbe il ramo 3 per mancanza di dati. Lo stesso
succederebbe con il ramo C, che è anche la previsione dichiarata sull'ordine (§7). Un ramo previsto
non deve poter uscire per mancanza di dati.

### 5.4 I rami li stampa uno script, non una persona

Lo script è `analisi_N1_nodi.py`, committato **insieme a questa pre-registrazione**. Legge i CSV di
`MMM_griglia_N1` e quelli di D0 nel repository, e stampa in prima riga il ramo del livello e il ramo
dell'ordine. Stampa anche il cancello di replica e tutto quello che il §6 chiede di riportare. Nessun
ramo si dichiara prima che lo stampi lo script.

## 6. Si riportano sempre, senza che selezionino i rami

- `E`, `rho` e `C_tot` per **tutti e quattro** i livelli (1, 3, 6 e 12 = D0), mediani e mondo per
  mondo, sia sugli ammissibili sia su tutti.
- I run ammissibili sul totale, per livello; ogni run non ammissibile col suo numero `n`; R-hat, ESS
  e divergenze.
- **La monotonia di `E` nei nodi**, cioè se `E(1) ≥ E(3) ≥ E(6) ≥ E(12)`, mondo per mondo e in
  mediana.
- **La monotonia di `rho` nei nodi**, cioè se `rho(1) ≥ rho(3) ≥ rho(6) ≥ rho(12)` oppure
  `rho(1) ≤ rho(3) ≤ rho(6) ≤ rho(12)`, mondo per mondo e in mediana.
- `rho` accanto ai due riferimenti (+0,6071 e +0,2321), a ogni livello.
- **Il confronto dei livelli 3 e 6 con la Sezione 5.8.1**: l'andamento, non le cifre (§8, punto 5).
  Sul mondo 42 si riportano la quota stimata e il rapporto dei livelli 3 e 6 accanto alle righe 1 e 2
  della Sezione A.2 (57,9% e 3,13×; 47,6% e 2,57×). Si dice che quelle righe usavano 1.000 campioni
  e non 2.000, e che precedono in parte la griglia. Il testo della Sezione 5.8.1 non è nel repository,
  perché i capitoli sono file locali. Il prompt ne riporta 3,13 → 2,57 → 2,23, mentre la A.2 dà 2,26
  per la terza riga: la differenza va sistemata nel testo, non qui.
- Il ROI stimato dei canali per livello. Serve a vedere se il meccanismo del §7 (canali piccoli fermi
  vicino al prior, eccesso ai canali grandi) cambia con i nodi.

## 7. Previsioni dichiarate

### 7.1 La previsione del prompt (Giacomo)

- **Livello: ramo 1.** Meno nodi, più sovrastima. È quello che dice la Sezione 5.8.1 sul mondo 42,
  ed è il meccanismo descritto nella tesi. Una baseline rigida non riesce a rivendicare la domanda
  stagionale, e ciò che non rivendica finisce ai canali media, che si muovono con la stagione.
- **Ordine: ramo C.** Il `rho` scarso di Meridian viene dall'attribuzione in eccesso ai canali grandi
  e sempre accesi. In D0 Google Ads è a 3,80 volte il vero come mediana sugli otto mondi (ricalcolato
  dal file: 3,797). Se con meno nodi la sovrastima cresce, l'ordine non ha motivo di migliorare.

### 7.2 La previsione della sessione che ha proposto la prova

La prova l'ha proposta il 21 settembre la sessione che ha fatto M0 («Meridian con pochi nodi»). La
motivazione di allora era: «se ρ sale, abbiamo la causa». L'attesa implicita era quindi il ramo A o
il ramo B. **Quell'attesa non è mai stata registrata, e la sessione la cambia adesso, prima di
qualunque fit di N1.** La previsione registrata è:

- **Livello: ramo 1.**
- **Ordine: ramo C.**

Il cambio poggia su tre fatti, tutti già nei file e nessuno di N1:

1. **La regola «spesa inversa» fa +0,6071 su D0** (§4.2). Il +0,66 di M0 è quindi poco più della
   regola, e perde quasi tutto il suo valore di indizio contro la baseline.
2. **In D0 i canali piccoli sono fermi vicino al prior.** Sugli otto mondi, i tre canali con meno
   spesa hanno un ROI stimato mediano di 1,28 (da 1,21 a 2,09), contro un vero mediano di 2,57. La
   mediana del prior è exp(0,2) = 1,22. I quattro canali più grandi hanno uno stimato mediano di 2,00,
   contro un vero di 1,60. Per portare `rho` sopra +0,23 i canali grandi dovrebbero scendere sotto i
   piccoli. Meno nodi, se il ramo 1 è giusto, gli danno **più** attribuzione, non meno.
3. **Il solo confronto già disponibile va in quella direzione.** Dai rapporti per canale della
   Sezione A.3 (mondo 42), il `rho` implicito vale −0,61 a 6 nodi per trimestre e −0,82 a 12. Con
   meno nodi l'ordine migliora un poco, ma resta lontanissimo da +0,23.

Le due previsioni quindi coincidono, e non è un accordo cercato. Il contrasto che il prompt si
aspettava era fra la previsione di Giacomo e l'attesa di allora della sessione, e quell'attesa è
stata ritirata qui, per le ragioni scritte sopra.

### 7.3 Cosa le smentirebbe

- **Per il livello, il ramo 2.**
- **Per l'ordine, il ramo A.** Direbbe che la baseline flessibile nasconde davvero la graduatoria,
  come suggeriva M0, e cambierebbe il capitolo 6. **Va cercato con onestà.** Anche il ramo B
  smentirebbe la previsione sull'ordine, ma in misura minore: direbbe che la baseline nasconde una
  parte della graduatoria, non tutta.

## 8. Il legame con D13, da non perdere

Il risultato nullo di D13 è stato misurato con la **baseline a 96 nodi**. D13 ha dato al modello la
domanda organica vera come controllo, con correlazione 0,975, e `E` è rimasto circa quello di D0.
Può darsi che il controllo organico non servisse proprio perché quei nodi si erano già presi la
stessa informazione.

- Se N1 trova che la baseline conta — **ramo 2 sul livello oppure ramo A sull'ordine** — potrebbe
  avere senso una prova in stile D13 con la baseline a **1 nodo per trimestre**. Basterebbe un livello
  solo, perché `f` non conta: dopo la standardizzazione dei controlli i tre livelli sono lo stesso
  dato. Sarebbero 8 fit.
- **Quella prova non la avvia nessuna sessione.** Il ramo di N1 si riporta a Giacomo: la decisione,
  e l'eventuale pre-registrazione, sono sue.
- **Nei risultati di N1 non si scrive che D13 è chiuso in assoluto.** È chiuso con la baseline a 96
  nodi.

## 9. Cosa NON è ammesso dopo aver visto i risultati

1. Spostare le soglie (±5,0 punti · 6 mondi su 8 e la formula del §5.1 · +0,6071 · +0,2321 · `N` < 5)
   o i confini dei rami.
2. Aggiungere o togliere livelli di nodi, aggiungere mondi, rifare un run non ammissibile.
3. Cambiare il riferimento «spesa inversa» dopo averlo ricalcolato: è 17/28 = +0,6071.
4. Leggere il ramo A come «Meridian funziona». Direbbe che con una baseline rigida ordina come una
   regola empirica, non che ordina bene.
5. Presentare i livelli 3 e 6 come replica esatta della 5.8.1. Quella girava sul solo mondo 42, con
   esecuzioni in parte precedenti alla griglia e con 1.000 campioni, e la tesi stessa avverte che i
   suoi valori «non vanno confrontati al centesimo» con le tabelle successive. Si confronta
   l'andamento, non le cifre.
6. Leggere i rami sull'insieme «tutti» invece che sugli ammissibili, o passare da uno all'altro dopo
   aver visto quale conviene.
7. Usare il fit di replica come dato del livello 12: il livello 12 è D0, letto dal file.
8. Far partire i 24 fit dopo un cancello di replica fallito (§3, riga 3), o rilanciare la replica
   dopo una differenza sperando che torni.
9. Avviare la prova D13 a 1 nodo per trimestre senza una decisione e una pre-registrazione di
   Giacomo, o scrivere che D13 è chiuso in assoluto (§8).

## 10. Cosa viene consegnato

1. Questa pre-registrazione, **con la sua data, committata prima** del primo fit, insieme allo
   script `analisi_N1_nodi.py` che stampa i rami.
2. Il notebook `colab_griglia_N1_nodi.ipynb`, sullo stesso impianto di `colab_griglia_D13.ipynb`. Si
   genera con `controlli_fedelta_D12_D13/fai_notebook.py` adattato al clone (la prova
   dell'adattamento, cioè D12 e D13 rigenerati identici al byte, è nel messaggio di commit). Viene
   con il collaudo locale del pre-volo, controlli 5 e 6. Il notebook caricato su Colab deve avere la
   stessa impronta di `git show HEAD:colab_griglia_N1_nodi.ipynb | sha256sum`.
3. Dopo il run: `RISULTATI_N1_nodi_<data>.md`, con **i due rami in prima riga** e le previsioni
   confermate o smentite, la tabella dei quattro livelli, il confronto con la 5.8.1 e la riga per la
   Sezione A.2 dell'Appendice A nello stesso formato delle altre.

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
