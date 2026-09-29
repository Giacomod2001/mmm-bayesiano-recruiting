# Pre-registrazione — D10: calendario a quattro giri, otto mondi

**Versione 1, 17 settembre 2026.** Scritta PRIMA di generare i mondi col disegno a quattro giri
e prima di qualunque fit. Nessun calendario a più di due giri è mai stato eseguito.

D10 esiste per rispondere a una domanda che la griglia ha aperto e non ha chiuso: il calendario
a rotazione (D2) è il disegno che si avvicina di più al vero — `C_tot` 4 su 8, eccesso di quota
media 7,2 punti contro i 22,9 dell'osservativo — **ma non arriva**. Restano 7 punti. Questa
pre-registrazione fissa prima come si legge il perché.

---

## 1. Domanda

I 7 punti che restano dopo il calendario sono **poca dose** o **la baseline**?

Il calendario tratta tutti e sette i canali, ma in gruppi disgiunti di regioni: ogni canale ne
riceve solo il 12-21%, metà della dose del geo canonico, e per sole 16 settimane su 104. Se il
limite è questo, raddoppiare i giri deve spostare il numero. Se invece i 7 punti sono errore
sulla domanda organica — che i media non toccano e che nessun esperimento sui media può
identificare — il numero non si muove, e il capitolo 7 deve dirlo.

## 2. Disegno

Otto mondi, stessi semi `42, 101, …, 107`, stessa rotazione di D2 (il mondo in posizione i usa
`rotazione = i mod 7`). `genera_dati_simulati.py --seed-mondo N --calendario
--calendario-rotazione i --calendario-giri 4` (patch G4); runner `--disegno calendario
--parametri-disegno "rotazione=i;giri=4"` (patch R7).

**Rispetto a D2 cambia UNA COSA SOLA: il numero di giri, da 2 a 4.** Stessi gruppi di regioni,
stessa lunghezza del blocco (8 settimane), stesso sfasamento fra canali (7 settimane), stessa
regola di rotazione, stessa meccanica della spesa (spenta nelle celle trattate, ridistribuita
nella stessa settimana, spesa nazionale conservata). È deliberato: se il numero si muove, si sa
di cosa è colpa.

Partenze dei giri, 1-based: **9, 24, 39, 54**, più lo sfasamento di 7 per canale. Blocchi:

| canale | blocchi (settimane 1-based) |
|---|---|
| Google Ads | 9–16 · 24–31 · 39–46 · 54–61 |
| Meta Ads | 16–23 · 31–38 · 46–53 · 61–68 |
| LinkedIn Ads | 23–30 · 38–45 · 53–60 · 68–75 |
| Indeed | 30–37 · 45–52 · 60–67 · 75–82 |
| Subito Lavoro | 37–44 · 52–59 · 67–74 · 82–89 |
| Jooble | 44–51 · 59–66 · 74–81 · 89–96 |
| Altre job board | 51–58 · 66–73 · 81–88 · 96–103 |

**32 settimane spente per canale** invece di 16, **quattro transizioni** invece di due, **7
settimane di pausa** fra un blocco e il successivo dello stesso canale. Le prime 8 settimane
restano libere (l'adstock si spegne prima di cominciare) e l'ultimo blocco chiude alla 103 su 104.

**Perché quattro e non di più.** Con cinque giri la pausa scende a 3 settimane e l'adstock non si
spegne: la misura del "dopo" sarebbe sporca di prima. Con sei i blocchi si toccano e il disegno
degenera in **un unico blackout da 48 settimane** — una sola transizione, che è il disegno
peggiore, non il migliore: assomiglia a "in quella regione si spende meno", cioè al
confondimento osservazionale da cui l'esperimento deve uscire. Quattro giri è il massimo che
tiene la pausa dell'adstock. Dichiarato adesso perché non lo si rialzi dopo aver visto i numeri.

**Verificato prima di scrivere questo documento** (mondo 42, rotazione 0):

| Controllo | Esito |
|---|---|
| G4 con `giri=2` contro il generatore senza G4 | **bit-identico**, 16 file su 16 |
| Percorso senza `--calendario` | invariato: G4 tocca solo il ramo del calendario |
| Spesa nazionale per canale, 4 giri contro 2 | conservata, scarto massimo **0,0003%** (arrotondamento) |
| Piano dei blocchi | come in tabella; ultimo blocco alla settimana 103 di 104 |
| Dose di popolazione per canale | identica a D2 (Google 21,1%, gli altri 11,7–14,1%) |
| Impronta del generatore con G4 | `c57be0b1e94c0bbd` (senza G4 era `f4f243a6d62b7f16`) |
| R7 con la sola `rotazione=i` | produce il comando di D2 invariato |

**Nessun atteso sul numero: è la prima misura.** Il mondo 42 serve da collaudo di
configurazione, non di valore.

## 3. Configurazione del fit — identica a tutta la griglia

| Parametro | Valore | Da dove |
|---|---|---|
| `KNOTS_PER_QUARTER` | 12 → **96 nodi** | `--knots-per-quarter 12` |
| `N_KEEP` | **2000** | `--keep 2000` |
| Catene / adapt / burnin | 4 / 500 / 500 | default del runner |
| Seme MCMC | **42** per tutti i mondi | il mondo varia col SUO seme |
| `revenue_per_kpi` | **40,0** EUR | guardia del runner |
| Prior | `ROI ~ LogNormal(0,2; 0,9)`, di riferimento | `--prior riferimento` |
| Dati | mondi rigenerati, `stagionalita.csv` a 4 decimali | `decimali_stagionalita = 4` |

Una sola differenza da questa tabella annulla il confronto con D2 e con il resto della griglia.

## 4. Metriche — dal runner, mai a posteriori

Le stesse di tutta la griglia: intervallo esatto del totale (somma dei sette canali **dentro ogni
draw**, poi quantili 5% e 95%), **PIT** = `media(totale_draw <= vero)`, `rapporto_mediana` =
mediana / vero, e per canale `dentro`, `larghezza_relativa`, `roi_vero`, `roi_stimato`,
`rho_spearman`, `dose_pct`, `riduzione_effettiva_pct`.

In più, la grandezza su cui si legge il ramo:

```
E = mediana sugli N mondi di (quota_media_stimata_pct - quota_media_vera_pct)
C_tot = mondi con 0,05 <= PIT <= 0,95
```

`E` è l'eccesso di attribuzione ai media in punti percentuali. Riferimenti già misurati:
osservativo **22,9**, geo a 3 regioni **19,4**, geo canonico **15,5**, **D2 calendario 7,2**.

**Verità.** Letta solo da `<mondo>/verita/contributo_vero.csv`, quella di quel mondo.
**Dichiarato adesso:** la verità di D10 **non** coincide con quella di D2 — misurata sul mondo 42,
differisce dello **0,61%**. Non è un errore: muovere più spesa fra regioni passa per la curva di
risposta, che non è lineare. Ogni mondo è misurato contro la propria verità, quindi fra D2 e D10
si confrontano **rapporti stima/vero, mai livelli**. In D1 lo scarto era sotto 4·10⁻⁶ perché il geo
muoveva due canali; qui se ne muovono sette, quattro volte.

## 5. Regola di decisione — deterministica, prima riga che corrisponde

| # | Condizione | Ramo |
|---|---|---|
| 1 | `C_tot >= 6` | **ERA LA DOSE**: più giri chiudono il divario. Il cap. 7 raccomanda il calendario a quattro giri, non a due |
| 2 | `C_tot <= 4` **e** `E >= 6,0` | **IL LIMITE È LA BASELINE**: raddoppiare l'esperimento non sposta né copertura né errore. Nessun disegno sui media supera quel muro, e va scritto nei limiti del cap. 7 |
| 3 | tutto il resto (`C_tot = 5`, oppure `C_tot <= 4` con `E < 6,0`) | **MIGLIORA MA NON CHIUDE**: si dichiara di quanto, con `C_tot` ed `E` accanto, e non si generalizza |

**Attesa dichiarata, che NON seleziona il ramo:** se il vincolo fosse la dose nel tempo,
raddoppiare i giri dovrebbe portare `E` verso i 4 punti. Se il vincolo è la baseline, `E` resta
intorno a 7. È una previsione, ed è lì per poter essere smentita.

## 6. Cosa NON è ammesso dopo aver visto i risultati

1. Cambiare le soglie (`C_tot` 6 e 4, `E` 6,0) o i confini dei rami, o aggiungere rami.
2. Alzare il numero di giri oltre quattro perché quattro non è bastato: cinque e sei sono già
   esclusi al §2, con la ragione, prima di guardare.
3. Escludere un mondo per ragioni non computazionali (§7); sostituire un seme fallito.
4. Cambiare nodi, keep, prior, campionatore o dati e ripresentare il run come questo.
5. Confrontare D10 con D2 sui livelli invece che sui rapporti (§4).
6. Interpretare prima che questa pre-registrazione sia approvata e committata.

## 7. Mondi che falliscono e criterio di ammissibilità (cap. 4.7)

Un mondo che si interrompe per errore tecnico viene **rilanciato una volta con lo stesso seme**.
Se fallisce di nuovo resta con `esito = errore`, i conteggi sono su N mondi e **N va dichiarato**.
Un seme fallito non viene mai sostituito.

Ammissibilità: **R-hat ≤ 1,1 ed ESS ≥ 100 su `roi_m` e `beta_m`**. Chi non passa è
`non_ammissibile`: si riporta col suo numero, non si rifà. Le divergenze si riportano sempre e non
squalificano da sole. Ogni cifra si dà **due volte**, su tutti i mondi arrivati in fondo e sui soli
ammissibili; **il ramo si calcola sulla prima**.

Con N < 8 la soglia del ramo 1 diventa l'arrotondamento di 6/8 · N (0,5 verso l'alto) e la soglia
del ramo 2 quella di 4/8 · N; N va dichiarato accanto a ogni cifra.

## 8. Cosa viene consegnato

1. `griglia_D10_calendario_4giri.csv` (43 colonne), `_canali.csv` (19 colonne), `_draw/` (un
   `.csv.gz` per mondo, `totale` sommato dentro il draw), `_verifiche.csv`.
2. La tabella per mondo: `rapporto_mediana`, forbice, PIT, `E`, ammissibilità, e per ogni canale
   `dentro`, `larghezza_relativa`, `dose_pct`.
3. `C_tot` ed `E` su tutti i mondi e sui soli ammissibili, con N; accanto le stesse due cifre di
   D2, per il confronto dichiarato al §4.
4. Questo documento, **con la sua data**, committato prima del run e separato dai risultati.
5. Se il ramo è il 2 — cioè se raddoppiare l'esperimento non serve — lo si dichiara **nella prima
   riga** della consegna.

## 9. Provenienza

- Generatore: `genera_dati_simulati.py` di `main` del repo pubblico + patch A + G1 + G2 + G3 +
  **G4** (`--calendario-giri`, sette sostituzioni). Impronta **`c57be0b1e94c0bbd`**. G4 con
  `giri=2` riproduce il calendario precedente **bit per bit** (16 file su 16, verificato); la
  guardia su `n_blocchi` è stata spostata dopo il ramo del piano fisso, dove il geo — l'unico
  disegno che estrae i blocchi a sorte — la incontra esattamente dov'era.
- Runner: `studio_copertura_runner.py` + B1–B4 + R5 + R6 + **R7** (`giri` fra i parametri del
  calendario). Con la sola `rotazione=i` il comando è quello di D2, invariato.
- Notebook: `colab_griglia_D10.ipynb`, **separato** da `colab_griglia.ipynb`, che resta come
  committato: è la provenienza che il §9 delle altre nove pre-registrazioni cita, e non si tocca.

## 10. Precondizioni prima di lanciare

1. **D2 deve essere completo sugli otto mondi con esito `ok`** (lo è: 8 su 8, `C_tot` 4, `E` 7,2):
   è il termine di paragone, e senza di esso il §5 non si calcola.
2. Il pre-volo deve superare il cancello di fedeltà sul mondo 42 con il generatore che porta G4
   (impronte `b3215553829a`, `8b172390e2b2`, `a7d6a9e15487`, `ba045e89147d`, `4714c42e463b`):
   se una sola non torna, il disegno non parte.
3. Questa pre-registrazione è approvata dall'autore e committata **prima** del primo fit; il file
   dei risultati è committato dopo, separatamente.
4. I semi vanno verificati contro `copertura_risultati.csv`, non contro la memoria.

**Il run non parte prima di questi controlli.**

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
