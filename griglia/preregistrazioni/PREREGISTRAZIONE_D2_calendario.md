# Pre-registrazione — D2: calendario di esperimenti a rotazione, sette canali, otto mondi

**Versione 1, 15 settembre 2026.** Scritta PRIMA di qualunque fit del disegno. Nessun
calendario è mai stato eseguito: il mondo 42 è la prima misura, e va detto. Approvata con gli
aggiustamenti del 15/9: confondimento di dose dichiarato e controllato da **D7**, rotazione
dell'assegnazione gruppo → canale sugli otto mondi, dose riportata per canale e mondo.

---

## 1. Domanda

Il capitolo 7 raccomanda **un calendario di esperimenti a rotazione**: tutti i canali
trattati, ciascuno in regioni diverse e in periodi sfalsati. Un calendario così identifica i
sette canali? E identifica il totale? E trattare tutti i canali insieme **costa** qualcosa
rispetto a trattarne uno solo a dose comparabile?

## 2. Disegno

Otto mondi, stessi semi. `genera_dati_simulati.py --seed-mondo N --calendario
--calendario-rotazione i` (patch G3); runner `--disegno calendario --parametri-disegno
"rotazione=i"`. **Un piano, non un'estrazione: nessun generatore casuale.**

- **Gruppi di regioni**: le 20 regioni ordinate per popolazione e assegnate a 7 gruppi
  disgiunti a serpentina (giro 1 gruppi 0…6, giro 2 gruppi 6…0, giro 3 gruppi 0…5):

  | Gruppo | Regioni | Quota di popolazione |
  |---:|---|---:|
  | 0 | Lombardia, Abruzzo, Friuli-Venezia Giulia | 21,1% |
  | 1 | Lazio, Marche, Trentino-Alto Adige | 14,1% |
  | 2 | Campania, Liguria, Umbria | 13,5% |
  | 3 | Veneto, Sardegna, Basilicata | 11,8% |
  | 4 | Sicilia, Calabria, Molise | 11,7% |
  | 5 | Emilia-Romagna, Toscana, Valle d'Aosta | 14,0% |
  | 6 | Piemonte, Puglia | 13,9% |

- **Rotazione**: nel mondo di posizione i (0…7 nell'ordine 42, 101, …, 107) il canale k
  (ordine di CANALI: Google Ads, Meta Ads, LinkedIn Ads, Indeed, Subito Lavoro, Jooble, Altre
  job board) riceve il gruppo **(k + i) mod 7**. Sette rotazioni per otto mondi: il mondo 107
  (i = 7 ≡ 0) ha la stessa assegnazione del mondo 42, su un mondo diverso. Dose per canale e
  mondo (quota di popolazione trattata), già determinata:

  | Mondo | i | Google Ads | Meta Ads | LinkedIn Ads | Indeed | Subito Lavoro | Jooble | Altre job board |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|
  | 42 | 0 | 21,1 | 14,1 | 13,5 | 11,8 | 11,7 | 14,0 | 13,9 |
  | 101 | 1 | 14,1 | 13,5 | 11,8 | 11,7 | 14,0 | 13,9 | 21,1 |
  | 102 | 2 | 13,5 | 11,8 | 11,7 | 14,0 | 13,9 | 21,1 | 14,1 |
  | 103 | 3 | 11,8 | 11,7 | 14,0 | 13,9 | 21,1 | 14,1 | 13,5 |
  | 104 | 4 | 11,7 | 14,0 | 13,9 | 21,1 | 14,1 | 13,5 | 11,8 |
  | 105 | 5 | 14,0 | 13,9 | 21,1 | 14,1 | 13,5 | 11,8 | 11,7 |
  | 106 | 6 | 13,9 | 21,1 | 14,1 | 13,5 | 11,8 | 11,7 | 14,0 |
  | 107 | 0 | 21,1 | 14,1 | 13,5 | 11,8 | 11,7 | 14,0 | 13,9 |
  | media | | 15,2 | 14,3 | 14,2 | 14,0 | 14,0 | 14,3 | 14,3 |

- **Tempo**: per il canale k due blocchi da 8 settimane, 1-based **[9 + 7k, 16 + 7k]** e
  **[53 + 7k, 60 + 7k]**: Google 9–16 e 53–60, Meta 16–23 e 60–67, …, Altre job board 51–58 e
  95–102. Canali consecutivi condividono al più una settimana, in regioni diverse; nessuna
  coppia canale × regione × settimana si sovrappone; le prime 8 settimane restano libere.
- **Spesa**: nelle celle trattate spenta e ridistribuita nella stessa settimana; **spesa
  nazionale settimanale per canale conservata**, come nel geo (stessa meccanica, intensità 0).
- **Confondimento di dose, dichiarato**: la dose per canale (~14%) è circa metà di quella del
  geo canonico (Google 27,6% nel mondo 42). Se D2 identifica peggio di D1 non si distingue
  "interferenza fra canali" da "metà dose": per questo il confronto che conta è con **D7**
  (Google, 3 regioni, dose mediana 12,0%), non con D1.

**Verificato prima di scrivere** (mondi 42 e 101, rotazioni 0 e 3): 7 gruppi disgiunti
3-3-3-3-3-3-2 che coprono le 20 regioni; assegnazione (k + i) mod 7; blocchi come sopra; le
dosi dei sette canali sommano al 100%; spesa nazionale settimanale conservata (scarto massimo
0,1 EUR); verità per canale = mondo base; nessuna riga nelle celle trattate (48 per canale,
32 per il gruppo a 2 regioni). Impronte mondo 42 (rotazione 0): `7976f3769334`.

**Mondo 42 = collaudo di configurazione**, non di numero (nessun atteso: prima misura).

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

`N_ok` = numero di canali con `C_k >= 6`; `rho_med` = mediana degli 8 `rho_spearman`.

## 5. Regola di decisione — deterministica, prima riga che corrisponde

| # | Condizione | Ramo |
|---|---|---|
| 1 | `N_ok = 7` e `C_tot >= 6` | **IDENTIFICA CANALI E TOTALE**: la raccomandazione del cap. 7 regge |
| 2 | `N_ok = 7` e `C_tot <= 5` | **IDENTIFICA I CANALI, NON IL TOTALE**: la raccomandazione va indebolita così, alla lettera |
| 3 | `4 <= N_ok <= 6` | **IDENTIFICAZIONE PARZIALE**: elencare i canali non identificati con la loro quota di spesa (atteso, se succede: i piccoli) |
| 4 | `N_ok <= 3` | **IL CALENDARIO NON BASTA**: necessario ma non sufficiente; la raccomandazione va riformulata |

**Confronto a dose comparabile con D7** (Google in D2 contro Google in D7, stesso mondo):

```
W2 = mondi in cui larghezza_relativa(Google, D2) <= larghezza_relativa(Google, D7)
```

| `W2` | Lettura |
|---|---|
| `>= 6` | **trattare tutti i canali insieme non costa niente** |
| 3–5 | non conclusivo |
| `<= 2` | **costa**: l'interferenza fra canali trattati insieme allarga l'intervallo |

Le dosi di Google per mondo in D2 e in D7 si riportano accanto a `W2`; il confronto D2–D1 si
riporta ma **non** si legge come costo dell'interferenza (dose diversa).

## 5-bis. Si riportano sempre, non selezionano il ramo

- **`rho_med`**, predizione dichiarata **≥ 0,7**. Lettura meccanica: ≥ 0,7 la classifica dei
  canali è usabile; 0,5–0,7 usabile per ordinare; < 0,5 no (randomizzato: 0,27).
- Ramo sfavorevole scritto prima: se `C_tot <= 5` anche col calendario, **il totale non è
  identificato da esperimenti parziali**, e lo si dice.
- Per ogni canale: `C_k`, mediana di `larghezza_relativa` sugli 8 mondi, e la sua relazione con
  la dose (Spearman fra `dose_pct` e `larghezza_relativa` sugli 8 mondi, per canale: solo
  riportato).
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

1. `griglia_D2_calendario.csv` (43 colonne: le 35 dello studio di copertura + `decimali_stagionalita`,
   `prior_tipo`, `prior_sigma` + `disegno`, `canali_trattati`, `parametri_disegno` + `prior_mu`,
   `prior_mu_per_canale`),
   `griglia_D2_calendario_canali.csv` (19 colonne), `griglia_D2_calendario_draw/` (un `.csv.gz` per mondo,
   `totale` sommato dentro il draw), `griglia_D2_calendario_verifiche.csv` (il controllo per riga).
2. La tabella per mondo: `rapporto_mediana`, forbice, PIT, ammissibilità, e per ogni canale
   `dentro`, `larghezza_relativa`, `dose_pct`, `riduzione_effettiva_pct`.
3. I conteggi del §5 e le grandezze del §5-bis, ciascuno su tutti i mondi e sui soli
   ammissibili, con N.
4. Questo documento, **con la sua data**, committato prima del run e separato dai risultati.
5. Se il ramo è quello sfavorevole, lo si dichiara **nella prima riga** della consegna.

## 9. Provenienza

- Generatore: `genera_dati_simulati.py` di `main` + patch A (`--seed-mondo`, 4 decimali,
  `--sanita`) + **G2** + **G3** (`--calendario`, `--calendario-rotazione`). **Cancello di fedeltà superato prima di scrivere questo documento**:
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
4. **D7 deve essere completo** sugli otto mondi (o su N dichiarati) prima di leggere `W2`; il
   calendario può girare prima, ma `W2` non si calcola finché D7 non è finito.

**Il run non parte prima di questi controlli.**

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
