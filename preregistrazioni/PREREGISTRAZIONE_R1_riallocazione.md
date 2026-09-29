# Pre-registrazione — R1: sette strategie di riallocazione sugli stessi otto casi

**21 settembre 2026. Definitiva.** Scritta prima di calcolare qualunque cifra delle sette
strategie. Non è un disegno sperimentale nuovo: è una ri-analisi sui draw già prodotti, senza GPU e
senza fit. I controlli del passo 0 sono stati eseguiti prima di scrivere questo documento — sono
verifiche di **input**, che devono riprodurre CSV già pubblicati e non rivelano nulla sulle
strategie — e le loro uscite sono al §8. Qualunque risultato va in un file separato.

---

## 0. Il limite che vale per tutte e sette, e che va letto prima dei numeri

**Tutte e sette le strategie leggono il ROI MEDIO, non quello marginale.** È precisamente l'errore
diagnosticato nella sezione 3 di `RISULTATI_D11_riparto_controfattuale_2026-09-17.md`: al passo
pieno Indeed rende fra 1,02 e 1,12 euro per euro contro il 2,52 del suo ROI medio. Nessuna di queste
sette strategie può risolvere quel problema, perché nessuna dispone dei parametri delle curve di
risposta: quelli richiedono un refit che salvi Hill e adstock draw per draw, ed è il disegno M1,
separato e non ancora eseguito.

Quello che R1 può fare è un'altra cosa, ed è comunque una domanda aperta: **dato che si legge il ROI
medio, esiste un modo di leggerlo che almeno non perda?** Le sette strategie non cambiano
l'informazione, cambiano la regola di decisione che ci si costruisce sopra: cancelli di certezza,
dosi ridotte, ottimizzazione dentro il draw invece che sul collasso del posteriore. Se nessuna
funziona, il risultato è che il difetto non sta nella regola ma nell'informazione, e questo è un
risultato che vale la pena avere prima di M1, non dopo.

Questa avvertenza va in prima pagina del file dei risultati, prima di qualunque tabella.

## 1. Domanda

Esiste una regola di riallocazione che, letta su **questo** posteriore, batta il non far niente? E
se non esiste, ne esiste una che almeno eviti la perdita dell'allocatore?

## 2. Gli otto casi, e la macchina che li valuta

Gli stessi otto di D11, e mai altri: **D1/101, D1/103, D1/105, D1/107, D2/102, D2/103, D10/42,
D10/103**. Sono **sei mondi distinti**, perché il 103 compare tre volte: i casi non sono
indipendenti e la cosa va ripetuta accanto a ogni mediana.

Il riferimento, letto da `RISULTATI_D11_riparto_controfattuale_2026-09-17.md` e non ricopiato a
memoria:

| | |
|---|---|
| non far niente | riferimento, 0 per definizione |
| allocatore Meridian | perde in 8 casi su 8, fra −1,03% e −1,30%, **mediana −1,261%** |
| regola 90/10 | **mediana −0,082%**, guadagna in 3 casi su 8 (37,5%) |
| mosse casuali (nullo) | guadagnano nel 35% delle estrazioni, mediana negativa ovunque |
| oracolo | **+0,72% mediano**, cioè circa 1.140 candidature |

**Ogni riparto si valuta esattamente come in D11**: generatore con `beta` fisso al mondo non
modificato, contributo incrementale vero in candidature, stessi otto casi, stesso controllo nullo
(200 coppie casuali con la stessa cifra in euro, `numpy.random.default_rng(20260917 + seme_mondo)`),
stesso oracolo (la migliore fra le 42 coppie ordinate sotto le curve vere).

## 2-bis. Precondizione: la macchina di D11 non è nel repository

**Va dichiarato adesso perché condiziona tutto il resto.** `studio_D11.py`, la patch G5 del
generatore (`--riparto`) e il pacchetto `D11_pacchetto` **non sono nella copia di lavoro e non sono
mai stati committati** (verificato su tutta la storia di git). Nel repository ci sono solo la
pre-registrazione di D11, il suo file di risultati e `proposta_budget.py`.

Due strade, e si dichiara adesso quale si segue e con quale cancello:

**(i) Giacomo consegna il pacchetto D11.** Allora si usa quello, senza modificarlo, come chiede la
regola 6 del mandato.

**(ii) Il pacchetto non arriva e la macchina si ricostruisce.** Si scrive una patch al generatore
equivalente a G5 — lo stesso meccanismo di G6, già verificato per D12: `beta` ed `ec` tenuti fissi
ai valori del mondo non modificato, e la spesa di ogni canale scalata di un moltiplicatore
costante — e la si chiama con un nome nuovo, senza toccare niente di D11.

**Deciso il 21 settembre 2026: il pacchetto non esiste.** Giacomo ha cercato in tutto il progetto,
anche fuori da git, anche in `archivio_tesi/` e `_lavoro/`: `studio_D11.py`, la patch G5,
`D11_pacchetto`, `D11_risultati.csv` e `D11_controllo_nullo.json` non ci sono da nessuna parte.
**Si segue la strada (ii): la macchina si ricostruisce.**

> **Nota del 22 settembre 2026 — il pacchetto è stato ritrovato.** Il giorno dopo, cercando file da
> togliere dal Desktop, è emersa una cartella `03_D11b/` con `studio_D11.py`, la patch G5
> (`g5/genera_dati_simulati.py`), `D11_risultati.csv` e il pacchetto `D11_pacchetto/`, datati 21
> settembre alle 19:54. Non era nel repository ed è sfuggita alla ricerca. Ora è in
> `allocatore_D11_D11b/`, conservata come ritrovata; la provenienza è in `LEGGIMI_RITROVAMENTO.md`.
>
> **Che cosa cambia e che cosa no.** Il cancello di questo paragrafo era già stato eseguito con la
> ricostruzione, contro la tabella pubblicata di D11: sei colonne su sette esatte su tutti e otto i
> casi, e resta valido così come è stato registrato. Le sette strategie, a questa data, sono già
> state calcolate sulla macchina ricostruita, e le loro cifre non si toccano. La regola di decisione
> del §5 non è stata modificata.
>
> **Che cosa corregge.** Il codice originale calcola `p_b = (gd < gb).mean()` (riga 135): una sola
> convenzione, il minore stretto, la stessa adottata qui al §4. La differenza fra D2/103 e D10/103
> — che sono lo stesso calcolo, e per cui `D11_risultati.csv` riporta 0,56 e 0,53 — non viene quindi
> da due convenzioni diverse, come era stato ipotizzato leggendo la sola tabella, ma da **quasi-pareggi
> sciolti dall'arrotondamento**. Nel codice originale la mossa della 90/10 calcola le percentuali
> sulla spesa del file dei canali, arrotondata al centesimo (riga 81), e il controllo nullo sulla
> spesa del generatore (riga 108): per la stessa coppia di canali le due mosse differiscono
> all'ultima cifra (i riparti di D2/103 e D10/103 valgono Meta Ads −8,444655 e −8,444656), e le
> estrazioni del nullo che coincidono con la coppia della 90/10 cadono sotto o sopra il guadagno
> della regola a seconda di quella cifra. La macchina ricostruita usa una sola fonte, e i pari sono
> esatti. La mediana di `p_b` con i pareggi trattati esattamente resta **0,547**, contro lo 0,563
> pubblicato.

**Il cancello è la riproduzione della TABELLA INTERA di D11, riga per riga, non delle mediane.** Una
mediana può tornare per caso mentre i singoli casi sbagliano, e otto numeri costano quanto quattro.
Prima di calcolare una sola delle sette strategie, la macchina ricostruita deve restituire, con i
riparti del §2 di D11 e sugli stessi otto casi, questi valori — letti dalla tabella della §1 di
`RISULTATI_D11_riparto_controfattuale_2026-09-17.md`:

| Caso | `g_b` % (90/10) | `g_c` % (allocatore) | nullo, 90° perc. | `p_b` | `f_b` | EUR mossi (b) / (c) |
|---|---:|---:|---:|---:|---:|---:|
| D1/101 | −0,149% | −1,033% | +770,6 | 0,565 | −0,221 | 75.590 / 123.173 |
| D1/103 | −0,120% | −1,261% | +512,2 | 0,500 | −0,183 | 79.301 / 125.451 |
| D1/105 | +0,356% | −1,298% | +564,2 | 0,890 | 0,437 | 77.081 / 117.643 |
| D1/107 | −0,848% | −1,178% | +679,6 | 0,470 | −0,758 | 145.079 / 123.074 |
| D2/102 | +0,365% | −1,060% | +601,9 | 0,880 | 0,463 | 74.737 / 116.788 |
| D2/103 | −0,082% | −1,261% | +512,2 | 0,560 | −0,125 | 79.301 / 125.451 |
| D10/42 | +0,173% | −1,271% | +753,4 | 0,690 | 0,227 | 76.726 / 112.945 |
| D10/103 | −0,082% | −1,261% | +512,2 | 0,530 | −0,125 | 79.301 / 125.451 |

**Tolleranze, dichiarate adesso e non allargabili dopo:**

- `g_b %` e `g_c %`: **±0,010 punti percentuali** su **ciascuno** degli otto casi;
- `p_b`: **±0,010** su ciascun caso (è un percentile su 200 estrazioni, quindi il passo è 0,005);
- `f_b`: **±0,010** su ciascun caso;
- EUR mossi: **±1 EUR** su ciascun caso e su entrambe le colonne;
- il nullo, 90° percentile: **±1%** relativo su ciascun caso;
- conteggi esatti: allocatore in perdita **8 su 8**, 90/10 in guadagno **3 su 8**, `V = 3`, `S = 0`,
  `W = 8`;
- il contributo vero del non far niente: **±0,5 candidature** su ciascun caso (i valori sono nella
  tabella della §1 di D11, fra 158.329,1 e 158.330,8).

**Che cosa succede se il cancello NON passa — dichiarato adesso, prima di vederlo.** Non è «R1 è
bloccato». Se una ricostruzione fedele del metodo descritto in D11 non riproduce quei numeri, allora
**le cifre del capitolo 6 della tesi non sono riproducibili**, e questo è esso stesso un risultato,
da scrivere nei limiti del capitolo 7 con il suo nome. Le conseguenze, in ordine e senza margini di
manovra:

1. **Non si aggiusta la macchina finché torna.** Nessuna modifica alla ricostruzione motivata dal
   fatto che un numero non quadra; nessuna tolleranza allargata; nessun caso escluso.
2. Si scrive un file che riporta, caso per caso, **quanto** si scosta e in che verso, con il codice
   della ricostruzione allegato perché un terzo possa rifarlo.
3. Nel capitolo 7 si dichiara che le cifre di D11 citate nel capitolo 6 provengono da codice non
   conservato e **non sono state riprodotte**, indicando lo scarto misurato.
4. R1 si esegue **comunque**, perché le sette strategie si valutano sulla macchina ricostruita e
   confrontate fra loro; ma ogni confronto con l'allocatore e con la 90/10 di D11 porta accanto lo
   scarto del punto 2, e nessuna cifra di D11 viene citata come se fosse stata verificata.

Questo paragrafo è scritto adesso proprio perché fra due ore, davanti a un cancello che non passa,
la pressione andrebbe tutta nella direzione opposta.

## 3. Le sette strategie, in forma definitiva

Ognuna produce un **riparto**, cioè un vettore di euro spostati fra canali, che poi si valuta con la
macchina del §2.

**Definizioni comuni, fissate adesso.**

- `ROI_medio(k, d) = contributo(k, d) / spesa(k)`, con il contributo dal file dei draw e `spesa(k)`
  dalla colonna `spesa` del file per canale. È un ROI **medio** (§0).
- **Guadagno stimato** di una mossa che sposta `X` euro dal canale `B` al canale `A`, sul draw `d`:
  `X × (ROI_medio(A, d) − ROI_medio(B, d))`. È la lettura che le strategie fanno; la sua distanza
  dal guadagno vero è precisamente l'oggetto dello studio.
- **`P(A > B)`** = frazione degli 8.000 draw in cui `ROI_medio(A, d) > ROI_medio(B, d)`. Quando i
  canali che cedono sono più di uno, `B` è il loro **ROI medio pesato per gli euro ceduti**, draw
  per draw: è la definizione usata da S1 e S2 e non se ne usano altre.
- **`euro_base`** = la cifra in euro della mossa **90/10 di quel caso**, come in D11. È la stessa
  cifra usata dal controllo nullo di D11, ed è per questo che i percentili sono confrontabili. Vale
  per S1, S2, S4, S5 e S7. S3 e S6 partono invece dagli euro dell'**allocatore**, perché sono
  correzioni di quello.
- I conti si fanno in **float64** dopo aver letto i draw (§8): i file sono in float32.

| # | Strategia | Forma definitiva |
|---|---|---|
| **S1** | Freno (cancello di certezza) | Direzione e coppia della **90/10**. Si muove `euro_base` solo se `P(A > B) ≥ soglia`; sotto soglia riparto **nullo**, zero euro mossi. Tre varianti dichiarate: **0,70 · 0,80 · 0,90**, riportate tutte e tre |
| **S2** | Taglia proporzionale alla certezza | Stessa coppia della 90/10, euro mossi `= euro_base × max(0, 2 × (P − 0,5))`. Versione continua di S1 |
| **S3** | Passo ridotto | Stessa direzione e stessa selezione dell'**allocatore**, con **1/2** e **1/4** dei suoi euro. Due varianti, entrambe riportate. Serve a separare «sbaglia direzione» da «esagera la dose» |
| **S4** | Ottimizzazione dentro il draw, poi media | Per ciascuno degli 8.000 draw si sceglie la coppia migliore fra le **42 ordinate**, spostando `euro_base`; si mediano gli 8.000 riparti risultanti e si valuta **il riparto medio**. È la correzione da manuale al difetto della Sezione 6.1 |
| **S5** | Massimo del 5º percentile | Fra le 42 coppie si sceglie quella che massimizza il **5º percentile** del guadagno stimato sui draw, non la mediana. Se anche la migliore ha 5º percentile negativo, riparto **nullo** |
| **S6** | Tetto per canale | Stessa direzione dell'**allocatore**, ma nessun canale si muove più del **5% della sua spesa**. Contro la soluzione d'angolo |
| **S7** | Mossa diffusa | `euro_base` spalmato sulle **prime tre coppie** per guadagno stimato mediano, **un terzo ciascuna** |

Le varianti di S1 (tre soglie) e S3 (due passi) **non contano come strategie in più** per la regola
del §5: la regola si legge su ciascuna variante separatamente, e la severità della soglia è
giustificata al §5 proprio dal numero di tentativi.

## 4. Metriche

Per ogni strategia e ogni caso, le stesse di D11 più una:

- **`g%`** — guadagno sul contributo vero, in percentuale del non far niente;
- **`p`** — percentile dentro il controllo nullo di D11 (200 coppie casuali, stessa cifra, rng
  `default_rng(20260917 + seme_mondo)`);
- **`f`** — frazione del guadagno dell'oracolo catturata;
- **EUR mossi**;
- **nuova: euro di contributo vero guadagnati per euro spostato.**

Tabella riassuntiva con la **mediana sugli otto casi** per ogni strategia, e **tutte e sette sempre
riportate**, anche quelle che vanno male, anche quelle che non muovono mai.

## 5. Regola di decisione — deterministica, prima riga che corrisponde

| # | Condizione | Ramo |
|---|---|---|
| 1 | Almeno una strategia ha `g%` mediano **> 0** **e** percentile nel nullo **≥ 0,90 in almeno 6 casi su 8** | **QUELLA STRATEGIA FUNZIONA**: diventa la raccomandazione operativa del capitolo 7.2, con il suo numero |
| 2 | Nessuna soddisfa il punto 1, ma almeno una ha `g%` mediano **≥ −0,10%** muovendo **meno di 10.000 EUR mediani** | **IL VALORE DEL MODELLO È IL FRENO, NON IL VOLANTE**: il modello serve a capire quando NON si sa abbastanza per muoversi. Va scritto così, senza abbellirlo |
| 3 | Tutte hanno `g%` mediano **< −0,10%** | **NESSUNA RIALLOCAZIONE È DIFENDIBILE SU QUESTO POSTERIORE**: il limite del 7.3 si rafforza e il 6.4 resta l'ultima parola |

**La soglia di 6 casi su 8 con percentile ≥ 0,90 è volutamente severa**, perché le strategie sono
sette e le varianti dichiarate le portano a dieci letture sugli stessi otto casi: con dieci
tentativi, una che sembra buona per caso è attesa. Questa severità è parte della pre-registrazione e
**non si negozia dopo**.

Si riportano sempre, senza che selezionino il ramo: la mediana di `g%` di ogni strategia, la mediana
di `p`, la mediana di `f`, gli euro mossi mediani, gli euro guadagnati per euro mosso, e il
confronto con allocatore, 90/10 e oracolo di D11.

## 6. Previsione dichiarata

**Previsione: ramo 2**, con **S4 la migliore fra quelle che muovono** e **S1 a 0,80 che quasi non
muove mai**.

Il motivo è la correlazione di rango fra ordine stimato e ordine vero, che è **circa zero in tutti i
disegni**: D0 −0,04 con `E` a 22,9 punti, D1 +0,34 a 15,5, D2 +0,11 a 7,2, D10 +0,04 a 8,3, e +0,27
perfino nel mondo randomizzato dove la copertura è 8 su 8. L'errore di livello crolla da 22,9 a 7,2
punti e l'ordine resta a zero. Se il posteriore non contiene informazione sull'ordinamento, nessuna
regola che legga l'ordinamento può guadagnare: può solo ridurre l'esposizione. Questi valori vanno
**ricalcolati dai CSV della griglia** dentro R1 e non copiati da qui: la cifra ricalcolata è quella
che va in tesi.

**Cosa la smentirebbe: il ramo 1.** Direbbe che l'informazione c'era e che l'allocatore la buttava
via nel modo in cui collassa il posteriore a un valore per canale — cioè che il difetto era la
procedura e non il dato. Sarebbe il risultato più utile per il lettore aziendale, e va cercato con
onestà.

Il **ramo 3** non smentisce la previsione, la rafforza nella direzione più dura: nemmeno il freno
salva, e allora l'unica cosa difendibile è non muoversi.

## 7. Cosa NON è ammesso dopo aver visto i risultati

1. Spostare le soglie (0 · −0,10% · 0,90 · 6 casi su 8 · 10.000 EUR) o i confini dei rami.
2. Aggiungere, togliere o ritoccare una strategia dopo il primo calcolo; aggiungere una soglia a S1
   o un passo a S3 «per vedere».
3. Riportare solo le strategie che vanno bene, o relegare in nota quelle che vanno male.
4. Allargare la tolleranza del cancello del §2-bis per farlo passare.
5. Leggere il ramo 2 come un successo dell'allocazione: è il contrario, ed è il capitolo 6.4 che
   resta in piedi.
6. Presentare una qualunque cifra di R1 come una misura del rendimento marginale: tutte leggono il
   ROI medio (§0).
7. Cambiare la definizione di `euro_base`, di `P(A > B)` o del guadagno stimato dopo averne visto
   l'effetto.

## 8. Il passo 0, eseguito prima di questo documento

I draw compressi sono l'unico ingrediente nuovo. Otto file, uno per caso, 8.000 draw × 7 canali più
la colonna `totale`.

| # | Controllo | Esito |
|---|---|---|
| a | la mediana per colonna riproduce `mediana` del `_canali.csv` di quel mondo, alla quarta cifra significativa | **PASSATO, 8 casi su 8**; scarto relativo massimo **5,23·10⁻⁷** |
| b | il 5º e il 95º percentile riproducono `ci05` e `ci95` alla quarta cifra | **PASSATO, 8 casi su 8**; scarto relativo massimo **2,52·10⁻⁶** |
| c | la colonna `totale` coincide con la somma dei sette canali dentro ogni draw | **PASSATO, 8 casi su 8**: **0 draw su 64.000** oltre il limite derivato; scarto relativo massimo **2,06·10⁻⁷**, cioè 1,73 volte l'epsilon di float32 |
| d | 8.000 righe per file, nessun NaN, nessun valore negativo | **PASSATO, 8 casi su 8** |

**Un fatto sui file, trovato dal controllo (c) e da portare in tesi: i draw sono in FLOAT32.** La
prima stesura del controllo confrontava `totale` e somma **in euro**, con una tolleranza di cinque
centesimi, e falliva su tutti e otto i casi con scarti fino a 3,41 EUR. La diagnosi, fatta prima di
toccare qualunque cosa: lo scarto relativo massimo è 2,06·10⁻⁷, cioè **1,7 volte l'epsilon di
float32** (1,19·10⁻⁷); solo il 5,6% dei draw sta dentro l'arrotondamento al centesimo, quindi
l'arrotondamento non è la causa; e su totali dell'ordine di 10⁷ EUR il float32 ha una risoluzione di
circa un euro, tanto che i valori a sette cifre sono scritti senza decimali. La colonna `totale` fu
calcolata sommando i valori non arrotondati, le colonne per canale sono arrotondate al centesimo una
per una: **lo scarto è rappresentazione, non contenuto**.

**Da dove viene la soglia — e la prima risposta onesta è che la prima soglia era tarata sul dato.**
Riscrivendo il controllo avevo messo un criterio relativo a **1·10⁻⁶**, motivandolo come «otto volte
l'epsilon». Il richiamo all'epsilon era un ragionamento vero, ma quando ho scelto quel numero
**avevo già visto il 2,06·10⁻⁷**, e non posso sostenere che a occhi chiusi avrei scritto proprio
1·10⁻⁶: era un numero tondo che stava comodamente sopra ciò che avevo osservato. Va ammesso, e lo
ammetto qui.

Il criterio registrato è perciò un altro, **derivato dalle due sorgenti prima di guardare i dati**:

```
limite(draw) = 0,035 EUR            (7 canali arrotondati al centesimo: 7 x 0,005)
             + 5 x eps32 x |totale| (7 valori sommati in float32, piu' la
                                     rappresentazione del totale stesso)
```

che sugli ordini di grandezza di questi file vale **5,96·10⁻⁷ relativo**. È **più stretto** del
mio 1·10⁻⁶ e non dipende da ciò che ho osservato. **Nessuno dei 64.000 draw degli otto casi lo
supera**, e lo scarto massimo osservato è 1,73 volte l'epsilon.

Il cambio di criterio riguarda una verifica di **input** scritta da me poche ore fa, non una soglia
di decisione, e nessuna cifra delle sette strategie era ancora stata calcolata quando è avvenuto.

**Conseguenza operativa, registrata adesso:** ogni conto di R1 legge i draw e li converte in
**float64 prima** di sommare o mediare 8.000 valori. Mediare in float32 su otto casi × dieci
letture introdurrebbe un errore dello stesso ordine delle differenze che R1 misura, che sono decimi
di punto percentuale.

Lo script è `riallocazione_R1/controllo_draw_R1.py` e le sue uscite sono in
`riallocazione_R1/R1_controllo_draw.csv`.

## 9. Avvertenze obbligatorie, in prima pagina dei risultati

1. **ROI medio, non marginale** (§0). Nessuna di queste strategie può risolvere l'errore
   diagnosticato in D11: solo la macchina marginale può, ed è M1.
2. **Otto casi ma sei mondi distinti**: il 103 compare tre volte. I casi non sono indipendenti.
3. **`beta` fisso**: si valuta la superficie di risposta implicita nei parametri veri del mondo, non
   un mondo nuovo (D11 §0). È l'unica strada possibile ed è un'altra cosa.
4. **Sette strategie e dieci letture sugli stessi otto casi**: la molteplicità è reale e la soglia
   severa la governa solo in parte. Riportare tutte e sette, sempre.
5. **Il codice di valutazione di D11 non è stato conservato.** Le sue cifre, citate nel capitolo 6,
   sono state riprodotte da una ricostruzione indipendente verificata sui valori pubblicati (§2-bis).
   Va dichiarato accanto a ogni confronto con l'allocatore e con la 90/10, e va in Appendice A.
6. **I draw sono conservati in float32** (§8). Alla precisione con cui la tesi riporta quantili e
   mediane non cambia nulla, ma ogni quantità derivata va ricalcolata in float64. Anche questo va in
   Appendice A.

## 10. Cosa viene consegnato

1. Questa pre-registrazione, **con la sua data, committata prima** di calcolare qualunque cifra
   delle sette strategie.
2. `riallocazione_R1/controllo_draw_R1.py` e `R1_controllo_draw.csv`, già pronti (§8).
3. `studio_R1.py` e `riallocazione_R1/R1_risultati.csv`, con il cancello del §2-bis riportato per
   primo con i suoi numeri.
4. `RISULTATI_R1_riallocazione_2026-09-xx.md`: ramo calcolato in prima riga, previsione confermata o
   smentita, tabella delle sette strategie per gli otto casi, tabella delle mediane, le quattro
   avvertenze del §9.
5. Un paragrafo per il capitolo 6 sul fatto nuovo: ridurre l'errore di attribuzione non migliora
   l'ordinamento (la tabella `E` contro rho, **ricalcolata dai CSV**).
6. Le righe per il capitolo 7.2, nello stesso registro del testo.

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
