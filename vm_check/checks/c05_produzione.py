"""
Controllo 5 — la catena di produzione per intero, sul mondo sintetico.

Gli altri controlli verificano i pezzi. Questo verifica che, messi in fila,
funzionino: dai fatti canonici prodotti dall'ingestion fino all'Excel per il
decisore e alle tabelle del registro, passando per l'allocatore. È il
collaudo da superare **prima di toccare i dati reali dell'azienda**: se passa
qui, l'unica variabile rimasta sono i dati.

Come funziona
-------------
1. Riusa i canonici che il controllo ingestion ha appena generato.
2. Costruisce un `model_fit.json` a partire dalla `ground_truth.json` del
   mondo sintetico — quindi un riepilogo posterior *finto ma coerente*.
   Il fit MCMC vero dura 20-40 minuti e non appartiene a un collaudo; con
   `MMM_CHECK_FIT=1` viene comunque eseguita una versione minuscola
   (`python -m pipeline.model.run --smoke`) solo per provare che Meridian
   giri su questa macchina.
3. Lancia **l'allocatore vero**, come comando, non una sua reimplementazione:
   `python -m pipeline.allocator.run`. È il punto: si collauda ciò che poi
   verrà eseguito davvero, con gli stessi flag.
4. Verifica l'Excel, la conservazione del budget, le tabelle del registro e —
   se BigQuery è configurato — che le righe siano rileggibili da lì.

L'esecuzione scrive in `vm_check/out/produzione/` grazie alle variabili
`MMM_OUTPUT_DIR` e `MMM_WORKBOOK`: i risultati di lavoro in
`pipeline/data/output/` non vengono toccati.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pandas as pd

from . import _util as U

TITOLO = "CATENA DI PRODUZIONE (ingestion → allocator → Excel → tabelle)"

#: fogli che l'allocatore deve aver scritto nel workbook
_FOGLI_ATTESI = ("Legenda", "Canali", "Campagne", "Settimane", "Mesi")

_QUARTER_START = "2026-01-05"        # un lunedì
_WEEKS = 13


def _fit_da_ground_truth(world_root: str, out_path: str) -> dict:
    """Riepilogo posterior coerente col mondo sintetico.

    Stessa costruzione della fixture `mock_fit` dei test: si prendono i
    parametri veri del generatore e li si veste da posterior. Non è una
    stima — è un input plausibile per collaudare tutto ciò che *sta a valle*
    della stima.
    """
    gt_path = os.path.join(world_root, "ground_truth.json")
    with open(gt_path, encoding="utf-8") as fh:
        gt = json.load(fh)
    s: dict = {"channels": {}, "seed": 42,
               "note": "riepilogo sintetico per collaudo, NON una stima"}
    for ch, p in gt["channels"].items():
        roi = float(p["roi_true"])
        s["channels"][ch] = {
            "roi": {"q05": roi * 0.7, "q50": roi, "q95": roi * 1.3},
            "adstock_lam": {"q05": 0.05, "q50": float(p["adstock_lam"]), "q95": 0.9},
            "hill_ec": {"q05": 0.8, "q50": 1.2, "q95": 1.8},
            "hill_slope": {"q05": 0.8, "q50": float(p["hill_slope"]), "q95": 2.2},
        }
    s["diagnostics"] = {"r_hat_max": 1.0, "origine": "collaudo"}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=1)
    return s


def _budget_dal_mondo(canon_dir: str) -> tuple[float, dict[str, float]]:
    """Budget di collaudo pari alla spesa storica riportata a un trimestre.

    Derivarlo dai dati invece di fissarlo tiene il collaudo sensato anche
    quando il mondo di prova è più piccolo o più grande.
    """
    media = pd.read_csv(os.path.join(canon_dir, "media.csv"),
                        parse_dates=["week"])
    n = max(media["week"].nunique(), 1)
    per_ch = (media.groupby("channel")["spend"].sum() / n * _WEEKS)
    return float(per_ch.sum()), per_ch.to_dict()


def run(ctx: dict) -> list[U.Result]:
    esiti: list[U.Result] = []
    radice = ctx.get("root", ".")
    out_dir = ctx.get("out_dir", ".")
    canon_dir = ctx.get("canon_dir")
    lavoro = os.path.join(out_dir, "produzione")
    workbook = os.path.join(lavoro, "risultati_collaudo.xlsx")

    if not canon_dir or not os.path.exists(os.path.join(canon_dir, "media.csv")):
        return [U.skip("Catena di produzione",
                       "mancano i canonici: il controllo ingestion non è "
                       "arrivato in fondo")]
    try:
        import scipy                                   # noqa: F401
    except Exception:                                  # noqa: BLE001
        return [U.skip("Catena di produzione",
                       "scipy assente: `pip install scipy` (serve "
                       "all'ottimizzatore dell'allocatore)")]

    os.makedirs(lavoro, exist_ok=True)
    world_root = os.path.dirname(os.path.abspath(canon_dir))
    fit_path = os.path.join(lavoro, "model_fit.json")

    # ------------------------------------------------ 1. riepilogo posterior
    with U.Timer() as t:
        try:
            fit = _fit_da_ground_truth(world_root, fit_path)
            canali = list(fit["channels"])
        except Exception as e:                         # noqa: BLE001
            return esiti + [U.fail("Riepilogo posterior di collaudo",
                                   f"{type(e).__name__}: {e}")]
    esiti.append(U.ok("Riepilogo posterior di collaudo",
                      f"{len(canali)} canali dalla ground truth: "
                      f"{', '.join(canali)}", t.elapsed))

    # ------------------------------------------------ 2. fit vero (opzionale)
    if os.environ.get("MMM_CHECK_FIT") == "1":
        with U.Timer() as t:
            proc = subprocess.run(
                [sys.executable, "-m", "pipeline.model.run",
                 "--smoke", "--canon", canon_dir],
                cwd=radice, capture_output=True, text=True,
                env={**os.environ, "MMM_OUTPUT_DIR": lavoro})
        esiti.append(U.verdict(
            "Fit Meridian (smoke, pochi draw)", proc.returncode == 0,
            "Meridian gira su questa macchina — le stime NON sono usabili",
            (proc.stderr or proc.stdout or "").strip().splitlines()[-1:][0]
            if (proc.stderr or proc.stdout) else "errore senza messaggio",
            t.elapsed, soft=True))
    else:
        esiti.append(U.skip(
            "Fit Meridian (smoke)",
            "esporta MMM_CHECK_FIT=1 per provare anche il fit (lento)"))

    # ------------------------------------------------ 3. allocatore vero
    budget, per_ch = _budget_dal_mondo(canon_dir)
    # un vincolo che morde di sicuro: il canale più piccolo portato a un
    # quarto del budget. Serve a collaudare anche il percorso dei vincoli.
    canale_min = min(per_ch, key=per_ch.get)
    minimo = round(budget * 0.25, 2)

    ambiente = {**os.environ,
                "MMM_OUTPUT_DIR": lavoro,
                "MMM_WORKBOOK": workbook,
                "PYTHONPYCACHEPREFIX": os.environ.get(
                    "PYTHONPYCACHEPREFIX", "/tmp/pyc")}
    ambiente.setdefault("MMM_REGISTRY",
                        "auto" if os.environ.get("MMM_BQ_PROJECT") else "local")

    comando = [sys.executable, "-m", "pipeline.allocator.run",
               "--budget", str(budget),
               "--quarter-start", _QUARTER_START,
               "--canon", canon_dir,
               "--fit", fit_path,
               "--min", f"{canale_min}={minimo}",
               "--registry-label", "collaudo-vm"]
    with U.Timer() as t:
        proc = subprocess.run(comando, cwd=radice, capture_output=True,
                              text=True, env=ambiente)
    if proc.returncode != 0:
        coda = (proc.stderr or proc.stdout or "").strip().splitlines()
        return esiti + [U.fail(
            "Allocatore end-to-end",
            "; ".join(coda[-3:]) if coda else "uscita non nulla senza messaggio",
            t.elapsed)]
    esiti.append(U.ok("Allocatore end-to-end",
                      f"budget {budget:,.0f} € su {len(canali)} canali, "
                      f"vincolo minimo su {canale_min}", t.elapsed))

    # ------------------------------------------------ 4. Excel per il decisore
    with U.Timer() as t:
        try:
            fogli = pd.ExcelFile(workbook).sheet_names
            mancanti = [f for f in _FOGLI_ATTESI if f not in fogli]
        except Exception as e:                         # noqa: BLE001
            fogli, mancanti = [], list(_FOGLI_ATTESI)
            errore = f"{type(e).__name__}: {e}"
        else:
            errore = ""
    esiti.append(U.verdict(
        "Excel per il decisore", not mancanti,
        f"{len(fogli)} fogli: {', '.join(fogli)}",
        errore or f"fogli mancanti: {mancanti}", t.elapsed))

    # ------------------------------------------------ 5. budget conservato
    if not mancanti:
        with U.Timer() as t:
            try:
                cn = pd.read_excel(workbook, sheet_name="Canali")
                riga = cn[cn["canale"] == "TOTALE"].iloc[0]
                totale = float(riga["spesa consigliata (EUR)"])
                scarto = abs(totale - budget)
                conserva = scarto <= max(len(canali) * 1.0, budget * 1e-4)
            except Exception as e:                     # noqa: BLE001
                totale, scarto, conserva = 0.0, budget, False
                errore = f"{type(e).__name__}: {e}"
            else:
                errore = ""
        esiti.append(U.verdict(
            "Budget conservato dall'ottimizzatore", conserva,
            f"{totale:,.0f} € distribuiti su {budget:,.0f} € "
            f"(scarto {scarto:,.0f} €, arrotondamenti)",
            errore or f"scarto {scarto:,.0f} € su {budget:,.0f} €", t.elapsed))

    # ------------------------------------------------ 6. registro popolato
    reg_dir = os.path.join(lavoro, "registry")
    if os.path.isdir(reg_dir):
        with U.Timer() as t:
            try:
                runs = pd.read_csv(os.path.join(reg_dir, "runs.csv"))
                ultimo = runs.iloc[-1]
                tabelle = [f[:-4] for f in sorted(os.listdir(reg_dir))
                           if f.endswith(".csv")]
                esito_run = str(ultimo["status"])
            except Exception as e:                     # noqa: BLE001
                tabelle, esito_run = [], f"{type(e).__name__}: {e}"
        esiti.append(U.verdict(
            "Tabelle del registro scritte", esito_run == "ok" and len(tabelle) >= 5,
            f"{len(tabelle)} tabelle ({', '.join(tabelle)}), run '{esito_run}'",
            f"tabelle={tabelle}, esito run={esito_run}", t.elapsed))

        # il vincolo attivo deve sopravvivere fino alla tabella: è la prova
        # che la catena non perde semantica per strada
        try:
            alloc = pd.read_csv(os.path.join(reg_dir, "allocation.csv"))
            riga = alloc[alloc["channel"] == canale_min].iloc[-1]
            attivo = str(riga.get("constraint_active", ""))
        except Exception as e:                         # noqa: BLE001
            attivo = f"illeggibile ({type(e).__name__})"
        esiti.append(U.verdict(
            "Il vincolo manageriale arriva fino alla tabella",
            attivo == "min",
            f"{canale_min}: vincolo 'min' registrato",
            f"{canale_min}: atteso 'min', trovato {attivo!r}", soft=True))
    else:
        esiti.append(U.fail("Tabelle del registro scritte",
                            f"cartella non creata: {reg_dir}"))

    # ------------------------------------------------ 7. rilettura da BigQuery
    progetto = os.environ.get("MMM_BQ_PROJECT")
    if not progetto:
        esiti.append(U.skip("Rilettura della catena da BigQuery",
                            "MMM_BQ_PROJECT non impostata: il registro ha "
                            "scritto in locale"))
    else:
        with U.Timer() as t:
            try:
                from google.cloud import bigquery
                import mmm_registry as REG
                dataset = os.environ.get("MMM_BQ_DATASET", REG.DATASET_DEFAULT)
                cli = bigquery.Client(project=progetto)
                q = (f"SELECT COUNT(*) AS n FROM "
                     f"`{progetto}.{dataset}.allocation` "
                     f"WHERE run_id IN (SELECT run_id FROM "
                     f"`{progetto}.{dataset}.runs` WHERE label = 'collaudo-vm')")
                n = list(cli.query(q).result())[0]["n"]
                okbq, dettaglio = n > 0, f"{n} righe di allocazione in {dataset}"
            except Exception as e:                     # noqa: BLE001
                okbq, dettaglio = False, f"{type(e).__name__}: {e}"
        esiti.append(U.verdict("Rilettura della catena da BigQuery", okbq,
                               dettaglio, dettaglio, t.elapsed))

    return esiti
