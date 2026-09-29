# Risultati — D14: allocare il budget con i ROAS del benchmark interno

**A: ramo A1 SUCCESSO. B1: nessun livello soddisfa il criterio, nemmeno con ROAS esatti. B2: soddisfano
il criterio i livelli δ = 0,10; 0,25; 0,50; 0,75; 1,00; il livello zero no, quindi la soglia di
tolleranza non esiste.**

Scritto il 24/9/2026 dopo il run, in un file separato dalla pre-registrazione
`preregistrazioni/PREREGISTRAZIONE_D14_allocatore_ROAS_benchmark.md`, approvata da Giacomo il 24/9 e
congelata alle 22:44:34 UTC (sha256 `43b4cf866856ed7ad0b9aba2b69ea3c7b06500817fa9ef8e86294953c73c9cb8`).
Run dalle 22:46:18 alle 22:46:38 UTC secondo il registro, 13,2 s di calcolo su CPU. Ogni cifra viene dai CSV del run
(`D14_risultati.csv`, `D14_B1_tolleranza.csv`, `D14_B1_estrazioni.csv`, `D14_B2_sistematico.csv`), dal
suo registro `D14_esecuzione.txt` o dai file scritti dal generatore.

---

## Limiti, da leggere prima dei numeri (§10 della pre-registrazione)

1. **Nel simulatore il benchmark parte dal ROI vero MEDIO**, moltiplicato per un fattore fisso per
   canale. Non contiene la domanda organica assorbita dai canali tracciati né il tracciamento non
   casuale della Sezione 3.5. Il test misura quindi il caso migliore: se i ROAS perdono qui, perdono
   anche nella realtà; se vincono qui, nella realtà non è garantito.
2. **Cautela della Sezione 6.3**: l'accuratezza del benchmark è un parametro di costruzione. I fattori
   della parte A sono fissi, uguali in tutti i mondi e scelti da noi: Google 1,30; Jooble 1,10; Meta
   1,05; Subito Lavoro e Altre job board 0,95; LinkedIn 0,85; Indeed 0,80.
3. **Otto casi, sei mondi distinti**: i tre casi del mondo 103 sono identici per costruzione.
4. **`beta` fisso**: si legge la superficie di risposta implicita nei parametri veri.
5. **A questa cifra il nullo di R1 favorisce la regola** (aggiunta (a)); il §4 qui sotto lo mostra con
   i numeri. A1 va letto insieme al controllo nella banda.
6. **La pre-registrazione non è cieca** (sotto).

## Il run preliminare annullato, citato come richiesto

Prima dell'approvazione di Giacomo ho eseguito una versione preliminare, con una pre-registrazione
mia congelata prima del run (sha256 `bc601cf4a8519cb4683f87cfc3d5587e4267242c4f73009d1b13b0595f15bf52`)
ma non verificata da lui. Differiva in quattro punti:

1. usava gli 8 mondi base 42, 101–107, non gli 8 casi di D11 e R1;
2. usava come controllo nullo le 5.040 graduatorie dentro lo stesso allocatore, non le 200 coppie di R1;
3. non aveva la variante sistematica;
4. il suo script leggeva il file del benchmark per nome di colonna.

Le sue cifre, dichiarate al §0 della pre-registrazione prima di questo run:

- l'allocatore sui ROAS del benchmark guadagnava fra +0,5852% e +1,3389% in 8 mondi su 8, con
  percentile fra 0,950 e 0,981 rispetto alle 5.040 graduatorie, spostando fra l'11,53% e il 12,34%
  del budget;
- con ROAS perfetti perdeva in 8 mondi su 8, fra −1,2565% e −1,9641%;
- con distorsioni casuali la mediana del percentile stava fra 0,6452 e 0,7024, e le estrazioni con
  guadagno positivo fra lo 0% e il 33,0%.

La cartella `D14_preliminare_ANNULLATO` resta archiviata e non è stata cancellata. Nessuna sua cifra
entra nelle tabelle qui sotto.

---

## 1. Cancello: passato

- ROAS del benchmark letto dal file, contro il contributo vero per il fattore del generatore: scarto
  massimo fra −0,0324% (seme 107, Jooble) e +0,0095% (seme 103, Jooble). Tolleranza 0,1%.
- Contributo vero del non fare niente e guadagno dell'allocatore del modello riprodotti per tutti gli
  8 casi, rispetto a `D11_risultati.csv` del pacchetto D11. Il contributo coincide alle tre cifre
  decimali; l'allocatore coincide alla quarta cifra, tranne D1/105 (−1,2984% contro −1,2985%, dentro
  la tolleranza di ±0,010 punti).

## 2. Parte A — ramo A1, previsione confermata

La regola, identica negli otto casi, porta **Jooble, Subito Lavoro, Altre job board e Indeed a
+30%**, lascia Google Ads a un valore intermedio fra +11,08% e +14,21%, e taglia **Meta Ads e
LinkedIn Ads a −30%**. Sposta fra l'11,53% e il 12,34% del budget.

| Caso | g% | p (nullo R1) | nullo R1, 90° perc. | oracolo (coppie) | f | allocatore del modello (D11) | p nella banda (descr.) | migliore graduatoria (descr.) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| D1/101 | +1,1119% | 0,920 | +0,4857% | +3,0606% | 0,363 | −1,0332% | 0,967 | +1,6851% |
| D1/103 | +0,5852% | 0,965 | −0,9183% | +2,0701% | 0,283 | −1,2608% | 0,974 | +0,6846% |
| D1/105 | +1,2279% | 0,955 | −0,5687% | +2,9145% | 0,421 | −1,2985% | 0,974 | +1,6857% |
| D1/107 | +1,1809% | 0,955 | −0,2785% | +2,8662% | 0,412 | −1,1779% | 0,974 | +1,6997% |
| D2/102 | +1,3389% | 0,950 | +0,8986% | +3,6421% | 0,368 | −1,0605% | 0,957 | +2,2054% |
| D2/103 | +0,5852% | 0,965 | −0,9183% | +2,0701% | 0,283 | −1,2608% | 0,974 | +0,6846% |
| D10/42 | +0,9956% | 0,935 | +0,0317% | +2,7232% | 0,366 | −1,2714% | 0,950 | +2,0187% |
| D10/103 | +0,5852% | 0,965 | −0,9183% | +2,0701% | 0,283 | −1,2608% | 0,974 | +0,6846% |

- **8 casi**: g% mediano **+1,0537%**; guadagno in 8 su 8; p ≥ 0,90 in **8 su 8**; meglio
  dell'allocatore del modello in 8 su 8. **Ramo A1.**
- **6 mondi distinti** (descrittivo): g% mediano +1,1464%, guadagno in 6 su 6, p ≥ 0,90 in 6 su 6.
- **Controllo nella banda** (descrittivo, non sceglie il ramo): p mediano 0,974, fra 0,950 e 0,974. La
  regola batte almeno il 95% delle 5.040 graduatorie possibili nella stessa banda; A1 regge anche
  letto con questo controllo.
- f mediano 0,364: la regola cattura circa un terzo del guadagno della migliore coppia alla stessa
  cifra.

## 3. Parte B1 — errore casuale: nessun livello soddisfa il criterio (previsione confermata)

**Livelli che soddisfano il criterio: nessuno. Soglia: nemmeno con ROAS esatti.**

| σ | Repliche che soddisfano (su 200) | Esito | g% mediano | Estrazioni con g > 0 | p mediano (R1) | Estrazioni con p ≥ 0,90 |
|---:|---:|---|---:|---:|---:|---:|
| 0,00 | 0 | non soddisfa | −1,4214% | 0,0% | 0,943 | 62,5% |
| 0,10 | 5 | non soddisfa | −1,2739% | 17,1% | 0,955 | 71,1% |
| 0,25 | 35 | non soddisfa | −1,2739% | 33,8% | 0,955 | 73,2% |
| 0,50 | 14 | non soddisfa | −1,2739% | 28,9% | 0,930 | 57,2% |
| 0,75 | 11 | non soddisfa | −1,3530% | 23,1% | 0,895 | 45,8% |
| 1,00 | 5 | non soddisfa | −1,6118% | 21,1% | 0,885 | 39,1% |

## 4. Parte B2 — errore sistematico: soddisfa da δ = 0,10, non a δ = 0 (previsione confermata)

**Livelli che soddisfano il criterio: 0,10; 0,25; 0,50; 0,75; 1,00. Soglia (contigua da zero): non
esiste, perché il livello zero fallisce.**

| δ | Rapporto di credito chiusura / inizio | g% mediano | p ≥ 0,90 | Esito |
|---:|---:|---:|---:|---|
| 0,00 | 1,00 | −1,4214% | 5 su 8 | non soddisfa |
| 0,10 | 1,22 | +1,0537% | 8 su 8 | soddisfa |
| 0,25 | 1,65 | +1,0537% | 8 su 8 | soddisfa |
| 0,50 | 2,72 | +1,0537% | 8 su 8 | soddisfa |
| 0,75 | 4,48 | +1,0537% | 8 su 8 | soddisfa |
| 1,00 | 7,39 | +1,0537% | 8 su 8 | soddisfa |

Da δ = 0,10 in su **il riparto è identico a quello della parte A in tutti gli 8 casi**, verificato
riga per riga sul CSV: stesso insieme di canali alzati, stesso canale intermedio, stessi canali tagliati.

**Il livello zero mostra l'avvertenza (a) con i numeri.** Con ROAS esatti la regola perde in tutti gli
8 casi, fra −1,2565% e −1,9641% (−1,2739% nei tre casi del 103). Eppure contro il nullo di R1 ha
p = 1,000 nei tre casi del 103, 0,955 nel 42 e 0,930 nel 101. Una ripartizione che perde candidature
batte comunque fino al 100% delle mosse casuali, perché una mossa del 12% del budget su una sola coppia
perde di più. Da solo, il percentile rispetto al nullo di R1 a questa cifra non distingue una regola
che guadagna da una che perde: a decidere il ramo è il segno del guadagno.

## 5. Previsioni, una per una

| Previsione (§9) | Esito |
|---|---|
| A: ramo A1 | **confermata** |
| A: p ≥ 0,90 rispetto al nullo di R1 in almeno 6 casi su 8 | **confermata**: 8 su 8 |
| B1: la soglia non esiste; nessun livello soddisfa il criterio | **confermata** |
| B2: fallisce a δ = 0 | **confermata** |
| B2: soddisfa dal primo livello in cui Google supera Meta, già a δ = 0,10 | **confermata**: da 0,10, con riparto identico ad A |

Nessuna previsione smentita. Va letto con il §0 della pre-registrazione: le previsioni erano informate
dal run preliminare e, per B2, dalla struttura della regola. La conferma dice che il run formale
riproduce quanto era atteso; non è una prova indipendente.

## 6. Lettura

**Il guadagno della parte A non viene dall'accuratezza dell'attribuzione.** Con il ROI medio vero, cioè
con un benchmark senza errore, la stessa regola perde in tutti gli 8 casi. In tutti e sei i mondi il
ROI medio vero di Meta supera quello di Google: 1,6249 contro 1,4973 nel 42, 1,6584 contro 1,3640 nel
103, dai file dei parametri del generatore. La regola con ROAS esatti taglia quindi Google del 30% e
lascia Meta intermedio. Ma Google ha più margine sulla propria curva (saturazione 26,4% contro 39,0%
di Meta, Tabella 5.1), e al margine un suo euro rende di più (Tabella 5.9 per il mondo 42: 1,43 contro
1,09). Il fattore 1,30 che il generatore dà al benchmark di Google, contro l'1,05 di Meta, inverte i
due canali, e la graduatoria distorta si avvicina per caso a quella marginale.

**La parte B lo conferma da due lati.** L'errore casuale non soddisfa il criterio a nessun livello.
L'errore sistematico realistico, più credito ai canali che chiudono il percorso, lo soddisfa da un
rapporto di credito di 1,22 in su, e solo perché produce la stessa inversione. Nel simulatore il
difetto tipico dell'attribuzione aiuta per una coincidenza dei parametri del generatore. Sui dati reali
niente garantisce che il verso sia lo stesso: dipende da dove stanno i canali sulle loro curve, cioè
proprio dalla grandezza che né il benchmark né il modello osservativo misurano.

**Conseguenza per la tesi.** Rafforza, per un'altra via, la Sezione 5.10.6: un ritorno medio, anche
esatto, non basta a spostare budget, perché la decisione dipende dal rendimento marginale. Non
rovescia la Sezione 6.3: il benchmark ordina bene i canali per ritorno medio, ma ordinarli per ritorno
medio non è ciò che serve per allocare.

## 7. File, impronte, tempi

| File | sha256 |
|---|---|
| `preregistrazioni/PREREGISTRAZIONE_D14_allocatore_ROAS_benchmark.md` | `43b4cf866856ed7ad0b9aba2b69ea3c7b06500817fa9ef8e86294953c73c9cb8` |
| `studio_D14.py` | `8401eb4814d6ce2a7412a73694d65039dcb0e861824cd3464b6589bff64763ff` |
| `D14_risultati.csv` | `ce9608e492263ef5568a4ab7fc5432e79d7b065c29dbc07760f2afd2a13fd670` |
| `D14_B1_tolleranza.csv` | `a6bde7b97adfc794abe71c9bc50b45fd8f6091bd911044fc94b264b64ce6168a` |
| `D14_B1_estrazioni.csv` | `205e31d1f67744c5bf88d80e37ca023df538e845cfc1fc15d6d65024c21bc31d` |
| `D14_B2_sistematico.csv` | `ebe8544da7de8e3604510470dcb54a7fbc8b38c1acd09d646699bf7c56328790` |
| `D14_esecuzione.txt` | `0b93cc59bc9805fc139a4a10fedde67a08d8088efb0fb35615d652eb307e2d2b` |

Tempi dal registro: cancello 1,4 s; parte A 4,7 s; B1 7,1 s; B2 meno di 0,1 s; totale 13,2 s.
I mondi base scritti dal generatore stanno in `mondi/`. Nessun commit, nessun push.

---

*File dei risultati. La pre-registrazione è un file separato e non è stata modificata dopo il
congelamento.*
