"""D11 - il riparto controfattuale: la regola 90/10 fa guadagnare?

Esegue quanto pre-registrato in PREREGISTRAZIONE_D11_riparto_controfattuale.md (v2).
Per ognuno degli 8 casi genera il mondo BASE con il generatore ricostruito + G5 e
valuta cinque ripartizioni sulla superficie di risposta vera, a `beta` FISSO:

  (a) spesa attuale   (b) regola 90/10   (c) allocatore vecchio
  (d) 200 riparti casuali della stessa cifra   (e) oracolo sulla stessa classe di mosse

Metrica: contributo incrementale vero dei media, in candidature.
uso: python studio_D11.py
"""
import collections
import csv
import importlib.util
import json
import os
import sys

import numpy as np

QUI = os.path.dirname(os.path.abspath(__file__))
PK = os.path.join(QUI, "D11_pacchetto")
_s = importlib.util.spec_from_file_location("g5", os.path.join(QUI, "g5", "genera_dati_simulati.py"))
G = importlib.util.module_from_spec(_s); _s.loader.exec_module(G)
_p = importlib.util.spec_from_file_location("pb", os.path.join(PK, "proposta_budget.py"))
PB = importlib.util.module_from_spec(_p); _p.loader.exec_module(PB)

CASI = [
    ("D1", 101, "griglia/griglia_D1_geo_draw/D1_geo_m0101_draw.csv.gz", "griglia/griglia_D1_geo_canali.csv"),
    ("D1", 103, "griglia/griglia_D1_geo_draw/D1_geo_m0103_draw.csv.gz", "griglia/griglia_D1_geo_canali.csv"),
    ("D1", 105, "griglia/griglia_D1_geo_draw/D1_geo_m0105_draw.csv.gz", "griglia/griglia_D1_geo_canali.csv"),
    ("D1", 107, "griglia/griglia_D1_geo_draw/D1_geo_m0107_draw.csv.gz", "griglia/griglia_D1_geo_canali.csv"),
    ("D2", 102, "griglia/griglia_D2_calendario_draw/D2_cal_rot2_m0102_draw.csv.gz", "griglia/griglia_D2_calendario_canali.csv"),
    ("D2", 103, "griglia/griglia_D2_calendario_draw/D2_cal_rot3_m0103_draw.csv.gz", "griglia/griglia_D2_calendario_canali.csv"),
    ("D10", 42, "griglia_D10/griglia_D10_calendario_4giri_draw/D10_cal4_rot0_m0042_draw.csv.gz", "griglia_D10/griglia_D10_calendario_4giri_canali.csv"),
    ("D10", 103, "griglia_D10/griglia_D10_calendario_4giri_draw/D10_cal4_rot3_m0103_draw.csv.gz", "griglia_D10/griglia_D10_calendario_4giri_canali.csv"),
]
CASO_GIA_VISTO = ("D10", 42)          # dichiarato nella pre-registrazione, §5
N_CASUALI = 200
SEME_NULLO = 20260917
ALLOC_VECCHIO_SU = "Google Ads"
ALLOC_VECCHIO_GIU = ["Subito Lavoro", "Altre job board", "Jooble"]
ALLOC_VECCHIO_LIMITE = 30.0


def mondo(seed):
    """Il mondo BASE del seme: la superficie di risposta vera, pronta da valutare."""
    p = G.genera(seed=seed)
    canali = list(p["canali"])
    pop = p["pop"]
    curve = {}
    for ch in canali:
        c = G.CANALI[ch]
        a = G.adstock_geometrico(p["ch_impr"][ch] / pop[None, :], c["lam"])
        ec = c["ec_mult"] * float(np.mean(p["ch_impr"][ch].sum(axis=1)))
        # K(g) = beta x pop_g x mg_g: il fattore che resta FISSO quando si sposta budget
        K = p["beta"][ch] * (pop * p["beta_geo"][ch])
        curve[ch] = (a, ec, c["slope"], K)
    spesa = {ch: float(p["ch_spesa"][ch].sum()) for ch in canali}
    return canali, spesa, curve


def contributo(curve, canali, riparto=None):
    """Candidature incrementali vere totali sotto una ripartizione. beta FISSO."""
    tot = 0.0
    for ch in canali:
        a, ec, slope, K = curve[ch]
        k = 1.0 + (riparto or {}).get(ch, 0.0) / 100.0
        tot += float((K[None, :] * G.hill(k * a, ec, slope)).sum())
    return tot


def riparto_90_10(draw, can, seed):
    spesa = {x["canale"]: float(x["spesa"]) for x in
             csv.DictReader(open(os.path.join(PK, can), newline="", encoding="utf-8"))
             if x["seed_mondo"] == str(seed)}
    P, n = PB.probabilita(os.path.join(PK, draw), spesa)
    righe, scambio = PB.proposta(P, spesa)
    return ({c: d for c, p, dec, d, nu, no in righe if dec in ("ALZA", "TAGLIA")}, scambio, spesa)


def riparto_allocatore_vecchio(spesa):
    """§6.2: Google al massimo (+30%), i tre job board al minimo (-30%). Il +30% di
    Google chiede piu' di quanto i tagli liberino, quindi l'alzata si scala a cio'
    che i tagli liberano: stessa regola di bilancio di (b), spesa totale costante."""
    liberati = sum(spesa[c] * ALLOC_VECCHIO_LIMITE / 100.0 for c in ALLOC_VECCHIO_GIU)
    su_pieno = spesa[ALLOC_VECCHIO_SU] * ALLOC_VECCHIO_LIMITE / 100.0
    scambio = min(su_pieno, liberati)
    r = {c: -ALLOC_VECCHIO_LIMITE * (scambio / liberati) for c in ALLOC_VECCHIO_GIU}
    r[ALLOC_VECCHIO_SU] = ALLOC_VECCHIO_LIMITE * (scambio / su_pieno)
    return r, scambio


def coppie(canali):
    return [(i, j) for i in canali for j in canali if i != j]


def main():
    righe_out, dettaglio_nullo = [], {}
    print("D11 - riparto controfattuale. Contributo vero dei media, in candidature.")
    print("beta FISSO al mondo non modificato: si valuta la superficie di risposta vera.")
    print()
    for dis, seed, draw, can in CASI:
        canali, spesa, curve = mondo(seed)
        rip_b, eur_b, spesa_fit = riparto_90_10(draw, can, seed)
        scarto_b = sum(spesa[c] * d / 100.0 for c, d in rip_b.items())
        eur_b_mondo = sum(abs(spesa[c] * d / 100.0) for c, d in rip_b.items()) / 2.0
        Ya = contributo(curve, canali)
        Yb = contributo(curve, canali, rip_b)
        rip_c, eur_c_fit = riparto_allocatore_vecchio(spesa)
        Yc = contributo(curve, canali, rip_c)
        eur_c = sum(abs(spesa[c] * d / 100.0) for c, d in rip_c.items()) / 2.0
        # (d) controllo nullo: la stessa cifra fra due canali estratti a sorte
        rng = np.random.default_rng(SEME_NULLO + seed)
        tutte = coppie(canali)
        gd = []
        while len(gd) < N_CASUALI:
            su, giu = tutte[int(rng.integers(0, len(tutte)))]
            d_giu = -100.0 * eur_b_mondo / spesa[giu]
            if d_giu <= -100.0:
                continue
            gd.append(contributo(curve, canali, {su: 100.0 * eur_b_mondo / spesa[su], giu: d_giu}) - Ya)
        gd = np.array(sorted(gd))
        # (e) oracolo: la migliore della stessa classe, stessa cifra
        migliore, ge = None, -np.inf
        for su, giu in tutte:
            d_giu = -100.0 * eur_b_mondo / spesa[giu]
            if d_giu <= -100.0:
                continue
            g = contributo(curve, canali, {su: 100.0 * eur_b_mondo / spesa[su], giu: d_giu}) - Ya
            if g > ge:
                ge, migliore = g, (su, giu)
        gb, gc = Yb - Ya, Yc - Ya
        p_b = float((gd < gb).mean())
        f_b = gb / ge if ge > 0 else float("nan")
        righe_out.append(dict(
            disegno=dis, mondo=seed, gia_visto=int((dis, seed) == CASO_GIA_VISTO),
            riparto_b=";".join(c + "=" + format(d, "+.6f") for c, d in rip_b.items()),
            euro_mossi_b=round(eur_b_mondo, 2), scarto_somma_b_eur=round(scarto_b, 4),
            Y_a=round(Ya, 3), Y_b=round(Yb, 3), Y_c=round(Yc, 3),
            g_b=round(gb, 3), g_b_pct=round(100 * gb / Ya, 5),
            g_c=round(gc, 3), g_c_pct=round(100 * gc / Ya, 5),
            g_b_per_euro=round(gb * 40.0 / eur_b_mondo, 5),
            g_c_per_euro=round(gc * 40.0 / eur_c, 5), euro_mossi_c=round(eur_c, 2),
            g_d_mediana=round(float(np.median(gd)), 3),
            g_d_p90=round(float(np.quantile(gd, 0.90)), 3),
            g_d_min=round(float(gd.min()), 3), g_d_max=round(float(gd.max()), 3),
            g_d_frazione_positive=round(float((gd > 0).mean()), 4),
            g_e=round(ge, 3), g_e_pct=round(100 * ge / Ya, 5),
            oracolo=migliore[0] + " <- " + migliore[1],
            p_b=round(p_b, 4), f_b=round(f_b, 4)))
        dettaglio_nullo[dis + "_" + str(seed)] = gd.tolist()
        print(("[" + dis + " mondo " + str(seed) + "]").ljust(22) +
              "g_b " + format(gb, "+9.1f") + " (" + format(100 * gb / Ya, "+.3f") + "%)" +
              " | nullo mediana " + format(float(np.median(gd)), "+8.1f") +
              " p90 " + format(float(np.quantile(gd, 0.90)), "+8.1f") +
              " | oracolo " + format(ge, "+8.1f") +
              " | p_b " + format(p_b, ".3f") + " f_b " + format(f_b, ".3f"))
    with open(os.path.join(QUI, "D11_risultati.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(righe_out[0])); w.writeheader(); w.writerows(righe_out)
    json.dump(dettaglio_nullo, open(os.path.join(QUI, "D11_controllo_nullo.json"), "w"))
    # --- i conteggi pre-registrati
    def conta(ins):
        V = sum(1 for r in ins if r["g_b"] > 0)
        S = sum(1 for r in ins if r["p_b"] >= 0.90)
        W = sum(1 for r in ins if r["g_b_per_euro"] > r["g_c_per_euro"])
        return V, S, W
    tutti = righe_out
    non_visti = [r for r in righe_out if not r["gia_visto"]]
    print()
    for et, ins in (("tutti e 8 i casi", tutti), ("i 7 non visti", non_visti)):
        V, S, W = conta(ins)
        N = len(ins)
        soglia = 6 if N == 8 else int(6.0 / 8.0 * N + 0.5)
        print(et.ljust(20) + "N=" + str(N) + "  V=" + str(V) + "  S=" + str(S) + "  W=" + str(W) +
              "  (soglia " + str(soglia) + ")" +
              "  mediane: g_b " + format(np.median([r["g_b_pct"] for r in ins]), "+.3f") + "%" +
              "  p_b " + format(np.median([r["p_b"] for r in ins]), ".3f") +
              "  f_b " + format(np.median([r["f_b"] for r in ins]), ".3f"))
    V, S, W = conta(tutti)
    ramo = ("1 LA REGOLA GUADAGNA E BATTE IL CASO" if S >= 6 else
            "2 NON CONCLUSIVO" if 3 <= S <= 5 else
            "3 DIREZIONE GIUSTA, GUADAGNO INDISTINGUIBILE DAL CASO" if V >= 6 else
            "4 LA REGOLA NON GUADAGNA")
    print()
    print("RAMO CALCOLATO SULLA REGOLA PRE-REGISTRATA: " + ramo)


if __name__ == "__main__":
    main()
