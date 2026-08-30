# Marketing Mix Modeling per il budget digitale nel recruiting

Codice, notebook e dataset di una tesi magistrale sul Marketing Mix Modeling
bayesiano geo-gerarchico applicato alla spesa pubblicitaria di un'agenzia per il
lavoro. Il modello (Google Meridian) stima il ritorno incrementale di ogni
canale su un panel **regione × settimana** e propone la ripartizione del budget
trimestrale.

> **I dati in questo repository sono simulati.** Non sono dati aziendali. Sono
> generati da `genera_dati_simulati.py` con seed fisso e dichiarati come tali
> nel testo della tesi. Vedi [`dati_simulati/README.md`](dati_simulati/README.md)
> per come sono costruiti e su quali parametri sono calibrati.

Descrizione discorsiva di architettura e scelte modellistiche:
[`ARCHITETTURA.md`](ARCHITETTURA.md).

---

## Cosa si può fare con questo repository

Tre cose, in ordine di sforzo crescente.

**1. Rieseguire l'analisi della tesi.** Apri
[`colab_end_to_end.ipynb`](colab_end_to_end.ipynb) su Colab con GPU, puntalo su
`dati_simulati/modello/` ed esegui le celle in ordine. È il deliverable: fa
ingestion, fit, analisi, confronto col benchmark, allocazione ed export Excel.
Il gemello [`kaggle_end_to_end.ipynb`](kaggle_end_to_end.ipynb) è identico salvo
il modo di caricare i file.

**2. Verificare il risultato principale.** In `dati_simulati/verita/` ci sono i
file che dicono quanto i media hanno *davvero* generato nel mondo simulato. La
cella 10 del notebook li legge da sola, se li trova, e stampa quota stimata
contro quota vera per canale. È il controllo che sui dati reali non si può fare,
perché lì la verità non è osservabile.

**3. Rigenerare tutto da zero.** Il generatore e il verificatore sono nel repo:
`python genera_dati_simulati.py --tutte`, poi `python verifica_dati_simulati.py`.

---

## Il notebook end-to-end

È il percorso principale e si regge da solo: non richiede di aver installato
niente in locale.

| Cella | Cosa fa |
|---|---|
| 1 | dipendenze e verifica dell'ambiente |
| 2 | **CONFIG**: sinonimi colonne, regole canali, tassonomia geo, parametri del fit |
| 3–5 | ingestion generica dei file grezzi + **Checkpoint 1** (configurazione auto-rilevata) |
| 6–7 | armonizzazione e costruzione di `InputData` per Meridian |
| 8 | EDA e diagnostica di collinearità |
| 9 | **fit** MCMC (GPU, 20–40 min) |
| 10 | ROAS, contributi, curve di risposta, e la diagnostica stimato-vs-vero |
| 11 | confronto col benchmark di attribuzione |
| 12 | allocazione del budget trimestrale |
| 13 | export Excel multi-foglio |
| 14 | riepilogo: cosa è stato prodotto e cosa controllare prima di fidarsi |

Il notebook si ferma a sei checkpoint che chiedono conferma umana. Non è un
vezzo: l'ingestion è generica e deduce dai file cose (finestra temporale,
livello geografico, quale colonna è il KPI, come si mappano i canali) che vanno
guardate prima di lasciar girare quaranta minuti di MCMC.

Tutto ciò che è personalizzabile sta nella cella 2. Aggiungere un canale, un
sinonimo di colonna o una regione custom significa aggiungere una riga lì, non
toccare il codice.

---

## Cosa c'è nel repository

```
colab_end_to_end.ipynb      il deliverable: pipeline completa su Colab
kaggle_end_to_end.ipynb     lo stesso per Kaggle

genera_dati_simulati.py     costruisce il mondo simulato (seed 42)
verifica_dati_simulati.py   controlla che il mondo generato sia quello atteso
dati_simulati/              i file usati per il fit della tesi + la verita'

app_ingestion.py            app locale di ingestion (Streamlit)
results_xlsx.py             export Excel dei risultati
mmm_registry.py             registro dei run: BigQuery o CSV locali
mmm_tables.py               costruttori delle tabelle del registro

pipeline/
  generator/    mondo sintetico + ground_truth.json
  ingestion/    parser -> mappatura confermata -> GDPR -> panel canonico
  model/        Meridian: ROI, adstock, saturazione, geo-gerarchia
  allocator/    ottimizzazione budget trimestrale a due stadi
  validation/   parameter recovery e stress test
  tests/        49 test, girano offline

vm_check/                   collaudo dell'ambiente prima dei dati reali
confronto_robyn_meridian/   protocollo e notebook del confronto Robyn/Meridian
examples/                   un model_fit.json di esempio
```

---

## Il dataset simulato

`dati_simulati/` contiene i file **esatti** usati per il fit della tesi, non
solo la ricetta per rigenerarli. La riproducibilità da seed dipende dalla
versione di numpy e dalla piattaforma, e una tesi depositata non può appoggiarsi
a una promessa che scade.

| Cartella | Contenuto |
|---|---|
| `modello/` | i dodici file di input: sette canali media, il KPI, due controlli di domanda, stagionalità, popolazione |
| `benchmark/` | ROAS dichiarato dalle piattaforme e benchmark interno, per trimestre |
| `verita/` | i parametri veri della generazione, il contributo incrementale vero per canale e le candidature organiche |

Il mondo è un panel di 20 regioni × 104 settimane, 7 canali, 31 campagne. I
quattro job board sono canali **separati** e non un aggregato: la categoria non
è omogenea e i modelli d'asta sono diversi.

Le varianti diagnostiche restano fuori dal repo perché rigenerabili e non usate
per il fit: i comandi sono in [`dati_simulati/README.md`](dati_simulati/README.md).

---

## Il registro dei run

Ogni esecuzione dell'allocatore produce un workbook Excel — che circola bene ma
non si interroga. `mmm_registry.py` aggiunge una seconda destinazione senza
togliere la prima: sette tabelle in formato lungo, marcate con un `run_id`, con
seed, hash degli input e versioni delle librerie.

Serve a confrontare esecuzioni diverse, che è un'operazione che con un file solo
non si può fare. Due backend, stessa interfaccia: BigQuery se le variabili
d'ambiente ci sono, altrimenti CSV locali.

```bash
python -m pipeline.allocator.run --budget 450000 --registry local \
    --registry-label "Q1 2026 baseline"
```

Dove c'è un posterior le tabelle portano q05/q50/q95, non la sola media:
ridurre a un numero butterebbe via ciò che giustifica l'approccio bayesiano.

---

## Da terminale

```bash
pip install -r pipeline/requirements.txt

python -m pipeline.generator.run        # mondo sintetico + ground_truth.json
python -m pipeline.ingestion.run        # ingestion con conferma della mappatura
python -m pipeline.model.run            # fit Meridian (--smoke per una prova veloce)
python -m pipeline.validation.recovery  # stime vs verita'
python -m pipeline.allocator.run --budget 450000 \
    --min linkedin=50000 --max meta=250000 --quarter-start 2026-07-06

python -m pytest pipeline/tests -q
```

L'app locale di ingestion, per chi preferisce l'interfaccia:

```bash
pip install -r requirements.txt
streamlit run app_ingestion.py
```

---

## Collaudo dell'ambiente

Prima di far girare la pipeline su una macchina nuova — tipicamente una VM
cloud — `vm_check/` verifica in un comando che l'ambiente regga: pacchetti,
ingestion end-to-end su un mondo ridotto, Excel, registro dei run, uscita verso
internet, access scope dell'istanza, e infine la catena di produzione per
intero, lanciando l'allocatore vero come comando.

```bash
bash vm_check/run_check.sh --rapido
```

Esito PASS/FAIL a schermo. Dettagli e rimedi in
[`vm_check/README.md`](vm_check/README.md).

---

## Requisiti

- Python 3.11+
- Fit Meridian: GPU consigliata (su CPU il fit richiede ore)
- `pip install -r requirements.txt` per l'app locale,
  `pip install -r pipeline/requirements.txt` per la pipeline

Il fit della tesi è girato con seed 42; le versioni esatte dei pacchetti
vengono salvate a ogni esecuzione del notebook in `requirements_freeze.txt` e
nel foglio README dell'Excel.
