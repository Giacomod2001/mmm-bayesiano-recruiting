# D13b — la domanda organica osservata con la baseline a 1 nodo per trimestre: risultati

**NESSUN RAMO — cancello di replica non riuscito.** Il fit di replica (D13 a f = 0,30, mondo 101,
12 nodi per trimestre) ha dato `rapporto_mediana` **2,4643** invece di **2,4593**, cioè +0,203%. La
regola era «identico alla riga di D13 alla quarta cifra». Come registrato al §2 e al §7 (punto 4)
della pre-registrazione, **nessuno degli 8 fit a 1 nodo è partito, e la replica non si rilancia**.

La previsione dichiarata (livello ramo 4, ordine ramo C) **non è valutabile**: il disegno non ha
prodotto nessun numero su cui leggerla.

Il risultato l'ha stampato `analisi_D13b.py`, committato con la pre-registrazione in `30049d1`, sulla
cartella scaricata da Drive (`MMM_griglia_D13b_1nodo-20260923T213656Z-1-001.zip`, sha256
`2b4e2852cb6c5f11…`), conservata identica in `griglia_D13b_1nodo/`:

```
D13b - NESSUN RAMO: cancello di replica FALLITA (rapporto_mediana 2.4643 invece di 2.4593 |
rapporto_ci05 1.8418 invece di 1.8321 | rapporto_ci95 3.1577 invece di 3.1253)
```

**D13 resta chiuso con la baseline a 96 nodi**, e la domanda del §8 di N1 (il nulla di D13 era un
effetto dei 96 nodi?) resta senza risposta.

---

## Il caveat di D13, che resta valido

Il controllo è costruito dalla baseline vera: sarebbe stato un limite superiore di ciò che un dato
reale può dare, e nel mondo reale un controllo del genere sarebbe in parte un mediatore. Qui non ci
sono cifre da accompagnare, ma il caveat resta la cornice di qualunque ripresa della prova.

---

## Che cosa è uguale e che cosa no

La riga della replica è stata confrontata, campo per campo, con la riga di D13 dello stesso mondo e
dello stesso livello.

**Uguali (34 campi).** Tutto ciò che riguarda i dati e la configurazione:
- l'impronta dei dati (`7eaa88ed1323`) e il contributo vero;
- la quota vera, il controllo (`domanda_organica_osservata`, f = 0,30) e la sua correlazione con la
  baseline vera;
- nodi (96), campioni, catene, adattamento, burn-in, seme MCMC, prior, valore per candidatura.

Il pre-volo aveva verificato anche il generatore (sha `8f86eb032d0113c0`) e i cinque dataset del
mondo 42 identici ai committati: se una di queste cose fosse cambiata, si sarebbe fermato prima del
fit.

**Diversi.** Tutto ciò che esce dal campionamento:

| Campo | D13 (22/9) | D13b, replica (23/9) |
|---|---:|---:|
| `rapporto_mediana` | 2,4593 | 2,4643 |
| forbice 5%–95% | 1,8321 – 3,1253 | 1,8418 – 3,1577 |
| quota attribuita ai media | 45,71% | 45,88% |
| divergenze | 1 | 4 |
| ESS su `roi_m` / `beta_m` | 2.434 / 2.510 | 2.659 / 2.595 |
| **durata del fit** | **9,8 min** | **39,85 min** |

Anche il primo draw della catena è diverso (16.888.756 contro 16.836.694): il campionatore ha
percorso un'altra traiettoria fin dall'inizio.

**Il fit è durato quattro volte tanto, sulla stessa GPU dichiarata (Tesla T4).** Con dati e
configurazione identici, il calcolo non è stato lo stesso calcolo.

---

## L'ambiente del 23 settembre

Stampato da Giacomo nella stessa sessione di Colab, dopo l'arresto:

| | versione |
|---|---|
| Python | 3.13.15 (build del 6 agosto 2026) |
| GPU | Tesla T4 |
| google-meridian | 1.8.0 |
| tensorflow | 2.21.0 |
| tensorflow-probability | 0.25.0 |
| tfp-nightly | 0.26.0.dev20260130 |
| jax | 0.11.1 |
| numpy | 2.1.3 |
| pandas | 2.2.3 |
| scipy | 1.16.3 |

**Che cosa si può dire e che cosa no.** I run precedenti non hanno registrato le versioni delle
librerie, quindi non si può stabilire quale sia cambiata. Due fatti restano:
- il 22 settembre alle 21:52 CEST la replica di N1 riproduceva ancora D0, eseguito il 15–16
  settembre, alla quarta cifra su rapporto, PIT, forbice e copertura;
- il 23 settembre, con gli stessi dati, lo stesso generatore e lo stesso runner, il fit è stato
  quattro volte più lento e ha dato un risultato diverso.

L'ipotesi più economica è che fra le due sessioni sia cambiato l'ambiente di esecuzione di Colab.
Può essere cambiata la versione di Python o di una libreria, oppure il fit può non aver usato la GPU
nello stesso modo, e la lentezza va in questa direzione. **È un'ipotesi, non una verifica.**

**Che cosa non tocca.** I risultati già registrati hanno superato ciascuno i propri cancelli nel
proprio ambiente, e nessuno di essi dipende da un confronto fra ambienti diversi.

---

## Le ore

| Che cosa | Quando (CEST) | Fonte |
|---|---|---|
| Commit della pre-registrazione | 23/9, 22:48:37 | commit `30049d1` |
| Pre-registrazione scritta su Drive dal pre-volo | 23/9, 22:52:08 | data del file su Drive; identica al byte a quella committata |
| Fine del fit di replica, arresto del cancello | 23/9, 23:34:35 | colonna `quando` (in UTC nel file) |

Questa volta la pre-registrazione è entrata in git prima del primo fit.

---

## Conseguenze

- **Per la tesi.**
  - Nell'Appendice A, D13b va registrato come un fit, la replica, con esito «cancello non riuscito».
  - Nella parte sulla riproducibilità va una frase: nello stesso ambiente i run si riproducono alla
    quarta cifra (D0 replicato da N1 dopo sei giorni); cambiando ambiente, lo stesso fit si è
    spostato dello 0,2% ed è durato quattro volte tanto. Per questo ogni run futuro deve registrare
    le versioni delle librerie e il dispositivo usato.
  - Il rimando «Sezione 5.x» del §7.3 punta a D13, chiuso a 96 nodi.
- **Per il notebook aziendale.** Deve scrivere, accanto a ogni risultato, le versioni dell'ambiente
  e il dispositivo su cui ha girato il fit. Senza, un'analisi rifatta un mese dopo può dare numeri
  diversi senza che nessuno sappia perché.
- **Per il programma sperimentale.** Riprendere D13b vorrebbe dire un cancello tarato sul nuovo
  ambiente, cioè un disegno nuovo da registrare daccapo. Non è previsto: gli esperimenti si
  chiudono qui.

---

*File dei risultati, scritto il 23 settembre 2026 dopo che lo script aveva stampato l'esito. Ogni
cifra viene dai CSV in `griglia_D13b_1nodo/`, da quelli di D13 in `griglia_D13/`, o dall'uscita
dell'ambiente stampata in chat.*
