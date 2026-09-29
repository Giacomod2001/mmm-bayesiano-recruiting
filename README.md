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

**2. Verificare il risultato principale.** In `dati_simulati/verita/` ci sono i
file che dicono quanto i media hanno *davvero* generato nel mondo simulato. La
cella 10 del notebook li legge da sola, se li trova, e stampa quota stimata
contro quota vera per canale. È il controllo che sui dati reali non si può fare,
perché lì la verità non è osservabile.

**3. Rigenerare tutto da zero.** Il generatore e il verificatore sono nel repo:
`python genera_dati_simulati.py --tutte`, poi `python verifica_dati_simulati.py`.

**4. Controllare gli esperimenti.** Per lo studio di copertura, la griglia
sperimentale e le prove successive ci sono la regola di lettura fissata prima
del run, il notebook che l'ha eseguito, i file prodotti dal run e i risultati.
La mappa è nella sezione [Gli esperimenti della tesi](#gli-esperimenti-della-tesi).

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

preregistrazioni/           una pre-registrazione per disegno, prima del run
colab_copertura*.ipynb      lo studio di copertura (osservativo e randomizzato)
colab_griglia*.ipynb        la griglia sperimentale e i disegni successivi
copertura/, griglia*/       i file prodotti dai run, coi byte del run
RISULTATI_*.md              un file dei risultati per prova, scritto dopo il run
esperimenti/                i generatori dei mondi di controllo (Sez. 5.8)
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

## Gli esperimenti della tesi

La Parte III e l'Appendice A della tesi poggiano su questi file. Dalla griglia
in poi ogni prova ha una pre-registrazione in
[`preregistrazioni/`](preregistrazioni/), scritta prima del run, che fissa
domanda, metrica, soglie e previsione. Lo studio di copertura, che la precede,
ha la regola di lettura scritta nel notebook, prima del ciclo dei fit. I
risultati stanno in file separati, scritti dopo.

| Prova | Notebook o script | File del run | Risultati |
|---|---|---|---|
| Studio di copertura, osservativo | `colab_copertura.ipynb`, `studio_copertura_runner.py` | `copertura/copertura_risultati.csv` | Tabella A.4 |
| Studio di copertura, mondo randomizzato | `colab_copertura_randomizzata.ipynb` | `copertura/*_randomizzato*.csv` | Tabella A.5 |
| Griglia D0-D9 (96 fit su otto mondi) | `colab_griglia.ipynb` | `griglia/` | `griglia/griglia_riepilogo.csv` |
| D10 calendario a quattro giri | `colab_griglia_D10.ipynb` | `griglia_D10/` | `RISULTATI_D10_*.md` |
| D11 riparto controfattuale | `allocatore_D11_D11b/studio_D11.py` | `allocatore_D11_D11b/` | `RISULTATI_D11_*.md` |
| D12 blackout totale, D13 baseline osservata | `colab_griglia_D12.ipynb`, `colab_griglia_D13.ipynb`, `analisi_D12_D13.py` | `griglia_D12/`, `griglia_D13/`, `controlli_fedelta_D12_D13/` | `RISULTATI_D12_*.md` |
| R1 riallocazione | `riallocazione_R1/studio_R1.py` | `riallocazione_R1/` | `RISULTATI_R1_*.md` |
| N1 nodi della baseline | `colab_griglia_N1_nodi.ipynb`, `analisi_N1_nodi.py` | `griglia_N1/`, `controlli_fedelta_N1/` | `RISULTATI_N1_*.md` |
| Robyn a verità nota | `confronto_robyn_verita_nota/colab_robyn_mondo42.ipynb` | `confronto_robyn_verita_nota/risultati_run/` | `confronto_robyn_verita_nota/ROBYN_RISULTATI_verita_nota.md` |
| D13b baseline osservata a un nodo | `colab_griglia_D13b_1nodo.ipynb`, `analisi_D13b.py` | `griglia_D13b_1nodo/`, `controlli_fedelta_D13b/` | `RISULTATI_D13b_*.md` |
| D14 allocatore sui ROAS del benchmark | `allocatore_D14/studio_D14.py` | `allocatore_D14/` | `RISULTATI_D14_*.md` |

I notebook della griglia clonano questo repository, ricostruiscono il generatore
da `main` con le patch che portano dentro e ne controllano l'impronta prima di
generare i mondi. Poi rigenerano i dataset del mondo 42 e li confrontano con
quelli in `dati_simulati/`. Per questo `genera_dati_simulati.py` e
`dati_simulati/` non si toccano: una modifica fermerebbe quei controlli.

Le cartelle dei run sono conservate coi byte prodotti dal run. Il
`.gitattributes` impedisce a git di convertire i fine riga, perché la
conversione cambierebbe le impronte.

**Sulle date.** In questo repository i file degli esperimenti sono entrati
tutti insieme il 29 settembre 2026. Sono copiati identici dal repository di
lavoro, dove ciascuna pre-registrazione ha il commit con la sua data. Quelle
sono le date riportate nella Tabella A.11 della tesi.

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
