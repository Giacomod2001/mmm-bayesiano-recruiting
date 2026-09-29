# -*- coding: utf-8 -*-
"""Proposta di budget con probabilita': l'artefatto per il decisore.

Non produce UNA ripartizione ottima. Produce, per ogni canale, la probabilita'
che meriti piu' budget - calcolata DENTRO i draw del posterior - e una mossa
solo dove quella probabilita' supera la soglia dichiarata.

    python proposta_budget.py <draw.csv.gz> <canali.csv> <seed_mondo>

Regola (soglia fissata a priori, non tarata sui risultati):
    P >= 90%  -> ALZA      P <= 10%  -> TAGLIA      altrimenti -> NON TOCCARE

Il cancello valida il VERSO della mossa, non la sua taglia: il passo e' quindi
uniforme e dichiarato, non scalato con P. La spesa totale resta costante.

PRECONDIZIONE: vale solo a valle di un esperimento (calendario a rotazione o
geo). Sul regime osservativo la stessa regola sbaglia il 61% delle volte, e
spara quattro volte piu' spesso: se si pronuncia su quasi tutti i canali, il
segnale non e' abbondanza di evidenza ma il regime sbagliato.
"""
import csv, gzip, sys

SOGLIA_ALZA, SOGLIA_TAGLIA = 90.0, 10.0
PASSO_PCT = 15.0   # passo UNIFORME per ogni mossa validata, in percentuale
                   # della spesa attuale del canale. Uniforme e non scalato con
                   # P perche' il cancello valida il VERSO, non la TAGLIA: una
                   # mossa piu' grande dove P e' piu' alta sarebbe un numero
                   # inventato con l'aria di essere misurato. La taglia giusta
                   # la dara' la macchina marginale (rifit + ottimizzazione
                   # dentro i draw); finche' non c'e', il passo resta fisso e
                   # dichiarato.


def probabilita(draw_path, spesa):
    """P(il canale rende piu' della media di portafoglio), dentro ogni draw."""
    with gzip.open(draw_path, "rt", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        canali = [c for c in r.fieldnames if c != "totale"]
        totale_spesa = sum(spesa[c] for c in canali)
        n = 0
        sopra = {c: 0 for c in canali}
        for riga in r:
            n += 1
            roi_portafoglio = float(riga["totale"]) / totale_spesa
            for c in canali:
                if float(riga[c]) / spesa[c] > roi_portafoglio:
                    sopra[c] += 1
    return {c: sopra[c] / n * 100.0 for c in canali}, n


def proposta(P, spesa):
    """Dalla probabilita' alla mossa, A SPESA TOTALE COSTANTE e A PASSO FISSO.

    Due vincoli, e nessuno dei due e' una preferenza.

    1. Il TOTALE non si tocca: e' la grandezza che il modello sbaglia di circa
       otto punti percentuali di quota e che nessun disegno sperimentale provato
       corregge (D10 lo misura). Una proposta che alza la spesa complessiva
       userebbe proprio il numero inaffidabile.

    2. Il PASSO e' uniforme: il cancello 90/10 valida il verso della mossa, non
       la sua ampiezza. Far crescere la mossa con P produrrebbe una cifra
       inventata travestita da misura.

    Il bilanciamento: si alza solo con i soldi che i tagli liberano. Se un lato
    chiede piu' dell'altro, si scala quello piu' grande - non e' una scelta, e'
    l'unico modo di far quadrare due lati di taglia diversa. Se manca un lato,
    non si muove niente: dire chi merita di piu' non dice a spese di chi.
    """
    desiderio = {c: ("ALZA" if p >= SOGLIA_ALZA else "TAGLIA")
                 for c, p in P.items() if p >= SOGLIA_ALZA or p <= SOGLIA_TAGLIA}

    su = sum(spesa[c] * PASSO_PCT / 100 for c, v in desiderio.items() if v == "ALZA")
    giu = sum(spesa[c] * PASSO_PCT / 100 for c, v in desiderio.items() if v == "TAGLIA")
    scambio = min(su, giu)
    k_su = scambio / su if su > 0 else 0.0
    k_giu = scambio / giu if giu > 0 else 0.0

    fuori = []
    for c in sorted(P, key=lambda k: -P[k]):
        if c not in desiderio:
            fuori.append((c, P[c], "non toccare", 0.0, spesa[c], 0.0))
            continue
        verso = desiderio[c]
        k = k_su if verso == "ALZA" else k_giu
        eff = (PASSO_PCT if verso == "ALZA" else -PASSO_PCT) * k
        nota = (PASSO_PCT if verso == "ALZA" else -PASSO_PCT) if abs(abs(eff) - PASSO_PCT) > 1e-9 else 0.0
        fuori.append((c, P[c], verso if eff else "congelato", eff, spesa[c] * (1 + eff / 100), nota))
    return fuori, scambio


def main(draw_path, canali_path, seed):
    spesa, vero = {}, {}
    for x in csv.DictReader(open(canali_path, newline="", encoding="utf-8")):
        if x["seed_mondo"] != str(seed):
            continue
        spesa[x["canale"]] = float(x["spesa"])
        vero[x["canale"]] = float(x["roi_vero"])
    if not spesa:
        raise SystemExit("nessun canale per seed_mondo=%s" % seed)

    P, n_draw = probabilita(draw_path, spesa)
    righe, scambio = proposta(P, spesa)
    eur = lambda v: "{:,.0f}".format(v).replace(",", ".")

    print("PROPOSTA DI BUDGET  -  mondo %s, %d draw del posterior" % (seed, n_draw))
    print("Soglia: alza >= %.0f%%, taglia <= %.0f%%. Passo uniforme %.0f%%, "
          "spesa totale costante.\n" % (SOGLIA_ALZA, SOGLIA_TAGLIA, PASSO_PCT))
    print("%-18s %8s  %-12s %8s  %14s  %14s"
          % ("canale", "P(+)", "decisione", "var.", "spesa attuale", "spesa proposta"))
    print("-" * 82)
    mosse, scalate = 0, []
    for c, p, dec, delta, nuova, nota in righe:
        if dec in ("ALZA", "TAGLIA"):
            mosse += 1
            if nota:
                scalate.append((c, nota, delta))
        print("%-18s %7.1f%%  %-12s %7s  %14s  %14s"
              % (c, p, dec, ("%+.0f%%" % delta) if delta else "-",
                 eur(spesa[c]), eur(nuova)))
    print("-" * 82)
    tot_a, tot_n = sum(spesa.values()), sum(r[4] for r in righe)
    print("%-18s %8s  %-12s %7s  %14s  %14s"
          % ("TOTALE", "", "%d mosse su %d" % (mosse, len(righe)), "",
             eur(tot_a), eur(tot_n)))
    print("spesa totale invariata: %s    budget spostato: %s"
          % ("si" if abs(tot_n - tot_a) < 1.0 else "NO", eur(scambio)))
    for c, voluto, ottenuto in scalate:
        print("  nota: %s al passo pieno sarebbe %+.0f%%, scalato a %+.1f%% per far"
              " quadrare il totale" % (c, voluto, ottenuto))

    congelati = [c for c, p, d, _, _, _ in righe if d == "congelato"]
    if mosse == 0 and congelati:
        print("\nNessuna mossa. L'evidenza indica %s, ma manca il lato opposto che la"
              % ", ".join(congelati))
        print("finanzi: dire chi merita di piu' non dice a spese di chi. Si dichiara e")
        print("non si muove.")
    elif mosse == 0:
        print("\nNessuna mossa difendibile: i dati non giustificano di spostare budget.")
    if mosse > len(righe) * 0.35:
        print("\nATTENZIONE: la regola si pronuncia su %d canali su %d. Sotto esperimento"
              % (mosse, len(righe)))
        print("            ce ne si aspetta 1 o 2. Verificare di non essere in regime")
        print("            osservativo, dove questa regola sbaglia il 61%% delle volte.")

    print("\n--- verifica contro la verita' (possibile solo sul simulato) ---")
    roi_p = sum(vero[c] * spesa[c] for c in spesa) / sum(spesa.values())
    verificate = 0
    for c, p, dec, delta, _, _ in righe:
        if dec not in ("ALZA", "TAGLIA"):
            continue
        verificate += 1
        giusta = (vero[c] > roi_p) == (dec == "ALZA")
        print("  %-18s %-7s  ROI vero %.2f vs portafoglio %.2f  ->  %s"
              % (c, dec, vero[c], roi_p, "GIUSTA" if giusta else "SBAGLIATA"))
    if not verificate:
        print("  nessuna mossa da verificare")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
