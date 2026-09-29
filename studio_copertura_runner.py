"""Runner di UN mondo per lo studio di copertura degli intervalli di credibilita'.

Eseguito come SOTTOPROCESSO dal notebook colab_copertura.ipynb, un mondo per
processo: alla fine il processo muore e la memoria GPU torna libera, cosa che
otto fit consecutivi nello stesso processo non garantirebbero.

Cosa fa, nell'ordine:
  1. genera il mondo con genera_dati_simulati.py --seed-mondo N (deterministico:
     stesso seme = dataset identico byte per byte, verificato nei test);
  2. esegue LE STESSE celle del notebook congelato colab_end_to_end.ipynb
     (CELLA 2, 3, 5, 6, 7, 9) lette dal .ipynb: niente copia della logica,
     il fit del mondo e' il fit della tesi;
  3. risponde alle domande interattive in modo VINCOLATO: ogni domanda ha una
     risposta dichiarata (il valore della conversione e' 40.0 EUR); una domanda
     non prevista FERMA il run con errore, mai un default silenzioso;
  4. misura le due metriche sul TOTALE e per canale contro la verita' DI QUEL
     mondo: intervallo esatto (somma dentro ogni draw, poi quantili - MAI la
     somma degli estremi canale per canale) e PIT calcolato sui draw;
  5. accoda UNA riga al CSV dei risultati (header creato se il file non c'e');
  6. cancella il pickle del modello e, salvo --conserva-mondo, l'intera
     cartella del mondo (rigenerabile in un secondo dal suo seme).

Questo processo gira NON PRESIDIATO: stdin va chiuso dal chiamante
(stdin=DEVNULL), cosi' un input() imprevisto diventa EOFError immediato -
un errore visibile - invece di un blocco infinito in attesa di un click.

LETTURA DEI RISULTATI, FISSATA PRIMA DI ESEGUIRE (dal mandato):
  copertura 7-8 su 8 con PIT sparsi  -> intervallo calibrato; il dataset
                                        canonico era un mondo sfortunato
  copertura 4-6, PIT irregolari      -> copertura degradata ma non collassata;
                                        serve N piu' grande
  copertura 0-3, PIT tutti < 0,05    -> l'intervallo al 90% non vale il 90%
                                        in regime osservazionale: il modello
                                        non sa di sbagliare
Con N=8 l'incertezza sulla copertura resta ampia: il risultato e' indicativo
e il numero di mondi va sempre scritto accanto alla percentuale.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")  # nessuna finestra: gira in sottoprocesso senza display


# -----------------------------------------------------------------------------
# Celle del notebook congelato
# -----------------------------------------------------------------------------
def carica_celle(percorso_ipynb: str, etichette: list[str]) -> dict[str, str]:
    nb = json.load(open(percorso_ipynb, encoding="utf-8"))
    fuori: dict[str, str] = {}
    for cella in nb["cells"]:
        if cella["cell_type"] != "code":
            continue
        src = "".join(cella["source"])
        for et in etichette:
            if re.search(r"^#\s*" + et + r"\s*-", src, flags=re.M):
                if et in fuori:
                    raise SystemExit("etichetta duplicata nel notebook: " + et)
                fuori[et] = src
    mancanti = [e for e in etichette if e not in fuori]
    if mancanti:
        raise SystemExit("celle non trovate nel notebook: " + ", ".join(mancanti))
    return fuori


def _input_vietato(*_a, **_k):
    raise RuntimeError(
        "input() raggiunto in un run non presidiato: una domanda non prevista "
        "dal runner. Va aggiunta alle risposte dichiarate, non lasciata al caso.")


def costruisci_namespace(mondo_dir: str, output_tmp: str, keep: int,
                         seed_mcmc: int, risposte_log: list[str]) -> dict:
    # Le stesse import della CELLA 1 del notebook (senza pip: l'ambiente e' gia'
    # pronto) - il runner NON reimplementa nulla del modello.
    import io as _io
    import math as _math
    import pickle as _pickle
    import inspect as _inspect
    import unicodedata as _unicodedata
    import difflib as _difflib
    import warnings as _warnings
    import datetime as _dt
    import numpy as _np
    import pandas as _pd
    import matplotlib.pyplot as _plt
    import tensorflow as _tf
    import tensorflow_probability as _tfp
    import arviz as _az
    import meridian as _meridian
    from meridian import constants as _constants
    from meridian.data import load as _load
    from meridian.model import model as _model, spec as _spec, \
        prior_distribution as _prior_distribution

    ns = {
        "os": os, "io": _io, "re": re, "csv": csv, "json": json,
        "math": _math, "pickle": _pickle, "inspect": _inspect,
        "unicodedata": _unicodedata, "difflib": _difflib,
        "warnings": _warnings, "dt": _dt, "np": _np, "pd": _pd, "plt": _plt,
        "tf": _tf, "tfp": _tfp, "az": _az, "meridian": _meridian,
        "constants": _constants, "load": _load, "model": _model,
        "spec": _spec, "prior_distribution": _prior_distribution,
        "OUTPUT_DIR": output_tmp, "FIG_DIR": os.path.join(output_tmp, "fig"),
        "input": _input_vietato,
    }
    os.makedirs(ns["FIG_DIR"], exist_ok=True)
    return ns


def blinda_helper(ns: dict, risposte_log: list[str]) -> None:
    # Dopo l'exec della CELLA 2: run non presidiato, risposte VINCOLATE.
    ns["AUTO_CONFERMA"] = True   # checkpoint/scegli_opzione la onorano

    scegli_orig = ns["scegli_opzione"]

    def scegli_registrato(domanda, opzioni, default=0):
        scelta = default   # stessa scelta di AUTO_CONFERMA, ma registrata
        risposte_log.append("scegli[" + str(scelta) + "]: " + str(domanda)[:80])
        print("[auto] " + str(domanda)[:100] + " -> [" + str(scelta) + "] " +
              str(opzioni[scelta])[:80])
        return scelta

    def chiedi_vincolato(domanda, default=None, vuoto_ok=True):
        # chiedi_numero del notebook ignora AUTO_CONFERMA (bug noto): qui viene
        # sostituito. Ogni domanda DEVE avere una risposta dichiarata.
        d = str(domanda).lower()
        if "valore medio di una conversione" in d:
            risposte_log.append("numero[40.0]: valore conversione")
            print("[auto] valore della conversione -> 40.0 EUR (dal mandato)")
            return 40.0
        raise RuntimeError(
            "chiedi_numero con domanda NON prevista dal runner: '" +
            str(domanda)[:120] + "'. Aggiungere la risposta dichiarata.")

    ns["scegli_opzione"] = scegli_registrato
    ns["chiedi_numero"] = chiedi_vincolato


# -----------------------------------------------------------------------------
# Verita' del mondo
# -----------------------------------------------------------------------------
def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def verita_del_mondo(mondo_dir: str, settimane, canali_modello: list[str],
                     pd) -> tuple[float, dict[str, float]]:
    """Somma la verita' DI QUEL mondo sulla finestra del fit, per canale.

    Il confronto e' sempre fit-di-quel-mondo contro verita'-di-quel-mondo:
    il file viene letto SOLO dalla cartella verita/ del mondo appena
    generato, mai cercato altrove (la ricerca generica della cella 10-bis
    puo' agganciare la verita' di una variante sbagliata)."""
    path = os.path.join(mondo_dir, "verita", "contributo_vero.csv")
    if not os.path.exists(path):
        raise SystemExit("verita' del mondo assente: " + path)
    vt = pd.read_csv(path)
    vt["settimana"] = pd.to_datetime(vt["settimana"])
    lo, hi = pd.Timestamp(min(settimane)), pd.Timestamp(max(settimane))
    vt = vt[(vt["settimana"] >= lo) & (vt["settimana"] <= hi)]
    per_canale_raw = vt.groupby("canale")["candidature_incrementali_vere"].sum()

    mappa = {}
    for cm in canali_modello:
        candidati = [c for c in per_canale_raw.index if _norm(c) == _norm(cm)]
        if len(candidati) != 1:
            raise SystemExit(
                "mappatura canale modello->verita' non univoca per '" + cm +
                "': trovati " + str(candidati) + ". Canali verita': " +
                ", ".join(map(str, per_canale_raw.index)) +
                ". Meglio fermarsi che confrontare canali sbagliati.")
        mappa[cm] = float(per_canale_raw[candidati[0]])
    return float(sum(mappa.values())), mappa


# -----------------------------------------------------------------------------
# CSV: append di una riga per mondo, header alla prima scrittura
# -----------------------------------------------------------------------------
COLONNE = ["mondo", "seed_mondo", "esito", "unita_outcome",
           "vero", "mediana", "ci05", "ci95",
           "rapporto_mediana", "rapporto_ci05", "rapporto_ci95",
           "dentro", "pit", "sd_dalla_mediana",
           "quota_media_stimata_pct", "quota_media_vera_pct",
           "divergenze", "rhat_roi_m", "ess_roi_m",
           "rhat_beta_m", "ess_beta_m", "var_beta_usata",
           "canali_dentro_su_7", "pit_per_canale",
           "n_knots", "keep", "n_chains", "adapt", "burnin", "seed_mcmc",
           "revenue_per_kpi", "impronta_input_data", "durata_fit_min",
           "risposte_automatiche", "errore"]


def accoda_riga(csv_path: str, riga: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
    nuovo = not (os.path.exists(csv_path) and os.path.getsize(csv_path) > 0)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLONNE, extrasaction="ignore")
        if nuovo:
            w.writeheader()
        w.writerow({c: riga.get(c, "") for c in COLONNE})
        f.flush()
        os.fsync(f.fileno())   # la riga deve sopravvivere a un crash di Colab


# -----------------------------------------------------------------------------
# Il mondo, dall'inizio alla riga di CSV
# -----------------------------------------------------------------------------
def esegui_mondo(args) -> int:
    repo = os.path.abspath(args.repo)
    nome_mondo = "mondo_" + format(args.seed_mondo, "04d")
    mondo_dir = os.path.join(repo, "dati_simulati_mondi", nome_mondo)
    output_tmp = os.path.join(mondo_dir, "_output_fit")
    risposte: list[str] = []
    riga = {"mondo": nome_mondo, "seed_mondo": args.seed_mondo,
            "keep": args.keep, "n_chains": args.n_chains,
            "adapt": args.n_adapt, "burnin": args.n_burnin,
            "seed_mcmc": args.seed_mcmc, "esito": "errore", "errore": ""}

    try:
        # --- 1. genera il mondo (deterministico dal suo seme) ----------------
        subprocess.run([sys.executable,
                        os.path.join(repo, "genera_dati_simulati.py"),
                        "--seed-mondo", str(args.seed_mondo)],
                       cwd=repo, check=True, stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # --- 2. celle del notebook congelato ---------------------------------
        celle = carica_celle(os.path.join(repo, "colab_end_to_end.ipynb"),
                             ["CELLA 2", "CELLA 3", "CELLA 5",
                              "CELLA 6", "CELLA 7", "CELLA 9"])
        ns = costruisci_namespace(mondo_dir, output_tmp, args.keep,
                                  args.seed_mcmc, risposte)
        exec(compile(celle["CELLA 2"], "CELLA2", "exec"), ns)
        blinda_helper(ns, risposte)

        # Config dello studio: IDENTICA per tutti i mondi e dichiarata nel CSV.
        # I default della CONFIG del notebook NON fanno fede qui: il mandato
        # fissa 96 nodi (12/trimestre), keep 2000, prior deboli LogNormal(0.2,
        # 0.9), seed MCMC 42, revenue_per_kpi 40.
        ns["KNOTS_PER_QUARTER"] = 12
        ns["N_CHAINS"] = args.n_chains
        ns["N_ADAPT"] = args.n_adapt
        ns["N_BURNIN"] = args.n_burnin
        ns["N_KEEP"] = args.keep
        ns["SEED"] = args.seed_mcmc
        ns["USA_PRIOR_INFORMATIVI"] = False
        ns["PRIOR_ROI_MU"] = 0.2
        ns["PRIOR_ROI_SIGMA"] = 0.9
        ns["KPI"] = "auto"
        ns["PERIODO"] = "auto"
        ns["GEO"] = "auto"
        ns["VALUTA"] = "auto"

        exec(compile(celle["CELLA 3"], "CELLA3", "exec"), ns)

        # dati del mondo: SOLO la cartella modello/ (la verita' non entra mai)
        dir_dati = os.path.join(mondo_dir, "modello")
        files = {}
        for nome in sorted(os.listdir(dir_dati)):
            if nome.lower().endswith(".csv"):
                files[nome] = open(os.path.join(dir_dati, nome), "rb").read()
        if not files:
            raise SystemExit("nessun CSV in " + dir_dati)
        ns["FILES_GREZZI"] = files
        ns["ORIGINE_DATI"] = dir_dati

        exec(compile(celle["CELLA 5"], "CELLA5", "exec"), ns)
        exec(compile(celle["CELLA 6"], "CELLA6", "exec"), ns)
        exec(compile(celle["CELLA 7"], "CELLA7", "exec"), ns)

        # --- 3. guardie PRIMA del fit (fermarsi qui costa secondi) -----------
        np = ns["np"]
        if not ns.get("REVENUE_PER_KPI_PRESENTE"):
            riga["esito"] = "unita_sbagliata"
            raise SystemExit(
                "revenue_per_kpi NON arrivato all'InputData: il fit girerebbe "
                "in conversioni, non in EUR. E' il bug che brucio' tre run: "
                "qui ferma tutto PRIMA del fit.")
        if abs(float(ns.get("RPK_MEDIO") or 0.0) - 40.0) > 1e-9:
            riga["esito"] = "unita_sbagliata"
            raise SystemExit("revenue_per_kpi = " + str(ns.get("RPK_MEDIO")) +
                             " invece di 40.0: config non conforme al mandato.")
        riga["unita_outcome"] = "EUR per EUR speso"
        riga["revenue_per_kpi"] = 40.0

        n_geo = int(ns["N_GEOS"]); n_sett = int(ns["N_SETTIMANE"])
        canali = list(ns["CANALI_MODELLO"])
        if (n_geo, n_sett, len(canali)) != (20, 104, 7):
            raise SystemExit("struttura del mondo inattesa: " +
                             str((n_geo, n_sett, len(canali))) +
                             " invece di (20, 104, 7)")

        # verita' del mondo, sulla finestra del fit, in EUR (x 40)
        vero_conv, vero_canale_conv = verita_del_mondo(
            mondo_dir, ns["SETTIMANE"], canali, ns["pd"])
        RPK = 40.0
        vero = vero_conv * RPK
        vero_canale = {c: v * RPK for c, v in vero_canale_conv.items()}
        riga["vero"] = round(vero, 1)
        kpi_tot = float(ns["DF_BASE"]["kpi"].sum())
        riga["quota_media_vera_pct"] = round(100 * vero_conv / kpi_tot, 2)

        # --- 4. il fit (la parte da ~10 minuti) -------------------------------
        exec(compile(celle["CELLA 9"], "CELLA9", "exec"), ns)
        riga["durata_fit_min"] = round(float(ns.get("DURATA_FIT_MIN", 0)), 2)
        riga["n_knots"] = int(ns["N_KNOTS"])
        riga["divergenze"] = int(ns.get("DIVERGENZE", -1))
        riga["impronta_input_data"] = str(
            (ns.get("IMPRONTA_INPUT_DATA") or {}).get("hash_spesa", "n/d"))

        # R-hat/ESS dei PARAMETRI DI INTERESSE (roi_m, beta della media), non
        # il massimo globale: quello e' dominato da knot_values e fa scartare
        # run buoni.
        diag = ns.get("DIAG_TABELLA")
        if diag is not None and "parametro" in diag.columns:
            d = diag.set_index("parametro")
            if "roi_m" in d.index:
                riga["rhat_roi_m"] = float(d.loc["roi_m", "rhat_max"])
                riga["ess_roi_m"] = float(d.loc["roi_m", "ess_min"])
            beta_vars = [p for p in d.index
                         if _norm(p).startswith("beta") and "m" in _norm(p)]
            if beta_vars:
                bv = sorted(beta_vars)[0]
                riga["var_beta_usata"] = bv
                riga["rhat_beta_m"] = float(d.loc[bv, "rhat_max"])
                riga["ess_beta_m"] = float(d.loc[bv, "ess_min"])

        # --- 5. metriche: intervallo esatto + PIT sui draw --------------------
        from meridian.analysis import analyzer as _analyzer
        AN = _analyzer.Analyzer(ns["MMM"])
        io_t = AN.incremental_outcome()      # outcome in EUR (rpk presente)
        arr = np.asarray(io_t)
        # Validazione di forma ESPLICITA: un tensore con una dimensione in piu'
        # (geo/tempo non aggregati) o trasposto verrebbe altrimenti mescolato
        # in silenzio dal reshape.
        if arr.ndim != 3 or arr.shape[-1] != len(canali):
            raise SystemExit("forma inattesa da incremental_outcome(): " +
                             str(arr.shape) + " (attesa: (catene, draw, " +
                             str(len(canali)) + "))")
        if arr.shape[0] * arr.shape[1] != args.n_chains * args.keep:
            raise SystemExit("numero di campioni inatteso: " + str(arr.shape) +
                             " vs " + str(args.n_chains) + "x" + str(args.keep))

        tot = arr.sum(axis=-1).reshape(-1)   # somma DENTRO ogni draw
        lo05, hi95 = np.quantile(tot, [0.05, 0.95])
        mediana = float(np.median(tot))
        sd = float(np.std(tot))
        riga.update({
            "mediana": round(mediana, 1),
            "ci05": round(float(lo05), 1), "ci95": round(float(hi95), 1),
            "rapporto_mediana": round(mediana / vero, 4),
            "rapporto_ci05": round(float(lo05) / vero, 4),
            "rapporto_ci95": round(float(hi95) / vero, 4),
            "dentro": int(bool(lo05 <= vero <= hi95)),
            "pit": round(float(np.mean(tot <= vero)), 6),
            "sd_dalla_mediana": round((vero - mediana) / sd, 3) if sd > 0 else "",
            "quota_media_stimata_pct": round(
                100 * float(np.mean(tot)) / RPK / kpi_tot, 2),
        })

        # per canale: stessa logica, canale per canale (extra a costo zero)
        dentro_c, pit_c = 0, []
        for j, c in enumerate(canali):
            s = arr[..., j].reshape(-1)
            l, h = np.quantile(s, [0.05, 0.95])
            v = vero_canale[c]
            dentro_c += int(l <= v <= h)
            pit_c.append(_norm(c)[:12] + ":" +
                         str(round(float(np.mean(s <= v)), 4)))
        riga["canali_dentro_su_7"] = dentro_c
        riga["pit_per_canale"] = "|".join(pit_c)
        riga["esito"] = "ok"
        return 0

    except BaseException as e:   # anche SystemExit: la riga va scritta comunque
        riga["errore"] = str(e)[:400]
        if riga.get("esito") == "ok":
            riga["esito"] = "errore"
        return 1

    finally:
        riga["risposte_automatiche"] = " ; ".join(risposte)[:400]
        accoda_riga(args.csv, riga)
        # --- 6. pulizia: nessun pickle sopravvive alla misura -----------------
        shutil.rmtree(output_tmp, ignore_errors=True)
        if not args.conserva_mondo:
            shutil.rmtree(mondo_dir, ignore_errors=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed-mondo", type=int, required=True)
    ap.add_argument("--repo", required=True,
                    help="cartella del repo (contiene generatore e notebook)")
    ap.add_argument("--csv", required=True,
                    help="CSV dei risultati (una riga per mondo, append)")
    ap.add_argument("--keep", type=int, default=2000,
                    help="N_KEEP: 2000 come i run canonici; se ridotto, "
                         "ridotto UGUALE per tutti i mondi e dichiarato")
    ap.add_argument("--n-chains", type=int, default=4)
    ap.add_argument("--n-adapt", type=int, default=500)
    ap.add_argument("--n-burnin", type=int, default=500)
    ap.add_argument("--seed-mcmc", type=int, default=42,
                    help="seme MCMC: 42 per tutti i mondi (il mondo varia "
                         "col SUO seme, non con questo)")
    ap.add_argument("--conserva-mondo", action="store_true",
                    help="non cancellare la cartella del mondo a fine misura")
    sys.exit(esegui_mondo(ap.parse_args()))


if __name__ == "__main__":
    main()
