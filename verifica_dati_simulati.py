# -*- coding: utf-8 -*-
"""
Verifica del dataset simulato: l'ingestion lo legge? e' identificabile?

Non lancia il fit Meridian. Esegue, in ordine:

  1. mappa dei ruoli   cosa vede l'ingestion in ogni colonna di ogni file
  2. ingestion vera    celle CONFIG + ingestion + harmonization del notebook
                       kaggle_end_to_end.ipynb, eseguite qui senza modificarlo
  3. lettore B         pipeline/ingestion + validazione di schema
  4. collinearita'     corr spesa/stagionalita', corr spesa/spesa, VIF,
                       contrasto geografico, settimane a zero
  5. curve vere        un grafico per canale: spesa -> candidature incrementali
  6. stage 2           ordinamento intra-canale, fattore k, somme attribuite
  7. cella 8-bis       diagnostica di separabilita' delle tipologie

    python verifica_dati_simulati.py
    python verifica_dati_simulati.py --cartella dati_simulati/modello_diagnostica_q30
    python verifica_dati_simulati.py --interattivo   # conferme reali ai checkpoint
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import difflib
import io
import json
import os
import re
import unicodedata

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
NOTEBOOK = os.path.join(ROOT, "kaggle_end_to_end.ipynb")

# celle del notebook riusate (indici nel file .ipynb)
CELLA_CONFIG = 4
CELLA_INGESTION = 6
CELLA_INGEST_CP1 = 10
CELLA_HARMONIZE_CP2 = 12
CELLA_SPLIT_8BIS = 18

# Seed usati per il valore ATTESO dello Spearman. Con 4-6 campagne per canale
# una sola realizzazione dice piu' sul seed che sul meccanismo.
SEED_MULTISEED = (42, 7, 123, 2024, 99, 555, 31, 17)


class Tee:
    """Stampa a schermo e accumula per il report su file."""

    def __init__(self):
        self.righe: list[str] = []

    def __call__(self, testo: str = "") -> None:
        print(testo)
        self.righe.append(testo)

    def salva(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.righe) + "\n")


class Doppio:
    """stdout che scrive a schermo E accumula nel report (modo interattivo)."""

    def __init__(self, log: "Tee", reale):
        self.log, self.reale, self.buf = log, reale, ""

    def write(self, testo: str) -> int:
        self.reale.write(testo)
        self.buf += testo
        while chr(10) in self.buf:
            riga, self.buf = self.buf.split(chr(10), 1)
            self.log.righe.append(riga)
        return len(testo)

    def flush(self) -> None:
        self.reale.flush()


def celle(nb_path: str) -> list[str]:
    nb = json.load(open(nb_path, encoding="utf-8"))
    return ["".join(c["source"]) for c in nb["cells"]]


def prepara_notebook(auto_conferma: bool = True) -> dict:
    """Esegue CONFIG + funzioni di ingestion del notebook in un namespace."""
    src = celle(NOTEBOOK)
    ns: dict = {"re": re, "io": io, "csv": csv, "os": os, "json": json,
                "unicodedata": unicodedata, "difflib": difflib,
                "np": np, "pd": pd}
    silenzio = io.StringIO()
    with contextlib.redirect_stdout(silenzio):
        exec(src[CELLA_CONFIG], ns)
        exec(src[CELLA_INGESTION], ns)
    ns["AUTO_CONFERMA"] = auto_conferma
    ns["_src"] = src
    return ns


def leggi_cartella(cartella: str) -> dict:
    est = (".csv", ".tsv", ".txt", ".xlsx", ".xls", ".json")
    out = {}
    for nome in sorted(os.listdir(cartella)):
        if os.path.splitext(nome)[1].lower() in est:
            with open(os.path.join(cartella, nome), "rb") as f:
                out[nome] = f.read()
    return out


# =============================================================================
# 1. mappa dei ruoli
# =============================================================================

def mappa_ruoli(ns: dict, cartella: str, log: Tee) -> None:
    log("=" * 78)
    log("1. MAPPA DEI RUOLI - cosa vede l'ingestion in ogni colonna")
    log("=" * 78)
    log("(ruolo None = colonna non riconosciuta: se numerica diventa un "
        "controllo ctrl_*)")
    for nome, dati in leggi_cartella(cartella).items():
        tabelle = ns["leggi_file_grezzo"](nome, dati)
        for nome_tab, grezza in tabelle.items():
            df, _h = ns["pulisci_tabella"](grezza)
            log(f"\n  {nome_tab}   ({len(df):,} righe)")
            for col in df.columns:
                ruolo, punteggio = ns["abbina_colonna"](col)
                etichetta = f"{ruolo} ({punteggio:.2f})" if ruolo else "-"
                log(f"     {str(col):<26} -> {etichetta}")
            if "canale" in [str(c).lower() for c in df.columns]:
                col = [c for c in df.columns if str(c).lower() == "canale"][0]
                valori = sorted(df[col].astype(str).unique())[:4]
                mappati = {v: ns["mappa_canale"](v) for v in valori}
                log(f"     canale: {mappati}")


# =============================================================================
# 2. ingestion + harmonization del notebook
# =============================================================================

def ingestion_notebook(ns: dict, cartella: str, log: Tee,
                       interattivo: bool = False) -> dict:
    log("\n" + "=" * 78)
    log("2. INGESTION VERA (celle 3, 5 e 6 di kaggle_end_to_end.ipynb)")
    log("=" * 78)
    ns["FILES_GREZZI"] = leggi_cartella(cartella)
    log(f"  {len(ns['FILES_GREZZI'])} file da {cartella}")

    import sys
    buffer = io.StringIO()
    ctx = (contextlib.redirect_stdout(Doppio(log, sys.stdout)) if interattivo
           else contextlib.redirect_stdout(buffer))
    with ctx:
        exec(ns["_src"][CELLA_INGEST_CP1], ns)
        exec(ns["_src"][CELLA_HARMONIZE_CP2], ns)
    testo = buffer.getvalue()
    if not interattivo:
        # riporto solo le parti decisive (i due checkpoint e le scelte)
        tieni = [r for r in testo.splitlines()
                 if r.startswith(("ruolo=", "  ruolo=", "[DQ]", "CHECKPOINT",
                                  "  - ", "  * ", "[AUTO_CONFERMA", "  ["))
                 or "KPI" in r or "candidati" in r]
        for r in tieni:
            log("  " + r)
    else:
        log("")
        log("  (le risposte ai prompt sono state fornite da stdin: la sessione "
            "esercita davvero il ramo interattivo, ma non c'e' una persona che "
            "digita. I checkpoint 3-6 richiedono Meridian e il fit.)")

    log("\n  --- esito ---")
    log(f"  geo: {len(ns['GEOS'])} | settimane: {len(ns['SETTIMANE'])} | "
        f"canali: {len(ns['CANALI'])}")
    log(f"  canali riconosciuti: {', '.join(ns['CANALI'])}")
    log(f"  controlli tenuti   : {', '.join(ns['CONTROLLI']) or 'nessuno'}")
    log(f"  KPI scelto         : {ns['KPI_DESCR']}")
    log(f"  KPI totale         : {int(ns['DF_BASE']['kpi'].sum()):,}")
    log(f"  spesa totale       : {ns['DF_TIDY']['spend'].sum():,.0f} EUR")
    log(f"  righe base tidy    : {len(ns['DF_TIDY']):,} "
        f"(= {len(ns['GEOS'])} x {len(ns['SETTIMANE'])} x {len(ns['CANALI'])})")
    return ns


# =============================================================================
# 3. lettore B: pipeline/ingestion
# =============================================================================

def ingestion_pipeline(cartella: str, log: Tee) -> None:
    log("\n" + "=" * 78)
    log("3. LETTORE B - pipeline/ingestion (app locale e vm_check)")
    log("=" * 78)
    try:
        from pipeline import schema
        from pipeline.ingestion import build
    except Exception as e:                                   # pragma: no cover
        log(f"  [saltato] import fallito: {e}")
        return

    silenzio = io.StringIO()
    with contextlib.redirect_stdout(silenzio):
        piani, tabelle = build.propose_plan(cartella)
        # Esclusione human-in-the-middle di due file che il lettore B non sa
        # usare: il KPI aggregato (qui l'outcome arriva solo da un file
        # individuale) e l'anagrafica di popolazione. Senza l'esclusione il
        # KPI verrebbe sommato dentro il controllo candidate_searches, perche'
        # _demand_variable_from_filename mappa 'candidature' su quella serie.
        ESCLUSI = ("candidature_settimanali.csv", "popolazione_regioni.csv")
        for p in piani:
            p.confirmed = p.file not in ESCLUSI
        tenuti = [p for p in piani if p.confirmed]
        esito = build.ingest(cartella, plan=tenuti, interactive=False,
                             out_dir=os.path.join(ROOT, "dati_simulati",
                                                  "verita", "_canonici_lettore_b"),
                             tables=tabelle, salt="verifica")
    log("  riconoscimento sorgenti:")
    for p in piani:
        stato = "confermato" if p.confirmed else "ESCLUSO a mano"
        log(f"     {p.file:<34} tipo={p.kind:<12} canale={p.channel or '-':<12} {stato}")
    fatti = esito["facts"]
    log("\n  fatti canonici prodotti:")
    for nome, df in fatti.items():
        log(f"     {nome:<12} {len(df):>7,} righe")
    rep = schema.validate_all(fatti)
    for nome, r in rep.items():
        stato = "OK" if r.ok else "ERRORI: " + " | ".join(r.errors)
        log(f"     validazione {nome:<12} {stato}")
        for w in r.warnings[:2]:
            log(f"        avviso: {w}")
    if "media" in fatti:
        canali = sorted(fatti["media"]["channel"].unique())
        log(f"\n  canali visti dal lettore B: {canali}")
    log("  NOTA: il lettore B riconosce il canale dal NOME FILE (regex "
        "google|meta|facebook|linkedin|indeed): i tre job board minori "
        "finiscono in 'sconosciuto'.")
    log("  NOTA: il fatto 'outcome' non viene prodotto perche' richiede un "
        "file INDIVIDUALE con dati personali, che questo dataset non contiene "
        "per scelta (minimizzazione dei dati). Il Cap. 5 gira sul notebook.")


# =============================================================================
# 4. collinearita' e identificazione
# =============================================================================

def _vif(X: pd.DataFrame) -> dict:
    out = {}
    Z = (X - X.mean()) / X.std().replace(0, np.nan)
    for c in Z.columns:
        y = Z[c].to_numpy()
        A = np.column_stack([np.ones(len(Z))] +
                            [Z[o].to_numpy() for o in Z.columns if o != c])
        beta, *_ = np.linalg.lstsq(A, y, rcond=None)
        r2 = 1.0 - float(np.sum((y - A @ beta) ** 2) / np.sum((y - y.mean()) ** 2))
        out[c] = float(1.0 / max(1e-9, 1.0 - r2))
    return out


def collinearita(ns: dict, p: dict, log: Tee) -> None:
    log("\n" + "=" * 78)
    log("4. COLLINEARITA' E IDENTIFICAZIONE")
    log("=" * 78)
    tidy = ns["DF_TIDY"]
    naz = tidy.groupby(["week", "channel"])["spend"].sum().unstack(fill_value=0.0)
    kpi = ns["DF_BASE"].groupby("week")["kpi"].sum()
    stag = pd.Series(p["seas_naz"], index=pd.DatetimeIndex(p["settimane"]))
    stag = stag.reindex(naz.index)

    log("\n  spesa vs indice stagionale (target 0,40-0,60: il budget segue la")
    log("  domanda, ma imperfettamente; se fosse collineare il fit non "
        "identificherebbe nulla)")
    log(f"     {'canale':<20}{'corr(spesa,stag)':>18}{'corr(spesa,KPI)':>18}"
        f"{'sett. a zero':>14}{'quota spesa':>13}")
    tot_spesa = naz.sum().sum()
    for ch in naz.columns:
        c1 = float(np.corrcoef(naz[ch], stag)[0, 1])
        c2 = float(np.corrcoef(naz[ch], kpi.reindex(naz.index))[0, 1])
        nz = int((naz[ch] == 0).sum())
        log(f"     {ch:<20}{c1:>18.2f}{c2:>18.2f}{nz:>14}"
            f"{naz[ch].sum() / tot_spesa:>12.1%}")

    log("\n  correlazione spesa x spesa tra canali")
    corr = naz.corr()
    intestazione = "".join(f"{c[:11]:>13}" for c in corr.columns)
    log(f"     {'':<20}{intestazione}")
    for ch in corr.index:
        log(f"     {ch:<20}" + "".join(f"{corr.loc[ch, o]:>13.2f}"
                                       for o in corr.columns))
    fuori = corr.values[~np.eye(len(corr), dtype=bool)]
    log(f"     massima correlazione fuori diagonale: {fuori.max():.2f}")

    log("\n  VIF (collinearita' multipla; >5 = intervalli larghi da attendersi)")
    for ch, v in _vif(naz).items():
        log(f"     {ch:<20}{v:>8.2f}")

    log("\n  contrasto geografico della spesa (Sez. 3.4: con quote regionali")
    log("  fisse l'identificazione torna nazionale in silenzio)")
    for ch in p["canali"]:
        X = p["ch_spesa"][ch]
        quote = X / np.maximum(X.sum(axis=1, keepdims=True), 1e-9)
        cv = float(np.mean(quote.std(axis=0) /
                           np.maximum(quote.mean(axis=0), 1e-9)))
        log(f"     {ch:<20} CV temporale delle quote regionali {cv:>6.3f}"
            + ("   (0 = quote fisse)" if ch == p["canali"][0] else ""))

    log("\n  proporzionalita' spesa/impression (i due rami della pipeline usano")
    log("  metriche di esecuzione diverse: devono vedere la stessa curva)")
    for ch in p["canali"]:
        s = p["ch_spesa"][ch].sum(axis=1)
        i = p["ch_impr"][ch].sum(axis=1)
        cpm = np.divide(s, np.maximum(i, 1)) * 1000
        cpm = cpm[s > 0]
        log(f"     {ch:<20} corr {np.corrcoef(s, i)[0, 1]:>6.4f}   "
            f"CPM medio {cpm.mean():>6.2f} EUR   CV {cpm.std() / cpm.mean():.3f}")

    quota = p["quota_media_realizzata"]
    log(f"\n  quota delle candidature spiegata dai media: {quota:.1%} "
        f"(baseline {1 - quota:.1%})")
    if quota < 0.25:
        log("  e' il caso difficile del recruiting: la baseline domina, e un "
            "piccolo errore sulla baseline si scarica sui canali.")
    else:
        log("  VARIANTE DIAGNOSTICA: quota dei media piu' alta del realistico. "
            "Serve a distinguere 'il metodo non identifica' da 'questo settore "
            "e' difficile'. Non e' lo scenario del Capitolo 5.")


# =============================================================================
# 5. curve vere
# =============================================================================

def curve_vere(p: dict, dir_out: str, log: Tee) -> pd.DataFrame:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from genera_dati_simulati import CANALI, VALORE_CANDIDATURA_EUR, hill

    os.makedirs(dir_out, exist_ok=True)
    log("\n" + "=" * 78)
    log("5. CURVE VERE spesa -> candidature incrementali (a regime)")
    log("=" * 78)
    pop = p["pop"]
    righe = []
    for ch in p["canali"]:
        c = CANALI[ch]
        spesa_g = p["ch_spesa"][ch]
        impr_g = p["ch_impr"][ch]
        attive = spesa_g.sum(axis=1) > 0
        spesa_media = float(spesa_g[attive].sum(axis=1).mean())
        quote = spesa_g[attive].sum(axis=0)
        quote = quote / quote.sum()
        cpm = float(spesa_g[attive].sum() / max(impr_g[attive].sum(), 1) * 1000)
        beta_g = p["beta"][ch] * p["beta_geo"][ch] * pop

        def risposta(spesa_naz: np.ndarray) -> np.ndarray:
            # a regime la spesa e' costante: l'adstock normalizzato = la spesa
            impr_pc = (spesa_naz[:, None] * quote[None, :] / cpm * 1000.0
                       / pop[None, :])
            return (hill(impr_pc, c["_ec_impr"], c["slope"])
                    * beta_g[None, :]).sum(axis=1)

        x = np.linspace(0.0, 2.6 * spesa_media, 160)
        y = risposta(x)
        d = 0.01 * spesa_media
        mroi = float((risposta(np.array([spesa_media + d]))[0]
                      - risposta(np.array([spesa_media - d]))[0])
                     / (2 * d) * VALORE_CANDIDATURA_EUR)
        roi_medio = float(risposta(np.array([spesa_media]))[0]
                          * VALORE_CANDIDATURA_EUR / spesa_media)
        righe.append(dict(canale=ch, spesa_media_settimanale=round(spesa_media),
                          roi_medio=round(roi_medio, 2),
                          roi_marginale=round(mroi, 2),
                          lam=c["lam"], slope=c["slope"], ec_mult=c["ec_mult"]))

        plt.figure(figsize=(6.4, 4.0))
        plt.plot(x, y, lw=2)
        plt.axvline(spesa_media, ls="--", lw=1,
                    label=f"spesa media osservata ({spesa_media:,.0f} EUR)")
        plt.scatter([spesa_media], [risposta(np.array([spesa_media]))[0]], zorder=5)
        plt.title(f"{ch}: spesa settimanale -> candidature incrementali (vero)")
        plt.xlabel("spesa settimanale nazionale (EUR)")
        plt.ylabel("candidature incrementali/settimana")
        plt.legend(fontsize=8)
        plt.tight_layout()
        nome = re.sub(r"[^a-z0-9]+", "_", ch.lower()).strip("_")
        plt.savefig(os.path.join(dir_out, f"curva_{nome}.png"), dpi=130)
        plt.close()

    tab = pd.DataFrame(righe)
    log(f"\n     {'canale':<20}{'spesa/sett':>12}{'ROI medio':>11}"
        f"{'ROI marginale':>15}{'lambda':>9}{'ec_mult':>9}")
    for _, r in tab.iterrows():
        log(f"     {r['canale']:<20}{r['spesa_media_settimanale']:>12,.0f}"
            f"{r['roi_medio']:>11.2f}{r['roi_marginale']:>15.2f}"
            f"{r['lam']:>9.2f}{r['ec_mult']:>9.2f}")
    log("\n  Il ROI marginale e' cio' su cui l'allocatore decide: un canale con")
    log("  ROI medio alto ma marginale basso e' gia' vicino alla saturazione.")
    log(f"  grafici: {dir_out}")
    return tab


# =============================================================================
# 6. stage 2 e fattore k
# =============================================================================

def stage_due(p: dict, dir_bench: str, suffisso: str, log: Tee,
              quota: float) -> None:
    from scipy.stats import spearmanr

    from genera_dati_simulati import CAMPAGNE, CANALI, VALORE_CANDIDATURA_EUR

    log("\n" + "=" * 78)
    log("6. STAGE 2: ordinamento intra-canale e fattore k")
    log("=" * 78)
    plat = pd.read_csv(os.path.join(
        dir_bench, f"roas_piattaforma_trimestrale{suffisso}.csv"))
    interno = pd.read_csv(os.path.join(
        dir_bench, f"benchmark_interno_trimestrale{suffisso}.csv"))

    log("\n  assunzione della Sez. 3.8: dentro il canale l'ordinamento dei ROAS")
    log("  dichiarati e' informativo anche quando il livello non lo e'. La tesi")
    log("  sostiene che sia informativo ma IMPERFETTO: senza rumore di")
    log("  attribuzione sarebbe vero per costruzione, e non proverebbe niente.")
    log("")
    log("  AVVERTENZA DI LETTURA: con 4-6 campagne per canale lo Spearman e'")
    log("  grossolano. Con 4 campagne uno scambio adiacente vale gia' 0,80, con")
    log("  6 vale 0,83: e' un indicatore aggregato, non un giudizio canale per")
    log("  canale. Nel Cap. 5 non ci si costruisce sopra un ragionamento")
    log("  sul singolo canale.")

    def _spearman(pan, ultime=None):
        n_sett = len(pan["settimane"])
        sl = slice(n_sett - ultime, n_sett) if ultime else slice(0, n_sett)
        out = {}
        for canale in pan["canali"]:
            camps = [c for c, d in CAMPAGNE.items() if d["canale"] == canale]
            roas, qual = [], []
            for cp in camps:
                sp = float(pan["camp_spesa"][cp][sl].sum())
                if sp <= 0:
                    continue
                roas.append(float(pan["camp_conv"][cp][sl].sum())
                            * VALORE_CANDIDATURA_EUR / sp)
                qual.append(CAMPAGNE[cp]["qualita"])
            out[canale] = (float(spearmanr(roas, qual).statistic)
                           if len(roas) > 2 else np.nan)
        return out

    # dato principale: valore ATTESO su piu' seed. Il realizzato a seed 42 sta
    # accanto, mai al posto: con cosi' poche campagne una sola realizzazione
    # dice piu' sul seed che sul meccanismo.
    import genera_dati_simulati as _G
    attesi = {}
    for sigma in (0.0, _G.RUMORE_ATTRIBUZIONE_SD):
        due_anni, trimestre = [], []
        for sd in SEED_MULTISEED:
            pan = _G.genera(seed=sd, quota_media=quota, sigma_attr=sigma)
            due_anni.append(np.nanmean(list(_spearman(pan).values())))
            trimestre.append(np.nanmean(list(_spearman(pan, 13).values())))
        attesi[sigma] = (float(np.mean(due_anni)), float(np.mean(trimestre)))

    r42_lungo = _spearman(p)
    r42_trim = _spearman(p, 13)
    sd_attr = _G.RUMORE_ATTRIBUZIONE_SD

    log(f"\n  Spearman medio fra i {len(p['canali'])} canali. Dato principale = "
        f"atteso su {len(SEED_MULTISEED)} seed;")
    log("  fra parentesi il realizzato a seed 42, quello del dataset.")
    log(f"\n     {'finestra':<24}{'senza rumore attr.':>22}"
        f"{'con rumore attr. (sd ' + format(sd_attr, '.2f') + ')':>30}")
    log(f"     {'due anni (intera)':<24}{attesi[0.0][0]:>22.2f}"
        f"{attesi[sd_attr][0]:>21.2f}  ({np.nanmean(list(r42_lungo.values())):.2f})")
    log(f"     {'ultimo trimestre':<24}{attesi[0.0][1]:>22.2f}"
        f"{attesi[sd_attr][1]:>21.2f}  ({np.nanmean(list(r42_trim.values())):.2f})")

    log("\n  DA PORTARE IN TESI: lo stage 2 non consuma i due anni, consuma")
    log("  l'ULTIMO TRIMESTRE (window_weeks=13 in pipeline/allocator/campaigns.py,")
    log("  il trimestre piu' recente nel notebook). L'assunzione della Sez. 3.8")
    log("  si indebolisce proprio nella finestra che il sistema usa davvero.")
    log("  Non e' un difetto della calibrazione: e' un limite del metodo, da")
    log("  dichiarare nel Cap. 5 e da mettere in roadmap nel Cap. 7 (allungare")
    log("  la finestra dello stage 2, o pesare piu' trimestri).")

    log(f"\n  dettaglio a seed 42, per canale")
    log(f"     {'canale':<20}{'n campagne':>12}{'due anni':>11}{'ultimo trim.':>15}")
    for ch in p["canali"]:
        n_camp = len([1 for c, d in CAMPAGNE.items() if d["canale"] == ch])
        log(f"     {ch:<20}{n_camp:>12}{r42_lungo[ch]:>11.2f}{r42_trim[ch]:>15.2f}")

    log("\n  fattore k = ROI(MMM) / ROAS(benchmark interno), per canale")
    log("  k<1: il benchmark sovra-attribuisce; k>1: sotto-attribuisce.")
    log("  ATTENZIONE (Sez. 3.8): k e' costante dentro il canale, si semplifica")
    log("  nella normalizzazione delle quote e NON sposta budget ne' cambia")
    log("  l'ordinamento. Serve a rendere confrontabili i ROAS TRA canali.")
    log(f"\n     {'canale':<20}{'ROI vero':>10}{'ROAS bench.':>13}"
        f"{'k atteso':>10}{'ROAS piattaforme':>18}")
    tot_plat = tot_int = tot_vero = 0.0
    for ch in p["canali"]:
        spesa = float(p["ch_spesa"][ch].sum())
        inc = float(p["risposta"][ch].sum())
        roi = inc * VALORE_CANDIDATURA_EUR / spesa
        b = interno[interno["canale"] == ch]
        roas_b = float(b["candidature_attribuite"].sum()
                       * VALORE_CANDIDATURA_EUR / b["spesa"].sum())
        pl = plat[plat["canale"] == ch]
        roas_p = float(pl["conversioni_dichiarate"].sum()
                       * VALORE_CANDIDATURA_EUR / pl["spesa"].sum())
        log(f"     {ch:<20}{roi:>10.2f}{roas_b:>13.2f}{roi / roas_b:>10.2f}"
            f"{roas_p:>18.2f}")
        tot_vero += inc
        tot_int += float(b["candidature_attribuite"].sum())
        tot_plat += float(pl["conversioni_dichiarate"].sum())

    totali = float(p["candidature"].sum())
    log(f"\n  candidature totali osservate            {totali:>12,.0f}")
    log(f"  contributo incrementale VERO dei media  {tot_vero:>12,.0f}"
        f"   ({tot_vero / totali:.1%} del totale)")
    log(f"  benchmark interno (deduplicato)         {tot_int:>12,.0f}"
        f"   ({tot_int / totali:.1%})")
    log(f"  somma dichiarata dalle piattaforme      {tot_plat:>12,.0f}"
        f"   ({tot_plat / totali:.1%})")
    log(f"  sovraconteggio piattaforme vs vero      "
        f"{tot_plat / tot_vero:>12.2f}x")
    log("  Il benchmark interno resta sotto il totale vero (e' deduplicato e")
    log("  ancorato alle candidature reali); la somma delle piattaforme no.")


# =============================================================================
# 7. cella 8-bis
# =============================================================================

def diagnostica_split(ns: dict, log: Tee) -> None:
    log("\n" + "=" * 78)
    log("7. CELLA 8-bis: le tipologie di campagna sono separabili?")
    log("=" * 78)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        exec(ns["_src"][CELLA_SPLIT_8BIS], ns)
    for r in buffer.getvalue().splitlines():
        log("  " + r)


# =============================================================================
# main
# =============================================================================

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cartella", default=os.path.join("dati_simulati", "modello"))
    ap.add_argument("--suffisso", default="")
    ap.add_argument("--quota", type=float, default=None)
    ap.add_argument("--interattivo", action="store_true",
                    help="conferme reali ai checkpoint (niente AUTO_CONFERMA)")
    args = ap.parse_args()

    import genera_dati_simulati as G
    cartella = os.path.join(ROOT, args.cartella)
    dir_verita = os.path.join(ROOT, "dati_simulati", "verita")
    dir_bench = os.path.join(ROOT, "dati_simulati", "benchmark")
    os.makedirs(dir_verita, exist_ok=True)

    log = Tee()
    log(f"VERIFICA DEL DATASET SIMULATO - {cartella}")
    log("(nessun fit Meridian: solo ingestion, correlazioni e curve vere)")
    log("")

    quota = args.quota if args.quota is not None else G.QUOTA_MEDIA_TARGET
    p = G.genera(quota_media=quota)          # stesso seed: stesso panel dei file

    ns = prepara_notebook(auto_conferma=not args.interattivo)
    mappa_ruoli(ns, cartella, log)
    ingestion_notebook(ns, cartella, log, interattivo=args.interattivo)
    ingestion_pipeline(cartella, log)
    collinearita(ns, p, log)
    curve_vere(p, os.path.join(dir_verita, "curve" + args.suffisso), log)
    stage_due(p, dir_bench, args.suffisso, log, quota)
    diagnostica_split(ns, log)

    nome = f"report_verifica{args.suffisso}.txt"
    if args.interattivo:
        nome = f"trascrizione_checkpoint{args.suffisso}.txt"
    log.salva(os.path.join(dir_verita, nome))
    print(f"\nReport salvato in dati_simulati/verita/{nome}")


if __name__ == "__main__":
    main()
