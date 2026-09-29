# Pre-registrazione — D6 e D8: dose-risposta dell'esperimento geografico su Google Ads (con D1 e D7), otto mondi ciascuno

**Versione 1, 15 settembre 2026.** Scritta PRIMA di qualunque fit di D6 e D8. D1 (6 regioni,
spento) e D7 (3 regioni, spento) hanno le loro pre-registrazioni; questa aggiunge le due
varianti mancanti e fissa **prima** l'ordinamento che lega i quattro disegni. Approvata con
l'aggiustamento del 15/9: D6 contro D7 è un confronto **aperto**, con entrambe le letture
scritte prima.

---

## 1. Domanda

Quanto esperimento serve? A parità di canale (Google Ads) e di mondo: più contrasto
(spento contro dimezzato), più regioni (6 contro 3), blocchi sincroni o sfalsati fra regioni:
che cosa restringe la forbice del canale trattato, e qual è il disegno più debole che lo
identifica ancora?

## 2. Disegno

Quattro disegni sullo stesso canale, stessi otto mondi, stesse 6 regioni e stessi blocchi di
D1 (D7: le prime 3 delle 6):

| Disegno | Regioni | Intensità (moltiplicatore della quota) | Riduzione effettiva nelle celle trattate | Blocchi | Comando del runner |
|---|---|---|---|---|---|
| **D1** | 6 | 0 | −100% | 2×8, sincroni | `--disegno geo` |
| **D7** | 3 | 0 | −100% | come D1 | `canali=Google Ads;regioni=3` |
| **D6** | 6 | **0,5** | **≈ −42% … −46%** (varia col mondo: dipende dalla quota trattata) | come D1 | `canali=Google Ads;intensita=0.5` |
| **D8** | 6 | 0 | −100% | 2×8 **sfalsati per regione** (inizi propri per ogni regione, stesso rng, dopo le estrazioni standard) | `canali=Google Ads;sfalsato=1` |

**Intensità**, definizione impegnata: moltiplicatore della quota delle regioni trattate
**prima** della rinormalizzazione della settimana. Poiché la spesa nazionale è conservata, la
riduzione effettiva di spesa nelle regioni trattate è **minore** di 1 − intensità: con il
27,6% di popolazione trattata e 0,5 è −42%, non −50%; con blocchi sfalsati (meno regioni
trattate per settimana) è −46%. **In tesi va la riduzione effettiva**, colonna
`riduzione_effettiva_pct` del CSV, per canale e mondo; l'intensità è solo il parametro.

**Verificato prima di scrivere** (mondi 42 e 101): la riduzione effettiva del diario coincide
con quella misurata sui file (−37,4% e −39,2% sul mondo 101 a intensità 0,5 con 6 regioni;
−45,9% con blocchi sfalsati); canali non trattati identici al mondo base; spesa nazionale
settimanale conservata; verità per canale = mondo base; nello sfalsato ogni regione ha blocchi
propri.

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


```
M_d = mediana su 8 mondi di larghezza_relativa(Google Ads) nel disegno d
I_d = 1 se C_Google(d) >= 6, altrimenti 0
```

## 5. Regola di decisione — deterministica

**Impegni pre-registrati** (identificazione decrescente al calare della dose o del contrasto):

```
(i)  M_D1 <= M_D8
(ii) M_D1 <= min(M_D6, M_D7)
```

| # | Condizione | Ramo |
|---|---|---|
| 1 | (i) e (ii) valgono | **DOSE-RISPOSTA CONFERMATA**: il canonico è il disegno più informativo dei quattro |
| 2 | una sola violata | **PARZIALE**: si dice quale, senza riordinare |
| 3 | entrambe violate | **NESSUNA DOSE-RISPOSTA**: la raccomandazione quantitativa del cap. 7 non si scrive |

**D6 contro D7: confronto aperto, entrambe le letture scritte prima.** A parità (approssimata)
di spesa tolta, conta più il **contrasto** (D7: spento del tutto in 3 regioni) o il **numero
di regioni** (D6: dimezzato in 6)? Se `M_D7 < M_D6` conta il contrasto; se `M_D6 < M_D7`
conta il numero di regioni. **Nessuna delle due è la predizione**; il risultato si riporta con
la spesa effettivamente tolta per mondo nei due disegni (`spesa_ridistribuita_eur`).

**"Quanto basta"** = il disegno più debole con `I_d = 1`, letto sull'ordinamento impegnato
(D1 → D8 → {D6, D7}); se nessuno dei più deboli identifica, "quanto basta" è il canonico.

## 5-bis. Si riportano sempre, non selezionano il ramo

- `C_Google` e `M_d` per ciascun disegno, su tutti i mondi e sui soli ammissibili.
- Per D6: `riduzione_effettiva_pct` per mondo; per D8: i blocchi per regione (dal JSON).
- `C_tot` di ciascun disegno (attesa 0–2); danno collaterale (mediana sui non trattati di
  `larghezza_relativa(d) / larghezza_relativa(D1)`, stesso mondo), senza predizione.
- 1×8 settimane (un solo blocco) resta **facoltativa e separata**: non entra in questi
  ordinamenti.

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

1. `griglia_D6_geo_intensita05.csv` e `griglia_D8_geo_sfalsato.csv` (un CSV per disegno, 43
   colonne: le 35 dello studio di copertura + `decimali_stagionalita`, `prior_tipo`,
   `prior_sigma` + `disegno`, `canali_trattati`, `parametri_disegno` + `prior_mu`, `prior_mu_per_canale`), ciascuno con i propri
   `_canali.csv` (19 colonne), `_draw/` (un `.csv.gz` per mondo, `totale` sommato dentro il
   draw) e `_verifiche.csv` (il controllo per riga).
2. La tabella per mondo: `rapporto_mediana`, forbice, PIT, ammissibilità, e per ogni canale
   `dentro`, `larghezza_relativa`, `dose_pct`, `riduzione_effettiva_pct`.
3. I conteggi del §5 e le grandezze del §5-bis, ciascuno su tutti i mondi e sui soli
   ammissibili, con N.
4. Questo documento, **con la sua data**, committato prima del run e separato dai risultati.
5. Se il ramo è quello sfavorevole, lo si dichiara **nella prima riga** della consegna.


## 9. Provenienza

- Generatore: `genera_dati_simulati.py` di `main` + patch A (`--seed-mondo`, 4 decimali,
  `--sanita`) + **G2** (`--geo-intensita`, `--geo-sfalsato`, `--geo-regioni`). **Cancello di fedeltà superato prima di scrivere questo documento**:
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
4. D1 e D7 devono essere completi sugli otto mondi (o su N dichiarati) prima di leggere gli
   ordinamenti; D6 e D8 si eseguono dopo il nucleo D1–D5 (se c'è tempo), e la loro
   pre-registrazione è comunque committata prima del loro primo fit.

**Il run non parte prima di questi controlli.**

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
