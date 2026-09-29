# Pre-registrazione — D9: robustezza al prior, mondo 42, dati base, 96 nodi (3 fit)

**Versione 1, 15 settembre 2026.** Scritta PRIMA dei tre fit. Il numero di riferimento è il
run 1 del registro (`base_96_rif_s42`, prior LN(0,2; 0,9): 2,2348, bit-identico allo studio
di copertura) e, per il prior ancorato al vero con σ 0,90, il run 8 del registro (sanità) e
i run 14–17 (circolari, fuori dai risultati).

---

## 1. Domanda

Il rapporto stima/vero ≈ 2,2 dell'osservativo è un effetto del **confondimento** (spesa che
segue la domanda) o del **prior**? Se il prior di riferimento venisse allargato, stretto, o
centrato su un'informazione realistica ma sbagliata (il ROAS di piattaforma), il
confondimento continuerebbe a dominare?

## 2. Disegno

Tre fit sul **mondo 42, dati base** (4 decimali, il mondo del run 1), 96 nodi, seme MCMC 42:

| Fit | Prior sul ROI | Comando del runner | Nota |
|---|---|---|---|
| **D9a** | LN(0,2; **1,5**) — più largo | `--prior riferimento --prior-mu 0.2 --prior-sigma 1.5` | il prior lascia più spazio ai dati |
| **D9b** | LN(0,2; **0,5**) — più stretto | `--prior riferimento --prior-mu 0.2 --prior-sigma 0.5` | il prior tira verso exp(0,2) ≈ 1,22 |
| **D9c** | **ancorato al ROAS di piattaforma** del benchmark, σ 0,90 | `--prior ancorato-benchmark --prior-sigma 0.90` | informazione realistica ma gonfiata: ROAS **aggregato sul periodo** per canale da `benchmark/roas_piattaforma_trimestrale.csv` del mondo 42 (somma di spesa × ROAS dichiarato diviso somma della spesa, cioè conversioni dichiarate × 40 / spesa). Mondo 42: Google 1,79 · Meta 2,89 · LinkedIn 0,57 · Indeed 2,63 · Subito 3,03 · Jooble 3,03 · Altre 3,22 (ROI veri: 1,50 · 1,63 · 0,88 · 2,52 · 2,88 · 2,52 · 2,72) |

**Patch R6 del runner, scritta e collaudata il 15/9** (approvazione B5): `--prior-mu` e
`--prior-sigma` sul prior di riferimento (default 0,2 e 0,9), `--prior ancorato-benchmark` che
legge i ROAS dal benchmark del mondo; due colonne in più nel CSV (`prior_mu`,
`prior_mu_per_canale`). Cancello in locale superato: senza i nuovi flag la riga del run 1 è
identica a quella del runner R5 su tutte le colonne stabili. Il cancello **sul numero** (2,2348)
si chiude su Colab: D0 (mondo 42, stesso runner R6 senza flag) precede D9 e deve dare 2,2348.

**Mondo 42 = collaudo** solo per configurazione: i tre fit non hanno atteso puntuale; il
riferimento è il 2,2348 del run 1.

## 3. Configurazione del fit — identica al registro e ai due studi di copertura

| Parametro | Valore | Da dove |
|---|---|---|
| `KNOTS_PER_QUARTER` | 12 → **96 nodi** | `--knots-per-quarter 12` (override della CONFIG del notebook, che dice 3) |
| `N_KEEP` | **2000** | `--keep 2000` |
| Catene / adapt / burnin | 4 / 500 / 500 | default del runner |
| Seme MCMC | **42** per tutti i mondi | il mondo varia col SUO seme, non con questo |
| `revenue_per_kpi` | **40,0** EUR → esito in EUR | guardia del runner |
| Prior | **varia per fit** (§2): D9a LN(0,2; 1,5), D9b LN(0,2; 0,5), D9c ancorato al benchmark σ 0,90 | `prior_tipo`, `prior_sigma`, `prior_mu_per_canale` nel CSV |
| Dati | mondo 42 base rigenerato (`--seed-mondo 42`), 4 decimali | impronta `b3215553829a` |

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

```
K = numero dei tre fit con rapporto_mediana > 1,8
```

| # | Condizione | Ramo |
|---|---|---|
| 1 | `K = 3` | **IL CONFONDIMENTO DOMINA IL PRIOR**: la sovrastima non è un artefatto del prior di riferimento |
| 2 | `K = 2` | dichiarare quale fit scende sotto 1,8 (atteso: nessuno; se uno, D9b, il prior stretto) e non generalizzare |
| 3 | `K <= 1` | **IL PRIOR CONTA PIÙ DEL CONFONDIMENTO**: il cap. 6 va riscritto |

**Pre-registrati e riportati** (non selezionano):
- `rapporto(D9c) >= rapporto(run 1)`: un prior già gonfiato non si corregge da solo.
- `rapporto(D9b) < rapporto(D9a)`: il prior stretto tira verso 1,22.
- La forbice del totale (`rapporto_ci05`, `rapporto_ci95`) e `dentro` per ciascun fit; per
  canale, `larghezza_relativa` e `rho_spearman` contro il run 1.

## 5-bis. Limiti dichiarati

Un solo mondo: nessun conteggio su 8, nessuna copertura. D9 serve a rispondere a un'obiezione
("è il prior"), non a stimare un effetto; la generalizzazione a otto mondi, se servisse,
sarebbe una pre-registrazione nuova.

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

1. `griglia_D9_prior.csv` (43 colonne: le 35 dello studio di copertura + `decimali_stagionalita`,
   `prior_tipo`, `prior_sigma` + `disegno`, `canali_trattati`, `parametri_disegno` + `prior_mu`,
   `prior_mu_per_canale`),
   `griglia_D9_prior_canali.csv` (19 colonne), `griglia_D9_prior_draw/` (un `.csv.gz` per mondo,
   `totale` sommato dentro il draw), `griglia_D9_prior_verifiche.csv` (il controllo per riga).
2. La tabella per mondo: `rapporto_mediana`, forbice, PIT, ammissibilità, e per ogni canale
   `dentro`, `larghezza_relativa`, `dose_pct`, `riduzione_effettiva_pct`.
3. I conteggi del §5 e le grandezze del §5-bis, ciascuno su tutti i mondi e sui soli
   ammissibili, con N.
4. Questo documento, **con la sua data**, committato prima del run e separato dai risultati.
5. Se il ramo è quello sfavorevole, lo si dichiara **nella prima riga** della consegna.


## 9. Provenienza

- Generatore: `genera_dati_simulati.py` di `main` + patch A (`--seed-mondo`, 4 decimali,
  `--sanita`) + **R6** (prior parametrico, da scrivere; il percorso senza flag resta identico al run 1). **Cancello di fedeltà superato prima di scrivere questo documento**:
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
4. R6 collaudata: il run 1 rifatto col runner R6 senza i nuovi flag deve restare bit-identico
   (2,2348). Il benchmark del mondo 42 (`roas_piattaforma_trimestrale.csv`) deve essere quello
   rigenerato, identico al committato (cancello di fedeltà).

**Il run non parte prima di questi controlli.**

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
