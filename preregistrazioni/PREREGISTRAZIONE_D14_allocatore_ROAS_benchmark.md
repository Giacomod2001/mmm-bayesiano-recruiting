# Pre-registrazione — D14: allocare il budget con i ROAS del benchmark interno

**24 settembre 2026. APPROVATA da Giacomo il 24/9**, con le risposte al §13 e le aggiunte (a) al §5
e (b) al §8. La bozza verificata aveva sha256
`18f6498e4cd6cbba7298520460cb58b3c2398cba4197dfacd1c04a5f9987c9b0`. Questa versione si congela
prima del run: nessun calcolo di D14 è stato fatto prima del congelamento. I risultati andranno in un
file separato, scritto dopo il run.
Scadenza: tutto chiuso entro il 27/9, data di congelamento degli esperimenti.

Decisioni di Giacomo (24/9): parte A e parte B; solo il benchmark interno, niente ROAS di
piattaforma; il risultato entra nella tesi con un paragrafo nella Sezione 6.3, che scrive lui.

---

## 0. Dichiarazione preliminare: questa pre-registrazione NON è cieca

Va letto prima di tutto il resto.

Il 24/9, prima di ricevere le istruzioni di Giacomo, ho eseguito una versione preliminare di questo
studio, di mia iniziativa, dopo un suo «veloce» che ho preso per un via libera. Quella versione
aveva una pre-registrazione scritta da me e congelata prima del run (sha256
`bc601cf4a8519cb4683f87cfc3d5587e4267242c4f73009d1b13b0595f15bf52`), ma **non verificata da
Giacomo**. Differiva da questa in quattro punti:

1. usava gli 8 mondi base 42, 101–107, non gli 8 casi di D11 e R1;
2. usava come controllo nullo tutte le 5.040 graduatorie dei canali dentro lo stesso allocatore, non
   le 200 coppie casuali di R1;
3. non aveva la variante sistematica della parte B;
4. il suo script leggeva il file del benchmark per nome di colonna.

È archiviata come **annullata** e nessuna sua cifra entrerà nei risultati di D14. Ma i suoi numeri li
ho visti, e dichiaro qui quali sono, letti dai suoi CSV (`D14_risultati.csv`, `D14_tolleranza.csv`
della cartella `D14_preliminare_ANNULLATO`):

- l'allocatore sui ROAS del benchmark guadagnava in 8 mondi su 8, fra **+0,5852%** e **+1,3389%** del
  contributo vero dei media; percentile rispetto alle 5.040 graduatorie fra **0,950** e **0,981**;
  spostava fra l'**11,53%** e il **12,34%** del budget;
- lo stesso allocatore con ROAS **perfetti** (il ROI medio vero, senza distorsione) perdeva in 8 mondi
  su 8, fra **−1,2565%** e **−1,9641%**;
- con distorsioni casuali lognormali, σ da 0 a 1, la mediana del percentile stava fra **0,6452** e
  **0,7024**, e le estrazioni con guadagno positivo fra lo **0%** e il **33,0%**.

Le previsioni del §9 sono quindi **informate** da questi numeri. Le parti che nessuno ha ancora
calcolato sono: il confronto con il nullo di R1 alla cifra della regola, i conteggi sugli 8 casi di
D11/R1, e l'intera variante sistematica della parte B.

---

## 1. Domanda

**A.** Se l'allocatore usasse i ROAS del benchmark interno al posto delle stime del modello, la
ripartizione fra canali farebbe guadagnare candidature vere, e batterebbe mosse casuali della
stessa entità?

**B.** Quanto errore dell'attribuzione può tollerare quella ripartizione prima di smettere di
soddisfare il criterio di A: con errori casuali, e con l'errore sistematico realistico
dell'attribuzione (Sezione 3.5)?

## 2. I casi

Gli stessi otto di D11 e di R1, e mai altri: **D1/101, D1/103, D1/105, D1/107, D2/102, D2/103,
D10/42, D10/103**.

Per ciascun caso si usa il **mondo base, senza esperimento, del suo seme**, esattamente come D11 e R1
valutano i riparti. Il disegno (D1, D2, D10) contava in D11 e R1 solo per il fit del modello, da cui
veniva la regola 90/10; D14 non usa il fit. Ne segue un fatto da ripetere accanto a ogni conteggio:
**gli otto casi sono sei mondi distinti**, e i tre casi del mondo 103 danno per costruzione lo stesso
identico risultato. Accanto al conteggio sugli 8 casi si riporta, solo come descrizione, quello sui 6
mondi distinti.

## 3. La macchina e il cancello

- **Generatore**: quello del pacchetto D11 (`D11/g5/genera_dati_simulati.py`, cancello
  c57be0b1e94c0bbd + patch G5), senza modifiche.
- **Valutazione**: come D11 e R1. Contributo incrementale vero dei media, in candidature, sulla
  superficie di risposta vera con `beta` fisso al mondo non modificato. Un riparto moltiplica la
  spesa di ogni canale per un fattore costante nel tempo e nelle regioni. Il pavimento di LinkedIn non
  si applica, come in D11 e R1.
- **Dati del benchmark**: per ciascuno dei 6 semi il generatore scrive il mondo base con le sue
  funzioni di scrittura (benchmark e verità) in una cartella di D14. Il ROAS del benchmark di un
  canale è la somma sul biennio delle candidature attribuite, per 40 €, diviso la somma della spesa,
  entrambe lette dal file trimestrale del benchmark interno. Il file si legge **per posizione**:
  nessun nome di colonna del file benchmark compare nel codice o nei documenti di D14.
- **ROI medio vero** (parte B): candidature incrementali vere del canale sul biennio, per 40 €, diviso
  la spesa totale del canale, dal file dei parametri di generazione scritto dal generatore per quel
  mondo.

**Cancello, prima di qualunque numero di D14.** Lo script deve riprodurre dalla tabella di D11
(`D11_risultati.csv` del pacchetto D11, la stessa della §1 di
`RISULTATI_D11_riparto_controfattuale_2026-09-17.md`), per ciascuno degli otto casi:

- il contributo vero del non fare niente entro **±0,5 candidature**;
- il guadagno percentuale dell'allocatore del modello entro **±0,010 punti percentuali**.

Sono le tolleranze del cancello di R1 (§2-bis). Si verifica inoltre che, per ogni canale e ogni seme,
il ROAS del benchmark letto dal file coincida entro lo **0,1%** con quello che il generatore ottiene
dal contributo vero per il fattore di distorsione del canale: la differenza ammessa è solo
l'arrotondamento a candidature intere del file trimestrale.
**Se il cancello non passa, D14 si ferma, si riporta di quanto e dove, e non si legge nient'altro.**

## 4. La regola: l'allocatore alimentato dai ROAS

Budget totale fisso; ogni canale fra **−30% e +30%** della propria spesa attuale, come l'allocatore
del modello.

Il ROAS è un rendimento **costante**: una retta, senza curva di saturazione. Massimizzare
Σ ROAS_c · spesa_c sotto questi vincoli è un problema lineare, e la soluzione sta **agli estremi
della banda**: tutti i canali partono da −30%; il budget così liberato, il 30% del totale, va ai canali
in ordine di ROAS decrescente, ciascuno fino a +30%; un solo canale resta a un valore intermedio.
Conta quindi **solo l'ordine** dei canali secondo il ROAS, non la sua entità.

**Pareggi.** Due o più canali con ROAS identico in doppia precisione formano un blocco; se il blocco
riceve solo una parte del budget residuo, la parte si divide in modo che tutti i membri abbiano la
**stessa variazione percentuale**. Con ROAS calcolati da somme di candidature e di spesa un pareggio
esatto è improbabile; la regola si dichiara comunque adesso.

## 5. I confronti, tutti valutati sulla risposta vera

| | Riparto | Fonte |
|---|---|---|
| (a) | non fare niente | 0 per definizione |
| (b) | **regola D14**: allocatore sui ROAS del benchmark | calcolato qui |
| (c) | allocatore del modello (Sez. 5.5) | **numeri di D11**, da `D11_risultati.csv` del pacchetto D11 (tabella §1 di `RISULTATI_D11_riparto_controfattuale_2026-09-17.md`); ricalcolati solo nel cancello |
| (d) | **nullo di R1**: 200 mosse casuali | vedi sotto |
| (e) | oracolo: la migliore delle 42 coppie ordinate alla stessa cifra | come R1 |

**(d) Il nullo, con la definizione di R1.** 200 coppie casuali (canale che riceve ← canale che cede)
fra le 42 ordinate. Ogni coppia sposta **la stessa cifra in euro che la regola D14 sposta in quel
caso**, cioè metà della somma dei valori assoluti delle variazioni in euro. Generatore di numeri
casuali `numpy.random.default_rng(20260917 + seme)`, lo stesso di D11 e R1. Una coppia in cui il
canale che cede non ha abbastanza spesa si scarta e se ne estrae un'altra, come in D11.

**Avvertenza, dichiarata adesso.** Nel run preliminare la regola spostava circa il 12% del budget.
A questa cifra le coppie casuali escono dalla banda del ±30%, e le tre job board più piccole non
possono cedere quella somma. Il nullo di R1 è quindi una classe di mosse diversa da quella della
regola. Per questo si riporta anche, **solo come descrizione e senza che scelga il ramo**:

- (d′) **controllo nella banda**: il percentile della regola fra le 5.040 graduatorie possibili dei
  7 canali dentro lo stesso allocatore, cioè il nullo del run preliminare;
- (e′) la migliore delle 5.040 graduatorie.

**Aggiunta (a), approvata il 24/9.** A questa cifra il nullo di R1 **favorisce la regola**: una mossa
concentrata del 12% del budget su una sola coppia di canali perde spesso. Un eventuale A1 va quindi
letto insieme al controllo nella banda (d′). Quel controllo l'ho già visto nel run preliminare (§0),
e per questo non può diventare il criterio.

## 6. Metriche

- **g%**: variazione delle candidature vere in percentuale del contributo vero dei media senza
  riparto; la stessa metrica della Sezione 6.2 e di D11 e R1.
- **p**: frazione delle 200 mosse casuali con guadagno **strettamente minore** di quello della regola
  (i pareggi contano contro la regola, come in D11). p ≥ 0,90 significa battere il 90° percentile.
- **f**: guadagno della regola diviso il guadagno dell'oracolo (e).
- Euro spostati, e candidature vere guadagnate per euro spostato.

## 7. Criterio di A (fissato adesso: è il ramo 1 di R1)

Prima riga che corrisponde:

| Ramo | Condizione sugli 8 casi | Lettura |
|---|---|---|
| **A1 SUCCESSO** | g% mediano **> 0** **e** p ≥ 0,90 in **almeno 6 casi su 8** | allocare con i ROAS del benchmark guadagna e batte le mosse casuali |
| **A2** | g% mediano > 0, ma p ≥ 0,90 in meno di 6 casi | guadagna, ma non si distingue da una mossa casuale della stessa entità |
| **A3** | g% mediano ≤ 0 | non guadagna |

Si riportano sempre, senza che scelgano il ramo: i conteggi sui 6 mondi distinti, il confronto con
l'allocatore del modello caso per caso, f, (d′) ed (e′).

## 8. Parte B: tolleranza all'errore dell'attribuzione

Tutte e due le varianti partono dal **ROI medio vero** e ci applicano un errore noto. La valutazione
di ogni riparto è quella di A, con il suo nullo (d), ricalcolato alla cifra spostata da quel riparto.

**B1 — errore casuale.**
- ROAS del canale = ROI medio vero × exp(σ · z), con z normale standard, **indipendente per canale**
  (distorsione lognormale, centrata sul vero).
- Livelli: **σ = 0; 0,10; 0,25; 0,50; 0,75; 1,00**. A σ = 0,50 un canale su tre sbaglia di più di un
  fattore 1,65, in un verso o nell'altro.
- **200 estrazioni per livello.** Generatore `numpy.random.default_rng(20260924 + 1000 × i + seme)`,
  con i = 0…5 l'indice del livello. I tre casi del mondo 103 hanno quindi le stesse estrazioni, come
  devono.
- L'estrazione j di un livello, presa sugli 8 casi, forma una **replica**. Si applica il criterio di A
  a ciascuna delle 200 repliche. **Il livello soddisfa il criterio se lo soddisfa almeno la metà delle
  repliche**, cioè 100 su 200.

**B2 — errore sistematico: più credito a chi chiude il percorso.**
La Sezione 3.5 descrive il difetto realistico dell'attribuzione: premia i canali che chiudono il
percorso e assorbe in essi la domanda spontanea, mentre i canali di inizio percorso restano in ombra.
Il rumore casuale di B1 non lo rappresenta, perché ha sempre lo stesso verso per gli stessi canali.
Gruppi, dichiarati adesso con la loro motivazione (Sezioni 2.3 e 3.5):

- **chiusura, credito in più**: **Google Ads**, che «presidia la domanda esplicita»; **Indeed,
  Subito Lavoro, Jooble, Altre job board**, dove il candidato cerca l'offerta e si candida, cioè
  l'ultimo contatto prima della candidatura;
- **inizio percorso, credito in meno**: **Meta Ads**, che stimola «la domanda latente», e
  **LinkedIn Ads**, con employer branding e candidati passivi.

ROAS = ROI medio vero × exp(+δ) per la chiusura, × exp(−δ) per l'inizio percorso.
Livelli **δ = 0; 0,10; 0,25; 0,50; 0,75; 1,00**: il rapporto di credito fra i due gruppi vale 1;
1,22; 1,65; 2,72; 4,48; 7,39. È deterministico, quindi c'è un riparto per caso e per livello, e il
criterio di A si applica direttamente sugli 8 casi.

Il limite della scelta dei gruppi va detto: la Sezione 3.8 ricorda che le candidature avviate sulle
job board non passano da GA4, quindi la copertura spingerebbe le job board nel verso opposto. B2
modella solo l'effetto dell'ultimo clic, non quello della copertura.

**Soglia di tolleranza (definita adesso, uguale per B1 e B2).** Il livello più alto, partendo da
zero e senza salti, a cui il criterio di A è soddisfatto; oltre quel livello allocare con i ROAS
smette di soddisfarlo.
- Se il criterio non è soddisfatto **nemmeno al livello zero**, cioè con ROAS esatti, la soglia non
  esiste e si scrive: «nemmeno con ROAS esatti».
- Se il criterio è soddisfatto a livelli non contigui, si riportano tutti, ma la soglia resta quella
  contigua a partire da zero.
- Il livello zero di B1 e quello di B2 coincidono: sono i ROAS perfetti.

**Aggiunta (b), approvata il 24/9.** Se il livello zero fallisce, i risultati di B1 e di B2 riportano
comunque **in prima riga l'elenco completo dei livelli che soddisfano il criterio**, e non solo la
frase «nemmeno con ROAS esatti».

## 9. Previsioni (informate: vedi §0)

- **A: ramo A1.** Lo intuivano già le Tabelle 5.3 e 5.9 per il mondo 42: il benchmark mette in testa
  le tre job board piccole e in coda Meta e LinkedIn, che sono anche i primi e gli ultimi per
  rendimento marginale vero. E il run preliminare l'ha mostrato sui sei mondi. Il punto davvero
  incerto è il percentile rispetto al nullo di R1, che nessuno ha calcolato: prevedo p ≥ 0,90 in
  almeno 6 casi su 8. I fattori di distorsione del generatore sono **fissi, uguali in tutti i mondi e
  scelti da noi** (Google 1,30; Jooble 1,10; Meta 1,05; Subito Lavoro e Altre job board 0,95; LinkedIn
  0,85; Indeed 0,80, dalla tabella dei canali del generatore). **A da sola quindi non generalizza.**
- **B1: la soglia non esiste.** Il criterio non è soddisfatto nemmeno a σ = 0: con ROAS perfetti il
  g% mediano è già negativo, come nel run preliminare, qualunque sia il nullo. Prevedo che nessun
  livello lo soddisfi.
- **B2: fallisce a δ = 0 e lo soddisfa dal primo livello in cui Google supera Meta nel ROAS
  distorto; prevedo che succeda già a δ = 0,10.** Il motivo sta nella regola, non nei dati: da quel
  livello l'insieme dei canali alzati, di quello intermedio e di quelli tagliati coincide con quello
  che la regola forma con i fattori del generatore. Quindi il riparto è identico a quello di A.
  Se va così, la lettura è netta: nel simulatore il difetto realistico dell'attribuzione **aiuta** per
  caso, perché il canale di chiusura più grande, Google, ha ancora margine sulla curva (saturazione
  26,4%, Tabella 5.1), mentre quello di inizio percorso, Meta, ne ha meno (39,0%). È una proprietà dei
  parametri del generatore, non dell'attribuzione: sui dati reali niente garantisce che il verso sia
  lo stesso.

**Che cosa smentirebbe le previsioni**: A2 o A3 per la parte A; B1 soddisfatto a σ = 0; B2 non
soddisfatto a nessun livello, oppure già a δ = 0.

## 10. Limiti, dichiarati adesso e da ripetere in prima pagina dei risultati

1. **Nel simulatore il benchmark parte dal ROI vero MEDIO**, moltiplicato per un fattore fisso per
   canale. Non contiene la domanda organica assorbita dai canali tracciati né il tracciamento non
   casuale della Sezione 3.5. Il test misura quindi **il caso migliore**: se i ROAS perdono qui,
   perdono anche nella realtà; se vincono qui, nella realtà non è garantito.
2. **Cautela della Sezione 6.3**: l'accuratezza del benchmark è un parametro di costruzione. I
   fattori della parte A li abbiamo scelti noi; la parte B li sostituisce con errori noti, ma resta
   dentro lo stesso simulatore.
3. **Otto casi, sei mondi distinti** (§2): i casi non sono indipendenti.
4. **`beta` fisso**: si legge la superficie di risposta implicita nei parametri veri, non un mondo che
   il generatore produrrebbe (D11 §0, Sezione 5.10.6).
5. **Il nullo di R1 è una classe di mosse diversa dalla regola** a questa cifra (§5); il controllo
   nella banda è riportato accanto.
6. **Pre-registrazione non cieca** (§0).

## 11. Che cosa non si farà dopo aver visto i numeri

1. Spostare le soglie: 0; 0,90; 6 casi su 8; metà delle repliche; livelli di σ e δ; banda del ±30%.
2. Cambiare la regola, la finestra del ROAS (il biennio intero), i gruppi di B2, i semi o il nullo.
3. Promuovere il controllo nella banda (d′) a criterio, o il criterio a descrizione.
4. Aggiungere varianti della regola o livelli «per vedere».
5. Riportare solo una parte dei casi o dei livelli.
6. Scrivere confermata una previsione smentita: se è smentita, si scrive smentita.
7. Leggere un successo di A come prova che i ROAS reali siano adatti ad allocare (§10, punti 1 e 2).

## 12. Consegna, dopo l'OK

1. `studio_D14.py`: il cancello per primo, con i suoi numeri; poi A, B1, B2.
2. `D14_risultati.csv` (A, caso per caso), `D14_B1_tolleranza.csv`, `D14_B2_sistematico.csv`.
3. `RISULTATI_D14_allocatore_ROAS_benchmark_2026-09-xx.md`, scritto dopo il run: ramo calcolato in
   prima riga, previsioni confermate o smentite una per una, i limiti del §10 in prima pagina, e il
   run preliminare citato con la sua impronta, i quattro punti di differenza e le cifre del §0. La
   cartella `D14_preliminare_ANNULLATO` resta archiviata e non si cancella.
4. Un paragrafo proposto per la Sezione 6.3, da inserire a cura di Giacomo. `Tesi_completa_v8.md` non
   si modifica, e il blocco della 7.3 («La domanda organica non è identificabile…» e «Portata delle
   conclusioni») non si tocca.
5. Per ogni file: impronta sha256, tempo di esecuzione ed esiti, riportati così come sono.

## 13. Punti da verificare prima dell'OK — risposte di Giacomo del 24/9

1. **Casi**: gli 8 casi di D11/R1, come nella bozza, con accanto il conteggio sui 6 mondi distinti.
2. **Nullo**: come nella bozza. Criterio = nullo di R1; (d′) ed (e′) solo come descrizione.
3. **Gruppi di B2**: come nella bozza.
4. **Run preliminare**: citato anche nel file dei risultati (impronta, quattro punti di differenza,
   cifre del §0); la cartella resta archiviata e non si cancella.

Testo della bozza, lasciato com'era:

1. **«Gli 8 mondi senza esperimento, gli stessi di D11 e di R1»**: sono 8 casi su **6 mondi
   distinti** (il 103 tre volte). Questa bozza segue alla lettera gli 8 casi. L'alternativa sono gli 8
   mondi distinti 42, 101–107: per il 104 e il 106 l'allocatore del modello non ha numeri in D11 e
   andrebbe ricalcolato, quindi numeri nuovi e non di D11.
2. **Nullo**: la bozza usa quello di R1 come criterio e il controllo nella banda come descrizione
   (§5). Se preferisci l'inverso, va deciso adesso.
3. **Gruppi di B2**: job board nel gruppo di chiusura, con il limite della copertura GA4 dichiarato
   al §8.
4. **Run preliminare**: la bozza lo archivia come annullato e lo dichiara qui al §0. Dimmi se lo vuoi
   anche citato nel file dei risultati.

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
