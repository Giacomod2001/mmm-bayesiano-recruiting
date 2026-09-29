# CONTROLLI DI FEDELTA' 2-5 (D12) su tutti e otto i mondi, piu' il costo.
#
#   2. nelle celle trattate la spesa e' esattamente 0 su tutti e sette i canali,
#      e fuori da quelle celle e' quella del mondo base, valore per valore
#   3a beta e ec del mondo blackout contro quelli del mondo base, a precisione
#      di macchina (in memoria)
#   3b K = beta x pop x mg ricavato DAI FILE (contributo_vero / hill), per
#      regione, come rapporto di somme: e' la strada che un lettore esterno
#      puo' rifare sui CSV committati
#   4a verita' del generatore contro calcolo analitico IN MEMORIA, con adstock
#      e Hill riscritti qui e non importati
#   4b lo stesso, dai file (limitato dai 4 decimali di contributo_vero.csv)
#   5. impronte sha256 dei sette file media, per mondo
#
# COSTO: candidature vere perse, nelle celle trattate e in totale (la coda
# dell'adstock continua a pesare per otto settimane dopo il blocco).
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd

SP = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(SP, "A")
B = os.path.join(SP, "B")
MONDI = [42, 101, 102, 103, 104, 105, 106, 107]

FILE_MEDIA = ["google_ads_settimanale.csv", "meta_ads_settimanale.csv",
              "linkedin_ads_settimanale.csv", "indeed_settimanale.csv",
              "subito_lavoro_settimanale.csv", "jooble_settimanale.csv",
              "altre_job_board_settimanale.csv"]


def genera(radice, flag):
    r = subprocess.run([sys.executable, "genera_dati_simulati.py"] + flag,
                       cwd=radice, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("generazione fallita: " + " ".join(flag) + "\n" +
                         (r.stdout + r.stderr)[-3000:])


def adstock(x, lam, max_lag=8):
    """Seconda strada: riscritto qui, non importato dal generatore."""
    pesi = np.array([lam ** l for l in range(max_lag + 1)], dtype=float)
    pesi = pesi / pesi.sum()
    n = x.shape[0]
    out = np.zeros_like(x, dtype=float)
    for t in range(n):
        for l in range(max_lag + 1):
            if t - l >= 0:
                out[t] += pesi[l] * x[t - l]
    return out


def hill(a, ec, slope):
    a = np.maximum(a, 0.0)
    return a ** slope / (a ** slope + ec ** slope + 1e-12)


def _piv(dir_modello, colonna, settimane, regioni):
    fuori = {}
    for f in FILE_MEDIA:
        d = pd.read_csv(os.path.join(dir_modello, f))
        ch = d["canale"].iloc[0]
        piv = (d.groupby(["settimana", "regione"])[colonna].sum()
               .unstack(fill_value=0.0)
               .reindex(index=settimane, columns=regioni, fill_value=0.0))
        fuori[ch] = piv.to_numpy(dtype=float)
    return fuori


def contributo(dir_verita, settimane, regioni):
    d = pd.read_csv(os.path.join(dir_verita, "contributo_vero.csv"))
    fuori = {}
    for ch, g in d.groupby("canale"):
        piv = (g.set_index(["settimana", "regione"])["candidature_incrementali_vere"]
               .unstack(fill_value=0.0)
               .reindex(index=settimane, columns=regioni, fill_value=0.0))
        fuori[ch] = piv.to_numpy(dtype=float)
    return fuori


def impronta(dir_modello):
    h = hashlib.sha256()
    for f in FILE_MEDIA:
        h.update(open(os.path.join(dir_modello, f), "rb").read())
    return h.hexdigest()[:16]


spec = importlib.util.spec_from_file_location(
    "gB", os.path.join(B, "genera_dati_simulati.py"))
gB = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gB)

righe = []
for seme in MONDI:
    genera(A, ["--seed-mondo", str(seme)])
    genera(B, ["--seed-mondo", str(seme), "--blackout"])
    d_base = os.path.join(A, "dati_simulati_mondi", "mondo_%04d" % seme)
    d_bk = os.path.join(B, "dati_simulati_mondi", "mondo_%04d_blackout" % seme)
    par = json.load(open(os.path.join(d_base, "verita",
                                      "parametri_generazione.json"), encoding="utf-8"))
    par_bk = json.load(open(os.path.join(d_bk, "verita",
                                         "parametri_generazione.json"), encoding="utf-8"))
    sc = par_bk["scenario_blackout"]

    kpi = pd.read_csv(os.path.join(d_base, "modello", "candidature_settimanali.csv"))
    settimane = sorted(kpi["settimana"].unique())
    regioni = sorted(kpi["regione"].unique())
    n, R = len(settimane), len(regioni)
    idx = {r: i for i, r in enumerate(regioni)}
    maschera = np.zeros((n, R), dtype=bool)
    for a, b in sc["blocchi_1based_inclusivi"]:
        for r in sc["regioni_trattate"]:
            maschera[a - 1:b, idx[r]] = True

    # --- 2 --------------------------------------------------------------
    sp_bk = _piv(os.path.join(d_bk, "modello"), "spesa", settimane, regioni)
    sp_base = _piv(os.path.join(d_base, "modello"), "spesa", settimane, regioni)
    max_tr = max(float(sp_bk[ch][maschera].max()) for ch in sp_bk)
    fuori_uguale = all(np.array_equal(sp_bk[ch][~maschera], sp_base[ch][~maschera])
                       for ch in sp_bk)
    ok2 = (max_tr == 0.0) and fuori_uguale

    # --- 3a e 4a: in memoria -------------------------------------------
    p_base = gB.genera(seed=seme)
    p_bk = gB.genera(seed=seme, geo_spec=gB.blackout_spec())
    d_beta = max(abs(p_bk["beta"][ch] / p_base["beta"][ch] - 1.0) for ch in p_base["beta"])
    d_ec = max(abs(p_bk["ec_impr"][ch] / p_base["ec_impr"][ch] - 1.0) for ch in p_base["ec_impr"])
    pop = p_base["pop"]
    scarti_mem = []
    for ch in p_base["canali"]:
        c = gB.CANALI[ch]
        K = p_base["beta"][ch] * (pop * p_base["beta_geo"][ch])          # (R,)
        ec = p_base["ec_impr"][ch]
        a = adstock(p_bk["ch_impr"][ch] / pop[None, :], c["lam"])
        atteso = K[None, :] * hill(a, ec, c["slope"])
        vero = p_bk["risposta"][ch]
        scarti_mem.append(float(np.abs(atteso - vero).sum() / np.abs(vero).sum()))
    ok4a = max(scarti_mem) < 1e-6

    # --- 3b e 4b: dai file ----------------------------------------------
    pop_f = pd.read_csv(os.path.join(d_base, "modello", "popolazione_regioni.csv"))
    popf = pop_f.set_index("regione")["popolazione"].reindex(regioni).to_numpy(float)
    popf = popf / popf.sum()
    impr_base = _piv(os.path.join(d_base, "modello"), "impressioni", settimane, regioni)
    impr_bk = _piv(os.path.join(d_bk, "modello"), "impressioni", settimane, regioni)
    con_base = contributo(os.path.join(d_base, "verita"), settimane, regioni)
    con_bk = contributo(os.path.join(d_bk, "verita"), settimane, regioni)
    scarti_K, scarti_file = [], []
    perse_celle = perse_tot = 0.0
    for ch, cp in par["canali"].items():
        lam = cp["adstock_lambda"]
        slope = cp["hill_slope"]
        ec = cp["hill_ec_moltiplicatore_esecuzione_media"] * float(
            np.mean(impr_base[ch].sum(axis=1)))
        h_base = hill(adstock(impr_base[ch] / popf[None, :], lam), ec, slope)
        h_bk = hill(adstock(impr_bk[ch] / popf[None, :], lam), ec, slope)
        # K per regione come RAPPORTO DI SOMME: l'arrotondamento a 4 decimali
        # del contributo si media invece di esplodere nelle celle a hill piccolo
        Kb = con_base[ch].sum(axis=0) / h_base.sum(axis=0)
        Kk = con_bk[ch].sum(axis=0) / np.where(h_bk.sum(axis=0) > 0,
                                               h_bk.sum(axis=0), np.nan)
        scarti_K.append(float(np.nanmax(np.abs(Kk / Kb - 1.0))))
        atteso = Kb[None, :] * h_bk
        scarti_file.append(float(np.abs(atteso - con_bk[ch]).sum() /
                                 np.abs(con_bk[ch]).sum()))
        perse_celle += float(con_base[ch][maschera].sum() - con_bk[ch][maschera].sum())
        perse_tot += float(con_base[ch].sum() - con_bk[ch].sum())
    ok3b = max(scarti_K) < 1e-3
    ok4b = max(scarti_file) < 1e-3

    sp_tot_base = sum(float(v.sum()) for v in sp_base.values())
    sp_tot_bk = sum(float(v.sum()) for v in sp_bk.values())
    kpi_base = float(kpi["candidature"].sum())
    kpi_bk = float(pd.read_csv(os.path.join(d_bk, "modello",
                                            "candidature_settimanali.csv"))["candidature"].sum())
    righe.append(dict(
        seme=seme, ok2=ok2, ok4a=ok4a, ok3b=ok3b, ok4b=ok4b,
        max_spesa_trattata=max_tr, fuori_uguale=fuori_uguale,
        d_beta=d_beta, d_ec=d_ec,
        scarto_memoria=max(scarti_mem), scarto_K_file=max(scarti_K),
        scarto_file=max(scarti_file),
        quota_vera_base_pct=100.0 * p_base["quota_media_realizzata"],
        quota_vera_blackout_pct=100.0 * p_bk["quota_media_realizzata"],
        contributo_base=sum(v.sum() for v in p_base["risposta"].values()),
        contributo_blackout=sum(v.sum() for v in p_bk["risposta"].values()),
        perse_celle_trattate=perse_celle, perse_totali=perse_tot,
        spesa_base=sp_tot_base, spesa_blackout=sp_tot_bk,
        spesa_tolta=sp_tot_base - sp_tot_bk,
        spesa_tolta_pct=100.0 * (1 - sp_tot_bk / sp_tot_base),
        kpi_base=kpi_base, kpi_blackout=kpi_bk,
        celle_trattate=int(maschera.sum()),
        impronta_base=impronta(os.path.join(d_base, "modello")),
        impronta_blackout=impronta(os.path.join(d_bk, "modello")),
    ))
    print("mondo %3d: 2=%s 4a=%s 3b=%s 4b=%s | dbeta=%.1e dec=%.1e | "
          "mem=%.1e file=%.1e K=%.1e" %
          (seme, ok2, ok4a, ok3b, ok4b, d_beta, d_ec, max(scarti_mem),
           max(scarti_file), max(scarti_K)))

df = pd.DataFrame(righe)
df.to_csv(os.path.join(SP, "controlli_D12.csv"), index=False)
pd.set_option("display.width", 200)
print()
print(df[["seme", "quota_vera_base_pct", "quota_vera_blackout_pct", "spesa_tolta",
          "spesa_tolta_pct", "perse_celle_trattate", "perse_totali",
          "kpi_base", "kpi_blackout"]].to_string(index=False))
print()
print("CONTROLLO 2  (spesa zero e resto identico) :",
      "PASSATO" if df["ok2"].all() else "FALLITO")
print("CONTROLLO 3a (beta e ec, in memoria)       : scarto massimo %.1e / %.1e -> %s"
      % (df["d_beta"].max(), df["d_ec"].max(),
         "PASSATO" if max(df["d_beta"].max(), df["d_ec"].max()) == 0.0 else "FALLITO"))
print("CONTROLLO 3b (K dai file)                  : scarto massimo %.2e -> %s"
      % (df["scarto_K_file"].max(), "PASSATO" if df["ok3b"].all() else "FALLITO"))
print("CONTROLLO 4a (analitico, in memoria)       : scarto massimo %.2e -> %s"
      % (df["scarto_memoria"].max(), "PASSATO" if df["ok4a"].all() else "FALLITO"))
print("CONTROLLO 4b (analitico, dai file)         : scarto massimo %.2e -> %s"
      % (df["scarto_file"].max(), "PASSATO" if df["ok4b"].all() else "FALLITO"))
print()
print("IMPRONTE (sha256 dei sette file media, 16 caratteri):")
for r in righe:
    print("  mondo %4d  base %s  blackout %s" %
          (r["seme"], r["impronta_base"], r["impronta_blackout"]))
