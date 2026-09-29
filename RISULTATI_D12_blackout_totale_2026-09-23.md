# D12 — blackout totale geografico: risultati

**Ramo 2 — RECUPERO PARZIALE: si riporta, non si raccomanda senza il conto del costo.** `E`
mediano **+5,38** punti, dentro la fascia 4,0–6,0. `C_tot` 4/8. La previsione dichiarata (ramo 1,
con `E` fra 3 e 4) è **smentita**.

Il ramo 3, quello che la pre-registrazione indicava come smentita piena, non è scattato. D12 è finito
nel caso che il §5 aveva scritto prima dei numeri come punto debole della previsione, con la sua
lettura già fissata: **«il recupero c'è ma non basta, e va pesato contro il costo del §6»**. Non si
legge come «ha quasi funzionato» (§7, punto 5).

Il ramo l'ha stampato `analisi_D12_D13.py` dai CSV del run, conservati in `griglia_D12/` identici al
byte allo zip scaricato da Drive (`MMM_griglia_D12-20260921T175905Z-1-001.zip`, sha256
`b963dd46fc9d706b…`).

---

## Il costo, accanto al ramo (§6)

Il disegno spegne tutti e sette i canali in cinque regioni per due blocchi di otto settimane, e la
spesa tolta **non viene ridistribuita**. Le candidature perse sono vere. La tabella è quella
calcolata sui mondi prima dei fit; la colonna `candidature_vere_perse` del CSV del run la riproduce
alla prima cifra decimale (101: 5.407,0 contro 5.406,9, arrotondamento).

| Mondo | Spesa tolta (EUR) | Spesa tolta | Candidature vere perse |
|---|---:|---:|---:|
| 42 | 125.463,37 | −3,42% | 5.339,0 |
| 101 | 118.463,42 | −3,25% | 5.406,9 |
| 102 | 114.432,75 | −3,24% | 5.430,2 |
| 103 | 131.606,00 | −3,46% | 4.977,7 |
| 104 | 120.618,05 | −3,30% | 5.032,3 |
| 105 | 139.084,37 | −3,72% | 5.831,1 |
| 106 | 119.789,71 | −3,19% | 4.841,1 |
| 107 | 140.428,43 | −3,71% | 5.841,6 |

Mediana: **5.373 candidature vere perse per mondo**, fra 4.841 e 5.842. Sul mondo 42 sono il 3,4% del
contributo incrementale del biennio. In cambio `E` scende da +22,9 (D0) a +5,4. È 1,8 punti meno del
calendario a rotazione D2 (+7,2), che secondo la pre-registrazione (§5) muove la distribuzione della
spesa ma ne lascia intatto il livello.

---

## Per mondo

`E` = quota stimata − quota vera **di quel mondo**, in punti (§3; §7, punto 4).

| Mondo | Quota vera | Quota stimata | `E` | Rapporto | Forbice 5%–95% | PIT | Copre |
|---|---:|---:|---:|---:|---|---:|:---:|
| 42 | 17,99% | 22,38% | +4,39 | 1,2366 | 0,9973–1,5142 | 0,0515 | sì |
| 101 | 17,98% | 28,34% | +10,36 | 1,5679 | 1,2840–1,8874 | 0,0005 | no |
| 102 | 17,97% | 24,25% | +6,28 | 1,3444 | 1,0867–1,6328 | 0,0124 | no |
| 103 | 18,06% | 20,84% | +2,78 | 1,1449 | 0,9033–1,4350 | 0,1696 | sì |
| 104 | 18,09% | 23,84% | +5,75 | 1,3121 | 1,0628–1,5931 | 0,0168 | no |
| 105 | 17,96% | 24,33% | +6,37 | 1,3473 | 1,0995–1,6354 | 0,0086 | no |
| 106 | 18,12% | 20,56% | +2,44 | 1,1301 | 0,8723–1,4288 | 0,2208 | sì |
| 107 | 17,91% | 22,91% | +5,00 | 1,2649 | 0,9883–1,6225 | 0,0596 | sì |

`E` mediano +5,38 (fra +2,44 e +10,36) · rapporto mediano **1,29** · PIT mediano 0,0341 · `C_tot`
**4/8**.

**Quale quota vera.** La quota vera del CSV è la stessa definizione della griglia: somma del
contributo vero diviso somma del KPI **osservato** di quel mondo, lo stesso denominatore della quota
stimata. La tabella della quota vera al §8 della pre-registrazione (17,9884 … 17,9399) è calcolata sul
**valore atteso** del KPI, e la sua didascalia non lo dice. Le due differiscono al massimo di 0,08
punti (mondo 106: 18,12 contro 18,0364). Con la tabella del §8 al posto del CSV, `E` mediano sarebbe
+5,40: **stesso ramo**. La pre-registrazione non è stata modificata; la precisazione sta qui.

---

## Confronto a parità di tutto il resto

Tutti i valori sono ricalcolati dai CSV della griglia sugli stessi otto mondi.

| Disegno | `E` mediano | `C_tot` | Rapporto mediano | Spesa |
|---|---:|:---:|---:|---|
| D0 osservativo | +22,92 | 0/8 | 2,22 | — |
| D2 calendario a rotazione | +7,18 | 4/8 | 1,38 | non tolta |
| D10 calendario a 4 giri | +8,28 | 2/8 | 1,44 | non tolta |
| **D12 blackout totale** | **+5,38** | **4/8** | **1,29** | **tolta, −3,2% / −3,7%** |

---

## Per canale

`C_k` = mondi su otto in cui l'intervallo al 90% del canale contiene il vero. Larghezza = larghezza
relativa mediana dell'intervallo.

| Canale | ROI vero (mediano) | Stimato / vero (mediano) | `C_k` | Larghezza |
|---|---:|---:|:---:|---:|
| Subito Lavoro | 2,70 | 0,48 | 8/8 | 3,88 |
| Indeed | 2,67 | 0,53 | 8/8 | 2,96 |
| Jooble | 2,54 | 0,50 | 8/8 | 4,18 |
| Altre job board | 2,44 | 0,52 | 8/8 | 4,06 |
| Meta Ads | 1,66 | 0,86 | 8/8 | 2,63 |
| Google Ads | 1,45 | 2,06 | 7/8 | 1,41 |
| LinkedIn Ads | 0,84 | 1,44 | 8/8 | 3,21 |

`rho` di Spearman mediano fra ordine stimato e ordine vero: **−0,05** (`griglia_conteggi.csv`). Il
blackout riduce l'eccesso sul totale ma non rimette in ordine i canali.

---

## La corsa fra le due diagnosi (§4-bis)

La regola fissata prima era questa: la collinearità vince per eliminazione solo se D12 dà il ramo 3
**e** D13 il ramo 4; l'ipotesi organica regge se almeno uno dei due dà il ramo buono (D12 ramo 1, D13
ramo 1 o 2).

**D12 al ramo 2 non decide la corsa**: non è il ramo peggiore e non è quello buono. D13 non ha un
ramo calcolabile (vedi il suo file). **La corsa resta aperta**, e per il §7 (punto 8) non si dichiara
un vincitore sulla base di D12 da solo.

---

## Ammissibilità e diagnostica

- **8 run ammissibili su 8.** R-hat massimo 1,004, ESS minimo 1.263 (su `beta_m`, mondo 42).
- Divergenze sopra l'1%, segnalate come chiede l'Appendice A: mondo 42 **1,90%** (152), mondo 102
  **2,91%** (233). Gli altri stanno fra 0 e 0,61%. Da sole non squalificano.
- Durata di un fit fra 10,0 e 15,6 minuti.
- Le impronte dei dati sono state verificate dal pre-volo sul contenuto normalizzato a LF, come
  dice l'emendamento. Se non fossero tornate, il pre-volo non avrebbe fatto partire i fit.

**Vale a `beta` ed `ec` fissi** (§7, punto 7): la superficie di risposta è quella del mondo base, e
la spesa tolta non la sposta.

---

## Le ore

| Che cosa | Quando (CEST) | Fonte |
|---|---|---|
| Pre-registrazione | 21/9, 17:37:11 | commit `4cdaf72` |
| Testo dell'emendamento scritto su Drive dal pre-volo | 21/9, 18:17:52 | data del file su Drive |
| Commit dell'emendamento | 21/9, 18:22:03 | commit `85b4dc2` |
| Fine del primo fit (mondo 42) | 21/9, 18:35:54 | colonna `quando` (in UTC nel file) |
| Fine dell'ultimo fit (mondo 107) | 21/9, 19:58:18 | colonna `quando` |

**La pre-registrazione precede tutti i fit.** L'emendamento, che cambia solo il modo di calcolare
le impronte e nessuna soglia, era nel notebook e su Drive alle 18:17:52. Il commit è arrivato alle
18:22:03. Il primo fit è finito alle 18:35:54 ed è durato 15,6 minuti, quindi è partito verso le
18:20, **circa due minuti prima del commit dell'emendamento**. La stima dell'ora di partenza è
dedotta dalla durata e non è registrata nel file. Il testo su Drive è identico a quello di
`85b4dc2` (sha256 LF `3bc4c9a18b8e4bbf`); la versione precedente archiviata dal notebook è identica a
quella di `4cdaf72` (`700d5e75c04a3e49`).

---

## Righe per l'Appendice A

Tabella A.2 (i disegni):

| D12 blackout totale | tutti e sette i canali spenti in 5 regioni su 20 (una per strato di popolazione, 23,4% della popolazione), due blocchi di 8 settimane; spesa tolta e non ridistribuita; `beta` ed `ec` fissi al mondo base | 8 |

Tabella A.3 (registro dei run):

| D12 blackout totale | 8 | 1,29 | +5,4 | 4/8 | 0,04% | 1.990 |

**Per il testo dell'appendice.**
- La didascalia della Tabella A.3 dice «contro un valore vero del 18,5%». Per D12 il valore vero è
  quello di ciascun mondo, fra 17,91% e 18,12%, perché `beta` è fisso al mondo base.
- Il totale «96 esecuzioni» della didascalia della Tabella A.2 va aggiornato.

---

*File dei risultati, scritto il 23 settembre 2026 dopo che il ramo era stato stampato. Ogni cifra
viene dai CSV in `griglia_D12/`, dalla pre-registrazione o dai CSV della griglia citati.*
