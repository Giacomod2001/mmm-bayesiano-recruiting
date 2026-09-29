"""D14 - allocare il budget con i ROAS del benchmark interno.

Esegue PREREGISTRAZIONE_D14_allocatore_ROAS_benchmark.md (approvata il 24/9, sha256 43b4cf86...).
Ordine: cancello, parte A, parte B1 (errore casuale), parte B2 (errore sistematico).
Riusa senza modifiche la macchina di D11 (generatore G5, contributo vero a beta fisso).
Il file trimestrale del benchmark interno si legge per posizione, mai per nome di colonna.
uso: python studio_D14.py
"""
import csv
import hashlib
import importlib.util
import itertools
import json
import os
import sys
import time

import numpy as np

QUI = os.path.dirname(os.path.abspath(__file__))
D11 = os.path.join(QUI, "..", "D11")
PREREG = os.path.join(QUI, "preregistrazioni", "PREREGISTRAZIONE_D14_allocatore_ROAS_benchmark.md")
SHA_PREREG = "43b4cf866856ed7ad0b9aba2b69ea3c7b06500817fa9ef8e86294953c73c9cb8"

_s = importlib.util.spec_from_file_location("studio_D11", os.path.join(D11, "studio_D11.py"))
S11 = importlib.util.module_from_spec(_s); _s.loader.exec_module(S11)
G = S11.G

CASI = [("D1", 101), ("D1", 103), ("D1", 105), ("D1", 107),
        ("D2", 102), ("D2", 103), ("D10", 42), ("D10", 103)]
SEMI = sorted({s for _, s in CASI})
BANDA = 0.30
VAL = G.VALORE_CANDIDATURA_EUR
N_NULLO = S11.N_CASUALI              # 200, come D11 e R1
SEME_NULLO = S11.SEME_NULLO          # 20260917, come D11 e R1
LIVELLI = [0.0, 0.10, 0.25, 0.50, 0.75, 1.00]
N_ESTRAZIONI = 200
SEME_B1 = 20260924
CHIUSURA = ["Google Ads", "Indeed", "Subito Lavoro", "Jooble", "Altre job board"]
INIZIO = ["Meta Ads", "LinkedIn Ads"]
# posizioni nel file trimestrale del benchmark interno scritto dal generatore
POS_CANALE, POS_SPESA, POS_ATTRIBUITE = 1, 2, 3


def fmt(x, d=3):
    return format(x, "." + str(d) + "f").replace(".", ",")


# ----------------------------------------------------------------------------- dati
def scrivi_mondo(seed):
    """Il mondo base del seme, scritto con le funzioni di scrittura del generatore."""
    radice = os.path.join(QUI, "mondi", "mondo_%04d" % seed)
    db, dv = os.path.join(radice, "benchmark"), os.path.join(radice, "verita")
    os.makedirs(db, exist_ok=True); os.makedirs(dv, exist_ok=True)
    p = G.genera(seed=seed)
    bench = G.scrivi_benchmark(p, db)
    parametri = G.costruisci_parametri(p, G.QUOTA_MEDIA_TARGET)
    G.scrivi_verita(p, dv, parametri)
    return p, os.path.join(db, bench["file"][1]), os.path.join(dv, "parametri_generazione.json")


def roas_da_file(percorso):
    att, sp = {}, {}
    with open(percorso, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for riga in r:
            c = riga[POS_CANALE]
            sp[c] = sp.get(c, 0.0) + float(riga[POS_SPESA])
            att[c] = att.get(c, 0.0) + float(riga[POS_ATTRIBUITE])
    return {c: att[c] * VAL / sp[c] for c in sp}


def roi_vero_da_file(percorso):
    par = json.load(open(percorso, encoding="utf-8"))["canali"]
    return {c: par[c]["candidature_incrementali_vere"] * VAL / par[c]["spesa_totale_eur"] for c in par}


def roas_interno(p):
    """Cio' che il generatore attribuisce: contributo vero x fattore di distorsione del canale."""
    return {c: float(p["risposta"][c].sum()) * G.CANALI[c]["bias_bench"] * VAL / float(p["ch_spesa"][c].sum())
            for c in p["canali"]}


# ----------------------------------------------------------------------------- regola
def riparto_da_roas(roas, spesa):
    """Allocatore lineare, budget fisso, banda +-30%: tutti a -30%, il budget liberato ai canali in
    ordine di ROAS decrescente fino a +30%. Pareggi esatti: blocco con la stessa variazione %."""
    x = {c: (1 - BANDA) * spesa[c] for c in spesa}
    resto = BANDA * sum(spesa.values())
    for v in sorted(set(roas.values()), reverse=True):
        blocco = [c for c in spesa if roas[c] == v]
        cap = sum(2 * BANDA * spesa[c] for c in blocco)
        quota = min(1.0, resto / cap) if cap > 0 else 0.0
        for c in blocco:
            x[c] += quota * 2 * BANDA * spesa[c]
        resto -= quota * cap
        if resto <= 0:
            break
    return {c: 100.0 * (x[c] / spesa[c] - 1.0) for c in spesa}


def euro_mossi(rip, spesa):
    return sum(abs(spesa[c] * d / 100.0) for c, d in rip.items()) / 2.0


class Mondo:
    def __init__(self, seed):
        self.seed = seed
        self.canali, self.spesa, self.curve = S11.mondo(seed)
        self.Ya = S11.contributo(self.curve, self.canali)
        self.coppie = S11.coppie(self.canali)
        self._nulli = {}

    def g(self, rip):
        return S11.contributo(self.curve, self.canali, rip) - self.Ya

    def nullo_R1(self, eur):
        """200 coppie casuali alla stessa cifra, rng di D11/R1; oracolo sulle 42 coppie."""
        chiave = round(eur, 6)
        if chiave not in self._nulli:
            rng = np.random.default_rng(SEME_NULLO + self.seed)
            gd = []
            while len(gd) < N_NULLO:
                su, giu = self.coppie[int(rng.integers(0, len(self.coppie)))]
                d_giu = -100.0 * eur / self.spesa[giu]
                if d_giu <= -100.0:
                    continue
                gd.append(self.g({su: 100.0 * eur / self.spesa[su], giu: d_giu}))
            best, ge = None, -np.inf
            for su, giu in self.coppie:
                d_giu = -100.0 * eur / self.spesa[giu]
                if d_giu <= -100.0:
                    continue
                v = self.g({su: 100.0 * eur / self.spesa[su], giu: d_giu})
                if v > ge:
                    ge, best = v, (su, giu)
            self._nulli[chiave] = (np.array(gd), ge, best)
        return self._nulli[chiave]

    def valuta(self, roas):
        rip = riparto_da_roas(roas, self.spesa)
        eur = euro_mossi(rip, self.spesa)
        g = self.g(rip)
        gd, ge, best = self.nullo_R1(eur)
        return dict(rip=rip, eur=eur, g=g, g_pct=100 * g / self.Ya, p=float((gd < g).mean()),
                    ge=ge, oracolo=best, gd=gd)


def criterio(gpcts, ps):
    return (float(np.median(gpcts)) > 0) and (sum(p >= 0.90 for p in ps) >= 6)


def soglia(esiti):
    """esiti: lista (livello, soddisfa) in ordine. Soglia contigua da zero; elenco completo."""
    s = None
    for liv, ok in esiti:
        if ok:
            s = liv
        else:
            break
    return s, [liv for liv, ok in esiti if ok]


# ----------------------------------------------------------------------------- main
def main():
    t0 = time.time()
    sha = hashlib.sha256(open(PREREG, "rb").read()).hexdigest()
    print("D14 - allocatore sui ROAS del benchmark interno")
    print("pre-registrazione sha256 " + sha + ("  (congelata, identica)" if sha == SHA_PREREG else "  DIVERSA DA QUELLA CONGELATA"))
    if sha != SHA_PREREG:
        sys.exit("La pre-registrazione non e' quella congelata: D14 si ferma.")

    # ---------------------------------------------------------------- dati e cancello
    print("\nCANCELLO")
    mondi, roas_b, roi_v = {}, {}, {}
    ok = True
    for seed in SEMI:
        p, f_bench, f_par = scrivi_mondo(seed)
        roas_b[seed] = roas_da_file(f_bench)
        roi_v[seed] = roi_vero_da_file(f_par)
        interno = roas_interno(p)
        scarti = {c: roas_b[seed][c] / interno[c] - 1 for c in interno}
        peggiore = max(scarti, key=lambda c: abs(scarti[c]))
        esito = all(abs(v) <= 0.001 for v in scarti.values())
        ok &= esito
        print("  seme %3d  ROAS del benchmark dal file contro generatore: scarto massimo %s%% (%s)  %s"
              % (seed, fmt(100 * scarti[peggiore], 4), peggiore, "OK" if esito else "OLTRE LO 0,1%"))
        mondi[seed] = Mondo(seed)
    d11 = {(r["disegno"], int(r["mondo"])): r for r in
           csv.DictReader(open(os.path.join(D11, "D11_risultati.csv"), encoding="utf-8"))}
    for dis, seed in CASI:
        m = mondi[seed]
        rip_c, _ = S11.riparto_allocatore_vecchio(m.spesa)
        gc_pct = 100 * m.g(rip_c) / m.Ya
        ya_ref, gc_ref = float(d11[(dis, seed)]["Y_a"]), float(d11[(dis, seed)]["g_c_pct"])
        esito = abs(m.Ya - ya_ref) <= 0.5 and abs(gc_pct - gc_ref) <= 0.010
        ok &= esito
        print("  %-4s %3d  non fare niente %s (D11 %s)  allocatore del modello %s%% (D11 %s%%)  %s"
              % (dis, seed, fmt(m.Ya), fmt(ya_ref), fmt(gc_pct, 4), fmt(gc_ref, 4), "OK" if esito else "FUORI TOLLERANZA"))
    if not ok:
        print("CANCELLO NON PASSATO: D14 si ferma qui e non si legge nient'altro.")
        return
    print("CANCELLO: PASSATO  (%s s)" % fmt(time.time() - t0, 1))

    # ---------------------------------------------------------------- parte A
    tA = time.time()
    print("\nPARTE A - allocatore sui ROAS del benchmark (fattori del generatore)")
    righe, per_seme = [], {}
    for seed in SEMI:
        m = mondi[seed]
        v = m.valuta(roas_b[seed])
        # (d') ed (e') descrittivi: tutte le 5.040 graduatorie nello stesso allocatore
        tutte = []
        for perm in itertools.permutations(m.canali):
            rango = {c: len(perm) - i for i, c in enumerate(perm)}
            tutte.append(m.g(riparto_da_roas(rango, m.spesa)))
        tutte = np.array(tutte)
        v["p_banda"] = float((tutte < v["g"]).mean())
        v["best_banda_pct"] = 100 * float(tutte.max()) / m.Ya
        per_seme[seed] = v
    for dis, seed in CASI:
        m, v = mondi[seed], per_seme[seed]
        ordine = sorted(m.canali, key=lambda c: -roas_b[seed][c])
        righe.append(dict(
            disegno=dis, mondo=seed,
            ordine_ROAS_benchmark=" > ".join(ordine),
            riparto_pct=";".join(c + "=" + format(v["rip"][c], "+.4f") for c in m.canali),
            euro_mossi=round(v["eur"], 2), quota_budget_mossa=round(v["eur"] / sum(m.spesa.values()), 5),
            contributo_non_fare_niente=round(m.Ya, 3),
            g=round(v["g"], 3), g_pct=round(v["g_pct"], 5), p_R1=round(v["p"], 4),
            nullo_R1_mediana_pct=round(100 * float(np.median(v["gd"])) / m.Ya, 5),
            nullo_R1_p90_pct=round(100 * float(np.quantile(v["gd"], 0.90)) / m.Ya, 5),
            oracolo_coppia=v["oracolo"][0] + " <- " + v["oracolo"][1],
            oracolo_pct=round(100 * v["ge"] / m.Ya, 5),
            f=round(v["g"] / v["ge"], 4) if v["ge"] > 0 else "",
            allocatore_modello_pct_D11=float(d11[(dis, seed)]["g_c_pct"]),
            candidature_per_1000_euro=round(1000 * v["g"] / v["eur"], 4),
            p_banda_descrittivo=round(v["p_banda"], 4),
            migliore_graduatoria_pct_descrittivo=round(v["best_banda_pct"], 5)))
        print("  %-4s %3d  g %s%%  p(R1) %s  f %s | nullo R1 p90 %s%% | oracolo %s%% | modello %s%% | banda: p %s, migliore %s%% | mossi %s%% del budget"
              % (dis, seed, fmt(v["g_pct"], 4), fmt(v["p"], 3), fmt(v["g"] / v["ge"], 3) if v["ge"] > 0 else "n.d.",
                 fmt(righe[-1]["nullo_R1_p90_pct"], 4), fmt(righe[-1]["oracolo_pct"], 4),
                 fmt(righe[-1]["allocatore_modello_pct_D11"], 4), fmt(v["p_banda"], 3),
                 fmt(v["best_banda_pct"], 4), fmt(100 * righe[-1]["quota_budget_mossa"], 2)))
    with open(os.path.join(QUI, "D14_risultati.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(righe[0])); w.writeheader(); w.writerows(righe)
    gp = [r["g_pct"] for r in righe]; pp = [r["p_R1"] for r in righe]
    S = sum(p >= 0.90 for p in pp)
    ramo = ("A1 SUCCESSO" if float(np.median(gp)) > 0 and S >= 6 else
            "A2 GUADAGNA MA NON SI DISTINGUE DA UNA MOSSA CASUALE" if float(np.median(gp)) > 0 else
            "A3 NON GUADAGNA")
    gp6 = [100 * per_seme[s]["g"] / mondi[s].Ya for s in SEMI]; pp6 = [per_seme[s]["p"] for s in SEMI]
    print("  8 casi: g%% mediano %s%%, g>0 in %d/8, p(R1)>=0,90 in %d/8, meglio del modello in %d/8"
          % (fmt(float(np.median(gp)), 4), sum(x > 0 for x in gp), S,
             sum(r["g_pct"] > r["allocatore_modello_pct_D11"] for r in righe)))
    print("  6 mondi distinti (descrittivo): g%% mediano %s%%, g>0 in %d/6, p(R1)>=0,90 in %d/6"
          % (fmt(float(np.median(gp6)), 4), sum(x > 0 for x in gp6), sum(p >= 0.90 for p in pp6)))
    print("  banda (descrittivo): p mediano %s; f mediano %s"
          % (fmt(float(np.median([r["p_banda_descrittivo"] for r in righe])), 3),
             fmt(float(np.median([r["f"] for r in righe if r["f"] != ""])), 3)))
    print("RAMO CALCOLATO PARTE A: " + ramo + "  (%s s)" % fmt(time.time() - tA, 1))

    # ---------------------------------------------------------------- parte B1
    tB = time.time()
    print("\nPARTE B1 - errore casuale lognormale (200 estrazioni per livello)")
    dett, esiti_b1, out_b1 = [], [], []
    for i, sig in enumerate(LIVELLI):
        per = {}
        for seed in SEMI:
            rng = np.random.default_rng(SEME_B1 + 1000 * i + seed)
            m, lst = mondi[seed], []
            for j in range(N_ESTRAZIONI):
                z = rng.standard_normal(len(m.canali))
                roas = {c: roi_v[seed][c] * float(np.exp(sig * z[k])) for k, c in enumerate(m.canali)}
                v = m.valuta(roas)
                lst.append((v["g_pct"], v["p"], v["eur"]))
                dett.append(dict(livello_sigma=sig, mondo=seed, estrazione=j + 1, g_pct=round(v["g_pct"], 5),
                                 p_R1=round(v["p"], 4), euro_mossi=round(v["eur"], 2)))
            per[seed] = lst
        repliche_ok = sum(criterio([per[s][j][0] for _, s in CASI], [per[s][j][1] for _, s in CASI])
                          for j in range(N_ESTRAZIONI))
        tutte_g = [per[s][j][0] for _, s in CASI for j in range(N_ESTRAZIONI)]
        tutte_p = [per[s][j][1] for _, s in CASI for j in range(N_ESTRAZIONI)]
        soddisfa = repliche_ok >= N_ESTRAZIONI // 2
        esiti_b1.append((sig, soddisfa))
        out_b1.append(dict(sigma=sig, repliche_che_soddisfano=repliche_ok, repliche=N_ESTRAZIONI,
                           soddisfa_il_criterio="si" if soddisfa else "no",
                           mediana_g_pct=round(float(np.median(tutte_g)), 5),
                           frazione_g_positiva=round(float(np.mean(np.array(tutte_g) > 0)), 4),
                           mediana_p_R1=round(float(np.median(tutte_p)), 4),
                           frazione_p_almeno_090=round(float(np.mean(np.array(tutte_p) >= 0.90)), 4)))
        r = out_b1[-1]
        print("  sigma %s: repliche che soddisfano %d/200 -> %s | g%% mediano %s%%, g>0 %s%%, p mediano %s, p>=0,90 %s%%"
              % (fmt(sig, 2), repliche_ok, "SODDISFA" if soddisfa else "non soddisfa", fmt(r["mediana_g_pct"], 4),
                 fmt(100 * r["frazione_g_positiva"], 1), fmt(r["mediana_p_R1"], 3), fmt(100 * r["frazione_p_almeno_090"], 1)))
    with open(os.path.join(QUI, "D14_B1_tolleranza.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_b1[0])); w.writeheader(); w.writerows(out_b1)
    with open(os.path.join(QUI, "D14_B1_estrazioni.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(dett[0])); w.writeheader(); w.writerows(dett)
    s1, elenco1 = soglia(esiti_b1)
    print("B1 livelli che soddisfano il criterio: " + (", ".join(fmt(x, 2) for x in elenco1) or "nessuno"))
    print("B1 SOGLIA DI TOLLERANZA: " + ("nemmeno con ROAS esatti" if s1 is None else "sigma = " + fmt(s1, 2))
          + "  (%s s)" % fmt(time.time() - tB, 1))

    # ---------------------------------------------------------------- parte B2
    tC = time.time()
    print("\nPARTE B2 - errore sistematico: piu' credito a chi chiude il percorso")
    out_b2, esiti_b2 = [], []
    for d in LIVELLI:
        per = {}
        for seed in SEMI:
            roas = {c: roi_v[seed][c] * float(np.exp(d if c in CHIUSURA else -d)) for c in mondi[seed].canali}
            assert set(CHIUSURA) | set(INIZIO) == set(mondi[seed].canali)
            per[seed] = mondi[seed].valuta(roas)
        gp2 = [per[s]["g_pct"] for _, s in CASI]; pp2 = [per[s]["p"] for _, s in CASI]
        soddisfa = criterio(gp2, pp2)
        esiti_b2.append((d, soddisfa))
        for dis, s in CASI:
            v = per[s]
            out_b2.append(dict(delta=d, disegno=dis, mondo=s, g_pct=round(v["g_pct"], 5), p_R1=round(v["p"], 4),
                               euro_mossi=round(v["eur"], 2),
                               riparto_pct=";".join(c + "=" + format(v["rip"][c], "+.4f") for c in mondi[s].canali),
                               soddisfa_il_criterio_livello="si" if soddisfa else "no"))
        print("  delta %s (rapporto %s): g%% mediano %s%%, p>=0,90 in %d/8 -> %s"
              % (fmt(d, 2), fmt(float(np.exp(2 * d)), 2), fmt(float(np.median(gp2)), 4),
                 sum(p >= 0.90 for p in pp2), "SODDISFA" if soddisfa else "non soddisfa"))
    with open(os.path.join(QUI, "D14_B2_sistematico.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_b2[0])); w.writeheader(); w.writerows(out_b2)
    s2, elenco2 = soglia(esiti_b2)
    print("B2 livelli che soddisfano il criterio: " + (", ".join(fmt(x, 2) for x in elenco2) or "nessuno"))
    print("B2 SOGLIA DI TOLLERANZA: " + ("nemmeno con ROAS esatti" if s2 is None else "delta = " + fmt(s2, 2))
          + "  (%s s)" % fmt(time.time() - tC, 1))
    print("\nTEMPO TOTALE %s s" % fmt(time.time() - t0, 1))


if __name__ == "__main__":
    main()
