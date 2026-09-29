# Pre-registrazione — D12: il blackout totale geografico. Muovere il livello recupera la baseline?

**21 settembre 2026. Definitiva.** Scritta prima di qualunque fit e prima di guardare qualunque
risultato di stima. I controlli di fedeltà del §7 sono stati eseguiti prima di chiudere questo
documento — erano una precondizione del disegno, non una sua misura — e le loro uscite sono al §8.
Qualunque risultato va in un file separato.

---

## 0. Il punto tecnico decisivo, verificato prima di scrivere il resto

**Senza una patch al generatore, D12 misurerebbe esattamente zero.** Non è un rischio: è una
proprietà del generatore, e l'ho verificata prima di scrivere questa pre-registrazione.

Al passo 7 di `genera()` (`genera_dati_simulati.py`, "calibrazione di beta sulla quota di contributo
media") il coefficiente di ogni canale è ricalibrato così:

```python
totale_atteso = organico_tot / (1.0 - S)          # non dipende dalla spesa dei media
grezzo  = float(risposta_grezza[ch].sum())        # dipende dalla spesa
beta[ch] = quote_ch[ch] * totale_atteso / max(grezzo, 1e-12)
risposta[ch] = beta[ch] * risposta_grezza[ch]     # = quote_ch[ch] * totale_atteso, SEMPRE
```

`beta` è scelto **proprio per cancellare** l'effetto della spesa. È la stessa scoperta che rese
necessaria la patch G5 per D11, e per D12 morde ancora più forte, perché D12 toglie spesa davvero.

**La prova, sui mondi, prima dei fit.** Ho generato il mondo blackout in due versioni, una con
`beta` ricalibrato (cioè senza patch) e una con `beta` tenuto fisso ai valori del mondo base:

| Mondo | Spesa tolta | Contributo vero, mondo base | Contributo vero **senza** la patch | Contributo vero **con** la patch |
|---|---:|---:|---:|---:|
| 42 | −3,42% | 158.330,7 | 158.330,7 (scarto 2,2·10⁻¹⁶) | 152.991,7 |
| 101 | −3,25% | 158.329,5 | 158.329,5 (scarto 0) | 152.922,6 |
| 103 | −3,46% | 158.329,8 | 158.329,8 (scarto 0) | 153.352,1 |
| 107 | −3,71% | 158.329,7 | 158.329,7 (scarto 0) | 152.488,1 |

Senza la patch, togliere il 3,4% della spesa lascia il contributo vero **identico a tutte le cifre**:
la quota vera resta 18,5000% e il disegno non misura niente, né se funziona né se non funziona.

**La patch, G6.** Nel mondo blackout `beta` — e con lui la mezza saturazione `ec`, che è una
proprietà del mondo e non del disegno — resta quello del **mondo base dello stesso seme**, rigenerato
per intero nello stesso processo con una chiamata ricorsiva a `genera()` senza il disegno. La verità
si ricalcola con quei `beta` e quegli `ec`. Verificato: la differenza relativa fra i `beta` del mondo
blackout e quelli del mondo base è **esattamente 0** su tutti e sette i canali e su tutti e otto i
mondi, e lo stesso vale per `ec` (§8, controllo 3a).

**Che cosa stiamo misurando, detto con precisione.** Con `beta` ed `ec` fissi non stiamo leggendo un
mondo che il generatore produrrebbe da solo: stiamo valutando **la superficie di risposta implicita
nei parametri veri di quel mondo**. È legittimo, è l'unica strada, ed è un'altra cosa: va dichiarato
accanto a ogni cifra dei risultati e nel testo che li commenta. È la stessa dichiarazione che
accompagna D11.

**Conseguenza sulla metrica, da fissare adesso.** Poiché il contributo vero scende, la quota vera dei
media in questo mondo **non è più 18,5%**: vale fra 17,94% e 18,04% a seconda del mondo (§8). `E` si
calcola contro la quota vera **di questo mondo**, letta dalla sua verità, esattamente come fa il
runner in tutta la griglia. Confrontare la quota stimata con 18,5% sarebbe confrontarla con la verità
di un altro mondo.

---

## 1. Domanda

I circa otto punti di eccesso che restano dopo il calendario (D2: +7,2; D10: +8,3, e raddoppiare i
giri non li riduce) stanno nella domanda organica. Nessuno degli undici disegni già eseguiti cambia
**quanta** pubblicità c'è: cambiano solo dove e quando. Un disegno che muove il **livello** dei
media, e non solo la loro distribuzione, recupera quei punti?

## 2. Disegno

Otto mondi, i semi della griglia: 42, 101, 102, 103, 104, 105, 106, 107. Un fit per mondo, otto fit.

**Le cinque regioni, fisse in tutti i mondi.** Le venti regioni si ordinano per popolazione
decrescente e si dividono in cinque strati contigui da quattro; da ogni strato si prende la regione
in **posizione 1** (0-based, cioè la seconda dello strato). Nessuna estrazione casuale.

| Strato | Regioni (popolazione decrescente) | Trattata |
|---|---|---|
| 0 | Lombardia, **Lazio**, Campania, Veneto | Lazio (9,7%) |
| 1 | Sicilia, **Emilia-Romagna**, Piemonte, Puglia | Emilia-Romagna (7,5%) |
| 2 | Toscana, **Calabria**, Sardegna, Liguria | Calabria (3,1%) |
| 3 | Marche, **Abruzzo**, Friuli-Venezia Giulia, Trentino-Alto Adige | Abruzzo (2,1%) |
| 4 | Umbria, **Basilicata**, Molise, Valle d'Aosta | Basilicata (0,9%) |

**Perché la posizione 1 e non un'altra.** Un campione di 5 regioni su 20 dovrebbe portare con sé il
25% della popolazione. Le quattro scelte sistematiche possibili danno 35,24% (posizione 0), **23,39%
(posizione 1)**, 21,99% (posizione 2) e 19,38% (posizione 3): la posizione 1 è quella più vicina al
25% nominale. Il criterio è la rappresentatività del campione, è deciso adesso e riguarda il disegno,
non il risultato. Diagnostica dichiarata, non filtro: la vocazione estiva media delle cinque regioni
trattate, pesata per popolazione, vale 0,5255 contro 0,5053 nazionale.

**I due blocchi, fissi in tutti i mondi e uguali per tutti i canali:** settimane **9–16** e **53–60**
(1-based, inclusive; 0-based 8–15 e 52–59). Sono le stesse partenze del calendario di D2 per il primo
canale: un blocco per anno, le prime otto settimane lasciate libere perché l'adstock si riempia.

**Che cosa succede nelle celle trattate.** Tutti e sette i canali hanno spesa **esattamente zero**.
Celle trattate per canale: 5 regioni × 16 settimane = **80**, cioè il 3,85% del panel.

**La spesa tolta NON viene ridistribuita.** È questo che distingue D12 da tutti i disegni precedenti.
Nel geo (D1, D6, D7, D8) e nel calendario (D2, D10) la quota delle regioni trattate viene azzerata e
la settimana rinormalizzata: la spesa nazionale settimanale resta quella della base. Qui no: le
quote non tornano a sommare a uno, e la spesa nazionale settimanale **scende**. Misurato sul mondo
42: nelle sedici settimane trattate la spesa nazionale passa da 530.478 a 405.015 EUR, cioè
**−23,65%** (fra −22,89% e −24,23% settimana per settimana); sul biennio la spesa totale scende fra
il 3,19% e il 3,72% a seconda del mondo.

**Nelle regioni-settimane trattate le candidature osservate sono la baseline**, letta e non inferita.
È l'informazione che il disegno porta al modello e che nessun altro disegno della griglia porta.

**Configurazione di stima: identica a tutta la griglia, non si cambia.** 96 nodi
(`KNOTS_PER_QUARTER` 12), keep 2.000, 4 catene, adapt 500, burnin 500, seme MCMC 42 su tutti i mondi,
`revenue_per_kpi` 40,0, prior ROI LogNormale(0,2; 0,9) di riferimento, stagionalità a 4 decimali.

## 3. Metriche

Le stesse della griglia, calcolate dal runner sulle stesse colonne:

- `rapporto_mediana` = contributo mediano stimato / contributo vero, con il totale **sommato dentro
  ogni draw** e poi mediana e quantili (mai la somma degli estremi canale per canale);
- **`E` = quota stimata − quota vera**, in punti percentuali, con la quota vera **di questo mondo**
  (§0), fra 17,94 e 18,04 a seconda del seme;
- `PIT` sui draw del totale;
- `C_tot` = numero di mondi su otto in cui l'intervallo al 90% sul contributo totale contiene il vero;
- per canale: `C_k`, `larghezza_relativa`, `rho_spearman`.

**Ammissibilità, criterio della Sezione 4.7, due cancelli:** (1) il prior non contiene la risposta;
(2) R-hat ≤ 1,1 ed ESS ≥ 100 su `roi_m` e `beta_m`. Le divergenze si riportano e da sole non
squalificano. Un run non ammissibile si riporta col suo numero e **non si rifà**.

## 4. Regola di decisione — deterministica, prima riga che corrisponde

Si legge su `E` **mediano** sugli otto mondi.

| # | Condizione | Ramo |
|---|---|---|
| 1 | `E` mediano ≤ 4,0 **e** `C_tot` ≥ 4/8 | **IL BLACKOUT TOTALE RECUPERA LA BASELINE** |
| 2 | 4,0 < `E` mediano ≤ 6,0 | **RECUPERO PARZIALE**: si riporta, non si raccomanda senza il conto del costo |
| 3 | `E` mediano > 6,0 | **NEMMENO IL LIVELLO BASTA**: il limite del capitolo 7.3 si rafforza |

Se il ramo 1 è selezionato dalla prima condizione ma `C_tot` < 4/8, si scende al ramo 2 o 3 secondo
il valore di `E`: la copertura è parte della prima riga e non si scorpora.

Si riportano sempre, senza che selezionino il ramo: `rapporto_mediana` mediano, mediana del PIT,
`C_tot`, `C_k` per canale, larghezza relativa mediana per canale, e il confronto con D2 e D10 a
parità di tutto il resto.

## 4-bis. La corsa fra due diagnosi, dichiarata adesso

Sul residuo ci sono **due ipotesi rivali**, e vanno messe l'una contro l'altra prima di guardare i
numeri, non dopo.

- **Ipotesi organica** (quella del mandato, e quella che D12 presuppone): i circa otto punti che
  restano dopo il calendario stanno nella domanda organica non modellata.
- **Ipotesi di collinearità**: il residuo è collinearità fra i canali a pagamento, che spendono
  tutti in alta stagione, con il più grande che assorbe l'effetto condiviso. È un problema di
  identificazione, e nessun dato in più lo risolve. Non è un'ipotesi inventata adesso: è la
  conclusione della sezione 9 di `report.md`, dove un controllo proxy della domanda organica
  (`direct_apps`, correlato 0,95 con le conversioni) non spostò di niente l'errore sui canali —
  Google da +39% a +38%, Indeed +30% invariato, LinkedIn −25% invariato, Meta da +9% a +10%.

D12 e D13 insieme sono una corsa fra le due, da due strade indipendenti:

- **D12** attacca l'ipotesi organica **muovendo il livello dei media**, cioè creando il contrasto
  che oggi non c'è: nelle regioni spente le candidature osservate sono la baseline, letta;
- **D13** la attacca **portando al modello il dato organico**, nel caso più favorevole possibile;
- se **entrambi** danno il ramo peggiore (D12 ramo 3, D13 ramo 4), l'ipotesi organica è esclusa da
  due strade indipendenti e la spiegazione per collinearità **vince per eliminazione**;
- se **almeno uno** dà il ramo buono (D12 ramo 1, o D13 ramo 1 o 2), l'ipotesi organica regge, e la
  sezione 9 va riletta come un falso negativo dovuto al proxy debole (il dettaglio
  dell'argomentazione sta al §4-bis della pre-registrazione di D13).

Questa lettura è fissata adesso e **non si negozia dopo**: in particolare non è ammesso, a risultati
visti, dichiarare vincente la collinearità sulla base di un solo disegno, né salvare l'ipotesi
organica invocando differenze di impianto non dichiarate qui.

## 5. Previsione dichiarata

**Previsione: ramo 1, con `E` fra 3 e 4 punti.** Il motivo è che nelle cinque regioni spente, per
sedici settimane, le candidature osservate **sono** la baseline: il modello non deve più inferirla da
un contrasto, la legge. È l'unica informazione che mancava a D2 e D10, che muovono la distribuzione
ma lasciano intatto il livello.

**Cosa la smentirebbe: il ramo 3.** Direbbe che il residuo non è identificabile nemmeno muovendo il
livello, e che il limite dichiarato nel capitolo 7.3 non è un difetto del disegno sperimentale ma una
proprietà del problema.

**Il punto debole della previsione, dichiarato adesso.** Le celle trattate sono l'3,85% del panel e
la spesa totale scende solo del 3,2–3,7%: il livello si muove, ma poco. Se `E` finisce fra 4 e 6
(ramo 2) la lettura onesta non è «ha quasi funzionato», è «il recupero c'è ma non basta, e va pesato
contro il costo del §6». Questa frase è scritta prima di vedere i numeri proprio perché non la si
possa scrivere dopo.

## 6. Il costo del disegno, che qui è reale e non redistribuito

È la cifra che il capitolo 7.2 oggi dichiara come non misurata, e D12 la misura. Calcolata dal
contributo vero: contributo del mondo base meno contributo del mondo blackout, a parità di tutto il
resto. Comprende la coda dell'adstock, che continua a pesare nelle otto settimane successive a ogni
blocco. **Già calcolata sui mondi, prima dei fit**, e scritta nel JSON di ogni mondo
(`scenario_blackout.costo_del_disegno`):

| Mondo | Spesa tolta (EUR) | Spesa tolta | Candidature vere perse, celle trattate | Candidature vere perse, totale |
|---|---:|---:|---:|---:|
| 42 | 125.463,37 | −3,42% | 5.013,6 | **5.339,0** |
| 101 | 118.463,42 | −3,25% | 5.110,7 | 5.406,9 |
| 102 | 114.432,75 | −3,24% | 5.115,3 | 5.430,2 |
| 103 | 131.606,00 | −3,46% | 4.681,8 | 4.977,7 |
| 104 | 120.618,05 | −3,30% | 4.698,9 | 5.032,3 |
| 105 | 139.084,37 | −3,72% | 5.533,3 | 5.831,1 |
| 106 | 119.789,71 | −3,19% | 4.570,9 | 4.841,1 |
| 107 | 140.428,43 | −3,71% | 5.481,4 | 5.841,6 |

Sul mondo 42: 125.463 EUR di spesa non fatta e 5.339 candidature vere non arrivate, cioè il 3,4% del
contributo incrementale totale del biennio, a fronte di 855.534 candidature osservate nel mondo base
contro 850.576 nel mondo blackout. Nei risultati questa tabella va riportata **accanto** al ramo, non
in fondo: un disegno che recupera la baseline al prezzo di 5.000 candidature è una raccomandazione
diversa da uno che la recupera gratis.

## 7. Cosa NON è ammesso dopo aver visto i risultati

1. Spostare le soglie (4,0 · 6,0 · 4/8) o i confini dei rami, o aggiungerne.
2. Cambiare le regioni trattate, la loro posizione nello strato, i blocchi, la loro lunghezza, o il
   numero di canali spenti.
3. Aggiungere mondi, toglierne, o rifare un run non ammissibile.
4. Confrontare la quota stimata con 18,5% invece che con la quota vera di questo mondo.
5. Leggere il ramo 2 come un successo, o presentare il recupero senza il costo del §6.
6. Ridistribuire la spesa a posteriori, o rileggere il disegno come se lo facesse.
7. Attribuire a D12 un risultato che vale per la superficie di risposta a `beta` e `ec` fissi senza
   dire che vale a `beta` e `ec` fissi.
8. Rinegoziare la corsa del §4-bis dopo aver visto i numeri: dichiarare vincente la collinearità
   sulla base del solo D12, o salvare l'ipotesi organica invocando differenze di impianto non
   dichiarate qui.

## 8. Controlli di fedeltà — eseguiti prima di chiudere questo documento

Generatore di riferimento: `main` del repo pubblico + le 8 sostituzioni della catena A + i diff
G1, G2, G3, G4 applicati a fuzz 0 in ordine. Impronta ottenuta **`c57be0b1e94c0bbd`**, uguale a
quella collaudata per D10 e D11: il punto di partenza è lo stesso file. Con G6 in più l'impronta
diventa **`8f86eb032d0113c0`**.

| # | Controllo | Esito |
|---|---|---|
| 1 | **senza il flag i mondi sono bit-identici** a quelli della griglia | **153 file su 153 identici**: base (mondi 42, 101, 107), sanità, pause2, casuale2, geo e calendario a 2 e 4 giri, 17 file ciascuno. **Cancello superato** |
| 2 | nelle celle trattate la spesa è **esattamente 0** su tutti e sette i canali; fuori da quelle celle è quella del mondo base | **8 mondi su 8**: massimo della spesa nelle 80 celle trattate = 0,00 EUR su ognuno dei sette canali; fuori dalle celle trattate, uguaglianza valore per valore con il mondo base |
| 3a | `beta` ed `ec` identici al mondo base (in memoria, precisione di macchina) | scarto relativo massimo **0,0** su 7 canali × 8 mondi, per entrambi |
| 3b | `K = beta × pop × mg` ricavato **dai file** (`contributo_vero` / `hill`, per regione, come rapporto di somme) contro quello del mondo base | scarto relativo massimo **1,17·10⁻⁴**, limitato dai 4 decimali con cui `contributo_vero.csv` è scritto |
| 4a | verità ricalcolata dal generatore contro **calcolo analitico indipendente** (adstock e Hill riscritti nello script di controllo, non importati) | scarto relativo massimo **7,1·10⁻¹⁷**, cioè la precisione di macchina. **Sotto la soglia di 10⁻⁶** |
| 4b | lo stesso, partendo dai CSV committati | scarto relativo massimo **1,24·10⁻⁴**, di nuovo il limite dei 4 decimali |
| 5 | impronta del generatore e impronta dei dati per mondo | sotto |

**Scostamento dichiarato dal mandato: anche `ec` è congelato, non solo `beta`.** Il mandato chiedeva
di tenere fisso `beta`. Ho congelato anche la mezza saturazione `ec`, che il generatore ricava dalla
media delle impression del canale (`ec = ec_mult × media(impression totali)`): con meno spesa
scenderebbe, la curva di Hill si sposterebbe a sinistra, e il disegno tornerebbe a misurare meno di
quello che deve, perché il metro si muoverebbe insieme alla cosa misurata. `ec` è una proprietà del
mondo, non del disegno — è la stessa ragione per cui D11 tenne ferma la mezza saturazione. Lo
scostamento è dichiarato qui, prima dei fit, ed è verificato: differenza relativa fra gli `ec` del
mondo blackout e quelli del mondo base **0,0 esatto su 7 canali × 8 mondi** (controllo 3a).

**Sul controllo 3b e 4b.** La soglia di 10⁻⁶ chiesta dal mandato è raggiunta e superata dalla strada
in memoria (4a): 7,1·10⁻¹⁷. Dai file non è raggiungibile e non lo sarebbe per nessun disegno, perché
`contributo_vero.csv` è scritto a quattro decimali: lo scarto di 1,2·10⁻⁴ è l'arrotondamento del
file, non una discrepanza del calcolo. Le due strade si riportano entrambe, con la loro soglia:
10⁻⁶ in memoria, 10⁻³ dai file. È lo stesso fenomeno che D11 documentò sulla costanza di `K`.

**Impronte dei dati** (sha256 dei sette file media, primi 16 caratteri), registrate adesso e pretese
uguali a ogni rilancio:

| Mondo | Base (D0) | Blackout (D12) |
|---|---|---|
| 42 | `30c5878df3ceb2e9` | `b7a2b625ffc9a013` |
| 101 | `2ad5692c92073a84` | `3e38f6094c971e73` |
| 102 | `d7343683106cc733` | `bcdc71db6de83d0f` |
| 103 | `5d862ed24917080a` | `3344de3e4d92076b` |
| 104 | `2bcb3398ff31fcf6` | `1fe997b5fff4ca92` |
| 105 | `05e482959e3731ac` | `7a82a2ac3a699853` |
| 106 | `436f68df7f639a49` | `3d384d0dbf49f577` |
| 107 | `50551d3535038789` | `519fd7724e81cc08` |

**Quota vera per mondo**, dalla verità ricalcolata, da usare come denominatore di `E`:

| Mondo | 42 | 101 | 102 | 103 | 104 | 105 | 106 | 107 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Quota vera (%) | 17,9884 | 17,9818 | 17,9796 | 18,0232 | 18,0180 | 17,9409 | 18,0364 | 17,9399 |

## 9. Cosa viene consegnato

1. Questa pre-registrazione, **con la sua data, committata prima** di generare qualunque mondo per i
   fit e prima del primo fit.
2. La patch **G6** al generatore, come diff unificato applicabile a fuzz 0, con l'impronta del
   risultato e la prova del controllo 1.
3. Il runner **R8** (= R7 + disegno `blackout` + `--controllo-baseline` per D13), con l'autotest.
4. Il notebook `colab_griglia_D12.ipynb`, sullo stesso impianto di `colab_griglia.ipynb`: pre-volo
   con cancello di fedeltà, fit, CSV di riepilogo, canali, verifiche e impronte, draw compressi.
5. Un file di risultati **separato**, con il ramo calcolato in prima riga, la previsione dichiarata
   confermata o smentita, e la tabella del costo del §6.
6. Le righe nuove per le tabelle delle Sezioni A.2 e A.3 dell'Appendice A, nello stesso formato.

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
