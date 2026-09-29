# Pre-registrazione — D13: la baseline parzialmente osservata. Quanta domanda organica bisogna saper contare?

**21 settembre 2026. Definitiva.** Scritta prima di qualunque fit e prima di guardare qualunque
risultato di stima. I controlli di fedeltà del §7 sono stati eseguiti prima di chiudere questo
documento e le loro uscite sono al §8. Qualunque risultato va in un file separato.

---

## 0. Il caveat, che qui viene prima di tutto il resto

Va scritto **in prima pagina dei risultati**, non in fondo, e ripetuto accanto a ogni cifra.

**Il controllo è costruito dalla baseline vera.** Non è un dato che qualcuno potrebbe raccogliere: è
la verità del simulatore, sporcata con del rumore. Quindi D13 misura **il caso più favorevole
possibile**: è un **limite superiore** di quello che un dato reale — candidature spontanee,
segnalazioni dei dipendenti, candidati di ritorno, traffico diretto — potrebbe dare, mai una stima di
quello che darebbe. Se D13 dice che osservare il 60% della baseline dimezza l'errore, la lettura
corretta è «nemmeno osservandone il 60% in condizioni ideali si fa meglio di così», non «basta
osservarne il 60%».

**E c'è una seconda differenza, che non si attenua.** Nel simulatore la baseline è generata
indipendentemente dalla spesa dei media: qui il controllo è quindi un controllo legittimo, non un
mediatore, e includerlo non introduce bias di post-trattamento. Nel mondo reale non è così: la
pubblicità genera anche ricerca di marca e traffico diretto, quindi una parte della «domanda
spontanea» osservata è **causata** dai media. Un controllo di quel tipo, nel mondo reale, assorbe
parte dell'effetto che si vuole misurare e **sottostima** i media. È la stessa ragione per cui la
Sezione 3.5 tiene la domanda organica fuori dal modello. Le due cose vanno dichiarate entrambe, e
nessuna delle due si attenua.

---

## 1. Domanda

Quanto della domanda organica bisogna saper contare perché l'errore si dimezzi? È la domanda gemella
di D12: invece di creare il contrasto con un esperimento, si porta al modello un dato che oggi non
ha.

## 2. Disegno

**I dati media non si toccano.** Nessuna modifica al generatore, nessun flag: il mondo è il mondo
base dello stesso seme, byte per byte. Si aggiunge **una sola variabile di controllo**, costruita
dalle candidature organiche vere del mondo (`verita/candidature_organiche.csv`, colonna
`candidature_organiche_vere`):

```
c(t, g) = f * organico_vero(t, g) * exp(eps),     eps ~ Normale(0, 0,15)
```

con `eps` estratto da un rng **dedicato**, `numpy.random.default_rng(seme_mondo + 31)`, nell'ordine
in cui il file è scritto (settimana esterna, regione interna: è l'ordine del file, non una scelta
fatta adesso). Il risultato è scritto come `domanda_organica_osservata.csv` nella cartella dei dati
del modello, con colonne `settimana, regione, domanda_organica_osservata`, valori arrotondati a tre
decimali. L'ingestion generica lo riconosce da sé come file di controllo e la colonna entra nel
modello come `ctrl_domanda_organica_osservata` (§8, controllo 3).

**Tre livelli di `f`: 0,30 — 0,60 — 0,90.** Tre livelli × otto mondi (42, 101–107) = **24 fit**.

**Che cosa significano i tre livelli.** `f` è la frazione della domanda organica che l'azienda sa
contare. `f = 0,30` è il caso in cui si riesce a tracciare solo il canale spontaneo più ovvio;
`f = 0,90` è il caso in cui si conta quasi tutto. Il rumore moltiplicativo del 15% rappresenta
l'imprecisione della misura: la correlazione fra il controllo e la baseline vera resta fra 0,9719 e
0,9792 (§8), e **non dipende da `f`**, perché `f` è un fattore di scala. Quindi fra i tre livelli
cambia solo **quanta** baseline il modello vede, non **quanto bene** la vede: è esattamente la
variabile che la domanda del §1 isola.

**Tutto il resto identico alla griglia.** 96 nodi (`KNOTS_PER_QUARTER` 12), keep 2.000, 4 catene,
adapt 500, burnin 500, seme MCMC 42 su tutti i mondi, `revenue_per_kpi` 40,0, prior ROI
LogNormale(0,2; 0,9) di riferimento, stagionalità a 4 decimali.

**Nota sul numero dei controlli.** Il mondo base porta già tre controlli al modello
(`ctrl_ricerche_candidati`, `ctrl_richieste_clienti`, `ctrl_indice_stagionale`); con D13 diventano
quattro. Il runner scrive nel CSV l'elenco effettivo dei controlli entrati nel modello, riga per
riga, e si ferma se quello di D13 non c'è.

## 3. Metrica

Le stesse della griglia, calcolate dal runner sulle stesse colonne: `rapporto_mediana` (totale
sommato **dentro** ogni draw), **`E` = quota stimata − quota vera** in punti percentuali, `PIT`,
`C_tot`, e per canale `C_k`, `larghezza_relativa`, `rho_spearman`. Qui la quota vera è **18,5% in
ogni mondo**, come in tutta la griglia: i dati media e la verità non sono toccati, e il riferimento
resta quello di D0.

Il riferimento contro cui si legge tutto è **D0 sugli stessi otto mondi: `E` mediano +22,9**.

**Ammissibilità, criterio della Sezione 4.7, due cancelli:** (1) il prior non contiene la risposta;
(2) R-hat ≤ 1,1 ed ESS ≥ 100 su `roi_m` e `beta_m`. Le divergenze si riportano e da sole non
squalificano. Un run non ammissibile si riporta col suo numero e **non si rifà**.

## 4. Regola di decisione — deterministica, prima riga che corrisponde

Si legge su `E` **mediano sugli otto mondi**, livello per livello.

| # | Condizione | Ramo |
|---|---|---|
| 1 | `E(0,30)` ≤ 4,0 | **BASTA OSSERVARNE UN TERZO** |
| 2 | `E(0,60)` ≤ 4,0 < `E(0,30)` | **SERVE METÀ** |
| 3 | `E(0,90)` ≤ 4,0 < `E(0,60)` | **SERVE QUASI TUTTA** |
| 4 | `E(0,90)` > 4,0 | **OSSERVARE LA BASELINE NON BASTA** |

Si riportano sempre, senza che selezionino il ramo: **la monotonia di `E` in `f`** (cioè se
`E(0,30) ≥ E(0,60) ≥ E(0,90)`, mondo per mondo e in mediana) e **`C_tot` per livello**. Si riportano
anche `E` di D0 sugli stessi mondi come riga zero della tabella, e il rapporto `E(f)/E(D0)`.

## 4-bis. Il precedente che c'è già, e che cambia la previsione

Questa ipotesi **è già stata testata una volta**, ed è andata male. Ignorarlo e dichiarare una
previsione ottimista sarebbe scrivere contro l'evidenza che ho in mano.

**La sezione 9 di `report.md`, "Esperimento: il traffico diretto deconfonde google? NO".** Ipotesi
di allora: Google si gonfia (+40%) perché assorbe la domanda organica non modellata. Test
(`pipeline/validation/deconfound.py`, commit `ebdcf2c`): aggiunto un controllo `direct_apps`, proxy
rumoroso della domanda organica, **correlato 0,95 con le conversioni**, dichiarato «più forte del
traffico diretto reale»; confronto del fit senza e con, stesso seme.

| Canale | ROI vero | senza | con | errore prima → dopo |
|---|---:|---:|---:|---|
| google | 1,38 | 1,91 | 1,90 | +39% → +38% |
| indeed | 2,09 | 2,71 | 2,72 | +30% → +30% |
| linkedin | 0,95 | 0,71 | 0,71 | −25% → −25% |
| meta | 1,67 | 1,82 | 1,83 | +9% → +10% |

Conclusione di allora, riportata testualmente: «nessun effetto»; i controlli già presenti catturano
già la domanda organica, `direct_apps` era **ridondante**; quindi il +40% di Google non è
confondimento con l'organico ma **probabilmente collinearità fra i canali a pagamento** — spendono
tutti in alta stagione, e Google, il più grande, assorbe l'effetto condiviso. Un problema di
identificazione, non di dato mancante.

**In che cosa D13 è diverso — e non è una formalità.** Quattro differenze, di cui la prima è quella
che conta:

1. **L'oggetto non è lo stesso.** `direct_apps` era un proxy **delle conversioni** (correlazione
   0,95 *con le conversioni*), non della componente organica. Ma le conversioni sono
   `baseline + effetto dei controlli + contributo dei media`: una serie che le insegue al 95% ne
   insegue anche la parte generata dai media. Come controllo è l'oggetto sbagliato in due modi
   opposti — non isola il confondente, e la parte di sé che si muove con la spesa è esattamente
   quella che non si deve controllare. Il controllo di D13 è costruito su `organico_vero = baseline
   + effetto dei controlli`, cioè **sul confondente stesso**, che nel simulatore è generato in modo
   indipendente dalla spesa (§0). Sono due variabili diverse, non due versioni della stessa.
2. **L'impianto non è lo stesso.** La sezione 9 è del vecchio impianto: quattro canali (google,
   indeed, linkedin, meta) contro i sette di oggi, baseline a 3 nodi per trimestre contro 12, prior
   sul ROI scontato di 1,3 contro il LogNormale(0,2; 0,9) di riferimento.
3. **Un mondo solo, contro otto.** La sezione 9 misura su un seme; D13 misura su otto, e la regola
   del §4 si legge sulla mediana.
4. **La metrica non è la stessa.** Lì si guardava l'errore sul ROI canale per canale; qui `E`,
   l'eccesso di quota attribuita ai media in punti percentuali, che è la metrica di tutta la griglia.
   E soprattutto: lì il controllo c'era o non c'era, qui ce n'è **tre dosi dichiarate**, perché la
   domanda non è «serve?» ma «quanto ne serve?».

**Conseguenza, decisa adesso: la previsione cambia.** Le quattro differenze rendono D13 un test
diverso e più pulito, ma non cancellano il precedente: il test più vicino disponibile sulla stessa
ipotesi ha dato **effetto nullo**. Dichiarare che basta osservare un terzo o metà della baseline
sarebbe una previsione contro l'evidenza già in mano. La previsione del §5 si sposta perciò dal
ramo 2-3 al **ramo 3-4**.

**Da dove viene questo cambio, per esteso, perché non resti implicito.** Una prima stesura di questo
documento, redatta il 21 settembre 2026 e **mai registrata in git**, dichiarava il ramo 2-3. Rileggendo
la sezione 9 di `report.md` prima del commit, la previsione è stata spostata al ramo 3-4 per la
ragione scritta qui sopra. **Nessuna delle due versioni è stata committata prima di oggi, e nessun fit
di D13 è mai stato eseguito**: al momento in cui questo documento entra in git non esiste un solo
numero di D13, né su Drive né altrove. Il cambio è quindi un cambio di previsione *a priori*, fatto
alla luce di evidenza vecchia e già pubblicata nel repository, non un aggiustamento a risultati visti
— che è la cosa che questa pre-registrazione esiste per rendere impossibile. Lo scrivo per esteso
perché un lettore che trova in git una sola versione avrebbe ragione a chiedersi «cambiata rispetto a
cosa».

## 4-ter. La corsa fra due diagnosi, dichiarata adesso

Sul residuo ci sono **due ipotesi rivali**, e vanno messe l'una contro l'altra prima di guardare i
numeri, non dopo.

- **Ipotesi organica** (quella del mandato): i circa otto punti che restano dopo il calendario
  stanno nella domanda organica non modellata.
- **Ipotesi di collinearità** (quella della sezione 9 di `report.md`): il residuo è collinearità fra
  i canali a pagamento, che spendono tutti in alta stagione, con il più grande che assorbe l'effetto
  condiviso. È un problema di identificazione, e nessun dato in più lo risolve.

D12 e D13 insieme sono una corsa fra le due, da due strade indipendenti:

- **D12** attacca l'ipotesi organica **muovendo il livello dei media**, cioè creando il contrasto
  che oggi non c'è;
- **D13** la attacca **portando al modello il dato organico**, nel caso più favorevole possibile;
- se **entrambi** danno il ramo peggiore (D12 ramo 3, D13 ramo 4), l'ipotesi organica è esclusa da
  due strade indipendenti e la spiegazione per collinearità **vince per eliminazione**;
- se **almeno uno** dà il ramo buono (D12 ramo 1, o D13 ramo 1 o 2), l'ipotesi organica regge, e la
  sezione 9 va riletta come un **falso negativo dovuto al proxy debole** descritto al §4-bis.

Questa lettura è fissata adesso e **non si negozia dopo**: in particolare non è ammesso, a risultati
visti, dichiarare vincente la collinearità sulla base di un solo disegno, né salvare l'ipotesi
organica invocando differenze di impianto che qui sono già elencate.

## 5. Previsione dichiarata

**Previsione: ramo 3 o 4.** Cioè: osservare la baseline aiuta poco, e o serve quasi tutta
(`f = 0,90`) o non basta nemmeno quella. `E` monotono decrescente in `f`.

Questa previsione sostituisce quella della prima stesura di oggi (ramo 2-3), mai registrata in git;
il §4-bis dice per esteso da dove viene il cambio e attesta che nessun fit di D13 è stato eseguito
prima di questo documento.

Il motivo è il precedente della sezione 9: il test più vicino disponibile sulla stessa ipotesi ha
dato effetto nullo, e la spiegazione data allora — i controlli già presenti bastano, il residuo è
identificazione e non informazione mancante — è una spiegazione che D13 non può smentire a metà. O
il dato organico vero porta informazione che il proxy non portava, e allora si vede già a `f` basso,
oppure non la porta, e allora non la porta nemmeno a `f` alto.

**Cosa la smentirebbe: il ramo 1 o il ramo 2.** Direbbero che l'informazione c'era e che la sezione 9
l'aveva mancata perché il suo proxy era l'oggetto sbagliato. Sarebbe il risultato più utile di tutti
per il capitolo 7, perché trasformerebbe un limite dichiarato in una raccomandazione operativa: si
raccolga la domanda spontanea. Va cercato con onestà, e il caveat del §0 resterebbe comunque valido
accanto a ogni cifra.

**La smentisce anche una non monotonia** — `E` che non scende al crescere di `f`, o che risale:
indicherebbe un problema di specificazione e non di informazione, e in quel caso il ramo si calcola
comunque ma la lettura è un'altra e va scritta come tale.

## 6. Cosa NON è ammesso dopo aver visto i risultati

1. Spostare la soglia di 4,0 o i confini dei rami, o aggiungerne.
2. Aggiungere, togliere o cambiare i livelli di `f`; aggiungere un quarto livello «per vedere».
3. Cambiare la deviazione standard del rumore (0,15) o il seme del rng dedicato (`seme + 31`).
4. Aggiungere mondi, toglierne, o rifare un run non ammissibile.
5. Presentare `E(f)` come stima di quello che un dato reale darebbe: è un limite superiore (§0).
6. Omettere, attenuare o spostare in fondo il caveat del §0, o una delle sue due parti.
7. Leggere una non monotonia come rumore senza riportarla.
8. Rinegoziare la corsa del §4-ter dopo aver visto i numeri: dichiarare vincente la collinearità
   sulla base di un solo disegno, o salvare l'ipotesi organica invocando differenze di impianto
   diverse da quelle già elencate al §4-bis.
9. Tornare alla previsione ramo 2-3 della prima stesura, o presentarla come se fosse quella
   registrata.

## 7. Controlli di fedeltà — eseguiti prima di chiudere questo documento

| # | Controllo | Esito |
|---|---|---|
| 1 | **con `f = 0` il run riproduce D0** dello stesso mondo | Con `f = 0` il runner **non scrive alcun file**: la cartella dei dati è quella del mondo base, byte per byte, e il run è D0 per costruzione, a tutte le cifre e non solo alla quarta. Verificato su 8 mondi. (Una colonna di soli zeri non sarebbe un controllo: l'ingestion la scarterebbe e leggerebbe il file come elenco di eventi, aggiungendo un candidato KPI. Non scriverlo è l'unica scelta sicura, ed è dichiarata qui.) |
| 2 | **spesa, impression, clic e KPI bit-identici al mondo base** in tutti i 24 run | **12 file su 12 identici** in tutte e 24 le combinazioni mondo × livello: i sette file media, `candidature_settimanali.csv`, i due controlli del mondo base, `stagionalita.csv`, `popolazione_regioni.csv`. L'unico file che cambia è quello nuovo |
| 3 | **la colonna di controllo entra come `control` e non come media** | Verificato eseguendo le CELLE 2, 3, 5 e 6 del notebook congelato `colab_end_to_end.ipynb` — le stesse che esegue il runner — sul mondo 42 con `f = 0,60`. Senza: controlli `ctrl_ricerche_candidati, ctrl_richieste_clienti, ctrl_indice_stagionale`. Con: gli stessi **più `ctrl_domanda_organica_osservata`**. Canali di modello invariati (gli stessi sette), 20 geo × 104 settimane invariati, KPI totale identico (855.534). Il runner ripete questa guardia a ogni run e si ferma se la colonna non è fra i controlli o se finisce fra i canali |

**Diagnostica del controllo, calcolata adesso su tutti e 24 i casi** (non seleziona nulla, si
riporta):

| Livello `f` | Rapporto somma controllo / somma baseline vera | Correlazione con la baseline vera |
|---|---|---|
| 0,30 | 0,3016 – 0,3044 | 0,9719 – 0,9792 |
| 0,60 | 0,6032 – 0,6088 | 0,9719 – 0,9792 |
| 0,90 | 0,9048 – 0,9131 | 0,9719 – 0,9792 |

La correlazione non dipende da `f`, come atteso da un fattore di scala; il rapporto è leggermente
sopra `f` perché `E[exp(eps)] = exp(0,15²/2) = 1,0113`. Entrambe le cose sono proprietà del disegno,
dichiarate qui prima dei fit.

## 8. Cosa viene consegnato

1. Questa pre-registrazione, **con la sua data, committata prima** del primo fit.
2. Il runner **R8** (= R7 + `--controllo-baseline` + disegno `blackout` per D12), con l'autotest e la
   guardia del controllo 3.
3. Il notebook `colab_griglia_D13.ipynb`, sullo stesso impianto di `colab_griglia.ipynb`: pre-volo
   con cancello di fedeltà, 24 fit, CSV di riepilogo, canali, verifiche e impronte, draw compressi.
4. Un file di risultati **separato**, con il caveat del §0 in prima pagina, il ramo calcolato in
   prima riga, la previsione dichiarata confermata o smentita, e la monotonia riportata.
5. Le righe nuove per le tabelle delle Sezioni A.2 e A.3 dell'Appendice A, nello stesso formato.

---

*Documento di pre-registrazione. Qualunque risultato va in un file separato.*
