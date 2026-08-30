# Dataset simulato per il Capitolo 5

**Questi dati non sono dati aziendali reali.** Sono generati da
`genera_dati_simulati.py` con seed fisso. I dati reali sono bloccati da vincoli
di compliance aziendale: il Capitolo 5 viene scritto su questo dataset
sintetico e dichiarato tale.

## Cosa sta nel repo, e perché

I file usati per il fit della tesi sono **versionati**, non solo la ricetta che
li genera. La riproducibilità da seed dipende dalla versione di numpy e dalla
piattaforma: fra due anni lo stesso comando potrebbe non rigenerare file
bit-identici, e l'Appendice A promette che il repository permette di rieseguire
la pipeline. Per una tesi depositata servono i file esatti che sono stati usati.

Dentro: `modello/` (i dodici input), `benchmark/`, `verita/*.json`,
`verita/contributo_vero.csv` e `verita/candidature_organiche.csv`. Le ultime due
sono la verità sul contributo dei media e sulla baseline: sono ciò che permette
a un lettore di **verificare** il risultato principale del Capitolo 6 invece di
crederci sulla parola.

Fuori, perché rigenerabile e non usato per il fit della tesi (~15 MB): le due
varianti diagnostiche, le curve vere in PNG, i canonici del lettore B, i report
di verifica e lo zip di distribuzione.

### Rigenerare ciò che non è versionato

Dalla radice del repo. Il generatore ha seed fisso (42).

```bash
# variante diagnostica al 30%
python genera_dati_simulati.py --quota 0.30 --suffisso _diagnostica_q30
python verifica_dati_simulati.py --cartella dati_simulati/modello_diagnostica_q30                                  --suffisso _diagnostica_q30 --quota 0.30

# variante a rumore normale (riserva diagnostica, vedi Varianti)
python genera_dati_simulati.py --rumore normale --suffisso _rumore_normale
python verifica_dati_simulati.py --cartella dati_simulati/modello_rumore_normale                                  --suffisso _rumore_normale

# curve vere in PNG, canonici del lettore B e report di verifica della primaria
python verifica_dati_simulati.py

# zip di distribuzione: e' solo modello/ compressa, serve a caricarla su Colab
python -c "import shutil; shutil.make_archive('dati_simulati/dati_mmm_simulati', 'zip', 'dati_simulati/modello')"
```

`python genera_dati_simulati.py --tutte` fa in un colpo la primaria e la
diagnostica al 30%.

Attenzione: rilanciare il generatore **sulla variante primaria** sovrascrive i
file versionati. Se succede, guarda `git diff` prima di committare. Differenze
inattese non sono un dettaglio: sono il segnale che la riproducibilità da seed
si è rotta su questa macchina, che è poi la ragione per cui questi file stanno
nel repo invece di essere solo promessi.

---

## Da dove vengono i numeri

> La ripartizione della spesa tra canali e tra job board è un **parametro di
> generazione scelto per plausibilità, non una stima di quote di mercato**. Gli
> unici fatti di mercato usati sono due: Indeed è la prima per traffico nella
> categoria lavoro in Italia, e InfoJobs ha chiuso il 31 dicembre 2025 con gli
> annunci confluiti in Subito. Tutto il resto — i pesi 55/20/8/17 tra le job
> board, i livelli di spesa, i CPM, le ritenzioni, le saturazioni — è
> calibrazione dell'autore, scelta per rendere il dataset realistico e
> istruttivo, non per rappresentare il mercato.

Questa frase va riportata nel Capitolo 5: un lettore che chiede «da dove viene
quel 55%?» deve trovare la risposta scritta.

Sui parametri veri vale lo stesso principio, in un'altra direzione:

> I parametri salvati in `verita/parametri_generazione.json` servono a
> **illustrare** il comportamento del sistema, non a rivendicare una
> validazione per parameter recovery. Nel testo della tesi non si scrive mai
> «validato».

Monster non compare tra i canali: non è più operativa.

---

### Due parametri tarati dopo aver visto i numeri

Vanno dichiarati, perché sono i punti in cui il mondo simulato è stato piegato per
far funzionare la dimostrazione.

**Quota KPI di LinkedIn: da 0,015 a 0,013.** Con 0,015 il ROI vero di LinkedIn
usciva esattamente 1,00, cioè al pareggio, e il pavimento di spesa non avrebbe
avuto mordente: lo scenario non avrebbe potuto illustrare il comportamento
dell'allocatore con un vincolo attivo (Sez. 3.7). Abbassando la quota il canale
finisce sotto il pareggio (ROI 0,88) e il pavimento morde davvero.

**Griglia di calibrazione dell'accoppiamento stagionale: estremo superiore
allargato.** Su Jooble e Altre job board la correlazione tra spesa e indice
stagionale si fermava a 0,32–0,36, sotto la banda 0,40–0,60 che serve perché il
panel sia informativo senza essere collineare.

**Rumore di attribuzione intra-canale: sd 0,25.** Senza, lo Spearman tra ROAS
dichiarato e qualità vera dentro il canale era 1,00 su sei canali su sette:
l'assunzione della Sezione 3.8 sarebbe risultata vera per costruzione, e il
dataset non avrebbe dimostrato niente. La tesi sostiene una cosa più debole e
più difendibile, cioè che l'ordinamento è informativo ma imperfetto, e il
dataset deve mostrare quella. La banda obiettivo per lo Spearman medio fra
canali, 0,70–0,90, è stata fissata **prima** di vedere i risultati; la sd è
scelta sul valore **atteso su otto seed** (0,73 sui due anni), non sul valore
realizzato a seed 42 (0,86), perché con 4–6 campagne per canale una sola
realizzazione dice più sul seed che sul meccanismo.

Il rumore agisce solo sulle conversioni dichiarate dalle piattaforme: è
persistente entro il trimestre e correlato fra trimestri (un rumore bianco si
medierebbe via nell'aggregazione e l'ordinamento tornerebbe perfetto),
indipendente dalla qualità vera, e rinormalizzato dentro il canale, quindi
sposta lo split fra campagne e non il totale dichiarato di canale. Usa un
generatore casuale dedicato: spesa, impression, clic, candidature, contributo
vero e benchmark interno restano identici a quelli di prima che il meccanismo
esistesse.

Nessuno dei due tocca la stima: agiscono sul mondo generato, prima che il modello
lo veda. Ma sono interventi mirati a ottenere un risultato desiderato, quindi
dichiararli è ciò che distingue una simulation study da un risultato costruito.
Nel Capitolo 5 vanno riportati entrambi.

## Cartelle

Il notebook, in locale, chiede una cartella e la percorre **in modo
ricorsivo** prendendo tutti i `.csv .tsv .txt .xlsx .xls .json`. Da qui la
separazione in tre cartelle: tutto ciò che sta dentro la cartella puntata
entra nel modello.

### `modello/` — input del modello (cella 4 del notebook)

| file | contenuto | cosa ne fa l'ingestion |
|---|---|---|
| `google_ads_settimanale.csv` | settimana, regione, canale, campagna, spesa, impressioni, clic, conversioni_piattaforma | file media, canale `Google Ads` |
| `meta_ads_settimanale.csv` | idem | file media, canale `Meta Ads` |
| `linkedin_ads_settimanale.csv` | idem | file media, canale `LinkedIn Ads` |
| `indeed_settimanale.csv` | idem | file media, canale `Indeed` |
| `subito_lavoro_settimanale.csv` | idem | file media, canale `Subito Lavoro` |
| `jooble_settimanale.csv` | idem | file media, canale `Jooble` |
| `altre_job_board_settimanale.csv` | idem | file media, canale `Altre job board` |
| `candidature_settimanali.csv` | settimana, regione, candidature | **KPI del modello**: tutte le candidature, comprese le spontanee |
| `richieste_clienti.csv` | settimana, regione, richieste_clienti | controllo `ctrl_richieste_clienti` |
| `ricerche_candidati.csv` | settimana, regione, ricerche_candidati | controllo `ctrl_ricerche_candidati` |
| `stagionalita.csv` | settimana, indice_stagionale | controllo nazionale, propagato a tutte le regioni |
| `popolazione_regioni.csv` | regione, popolazione | pesi geografici del modello |

Le colonne sono quelle del formato richiesto all'azienda (il modulo di
richiesta dati resta fuori dal repo, ma lo schema che definisce è questa
tabella più la cella CONFIG del notebook): l'ingestion generica le riconosce
per sinonimo, senza adattamenti al codice.

`modello_diagnostica_q30/` contiene la stessa struttura con la quota dei media
al 30% invece che al 18,5% (vedi *Varianti*).

### `benchmark/` — confronto a valle (cella 11 del notebook)

Due oggetti diversi, che la tesi tiene distinti (Sez. 3.5 e 3.8).

`benchmark_interno_trimestrale.csv` — trimestre, canale, spesa,
candidature_attribuite, roas_attribuito. È il calcolo interno GA4 × database:
regola unica per tutti i canali, deduplicato, ancorato alle candidature vere.
Si ferma al livello di **canale**. È la fonte del fattore k.

`roas_piattaforma_trimestrale.csv` — trimestre, canale, campagna, spesa,
conversioni_dichiarate, roas_dichiarato. È ciò che ogni piattaforma dichiara di
aver generato, con le sue regole proprietarie e senza deduplicazione tra
piattaforme. Scende al livello di **campagna**: serve all'ordinamento
intra-canale dello stage 2, quando le UTM non arrivano al dettaglio campagna.

La copertura del benchmark interno **non è uniforme tra canali**: le
candidature che nascono dai moduli nativi in-app di Meta e LinkedIn e quelle
avviate direttamente sulle job board non passano da GA4 e arrivano al database
per altra via. È un regime di misura misto, e va dichiarato quando si legge il
confronto.

### `verita/` — mai in input al modello

`parametri_generazione.json` (i parametri veri, il ROI vero per canale, lo
scenario dell'allocatore), `contributo_vero.csv` (contributo incrementale vero
per canale × settimana × regione), `candidature_organiche.csv`,
`curve/` (un grafico per canale: spesa → candidature incrementali vere),
`report_verifica.txt` e `trascrizione_checkpoint.txt`. I primi due file sono
versionati; `curve/` e i report no, si rigenerano con
`verifica_dati_simulati.py`.

Le candidature organiche stanno qui e non tra i controlli per una ragione di
merito, non di comodo: la Sez. 3.5 le esclude dal modello perché sono un
mediatore, non un confondente (l'organico osservato è influenzato dalla
pubblicità, e controllarci sopra assorbirebbe l'effetto indiretto che si vuole
misurare). Il loro posto è a valle, nella validazione della baseline stimata.

---

## Struttura del mondo simulato

Panel **20 regioni × 104 settimane** (2024-01-01 → 2025-12-22), **7 canali**,
31 campagne, KPI = candidature settimanali per regione, intere e non negative.

I quattro job board sono canali separati e non un unico aggregato: la categoria
non è omogenea, i modelli d'asta sono diversi (pay-per-application, slot in
abbonamento, CPC puro) e le saturazioni pure. Se in stima uno dei canali
piccoli non regge, la cella 8-bis lo dice e si può riaccorpare cambiando una
riga di `REGOLE_CANALI`: un canale che collassa con intervalli larghi è un
risultato che illustra la Sez. 3.8, non un fallimento del dataset.

Ordine di costruzione:

1. **baseline organica dominante** (81,5% delle candidature): livello
   proporzionale alla popolazione, trend lento, stagionalità composita con
   picco estivo (turismo, agricoltura) e picco Q4 (logistica, GDO), con pesi
   **regionali diversi**. L'indice stagionale pubblicato nel file è la media
   nazionale pesata: la struttura regionale della stagionalità resta non
   osservata, come nella realtà.
2. **spesa**: segue la domanda ma imperfettamente (correlazione con l'indice
   stagionale calibrata a ~0,50 per ogni canale), con inerzia di
   pianificazione, gradini trimestrali di budget, campagne che si accendono e
   si spengono, settimane a spesa zero. Il riparto regionale **non è a quote
   fisse**: con quote fisse ogni regione riceverebbe lo stesso profilo scalato
   per una costante e l'identificazione tornerebbe nazionale in silenzio
   (Sez. 3.4).
3. **trasformazioni**: adstock geometrico normalizzato (`max_lag=8`) e
   saturazione di Hill, nella stessa forma funzionale che assume Meridian,
   applicati alla metrica di esecuzione (impression) scalata per quota di
   popolazione. La dispersione regionale è **solo su beta** (e
   sull'intercetta): in Meridian adstock e saturazione sono parametri
   nazionali, estrarli per regione dimostrerebbe una misspecificazione invece
   del partial pooling.
4. **rumore**: binomiale negativa sul conteggio.
5. **scenario allocatore**: LinkedIn ha un pavimento di spesa (employer
   branding) sempre attivo. Il suo ROI vero è sotto il pareggio: senza vincolo
   l'ottimizzatore lo azzererebbe, con il vincolo si ferma al paletto e
   l'eguaglianza dei rendimenti marginali vale tra i soli canali liberi
   (Sez. 3.7). Parametri pronti in `parametri_generazione.json`, campo
   `scenario_allocatore`.

Attese qualitative per canale, coerenti con la Sez. 2.3.1: Google Ads
ritenzione breve e saturazione tardiva; Indeed ritenzione breve e saturazione
**precoce** (l'audience attiva è finita); Meta ritenzione e saturazione medie;
LinkedIn la coda più lunga; gli aggregatori CPC un costo marginale più lineare.

---

## Varianti

`QUOTA_MEDIA_TARGET` in CONFIG regola la quota di candidature spiegata dai
media. La variante primaria è al **18,5%**, che è il caso realistico del
recruiting ed è anche il caso difficile. La variante `_diagnostica_q30` al 30%
serve a distinguere due diagnosi diverse nel Capitolo 6: *il metodo non
identifica* oppure *questo settore è difficile*.

Se al 18-20% gli intervalli restano larghi, **non si alza la quota per
stringerli**: si riporta come risultato.

`RUMORE = 'nb' | 'normale'` isola l'effetto dell'eteroschedasticità: la
binomiale negativa è realistica sui conteggi, ma la verosimiglianza di Meridian
è normale. Se il fit soffre, la variante normale dice se il problema è lì. È già
generata in `modello_rumore_normale/` e tenuta in riserva: non va usata per il
Capitolo 5, serve solo come controllo diagnostico.

    python genera_dati_simulati.py --rumore normale --suffisso _rumore_normale

---

## Limiti noti

- **Ordinamento intra-canale più debole nella finestra che conta.** Lo Spearman
  tra ROAS dichiarato e qualità vera è 0,73 atteso sui due anni ma 0,69
  sull'ultimo trimestre, ed è l'ultimo trimestre che lo stage 2 consuma davvero
  (`window_weeks=13` in `pipeline/allocator/campaigns.py`, il trimestre più
  recente nel notebook). L'assunzione della Sezione 3.8 si indebolisce proprio
  dove il sistema la usa. Va dichiarato nel Capitolo 5 e sta in roadmap qui
  sotto. Avvertenza di lettura: con 4–6 campagne per canale lo Spearman è
  grossolano (con 4 campagne uno scambio adiacente vale già 0,80), quindi è un
  indicatore aggregato e non un giudizio canale per canale.
- **Conteggi dichiarati arrotondati all'intero** riga per riga, come negli
  export veri: sui canali piccoli l'arrotondamento erode qualche punto
  percentuale del totale dichiarato.
- **Verosimiglianza**: il rumore generato è binomiale negativo, quello assunto
  dal modello è normale. Scelta deliberata e dichiarata, non un errore.
- **Stagionalità regionale non osservata**: il modello riceve solo l'indice
  nazionale. È realistico, ma è una fonte di errore di specificazione che il
  Capitolo 5 deve nominare.

---

## Roadmap — non riguarda il Capitolo 5

Due voci di lavoro futuro, registrate qui perché emergono da questo dataset ma
non sono limiti del dataset.

**Lo stage 2 legge una finestra troppo corta.** Il ranking intra-canale si
prende dall'ultimo trimestre, che è la finestra in cui il rumore di
attribuzione pesa di più. Allungare la finestra, o pesare più trimestri con
decadimento, renderebbe l'ordinamento più stabile a parità di dati. Voce per il
Capitolo 7.

**Il lettore B non sa leggere un KPI aggregato.** `pipeline/ingestion` (l'app
locale e `vm_check`) costruisce il fatto `outcome` solo da un file
**individuale** con dati personali. Ma il formato realmente atteso dall'azienda
— foglio `candidature` con settimana, regione e candidature, come da modulo
di richiesta dati — è **aggregato**: quindi il problema non riguarda solo il dataset
simulato, si presenterebbe identico sui dati veri dell'azienda. Nel percorso del
lettore B un file di quel tipo viene classificato come controllo di domanda
(`_demand_variable_from_filename` fa match su `candidat`) e va escluso a mano
alla conferma, insieme a `popolazione_regioni.csv`. Aggiungere al lettore B il
concetto di file di outcome aggregato è lavoro a sé, da fare se e quando l'app
locale dovrà girare sui dati reali. Il Capitolo 5 non ne dipende: gira sul
notebook.

Nota minore dello stesso percorso: il lettore B riconosce il canale dal *nome
del file* con una regex che copre `google|meta|facebook|linkedin|indeed`,
quindi i tre job board minori finiscono in `sconosciuto`.
