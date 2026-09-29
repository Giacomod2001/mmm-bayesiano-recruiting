"""Runner di UN mondo per lo studio di copertura degli intervalli di credibilita'.

R8 = R7 + due cose, per D12 e D13:
  - disegno 'blackout' (D12): tutti e sette i canali a zero in cinque regioni
    fisse per due blocchi da otto settimane, spesa NON ridistribuita. Dal JSON
    del generatore arrivano anche la quota vera del mondo base e le
    candidature vere perse, cioe' il costo del disegno;
  - --controllo-baseline f (D13): una variabile di controllo costruita dalla
    baseline VERA del mondo, aggiunta ai dati del modello DOPO la generazione.
    Il generatore gira senza alcun flag e i file media e il KPI restano quelli
    del mondo base.

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

Con --dati-modello CARTELLA il passo 1 non genera niente: il fit gira su un
dataset GIA' PRESENTE nel repo (es. dati_simulati/geo/modello_geo, che nessun
flag del generatore committato sa riprodurre). La verita' e' quella della SUA
cartella sorella verita/ (contributo_vero<suffisso>.csv), derivata dal nome
della cartella e mai cercata altrove. Il dataset non viene mai toccato ne'
cancellato: la pulizia finale riguarda solo la cartella di lavoro
dati_simulati_mondi/_lavoro_<nome>. In entrambi i casi il CSV riporta quanti
decimali ha il stagionalita.csv dato in pasto al modello (3 = formato
originale, 8 righe su 104 lette x1000 dal parser; 4 = formato corretto).

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

# ROI VERI per canale del mondo 42 (verita/contributo_vero.csv x 40 EUR /
# spesa): sono i valori a cui il prior "ancorato" viene centrato. Un prior
# centrato sulla risposta e' circolare per costruzione: i run che lo usano
# stanno fuori dai risultati, si rifanno solo perche' i loro numeri sono
# citati, e il CSV li marca con prior_tipo = ancorato.
ROI_ANCORATI = {"Google Ads": 1.50, "Meta Ads": 1.63, "Indeed": 2.52,
                "Subito Lavoro": 2.88, "LinkedIn Ads": 0.88,
                "Altre job board": 2.72, "Jooble": 2.52}


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


def verita_del_mondo(path: str, settimane, canali_modello: list[str],
                     pd) -> tuple[float, dict[str, float]]:
    """Somma la verita' DI QUEL mondo sulla finestra del fit, per canale.

    Il confronto e' sempre fit-di-quel-mondo contro verita'-di-quel-mondo:
    `path` e' il contributo_vero della cartella verita/ SORELLA dei dati
    appena usati, fissato dal chiamante al passo 1 e mai cercato altrove
    (la ricerca generica della cella 10-bis puo' agganciare la verita' di
    una variante sbagliata)."""
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


def dataset_esistente(cartella: str, repo: str) -> tuple[str, str]:
    """(cartella dei dati, percorso della SUA verita') per un dataset gia'
    presente nel repo. Un percorso relativo e' relativo alla cartella del
    REPO (--repo), non alla directory corrente del processo: il notebook
    lo lancia da /content e il dataset sta in /content/<repo>/dati_simulati.
    La cartella deve chiamarsi modello<suffisso>: e' dal nome che si ricava
    la verita' sorella, <radice>/verita/contributo_vero<suffisso>.csv.
    Nessuna ricerca risalendo le cartelle: se il file non e' li', ci si
    ferma."""
    dir_dati = os.path.abspath(cartella if os.path.isabs(cartella)
                               else os.path.join(repo, cartella))
    if not os.path.isdir(dir_dati):
        raise SystemExit("--dati-modello: cartella inesistente: " + dir_dati +
                         " (relativa a --repo " + repo + ")")
    nome = os.path.basename(dir_dati)
    if not nome.startswith("modello"):
        raise SystemExit(
            "--dati-modello: la cartella deve chiamarsi modello<suffisso> "
            "(e' cosi' che si trova la SUA verita'), non '" + nome + "'")
    suffisso = nome[len("modello"):]
    percorso_verita = os.path.join(os.path.dirname(dir_dati), "verita",
                                   "contributo_vero" + suffisso + ".csv")
    if not os.path.exists(percorso_verita):
        raise SystemExit("verita' del dataset assente: " + percorso_verita +
                         " (attesa accanto a " + dir_dati + ")")
    return dir_dati, percorso_verita


_RE_MIGLIAIA_IT = re.compile(r"^-?\d{1,3}(\.\d{3})+$")   # la regex del parser


def decimali_stagionalita(dir_dati: str) -> int:
    """Quanti decimali ha stagionalita.csv cosi' com'e' scritto: il MINIMO
    sui valori. 3 = formato originale (pandas taglia lo zero finale: 0.929) e
    il parser dell'ingestion lo legge come migliaia all'italiana, 929; 4 =
    formato corretto (float_format %.4f). La colonna serve a scrivere
    l'attesa giusta per il run, e a non confondere un dato corretto con uno
    contaminato."""
    p = os.path.join(dir_dati, "stagionalita.csv")
    if not os.path.exists(p):
        raise SystemExit("stagionalita.csv assente in " + dir_dati)
    minimo, x1000 = None, 0
    with open(p, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v = str(r.get("indice_stagionale", "")).strip()
            if not re.fullmatch(r"-?\d+(\.\d+)?", v):
                raise SystemExit("stagionalita.csv: valore non numerico '" +
                                 v + "' in " + p)
            d = len(v.split(".")[1]) if "." in v else 0
            minimo = d if minimo is None else min(minimo, d)
            if _RE_MIGLIAIA_IT.match(v):
                x1000 += 1
    if minimo is None:
        raise SystemExit("stagionalita.csv vuoto: " + p)
    print("[dati] stagionalita.csv: " + str(minimo) + " decimali (minimo); "
          "righe che il parser leggerebbe x1000: " + str(x1000))
    return minimo


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
           "risposte_automatiche", "errore",
           "decimali_stagionalita"]


# Il CSV principale resta a colonne INVARIATE (le stesse dello studio
# osservativo, cosi' le due tabelle si affiancano). Il dettaglio per canale e i
# draw vanno in file AFFIANCATI, che il CSV non tocca.
COLONNE_CANALI = ["mondo", "seed_mondo", "canale", "spesa", "vero", "mediana",
                  "ci05", "ci95", "larghezza_relativa", "dentro", "pit",
                  "roi_vero", "roi_stimato", "rho_spearman"]

# Il prior e' parte della configurazione del run tanto quanto nodi e keep:
# senza queste due colonne una riga ancorata e una di riferimento sarebbero
# indistinguibili nel registro.
COLONNE += ["prior_tipo", "prior_sigma"]

# Griglia sperimentale (FASE 1-3): il disegno e' parte della configurazione
# come il prior. Tre colonne in coda: le 35 originali restano dove sono.
COLONNE += ["disegno", "canali_trattati", "parametri_disegno"]
# Prior parametrico (D9): mu del prior di riferimento e, per i prior ancorati,
# il ROAS di riferimento per canale (da ROI_ANCORATI o dal benchmark del mondo).
COLONNE += ["prior_mu", "prior_mu_per_canale"]
PRIOR_ANCORATI = ("ancorato", "ancorato-benchmark")


def roas_benchmark(percorso_csv: str) -> dict:
    """ROAS di piattaforma per canale dal benchmark del mondo: aggregato sul
    periodo, somma(spesa x roas_dichiarato) / somma(spesa) = conversioni
    dichiarate x valore / spesa. E' l'informazione 'realistica ma gonfiata' che
    un'azienda avrebbe davvero (D9c)."""
    num, den = {}, {}
    with open(percorso_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ch = r["canale"]
            sp = float(r["spesa"])
            num[ch] = num.get(ch, 0.0) + sp * float(r["roas_dichiarato"])
            den[ch] = den.get(ch, 0.0) + sp
    out = {ch: round(num[ch] / den[ch], 4) for ch in num if den[ch] > 0}
    if len(out) != 7:
        raise SystemExit("benchmark ROAS: " + str(len(out)) + " canali invece di 7 in " + percorso_csv)
    return out
# Per canale: la dose (quota di popolazione trattata) e la riduzione effettiva
# di spesa nelle regioni trattate, per canale e mondo; in casuale2 la spesa
# totale per canale rispetto al mondo base (che li' NON e' conservata).
COLONNE_CANALI += ["trattato", "dose_pct", "riduzione_effettiva_pct",
                   "spesa_vs_base_pct", "spesa_ridistribuita_eur"]
# R8 (D12): nel blackout la spesa non e' ridistribuita, e' TOLTA. Sono due
# colonne diverse perche' sono due cose diverse: confonderle farebbe leggere
# come "spostata" una spesa che nel mondo non c'e' piu'.
COLONNE_CANALI += ["spesa_tolta_eur"]
# R8 (D12): il costo del disegno e la quota vera del mondo BASE, dal JSON del
# generatore. Senza queste due colonne il costo andrebbe ricostruito a mano.
COLONNE += ["quota_media_vera_base_pct", "candidature_vere_perse"]
# R8 (D13): il controllo costruito dalla baseline vera. f = 0 significa
# nessun file scritto e run identico a D0.
COLONNE += ["controllo_baseline_f", "controllo_baseline_colonna",
            "controllo_baseline_rho", "controlli_nel_modello"]

# Disegni della griglia e flag del generatore. 'randomizzato' resta il nome
# storico dello studio di copertura per la variante sanita.
DISEGNI = ("base", "randomizzato", "sanita", "geo", "calendario", "casuale2",
           "pause2", "blackout")
FLAG_DISEGNO = {"base": [], "randomizzato": ["--sanita"], "sanita": ["--sanita"],
                "geo": ["--geo"], "calendario": ["--calendario"],
                "casuale2": ["--casuale2"], "pause2": ["--pause2"],
                "blackout": ["--blackout"]}
# parametri ammessi per disegno: chiave di --parametri-disegno -> flag del generatore
PARAMETRI_DISEGNO = {
    "geo": {"canali": "--geo-canali", "regioni": "--geo-regioni",
            "blocchi": "--geo-blocchi", "intensita": "--geo-intensita",
            "sfalsato": "--geo-sfalsato"},
    "calendario": {"rotazione": "--calendario-rotazione",
                   "giri": "--calendario-giri"},
}


def parametri_disegno(disegno: str, testo: str | None) -> tuple[list, str, str]:
    """'chiave=valore;chiave=valore' -> (flag del generatore, stringa
    normalizzata per il CSV, suffisso per la cartella del mondo). Le chiavi
    sconosciute per il disegno sono un errore: un parametro ignorato in
    silenzio darebbe una riga con un'etichetta falsa."""
    if not testo:
        return [], "", ""
    ammessi = PARAMETRI_DISEGNO.get(disegno, {})
    flag, norm, suff = [], [], []
    for pezzo in [p for p in testo.split(";") if p.strip()]:
        if "=" not in pezzo:
            raise SystemExit("--parametri-disegno: atteso chiave=valore, trovato " + repr(pezzo))
        k, v = (x.strip() for x in pezzo.split("=", 1))
        if k not in ammessi:
            raise SystemExit("--parametri-disegno: '" + k + "' non e' un parametro di '" +
                             disegno + "' (ammessi: " + ", ".join(sorted(ammessi)) + ")")
        if k == "sfalsato":
            if v not in ("1", "0", "si", "no"):
                raise SystemExit("--parametri-disegno: sfalsato=1|0")
            if v in ("1", "si"):
                flag.append(ammessi[k])
                norm.append(k + "=1")
                suff.append("sf")
            continue
        flag += [ammessi[k], v]
        norm.append(k + "=" + v)
        suff.append(k[:3] + re.sub(r"[^A-Za-z0-9.]+", "", v.replace(" ", "")))
    return flag, ";".join(norm), ("_" + "_".join(suff) if suff else "")


def leggi_disegno(percorso_json: str, disegno: str) -> tuple[str, dict]:
    """Dal JSON del generatore: i canali trattati (colonna del CSV) e, per
    canale, dose / riduzione effettiva / spesa vs base (colonne del file per
    canale). Letti dal file scritto dal generatore, non ricostruiti qui: se il
    generatore cambia il disegno, il registro lo dice."""
    if disegno == "base":
        return "", {}
    with open(percorso_json, encoding="utf-8") as f:
        j = json.load(f)
    dett: dict = {}
    if disegno in ("randomizzato", "sanita"):
        sc = j.get("scenario_sanita") or {}
        canali = sorted(sc.get("effetto_per_canale", {})) or []
        for c in canali:
            dett[c] = {"trattato": 1, "dose_pct": 100.0,
                       "riduzione_effettiva_pct": "", "spesa_vs_base_pct": 0.0,
                       "spesa_ridistribuita_eur": ""}
        return ";".join(canali), dett
    if disegno == "pause2":
        sc = j["scenario_pause"]
        canali = list(sc["canali_trattati"])
        for c in canali:
            e = sc["effetto_per_canale"].get(c, {})
            dett[c] = {"trattato": 1, "dose_pct": 100.0,
                       "riduzione_effettiva_pct": -100.0, "spesa_vs_base_pct": 0.0,
                       "spesa_ridistribuita_eur": e.get("spesa_tolta_eur", e.get("tolta", ""))}
        return ";".join(canali), dett
    if disegno == "casuale2":
        sc = j["scenario_casuale2"]
        canali = sorted(sc["effetto_per_canale"])
        for c in canali:
            dett[c] = {"trattato": 1, "dose_pct": 100.0, "riduzione_effettiva_pct": "",
                       "spesa_vs_base_pct": sc["effetto_per_canale"][c]["spesa_vs_base_pct"],
                       "spesa_ridistribuita_eur": ""}
        return ";".join(canali), dett
    sc = j["scenario_geo"]                         # geo, calendario, blackout
    canali = list(sc["canali_trattati"])
    for c in canali:
        e = sc["effetto_per_canale"][c]
        dett[c] = {"trattato": 1, "dose_pct": e["dose_popolazione_pct"],
                   "riduzione_effettiva_pct": e["riduzione_effettiva_pct"],
                   "spesa_vs_base_pct": 0.0,
                   "spesa_ridistribuita_eur": e["spesa_ridistribuita_eur"],
                   "spesa_tolta_eur": e.get("spesa_tolta_eur", "")}
    return ";".join(canali), dett


def leggi_costo_blackout(percorso_json: str) -> dict:
    """D12: quota vera del mondo BASE e candidature vere perse, dal JSON del
    generatore. Sono le due cifre che dicono quanto il disegno e' costato, e
    stanno nel file scritto dal generatore, non ricostruite qui."""
    with open(percorso_json, encoding="utf-8") as f:
        j = json.load(f)
    sc = j.get("scenario_blackout")
    if not sc:
        raise SystemExit("--disegno blackout ma il JSON del mondo non ha "
                         "scenario_blackout: il generatore non e' quello con G6")
    costo = sc.get("costo_del_disegno") or {}
    return {"quota_media_vera_base_pct": sc.get("quota_media_vera_mondo_base_pct", ""),
            "candidature_vere_perse": costo.get("candidature_vere_perse", "")}


def scrivi_controllo_baseline(mondo_dir: str, dir_dati: str, seed_mondo: int,
                              f: float, np, pd) -> tuple:
    """D13: aggiunge ai dati del modello UNA variabile di controllo costruita
    dalla baseline vera del mondo.

        c(t, g) = f x organico_vero(t, g) x exp(eps),  eps ~ Normale(0, 0,15)

    con rng dedicato numpy.random.default_rng(seed_mondo + 31) ed eps estratto
    nell'ordine in cui verita/candidature_organiche.csv e' scritto (settimana
    esterna, regione interna): l'ordine e' quello del file, non una scelta di
    questa funzione.

    I file media e il KPI non vengono toccati: il generatore ha girato senza
    alcun flag e la cartella e' quella del mondo base. Con f = 0 non viene
    scritto NIENTE (una colonna di soli zeri non sarebbe un controllo e il
    file verrebbe letto come elenco di eventi): il run e' identico a D0.

    IL CAVEAT, che va ripetuto ovunque compaia una cifra di D13: questo
    controllo e' costruito dalla baseline VERA, quindi misura il caso piu'
    favorevole possibile. E' un limite SUPERIORE di quello che un dato reale
    potrebbe dare, mai una stima di quello che darebbe."""
    if f <= 0:
        return "", "", ""
    percorso = os.path.join(mondo_dir, "verita", "candidature_organiche.csv")
    if not os.path.exists(percorso):
        raise SystemExit("--controllo-baseline: manca " + percorso)
    d = pd.read_csv(percorso)
    vera = d["candidature_organiche_vere"].to_numpy(dtype=float)
    rng = np.random.default_rng(int(seed_mondo) + 31)
    eps = rng.normal(0.0, 0.15, len(d))
    c = float(f) * vera * np.exp(eps)
    colonna = "domanda_organica_osservata"
    pd.DataFrame({"settimana": d["settimana"], "regione": d["regione"],
                  colonna: np.round(c, 3)}).to_csv(
        os.path.join(dir_dati, colonna + ".csv"), index=False)
    rho = float(np.corrcoef(c, vera)[0, 1])
    print("[D13] controllo " + colonna + " scritto: f=" + str(f) +
          ", corr con la baseline vera " + str(round(rho, 4)))
    return colonna, round(rho, 4), os.path.join(dir_dati, colonna + ".csv")


def percorso_affiancato(csv_path: str, suffisso: str) -> str:
    base = csv_path[:-4] if csv_path.lower().endswith(".csv") else csv_path
    return base + suffisso


def accoda_canali(csv_path: str, righe: list) -> None:
    """Una riga per mondo x canale: serve al §5-bis della pre-registrazione
    (larghezza relativa dell'intervallo e Spearman fra classifica stimata e
    vera). Senza questo file quelle due misure non sono calcolabili, e non si
    recuperano se non rifacendo i fit."""
    p = percorso_affiancato(csv_path, "_canali.csv")
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    nuovo = not (os.path.exists(p) and os.path.getsize(p) > 0)
    with open(p, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLONNE_CANALI, extrasaction="ignore")
        if nuovo:
            w.writeheader()
        for r in righe:
            w.writerow({c: r.get(c, "") for c in COLONNE_CANALI})
        f.flush()
        os.fsync(f.fileno())


def salva_draw(csv_path: str, nome_mondo: str, canali: list, arr) -> str:
    """I draw del posterior, compressi: una riga per draw, una colonna per
    canale piu' 'totale' GIA' SOMMATO DENTRO IL DRAW.

    E' il formato che rende impossibile l'errore di sommare i quantili canale
    per canale (quello che produsse la forbice 0,45-4,79): chi legge questo
    file ha gia' il totale corretto e non deve ricostruirlo."""
    import gzip
    dir_draw = percorso_affiancato(csv_path, "_draw")
    os.makedirs(dir_draw, exist_ok=True)
    p = os.path.join(dir_draw, nome_mondo + "_draw.csv.gz")
    piatto = arr.reshape(-1, len(canali))
    with gzip.open(p, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(list(canali) + ["totale"])
        for d in piatto:
            w.writerow([round(float(x), 2) for x in d] +
                       [round(float(d.sum()), 2)])
    return p


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
    # Il disegno entra nel NOME del mondo, non in una colonna nuova: il CSV
    # resta a colonne identiche a quelle dello studio osservativo e le due
    # tabelle si affiancano senza conversioni. La colonna "mondo" dice da sola
    # quale disegno e' stato misurato.
    nome_mondo = "mondo_" + format(args.seed_mondo, "04d")
    flag_param, param_norm, suff_mondo = parametri_disegno(args.disegno,
                                                          args.parametri_disegno)
    if args.disegno in ("randomizzato", "sanita"):
        nome_mondo += "_sanita"
    elif args.disegno != "base":
        nome_mondo += "_" + args.disegno + suff_mondo
    mondo_dir = os.path.join(repo, "dati_simulati_mondi", nome_mondo)
    output_tmp = os.path.join(mondo_dir, "_output_fit")
    risposte: list[str] = []
    # Etichetta del run nel registro (colonna "mondo", nome del file dei
    # draw): con --nome-run e' autodescrittiva, dataset_nodi_prior_seme
    # (es. base_96_rif_s42, sanita_40_anc030_s42), e una riga si legge da
    # sola senza incrociare la tabella. Senza, resta il nome della cartella
    # del generatore, come nello studio di copertura.
    if args.nome_run is not None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.nome_run):
            raise SystemExit("--nome-run non valido (solo lettere, cifre, "
                             "_ . -): " + repr(args.nome_run))
        nome_mondo = args.nome_run
    riga = {"mondo": nome_mondo, "seed_mondo": args.seed_mondo,
            "keep": args.keep, "n_chains": args.n_chains,
            "adapt": args.n_adapt, "burnin": args.n_burnin,
            "seed_mcmc": args.seed_mcmc, "esito": "errore", "errore": "",
            "disegno": args.disegno, "canali_trattati": "",
            "parametri_disegno": param_norm}
    dettaglio_canali: dict = {}   # canale -> dose, riduzione, spesa vs base

    try:
        # --- 1. genera il mondo (deterministico dal suo seme) ----------------
        #        oppure, con --dati-modello, usa un dataset GIA' PRESENTE
        if args.dati_modello is None:
            # Ogni disegno e' lo STESSO mondo con una spesa diversa: la
            # verita' per canale resta quella del mondo base (beta ricalibrato
            # sullo stesso target); cambiano solo dove/quando/come si spende.
            comando_gen = ([sys.executable,
                            os.path.join(repo, "genera_dati_simulati.py"),
                            "--seed-mondo", str(args.seed_mondo)]
                           + FLAG_DISEGNO[args.disegno] + flag_param)
            if suff_mondo:
                comando_gen += ["--suffisso-mondo", suff_mondo]
            subprocess.run(comando_gen,
                           cwd=repo, check=True, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            dir_dati = os.path.join(mondo_dir, "modello")
            percorso_verita = os.path.join(mondo_dir, "verita",
                                           "contributo_vero.csv")
            percorso_benchmark = os.path.join(mondo_dir, "benchmark",
                                              "roas_piattaforma_trimestrale.csv")
            if not os.path.isdir(dir_dati):
                raise SystemExit("il generatore non ha scritto " + dir_dati +
                                 ": nome della cartella del mondo diverso da "
                                 "quello atteso dal runner")
            riga["canali_trattati"], dettaglio_canali = leggi_disegno(
                os.path.join(mondo_dir, "verita", "parametri_generazione.json"),
                args.disegno)
            if args.disegno == "blackout":
                riga.update(leggi_costo_blackout(
                    os.path.join(mondo_dir, "verita",
                                 "parametri_generazione.json")))
            if args.controllo_baseline:
                import numpy as _np_c
                import pandas as _pd_c
                _col, _rho, _ = scrivi_controllo_baseline(
                    mondo_dir, dir_dati, args.seed_mondo,
                    args.controllo_baseline, _np_c, _pd_c)
                riga["controllo_baseline_colonna"] = _col
                riga["controllo_baseline_rho"] = _rho
            riga["controllo_baseline_f"] = args.controllo_baseline or 0.0
        else:
            if args.disegno != "base":
                raise SystemExit("--disegno " + args.disegno + " non ha senso "
                                 "con --dati-modello: il disegno e' quello del "
                                 "dataset indicato")
            dir_dati, percorso_verita = dataset_esistente(args.dati_modello, repo)
            percorso_benchmark = os.path.join(
                os.path.dirname(os.path.dirname(dir_dati)), "benchmark",
                "roas_piattaforma_trimestrale" + os.path.basename(dir_dati)[len("modello"):] + ".csv")
            # Cartella di lavoro SEPARATA dai dati: la pulizia finale cancella
            # solo questa, mai il dataset del repo.
            mondo_dir = os.path.join(repo, "dati_simulati_mondi",
                                     "_lavoro_" + nome_mondo)
            output_tmp = os.path.join(mondo_dir, "_output_fit")
            shutil.rmtree(mondo_dir, ignore_errors=True)
            print("[dati] dataset gia' presente: " + dir_dati)
            print("[dati] verita' del dataset : " + percorso_verita)

        # --- 2. celle del notebook congelato ---------------------------------
        celle = carica_celle(os.path.join(repo, "colab_end_to_end.ipynb"),
                             ["CELLA 2", "CELLA 3", "CELLA 5",
                              "CELLA 6", "CELLA 7", "CELLA 9"])
        ns = costruisci_namespace(mondo_dir, output_tmp, args.keep,
                                  args.seed_mcmc, risposte)
        exec(compile(celle["CELLA 2"], "CELLA2", "exec"), ns)
        blinda_helper(ns, risposte)

        # Config dello studio: dichiarata nel CSV, riga per riga.
        # I default della CONFIG del notebook NON fanno fede qui (3 nodi per
        # trimestre e keep 1000: chi la eredita ottiene 24 nodi e meta' draw
        # con la stessa etichetta "seed 42" e nessun errore). I nodi arrivano
        # dalla riga di comando: 12 per trimestre = 96 nodi (canonico),
        # 5 = 40, 4 = 32, 3 = 24; il CSV riporta N_KNOTS effettivo.
        ns["KNOTS_PER_QUARTER"] = int(args.knots_per_quarter)
        ns["N_CHAINS"] = args.n_chains
        ns["N_ADAPT"] = args.n_adapt
        ns["N_BURNIN"] = args.n_burnin
        ns["N_KEEP"] = args.keep
        ns["SEED"] = args.seed_mcmc
        # Prior sul ROI: 'riferimento' = LogNormal(0.2, 0.9) uguale per tutti
        # i canali (quello dei run canonici); 'ancorato' = mu = log(ROI VERO)
        # canale per canale (ROI_ANCORATI) con sigma da --prior-sigma. La
        # cella 9 del notebook legge USA_PRIOR_INFORMATIVI, PRIOR_ROI_SIGMA_INF
        # e PRIOR_ROAS_CANALE e si ferma da sola se un canale manca.
        # R6: prior parametrico. 'riferimento' = LogNormal(mu, sigma) uguale per
        # tutti i canali, mu e sigma da riga di comando (default 0.2 e 0.9: il
        # percorso senza flag e' identico ai run canonici); 'ancorato' = mu =
        # log(ROI vero) per canale (ROI_ANCORATI); 'ancorato-benchmark' = mu =
        # log(ROAS di piattaforma del benchmark del mondo) per canale (D9c).
        if args.prior in PRIOR_ANCORATI and args.prior_sigma is None:
            raise SystemExit("--prior " + args.prior + " richiede --prior-sigma")
        if args.prior in PRIOR_ANCORATI and args.prior_mu is not None:
            raise SystemExit("--prior-mu vale solo con --prior riferimento: nei prior "
                             "ancorati mu = log(ROAS) canale per canale")
        prior_mu = 0.2 if args.prior_mu is None else float(args.prior_mu)
        prior_sigma = (0.9 if args.prior_sigma is None else float(args.prior_sigma))
        ns["USA_PRIOR_INFORMATIVI"] = (args.prior in PRIOR_ANCORATI)
        ns["PRIOR_ROI_MU"] = prior_mu
        ns["PRIOR_ROI_SIGMA"] = prior_sigma
        roas_prior: dict = {}
        if args.prior == "ancorato":
            roas_prior = dict(ROI_ANCORATI)
        elif args.prior == "ancorato-benchmark":
            roas_prior = roas_benchmark(percorso_benchmark)
        if roas_prior:
            ns["PRIOR_ROI_SIGMA_INF"] = prior_sigma
            ns["PRIOR_ROAS_CANALE"] = dict(roas_prior)
        riga["prior_tipo"] = args.prior
        riga["prior_sigma"] = prior_sigma
        riga["prior_mu"] = "" if roas_prior else prior_mu
        riga["prior_mu_per_canale"] = ";".join(c + "=" + str(roas_prior[c]) for c in roas_prior)
        ns["KPI"] = "auto"
        ns["PERIODO"] = "auto"
        ns["GEO"] = "auto"
        ns["VALUTA"] = "auto"

        exec(compile(celle["CELLA 3"], "CELLA3", "exec"), ns)

        # dati del mondo: SOLO la cartella modello/ (la verita' non entra mai);
        # dir_dati e' fissato al passo 1 (generato oppure gia' presente)
        riga["decimali_stagionalita"] = decimali_stagionalita(dir_dati)
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
        # D13: il controllo deve essere entrato come CONTROLLO. Se f > 0 e i
        # controlli restano due (i due del mondo base), il file e' stato letto
        # come altro e la riga mentirebbe.
        _ctrl = list(ns.get("CONTROLLI") or [])
        riga["controlli_nel_modello"] = ";".join(_ctrl)
        if args.controllo_baseline:
            _atteso = "ctrl_" + str(riga.get("controllo_baseline_colonna") or "")
            if _atteso not in _ctrl:
                raise SystemExit(
                    "--controllo-baseline: la colonna " + _atteso + " NON e' "
                    "fra i controlli del modello (" + ", ".join(_ctrl) + "): "
                    "l'ingestion l'ha classificata diversamente e il run "
                    "misurerebbe un'altra cosa.")
            if str(riga.get("controllo_baseline_colonna")) in \
                    [str(x) for x in ns.get("CANALI_MODELLO", [])]:
                raise SystemExit("--controllo-baseline: la colonna e' finita "
                                 "fra i canali media")

        n_geo = int(ns["N_GEOS"]); n_sett = int(ns["N_SETTIMANE"])
        canali = list(ns["CANALI_MODELLO"])
        # Le settimane della finestra del fit sono l'INTERSEZIONE dei periodi
        # delle fonti (cella 5): un dataset i cui file media saltano le
        # settimane a spesa zero (la pause vecchia: 102 invece di 104) ha una
        # finestra piu' corta, e la verita' viene sommata su QUELLA finestra.
        # Il numero va dichiarato con --settimane-attese, mai indovinato.
        _struttura_attesa = (20, int(args.settimane_attese), 7)
        if (n_geo, n_sett, len(canali)) != _struttura_attesa:
            raise SystemExit("struttura del mondo inattesa: " +
                             str((n_geo, n_sett, len(canali))) +
                             " invece di " + str(_struttura_attesa))

        # verita' del mondo, sulla finestra del fit, in EUR (x 40)
        vero_conv, vero_canale_conv = verita_del_mondo(
            percorso_verita, ns["SETTIMANE"], canali, ns["pd"])
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
        # Lo stesso calcolo della cella 9: se non torna, i nodi passati non
        # sono quelli usati e la riga non deve sembrare corretta.
        _knots_attesi = min(n_sett, max(1, int(round(
            n_sett / 13.0 * int(args.knots_per_quarter)))))
        if riga["n_knots"] != _knots_attesi:
            raise SystemExit("N_KNOTS = " + str(riga["n_knots"]) + " invece di " +
                             str(_knots_attesi) + " (" +
                             str(args.knots_per_quarter) + " per trimestre)")
        riga["divergenze"] = int(ns.get("DIVERGENZE", -1))
        riga["impronta_input_data"] = str(
            (ns.get("IMPRONTA_INPUT_DATA") or {}).get("hash_spesa", "n/d"))
        # La cella 9 dice quale prior ha USATO davvero: deve coincidere con
        # quello chiesto, altrimenti la riga mentirebbe sul prior.
        if bool(ns.get("PRIOR_INFO_ATTIVI")) != (args.prior in PRIOR_ANCORATI):
            raise SystemExit("prior richiesto '" + args.prior + "' ma la cella 9 "
                             "ha usato PRIOR_INFO_ATTIVI=" +
                             str(ns.get("PRIOR_INFO_ATTIVI")))

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

        # --- 5-bis. dettaglio per canale + draw compressi --------------------
        spesa_ch = ns["DF_TIDY"].groupby("channel")["spend"].sum()
        righe_ch = []
        for j, c in enumerate(canali):
            s = arr[..., j].reshape(-1)
            l, h = np.quantile(s, [0.05, 0.95])
            med = float(np.median(s))
            v = float(vero_canale[c])
            sp = float(spesa_ch.get(c, float("nan")))
            righe_ch.append({
                "mondo": nome_mondo, "seed_mondo": args.seed_mondo, "canale": c,
                "spesa": round(sp, 2), "vero": round(v, 1),
                "mediana": round(med, 1),
                "ci05": round(float(l), 1), "ci95": round(float(h), 1),
                "larghezza_relativa": (round((float(h) - float(l)) / med, 4)
                                       if med > 0 else ""),
                "dentro": int(bool(l <= v <= h)),
                "pit": round(float(np.mean(s <= v)), 6),
                "roi_vero": round(v / sp, 4) if sp > 0 else "",
                "roi_stimato": round(med / sp, 4) if sp > 0 else "",
                **dettaglio_canali.get(c, {"trattato": "", "dose_pct": "",
                                           "riduzione_effettiva_pct": "",
                                           "spesa_vs_base_pct": "",
                                           "spesa_ridistribuita_eur": ""}),
            })

        # Spearman fra la classifica dei canali per ROI stimato e quella per
        # ROI vero DI QUESTO mondo: rango dei ranghi, senza dipendenze nuove.
        # Calcolato qui e non a posteriori: il valore resta quello della misura.
        def _rango(valori):
            a = np.asarray(valori, dtype=float)
            return np.argsort(np.argsort(a)).astype(float)

        _rv = [r["roi_vero"] for r in righe_ch]
        _rs = [r["roi_stimato"] for r in righe_ch]
        rho = ""
        if all(isinstance(x, float) for x in _rv + _rs):
            rho = round(float(np.corrcoef(_rango(_rv), _rango(_rs))[0, 1]), 4)
        for r in righe_ch:
            r["rho_spearman"] = rho
        accoda_canali(args.csv, righe_ch)
        salva_draw(args.csv, nome_mondo, canali, arr)

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
        # Si cancella SOLO dentro dati_simulati_mondi/ (mondi generati e
        # cartelle di lavoro): un dataset congelato del repo non passa mai di
        # qui, e se per errore ci arrivasse resta al suo posto.
        if not args.conserva_mondo:
            if os.path.basename(os.path.dirname(mondo_dir)) == "dati_simulati_mondi":
                shutil.rmtree(mondo_dir, ignore_errors=True)
            else:
                print("[guardia] NON cancello " + mondo_dir +
                      ": non e' una cartella di lavoro")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed-mondo", type=int, required=True,
                    help="seme del generatore (colonna seed_mondo). Con "
                         "--dati-modello non genera nulla: e' solo il seme "
                         "dichiarato del dataset (42 per quelli della tesi)")
    ap.add_argument("--dati-modello", default=None,
                    help="cartella modello<suffisso> di un dataset GIA' "
                         "presente nel repo (es. dati_simulati/geo/modello_geo, "
                         "relativa a --repo se non assoluta): il passo di "
                         "generazione viene saltato e la "
                         "verita' e' <radice>/verita/contributo_vero<suffisso>"
                         ".csv, quella di QUEL dataset. Il dataset non viene "
                         "mai toccato ne' cancellato")
    ap.add_argument("--settimane-attese", type=int, default=104,
                    help="settimane della finestra del fit (intersezione dei "
                         "periodi delle fonti): 104 per i mondi generati; 102 "
                         "per la pause vecchia, i cui file media saltano le "
                         "settimane a spesa zero. La guardia di struttura "
                         "confronta con questo valore")
    ap.add_argument("--disegno", choices=DISEGNI, default="base",
                    help="disegno della spesa del mondo: 'base' = osservativo "
                         "(la spesa segue la domanda); 'randomizzato' (alias "
                         "'sanita') = lognormale iid sigma 0.60; 'geo' = "
                         "esperimento geografico (--parametri-disegno "
                         "canali=..;regioni=..;blocchi=NxL;intensita=..;"
                         "sfalsato=1); 'calendario' = sette canali a rotazione "
                         "(rotazione=i); 'casuale2' = spesa scorrelata dalla "
                         "stagionalita'; 'pause2' = blackout temporali. Il "
                         "mondo, la verita' per canale e tutto il resto della "
                         "configurazione restano gli stessi: cambia SOLO come "
                         "la spesa e' distribuita")
    ap.add_argument("--controllo-baseline", type=float, default=None,
                    help="D13: aggiunge ai dati del modello una variabile di "
                         "controllo costruita dalla baseline VERA del mondo, "
                         "c = f x organico_vero x exp(N(0, 0,15)), rng "
                         "default_rng(seed_mondo + 31). f e' questo valore "
                         "(0,30 / 0,60 / 0,90 nella griglia D13); 0 o assente "
                         "= nessun file scritto, run identico a D0. I file "
                         "media e il KPI non vengono toccati")
    ap.add_argument("--parametri-disegno", default=None,
                    help="parametri del disegno, 'chiave=valore;...' (vedi "
                         "--disegno); finiscono nella colonna parametri_disegno "
                         "e nel nome della cartella del mondo")
    ap.add_argument("--repo", required=True,
                    help="cartella del repo (contiene generatore e notebook)")
    ap.add_argument("--csv", required=True,
                    help="CSV dei risultati (una riga per mondo, append)")
    ap.add_argument("--keep", type=int, default=2000,
                    help="N_KEEP: 2000 come i run canonici; se ridotto, "
                         "ridotto UGUALE per tutti i mondi e dichiarato")
    ap.add_argument("--knots-per-quarter", type=int, default=12,
                    help="nodi della baseline per trimestre: 12 = 96 nodi "
                         "(canonico), 5 = 40, 4 = 32, 3 = 24. Sovrascrive "
                         "SEMPRE la CONFIG del notebook (che dice 3)")
    ap.add_argument("--n-chains", type=int, default=4)
    ap.add_argument("--n-adapt", type=int, default=500)
    ap.add_argument("--n-burnin", type=int, default=500)
    ap.add_argument("--prior", choices=("riferimento", "ancorato", "ancorato-benchmark"),
                    default="riferimento",
                    help="'riferimento' = LogNormal(mu, sigma) per tutti i "
                         "canali (default 0.2 e 0.9: run canonici; --prior-mu e "
                         "--prior-sigma li cambiano, D9a/D9b); 'ancorato' = prior "
                         "centrato sul ROI VERO di ogni canale (ROI_ANCORATI): "
                         "circolare, fuori dai risultati; 'ancorato-benchmark' = "
                         "centrato sul ROAS di piattaforma del benchmark del mondo "
                         "(aggregato sul periodo per canale: informazione "
                         "realistica ma gonfiata, D9c)")
    ap.add_argument("--prior-mu", type=float, default=None,
                    help="mu (scala log) del prior di riferimento, default 0.2; "
                         "vietato con i prior ancorati")
    ap.add_argument("--prior-sigma", type=float, default=None,
                    help="sigma (scala log) del prior: default 0.9 col prior di "
                         "riferimento; obbligatorio con ancorato e "
                         "ancorato-benchmark (es. 0.90 o 0.30)")
    ap.add_argument("--seed-mcmc", type=int, default=42,
                    help="seme MCMC: 42 per tutti i mondi (il mondo varia "
                         "col SUO seme, non con questo)")
    ap.add_argument("--conserva-mondo", action="store_true",
                    help="non cancellare la cartella del mondo a fine misura")
    ap.add_argument("--nome-run", default=None,
                    help="etichetta del run nel registro (colonna 'mondo' e "
                         "nome del file dei draw), es. base_96_rif_s42. "
                         "Default: nome della cartella del generatore")
    _a = ap.parse_args()
    if _a.controllo_baseline is not None:
        if not 0.0 <= _a.controllo_baseline <= 1.0:
            ap.error("--controllo-baseline fra 0 e 1")
        if _a.dati_modello is not None:
            ap.error("--controllo-baseline richiede un mondo generato: la "
                     "baseline vera sta in verita/candidature_organiche.csv "
                     "del mondo, non in un dataset gia' presente")
    sys.exit(esegui_mondo(_a))


if __name__ == "__main__":
    main()
