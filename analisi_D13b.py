"""Legge i CSV prodotti dal notebook D13b (cartella `MMM_griglia_D13b_1nodo`
scaricata da Drive) e quelli di N1, D13 e D0 nel repository, e STAMPA I RAMI di
D13b in prima riga: il ramo del livello e il ramo dell'ordine, con la previsione
confermata o smentita. Poi il cancello di replica e tutto quello che il
paragrafo 5 della pre-registrazione chiede di riportare.

    python analisi_D13b.py <cartella MMM_griglia_D13b_1nodo> [--repo <clone>]

Committato INSIEME a preregistrazioni/PREREGISTRAZIONE_D13b_baseline_osservata_1nodo.md,
prima di qualunque fit: e' la regola scritta in codice. Soglie e rami sono
quelli della pre-registrazione del 23 settembre 2026 e non si toccano:

  cancello  la replica (D13, f = 0,30, mondo 101, 12 nodi/trim.) = riga di D13
            alla quarta cifra, altrimenti nessun ramo
  livello   dE_w = E_w(D13b) - E_w(N1, 1 nodo/trim.), sugli N mondi ammissibili
            0: N < 5 -> NON LEGGIBILE
            1: E mediano di D13b <= 4,0 -> IL CONTROLLO ORGANICO RECUPERA LA BASELINE
            2: mediana dE <= -5,0 e dE < 0 in >= soglia(N) -> IL CONTROLLO AIUTA, MA NON BASTA
            3: mediana dE >= +5,0 e dE > 0 in >= soglia(N) -> IL CONTROLLO PEGGIORA LA SOVRASTIMA
            4: altrimenti -> ANCHE A 1 NODO IL CONTROLLO NON SPOSTA IL LIVELLO IN MODO NETTO
  ordine    mediana di rho sugli N mondi ammissibili
            0: N < 5 -> NON LEGGIBILE
            A: mediana >= 17/28 (+0,6071)   B: mediana > 13/56 (+0,2321)   C: altrimenti
  soglia(N) = 6 se N = 8, altrimenti int(6/8 * N + 0,5)
  previsione registrata: livello ramo 4, ordine ramo C

Aritmetica esatta: E in centesimi interi (le colonne delle quote hanno due
decimali), rho in 28esimi interi (sette canali senza pari merito), mediane in
56esimi. Solo libreria standard. Su Windows: PYTHONIOENCODING=utf-8.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from fractions import Fraction

MONDI = [42, 101, 102, 103, 104, 105, 106, 107]
F = "0.3"
MONDO_REPLICA = 101
NOME_REPLICA = "D13b_k12_replica_f030_m0101"
CSV_LIVELLO = "griglia_D13b_k01.csv"
CSV_REPLICA = "griglia_D13b_replica_k12.csv"
CAMPI_REPLICA = (("rapporto_mediana", 4), ("pit", 6), ("rapporto_ci05", 4), ("rapporto_ci95", 4),
                 ("dentro", 0))
SPESA_INVERSA = Fraction(17, 28)
CASO = Fraction(13, 56)
PREVISIONE = ("4", "C")
TESTI_LIVELLO = {
    "0": "NON LEGGIBILE",
    "1": "IL CONTROLLO ORGANICO RECUPERA LA BASELINE, SE I NODI NON SE LA PRENDONO",
    "2": "IL CONTROLLO AIUTA, MA NON BASTA",
    "3": "IL CONTROLLO PEGGIORA LA SOVRASTIMA",
    "4": "ANCHE A 1 NODO IL CONTROLLO ORGANICO NON SPOSTA IL LIVELLO IN MODO NETTO"}
TESTI_ORDINE = {
    "0": "NON LEGGIBILE",
    "A": "CON BASELINE RIGIDA E CONTROLLO ORGANICO MERIDIAN ORDINA ALMENO COME LA REGOLA EMPIRICA",
    "B": "MEGLIO DEL CASO, NON MEGLIO DELLA REGOLA EMPIRICA",
    "C": "L'ORDINE NON SI DISTINGUE DAL CASO"}


def leggi(percorso):
    if not (os.path.exists(percorso) and os.path.getsize(percorso) > 0):
        return []
    with open(percorso, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def centesimi(x):
    """'22.38' -> 2238, esatto (le quote hanno due decimali)."""
    return int(round(Fraction(str(x).strip()) * 100))


def e_cent(r):
    return centesimi(r["quota_media_stimata_pct"]) - centesimi(r["quota_media_vera_pct"])


def rho_28(x):
    """rho di Spearman su sette canali senza pari merito = k/28 esatto. Il CSV lo
    scrive a quattro decimali: l'arrotondamento sposta k al massimo di 28 x 0,00005
    = 0,0014, lontanissimo dal passo 1 fra due valori possibili."""
    k = Fraction(str(x).strip()) * 28
    k_int = int(round(k))
    if abs(k - k_int) > Fraction(1, 100):
        raise ValueError("rho non e' un multiplo di 1/28: " + str(x))
    return k_int


def mediana(valori):
    """Mediana esatta di interi o frazioni."""
    v = sorted(Fraction(x) for x in valori)
    n = len(v)
    if n == 0:
        return None
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def soglia(n):
    return 6 if n == 8 else int(6 / 8 * n + 0.5)


def ammissibile(r):
    if r.get("esito") != "ok":
        return False
    for campo, lim, verso in (("rhat_roi_m", 1.1, "max"), ("rhat_beta_m", 1.1, "max"),
                              ("ess_roi_m", 100.0, "min"), ("ess_beta_m", 100.0, "min")):
        v = num(r.get(campo))
        if v is None or (verso == "max" and v > lim + 1e-9) or (verso == "min" and v < lim):
            return False
    return True


def per_mondo(righe):
    """{seme: riga}, l'ultima riga ok di ogni mondo."""
    out = {}
    for r in righe:
        if r.get("esito") == "ok":
            out[int(r["seed_mondo"])] = r
    return out


def cancello(cartella, d13):
    """(esito, dettaglio). esito: 'riuscita', 'fallita', 'assente'."""
    righe = [r for r in leggi(os.path.join(cartella, CSV_REPLICA)) if r.get("mondo") == NOME_REPLICA]
    if not righe or righe[-1].get("esito") != "ok":
        return "assente", "nessuna riga ok della replica in " + CSV_REPLICA
    r = righe[-1]
    att = d13[MONDO_REPLICA]
    diff = []
    for campo, dec in CAMPI_REPLICA:
        a, o = num(att.get(campo)), num(r.get(campo))
        if a is None or o is None or round(a, dec) != round(o, dec):
            diff.append(campo + " " + str(r.get(campo)) + " invece di " + str(att.get(campo)))
    for campo in ("impronta_input_data", "n_knots"):
        if str(r.get(campo)) != str(att.get(campo)):
            diff.append(campo + " " + str(r.get(campo)) + " invece di " + str(att.get(campo)))
    if num(r.get("controllo_baseline_f")) is None or abs(num(r.get("controllo_baseline_f")) - 0.3) > 1e-9:
        diff.append("controllo_baseline_f " + str(r.get("controllo_baseline_f")) + " invece di 0.3")
    if diff:
        return "fallita", " | ".join(diff)
    return "riuscita", ("rapporto_mediana " + r["rapporto_mediana"] + ", pit " + r["pit"] + ", forbice " +
                        r["rapporto_ci05"] + "-" + r["rapporto_ci95"] + ", impronta " +
                        r["impronta_input_data"] + ", " + r["n_knots"] + " nodi: uguale alla riga di D13")


def regola_livello(ok, n1):
    """ok: {seme: riga di D13b ammissibile}; n1: {seme: riga di N1 a 1 nodo}."""
    N = len(ok)
    dett = {"N": N, "soglia": soglia(N) if N else None}
    if N < 5:
        return "0", dett
    E = {w: e_cent(r) for w, r in ok.items()}
    dE = {w: E[w] - e_cent(n1[w]) for w in ok}
    dett.update(E=E, dE=dE, E_med=mediana(E.values()), dE_med=mediana(dE.values()),
                pos=sum(1 for v in dE.values() if v > 0), neg=sum(1 for v in dE.values() if v < 0))
    if dett["E_med"] <= 400:
        return "1", dett
    if dett["dE_med"] <= -500 and dett["neg"] >= dett["soglia"]:
        return "2", dett
    if dett["dE_med"] >= 500 and dett["pos"] >= dett["soglia"]:
        return "3", dett
    return "4", dett


def regola_ordine(ok, canali):
    N = len(ok)
    dett = {"N": N}
    if N < 5:
        return "0", dett
    rho = {}
    for w in ok:
        v = [c["rho_spearman"] for c in canali if int(c["seed_mondo"]) == w and c.get("rho_spearman")]
        if not v:
            raise SystemExit("rho del mondo %d assente dal CSV per canale" % w)
        rho[w] = rho_28(v[0])
    med = mediana(rho.values()) / 28
    dett.update(rho=rho, med=med)
    if med >= SPESA_INVERSA:
        return "A", dett
    if med > CASO:
        return "B", dett
    return "C", dett


def it(x, dec=2, segno=True):
    if x is None:
        return "n/d"
    s = format(float(x), ("+" if segno else "") + "." + str(dec) + "f")
    return s.replace(".", ",").replace("-", "−")


def esito_previsione(ramo, previsto, smentite):
    if ramo == previsto:
        return "CONFERMATA"
    if ramo in smentite:
        return "SMENTITA"
    return "NON CONFERMATA"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cartella")
    ap.add_argument("--repo", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    d0 = per_mondo(leggi(os.path.join(a.repo, "griglia", "griglia_D0_osservativo.csv")))
    n1 = per_mondo(leggi(os.path.join(a.repo, "griglia_N1", "griglia_N1_k01.csv")))
    d13 = per_mondo([r for r in leggi(os.path.join(a.repo, "griglia_D13", "griglia_D13_baseline_osservata.csv"))
                     if r.get("controllo_baseline_f") == F])
    if sorted(n1) != MONDI or sorted(d0) != MONDI or MONDO_REPLICA not in d13:
        raise SystemExit("riferimenti incompleti nel repository (N1 a 1 nodo, D0 o D13 a f = 0,30)")

    st, msg = cancello(a.cartella, d13)
    if st != "riuscita":
        print("D13b - NESSUN RAMO: cancello di replica " + st.upper() + " (" + msg + ")")
        print("Pre-registrazione, paragrafo 2: senza replica riuscita nessun fit a 1 nodo si legge.")
        return 2

    righe = leggi(os.path.join(a.cartella, CSV_LIVELLO))
    tutti = per_mondo(righe)
    fuori = [w for w in tutti if w not in MONDI]
    if fuori:
        raise SystemExit("mondi inattesi nel CSV: " + str(fuori))
    for w, r in tutti.items():
        if str(r.get("n_knots")) != "8" or num(r.get("controllo_baseline_f")) is None \
                or abs(num(r["controllo_baseline_f"]) - 0.3) > 1e-9 \
                or r.get("impronta_input_data") != d0[w]["impronta_input_data"]:
            raise SystemExit("riga del mondo %d non conforme alla tabella (nodi, f o impronta)" % w)
    ok = {w: r for w, r in tutti.items() if ammissibile(r)}
    canali = leggi(os.path.join(a.cartella, CSV_LIVELLO.replace(".csv", "_canali.csv")))

    rl, dl = regola_livello(ok, n1)
    ro, do = regola_ordine(ok, canali)
    print("D13b - LIVELLO: ramo " + rl + " (" + TESTI_LIVELLO[rl] + ") | ORDINE: ramo " + ro + " (" +
          TESTI_ORDINE[ro] + ")")
    print("previsione dichiarata (livello 4, ordine C): livello " +
          esito_previsione(rl, "4", ("1", "2")) + ", ordine " + esito_previsione(ro, "C", ("A", "B")))
    print()
    print("CAVEAT (paragrafo 0): il controllo e' costruito dalla baseline VERA: e' un limite SUPERIORE di")
    print("quello che un dato reale potrebbe dare, e nel mondo reale sarebbe in parte un mediatore.")
    print()
    print("CANCELLO DI REPLICA: riuscito - " + msg)
    print()
    print("REGOLA DEL LIVELLO: N = %d mondi ammissibili, soglia %s" % (dl["N"], dl["soglia"]))
    if dl["N"] >= 5:
        print("  E mediano di D13b " + it(dl["E_med"] / 100, 3) + " | mediana dE " + it(dl["dE_med"] / 100, 3) +
              " punti | dE > 0 in %d, < 0 in %d" % (dl["pos"], dl["neg"]))
    print("REGOLA DELL'ORDINE: N = %d" % do["N"] + (" | mediana rho " + it(do["med"], 4) +
          " contro spesa inversa +0,6071 e caso +0,2321" if do["N"] >= 5 else ""))
    print()
    print("MONDO PER MONDO (E in punti; D13 a f = 0,30 e' a 96 nodi)")
    print("  mondo | amm | E D13b | E N1 1 nodo |     dE | E D13 f030 | E D0 | effetto a 96 | rho D13b")
    for w in MONDI:
        r = tutti.get(w)
        eb = e_cent(r) / 100 if r else None
        en1 = e_cent(n1[w]) / 100
        e13 = e_cent(d13[w]) / 100 if w in d13 else None
        ed0 = e_cent(d0[w]) / 100
        amm13 = "" if w not in d13 or ammissibile(d13[w]) else " (D13 non amm.)"
        rh = [c["rho_spearman"] for c in canali if int(c["seed_mondo"]) == w and c.get("rho_spearman")]
        print("  %5d | %3s | %6s | %11s | %6s | %10s | %4s | %12s | %s" % (
            w, "si" if w in ok else ("no" if r else "-"), it(eb), it(en1),
            it(None if eb is None else eb - en1), it(e13), it(ed0),
            it(None if e13 is None else e13 - ed0) + amm13, it(num(rh[0]) if rh else None, 4)))
    print()
    print("PER CANALE: rapporto stimato/vero mediano sui mondi ammissibili (D13b) e su tutti (N1 a 1 nodo)")
    n1c = leggi(os.path.join(a.repo, "griglia_N1", "griglia_N1_k01_canali.csv"))

    def rapporti(righe_c, mondi):
        out = {}
        for c in righe_c:
            if int(c["seed_mondo"]) in mondi and num(c.get("roi_vero")) and num(c.get("roi_stimato")) is not None:
                out.setdefault(c["canale"], []).append(Fraction(str(c["roi_stimato"])) / Fraction(str(c["roi_vero"])))
        return {k: mediana(v) for k, v in out.items()}
    rb, rn = rapporti(canali, set(ok)), rapporti(n1c, set(MONDI))
    for k in sorted(rn, key=lambda c: -rn[c]):
        print("  %-16s D13b %6s | N1 a 1 nodo %6s" % (k, it(rb.get(k), 2, False), it(rn[k], 2, False)))
    print()
    print("RUN NON AMMISSIBILI (riportati col loro numero, mai rifatti)")
    na = [w for w in tutti if w not in ok]
    for w in na:
        r = tutti[w]
        print("  mondo %d: R-hat %s / %s, ESS %s / %s" % (w, r.get("rhat_roi_m"), r.get("rhat_beta_m"),
                                                          r.get("ess_roi_m"), r.get("ess_beta_m")))
    if not na:
        print("  nessuno")
    mancanti = [w for w in MONDI if w not in tutti]
    if mancanti:
        print("MONDI SENZA RIGA OK: " + ", ".join(map(str, mancanti)))
    print()
    print("ORE DEI RUN (colonna quando di _verifiche.csv, in UTC)")
    for nome in (CSV_REPLICA, CSV_LIVELLO):
        q = [r.get("quando", "") for r in leggi(os.path.join(a.cartella, nome.replace(".csv", "_verifiche.csv")))]
        q = [x for x in q if x]
        print("  " + nome + ": " + (q[0] + " -> " + q[-1] + " (" + str(len(q)) + " righe)" if q else "nessuna"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
