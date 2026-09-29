# Pre-registrazione — D7: esperimento geografico su Google Ads a metà dose (3 regioni), otto mondi

**Versione 1, 15 settembre 2026.** Scritta PRIMA di qualunque fit del disegno. Nessun run a
3 regioni esiste: il mondo 42 è la prima misura, e va detto. D7 è **essenziale**, non
facoltativo: è il controllo a dose comparabile del calendario (D2), che lo cita, e si esegue
**prima** di D2.

---

## 1. Domanda

Quanto esperimento serve? Con metà delle regioni (3 invece di 6, stessi blocchi) il canale
trattato resta identificato? E, a dose comparabile, il calendario (D2) identifica Google
peggio, uguale o meglio del geo su un canale solo?

## 2. Disegno

Otto mondi, stessi semi. `genera_dati_simulati.py --seed-mondo N --geo --geo-canali "Google Ads"
--geo-regioni 3`; runner `--disegno geo --parametri-disegno "canali=Google Ads;regioni=3"`.
Solo Google Ads è trattato. **Le 3 regioni sono le prime 3 delle 6 di D1 dello stesso mondo, e
i blocchi sono gli stessi di D1** (patch G2: con meno di 6 regioni si estraggono comunque le 6
del canonico e si tengono le prime n): fra D1 e D7, nello stesso mondo, **cambia solo la
dose**. LinkedIn Ads qui non è trattato (in D1 sì).

| Mondo | Regioni trattate (Google Ads) | Blocchi 1-based | Dose D7 | Dose D1 (6 regioni) |
|---|---|---|---:|---:|
| 42 | Trentino-Alto Adige, Puglia, Molise | 2–9 e 87–94 | 8,9% | 27,6% |
| 101 | Veneto, Puglia, Valle d'Aosta | 27–34 e 94–101 | 15,1% | 37,2% |
| 102 | Toscana, Valle d'Aosta, Veneto | 7–14 e 78–85 | 14,7% | 27,7% |
| 103 | Trentino-Alto Adige, Puglia, Campania | 24–31 e 68–75 | 18,0% | 30,2% |
| 104 | Puglia, Molise, Valle d'Aosta | 24–31 e 68–75 | 7,3% | 31,9% |
| 105 | Basilicata, Piemonte, Abruzzo | 13–20 e 68–75 | 10,2% | 17,9% |
| 106 | Emilia-Romagna, Umbria, Trentino-Alto Adige | 33–40 e 54–61 | 10,7% | 27,8% |
| 107 | Friuli-Venezia Giulia, Lazio, Umbria | 11–18 e 87–94 | 13,2% | 17,6% |

Dose mediana D7: **12,0%** (7,3–18,0%); dose di Google nel calendario D2: mediana **14,0%**
(11,7–21,1%, §2 di D2). "Dose comparabile" significa questo, e le due dosi per mondo si
riportano affiancate; non si ripesano i mondi.

**Verificato prima di scrivere** (mondi 42 e 101): regioni = prime 3 di D1 e blocchi identici
a D1; canali non trattati identici al mondo base (6 su 6); spesa nazionale settimanale
conservata (scarto massimo 0,09 EUR); verità per canale = mondo base; 48 celle trattate senza
righe.

**Mondo 42 = collaudo di configurazione**, non di numero: si controllano colonne di
configurazione, impronta registrata, ammissibilità; il numero è la prima misura e non ha
atteso.

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

**Sul canale trattato**, `C_Google` su 8 mondi:

| # | Condizione | Ramo |
|---|---|---|
| 1 | `C_Google >= 6` | **METÀ DOSE BASTA**: 3 regioni identificano Google |
| 2 | `C_Google <= 5` | **METÀ DOSE NON BASTA**: si dichiara, con la dose per mondo accanto |

**Confronto con D1 nello stesso mondo** (la dose è l'unica differenza):
`W7` = mondi in cui `larghezza_relativa(Google, D7) <= larghezza_relativa(Google, D1)`.
Impegno pre-registrato: **`M_D1 <= M_D7`** (mediana su 8 mondi della larghezza relativa di
Google), cioè più dose = forbice non più larga. `W7 <= 2` lo conferma; `W7 >= 6` lo smentisce
(dichiararlo: la dose non è ciò che restringe la forbice); 3–5 non conclusivo.

## 5-bis. Si riportano sempre, non selezionano il ramo

- `C_tot` (attesa 0–2, come D1); `rapporto_mediana` di Google per mondo (D1 mondo 42: 1,11).
- **Danno collaterale** (mediana sui 6 non trattati di `larghezza_relativa(D7) /
  larghezza_relativa(D1)`, stesso mondo): non ha predizione; si riporta.
- Il ruolo di D7 nel confronto con D2 (`W2`) è definito nella pre-registrazione di D2; qui si
  producono solo i numeri.
- Il ruolo di D7 nell'ordinamento dose-risposta (`M_D1 <= min(M_D6, M_D7)`, D6 contro D7
  aperto) è definito nella pre-registrazione di D6/D8.

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

1. `griglia_D7_geo_google_3regioni.csv` (43 colonne: le 35 dello studio di copertura + `decimali_stagionalita`,
   `prior_tipo`, `prior_sigma` + `disegno`, `canali_trattati`, `parametri_disegno` + `prior_mu`,
   `prior_mu_per_canale`),
   `griglia_D7_geo_google_3regioni_canali.csv` (19 colonne), `griglia_D7_geo_google_3regioni_draw/` (un `.csv.gz` per mondo,
   `totale` sommato dentro il draw), `griglia_D7_geo_google_3regioni_verifiche.csv` (il controllo per riga).
2. La tabella per mondo: `rapporto_mediana`, forbice, PIT, ammissibilità, e per ogni canale
   `dentro`, `larghezza_relativa`, `dose_pct`, `riduzione_effettiva_pct`.
3. I conteggi del §5 e le grandezze del §5-bis, ciascuno su tutti i mondi e sui soli
   ammissibili, con N.
4. Questo documento, **con la sua data**, committato prima del run e separato dai risultati.
5. Se il ramo è quello sfavorevole, lo si dichiara **nella prima riga** della consegna.

## 9. Provenienza

- Generatore: `genera_dati_simulati.py` di `main` + patch A (`--seed-mondo`, 4 decimali,
  `--sanita`) + **G2** (`--geo-canali`, `--geo-regioni`: regioni nidificate nelle 6 del canonico). **Cancello di fedeltà superato prima di scrivere questo documento**:
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
4. D1 deve essere completo sugli otto mondi (o su N dichiarati) prima di leggere `W7`; D7 si
   esegue **prima di D2**.

**Il run non parte prima di questi controlli.**

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
