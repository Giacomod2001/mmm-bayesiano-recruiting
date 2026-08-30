"""
Controllo 2 — ingestion end-to-end su un mondo sintetico ridotto.

Rifà in piccolo la catena "export sporchi → fatti canonici":
generatore → propose_plan → ingest (batch, piano auto-confermato) →
validazione di schema → confronto con i canonici VERI (canonical_true).

Nota: il mondo è generato in una cartella temporanea dentro `vm_check/out/`,
quindi NON tocca `pipeline/data/`.
"""
from __future__ import annotations

import contextlib
import io
import os

from ._util import Result, Timer, fail, ok, verdict, warn

TITOLO = "Ingestion"

# gli export che il generatore deve produrre (formati volutamente "sporchi")
RAW_ATTESI = [
    "meta_ads.csv", "google_ads.csv", "google_ads_geografia.csv",
    "linkedin_campaigns.xlsx", "indeed_export.csv", "crm_candidature.csv.gz",
    "richieste_clienti.xlsx", "ricerche_candidati.csv", "stagionalita.csv",
]
FATTI_ATTESI = ["media", "outcome", "demand", "seasonality"]
PII_VIETATE = ("pii_name", "pii_surname", "pii_cf", "nome", "cognome",
               "codice_fiscale", "email", "telefono")

TOLLERANZA_OK = 0.02      # scostamento accettato senza commenti
TOLLERANZA_WARN = 0.10    # oltre → FAIL


def _scostamento(stimato: float, vero: float) -> float:
    return abs(stimato - vero) / vero if vero else float("inf")


def run(ctx: dict) -> list[Result]:
    import pandas as pd

    from pipeline import schema
    from pipeline.generator import run as gen_run
    from pipeline.ingestion import build

    res: list[Result] = []
    n_weeks = ctx["n_weeks"]
    root = os.path.join(ctx["out_dir"], "mondo_prova")
    os.makedirs(root, exist_ok=True)
    silenzio = io.StringIO()

    # --- generazione degli export ------------------------------------------
    with Timer() as t:
        try:
            with contextlib.redirect_stdout(silenzio):
                gen_run.main(seed=7, n_weeks=n_weeks, out_root=root)
        except Exception as e:  # noqa: BLE001
            res.append(fail("Generatore mondo sintetico",
                            f"{type(e).__name__}: {e}", t.elapsed))
            return res
    raw_dir = os.path.join(root, "raw")
    true_dir = os.path.join(root, "canonical_true")
    res.append(ok("Generatore mondo sintetico",
                  f"{n_weeks} settimane in {raw_dir}", t.elapsed))

    mancanti = [f for f in RAW_ATTESI
                if not os.path.exists(os.path.join(raw_dir, f))]
    res.append(verdict("Export grezzi prodotti", not mancanti,
                       f"{len(RAW_ATTESI)} file (csv, csv.gz, xlsx)",
                       f"mancano: {', '.join(mancanti)}"))

    # --- proposta di mappatura ---------------------------------------------
    with Timer() as t:
        try:
            plans, tables = build.propose_plan(raw_dir)
        except Exception as e:  # noqa: BLE001
            res.append(fail("Riconoscimento sorgenti (propose_plan)",
                            f"{type(e).__name__}: {e}", t.elapsed))
            return res
    non_riconosciuti = [p.file for p in plans if not p.kind]
    res.append(verdict(
        "Riconoscimento sorgenti (propose_plan)", not non_riconosciuti,
        f"{len(plans)} sorgenti mappate automaticamente",
        f"senza tipo riconosciuto: {', '.join(non_riconosciuti)}",
        seconds=t.elapsed, soft=True))

    # --- ingestion batch ----------------------------------------------------
    for p in plans:
        p.confirmed = True            # conferma umana simulata (solo nel test)
    canon_dir = os.path.join(root, "canonical")
    with Timer() as t:
        try:
            with contextlib.redirect_stdout(silenzio):
                esito = build.ingest(raw_dir, plan=plans, interactive=False,
                                     out_dir=canon_dir, tables=tables,
                                     salt="check-vm")
        except Exception as e:  # noqa: BLE001
            res.append(fail("Ingestion end-to-end",
                            f"{type(e).__name__}: {e}", t.elapsed))
            return res
    fatti = esito["facts"]
    res.append(ok("Ingestion end-to-end",
                  ", ".join(f"{k} {len(v):,} righe" for k, v in fatti.items()),
                  t.elapsed))

    assenti = [f for f in FATTI_ATTESI if f not in fatti]
    res.append(verdict("Fatti canonici attesi", not assenti,
                       " + ".join(FATTI_ATTESI),
                       f"non prodotti: {', '.join(assenti)}"))

    file_scritti = [f for f in ("media.csv", "outcome.csv", "demand.csv",
                                "seasonality.csv", "mapping_confirmed.json")
                    if os.path.exists(os.path.join(canon_dir, f))]
    res.append(verdict("File canonici su disco", len(file_scritti) == 5,
                       f"{len(file_scritti)}/5 in {canon_dir}",
                       f"scritti solo: {', '.join(file_scritti) or 'nessuno'}"))

    # --- validazione di schema ----------------------------------------------
    reports = esito.get("reports") or schema.validate_all(fatti)
    errori = {n: r.errors for n, r in reports.items() if not r.ok}
    res.append(verdict(
        "Validazione di schema", not errori,
        "settimane lunedì, regioni canoniche, numerici >= 0, chiavi uniche",
        "; ".join(f"{n}: {' | '.join(e)}" for n, e in errori.items())))
    avvisi = sum(len(r.warnings) for r in reports.values())
    if avvisi:
        res.append(warn("Avvisi di validazione",
                        f"{avvisi} avvisi non bloccanti (dettaglio nel log)"))

    # --- privacy -------------------------------------------------------------
    colonne_out = set(fatti.get("outcome", pd.DataFrame()).columns)
    trapelate = sorted(c for c in colonne_out
                       if c.lower() in PII_VIETATE)
    res.append(verdict("Nessun dato personale nei canonici", not trapelate,
                       "outcome contiene solo week, region, conversions, "
                       "revenue",
                       f"colonne con PII: {', '.join(trapelate)}"))

    # --- confronto con la verità -------------------------------------------
    for fatto, colonna in (("media", "spend"), ("outcome", "conversions")):
        percorso = os.path.join(true_dir, f"{fatto}.csv")
        if fatto not in fatti or not os.path.exists(percorso):
            res.append(warn(f"Totale {colonna} vs verità",
                            "riferimento canonical_true non disponibile"))
            continue
        vero = float(pd.read_csv(percorso)[colonna].sum())
        stimato = float(fatti[fatto][colonna].sum())
        d = _scostamento(stimato, vero)
        testo = (f"ricostruito {stimato:,.0f} vs vero {vero:,.0f} "
                 f"(scarto {d:.2%})")
        if d <= TOLLERANZA_OK:
            res.append(ok(f"Totale {colonna} vs verità", testo))
        elif d <= TOLLERANZA_WARN:
            res.append(warn(f"Totale {colonna} vs verità",
                            testo + " — atteso in parte: rumore di "
                                    "piattaforma e riparti geografici"))
        else:
            res.append(fail(f"Totale {colonna} vs verità",
                            testo + " — scarto anomalo, controlla la "
                                    "mappatura delle sorgenti"))

    # --- copertura della griglia --------------------------------------------
    media = fatti.get("media")
    if media is not None and len(media):
        settimane = media["week"].nunique()
        regioni = media["region"].nunique()
        canali = media["channel"].nunique()
        res.append(verdict(
            "Copertura griglia settimana × regione",
            settimane >= n_weeks - 1 and regioni >= 19,
            f"{settimane} settimane × {regioni} regioni × {canali} canali",
            f"copertura parziale: {settimane} settimane, {regioni} regioni"))

    # lasciato al controllo Excel
    ctx["raw_dir"] = raw_dir
    ctx["canon_dir"] = canon_dir
    ctx["facts"] = fatti
    return res
