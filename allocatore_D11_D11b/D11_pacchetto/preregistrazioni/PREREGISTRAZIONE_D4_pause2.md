# Pre-registrazione — D4: esperimento temporale (pause2) su otto mondi

**Versione 1, 15 settembre 2026.** Scritta PRIMA di generare i mondi 101–107 col disegno
pause2 e prima di qualunque fit. L'unico dato esistente è il mondo 42 del registro (run 3:
2,17 sui dati committati; Google 2,05, Indeed 1,08, Jooble 0,95 trattati; Meta 4,33).

---

## 1. Domanda

L'esperimento temporale — spegnere un canale per blocchi di settimane ovunque — identifica i
canali che spegne? Ed è peggio o meglio dell'esperimento geografico, a parità di canale e di
mondo?

## 2. Disegno

Otto mondi, `genera_dati_simulati.py --seed-mondo N --pause2` (patch G1 apre `--pause2` ai
mondi; il disegno è quello committato: Google Ads, Indeed e Jooble spenti in due blocchi da 8
settimane in **tutte** le regioni, spesa ridistribuita sulle settimane attive dello stesso
canale, totale per canale conservato; Meta, LinkedIn, Subito Lavoro e Altre job board sono i
controlli, identici al mondo base). Runner `--disegno pause2`. Blocchi fissi (1-based), uguali
in ogni mondo: **Google Ads 13–20 e 53–60, Indeed 24–31 e 73–80, Jooble 37–44 e 85–92**
(`PAUSE2_BLOCCHI_1BASED`; scelti perché le settimane a spesa zero dei tre trattati non si
intersechino con le pause ereditate dalla base), riportati nel JSON del mondo (`scenario_pause`).

**Verificato prima di scrivere**: `--seed-mondo 42 --pause2` riproduce byte per byte
`dati_simulati/pause2` (14 file identici, 2 uguali a meno del formato; impronta
`4714c42e463b` con l'ingestion vera); mondo 101: controlli identici al mondo base in spesa,
impressioni e clic (4 su 4), totale per canale conservato (−0,001% al massimo,
arrotondamento), verità per canale = mondo base.

**Mondo 42 = collaudo.** Registro: 2,17 a 3 decimali; qui 4 decimali, atteso **2,17 spostato
di −1 … −1,7%** (2,13–2,15); oltre il ±2% è un'anomalia della pipeline.

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


## 5. Regola di decisione — deterministica, prima riga che corrisponde

| # | Condizione | Ramo |
|---|---|---|
| 1 | `C_Google`, `C_Indeed`, `C_Jooble` tutti `>= 6` | **IDENTIFICA I TRATTATI** |
| 2 | uno o due `>= 6` | **PARZIALE**: elencare quali, con la quota di spesa (Google 34,7%, Indeed 15,0%, Jooble 1,9%) |
| 3 | nessuno `>= 6` | **NON IDENTIFICA**: dichiararlo in prima riga |

**Temporale contro geografico su Google Ads** (D4 contro D1, stesso mondo, stesso canale;
dose diversa per costruzione: il temporale tratta il 100% delle regioni per 16 settimane, il
geografico il 17,6–37,2% per 16 settimane):

```
W = mondi in cui larghezza_relativa(Google, D1 geo) < larghezza_relativa(Google, D4 pause2)
```

Pre-registrato: **il geografico identifica meglio**, perché confronta regioni nello stesso
momento invece di momenti diversi. `W >= 6` conferma; `W <= 2` smentisce; 3–5 non conclusivo.

## 5-bis. Si riportano sempre, non selezionano il ramo

- `C_tot`, attesa **0–2** (mondo 42: forbice del totale senza il vero, come il geo).
- Non trattati: mediana sugli 8 mondi del rapporto stima/vero di Meta Ads (mondo 42: 4,33),
  attesa > 2; `C_Meta` ≤ 2.
- Per i tre trattati: `rapporto_mediana` per canale e mondo (mondo 42: 2,05 · 1,08 · 0,95) e
  `larghezza_relativa`; per Google, la coppia (D1, D4) per mondo che genera `W`.
- Le otto `rapporto_mediana` e i PIT.

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

1. `griglia_D4_pause2.csv` (43 colonne: le 35 dello studio di copertura + `decimali_stagionalita`,
   `prior_tipo`, `prior_sigma` + `disegno`, `canali_trattati`, `parametri_disegno` + `prior_mu`,
   `prior_mu_per_canale`),
   `griglia_D4_pause2_canali.csv` (19 colonne), `griglia_D4_pause2_draw/` (un `.csv.gz` per mondo,
   `totale` sommato dentro il draw), `griglia_D4_pause2_verifiche.csv` (il controllo per riga).
2. La tabella per mondo: `rapporto_mediana`, forbice, PIT, ammissibilità, e per ogni canale
   `dentro`, `larghezza_relativa`, `dose_pct`, `riduzione_effettiva_pct`.
3. I conteggi del §5 e le grandezze del §5-bis, ciascuno su tutti i mondi e sui soli
   ammissibili, con N.
4. Questo documento, **con la sua data**, committato prima del run e separato dai risultati.
5. Se il ramo è quello sfavorevole, lo si dichiara **nella prima riga** della consegna.


## 9. Provenienza

- Generatore: `genera_dati_simulati.py` di `main` + patch A (`--seed-mondo`, 4 decimali,
  `--sanita`) + **G1** (instradamento dei disegni per mondo: `--seed-mondo N --pause2`). **Cancello di fedeltà superato prima di scrivere questo documento**:
  con le patch applicate, `--seed-mondo 42` → base committato (14 file identici, i 2 a 4
  decimali uguali a meno del formato); `--seed-mondo 42 --sanita` → sanità; `--pause2` e
  `--seed-mondo 42 --pause2` → pause2; `--casuale2` → casuale2 (`ba045e89147d`); `--geo` e
  `--seed-mondo 42 --geo` → geo (`a7d6a9e15487`). Le cinque impronte del mondo 42 sono state
  ricalcolate con l'ingestion vera del notebook di tesi.
- Runner: `studio_copertura_runner.py` + B1–B4 (registro) + **R5** (`--disegno`,
  `--parametri-disegno`, tre colonne, dose per canale). La logica di misura è invariata.
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
4. D1 deve essere completo prima di leggere `W`.

**Il run non parte prima di questi controlli.**

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
