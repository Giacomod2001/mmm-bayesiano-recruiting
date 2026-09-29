"""R1 - PASSO 0: i quattro controlli sui draw, prima di qualunque altra cosa.

I draw compressi (`griglia/griglia_D*_draw/*.csv.gz` e
`griglia_D10/griglia_D10_calendario_4giri_draw/*.csv.gz`) sono l'unico
ingrediente nuovo di R1. Prima di usarli si verifica che siano quello che
pensiamo:

  a. la mediana per colonna riproduce la colonna `mediana` del corrispondente
     `griglia_D*_canali.csv` per quel mondo, alla quarta cifra significativa
  b. il 5o e il 95o percentile riproducono `ci05` e `ci95` alla quarta cifra
  c. la colonna `totale` coincide con la somma dei sette canali DENTRO ogni draw
  d. 8.000 righe per file, nessun NaN, nessun valore negativo

Questo e' un controllo di INPUT: la mediana e i percentili devono riprodurre
CSV gia' pubblicati, quindi non rivela nulla sulle strategie e puo' precedere
la pre-registrazione. Se un controllo fallisce ci si ferma e si scrive cosa
contengono davvero i file.

    python riallocazione_R1/controllo_draw_R1.py
"""
from __future__ import annotations

import gzip
import os
import sys

import numpy as np
import pandas as pd

QUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(QUI)

# Gli otto casi di D11, negli stessi termini: (etichetta, cartella dei draw,
# nome del run, csv per canale). Sei mondi distinti: il 103 compare tre volte.
CASI = [
    ("D1/101", "griglia/griglia_D1_geo_draw", "D1_geo_m0101",
     "griglia/griglia_D1_geo_canali.csv"),
    ("D1/103", "griglia/griglia_D1_geo_draw", "D1_geo_m0103",
     "griglia/griglia_D1_geo_canali.csv"),
    ("D1/105", "griglia/griglia_D1_geo_draw", "D1_geo_m0105",
     "griglia/griglia_D1_geo_canali.csv"),
    ("D1/107", "griglia/griglia_D1_geo_draw", "D1_geo_m0107",
     "griglia/griglia_D1_geo_canali.csv"),
    ("D2/102", "griglia/griglia_D2_calendario_draw", "D2_cal_rot2_m0102",
     "griglia/griglia_D2_calendario_canali.csv"),
    ("D2/103", "griglia/griglia_D2_calendario_draw", "D2_cal_rot3_m0103",
     "griglia/griglia_D2_calendario_canali.csv"),
    ("D10/42", "griglia_D10/griglia_D10_calendario_4giri_draw", "D10_cal4_rot0_m0042",
     "griglia_D10/griglia_D10_calendario_4giri_canali.csv"),
    ("D10/103", "griglia_D10/griglia_D10_calendario_4giri_draw", "D10_cal4_rot3_m0103",
     "griglia_D10/griglia_D10_calendario_4giri_canali.csv"),
]

N_DRAW_ATTESI = 8000
CIFRE = 4          # quarta cifra significativa


def sig(x, cifre=CIFRE):
    """Arrotonda alla `cifre`-esima cifra significativa."""
    if x == 0 or not np.isfinite(x):
        return x
    from math import floor, log10
    return round(x, -int(floor(log10(abs(x)))) + (cifre - 1))


def scarto_rel(a, b):
    return abs(a - b) / abs(b) if b else (0.0 if a == b else float("inf"))


def virgola(x, dec=4):
    return format(x, "." + str(dec) + "f").replace(".", ",")


def main() -> int:
    print("=" * 96)
    print("R1 - PASSO 0: i quattro controlli sui draw")
    print("=" * 96)
    print()
    righe, tutto_ok = [], True

    for etichetta, cartella, nome, csv_canali in CASI:
        percorso = os.path.join(ROOT, cartella, nome + "_draw.csv.gz")
        if not os.path.exists(percorso):
            print("%-9s FILE ASSENTE: %s" % (etichetta, percorso))
            tutto_ok = False
            continue
        with gzip.open(percorso, "rt", encoding="utf-8") as f:
            d = pd.read_csv(f)
        canali = [c for c in d.columns if c != "totale"]

        # --- d. forma, NaN, negativi ------------------------------------
        n = len(d)
        nan = int(d.isna().sum().sum())
        neg = int((d[canali] < 0).sum().sum())
        ok_d = (n == N_DRAW_ATTESI and nan == 0 and neg == 0 and len(canali) == 7)

        # --- c. totale = somma dentro il draw ---------------------------
        # Il confronto e' RELATIVO, non in euro, e il motivo e' un fatto sui
        # file che va dichiarato: i draw arrivano da TensorFlow in FLOAT32.
        # Su totali dell'ordine di 10^7 EUR il float32 ha una risoluzione di
        # circa un euro (eps = 1,19e-07), e i valori con sette cifre sono
        # scritti senza decimali proprio per questo. La colonna `totale` e'
        # stata calcolata sommando i valori NON arrotondati e poi arrotondata;
        # le colonne per canale sono arrotondate al centesimo una per una.
        # Lo scarto fra le due strade e' quindi rappresentazione, non
        # contenuto. Il limite NON e' un numero tondo scelto guardando il
        # risultato: e' derivato dalle due sorgenti, prima di leggerlo.
        #   arrotondamento: 7 canali al centesimo          -> 7 x 0,005 = 0,035 EUR
        #   float32: 7 valori sommati in float32, piu' la
        #            rappresentazione del totale stesso     -> ~5 x eps x |totale|
        # limite(draw) = 0,035 + 5 x eps x |totale|, cioe' 5,96e-07 relativo
        # sugli ordini di grandezza di questi file. La prima stesura di questo
        # controllo usava 1e-06, scelto DOPO aver visto 2,06e-07: era una
        # soglia tarata sul dato, ed e' stata sostituita da questa, che e'
        # piu' stretta e non guarda i dati. La pre-registrazione lo dichiara.
        EPS32 = float(np.finfo(np.float32).eps)
        somma = d[canali].to_numpy(dtype=np.float64).sum(axis=1)
        tot = d["totale"].to_numpy(dtype=np.float64)
        limite = 0.035 + 5.0 * EPS32 * np.abs(tot)
        scarto_c = float(np.max(np.abs(somma - tot)))
        rel_c = float(np.max(np.abs(somma - tot) / np.maximum(np.abs(tot), 1e-9)))
        quota_centesimi = float(np.mean(np.abs(somma - tot) <= 0.035))
        oltre = int(np.sum(np.abs(somma - tot) > limite))
        ok_c = (oltre == 0)

        # --- a, b. mediana e percentili contro il CSV per canale --------
        ca = pd.read_csv(os.path.join(ROOT, csv_canali))
        ca = ca[ca["mondo"] == nome]
        if len(ca) != 7:
            print("%-9s il CSV per canale ha %d righe per %s invece di 7"
                  % (etichetta, len(ca), nome))
            tutto_ok = False
            continue
        peggio_a = peggio_b = 0.0
        dett = []
        for _, r in ca.iterrows():
            ch = r["canale"]
            s = d[ch].to_numpy()
            med = float(np.median(s))
            lo, hi = (float(x) for x in np.quantile(s, [0.05, 0.95]))
            for calcolato, atteso, quale in ((med, float(r["mediana"]), "mediana"),
                                             (lo, float(r["ci05"]), "ci05"),
                                             (hi, float(r["ci95"]), "ci95")):
                uguale = sig(calcolato) == sig(atteso)
                rel = scarto_rel(calcolato, atteso)
                if quale == "mediana":
                    peggio_a = max(peggio_a, rel)
                else:
                    peggio_b = max(peggio_b, rel)
                if not uguale:
                    dett.append("%s %s: draw %.4g vs csv %.4g (scarto rel %.2e)"
                                % (ch, quale, calcolato, atteso, rel))
        ok_a = all("mediana" not in x for x in dett)
        ok_b = all(("ci05" not in x and "ci95" not in x) for x in dett)

        ok = ok_a and ok_b and ok_c and ok_d
        tutto_ok = tutto_ok and ok
        righe.append(dict(caso=etichetta, run=nome, righe=n, canali=len(canali),
                          nan=nan, negativi=neg,
                          scarto_max_totale_eur=round(scarto_c, 4),
                          scarto_rel_totale=rel_c,
                          quota_draw_entro_il_centesimo=round(quota_centesimi, 4),
                          draw_oltre_il_limite_derivato=oltre,
                          scarto_rel_mediana=peggio_a, scarto_rel_percentili=peggio_b,
                          a=ok_a, b=ok_b, c=ok_c, d=ok_d))
        print("%-9s %-20s righe %d  canali %d  NaN %d  negativi %d" %
              (etichetta, nome, n, len(canali), nan, neg))
        print("          a) mediana   4 cifre: %s   (scarto relativo massimo %.2e)"
              % ("ok" if ok_a else "FALLITO", peggio_a))
        print("          b) ci05/ci95 4 cifre: %s   (scarto relativo massimo %.2e)"
              % ("ok" if ok_b else "FALLITO", peggio_b))
        print("          c) totale = somma dentro il draw: %s  (%d draw su %d oltre il "
              "limite derivato 0,035 + 5 eps |tot|; scarto relativo massimo %.2e = %.2f eps)"
              % ("ok" if ok_c else "FALLITO", oltre, n, rel_c,
                 rel_c / float(np.finfo(np.float32).eps)))
        print("          d) 8.000 righe, niente NaN, niente negativi: %s"
              % ("ok" if ok_d else "FALLITO"))
        for x in dett[:6]:
            print("             ! " + x)
        print()

    df = pd.DataFrame(righe)
    df.to_csv(os.path.join(QUI, "R1_controllo_draw.csv"), index=False)
    print("=" * 96)
    for lettera, colonna, testo in (("a", "a", "mediana per colonna = CSV per canale, 4 cifre"),
                                    ("b", "b", "ci05 e ci95 = CSV per canale, 4 cifre"),
                                    ("c", "c", "totale = somma dei sette canali dentro il draw"),
                                    ("d", "d", "8.000 righe, nessun NaN, nessun negativo")):
        print("CONTROLLO (%s) %-52s %s (%d casi su %d)"
              % (lettera, testo, "PASSATO" if df[colonna].all() else "FALLITO",
                 int(df[colonna].sum()), len(df)))
    print()
    print("scarto relativo massimo su tutte le mediane   : %.2e" % df["scarto_rel_mediana"].max())
    print("scarto relativo massimo su tutti i percentili : %.2e" % df["scarto_rel_percentili"].max())
    print("scarto relativo massimo fra totale e somma    : %.2e  (eps di float32 %.2e, "
          "cioe' %.2f eps)" % (df["scarto_rel_totale"].max(), float(np.finfo(np.float32).eps),
                               df["scarto_rel_totale"].max() / float(np.finfo(np.float32).eps)))
    print("draw oltre il limite derivato 0,035 + 5 eps |tot|: %d su %d"
          % (int(df["draw_oltre_il_limite_derivato"].sum()), int(df["righe"].sum())))
    print("   in euro, al peggio: %s su totali dell'ordine di 10^7"
          % virgola(df["scarto_max_totale_eur"].max(), 2))
    print("   quota di draw il cui scarto sta dentro l'arrotondamento al centesimo: %s"
          % virgola(df["quota_draw_entro_il_centesimo"].mean(), 4))
    print()
    print("FATTO SUI FILE, DA PORTARE NELLA PRE-REGISTRAZIONE: i draw sono in FLOAT32.")
    print("   La colonna `totale` e' la somma dei valori non arrotondati, le colonne per")
    print("   canale sono arrotondate al centesimo una per una: lo scarto fra le due")
    print("   strade e' rappresentazione, non contenuto. Ogni conto di R1 legge i draw e")
    print("   li converte in float64 PRIMA di sommare o mediare 8.000 valori.")
    print()
    print("ESITO DEL PASSO 0:", "PASSATO - si puo' scrivere la pre-registrazione"
          if tutto_ok else "FALLITO - ci si ferma qui")
    print("scritto " + os.path.join(QUI, "R1_controllo_draw.csv"))
    return 0 if tutto_ok else 1


if __name__ == "__main__":
    sys.exit(main())
