# Pre-registrazione — D3: geo per canale singolo (mondo 42, 7 fit) e i due estremi su otto mondi (14 fit in più: 21 in tutto)

**Versione 1, 15 settembre 2026.** Scritta PRIMA di qualunque fit del disegno. Nessun geo a
canale singolo esiste; i numeri del geo canonico (Google 1,11 e LinkedIn 1,24 trattati
insieme, mondo 42) non sono un atteso per questi fit.

---

## 1. Domanda

L'esperimento geografico funziona solo sul canale dominante? L'identificazione del canale
trattato dipende dalla sua quota di spesa (Google Ads 34,7%, Jooble 1,9%)?

## 2. Disegno

**Parte A — mondo 42, sette fit**: `--disegno geo --parametri-disegno "canali=<canale>"`, un
canale per volta, stesso disegno del canonico (6 regioni, 2 blocchi da 8, spento). Quando un
solo canale è trattato, riceve la **prima** estrazione del rng dedicato del mondo: quindi **i
sette fit trattano le stesse sei regioni negli stessi blocchi** (mondo 42: Trentino-Alto
Adige, Puglia, Molise, Toscana, Lazio, Sardegna; settimane 2–9 e 87–94; dose 27,6%), quelle
di Google Ads in D1. Fra i sette fit cambia **solo il canale**. Conseguenza da tenere presente
nella lettura: **D3-LinkedIn tratta regioni diverse da D1-LinkedIn** (che in D1 aveva la seconda
estrazione). Stesso disegno su tutti i canali è un pregio del confronto fra canali, ma non è lo
stesso trattamento di D1: D3 e D1 si confrontano canale per canale solo per Google Ads. Regioni, blocchi e dose sono
nel CSV (`dose_pct`) e nel JSON del mondo, prima del fit.

**Parte B — otto mondi, due canali agli estremi della quota di spesa**: Google Ads (34,7%) e
Jooble (1,9%), `canali=Google Ads` e `canali=Jooble`, 6 regioni e 2×8 come il canonico. Sul
mondo 42 i due fit sono quelli della parte A (non si rifanno): 7 + 14 = 21 fit. Per lo
stesso motivo, in ogni mondo Google e Jooble trattati da soli ricevono **le stesse regioni e
gli stessi blocchi** (quelli di Google in D1, tabella di D1 §2): fra i due fit di un mondo
cambia solo il canale, e la sua quota di spesa.

Quote di spesa sul mondo 42 (dal file di verità): Google Ads 34,7%, Meta Ads 26,1%, Indeed
15,0%, LinkedIn Ads 13,9%, Subito Lavoro 4,6%, Altre job board 3,8%, Jooble 1,9%.

**Verificato prima di scrivere**: `--geo-canali "Google Ads"` e `--geo-canali Jooble` sui
mondi 42 e 101: canali non trattati identici al mondo base (6 su 6), spesa nazionale
settimanale conservata, verità per canale = mondo base, 96 celle trattate senza righe;
impronta mondo 101 Google a 3 regioni `0660ec331b21` (a 6 regioni si registra al primo run).

**Mondo 42 = collaudo di configurazione**, non di numero.

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


## 5. Regola di decisione — deterministica (parte B, otto mondi)

| # | Condizione | Ramo |
|---|---|---|
| 1 | `C_Google >= 6` e `C_Jooble >= 6` | **INDIPENDENTE DALLA QUOTA** fra 1,9% e 34,7% |
| 2 | `C_Google >= 6` e `C_Jooble < 6` | **DIPENDE DALLA QUOTA**: la soglia sta fra 1,9% e 34,7% e non è localizzata (non si stima dopo) |
| 3 | entrambi `< 6` | **IL GEO SU CANALE SINGOLO NON IDENTIFICA**: contraddice D1, dichiararlo in prima riga |
| 4 | `C_Jooble >= 6` e `C_Google < 6` | inatteso: dichiararlo, nessuna lettura pre-approvata |

## 5-bis. Parte A (mondo 42, sette fit): si riporta, non seleziona

- Per ogni canale: `dentro` del trattato, `larghezza_relativa` del trattato, `dose_pct`,
  `rapporto_mediana` del totale.
- **Ordinamento pre-registrato**: la larghezza relativa del trattato **cresce al calare della
  quota di spesa**. Si misura con lo Spearman fra rango di quota di spesa e rango di
  larghezza sui 7 canali; **confermato se ≤ −0,5**, smentito se ≥ 0, non conclusivo fra.
  Un trattato fuori CI è un risultato: si scrive canale e quota.
- **Danno collaterale**: mediana sui non trattati di `larghezza_relativa(fit) /
  larghezza_relativa(osservativo, mondo 42, run base_96_rif_s42 del registro)`, attesa ≥ 1.
- Parte B: `C_tot` per i due canali (attesa 0–2), `rapporto_mediana` per mondo, e la relazione
  fra `dose_pct` e `larghezza_relativa` del trattato sugli 8 mondi (solo riportata).
- Un solo mondo per la parte A: nessun conteggio su 8, nessuna generalizzazione; serve a
  scegliere le parole del cap. 6, non a sostenere una frase quantitativa.

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

1. `griglia_D3_geo_canale_singolo.csv` (43 colonne: le 35 dello studio di copertura + `decimali_stagionalita`,
   `prior_tipo`, `prior_sigma` + `disegno`, `canali_trattati`, `parametri_disegno` + `prior_mu`,
   `prior_mu_per_canale`),
   `griglia_D3_geo_canale_singolo_canali.csv` (19 colonne), `griglia_D3_geo_canale_singolo_draw/` (un `.csv.gz` per mondo,
   `totale` sommato dentro il draw), `griglia_D3_geo_canale_singolo_verifiche.csv` (il controllo per riga).
2. La tabella per mondo: `rapporto_mediana`, forbice, PIT, ammissibilità, e per ogni canale
   `dentro`, `larghezza_relativa`, `dose_pct`, `riduzione_effettiva_pct`.
3. I conteggi del §5 e le grandezze del §5-bis, ciascuno su tutti i mondi e sui soli
   ammissibili, con N.
4. Questo documento, **con la sua data**, committato prima del run e separato dai risultati.
5. Se il ramo è quello sfavorevole, lo si dichiara **nella prima riga** della consegna.


## 9. Provenienza

- Generatore: `genera_dati_simulati.py` di `main` + patch A (`--seed-mondo`, 4 decimali,
  `--sanita`) + **G2** (`--geo-canali`). **Cancello di fedeltà superato prima di scrivere questo documento**:
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
4. Il registro del 15/9 (run `base_96_rif_s42`, `registro_run_canali.csv`) è il denominatore
   del danno collaterale della parte A: deve essere su Drive.

**Il run non parte prima di questi controlli.**

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
