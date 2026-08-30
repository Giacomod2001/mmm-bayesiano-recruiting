"""
Collaudo del registro dei run e della connettività cloud.

Copre i tre punti che gli altri controlli non toccano e che, sulla VM
aziendale, sono anche i più probabili candidati a rompersi:

  * il registro in sé — costruttori di tabella e backend locale, che devono
    funzionare anche senza alcun accesso GCP;
  * l'**uscita verso internet**, cioè il problema Cloud NAT: senza egress la
    prima cella del notebook (`pip install`) non parte proprio;
  * gli **access scope** dell'istanza, che sono un controllo indipendente dai
    ruoli IAM: con gli scope di default Cloud Storage è in sola lettura e
    BigQuery è irraggiungibile *anche avendo tutti i permessi giusti*. È
    l'errore più insidioso perché non assomiglia a un problema di permessi.

I controlli cloud si attivano solo se le variabili d'ambiente ci sono; in
locale, o su una VM senza accessi, restano [skip] e non fanno rumore.

    export MMM_BQ_PROJECT=mmm-archivio
    export MMM_BQ_DATASET=mmm_output        # facoltativo
    export MMM_GCS_BUCKET=mmm-archivio-dati # facoltativo
"""
from __future__ import annotations

import os
import socket
import urllib.request

import pandas as pd

from . import _util as U

TITOLO = "REGISTRO DEI RUN E CONNETTIVITÀ CLOUD"

_METADATA = ("http://metadata.google.internal/computeMetadata/v1"
             "/instance/service-accounts/default/scopes")

#: riepilogo posterior finto, stessa forma di output/model_fit.json
_SUMMARY = {"channels": {
    "meta": {"roi": {"q05": 0.6, "q50": 0.9, "q95": 1.3}},
    "linkedin": {"roi": {"q05": 0.9, "q50": 1.6, "q95": 2.4}},
}}
_ALLOC = pd.DataFrame([
    {"channel": "meta", "hist_weekly_spend": 1000.0, "budget_quarter": 10000.0},
    {"channel": "linkedin", "hist_weekly_spend": 500.0, "budget_quarter": 50000.0},
])
_CAMP = pd.DataFrame([
    {"channel": "meta", "campaign": "dpa", "spend": 100.0, "platform_roas": 2.0,
     "k_channel": 0.5, "roas_adjusted": 1.0, "share_hist": 0.4,
     "share_proposed": 0.5, "budget_proposed": 120.0},
    {"channel": "meta", "campaign": "lead", "spend": 150.0, "platform_roas": 1.2,
     "k_channel": 0.5, "roas_adjusted": 0.6, "share_hist": 0.6,
     "share_proposed": 0.5, "budget_proposed": 120.0},
])


def _scrivi_run(REG, TB, mode: str, root: str | None, etichetta: str):
    """Un run completo del registro: tutte le tabelle, poi chiusura."""
    reg = REG.RunRegistry.start(mode=mode, local_root=root, seed=42,
                                config={"collaudo": True}, label=etichetta)
    reg.write("channel_roi", TB.channel_roi(_SUMMARY,
                                            TB.channel_platform_roas(_CAMP)))
    reg.write("allocation", TB.allocation(_ALLOC, min_spend={"linkedin": 50000.0}))
    reg.write("campaign_split", TB.campaign_split(_CAMP))
    reg.write("weekly_plan", pd.DataFrame(
        [{"week": "2026-01-05", "channel": "meta", "spend": 800.0}]))
    reg.write("response_curves", TB.response_curves(
        lambda ch, x: x * 1.5, ["meta"], {"meta": 1000.0}, n_points=8))
    reg.diagnostics({"r_hat_max": 1.01, "origine": "collaudo VM"})
    reg.finish(excel_path="collaudo.xlsx")
    return reg


def run(ctx: dict) -> list[U.Result]:
    esiti: list[U.Result] = []
    out_dir = ctx.get("out_dir", ".")
    radice_reg = os.path.join(out_dir, "registro_prova")

    # ------------------------------------------------ 1. moduli importabili
    try:
        import mmm_registry as REG
        import mmm_tables as TB
    except Exception as e:                                # noqa: BLE001
        return [U.fail("Import di mmm_registry / mmm_tables",
                       f"{type(e).__name__}: {e} — lancia dalla radice del repo")]
    esiti.append(U.ok("Import di mmm_registry / mmm_tables",
                      f"{len(REG.TABLES)} tabelle definite"))

    # ------------------------------------------------ 2. costruttori tabella
    with U.Timer() as t:
        roi = TB.channel_roi(_SUMMARY, {"meta": 1.8, "linkedin": 1.0})
        r = roi.set_index("channel")
        quantili = {"roi_q05", "roi_q50", "roi_q95"} <= set(roi.columns)
        k_meta = float(r.loc["meta", "k_factor"])
    esiti.append(U.verdict(
        "Tabella ROI: quantili e fattore k",
        quantili and abs(k_meta - 0.5) < 1e-9,
        f"q05/q50/q95 presenti, k(meta)={k_meta:.2f}",
        f"quantili={quantili}, k(meta)={k_meta:.3f} (atteso 0.50)",
        t.elapsed))

    with U.Timer() as t:
        alloc = TB.allocation(_ALLOC, min_spend={"linkedin": 50000.0}
                              ).set_index("channel")
        vincolo = str(alloc.loc["linkedin", "constraint_active"])
    esiti.append(U.verdict(
        "Tabella allocazione: vincolo attivo riconosciuto",
        vincolo == "min",
        "linkedin fermo sul minimo, come atteso",
        f"atteso 'min', ottenuto {vincolo!r}", t.elapsed))

    # ------------------------------------------------ 3. backend locale
    with U.Timer() as t:
        try:
            reg = _scrivi_run(REG, TB, "local", radice_reg, "collaudo-vm")
            attese = set(REG.TABLES)
            trovate = {tab for tab in attese
                       if os.path.exists(os.path.join(radice_reg, f"{tab}.csv"))}
            mancanti = attese - trovate
            righe = pd.read_csv(os.path.join(radice_reg, "channel_roi.csv"))
            # la tabella è in append per costruzione: dei run precedenti
            # restano le righe, quindi si verifica la presenza del nuovo
            # run_id, non che sia l'unico
            coerente = reg.run_id in set(righe["run_id"].astype(str))
        except Exception as e:                            # noqa: BLE001
            mancanti, coerente = {"?"}, False
            errore = f"{type(e).__name__}: {e}"
        else:
            errore = ""
    esiti.append(U.verdict(
        "Registro locale: run completo scritto",
        not mancanti and coerente,
        f"{len(trovate)} tabelle in {os.path.relpath(radice_reg, ctx.get('root', '.'))}",
        errore or f"tabelle mancanti: {sorted(mancanti)}; run_id coerente={coerente}",
        t.elapsed))

    # ------------------------------------------------ 4. due run confrontabili
    with U.Timer() as t:
        try:
            _scrivi_run(REG, TB, "local", radice_reg, "collaudo-vm-2")
            df = pd.read_csv(os.path.join(radice_reg, "channel_roi.csv"))
            n_run = df["run_id"].nunique()
        except Exception as e:                            # noqa: BLE001
            n_run, errore = 0, f"{type(e).__name__}: {e}"
        else:
            errore = ""
    esiti.append(U.verdict(
        "Due run convivono e restano distinguibili",
        n_run >= 2,
        f"{n_run} run nella stessa tabella — è il confronto fra trimestri",
        errore or f"trovati {n_run} run distinti, attesi almeno 2", t.elapsed))

    # ------------------------------------------------ 5. uscita internet (NAT)
    with U.Timer() as t:
        try:
            socket.create_connection(("pypi.org", 443), timeout=6).close()
            egress, dettaglio = True, "pypi.org raggiungibile"
        except OSError as e:
            egress, dettaglio = False, f"{type(e).__name__}: {e}"
    esiti.append(U.verdict(
        "Uscita verso internet (pip / Cloud NAT)", egress, dettaglio,
        f"{dettaglio} — se la VM è senza IP esterno serve Cloud NAT sulla "
        "subnet, altrimenti `pip install` non funziona", t.elapsed))

    # ------------------------------------------------ 6. access scope della VM
    try:
        req = urllib.request.Request(_METADATA,
                                     headers={"Metadata-Flavor": "Google"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            scopes = resp.read().decode().split()
    except Exception:                                     # noqa: BLE001
        scopes = []
    if not scopes:
        esiti.append(U.skip("Access scope dell'istanza",
                            "non siamo su una VM GCE (o metadata non raggiungibile)"))
    else:
        pieno = any(s.endswith("/cloud-platform") for s in scopes)
        bq = pieno or any("bigquery" in s for s in scopes)
        gcs_rw = pieno or any(s.endswith("/devstorage.read_write") or
                              s.endswith("/devstorage.full_control")
                              for s in scopes)
        esiti.append(U.verdict(
            "Access scope: BigQuery raggiungibile", bq,
            "cloud-platform" if pieno else "scope bigquery presente",
            "manca lo scope: BigQuery non è raggiungibile a prescindere dai "
            "ruoli IAM. Serve `cloud-platform` (si cambia a VM spenta)",
            soft=True))
        esiti.append(U.verdict(
            "Access scope: scrittura su Cloud Storage", gcs_rw,
            "cloud-platform" if pieno else "devstorage in scrittura",
            "lo scope di default è devstorage.read_only: dalla VM si legge "
            "ma non si scrive sul bucket. Serve `cloud-platform`", soft=True))

    # ------------------------------------------------ 7-8. BigQuery
    progetto = os.environ.get("MMM_BQ_PROJECT")
    try:
        from google.cloud import bigquery            # noqa: F401
        libreria = True
    except Exception:                                     # noqa: BLE001
        libreria = False

    if not libreria:
        esiti.append(U.warn("Libreria google-cloud-bigquery",
                            "assente: il registro userà i CSV locali "
                            "(`pip install google-cloud-bigquery`)"))
    elif not progetto:
        esiti.append(U.skip("Connessione a BigQuery",
                            "MMM_BQ_PROJECT non impostata — esporta la "
                            "variabile per collaudare anche la scrittura"))
    else:
        from google.cloud import bigquery
        with U.Timer() as t:
            try:
                client = bigquery.Client(project=progetto)
                valore = list(client.query("SELECT 1 AS uno").result())[0]["uno"]
                connesso, dettaglio = valore == 1, f"progetto {progetto}"
            except Exception as e:                        # noqa: BLE001
                connesso, dettaglio = False, f"{type(e).__name__}: {e}"
        esiti.append(U.verdict("Connessione a BigQuery", connesso, dettaglio,
                               dettaglio, t.elapsed))

        if connesso:
            dataset = os.environ.get("MMM_BQ_DATASET", REG.DATASET_DEFAULT)
            with U.Timer() as t:
                try:
                    reg = _scrivi_run(REG, TB, "bigquery", None, "collaudo-vm")
                    q = (f"SELECT COUNT(*) AS n FROM "
                         f"`{progetto}.{dataset}.channel_roi` "
                         f"WHERE run_id = '{reg.run_id}'")
                    n = list(client.query(q).result())[0]["n"]
                    scritto, dettaglio = n > 0, f"{n} righe rilette in {dataset}"
                except Exception as e:                    # noqa: BLE001
                    scritto, dettaglio = False, f"{type(e).__name__}: {e}"
            esiti.append(U.verdict(
                "Scrittura e rilettura su BigQuery", scritto, dettaglio,
                dettaglio, t.elapsed))
            if scritto:
                esiti.append(U.ok(
                    "Pulizia delle righe di collaudo",
                    f"per rimuoverle: DELETE FROM `{progetto}.{dataset}.runs` "
                    "WHERE label LIKE 'collaudo-vm%' (idem per le altre tabelle)"))

    # ------------------------------------------------ 9. bucket GCS
    bucket_nome = os.environ.get("MMM_GCS_BUCKET")
    if not bucket_nome:
        esiti.append(U.skip("Lettura/scrittura sul bucket",
                            "MMM_GCS_BUCKET non impostata"))
    else:
        with U.Timer() as t:
            try:
                from google.cloud import storage
                bucket = storage.Client().bucket(bucket_nome)
                blob = bucket.blob("vm_check/prova.txt")
                blob.upload_from_string("collaudo")
                letto = blob.download_as_text()
                blob.delete()
                okgcs, dettaglio = letto == "collaudo", f"gs://{bucket_nome}"
            except Exception as e:                        # noqa: BLE001
                okgcs, dettaglio = False, f"{type(e).__name__}: {e}"
        esiti.append(U.verdict("Lettura/scrittura sul bucket", okgcs,
                               f"{dettaglio} — scritto, riletto, cancellato",
                               dettaglio, t.elapsed))

    return esiti
