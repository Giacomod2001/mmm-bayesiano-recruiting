# Guida: pipeline MMM Meridian su Google Cloud aziendale (VM con GPU T4)

Aggiornata a luglio 2026. Contesto: account/organizzazione GCP aziendale
(billing gestito dall'IT). Obiettivo: replicare l'ambiente Colab su una VM,
usando `colab_end_to_end.ipynb` (alla cella dati scegli l'opzione "cartella
locale" e indica il percorso sulla VM).
Vantaggio chiave: i dati restano nel perimetro aziendale → nessun problema
di policy come con Colab.

## 1. Cosa chiedere all'IT / cloud admin (una volta sola)

Checklist da girare a chi amministra GCP:

1. **Progetto GCP** dedicato (es. `mmm-tesi`) collegato al billing aziendale,
   oppure accesso a un progetto sandbox/data-science esistente.
2. **API abilitata**: Compute Engine.
3. **Ruoli IAM** sul progetto per il tuo utente:
   - `Compute Instance Admin (v1)` (creare/avviare/fermare VM)
   - `Service Account User` (per usare il service account di default della VM)
   - `IAP-Secured Tunnel User` se l'organizzazione vieta gli IP esterni
     (molto comune in azienda: si entra in SSH via IAP, vedi §4).
4. **Quota GPU**: almeno 1x NVIDIA T4 nella regione europea consentita
   dall'organizzazione (tipicamente `europe-west1` o `europe-west4`).
   Se la quota di progetto è 0, la richiesta di aumento la fa/approva l'admin.
5. **Stima budget da comunicare**: ~20-60 $/mese di utilizzo effettivo
   (dettaglio in §5) — utile per farsi dire subito se serve un capitolo di
   spesa o un label di billing.
6. Chiedi anche se esistono **org policy** su immagini consentite o regioni:
   l'immagine che serve è `deeplearning-platform-release` (pubblica Google).

## 2. Creazione della VM (spot T4 + immagine Deep Learning)

L'immagine "Deep Learning VM" ha driver NVIDIA, CUDA, Python e JupyterLab già
pronti. Da [Cloud Shell](https://shell.cloud.google.com) (nessuna installazione
locale) o da terminale con `gcloud`:

```bash
# elenca le famiglie immagine disponibili (prendi una "common-cuXXX" recente)
gcloud compute images list --project deeplearning-platform-release \
  --filter="family~common-cu" --format="value(family)" | sort -u | tail -5

gcloud compute instances create mmm-meridian \
  --project=mmm-tesi \
  --zone=europe-west1-b \
  --machine-type=n1-standard-8 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --image-family=common-cu124 \
  --image-project=deeplearning-platform-release \
  --boot-disk-size=100GB --boot-disk-type=pd-balanced \
  --maintenance-policy=TERMINATE \
  --provisioning-model=SPOT --instance-termination-action=STOP \
  --metadata=install-nvidia-driver=True
```

Se l'org policy vieta IP esterni, aggiungi `--no-address` (e usa IAP per SSH).

Alternativa senza terminale: Console → Marketplace → **"Deep Learning VM"** →
Launch, stesse scelte (n1-standard-8, 1x T4, spot, 100 GB).

Note:
- **Spot** = ~70-90% di sconto, ma può essere spenta con 30s di preavviso.
  Con fit da 20-40 min il rischio è basso; se succede, riavvii e rilanci.
  Per il run "definitivo" togli `--provisioning-model=SPOT` (on-demand,
  ~3-4x il costo ma nessuna interruzione).
- Se la zona non ha T4 disponibili: prova `europe-west1-c`,
  `europe-west4-a/b/c`, `europe-west2-a`.

## 3. Collegarsi e lavorare

```bash
# SSH con tunnel verso JupyterLab (porta 8080 sulla Deep Learning VM)
gcloud compute ssh mmm-meridian --zone=europe-west1-b -- -L 8080:localhost:8080

# variante se la VM non ha IP esterno (IAP):
gcloud compute ssh mmm-meridian --zone=europe-west1-b --tunnel-through-iap -- -L 8080:localhost:8080
```

Poi apri **http://localhost:8080**: è JupyterLab.

1. Trascina dentro `colab_end_to_end.ipynb` e i file dati (drag & drop).
2. Terminale JupyterLab: `pip install "google-meridian==1.8.0" openpyxl statsmodels`
   (TensorFlow GPU è già nell'immagine).
3. Esegui il notebook: alla cella dati indica il percorso della cartella
   (es. `/home/tuo_utente/dati`).
4. A fine run scarichi Excel e zip da JupyterLab (tasto destro → Download)
   o dai link `FileLink` della cella finale.

In alternativa al drag & drop, per i dati puoi usare un bucket GCS aziendale:
`gsutil cp gs://bucket-mmm/dati/* ~/dati/` dalla VM.

## 4. Costi (stime luglio 2026, regione Europa)

| Voce                              | Spot           | On-demand |
|-----------------------------------|----------------|-----------|
| GPU T4                            | ~0,09-0,15 $/h | ~0,40 $/h |
| VM n1-standard-8 (8 vCPU, 30 GB)  | ~0,08-0,12 $/h | ~0,42 $/h |
| **Totale orario**                 | **~0,20-0,27 $/h** | **~0,80 $/h** |
| Disco 100 GB pd-balanced          | ~10 $/mese (si paga ANCHE a VM spenta) |

Scenario realistico: 20 sessioni × 3h in spot ≈ **12-16 $** + disco 10 $/mese.
Anche esagerando (tutto on-demand, 100h) restiamo sotto i 100 $ totali.
I prezzi spot variano di giorno in giorno: verifica sul
[calcolatore ufficiale](https://cloud.google.com/products/calculator).

## 5. Controllo spesa (buona educazione su billing aziendale)

1. **STOP alla VM quando non la usi** — a VM accesa paghi anche a vuoto:
   `gcloud compute instances stop mmm-meridian --zone=europe-west1-b`
   (per riprendere: `... start ...`; i dati sul disco restano).
2. Chiedi all'admin un **budget alert** sul progetto (es. 50 $/mese) o, se hai
   i permessi, impostalo tu: Fatturazione → Budget e avvisi.
3. A progetto finito: `gcloud compute instances delete mmm-meridian ...`
   per azzerare anche il costo del disco.
