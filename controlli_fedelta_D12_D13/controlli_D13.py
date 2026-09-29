# CONTROLLI DI FEDELTA' (D13).
#   1. con f = 0 il runner non scrive nulla: i file dati del mondo sono quelli
#      di D0, byte per byte (il run e' D0 per costruzione)
#   2. con f > 0 spesa, impression, clic e KPI restano bit-identici al mondo
#      base: l'unico file in piu' e' la colonna di controllo
#   3. la colonna di controllo entra nel modello come CONTROLLO e non come
#      media: verificato eseguendo le CELLE 2, 3, 5 e 6 del notebook congelato
#      colab_end_to_end.ipynb, le stesse che esegue il runner
# Piu' la monotonia dichiarata: correlazione fra controllo e baseline vera.
import difflib
import filecmp
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import unicodedata
import warnings

import numpy as np
import pandas as pd

SP = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(SP, "B")
NB = r"C:/Users/giaco/Claude/Projects/tesi magistrale/colab_end_to_end.ipynb"
RUNNER = os.path.join(SP, "gen", "runner_R8.py")
MONDI = [42, 101, 102, 103, 104, 105, 106, 107]
LIVELLI = [0.30, 0.60, 0.90]

FILE_DATI = ["google_ads_settimanale.csv", "meta_ads_settimanale.csv",
             "linkedin_ads_settimanale.csv", "indeed_settimanale.csv",
             "subito_lavoro_settimanale.csv", "jooble_settimanale.csv",
             "altre_job_board_settimanale.csv", "candidature_settimanali.csv",
             "richieste_clienti.csv", "ricerche_candidati.csv",
             "stagionalita.csv", "popolazione_regioni.csv"]

# la funzione del runner, presa dal runner e non riscritta
_src = open(RUNNER, encoding="utf-8").read()
_i = _src.index("def scrivi_controllo_baseline")
_j = _src.index("def percorso_affiancato")
_ns = {"os": os}
exec(compile(_src[_i:_j], "R8", "exec"), _ns)
scrivi_controllo_baseline = _ns["scrivi_controllo_baseline"]


def genera(flag):
    r = subprocess.run([sys.executable, "genera_dati_simulati.py"] + flag,
                       cwd=B, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("generazione fallita: " + (r.stdout + r.stderr)[-2000:])


def celle(percorso, etichette):
    nb = json.load(open(percorso, encoding="utf-8"))
    fuori = {}
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        s = "".join(c["source"])
        for et in etichette:
            if re.search(r"^#\s*" + et + r"\s*-", s, flags=re.M):
                fuori[et] = s
    return fuori


CELLE = celle(NB, ["CELLA 2", "CELLA 3", "CELLA 5", "CELLA 6"])


def ingesta(dir_dati):
    """Esegue le celle del notebook congelato e restituisce cosa il modello
    riceverebbe: controlli, canali, geo, settimane."""
    ns = {"os": os, "io": io, "re": re, "json": json, "np": np, "pd": pd,
          "unicodedata": unicodedata, "difflib": difflib, "warnings": warnings,
          "input": lambda *a, **k: (_ for _ in ()).throw(RuntimeError("input")),
          "csv": __import__("csv"), "math": __import__("math")}
    vecchio = sys.stdout
    sys.stdout = io.StringIO()
    try:
        exec(compile(CELLE["CELLA 2"], "c2", "exec"), ns)
        ns["AUTO_CONFERMA"] = True
        ns["KPI"] = "auto"
        ns["PERIODO"] = "auto"
        ns["GEO"] = "auto"
        ns["VALUTA"] = "auto"
        exec(compile(CELLE["CELLA 3"], "c3", "exec"), ns)
        files = {}
        for nome in sorted(os.listdir(dir_dati)):
            if nome.lower().endswith(".csv"):
                files[nome] = open(os.path.join(dir_dati, nome), "rb").read()
        ns["FILES_GREZZI"] = files
        ns["ORIGINE_DATI"] = dir_dati
        exec(compile(CELLE["CELLA 5"], "c5", "exec"), ns)
        exec(compile(CELLE["CELLA 6"], "c6", "exec"), ns)
    finally:
        sys.stdout = vecchio
    return ns


print("=" * 78)
print("CONTROLLO 3 (mondo 42, f = 0,60): la colonna entra come controllo?")
print("=" * 78)
genera(["--seed-mondo", "42"])
d42 = os.path.join(B, "dati_simulati_mondi", "mondo_0042")
dir_dati = os.path.join(d42, "modello")
ns0 = ingesta(dir_dati)
print("SENZA controllo:  controlli =", ns0["CONTROLLI"])
print("                  canali    =", ns0["CANALI"])
print("                  geo x sett =", len(ns0["GEOS"]), "x", len(ns0["SETTIMANE"]))
kpi0 = float(ns0["DF_BASE"]["kpi"].sum())

col, rho, _p = scrivi_controllo_baseline(d42, dir_dati, 42, 0.60, np, pd)
ns1 = ingesta(dir_dati)
print("CON controllo:    controlli =", ns1["CONTROLLI"])
print("                  canali    =", ns1["CANALI"])
print("                  geo x sett =", len(ns1["GEOS"]), "x", len(ns1["SETTIMANE"]))
kpi1 = float(ns1["DF_BASE"]["kpi"].sum())
ok3 = ("ctrl_" + col in ns1["CONTROLLI"] and
       set(ns1["CANALI"]) == set(ns0["CANALI"]) and
       len(ns1["CONTROLLI"]) == len(ns0["CONTROLLI"]) + 1 and
       kpi0 == kpi1 and len(ns1["GEOS"]) == 20 and len(ns1["SETTIMANE"]) == 104)
print("KPI totale identico:", kpi0 == kpi1, "(", kpi0, ")")
print("ESITO CONTROLLO 3:", "PASSATO" if ok3 else "FALLITO")
os.remove(_p)

print()
print("=" * 78)
print("CONTROLLI 1 e 2: i dati del mondo non si muovono")
print("=" * 78)
righe = []
tutti_ok = True
for seme in MONDI:
    genera(["--seed-mondo", str(seme)])
    d = os.path.join(B, "dati_simulati_mondi", "mondo_%04d" % seme)
    dd = os.path.join(d, "modello")
    prima = {f: open(os.path.join(dd, f), "rb").read() for f in FILE_DATI}
    # f = 0: nessun file scritto
    c0, r0, p0 = scrivi_controllo_baseline(d, dd, seme, 0.0, np, pd)
    ok1 = (c0 == "" and not os.path.exists(
        os.path.join(dd, "domanda_organica_osservata.csv")))
    org = pd.read_csv(os.path.join(d, "verita", "candidature_organiche.csv"))
    vera = org["candidature_organiche_vere"].to_numpy(float)
    for f in LIVELLI:
        col, rho, p = scrivi_controllo_baseline(d, dd, seme, f, np, pd)
        dopo = {x: open(os.path.join(dd, x), "rb").read() for x in FILE_DATI}
        ok2 = all(prima[x] == dopo[x] for x in FILE_DATI)
        c = pd.read_csv(p)[col].to_numpy(float)
        righe.append(dict(seme=seme, f=f, ok1=ok1, ok2=ok2, rho=rho,
                          media_controllo=float(c.mean()),
                          media_baseline_vera=float(vera.mean()),
                          rapporto=float(c.sum() / vera.sum()),
                          corr_pearson=float(np.corrcoef(c, vera)[0, 1])))
        tutti_ok = tutti_ok and ok1 and ok2
        os.remove(p)

df = pd.DataFrame(righe)
df.to_csv(os.path.join(SP, "controlli_D13.csv"), index=False)
pd.set_option("display.width", 200)
print(df.to_string(index=False))
print()
print("CONTROLLO 1 (f = 0 non scrive nulla)        :",
      "PASSATO" if df["ok1"].all() else "FALLITO")
print("CONTROLLO 2 (i 12 file dati non si muovono) :",
      "PASSATO" if df["ok2"].all() else "FALLITO",
      "(%d file x %d combinazioni)" % (len(FILE_DATI), len(df)))
print("correlazione controllo/baseline vera: min %.4f  max %.4f"
      % (df["corr_pearson"].min(), df["corr_pearson"].max()))
print("rapporto somma controllo / somma baseline vera per livello:")
for f in LIVELLI:
    s = df[df["f"] == f]["rapporto"]
    print("   f = %.2f  ->  %.4f - %.4f" % (f, s.min(), s.max()))
