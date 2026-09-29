# N1 — Meridian con meno nodi della baseline, otto mondi: risultati

**Livello: ramo 2 — MENO NODI, MENO SOVRASTIMA: la baseline flessibile gonfia i media.** A 1 nodo
per trimestre, `E` scende rispetto a D0 in **tutti gli otto mondi**, con `ΔE` mediano **−7,92** punti.
La previsione dichiarata (ramo 1) è **smentita**, ed è esattamente il caso che il §7.3 indicava come
smentita.

**Ordine: ramo C — ANCHE CON LA BASELINE RIGIDA L'ORDINE NON SI DISTINGUE DAL CASO.** `rho` mediano
a 1 nodo per trimestre **0,000**, contro +0,6071 della regola «spesa inversa» e +0,2321 del caso. La
previsione dichiarata (ramo C) è **confermata**.

I rami li ha stampati `analisi_N1_nodi.py`, committato con la pre-registrazione in `5f1c234`, dai
CSV del run, conservati in `griglia_N1/` identici al byte allo zip scaricato da Drive
(`MMM_griglia_N1-20260923T051238Z-1-001.zip`, sha256 `fb982ae74f4d94f7…`). Lo script, eseguito così
com'è, su Windows si ferma alla terza riga per la codifica della console (il segno meno tipografico);
con `PYTHONIOENCODING=utf-8` gira fino in fondo. Il codice non è stato toccato.

---

## Il cancello di replica

Il primo fit, 12 nodi per trimestre sul mondo 42, riproduce la riga di D0: rapporto 2,2348, PIT
0,000125, impronta dei dati `b3215553829a`, 96 nodi. **Replica riuscita**: i 24 fit dei livelli
nuovi sono partiti dopo.

---

## Le due regole

**Livello** (§5.2): `ΔE_w = E_w(1 nodo/trim.) − E_w(D0)` sugli otto mondi ammissibili, soglia 6 su
8.

| Mondo | 42 | 101 | 102 | 103 | 104 | 105 | 106 | 107 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `ΔE` (punti) | −7,18 | −13,40 | −8,66 | −12,14 | −8,89 | −1,52 | −4,27 | −2,42 |

Mediana **−7,92**, cioè ≤ −5,0. Negativo in **8 mondi su 8**, cioè almeno 6. Riga 2.

**Ordine** (§5.3): `rho` mediano a 1 nodo per trimestre **0,000** (0/56). Non raggiunge +0,6071
(riga A) e non supera +0,2321 (riga B). Riga C.

---

## I quattro livelli

Il livello 12 è D0, letto dal file (§9, punto 7). Tutti i run sono ammissibili, quindi la lettura
sugli ammissibili e quella su tutti coincidono.

| Nodi per trimestre | Nodi | Ammissibili | `E` mediano | `rho` mediano | `C_tot` | Rapporto mediano |
|---:|---:|:---:|---:|---:|:---:|---:|
| 1 | 8 | 8/8 | **+15,59** | 0,000 | 0/8 | 1,81 |
| 3 | 24 | 8/8 | +24,24 | −0,107 | 0/8 | 2,29 |
| 6 | 48 | 8/8 | +23,87 | −0,054 | 0/8 | 2,27 |
| 12 (D0) | 96 | 8/8 | +22,93 | −0,036 | 0/8 | 2,22 |

Riferimenti per `rho`: spesa inversa +0,6071, caso +0,2321. **A nessun livello l'intervallo al 90%
sul totale contiene il vero, in nessun mondo.**

**Mondo per mondo**, `E` in punti e `rho`:

| Mondo | `E` a 1 | `E` a 3 | `E` a 6 | `E` a 12 | `rho` a 1 | `rho` a 3 | `rho` a 6 | `rho` a 12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | +16,14 | +31,68 | +28,81 | +23,32 | −0,250 | −0,714 | −0,714 | −0,821 |
| 101 | +13,88 | +21,89 | +23,42 | +27,28 | +0,393 | 0,000 | −0,214 | +0,321 |
| 102 | +13,87 | +29,82 | +24,31 | +22,53 | +0,429 | +0,464 | +0,357 | +0,214 |
| 103 | +17,36 | +33,98 | +31,81 | +29,50 | −0,214 | +0,143 | +0,143 | +0,036 |
| 104 | +20,02 | +26,58 | +32,75 | +28,91 | +0,179 | −0,214 | +0,036 | −0,107 |
| 105 | +16,87 | +20,53 | +18,09 | +18,39 | +0,143 | +0,143 | +0,179 | +0,107 |
| 106 | +15,03 | +19,27 | +20,64 | +19,30 | −0,143 | −0,286 | −0,500 | −0,107 |
| 107 | +9,42 | +20,26 | +15,21 | +11,84 | −0,286 | −0,429 | −0,143 | −0,357 |

---

## La monotonia nei nodi (§6) — descrittiva, non seleziona rami

**`E` non è monotona in nessun mondo, e nemmeno in mediana.**
- In **tutti gli otto mondi** `E` è più basso a 1 nodo che a qualunque altro livello.
- Sopra 1 nodo l'andamento cambia da mondo a mondo: il massimo è a 3 nodi in cinque mondi (42, 102,
  103, 105, 107), a 6 in due (104, 106), e sul 101 `E` cresce fino a 12.
- In mediana: +15,6 → +24,2 → +23,9 → +22,9.

La regola legge solo il confronto 1 contro 12, e su quello il ramo è netto. Fra 3 e 12 nodi però,
in mediana, l'andamento è l'opposto: meno nodi, un po' più di sovrastima. Le due cose vanno scritte
insieme. «Meno nodi, meno sovrastima» vale per il passaggio alla baseline più rigida provata, non
lungo tutta la scala.

`rho` è monotona solo sul mondo 42, dove sale togliendo nodi, da −0,82 a −0,25. Negli altri sette
mondi e in mediana non lo è.

---

## Il confronto con la Sezione 5.8.1 — l'andamento, non le cifre (§6; §9, punto 5)

Mondo 42, quota attribuita ai media e rapporto con il vero (18,51%):

| Nodi per trimestre | N1 (2.000 campioni) | Sezione A.2, bozza (righe 1–2 con 1.000 campioni, in parte precedenti alla griglia) |
|---:|---|---|
| 1 | 34,65% · 1,87× | — (livello nuovo) |
| 3 | 50,19% · 2,71× | 57,9% · 3,13× |
| 6 | 47,32% · 2,56× | 47,6% · 2,57× |
| 12 | 41,83% · 2,26× | 41,9% · 2,26× |

**L'andamento fra 3, 6 e 12 nodi è quello della 5.8.1**: meno nodi, più attribuzione. Il livello a 1
nodo, che la 5.8.1 non aveva, lo rovescia. Le cifre a 3 nodi differiscono (50,2% contro 57,9%), e
per il §9 non si confrontano al centesimo. Il 2,23 che il prompt riportava per la terza riga è 2,26
nella A.2: la differenza va sistemata nel testo della tesi.

---

## Per canale: dove va l'eccesso quando si tolgono nodi

Rapporto stimato/vero mediano sugli otto mondi; fra parentesi `C_k`, i mondi su otto in cui
l'intervallo del canale contiene il vero.

| Canale | ROI vero | 1 nodo | 3 nodi | 6 nodi | 12 (D0) |
|---|---:|---:|---:|---:|---:|
| Google Ads | 1,45 | **2,72** (1/8) | 3,37 (1/8) | 3,89 (3/8) | **3,80** (2/8) |
| Indeed | 2,69 | **1,51** (8/8) | 1,23 (7/8) | 0,83 (7/8) | **0,73** (7/8) |
| LinkedIn Ads | 0,85 | 1,74 (7/8) | 1,82 (8/8) | 1,58 (8/8) | 1,50 (7/8) |
| Meta Ads | 1,65 | 1,06 (8/8) | 1,43 (7/8) | 1,15 (7/8) | 1,20 (8/8) |
| Altre job board | 2,45 | 0,75 (8/8) | 0,66 (8/8) | 0,58 (8/8) | 0,58 (8/8) |
| Jooble | 2,55 | 0,66 (8/8) | 0,55 (8/8) | 0,52 (8/8) | 0,51 (8/8) |
| Subito Lavoro | 2,69 | 0,51 (8/8) | 0,55 (8/8) | 0,52 (8/8) | 0,48 (8/8) |

Descrittivo, non seleziona rami: a 1 nodo l'eccesso su Google Ads scende (da 3,80 a 2,72 volte il
vero), ma **quello su Indeed sale** (da 0,73 a 1,51). I tre canali più piccoli restano fra la metà e
i tre quarti del vero, vicino al prior. **L'eccesso si sposta da un canale grande all'altro invece di
sparire**, e i piccoli restano dove sono: per questo l'ordine non migliora, anche se il totale
scende.

---

## Ammissibilità e diagnostica

| Livello | Ammissibili | R-hat massimo | ESS minimo | Divergenze mediane | Divergenze sopra l'1% | Durata di un fit |
|---:|:---:|---:|---:|---:|---|---|
| 1 | 8/8 | 1,007 | 1.000 | 0,23% | 42 (1,56%), 102 (1,63%), 107 (1,53%) | 9,2–9,7 min |
| 3 | 8/8 | 1,003 | 1.169 | 0,19% | 42 (2,20%), 102 (1,31%) | 9,3–9,7 min |
| 6 | 8/8 | 1,011 | 448 | 0,28% | 42 (1,25%), 102 (2,94%) | 9,4–9,7 min |

Nessun run non ammissibile. Le divergenze da sole non squalificano (§4.1) e sono segnalate come fa
l'Appendice A.

---

## Le ore

| Che cosa | Quando (CEST) | Fonte |
|---|---|---|
| Notebook con la pre-registrazione nel blob, nei Download di Giacomo | 22/9, 21:39 | data del file; blob identico al byte al file committato |
| Pre-registrazione scritta su Drive dal pre-volo | 22/9, 21:40:04 | data del file su Drive |
| Fine del fit di replica | 22/9, 21:52:28 | colonna `quando` (in UTC nel file) |
| Livello 1 | 22/9, 22:02:36 – 23:12:29 | colonna `quando` |
| **Commit della pre-registrazione** | **23/9, 00:11:11** | commit `5f1c234` |
| Livello 3 | 22/9, 23:22:44 – 23/9, 00:33:43 | colonna `quando` |
| Livello 6 | 23/9, 00:43:53 – 01:54:49 | colonna `quando` |

**La pre-registrazione è stata committata dopo l'avvio dei fit**, e lo dichiara
`preregistrazioni/NOTA_tempi_N1_Robyn_2026-09-22.md`. La prova che il testo precede i numeri è su
file: il notebook scaricato alle 21:39 contiene la pre-registrazione identica al byte, e il pre-volo
l'ha scritta su Drive alle 21:40, dodici minuti prima della fine del primo fit.

---

## Il legame con D13 (§8)

**La condizione del §8 è soddisfatta**: ramo 2 sul livello. Il nulla di D13 è stato misurato con la
baseline a 96 nodi, e N1 dice che a 1 nodo per trimestre la baseline conta. Una prova in stile D13
con la baseline a 1 nodo per trimestre **potrebbe avere senso**: un solo livello di `f`, 8 fit. **Non
l'avvia nessuna sessione**: la decisione e la pre-registrazione sono di Giacomo (§9, punto 9). D13 è
chiuso, se lo si chiude, **con la baseline a 96 nodi**, non in assoluto.

---

## Conseguenze per il testo della tesi

Sono proposte da approvare, non modifiche già fatte.

- **La Sezione 5.8.1** descrive «meno nodi, più sovrastima» come meccanismo. Fra 3 e 12 nodi resta
  vero; a 1 nodo si rovescia su tutti gli otto mondi. La frase va limitata all'intervallo in cui
  vale, e accanto va scritto il ramo 2.
- **Non si può scrivere** che la configurazione a 96 nodi è la più favorevole fra quelle provate, né
  che il fattore 2,2 è la stima meno sfavorevole: era il testo del ramo 1.
- **La Sezione A.2 dell'Appendice** dice che tutte le esecuzioni usano 96 nodi. Con N1 non è più vero.

**Righe per l'Appendice A.**

Tabella A.2 (i disegni):

| N1 nodi della baseline | nessun intervento sui dati: stessi otto mondi di D0, baseline a 1, 3 e 6 nodi per trimestre invece di 12; più una replica di D0 sul mondo 42 come cancello | 24 + 1 |

Tabella A.3 (registro dei run):

| N1, 1 nodo per trimestre | 8 | 1,81 | +15,6 | 0/8 | 0,23% | 4.291 |
| N1, 3 nodi per trimestre | 8 | 2,29 | +24,2 | 0/8 | 0,19% | 2.485 |
| N1, 6 nodi per trimestre | 8 | 2,27 | +23,9 | 0/8 | 0,28% | 1.865 |

---

*File dei risultati, scritto il 23 settembre 2026 dopo che i rami erano stati stampati. Ogni cifra
viene dai CSV in `griglia_N1/`, da quelli di D0 in `griglia/` o dall'uscita di `analisi_N1_nodi.py`.*
