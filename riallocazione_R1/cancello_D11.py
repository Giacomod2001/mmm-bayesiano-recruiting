"""R1 - il cancello del paragrafo 2-bis: la macchina di D11, ricostruita.

Il 21/9 `studio_D11.py`, la patch G5 e `D11_pacchetto` non si trovavano (cercati
in tutto il progetto, anche fuori da git), e la macchina e' stata riscritta da
zero seguendo il paragrafo 0 di `RISULTATI_D11_riparto_controfattuale_2026-09-17.md`.
Il 22/9 l'originale e' stato ritrovato fuori dal repository ed e' ora in
`allocatore_D11_D11b/`: questa ricostruzione resta quella del cancello registrato.
Cio' che fa:

    mondo BASE dello stesso seme, `beta` ed `ec` fissi, spesa di ogni canale
    scalata del suo moltiplicatore, contributo vero ricalcolato sotto le curve

Prima di calcolare una sola delle sette strategie deve riprodurre la tabella
del paragrafo 1 di D11, riga per riga, con le tolleranze della
pre-registrazione. Questo script fa solo quello e scrive R1_cancello_D11.csv.

    python riallocazione_R1/cancello_D11.py <cartella del generatore ricostruito>

Il generatore ricostruito e' `main` del repo pubblico + la catena A + G1..G4
(+ G6, che non cambia il percorso senza flag), impronta `8f86eb032d0113c0`.

NOTA SULLA LINEARITA': l'adstock geometrico normalizzato e' lineare, quindi
adstock(impr x m) = m x adstock(impr). L'adstock si calcola una volta per
mondo e si riscala: e' la stessa proprieta' che D11 dichiara al suo paragrafo 0,
e rende il cancello e le sette strategie un conto di secondi invece che di ore.

CONVENZIONE SUI PARI, DICHIARATA QUI: `p_b` e' la frazione delle 200 casuali
che guadagnano STRETTAMENTE MENO di (b). E' la definizione scritta al paragrafo
3 di D11 ("frazione delle 200 casuali che guadagnano MENO di (b)"), ed e' anche
quella del codice originale, ritrovato il 22/9 in allocatore_D11_D11b/:
`p_b = (gd < gb).mean()`, riga 135 di studio_D11.py.

PERCHE' p_b NON SI RIPRODUCE SU TRE CASI. La coppia di (b) puo' essere estratta
dal nullo, e allora la mossa casuale coincide con quella della regola. Qui le
due mosse sono calcolate dalla stessa aritmetica, i pari sono esatti e il
minore stretto li esclude sempre. Nell'originale le due mosse arrivavano da
due fonti diverse della spesa: la 90/10 calcola le percentuali sulla spesa del
file dei canali (spesa_fit, arrotondata al centesimo; riga 81 di studio_D11.py),
il nullo sulla spesa del generatore (riga 108, eur_b_mondo). Per la stessa
coppia le due mosse differiscono quindi all'ultima cifra: i riparti di D2/103 e D10/103,
che sono lo stesso calcolo, valgono Meta Ads -8,444655 e -8,444656, e
D11_risultati.csv riporta p_b 0,56 e 0,53. I quasi-pareggi cadevano sotto o
sopra a seconda dell'arrotondamento. Non sono due convenzioni diverse, come
era stato ipotizzato leggendo la sola tabella il 21/9: e' una convenzione sola,
numericamente instabile sui pari.
"""
from __future__ import annotations

import csv
import importlib.util
import os
import statistics
import sys

import numpy as np

QUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(QUI)

# La tabella del paragrafo 1 di D11, copiata dal file e non a memoria.
# (caso, seme, draw, canali, g_b%, g_c%, nullo 90째, p_b, f_b, EUR(b), EUR(c))
D11 = [
    ("D1/101", 101, "griglia/griglia_D1_geo_draw/D1_geo_m0101_draw.csv.gz",
     "griglia/griglia_D1_geo_canali.csv", -0.149, -1.033, 770.6, 0.565, -0.221, 75590, 123173),
    ("D1/103", 103, "griglia/griglia_D1_geo_draw/D1_geo_m0103_draw.csv.gz",
     "griglia/griglia_D1_geo_canali.csv", -0.120, -1.261, 512.2, 0.500, -0.183, 79301, 125451),
    ("D1/105", 105, "griglia/griglia_D1_geo_draw/D1_geo_m0105_draw.csv.gz",
     "griglia/griglia_D1_geo_canali.csv", +0.356, -1.298, 564.2, 0.890, 0.437, 77081, 117643),
    ("D1/107", 107, "griglia/griglia_D1_geo_draw/D1_geo_m0107_draw.csv.gz",
     "griglia/griglia_D1_geo_canali.csv", -0.848, -1.178, 679.6, 0.470, -0.758, 145079, 123074),
    ("D2/102", 102, "griglia/griglia_D2_calendario_draw/D2_cal_rot2_m0102_draw.csv.gz",
     "griglia/griglia_D2_calendario_canali.csv", +0.365, -1.060, 601.9, 0.880, 0.463, 74737, 116788),
    ("D2/103", 103, "griglia/griglia_D2_calendario_draw/D2_cal_rot3_m0103_draw.csv.gz",
     "griglia/griglia_D2_calendario_canali.csv", -0.082, -1.261, 512.2, 0.560, -0.125, 79301, 125451),
    ("D10/42", 42, "griglia_D10/griglia_D10_calendario_4giri_draw/D10_cal4_rot0_m0042_draw.csv.gz",
     "griglia_D10/griglia_D10_calendario_4giri_canali.csv", +0.173, -1.271, 753.4, 0.690, 0.227, 76726, 112945),
    ("D10/103", 103, "griglia_D10/griglia_D10_calendario_4giri_draw/D10_cal4_rot3_m0103_draw.csv.gz",
     "griglia_D10/griglia_D10_calendario_4giri_canali.csv", -0.082, -1.261, 512.2, 0.530, -0.125, 79301, 125451),
]

# tolleranze del paragrafo 2-bis della pre-registrazione, non allargabili
TOLL = {"g_b": 0.010, "g_c": 0.010, "p_b": 0.010, "f_b": 0.010,
        "eur_b": 1.0, "eur_c": 1.0, "nullo90_rel": 0.01, "y0": 0.5}
TAGLI_ALLOCATORE = ["Subito Lavoro", "Altre job board", "Jooble"]
BANDA = 30.0
N_NULLO = 200
SEME_NULLO = 20260917


def carica(percorso, nome):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def macchina(g, seed):
    """riparto -> contributo vero totale, a beta ed ec fissi del mondo base."""
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


def coppia(a, b, euro, spesa):
    return {a: +100.0 * euro / spesa[a], b: -100.0 * euro / spesa[b]}


def allocatore(spesa):
    liberati = sum(BANDA / 100.0 * spesa[c] for c in TAGLI_ALLOCATORE)
    d = {c: -BANDA for c in TAGLI_ALLOCATORE}
    d["Google Ads"] = 100.0 * liberati / spesa["Google Ads"]
    return d, liberati


def main(cartella_generatore):
    g = carica(os.path.join(cartella_generatore, "genera_dati_simulati.py"), "gen")
    pb = carica(os.path.join(ROOT, "proposta_budget.py"), "pb")
    cache, righe = {}, []
    for (et, seme, draw, can, gb_a, gc_a, n90_a, pb_a, fb_a, eb_a, ec_a) in D11:
        if seme not in cache:
            cache[seme] = macchina(g, seme)
        Y, canali = cache[seme]
        spesa = {x["canale"]: float(x["spesa"])
                 for x in csv.DictReader(open(os.path.join(ROOT, can), newline="", encoding="utf-8"))
                 if x["seed_mondo"] == str(seme)}
        P, _ = pb.probabilita(os.path.join(ROOT, draw), spesa)
        rr, euro_b = pb.proposta(P, spesa)
        d_b = {c: dl for c, _p, dec, dl, _, _ in rr if dec in ("ALZA", "TAGLIA")}
        y0 = Y()
        gb_abs = Y(d_b) - y0
        gb = 100.0 * gb_abs / y0
        d_c, euro_c = allocatore(spesa)
        gc = 100.0 * (Y(d_c) - y0) / y0
        rng = np.random.default_rng(SEME_NULLO + seme)
        tutte = [(a, b) for a in canali for b in canali if a != b]
        nullo = []
        while len(nullo) < N_NULLO:
            a, b = tutte[int(rng.integers(0, len(tutte)))]
            if euro_b > spesa[b]:
                continue
            nullo.append(Y(coppia(a, b, euro_b, spesa)) - y0)
        nullo = np.array(nullo)
        pari = int(np.sum(np.isclose(nullo, gb_abs, rtol=0, atol=1e-6)))
        p_lt = float(np.mean(nullo < gb_abs))
        p_le = float(np.mean(nullo <= gb_abs))
        n90 = float(np.quantile(nullo, 0.90))
        oracolo = max(Y(coppia(a, b, euro_b, spesa)) - y0
                      for a, b in tutte if euro_b <= spesa[b])
        fb = gb_abs / oracolo if oracolo else float("nan")
        righe.append(dict(
            caso=et, seme=seme, y0=round(y0, 1), g_b_abs=round(gb_abs, 1),
            g_b=round(gb, 3), g_b_atteso=gb_a, g_b_ok=abs(gb - gb_a) <= TOLL["g_b"],
            g_c=round(gc, 3), g_c_atteso=gc_a, g_c_ok=abs(gc - gc_a) <= TOLL["g_c"],
            nullo90=round(n90, 1), nullo90_atteso=n90_a,
            nullo90_ok=abs(n90 - n90_a) <= abs(n90_a) * TOLL["nullo90_rel"],
            p_b_lt=round(p_lt, 3), p_b_le=round(p_le, 3), p_b_atteso=pb_a,
            p_b_pari=pari,
            p_b_ok_lt=abs(p_lt - pb_a) <= TOLL["p_b"],
            p_b_ok_le=abs(p_le - pb_a) <= TOLL["p_b"],
            f_b=round(fb, 3), f_b_atteso=fb_a, f_b_ok=abs(fb - fb_a) <= TOLL["f_b"],
            eur_b=round(euro_b, 2), eur_b_atteso=eb_a, eur_b_ok=abs(euro_b - eb_a) <= TOLL["eur_b"],
            eur_c=round(euro_c, 2), eur_c_atteso=ec_a, eur_c_ok=abs(euro_c - ec_a) <= TOLL["eur_c"],
            riparto=";".join("%s=%+.2f" % (c, v) for c, v in d_b.items())))

    with open(os.path.join(QUI, "R1_cancello_D11.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(righe[0]))
        w.writeheader()
        w.writerows(righe)

    def q(x, d=3):
        return format(x, "." + str(d) + "f").replace(".", ",")

    print("=" * 104)
    print("R1 - CANCELLO DEL PARAGRAFO 2-BIS: la macchina di D11 ricostruita")
    print("=" * 104)
    print()
    print("%-9s %10s %9s %9s | %8s %8s | %8s %8s | %7s %7s | %9s %9s" %
          ("caso", "Y(0)", "g_b", "atteso", "g_c", "atteso", "nullo90", "atteso",
           "f_b", "atteso", "EUR(b)", "EUR(c)"))
    for r in righe:
        print("%-9s %10s %8s%% %8s%% | %7s%% %7s%% | %8s %8s | %7s %7s | %9s %9s" %
              (r["caso"], q(r["y0"], 1), q(r["g_b"]), q(r["g_b_atteso"]),
               q(r["g_c"]), q(r["g_c_atteso"]), q(r["nullo90"], 1), q(r["nullo90_atteso"], 1),
               q(r["f_b"]), q(r["f_b_atteso"]), q(r["eur_b"], 0), q(r["eur_c"], 0)))
    print()
    colonne = [("g_b %", "g_b_ok"), ("g_c %", "g_c_ok"), ("nullo 90", "nullo90_ok"),
               ("f_b", "f_b_ok"), ("EUR (b)", "eur_b_ok"), ("EUR (c)", "eur_c_ok")]
    esito = True
    for nome, chiave in colonne:
        n = sum(1 for r in righe if r[chiave])
        esito = esito and n == len(righe)
        print("  %-10s riprodotta su %d righe su %d   %s" %
              (nome, n, len(righe), "OK" if n == len(righe) else "NON RIPRODOTTA"))
    n_lt = sum(1 for r in righe if r["p_b_ok_lt"])
    n_le = sum(1 for r in righe if r["p_b_ok_le"])
    print("  %-10s con < : %d su %d   con <= : %d su %d   %s" %
          ("p_b", n_lt, len(righe), n_le, len(righe),
           "OK" if max(n_lt, n_le) == len(righe) else "NON RIPRODOTTA CON NESSUNA CONVENZIONE"))
    print()
    print("  dettaglio p_b (pari = estrazioni del nullo che replicano la coppia di (b)):")
    for r in righe:
        print("    %-9s D11 %s | < %s | <= %s | pari %2d  -> coincide con %s" %
              (r["caso"], q(r["p_b_atteso"]), q(r["p_b_lt"]), q(r["p_b_le"]), r["p_b_pari"],
               ("< e <=" if r["p_b_ok_lt"] and r["p_b_ok_le"] else
                "<" if r["p_b_ok_lt"] else "<=" if r["p_b_ok_le"] else "NESSUNA")))
    print()
    med_lt = statistics.median(r["p_b_lt"] for r in righe)
    med_le = statistics.median(r["p_b_le"] for r in righe)
    med_d11 = statistics.median(r["p_b_atteso"] for r in righe)
    print("  mediana di p_b:  con <  %s   con <=  %s   colonna pubblicata da D11  %s" %
          (q(med_lt), q(med_le), q(med_d11)))
    print()
    print("ESITO:", "CANCELLO SUPERATO" if esito and max(n_lt, n_le) == len(righe) else
          "SEI COLONNE SU SETTE RIPRODOTTE; p_b NO (vedi sopra e il file dei risultati)")
    print("scritto", os.path.join(QUI, "R1_cancello_D11.csv"))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    sys.exit(main(sys.argv[1]))
