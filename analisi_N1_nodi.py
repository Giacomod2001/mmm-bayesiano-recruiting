"""Legge i CSV prodotti dal notebook N1 (cartella `MMM_griglia_N1` scaricata da
Drive) e quelli di D0 nel repository, e STAMPA I RAMI di N1 in prima riga:
il ramo del livello e il ramo dell'ordine, con la previsione confermata o
smentita. Poi il cancello di replica e tutto quello che il paragrafo 6 della
pre-registrazione chiede di riportare.

    python analisi_N1_nodi.py <cartella MMM_griglia_N1> [--repo <clone>] [--json out.json]

Committato INSIEME a preregistrazioni/PREREGISTRAZIONE_N1_nodi.md, prima di
qualunque fit: e' la regola scritta in codice. Soglie e rami sono quelli della
pre-registrazione del 22 settembre 2026 e non si toccano:

  cancello  la replica (12 nodi/trim., mondo 42) = riga di D0 del mondo 42
            alla quarta cifra, altrimenti nessun ramo
  livello   dE_w = E_w(1 nodo/trim.) - E_w(D0), sugli N mondi ammissibili
            0: N < 5 -> NON LEGGIBILE
            1: mediana >= +5,0 e dE > 0 in >= soglia(N) mondi -> MENO NODI, PIU' SOVRASTIMA
            2: mediana <= -5,0 e dE < 0 in >= soglia(N) mondi -> MENO NODI, MENO SOVRASTIMA
            3: altrimenti -> IL LIVELLO NON DIPENDE IN MODO NETTO DAI NODI
  ordine    mediana di rho al livello 1, sugli N mondi ammissibili
            0: N < 5 -> NON LEGGIBILE
            A: mediana >= 17/28 (+0,6071, "spesa inversa" ricalcolata da D0)
            B: mediana >  13/56 (+0,2321, q90 del nullo di M0)
            C: altrimenti
  soglia(N) = 6 se N = 8, altrimenti int(6/8 * N + 0,5)

Aritmetica esatta: E in centesimi interi (le colonne hanno due decimali), rho
in 28esimi interi (sette canali senza pari merito), mediane in 56esimi.
Solo libreria standard.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from fractions import Fraction

MONDI = [42, 101, 102, 103, 104, 105, 106, 107]
LIVELLI = [1, 3, 6]                      # nuovi; il 12 e' D0, dal file
NODI = {1: 8, 3: 24, 6: 48, 12: 96}
CSV_LIVELLO = {1: "griglia_N1_k01.csv", 3: "griglia_N1_k03.csv", 6: "griglia_N1_k06.csv"}
CSV_REPLICA = "griglia_N1_replica_k12.csv"
NOME_REPLICA = "N1_k12_replica_m0042"
D0_CSV = os.path.join("griglia", "griglia_D0_osservativo.csv")
D0_CANALI = os.path.join("griglia", "griglia_D0_osservativo_canali.csv")

SOGLIA_E_CENT = 500                      # +/-5,0 punti, in centesimi
RIF_SPESA_INVERSA = Fraction(17, 28)     # +0,6071, ricalcolato il 22/9 da D0
RIF_CASO = Fraction(13, 56)              # +0,2321, q90 del nullo di M0
N_MIN = 5
PREVISIONE = {"livello": "1", "ordine": "C"}

TESTO_LIVELLO = {
    "0": "NON LEGGIBILE: troppi pochi mondi ammissibili",
    "1": "MENO NODI, PIU' SOVRASTIMA",
    "2": "MENO NODI, MENO SOVRASTIMA",
    "3": "IL LIVELLO NON DIPENDE IN MODO NETTO DAI NODI",
}
TESTO_ORDINE = {
    "0": "NON LEGGIBILE: troppi pochi mondi ammissibili",
    "A": "CON LA BASELINE RIGIDA MERIDIAN ORDINA ALMENO COME LA REGOLA EMPIRICA",
    "B": "MEGLIO DEL CASO, NON MEGLIO DELLA REGOLA EMPIRICA",
    "C": "ANCHE CON LA BASELINE RIGIDA L'ORDINE NON SI DISTINGUE DAL CASO",
}

# attesi del cancello: riga del mondo 42 di griglia/griglia_D0_osservativo.csv
# (confronto come la regola identico_osservativo del notebook)
CANCELLO = [("rapporto_mediana", 4), ("pit", 6), ("rapporto_ci05", 4),
            ("rapporto_ci95", 4), ("dentro", 0), ("n_knots", 0)]


def numero_run():
    """n come nel paragrafo 2 della pre-registrazione."""
    n = {NOME_REPLICA: 1}
    i = 2
    for k in LIVELLI:
        for m in MONDI:
            n[nome_run(k, m)] = i
            i += 1
    return n


def nome_run(k, m):
    return "N1_k%02d_m%04d" % (k, m)


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


def it(x, dec=2, segno=True):
    if x is None:
        return "n/d"
    s = format(float(x), ("+" if segno else "") + "." + str(dec) + "f")
    return s.replace(".", ",").replace("-", "−")


def ammissibile(r):
    """Sezione 4.7: R-hat <= 1,1 ed ESS >= 100 su roi_m e beta_m."""
    for campo, soglia, verso in (("rhat_roi_m", 1.1, "max"), ("rhat_beta_m", 1.1, "max"),
                                 ("ess_roi_m", 100.0, "min"), ("ess_beta_m", 100.0, "min")):
        v = num(r.get(campo))
        if v is None:
            return False
        if verso == "max" and v > soglia + 1e-9:
            return False
        if verso == "min" and v < soglia:
            return False
    return True


def centesimi(x):
    """Valore a due decimali del CSV -> intero in centesimi, esatto."""
    return int(round(float(x) * 100))


def e_cent(r):
    s, v = r.get("quota_media_stimata_pct"), r.get("quota_media_vera_pct")
    if num(s) is None or num(v) is None:
        return None
    return centesimi(s) - centesimi(v)


def rango(valori):
    """Ranghi con media sui pari merito (come Spearman)."""
    ordine = sorted(range(len(valori)), key=lambda i: valori[i])
    r = [0.0] * len(valori)
    i = 0
    while i < len(ordine):
        j = i
        while j + 1 < len(ordine) and valori[ordine[j + 1]] == valori[ordine[i]]:
            j += 1
        for t in range(i, j + 1):
            r[ordine[t]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = rango(a), rango(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra)
    vb = sum((y - mb) ** 2 for y in rb)
    return cov / (va * vb) ** 0.5


def rho_esatto(rho):
    """rho di sette canali senza pari merito = k/28 esatto. Se 28*rho non e'
    intero entro 0,01 (pari merito) si tiene il float, e lo si dichiara."""
    k = round(28 * rho)
    if abs(28 * rho - k) <= 0.01:
        return Fraction(k, 28), False
    return Fraction(rho).limit_denominator(10 ** 9), True


def mediana_frazioni(v):
    s = sorted(v)
    n = len(s)
    if n == 0:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def mediana(v):
    v = [x for x in v if x is not None]
    if not v:
        return None
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def soglia(n):
    return 6 if n == 8 else int(6.0 / 8.0 * n + 0.5)


def riga_ok(righe, nome):
    """Come il notebook: l'ultima riga ok del run; se non ce n'e', l'ultima."""
    tutte = [r for r in righe if r.get("mondo") == nome]
    ok = [r for r in tutte if r.get("esito") == "ok"]
    return ok[-1] if ok else (tutte[-1] if tutte else None)


def canali_di(righe_canali, nome):
    t = [r for r in righe_canali if r.get("mondo") == nome]
    return t[-7:] if len(t) >= 7 else []


def uguale(ott, att, dec):
    a, b = num(ott), num(att)
    if a is None or b is None:
        return False
    return abs(round(a, dec) - round(b, dec)) <= 1e-9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cartella", help="cartella MMM_griglia_N1 scaricata da Drive")
    ap.add_argument("--repo", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    N_RUN = numero_run()

    # --- D0 = livello 12, dal file -------------------------------------------
    d0 = {int(r["seed_mondo"]): r for r in leggi(os.path.join(a.repo, D0_CSV))}
    d0c = leggi(os.path.join(a.repo, D0_CANALI))
    if sorted(d0) != MONDI:
        raise SystemExit("D0: mondi " + str(sorted(d0)) + " invece di " + str(MONDI))
    d0_canali = {m: [r for r in d0c if int(r["seed_mondo"]) == m] for m in MONDI}
    # il riferimento "spesa inversa" si ricalcola dal file e deve tornare 17/28:
    # se non torna, il file non e' quello su cui la pre-registrazione e' scritta
    si = []
    for m in MONDI:
        c = d0_canali[m]
        if len(c) != 7:
            raise SystemExit("D0 mondo " + str(m) + ": " + str(len(c)) + " righe canali")
        si.append(rho_esatto(spearman([-float(r["spesa"]) for r in c],
                                      [float(r["roi_vero"]) for r in c]))[0])
    if mediana_frazioni(si) != RIF_SPESA_INVERSA:
        raise SystemExit("riferimento spesa inversa ricalcolato = " + str(mediana_frazioni(si)) +
                         " invece di 17/28: D0 non e' il file della pre-registrazione")

    # --- il cancello di replica -------------------------------------------------
    rep_righe = leggi(os.path.join(a.cartella, CSV_REPLICA))
    rep = riga_ok(rep_righe, NOME_REPLICA)
    att = d0[42]
    diff = []
    if rep is None or rep.get("esito") != "ok":
        cancello = "1"
        diff.append("nessuna riga" if rep is None else "esito=" + str(rep.get("esito")) +
                    " (" + str(rep.get("errore"))[:160] + ")")
    else:
        for campo, dec in CANCELLO:
            if not uguale(rep.get(campo), att.get(campo), dec):
                diff.append(campo + "=" + str(rep.get(campo)) + " invece di " + str(att.get(campo)))
        if str(rep.get("impronta_input_data")) != str(att.get("impronta_input_data")):
            diff.append("impronta_input_data=" + str(rep.get("impronta_input_data")) +
                        " invece di " + str(att.get("impronta_input_data")))
        for campo, atteso in (("keep", 2000), ("n_chains", 4), ("adapt", 500), ("burnin", 500),
                              ("seed_mcmc", 42), ("revenue_per_kpi", 40.0), ("prior_sigma", 0.9),
                              ("decimali_stagionalita", 4), ("seed_mondo", 42)):
            v = num(rep.get(campo))
            if v is None or abs(v - atteso) > 1e-9:
                diff.append(campo + "=" + str(rep.get(campo)) + " invece di " + str(atteso))
        if not ammissibile(rep):
            diff.append("replica non ammissibile")
        cancello = "2" if not diff else "3"
    testo_cancello = {"1": "NESSUN NUMERO: la replica non ha una riga ok, nessun ramo",
                      "2": "REPLICA RIUSCITA",
                      "3": "CI SI FERMA: la replica non riproduce D0, nessun ramo"}[cancello]

    # --- i tre livelli --------------------------------------------------------
    liv = {}
    for k in LIVELLI:
        righe = leggi(os.path.join(a.cartella, CSV_LIVELLO[k]))
        canali = leggi(os.path.join(a.cartella, CSV_LIVELLO[k][:-4] + "_canali.csv"))
        liv[k] = {}
        for m in MONDI:
            nome = nome_run(k, m)
            r = riga_ok(righe, nome)
            rec = {"n": N_RUN[nome], "nome": nome, "riga": r, "ok": bool(r and r.get("esito") == "ok")}
            if rec["ok"]:
                rec["amm"] = ammissibile(r)
                rec["E"] = e_cent(r)
                c = canali_di(canali, nome)
                rec["rho_col"] = num(c[0].get("rho_spearman")) if c else None
                rec["rho"], rec["pari_merito"] = (rho_esatto(rec["rho_col"]) if rec["rho_col"] is not None
                                                  else (None, False))
                rec["dentro"] = str(r.get("dentro")) == "1"
                p = num(r.get("pit"))
                rec["dentro_pit"] = p is not None and 0.05 <= p <= 0.95
                rec["n_knots"] = num(r.get("n_knots"))
                rec["impronta"] = str(r.get("impronta_input_data"))
            liv[k][m] = rec
    # D0 nello stesso formato
    liv[12] = {}
    for m in MONDI:
        r = d0[m]
        c = d0_canali[m]
        rc = num(c[0]["rho_spearman"])
        rho, pm = rho_esatto(rc)
        liv[12][m] = {"n": "D0", "nome": r["mondo"], "riga": r, "ok": True, "amm": ammissibile(r),
                      "E": e_cent(r), "rho_col": rc, "rho": rho, "pari_merito": pm,
                      "dentro": str(r.get("dentro")) == "1",
                      "dentro_pit": 0.05 <= float(r["pit"]) <= 0.95,
                      "n_knots": num(r.get("n_knots")), "impronta": r["impronta_input_data"]}

    # --- le due regole ---------------------------------------------------------
    ramo_l, ramo_o, dett_l, dett_o = "-", "-", {}, {}
    if cancello == "2":
        base = [m for m in MONDI if liv[1][m]["ok"] and liv[1][m]["amm"] and liv[1][m]["E"] is not None]
        N = len(base)
        dE = {m: liv[1][m]["E"] - liv[12][m]["E"] for m in base}
        s = soglia(N) if N else 0
        pos = sum(1 for m in base if dE[m] > 0)
        neg = sum(1 for m in base if dE[m] < 0)
        med2 = None
        if N:
            v = sorted(dE.values())
            med2 = 2 * v[N // 2] if N % 2 else v[N // 2 - 1] + v[N // 2]   # 2 x mediana, centesimi
        if N < N_MIN:
            ramo_l = "0"
        elif med2 >= 2 * SOGLIA_E_CENT and pos >= s:
            ramo_l = "1"
        elif med2 <= -2 * SOGLIA_E_CENT and neg >= s:
            ramo_l = "2"
        else:
            ramo_l = "3"
        dett_l = {"N": N, "soglia": s, "positivi": pos, "negativi": neg,
                  "mediana_dE": None if med2 is None else med2 / 200.0,
                  "dE": {m: dE[m] / 100.0 for m in base}}
        base_o = [m for m in base if liv[1][m]["rho"] is not None]
        No = len(base_o)
        med_rho = mediana_frazioni([liv[1][m]["rho"] for m in base_o])
        if No < N_MIN:
            ramo_o = "0"
        elif med_rho >= RIF_SPESA_INVERSA:
            ramo_o = "A"
        elif med_rho > RIF_CASO:
            ramo_o = "B"
        else:
            ramo_o = "C"
        dett_o = {"N": No, "mediana_rho": None if med_rho is None else float(med_rho),
                  "M56": None if med_rho is None else float(med_rho * 56),
                  "pari_merito": [m for m in base_o if liv[1][m]["pari_merito"]]}

    # --- PRIMA RIGA: i rami ------------------------------------------------------
    if cancello == "2":
        print("N1 - LIVELLO: ramo " + ramo_l + " (" + TESTO_LIVELLO[ramo_l] + ") | ORDINE: ramo " +
              ramo_o + " (" + TESTO_ORDINE[ramo_o] + ")")
        def _esito(ramo, previsto, smentita):
            # par. 7.3: smentisce il ramo 2 (livello) o il ramo A (ordine); un altro
            # ramo diverso dal previsto la lascia NON CONFERMATA
            if ramo == "0":
                return "NON VALUTABILE (ramo 0)"
            if ramo == previsto:
                return "CONFERMATA"
            return "SMENTITA" if ramo == smentita else "NON CONFERMATA"
        print("previsione dichiarata (livello 1, ordine C): livello " +
              _esito(ramo_l, PREVISIONE["livello"], "2") + ", ordine " +
              _esito(ramo_o, PREVISIONE["ordine"], "A"))
    else:
        print("N1 - NESSUN RAMO: cancello di replica riga " + cancello + " (" + testo_cancello + ")")
        print("previsione dichiarata (livello 1, ordine C): non valutabile")
    print()

    # --- il cancello --------------------------------------------------------------
    print("CANCELLO DI REPLICA (n 1, " + NOME_REPLICA + "): riga " + cancello + " - " + testo_cancello)
    if rep is not None:
        print("  rapporto_mediana " + str(rep.get("rapporto_mediana")) + " (atteso " + att["rapporto_mediana"] +
              ") | pit " + str(rep.get("pit")) + " (atteso " + att["pit"] + ") | impronta " +
              str(rep.get("impronta_input_data")) + " (attesa " + att["impronta_input_data"] + ") | n_knots " +
              str(rep.get("n_knots")))
    for d in diff:
        print("  DIFFERENZA: " + d)
    # un fit dei livelli dopo un cancello non riuscito non e' ammesso (par. 9.8)
    fatti = [liv[k][m]["nome"] for k in LIVELLI for m in MONDI if liv[k][m]["riga"] is not None]
    if cancello != "2" and fatti:
        print("  ATTENZIONE: " + str(len(fatti)) + " run dei livelli presenti nonostante il cancello: " +
              ", ".join(fatti[:5]) + ("..." if len(fatti) > 5 else ""))
    print()
    if cancello != "2":
        _json(a.json, cancello, diff, "-", "-", {}, {}, liv, rep)
        sys.exit(2)

    # --- dettaglio delle regole ----------------------------------------------------
    print("REGOLA DEL LIVELLO: N = " + str(dett_l["N"]) + " mondi ammissibili al livello 1, soglia " +
          str(dett_l["soglia"]) + " | mediana dE " + it(dett_l["mediana_dE"], 3) + " punti | dE > 0 in " +
          str(dett_l["positivi"]) + ", < 0 in " + str(dett_l["negativi"]))
    print("  dE per mondo: " + ", ".join(str(m) + " " + it(v) for m, v in dett_l["dE"].items()))
    print("REGOLA DELL'ORDINE: N = " + str(dett_o["N"]) + " | mediana rho al livello 1 " +
          it(dett_o["mediana_rho"], 4) + " (" + ("%g" % dett_o["M56"] if dett_o["M56"] is not None else "n/d") +
          "/56) contro spesa inversa +0,6071 (34/56) e caso +0,2321 (13/56)" +
          (" | PARI MERITO, confronto in virgola mobile: " + str(dett_o["pari_merito"]) if dett_o["pari_merito"] else ""))
    print()

    # --- i quattro livelli -----------------------------------------------------------
    print("I QUATTRO LIVELLI (12 = D0, dal file)")
    print("  nodi/trim  nodi | amm/tot | E med amm | E med tutti | rho med amm | rho med tutti | C_tot amm | C_tot tutti")
    tab = {}
    for k in (1, 3, 6, 12):
        ok = [liv[k][m] for m in MONDI if liv[k][m]["ok"]]
        amm = [x for x in ok if x["amm"]]
        r = {"amm": len(amm), "tot": len(ok),
             "E_amm": mediana([x["E"] / 100.0 for x in amm if x["E"] is not None]),
             "E_tutti": mediana([x["E"] / 100.0 for x in ok if x["E"] is not None]),
             "rho_amm": mediana([float(x["rho"]) for x in amm if x["rho"] is not None]),
             "rho_tutti": mediana([float(x["rho"]) for x in ok if x["rho"] is not None]),
             "C_amm": sum(1 for x in amm if x["dentro"]), "C_tutti": sum(1 for x in ok if x["dentro"])}
        tab[k] = r
        print("  " + str(k).rjust(9) + "  " + str(NODI[k]).rjust(4) + " | " + (str(r["amm"]) + "/" + str(r["tot"])).rjust(7) +
              " | " + it(r["E_amm"], 3).rjust(9) + " | " + it(r["E_tutti"], 3).rjust(11) + " | " +
              it(r["rho_amm"], 4).rjust(11) + " | " + it(r["rho_tutti"], 4).rjust(13) + " | " +
              str(r["C_amm"]).rjust(9) + " | " + str(r["C_tutti"]).rjust(11))
    print("  riferimenti per rho: spesa inversa +0,6071 | caso +0,2321")
    print()

    print("MONDO PER MONDO (E in punti | rho | dentro)")
    for m in MONDI:
        pezzi = []
        for k in (1, 3, 6, 12):
            x = liv[k][m]
            if not x["ok"]:
                pezzi.append(str(k) + ": " + ("nessuna riga" if x["riga"] is None else "esito " + str(x["riga"].get("esito"))))
                continue
            pezzi.append(str(k) + ": " + it(x["E"] / 100.0) + " | " + it(float(x["rho"]) if x["rho"] is not None else None, 4) +
                         " | " + ("1" if x["dentro"] else "0") + ("" if x["amm"] else " NON AMM."))
        print("  " + str(m).rjust(3) + "  " + "  ||  ".join(pezzi))
    print()

    print("RUN NON AMMISSIBILI (riportati col loro numero, mai rifatti)")
    nonamm = [(x["n"], x["nome"], x["riga"]) for k in LIVELLI for m in MONDI for x in [liv[k][m]]
              if x["ok"] and not x["amm"]]
    for n, nome, r in nonamm:
        print("  n " + str(n) + " " + nome + ": rhat_roi_m " + str(r.get("rhat_roi_m")) + ", ess_roi_m " +
              str(r.get("ess_roi_m")) + ", rhat_beta_m " + str(r.get("rhat_beta_m")) + ", ess_beta_m " +
              str(r.get("ess_beta_m")) + ", divergenze " + str(r.get("divergenze")))
    if not nonamm:
        print("  nessuno")
    senza = [(x["n"], x["nome"], x["riga"]) for k in LIVELLI for m in MONDI for x in [liv[k][m]] if not x["ok"]]
    for n, nome, r in senza:
        print("  SENZA NUMERI: n " + str(n) + " " + nome + " (" +
              ("nessuna riga" if r is None else "esito " + str(r.get("esito")) + ": " + str(r.get("errore"))[:120]) + ")")
    print()

    print("CONTROLLI DI RIGA")
    for k in LIVELLI:
        for m in MONDI:
            x = liv[k][m]
            if not x["ok"]:
                continue
            p = []
            if x["n_knots"] is None or int(x["n_knots"]) != NODI[k]:
                p.append("n_knots " + str(x["n_knots"]) + " invece di " + str(NODI[k]))
            if x["impronta"] != liv[12][m]["impronta"]:
                p.append("impronta " + x["impronta"] + " invece di " + liv[12][m]["impronta"] + " di D0")
            if x["dentro"] != x["dentro_pit"]:
                p.append("dentro e pit in disaccordo")
            if p:
                print("  n " + str(x["n"]) + " " + x["nome"] + ": " + "; ".join(p))
    print("  (righe senza problemi non stampate)")
    print()

    print("MONOTONIA NEI NODI (E: E(1) >= E(3) >= E(6) >= E(12); rho: tutta crescente o tutta decrescente)")
    for m in MONDI + ["mediana"]:
        if m == "mediana":
            Ev = [tab[k]["E_amm"] for k in (1, 3, 6, 12)]
            rv = [tab[k]["rho_amm"] for k in (1, 3, 6, 12)]
        else:
            Ev = [liv[k][m]["E"] / 100.0 if liv[k][m]["ok"] and liv[k][m]["E"] is not None else None for k in (1, 3, 6, 12)]
            rv = [float(liv[k][m]["rho"]) if liv[k][m]["ok"] and liv[k][m]["rho"] is not None else None for k in (1, 3, 6, 12)]
        if None in Ev or None in rv:
            print("  " + str(m).rjust(7) + ": incompleto")
            continue
        e_mon = all(Ev[i] >= Ev[i + 1] for i in range(3))
        r_cre = all(rv[i] <= rv[i + 1] for i in range(3))
        r_dec = all(rv[i] >= rv[i + 1] for i in range(3))
        print("  " + str(m).rjust(7) + ": E " + " , ".join(it(v) for v in Ev) + (" MONOTONA" if e_mon else " NON monotona") +
              " | rho " + " , ".join(it(v, 4) for v in rv) +
              (" costante" if (r_cre and r_dec) else (" crescente nei nodi" if r_cre else
               (" decrescente nei nodi" if r_dec else " NON monotona"))))
    print()

    print("CONFRONTO CON LA SEZIONE 5.8.1 - mondo 42, l'andamento e non le cifre")
    print("  (A.2 bozza: 3 nodi/trim. 57,9% 3,13x; 6 nodi/trim. 47,6% 2,57x; 12 nodi/trim. 41,9% 2,26x;")
    print("   righe 1-2 con 1.000 campioni, in parte precedenti alla griglia)")
    for k in (1, 3, 6, 12):
        x = liv[k][42]
        if not x["ok"]:
            print("  " + str(k).rjust(2) + " nodi/trim.: nessun numero")
            continue
        r = x["riga"]
        qs, qv = num(r.get("quota_media_stimata_pct")), num(r.get("quota_media_vera_pct"))
        print("  " + str(k).rjust(2) + " nodi/trim.: quota stimata " + it(qs, 2, False) + "% | stimata/vera " +
              it(qs / qv, 2, False) + "x | rapporto_mediana " + str(r.get("rapporto_mediana")))
    print()

    print("ORE DEI RUN (colonna quando di _verifiche.csv)")
    for nomefile in [CSV_REPLICA] + [CSV_LIVELLO[k] for k in LIVELLI]:
        q = [r.get("quando") for r in leggi(os.path.join(a.cartella, nomefile[:-4] + "_verifiche.csv")) if r.get("quando")]
        print("  " + nomefile + ": " + (min(q) + " -> " + max(q) + " (" + str(len(q)) + " righe)" if q else "nessuna riga"))

    _json(a.json, cancello, diff, ramo_l, ramo_o, dett_l, dett_o, liv, rep, tab)


def _json(percorso, cancello, diff, ramo_l, ramo_o, dett_l, dett_o, liv, rep, tab=None):
    if not percorso:
        return
    out = {"cancello": cancello, "differenze_cancello": diff, "ramo_livello": ramo_l, "ramo_ordine": ramo_o,
           "regola_livello": dett_l, "regola_ordine": dett_o, "livelli": tab or {},
           "replica": rep or {}}
    with open(percorso, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
