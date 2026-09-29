# Pre-registrazione — D0: replica dello studio osservativo (base × 8 mondi) con la pipeline corrente

**Versione 1, 15 settembre 2026.** Scritta PRIMA del run. Lo studio osservativo (13/9, 0 su 8) è
il risultato principale della tesi ed è l'unico studio eseguito **prima** della patch A4: non ha né
le righe per canale né i draw. La pipeline è deterministica (run 1 e 5 del registro bit-identici
allo studio di copertura), quindi rifarlo costa 80 minuti e deve riprodurre gli stessi numeri alla
quarta cifra, producendo canali e draw. D0 gira **per primo**, prima di D1, D7 e D2: è il test
del runner patchato (R5 + R6) su otto mondi a risposta nota; i disegni che seguono girano su
quel runner e **sono interpretabili solo se D0 è identico**.

---

## 1. Domanda

Nessuna domanda nuova. D0 è una **replica di controllo**: (0) è il test del runner patchato su otto
mondi a risposta nota alla quarta cifra, e precede tutto il resto; (a) mette lo studio osservativo sulla
stessa base documentale degli altri (canali, draw, verifiche); (b) fornisce il denominatore del
danno collaterale di D1 e D3 su tutti gli otto mondi; (c) è un cancello di fedeltà della pipeline
su otto mondi invece di uno.

## 2. Disegno

Otto mondi, `--seed-mondo N` senza varianti (disegno `base`), runner `--disegno base`, nomi
`D0_base_m<seme>`. **Attesi: identici a `copertura_risultati.csv`, riga per riga.**

| Mondo | `rapporto_mediana` | forbice (`rapporto_ci05` – `rapporto_ci95`) | PIT | dentro | impronta |
|---|---:|---|---:|---:|---|
| 42 | 2.2348 | 1.6048 – 2.9857 | 0.000125 | 0 | `b3215553829a` |
| 101 | 2.4623 | 1.8414 – 3.1728 | 0.0 | 0 | `7eaa88ed1323` |
| 102 | 2.2105 | 1.5996 – 2.8568 | 0.000625 | 0 | `565abd654b6a` |
| 103 | 2.5835 | 2.046 – 3.1754 | 0.0 | 0 | `29b7941e94a3` |
| 104 | 2.5481 | 1.9694 – 3.1798 | 0.0 | 0 | `96fa64a16f1f` |
| 105 | 1.9811 | 1.4369 – 2.5887 | 0.0005 | 0 | `c6262d1d1d30` |
| 106 | 2.0244 | 1.4222 – 2.7087 | 0.001625 | 0 | `35c658e7d251` |
| 107 | 1.6106 | 1.0081 – 2.3642 | 0.047625 | 0 | `cb44b26282bc` |

Le otto righe sono incorporate nel notebook e nel file degli attesi; il pre-volo verifica che la
copia su Drive (`MMM_copertura/copertura_risultati.csv`) coincida con esse e che i semi siano
questi otto, e non parte altrimenti.

## 3. Configurazione del fit — identica al registro e ai due studi di copertura

| Parametro | Valore | Da dove |
|---|---|---|
| `KNOTS_PER_QUARTER` | 12 → **96 nodi** | `--knots-per-quarter 12` (override della CONFIG del notebook, che dice 3) |
| `N_KEEP` | **2000** | `--keep 2000` |
| Catene / adapt / burnin | 4 / 500 / 500 | default del runner |
| Seme MCMC | **42** per tutti i mondi | il mondo varia col SUO seme, non con questo |
| `revenue_per_kpi` | **40,0** EUR → esito in EUR | guardia del runner |
| Prior | `ROI ~ LogNormal(0,2; 0,9)`, di riferimento | `--prior riferimento` |
| Dati | mondi rigenerati dal generatore corretto (`stagionalita.csv` a 4 decimali) | pre-volo: `decimali_stagionalita = 4` su ogni riga |

Se anche uno solo di questi valori differisce, il confronto con gli altri disegni e con gli
studi di copertura è nullo. Le colonne `n_knots`, `keep`, `n_chains`, `adapt`, `burnin`,
`seed_mcmc`, `revenue_per_kpi`, `prior_tipo`, `prior_sigma`, `decimali_stagionalita`,
`disegno`, `parametri_disegno` del CSV sono la prova d'esecuzione: il notebook le controlla
riga per riga contro questa tabella, subito dopo ogni fit, e una differenza è un'anomalia.


## 4. Metriche — calcolate come negli studi di copertura, dal runner, mai a posteriori

- **Intervallo esatto del totale**: somma dei sette canali **dentro ogni draw**, poi quantili
  5% e 95%. **PIT** = `media(totale_draw <= vero)`. **`rapporto_mediana`** = mediana / vero.
- **Per canale** (file `_canali.csv`, una riga per mondo × canale): `dentro` = 1 se
  `ci05 <= vero <= ci95`; `larghezza_relativa` = `(ci95 - ci05) / mediana`; `roi_vero`,
  `roi_stimato`; `rho_spearman` fra la classifica dei canali per ROI stimato e per ROI vero del
  mondo; **`trattato`**, **`dose_pct`** (quota di popolazione delle regioni trattate),
  **`riduzione_effettiva_pct`** (riduzione di spesa misurata nelle celle trattate),
  **`spesa_ridistribuita_eur`**.
- **Verità**: letta solo da `<mondo>/verita/contributo_vero.csv`, quella di quel mondo. Per
  costruzione coincide con la verità del mondo base dello stesso seme (verificato: scarto
  relativo < 4·10⁻⁶, arrotondamento a 3 decimali per cella).

**Conteggi sugli N mondi arrivati in fondo** (N = 8 se nessuno fallisce):

```
C_tot = mondi con 0,05 <= PIT <= 0,95           (totale coperto)
C_k   = mondi con dentro = 1 per il canale k      (canale k coperto)
soglia di identificazione: C_k >= 6 su 8
  (se N < 8: soglia = arrotondamento di 6/8 * N, 0,5 verso l'alto; N dichiarato accanto a ogni cifra)
```

## 5. Regola di decisione — deterministica

Per ogni mondo, la riga nuova contro la riga dello studio:

| Controllo | Tolleranza | Esito se non torna |
|---|---|---|
| `rapporto_mediana` | identico alla quarta cifra (±0,00005) | **anomalia di pipeline** |
| `pit` (6 cifre), `rapporto_ci05`, `rapporto_ci95` (4 cifre), `dentro` | identici | **anomalia di pipeline** |
| impronta della spesa | identica a quella dello studio | **anomalia di pipeline** (il mondo non è più lo stesso) |
| configurazione (nodi, keep, catene, adapt, burnin, seme, prior, decimali) | identica | anomalia |

**Qualunque differenza è un'anomalia di pipeline**, non un risultato: il ciclo prosegue (il notebook non
si ferma mai), ma finché l'anomalia non è spiegata **nessun risultato della griglia si interpreta**,
perché la pipeline che li ha prodotti non è più quella dello studio principale. Per questo D0 gira
per primo: si sa dopo 80 minuti, non dopo cinque ore.
Non esiste un ramo "entro il rumore MCMC": il fit è deterministico e lo si è già misurato.

## 5-bis. Cosa D0 aggiunge, senza selezionare niente

- Le righe per canale degli otto mondi osservativi (`dentro`, `larghezza_relativa`, `rho_spearman`)
  e i draw: da qui in poi lo studio osservativo ha lo stesso corredo degli altri.
- Il denominatore del danno collaterale di D1 §5-bis e D3 §5-bis su tutti gli otto mondi.
- Il criterio di ammissibilità applicato anche allo studio osservativo (`ammissibile` per mondo).

## 6. Cosa NON è ammesso dopo aver visto i risultati

1. Cambiare le soglie (6 su 8) o i confini dei rami, o aggiungere rami.
2. Escludere un mondo per ragioni non computazionali (§7); sostituire un seme fallito.
3. Cambiare nodi, keep, prior, campionatore o dati e ripresentare il run come questo.
4. Leggere come successo un conteggio che il ramo non chiama così; usare le mediane per
   selezionare il ramo (si riportano, non selezionano).
5. Presentare ordinamenti o confronti non dichiarati qui; confrontare con run a configurazione
   diversa.
6. Interpretare prima che questa pre-registrazione sia approvata e committata.


## 7. Mondi che falliscono e criterio di ammissibilità (cap. 4.7)

Un mondo che si interrompe per errore tecnico viene **rilanciato una volta con lo stesso seme**
(il notebook lo fa da solo al rilancio). Se fallisce di nuovo resta con `esito = errore`, i
conteggi sono su N mondi e N va dichiarato. **Un seme fallito non viene mai sostituito.**

Criterio di ammissibilità: **R-hat ≤ 1,1 ed ESS ≥ 100 su `roi_m` e `beta_m`** (colonne
`rhat_roi_m`, `ess_roi_m`, `rhat_beta_m`, `ess_beta_m`). Un mondo che non lo passa è
`non_ammissibile`: **si riporta col suo numero, non si rifà** con campionatore, nodi, prior
o keep diversi. Le divergenze si riportano sempre (`divergenze`) e non squalificano da sole.

**Deciso adesso:** ogni conteggio (`C_tot`, ogni `C_k`, ogni mediana) si dà **due volte**:
su tutti i mondi arrivati in fondo e sui soli mondi ammissibili. **Il ramo si calcola sulla
prima cifra**; la seconda è la riga di sensibilità e va accanto, sempre.


## 8. Cosa viene consegnato

1. `griglia_D0_osservativo.csv` (43 colonne: le 35 dello studio di copertura + `decimali_stagionalita`,
   `prior_tipo`, `prior_sigma` + `disegno`, `canali_trattati`, `parametri_disegno` + `prior_mu`,
   `prior_mu_per_canale`),
   `griglia_D0_osservativo_canali.csv` (19 colonne), `griglia_D0_osservativo_draw/` (un `.csv.gz` per mondo,
   `totale` sommato dentro il draw), `griglia_D0_osservativo_verifiche.csv` (il controllo per riga).
2. La tabella per mondo: `rapporto_mediana`, forbice, PIT, ammissibilità, e per ogni canale
   `dentro`, `larghezza_relativa`, `dose_pct`, `riduzione_effettiva_pct`.
3. I conteggi del §5 e le grandezze del §5-bis, ciascuno su tutti i mondi e sui soli
   ammissibili, con N.
4. Questo documento, **con la sua data**, committato prima del run e separato dai risultati.
5. Se il ramo è quello sfavorevole, lo si dichiara **nella prima riga** della consegna.


## 9. Provenienza

- Generatore: `genera_dati_simulati.py` di `main` + patch A (`--seed-mondo`, 4 decimali,
  `--sanita`) + G1 + G2 + G3 (nessuna usata da D0: disegno `base`). **Cancello di fedeltà superato prima di scrivere questo documento**:
  con le patch applicate, `--seed-mondo 42` → base committato (14 file identici, i 2 a 4
  decimali uguali a meno del formato); `--seed-mondo 42 --sanita` → sanità; `--pause2` e
  `--seed-mondo 42 --pause2` → pause2; `--casuale2` → casuale2 (`ba045e89147d`); `--geo` e
  `--seed-mondo 42 --geo` → geo (`a7d6a9e15487`). Le cinque impronte del mondo 42 sono state
  ricalcolate con l'ingestion vera del notebook di tesi.
- Runner: `studio_copertura_runner.py` + B1–B4 (registro) + **R5** + **R6** (prior parametrico; senza flag il run e' identico: verificato). La logica di misura è invariata.
- Notebook: `colab_griglia.ipynb`, stesso impianto del registro (pre-volo con cancello di
  fedeltà, ciclo riprendibile, controllo per riga, mai bloccante, mondo 42 per primo).


## 10. Precondizioni prima di lanciare

1. I semi (`42, 101, …, 107`) vanno verificati contro la colonna `seed_mondo` di
   `copertura_risultati.csv` (studio osservativo), non contro la memoria. Il notebook lo fa
   nel pre-volo e si ferma se differiscono.
2. Il pre-volo deve superare il cancello di fedeltà sul mondo 42 (impronte `b3215553829a`,
   `8b172390e2b2`, `a7d6a9e15487`, `ba045e89147d`, `4714c42e463b` con le patch applicate a
   runtime): se una sola non torna, nessun disegno parte.
3. Questa pre-registrazione è approvata dall'autore e committata **prima** del primo fit del
   disegno; il file dei risultati è committato dopo, separatamente.
4. `copertura_risultati.csv` su Drive identico alle otto righe incorporate (controllo 7 del pre-volo).
   Non si salta e non si aggiusta.

**Il run non parte prima di questi controlli.**

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
