# Collaudo della VM (`vm_check/`)

Kit per verificare, **appena la VM GCP è pronta**, che l'ambiente regga la
pipeline: pacchetti, ingestion end-to-end su un mondo sintetico ridotto,
lettura/scrittura dei file Excel, registro dei run, connettività cloud e
infine **la catena di produzione per intero**, dall'ingestion alle tabelle.
Un comando solo, esito PASS/FAIL a schermo.

È il collaudo da superare **prima di toccare i dati reali dell'azienda**: se
passa, l'unica variabile rimasta sono i dati.

Non tocca `pipeline/data/`: tutto quello che produce finisce in `vm_check/out/`.

---

## 1. Portare il repo sulla VM

Collegati alla VM (dal tuo PC o da [Cloud Shell](https://shell.cloud.google.com)):

```bash
gcloud compute ssh mmm-meridian --zone=europe-west1-b
# variante senza IP esterno:
gcloud compute ssh mmm-meridian --zone=europe-west1-b --tunnel-through-iap
```

Poi, **sulla VM**, porta dentro il repo. Tre modi, in ordine di comodità:

**a) git** (se il repo è su GitHub/GitLab aziendale)

```bash
git clone <url-del-repo> ~/tesi
cd ~/tesi
```

**b) copia dal tuo PC** — da eseguire **sul tuo PC**, non sulla VM:

```bash
gcloud compute scp --recurse "C:\Users\giaco\Claude\Projects\tesi magistrale" \
  mmm-meridian:~/tesi --zone=europe-west1-b
```

**c) drag & drop in JupyterLab** — apri il tunnel

```bash
gcloud compute ssh mmm-meridian --zone=europe-west1-b -- -L 8080:localhost:8080
```

vai su <http://localhost:8080>, trascina la cartella zippata nel file browser
e scompattala dal terminale di Jupyter: `unzip tesi.zip -d ~/tesi`.

## 2. Lanciare il collaudo

Dalla **radice del repo** (la cartella che contiene `pipeline/`):

```bash
cd ~/tesi
bash vm_check/run_check.sh --installa    # la prima volta: installa pandas/numpy/openpyxl
```

Le volte successive basta:

```bash
bash vm_check/run_check.sh          # collaudo standard, ~1 minuto
bash vm_check/run_check.sh --rapido # versione veloce (13 settimane)
```

Se hai già un ambiente virtuale (`~/mmm-venv`, quello di `setup_vm.sh`) lo
script lo trova da solo: non serve attivarlo a mano.

**Per collaudare anche BigQuery e il bucket** (facoltativo: senza queste
variabili quei controlli restano `[skip]` e il resto gira lo stesso):

```bash
export MMM_BQ_PROJECT=mmm-archivio          # il progetto-archivio
export MMM_BQ_DATASET=mmm_output            # facoltativo
export MMM_GCS_BUCKET=mmm-archivio-dati     # facoltativo
bash vm_check/run_check.sh
```

Il collaudo scrive un run vero su BigQuery e lo rilegge: è l'unico modo di
sapere che ruoli **e** access scope sono a posto entrambi. Le righe restano
etichettate `collaudo-vm` e il report stampa la query per cancellarle.

Da JupyterLab: `File → New → Terminal` e incolli gli stessi comandi. In una
cella di notebook funziona pure `!bash vm_check/run_check.sh --rapido`.

## 3. Leggere l'esito

```
[ OK ]  controllo superato
[warn]  non blocca: tipicamente GPU assente o pacchetti che servono solo al fit
[skip]  controllo rimandato (manca un prerequisito facoltativo)
[FAIL]  da sistemare prima di lavorare
```

In coda compare il riepilogo `26 ok · 6 avvisi · 1 saltati · 0 falliti`.
Lo script esce con codice 0 se non c'è nessun FAIL, 1 altrimenti.

File prodotti in `vm_check/out/`:

| File | Cosa contiene |
|---|---|
| `report_check.txt` | il report completo, da allegare o incollare |
| `ultimo_check.log` | stessa cosa, così com'è apparso a schermo |
| `prova_workbook.xlsx` | workbook di prova (2 fogli, formato valuta) |
| `mondo_prova/` | export grezzi + canonici generati per il test |
| `registro_prova/` | le sette tabelle del registro scritte in CSV dal collaudo |
| `produzione/` | l'esecuzione completa: Excel di prova, grafici, registro, `model_fit.json` |

## 4. Cosa viene controllato

**Ambiente** — Python ≥ 3.10; pandas, numpy, openpyxl (obbligatori); pytest,
statsmodels, matplotlib, pdfplumber, TensorFlow, Meridian (facoltativi);
GPU vista da TensorFlow; CPU, RAM, spazio disco; permessi di scrittura;
importabilità del pacchetto `pipeline`.

**Ingestion** — genera un mondo sintetico ridotto (9 export "sporchi": csv con
separatori e decimali italiani, csv.gz con PII finte, due .xlsx), propone la
mappatura, esegue l'ingestion in batch, valida i fatti contro lo schema
canonico, verifica che nei canonici non finisca nessun dato personale e
confronta i totali di `spend` e `conversions` con i canonici veri
(`canonical_true`): scarto atteso ≈ 0%.

**Excel** — legge i due export .xlsx, scrive un workbook multi-foglio con
`results_xlsx.write_sheet`, riscrive un foglio già esistente verificando che
gli altri restino, rilegge e controlla che valori e formato valuta `#,##0 €`
siano conservati.

**Registro e connettività cloud** — costruttori delle tabelle di `mmm_tables`
(quantili del ROI, fattore k, riconoscimento del vincolo attivo); un run
completo sul backend locale con tutte e sette le tabelle; due run consecutivi
che devono restare distinguibili, che è poi il confronto fra trimestri.
Poi i tre controlli che riguardano la VM in quanto tale:

- **uscita verso internet** — una connessione a `pypi.org:443`. Se fallisce e
  la VM è senza IP esterno, manca Cloud NAT sulla subnet: senza, `pip install`
  non funziona e il notebook non parte dalla prima cella.
- **access scope dell'istanza** — letti dal metadata server. Sono un controllo
  *indipendente* dai ruoli IAM: con gli scope di default Cloud Storage è in
  sola lettura e BigQuery è irraggiungibile anche avendo tutti i permessi.
  È l'errore più insidioso, perché non assomiglia a un problema di permessi.
- **BigQuery e bucket** — se le variabili d'ambiente ci sono: connessione,
  scrittura di un run reale, rilettura, e sul bucket un ciclo
  scrivi/rileggi/cancella.

**Catena di produzione** — l'ultimo blocco mette in fila tutto il resto e lo
esegue davvero. Riusa i canonici appena generati dall'ingestion, costruisce un
riepilogo posterior coerente a partire dalla `ground_truth.json` del mondo
sintetico, e poi lancia **l'allocatore vero come comando**
(`python -m pipeline.allocator.run`), non una sua imitazione: si collauda ciò
che verrà eseguito davvero, con gli stessi flag. Verifica poi che l'Excel
contenga i fogli attesi, che il budget sia conservato dall'ottimizzatore, che
le sette tabelle del registro siano state scritte, e che il vincolo
manageriale imposto in partenza arrivi intatto fino alla colonna
`constraint_active` — la prova che la catena non perde semantica per strada.
Se BigQuery è configurato, le stesse righe vengono rilette da lì.

Il fit MCMC vero dura 20-40 minuti e non appartiene a un collaudo. Con
`export MMM_CHECK_FIT=1` viene comunque eseguita una versione minuscola
(`--smoke`) solo per provare che Meridian giri su questa macchina: le stime
che produce non sono utilizzabili.

Tutto finisce in `vm_check/out/produzione/`: le variabili `MMM_OUTPUT_DIR` e
`MMM_WORKBOOK` deviano l'output della pipeline, così `pipeline/data/output/`
non viene toccato.

## 5. Se qualcosa fallisce

| Sintomo | Rimedio |
|---|---|
| `Import del pacchetto pipeline` FAIL | stai lanciando dalla cartella sbagliata: `cd` nella radice del repo |
| `pacchetto openpyxl` FAIL | `pip install openpyxl` oppure rilancia con `--installa` |
| `Python >= 3.10` FAIL | l'immagine è vecchia: usa `common-cu124` di `deeplearning-platform-release` |
| `GPU per il fit` warn | il collaudo passa comunque; per il fit servono i driver NVIDIA (`nvidia-smi` per verificare) |
| `Totale spend vs verità` FAIL | non è la VM: è la mappatura delle sorgenti nell'ingestion, guarda `mondo_prova/canonical/mapping_confirmed.json` |
| `Uscita verso internet` FAIL | VM senza IP esterno e senza Cloud NAT: va chiesto al cloud admin (vedi `ticket_global_en.md`) |
| `Access scope` warn | l'istanza è stata creata con gli scope di default: serve `cloud-platform`, si cambia a VM spenta con `gcloud compute instances set-service-account --scopes=cloud-platform` |
| `Connessione a BigQuery` FAIL con `403` | mancano i ruoli IAM sul progetto-archivio; se invece l'errore parla di *scope*, è il punto sopra |
| `Libreria google-cloud-bigquery` warn | `pip install google-cloud-bigquery google-cloud-storage`; senza, il registro scrive CSV locali e non si perde nulla |
| `Allocatore end-to-end` FAIL | leggi il messaggio in coda: quasi sempre è `scipy` mancante o un canale senza spesa nel mondo di prova |
| `Budget conservato` FAIL | problema nell'ottimizzatore, non nella VM: rilancia i test con `python -m pytest pipeline/tests -q` |
| errore inatteso in un blocco | rilancia con `bash vm_check/run_check.sh --traceback` e incolla il traceback |

## 6. Dopo il collaudo

Superato il collaudo (zero FAIL), la catena funziona end-to-end sui dati
sintetici: da lì in avanti l'unica variabile sono i dati reali. Passo
successivo: installare i pacchetti del fit e aprire il notebook.

```bash
pip install "google-meridian>=1.6" openpyxl statsmodels
```

Vedi `guida_gcp_mmm.md` (creazione VM, costi, budget alert) e `setup_vm.sh`
(venv + JupyterLab su VM generica).
