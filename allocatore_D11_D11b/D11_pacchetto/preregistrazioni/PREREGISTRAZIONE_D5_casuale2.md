# Pre-registrazione — D5: regime intermedio (casuale2) su otto mondi

**Versione 1, 15 settembre 2026.** Scritta PRIMA di generare i mondi 101–107 col disegno
casuale2 e prima di qualunque fit. L'unico dato esistente è il mondo 42 (registro, run 4:
1,99 sui dati committati, 6,2% di divergenze; tesi: "converge peggio").

---

## 1. Domanda

Nel regime **intermedio** — spesa scorrelata dalla stagionalità ma ancora pianificata (AR(1),
gradini trimestrali, settimane spente, pavimento) — la copertura del totale sta fra
l'osservativo (0 su 8) e il randomizzato (8 su 8)? È la spesa che segue la domanda, o è la
pianificazione in sé, a rompere l'identificazione?

## 2. Disegno

Otto mondi, `genera_dati_simulati.py --seed-mondo N --casuale2` (patch G1): due costanti della
calibrazione di `kappa` cambiano (target di correlazione spesa-stagionalità 0 invece di 0,50;
griglia bilaterale [−5, 5] a 239 punti), nessuna estrazione casuale in più. Runner
`--disegno casuale2`.

**Dichiarato: la spesa totale per canale NON è conservata** (un `kappa` diverso sposta la media
dell'esponenziale). La differenza rispetto al mondo base dello stesso seme va nel CSV **come
colonna per mondo e canale** (`spesa_vs_base_pct`, dal JSON del generatore): mondo 42 Google
−0,8%, Meta −1,1%, LinkedIn −0,6%, Indeed −1,4%, Subito −1,2%, Jooble −2,9%, Altre −1,8%;
mondo 101 fra −0,7% e −2,8%. La verità per canale resta quella del mondo base (`beta`
ricalibrato sullo stesso target).

**Verificato prima di scrivere**: `--casuale2` riproduce byte per byte
`dati_simulati/casuale2` (14 file identici, 2 uguali a meno del formato; impronta
`ba045e89147d` con l'ingestion vera); mondo 101: verità per canale = mondo base; il JSON
riporta la stessa differenza di spesa misurata sui file.

**Mondo 42 = collaudo.** Registro: 1,99 a 3 decimali; qui 4 decimali, atteso **1,99 spostato
di −1 … −1,7%** (1,96–1,97); oltre il ±2% anomalia della pipeline. Le divergenze (6% nel
registro) si riportano e non si tocca il campionatore.

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


## 5. Regola di decisione — la stessa partizione dello studio randomizzato

```
dentro = mondi con 0,05 <= PIT <= 0,95
alti   = mondi con PIT > 0,95     (il modello SOTTOSTIMA)
bassi  = mondi con PIT < 0,05     (il modello SOVRASTIMA)
sparsi = mondi con 0,20 <= PIT <= 0,80
```

| # | Condizione | Ramo |
|---|---|---|
| 1 | `dentro <= 3` | **NON COPRE**: il regime intermedio non basta; la pianificazione da sola rompe l'identificazione (lettura: è la struttura della spesa, non solo il legame con la domanda) |
| 2 | `dentro >= 7` e `sparsi >= 4` | **CALIBRATO E CENTRATO** |
| 3 | `dentro >= 7` e `sparsi <= 3` | **COPERTO MA SPOSTATO** (dichiarare la direzione: alti = sottostima, bassi = sovrastima) |
| 4 | `4 <= dentro <= 6` e `alti > bassi` | **IL VERSO SI RIBALTA COL REGIME** |
| 5 | `4 <= dentro <= 6` e `alti <= bassi` | **COPERTURA DEGRADATA**: intermedio per copertura, ma i mancati sono in basso come nell'osservativo |

Il ramo 1 qui **non è "fermarsi"** (lo studio randomizzato ha già mostrato che il metodo
funziona quando la spesa è a sorte): è un risultato, e si scrive.

## 5-bis. Si riportano sempre, non selezionano il ramo

- **Posizione fra 0 su 8 e 8 su 8**: `dentro` accanto ai due estremi già misurati.
- **Rapporto mediano** degli 8 mondi, atteso **in [1,3; 2,0]** (mondo 42: 1,99).
- `spesa_vs_base_pct` per canale e mondo, accanto ai risultati (non solo dichiarata).
- Divergenze per mondo; mondi `non_ammissibile` per R-hat/ESS: conteggio su N, N dichiarato;
  le divergenze da sole non squalificano.
- Per canale: `C_k`, `larghezza_relativa`, `rho_med` (attesa < 0,5 come nel randomizzato).

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

1. `griglia_D5_casuale2.csv` (43 colonne: le 35 dello studio di copertura + `decimali_stagionalita`,
   `prior_tipo`, `prior_sigma` + `disegno`, `canali_trattati`, `parametri_disegno` + `prior_mu`,
   `prior_mu_per_canale`),
   `griglia_D5_casuale2_canali.csv` (19 colonne), `griglia_D5_casuale2_draw/` (un `.csv.gz` per mondo,
   `totale` sommato dentro il draw), `griglia_D5_casuale2_verifiche.csv` (il controllo per riga).
2. La tabella per mondo: `rapporto_mediana`, forbice, PIT, ammissibilità, e per ogni canale
   `dentro`, `larghezza_relativa`, `dose_pct`, `riduzione_effettiva_pct`.
3. I conteggi del §5 e le grandezze del §5-bis, ciascuno su tutti i mondi e sui soli
   ammissibili, con N.
4. Questo documento, **con la sua data**, committato prima del run e separato dai risultati.
5. Se il ramo è quello sfavorevole, lo si dichiara **nella prima riga** della consegna.


## 9. Provenienza

- Generatore: `genera_dati_simulati.py` di `main` + patch A (`--seed-mondo`, 4 decimali,
  `--sanita`) + **G1** (`--casuale2`: target 0, griglia [−5, 5] × 239). **Cancello di fedeltà superato prima di scrivere questo documento**:
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
4. `copertura_risultati.csv` (osservativo, 0 su 8) e `copertura_risultati_randomizzato.csv`
   (8 su 8) sono i due estremi: devono essere disponibili per la tabella affiancata.

**Il run non parte prima di questi controlli.**

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
