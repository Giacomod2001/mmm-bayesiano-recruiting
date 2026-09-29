"""R1 - le sette strategie di riallocazione sugli otto casi di D11.

Si esegue DOPO `cancello_D11.py`, che verifica che la macchina ricostruita
riproduca la tabella pubblicata di D11. Le definizioni sono quelle del
paragrafo 3 della pre-registrazione `PREREGISTRAZIONE_R1_riallocazione.md`
(commit 08bc420), e non si toccano.

    python riallocazione_R1/studio_R1.py <cartella del generatore ricostruito>

AVVERTENZA CHE VALE PER TUTTE E SETTE, dal paragrafo 0 della pre-registrazione:
leggono tutte il ROI MEDIO, che e' precisamente l'errore diagnosticato nella
sezione 3 di D11. Nessuna puo' risolvere quel problema: solo la macchina
marginale puo', ed e' il disegno M1.

DUE INTERPRETAZIONI FISSATE QUI, prima di calcolare, perche' la
pre-registrazione non le specifica:

 1. `p` si calcola contro un controllo nullo costruito con la STESSA CIFRA in
    euro della strategia che si sta valutando ("stessa cifra", paragrafo 4).
    Per le strategie che non muovono nulla `p` non e' definito e si riporta
    n/d: una mossa nulla non batte e non perde. Accanto si riporta sempre
    anche `p` contro il nullo di D11 (la cifra della 90/10), per confronto
    diretto con la tabella pubblicata.
 2. I pari si contano con `<` (guadagnano STRETTAMENTE meno), che e' la
    definizione scritta nel paragrafo 3 di D11. La scelta e' dichiarata nel
    file dei risultati insieme al motivo.
"""
from __future__ import annotations

import csv
import gzip
import importlib.util
import os
import statistics
import sys

import numpy as np

QUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(QUI)

CASI = [
    ("D1/101", 101, "griglia/griglia_D1_geo_draw/D1_geo_m0101_draw.csv.gz",
     "griglia/griglia_D1_geo_canali.csv"),
    ("D1/103", 103, "griglia/griglia_D1_geo_draw/D1_geo_m0103_draw.csv.gz",
     "griglia/griglia_D1_geo_canali.csv"),
    ("D1/105", 105, "griglia/griglia_D1_geo_draw/D1_geo_m0105_draw.csv.gz",
     "griglia/griglia_D1_geo_canali.csv"),
    ("D1/107", 107, "griglia/griglia_D1_geo_draw/D1_geo_m0107_draw.csv.gz",
     "griglia/griglia_D1_geo_canali.csv"),
    ("D2/102", 102, "griglia/griglia_D2_calendario_draw/D2_cal_rot2_m0102_draw.csv.gz",
     "griglia/griglia_D2_calendario_canali.csv"),
    ("D2/103", 103, "griglia/griglia_D2_calendario_draw/D2_cal_rot3_m0103_draw.csv.gz",
     "griglia/griglia_D2_calendario_canali.csv"),
    ("D10/42", 42, "griglia_D10/griglia_D10_calendario_4giri_draw/D10_cal4_rot0_m0042_draw.csv.gz",
     "griglia_D10/griglia_D10_calendario_4giri_canali.csv"),
    ("D10/103", 103, "griglia_D10/griglia_D10_calendario_4giri_draw/D10_cal4_rot3_m0103_draw.csv.gz",
     "griglia_D10/griglia_D10_calendario_4giri_canali.csv"),
]
TAGLI_ALLOCATORE = ["Subito Lavoro", "Altre job board", "Jooble"]
BANDA = 30.0
TETTO_S6 = 5.0
N_NULLO = 200
SEME_NULLO = 20260917
SOGLIE_S1 = (0.70, 0.80, 0.90)


def carica(percorso, nome):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def macchina(g, seed):
    p = g.genera(seed=seed)
    pop = p["pop"]
    canali = list(p["canali"])
    K = {c: p["beta"][c] * (pop * p["beta_geo"][c]) for c in canali}
    ec = {c: p["ec_impr"][c] for c in canali}
    A = {c: g.adstock_geometrico(p["ch_impr"][c] / pop[None, :], g.CANALI[c]["lam"])
         for c in canali}

    def Y(d=None):
        t = 0.0
        for c in canali:
            m = 1.0 + (d.get(c, 0.0) / 100.0 if d else 0.0)
            t += float((K[c][None, :] * g.hill(m * A[c], ec[c], g.CANALI[c]["slope"])).sum())
        return t
    return Y, canali


def leggi_draw(percorso, canali):
    """(8000, 7) in FLOAT64: i file sono in float32 (passo 0)."""
    with gzip.open(percorso, "rt", encoding="utf-8") as f:
        import pandas as pd
        d = pd.read_csv(f)
    return np.column_stack([d[c].to_numpy(dtype=np.float64) for c in canali])


def coppia(a, b, euro, spesa):
    return {a: +100.0 * euro / spesa[a], b: -100.0 * euro / spesa[b]}


def euro_mossi(d, spesa):
    return sum(spesa[c] * v / 100.0 for c, v in d.items() if v > 0)


def nullo(Y, y0, canali, spesa, euro, seme):
    rng = np.random.default_rng(SEME_NULLO + seme)
    tutte = [(a, b) for a in canali for b in canali if a != b]
    fuori = []
    if euro <= 0:
        return np.array([]), tutte
    while len(fuori) < N_NULLO:
        a, b = tutte[int(rng.integers(0, len(tutte)))]
        if euro > spesa[b]:
            continue
        fuori.append(Y(coppia(a, b, euro, spesa)) - y0)
    return np.array(fuori), tutte


def oracolo(Y, y0, tutte, spesa, euro):
    if euro <= 0:
        return 0.0
    return max(Y(coppia(a, b, euro, spesa)) - y0 for a, b in tutte if euro <= spesa[b])


def main(cartella_generatore):
    g = carica(os.path.join(cartella_generatore, "genera_dati_simulati.py"), "gen")
    pb = carica(os.path.join(ROOT, "proposta_budget.py"), "pb")
    cache, righe = {}, []

    for et, seme, draw, can in CASI:
        if seme not in cache:
            cache[seme] = macchina(g, seme)
        Y, canali = cache[seme]
        spesa = {x["canale"]: float(x["spesa"])
                 for x in csv.DictReader(open(os.path.join(ROOT, can), newline="", encoding="utf-8"))
                 if x["seed_mondo"] == str(seme)}
        y0 = Y()
        contrib = leggi_draw(os.path.join(ROOT, draw), canali)          # (8000, 7)
        sp = np.array([spesa[c] for c in canali], dtype=np.float64)
        ROI = contrib / sp[None, :]                                     # ROI MEDIO per draw
        idx = {c: i for i, c in enumerate(canali)}
        tutte = [(a, b) for a in canali for b in canali if a != b]

        # --- la 90/10 e l'allocatore, come in D11 -----------------------
        P90, _ = pb.probabilita(os.path.join(ROOT, draw), spesa)
        rr, euro_b = pb.proposta(P90, spesa)
        d_b = {c: dl for c, _p, dec, dl, _, _ in rr if dec in ("ALZA", "TAGLIA")}
        su = [c for c, v in d_b.items() if v > 0]
        giu = [c for c, v in d_b.items() if v < 0]
        liberati = sum(BANDA / 100.0 * spesa[c] for c in TAGLI_ALLOCATORE)
        d_alloc = {c: -BANDA for c in TAGLI_ALLOCATORE}
        d_alloc["Google Ads"] = 100.0 * liberati / spesa["Google Ads"]

        # P(A > B) con B = media dei cedenti pesata per gli euro ceduti
        a0 = su[0]
        pesi = np.array([abs(d_b[c]) * spesa[c] for c in giu])
        pesi = pesi / pesi.sum()
        roi_b = sum(w * ROI[:, idx[c]] for w, c in zip(pesi, giu))
        P_ab = float(np.mean(ROI[:, idx[a0]] > roi_b))

        # guadagno stimato per coppia, draw per draw (euro fuori: si scala dopo)
        gain_unit = {(a, b): ROI[:, idx[a]] - ROI[:, idx[b]] for a, b in tutte}

        strategie = {}
        for s in SOGLIE_S1:
            strategie["S1 freno %.2f" % s] = (dict(d_b) if P_ab >= s else {})
        k2 = max(0.0, 2.0 * (P_ab - 0.5))
        strategie["S2 taglia x certezza"] = {c: v * k2 for c, v in d_b.items()} if k2 > 0 else {}
        for nome, f in (("1/2", 0.5), ("1/4", 0.25)):
            strategie["S3 passo " + nome] = {c: v * f for c, v in d_alloc.items()}
        # S4: la coppia migliore DENTRO ogni draw, poi la media dei riparti
        M = np.column_stack([gain_unit[p] for p in tutte])               # (8000, 42)
        scelte = np.argmax(M, axis=1)
        d_s4 = {}
        for j, (a, b) in enumerate(tutte):
            q = float(np.mean(scelte == j))
            if q > 0:
                d_s4[a] = d_s4.get(a, 0.0) + q * 100.0 * euro_b / spesa[a]
                d_s4[b] = d_s4.get(b, 0.0) - q * 100.0 * euro_b / spesa[b]
        strategie["S4 dentro il draw"] = d_s4
        # S5: massimo del 5o percentile del guadagno stimato
        p5 = {p: float(np.quantile(gain_unit[p] * euro_b, 0.05)) for p in tutte}
        migliore = max(p5, key=p5.get)
        strategie["S5 quinto percentile"] = (coppia(migliore[0], migliore[1], euro_b, spesa)
                                             if p5[migliore] > 0 else {})
        # S6: direzione dell'allocatore, tetto del 5% per canale
        lib6 = sum(TETTO_S6 / 100.0 * spesa[c] for c in TAGLI_ALLOCATORE)
        d_s6 = {c: -TETTO_S6 for c in TAGLI_ALLOCATORE}
        d_s6["Google Ads"] = min(TETTO_S6, 100.0 * lib6 / spesa["Google Ads"])
        strategie["S6 tetto 5%"] = d_s6
        # S7: le prime tre coppie per guadagno stimato mediano, un terzo ciascuna
        med = {p: float(np.median(gain_unit[p])) for p in tutte}
        prime3 = sorted(med, key=med.get, reverse=True)[:3]
        d_s7 = {}
        for a, b in prime3:
            d_s7[a] = d_s7.get(a, 0.0) + 100.0 * (euro_b / 3.0) / spesa[a]
            d_s7[b] = d_s7.get(b, 0.0) - 100.0 * (euro_b / 3.0) / spesa[b]
        strategie["S7 mossa diffusa"] = d_s7

        # riferimenti
        strategie["-- 90/10 (D11)"] = dict(d_b)
        strategie["-- allocatore (D11)"] = dict(d_alloc)

        nulli, oracoli = {}, {}
        nullo_b, _ = nullo(Y, y0, canali, spesa, euro_b, seme)
        for nome, d in strategie.items():
            e = euro_mossi(d, spesa)
            gab = Y(d) - y0 if d else 0.0
            chiave = round(e, 2)
            if chiave not in nulli:
                nulli[chiave], _ = nullo(Y, y0, canali, spesa, e, seme)
                oracoli[chiave] = oracolo(Y, y0, tutte, spesa, e)
            n = nulli[chiave]
            p_pro = float(np.mean(n < gab)) if len(n) else None
            p_d11 = float(np.mean(nullo_b < gab)) if len(nullo_b) else None
            orc = oracoli[chiave]
            righe.append(dict(
                caso=et, seme=seme, strategia=nome,
                g_abs=round(gab, 1), g_pct=round(100.0 * gab / y0, 4),
                eur_mossi=round(e, 2),
                cand_per_eur=round(gab / e, 6) if e > 0 else "",
                p=("" if p_pro is None else round(p_pro, 3)),
                p_nullo_9010=("" if p_d11 is None else round(p_d11, 3)),
                f=(round(gab / orc, 3) if orc else ""),
                P_ab=round(P_ab, 4),
                riparto=";".join("%s=%+.3f" % (c, v) for c, v in sorted(d.items())) or "(nulla)"))
        print("  %-9s fatto (P(A>B)=%.3f, euro 90/10 %.0f)" % (et, P_ab, euro_b))

    with open(os.path.join(QUI, "R1_risultati.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(righe[0]))
        w.writeheader()
        w.writerows(righe)

    def q(x, d=3):
        return "n/d" if x in ("", None) else format(float(x), "." + str(d) + "f").replace(".", ",")

    nomi = []
    for r in righe:
        if r["strategia"] not in nomi:
            nomi.append(r["strategia"])
    print()
    print("=" * 104)
    print("R1 - LE SETTE STRATEGIE, mediane sugli otto casi")
    print("=" * 104)
    print("%-22s %10s %9s %10s %8s %8s %7s" %
          ("strategia", "g% mediano", "casi >0", "EUR mediani", "p mediano", "p>=0,90", "f mediano"))
    sintesi = {}
    for nome in nomi:
        rr = [r for r in righe if r["strategia"] == nome]
        gp = [r["g_pct"] for r in rr]
        eu = [r["eur_mossi"] for r in rr]
        ps = [r["p"] for r in rr if r["p"] != ""]
        fs = [r["f"] for r in rr if r["f"] != ""]
        n90 = sum(1 for r in rr if r["p"] != "" and r["p"] >= 0.90)
        sintesi[nome] = dict(g=statistics.median(gp), n_pos=sum(1 for x in gp if x > 0),
                             eur=statistics.median(eu), n90=n90,
                             p=(statistics.median(ps) if ps else None),
                             f=(statistics.median(fs) if fs else None))
        s = sintesi[nome]
        print("%-22s %9s%% %7d/8 %10s %8s %6d/8 %7s" %
              (nome, q(s["g"], 3), s["n_pos"], q(s["eur"], 0), q(s["p"]), s["n90"], q(s["f"])))

    vere = [n for n in nomi if not n.startswith("--")]
    ramo1 = [n for n in vere if sintesi[n]["g"] > 0 and sintesi[n]["n90"] >= 6]
    ramo2 = [n for n in vere if sintesi[n]["g"] >= -0.10 and sintesi[n]["eur"] < 10000]
    # Correzione del 23/9, dopo il primo calcolo: prima il ramo 3 era l'else, e
    # veniva stampato anche quando la sua condizione (paragrafo 5: TUTTE con g%
    # mediano < -0,10%) non vale. La regola registrata non e' esaustiva, e se
    # nessuna riga corrisponde lo si stampa. Nessuna soglia e' cambiata.
    ramo3 = all(sintesi[n]["g"] < -0.10 for n in vere)
    print()
    if ramo1:
        print("RAMO 1 - FUNZIONA: " + ", ".join(ramo1))
    elif ramo2:
        print("RAMO 2 - IL VALORE DEL MODELLO E' IL FRENO, NON IL VOLANTE")
        print("         strategie che lo soddisfano: " + ", ".join(ramo2))
    elif ramo3:
        print("RAMO 3 - NESSUNA RIALLOCAZIONE E' DIFENDIBILE SU QUESTO POSTERIORE")
    else:
        print("NESSUN RAMO - nessuna riga della regola del paragrafo 5 corrisponde")
        print("  riga 1: nessuna con g% mediano > 0 e p >= 0,90 in almeno 6 casi su 8")
        print("  riga 2: nessuna con g% mediano >= -0,10% e meno di 10.000 EUR mediani")
        print("  riga 3: non tutte hanno g% mediano < -0,10%: " +
              ", ".join(n for n in vere if sintesi[n]["g"] >= -0.10))
    print()
    print("Previsione registrata: ramo 2, con S4 la migliore fra quelle che muovono")
    print("e S1 a 0,80 che quasi non muove mai.")
    print("scritto", os.path.join(QUI, "R1_risultati.csv"))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    sys.exit(main(sys.argv[1]))
