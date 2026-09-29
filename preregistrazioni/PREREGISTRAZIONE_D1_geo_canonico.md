# Pre-registrazione — D1: esperimento geografico canonico su otto mondi

**Versione 1, 15 settembre 2026.** Scritta PRIMA di generare i mondi 101–107 col disegno geo
e prima di qualunque fit della griglia. L'unico dato geo esistente è il mondo 42 del registro
(run 2: `rapporto_mediana` 1,79 sui dati committati a 3 decimali; Google 1,11, LinkedIn 1,24;
Meta 3,02, Indeed 2,21, Jooble 1,33 — dossier §7.1).

Lo scopo è **impedire di scegliere l'interpretazione dopo aver visto i numeri**: dato il CSV,
il ramo si calcola, non si sceglie.

---

## 1. Domanda

Il capitolo 6 dice che **l'esperimento geografico identifica ciò che tocca**: i due canali
trattati (Google Ads, LinkedIn Ads) tornano vicini al vero e con forbice stretta, gli altri no.
È vero su otto mondi, o solo sul mondo 42?

## 2. Disegno

Otto mondi, semi `42, 101, 102, 103, 104, 105, 106, 107`, generati con
`genera_dati_simulati.py --seed-mondo N --geo` (patch G2, default): per ogni canale trattato,
6 regioni e due blocchi da 8 settimane (uno per anno) estratti da un rng dedicato
(`seed + 77`); nelle celle trattate la spesa è **spenta** e ridistribuita sulle altre regioni
della stessa settimana. **La spesa nazionale settimanale del canale è quella del mondo base;
cambia solo dove viene spesa.** I cinque canali non trattati sono identici al mondo base in
spesa, impressioni e clic. Il runner: `--disegno geo` (R5), nessun parametro.

Regioni e blocchi sono **determinati dal seme** e quindi già noti, prima di ogni fit:

| Mondo | Google Ads: regioni | blocchi (settimane 1-based) | dose | LinkedIn Ads: regioni | blocchi | dose |
|---|---|---|---:|---|---|---:|
| 42 | Trentino-Alto Adige, Puglia, Molise, Toscana, Lazio, Sardegna | 2–9 e 87–94 | 27,6% | Piemonte, Abruzzo, Campania, Molise, Lombardia, Veneto | 28–35 e 61–68 | 44,6% |
| 101 | Veneto, Puglia, Valle d'Aosta, Lombardia, Abruzzo, Calabria | 27–34 e 94–101 | 37,2% | Puglia, Umbria, Veneto, Trentino-Alto Adige, Calabria, Lazio | 25–32 e 63–70 | 30,9% |
| 102 | Toscana, Valle d'Aosta, Veneto, Trentino-Alto Adige, Sicilia, Calabria | 7–14 e 78–85 | 27,7% | Lombardia, Sicilia, Emilia-Romagna, Liguria, Toscana, Molise | 20–27 e 79–86 | 41,9% |
| 103 | Trentino-Alto Adige, Puglia, Campania, Liguria, Marche, Piemonte | 24–31 e 68–75 | 30,2% | Veneto, Friuli-Venezia Giulia, Valle d'Aosta, Trentino-Alto Adige, Emilia-Romagna, Sardegna | 17–24 e 71–78 | 22,5% |
| 104 | Puglia, Molise, Valle d'Aosta, Toscana, Lombardia, Umbria | 24–31 e 68–75 | 31,9% | Trentino-Alto Adige, Lazio, Valle d'Aosta, Umbria, Piemonte, Liguria | 21–28 e 72–79 | 22,9% |
| 105 | Basilicata, Piemonte, Abruzzo, Marche, Calabria, Friuli-Venezia Giulia | 13–20 e 68–75 | 17,9% | Emilia-Romagna, Trentino-Alto Adige, Umbria, Lombardia, Puglia, Sardegna | 42–49 e 86–93 | 37,0% |
| 106 | Emilia-Romagna, Umbria, Trentino-Alto Adige, Toscana, Sicilia, Sardegna | 33–40 e 54–61 | 27,8% | Valle d'Aosta, Puglia, Friuli-Venezia Giulia, Calabria, Lazio, Campania | 14–21 e 94–101 | 31,2% |
| 107 | Friuli-Venezia Giulia, Lazio, Umbria, Abruzzo, Molise, Trentino-Alto Adige | 11–18 e 87–94 | 17,6% | Lombardia, Sicilia, Calabria, Lazio, Friuli-Venezia Giulia, Emilia-Romagna | 17–24 e 53–60 | 47,5% |

La dose (quota di popolazione trattata) **varia col mondo** (Google 17,6–37,2%, LinkedIn
22,5–47,5%): è riportata per canale e mondo nel CSV (`dose_pct`) e si legge accanto ai
conteggi; **non** si usa per escludere o ripesare mondi.

**Verificato prima di scrivere questo documento:**

| Controllo | Esito |
|---|---|
| `--geo` con i default contro `dati_simulati/geo` committato | **byte-identico**: 14 file su 16 identici, `stagionalita.csv` e `contributo_vero_geo.csv` uguali a meno del formato (4 decimali) |
| Impronta della spesa, mondo 42, ingestion vera del notebook | `a7d6a9e15487`, quella del run 2 del registro |
| Canali non trattati (mondi 42 e 101) | identici al mondo base in spesa, impressioni e clic (5 su 5) |
| Spesa nazionale settimanale dei trattati | conservata (scarto massimo 0,07 EUR, arrotondamento al centesimo) |
| Verità per canale | quella del mondo base (scarto relativo < 4·10⁻⁶) |
| Celle trattate | nessuna riga nei file media (96 per canale), come nel committato |
| Percorso senza flag | base, sanità, pause2, casuale2 invariati (cancello di fedeltà, 8 casi) |

**Mondo 42 = collaudo, non misura nuova.** Il registro ha 1,79 sui dati committati (3
decimali); qui i dati sono rigenerati a 4 decimali, quindi l'atteso è **1,79 spostato di
−1 … −1,7%** (come base e sanità: 2,26 → 2,2348, 0,69 → 0,6786), cioè **1,76–1,78**;
oltre il ±2% da 1,79 è un'anomalia della pipeline e il disegno non si interpreta finché non
è spiegata. I diagnostici 22 e 23 del registro misurano lo stesso effetto su base e sanità.

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
| 1 | `C_Google >= 6` e `C_LinkedIn >= 6` | **IDENTIFICA CIÒ CHE TOCCA**, su otto mondi: la frase del cap. 6 regge |
| 2 | esattamente uno dei due `>= 6` | **IDENTIFICA UNO SOLO**: dichiarare quale (se succede, l'atteso è Google, il dominante con il 34,7% della spesa); la frase va ristretta a quel canale |
| 3 | entrambi `< 6` | **NON IDENTIFICA NEMMENO I TRATTATI**: la frase del cap. 6 cade e va riscritta |

## 5-bis. Si riportano sempre, non selezionano il ramo

- **`C_tot`**, attesa dichiarata **0–2 su 8**: il geo non aggiusta il totale (nel mondo 42 la
  forbice del totale, 1,13–2,46, non conteneva il vero). Va scritto così nel cap. 6: "dimezza
  l'incertezza" vale per i canali trattati, mai per il totale.
- **Non trattati**: mediana sugli 8 mondi del rapporto stima/vero di **Meta Ads** (mondo 42:
  3,02), attesa **> 2**; `C_Meta`, attesa **≤ 2**.
- **Danno collaterale** sui non trattati: per **Indeed** e **Jooble**, mediana sugli 8 mondi
  di `larghezza_relativa(geo) / larghezza_relativa(osservativo, stesso mondo)`, attesa
  **≥ 1** (mondo 42, in multipli del vero: Indeed 2,09 → 5,16, Jooble 3,21 → 4,35). Il
  denominatore viene da `copertura_risultati_canali.csv` dello studio osservativo (§10.4).
- **Larghezza dei trattati**: mediana sugli 8 mondi di `larghezza_relativa` di Google e di
  LinkedIn, e la loro relazione con `dose_pct` (Spearman su 8 punti, solo riportato).
- Le otto `rapporto_mediana` e i PIT, per mondo.

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

1. `griglia_D1_geo.csv` (43 colonne: le 35 dello studio di copertura + `decimali_stagionalita`,
   `prior_tipo`, `prior_sigma` + `disegno`, `canali_trattati`, `parametri_disegno` + `prior_mu`,
   `prior_mu_per_canale`),
   `griglia_D1_geo_canali.csv` (19 colonne), `griglia_D1_geo_draw/` (un `.csv.gz` per mondo,
   `totale` sommato dentro il draw), `griglia_D1_geo_verifiche.csv` (il controllo per riga).
2. La tabella per mondo: `rapporto_mediana`, forbice, PIT, ammissibilità, e per ogni canale
   `dentro`, `larghezza_relativa`, `dose_pct`, `riduzione_effettiva_pct`.
3. I conteggi del §5 e le grandezze del §5-bis, ciascuno su tutti i mondi e sui soli
   ammissibili, con N.
4. Questo documento, **con la sua data**, committato prima del run e separato dai risultati.
5. Se il ramo è quello sfavorevole, lo si dichiara **nella prima riga** della consegna.

## 9. Provenienza

- Generatore: `genera_dati_simulati.py` di `main` + patch A (`--seed-mondo`, 4 decimali,
  `--sanita`) + **G2** (`--geo`, parametrico; i default riproducono il committato). **Cancello di fedeltà superato prima di scrivere questo documento**:
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
4. Per il danno collaterale (§5-bis) serve `copertura_risultati_canali.csv` dello studio
   osservativo per gli otto mondi (Drive `MMM_copertura`). Se non esiste, la grandezza si
   calcola **solo sul mondo 42** contro `registro_run_canali.csv` (run `base_96_rif_s42`) e
   lo si dichiara; non si rifà lo studio osservativo.

**Il run non parte prima di questi controlli.**

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
