"""D11b - regole di riparto alternative, sullo stesso banco di D11.

Riusa studio_D11.py (che NON viene modificato): stessi 8 casi, stessa verita'
(superficie di risposta del mondo base, beta FISSO), stesso controllo nullo
(200 coppie casuali della stessa cifra), stesso oracolo (miglior coppia).
Aggiunge quattro regole:

  B1  aggregato a 4 voci (Google / Meta / LinkedIn / Job board), poi 90/10
  B2  solo tagli: taglia dove P<=10%, ridistribuisce in proporzione alla spesa
  H9  passo scalato con la certezza: passo_c = 15% x (1 - w_c / w_max)
  H6  il totale: tutti i canali x k, sulla verita'; ROI del totale dai draw

uso: python studio_D11b.py --cancello   # riproduce (a) e (b) di D11, e basta
     python studio_D11b.py              # lo studio intero (DOPO l'approvazione)
"""
import csv
import gzip
import importlib.util
import json
import os
import sys

import numpy as np

QUI = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("s11", os.path.join(QUI, "studio_D11.py"))
S11 = importlib.util.module_from_spec(_s); _s.loader.exec_module(S11)
G, PB, PK, CASI = S11.G, S11.PB, S11.PK, S11.CASI

AGGREGATI = {"Google": ["Google Ads"], "Meta": ["Meta Ads"], "LinkedIn": ["LinkedIn Ads"],
             "Job board": ["Indeed", "Subito Lavoro", "Jooble", "Altre job board"]}
PASSO = PB.PASSO_PCT                       # 15%, lo stesso della 90/10
K_TOTALE = [0.80, 0.90, 0.95, 1.00, 1.05, 1.10, 1.20]
RPK = 40.0                                 # revenue_per_kpi del runner
REGOLE = ["b", "B1", "B2", "H9"]
TOLL_SOMMA_EUR = 1.0


# ----------------------------------------------------------------- i draw
def draw_matrice(draw_path):
    """(n_draw x canali) contributi, piu' la colonna totale, dai draw salvati."""
    with gzip.open(draw_path, "rt", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        canali = [c for c in r.fieldnames if c != "totale"]
        righe = [[float(x[c]) for c in canali] + [float(x["totale"])] for x in r]
    M = np.array(righe)
    return canali, M[:, :-1], M[:, -1]


def spesa_del_fit(can, seed):
    return {x["canale"]: float(x["spesa"]) for x in
            csv.DictReader(open(os.path.join(PK, can), newline="", encoding="utf-8"))
            if x["seed_mondo"] == str(seed)}


# ----------------------------------------------------------------- le regole
def riparto_B1(draw_path, spesa):
    """90/10 su quattro aggregati; dentro l'aggregato la stessa percentuale a tutti."""
    canali, C, T = draw_matrice(draw_path)
    idx = {c: i for i, c in enumerate(canali)}
    sp_agg = {a: sum(spesa[c] for c in cs) for a, cs in AGGREGATI.items()}
    roi_port = T / sum(spesa.values())
    P = {}
    for a, cs in AGGREGATI.items():
        contrib = C[:, [idx[c] for c in cs]].sum(axis=1)
        P[a] = float((contrib / sp_agg[a] > roi_port).mean() * 100.0)
    righe, scambio = PB.proposta(P, sp_agg)          # stessa regola di bilancio della 90/10
    rip = {}
    for a, p, dec, d, nu, no in righe:
        if dec in ("ALZA", "TAGLIA"):
            for c in AGGREGATI[a]:
                rip[c] = d
    return rip, P


def riparto_B2(draw_path, spesa):
    """Solo il lato del taglio della 90/10; i soldi liberati vanno a tutti gli altri
    in proporzione alla spesa attuale (= stessa percentuale per tutti i non tagliati)."""
    P, n = PB.probabilita(draw_path, spesa)
    tagli = [c for c, p in P.items() if p <= PB.SOGLIA_TAGLIA]
    if not tagli:
        return {}, P
    liberati = sum(spesa[c] * PASSO / 100.0 for c in tagli)
    altri = [c for c in spesa if c not in tagli]
    sp_altri = sum(spesa[c] for c in altri)
    rip = {c: -PASSO for c in tagli}
    for c in altri:
        rip[c] = 100.0 * liberati / sp_altri
    return rip, P


def riparto_H9(draw_path, spesa):
    """La 90/10 con passo per canale scalato dalla certezza: 1 - w_c / w_max, dove
    w_c = (q95 - q05) / mediana del ROI del canale nei draw. Il canale con
    l'intervallo piu' largo ha passo zero. Bilancio: si scala il lato piu' grande."""
    canali, C, T = draw_matrice(draw_path)
    idx = {c: i for i, c in enumerate(canali)}
    P, n = PB.probabilita(draw_path, spesa)
    w = {}
    for c in canali:
        roi = C[:, idx[c]] / spesa[c]
        w[c] = float((np.quantile(roi, .95) - np.quantile(roi, .05)) / np.median(roi))
    w_max = max(w.values())
    passo = {c: PASSO * (1.0 - w[c] / w_max) for c in canali}
    desiderio = {c: ("ALZA" if p >= PB.SOGLIA_ALZA else "TAGLIA")
                 for c, p in P.items() if p >= PB.SOGLIA_ALZA or p <= PB.SOGLIA_TAGLIA}
    su = sum(spesa[c] * passo[c] / 100.0 for c, v in desiderio.items() if v == "ALZA")
    giu = sum(spesa[c] * passo[c] / 100.0 for c, v in desiderio.items() if v == "TAGLIA")
    scambio = min(su, giu)
    k_su = scambio / su if su > 0 else 0.0
    k_giu = scambio / giu if giu > 0 else 0.0
    rip = {}
    for c, v in desiderio.items():
        eff = passo[c] * (k_su if v == "ALZA" else -k_giu)
        if abs(eff) > 1e-12:
            rip[c] = eff
    return rip, P, w, passo


def totale_H6(curve, canali, spesa, draw_path):
    """Tutti i canali x k, sulla verita'. Piu' il ROI del totale nei draw."""
    Y = {k: S11.contributo(curve, canali, {c: 100.0 * (k - 1.0) for c in canali}) for k in K_TOTALE}
    tot_sp = sum(spesa.values())
    marg_vero = (Y[1.05] - Y[0.95]) / (0.10 * tot_sp) * RPK      # EUR per EUR, al totale attuale
    roi_medio_vero = Y[1.00] * RPK / tot_sp
    _, C, T = draw_matrice(draw_path)
    roi_tot = T / tot_sp
    return Y, marg_vero, roi_medio_vero, (float(np.quantile(roi_tot, .05)),
                                          float(np.median(roi_tot)),
                                          float(np.quantile(roi_tot, .95)))


# ----------------------------------------------------------------- il banco
def valuta(curve, canali, spesa, rip, Ya, seed):
    """g, euro mossi, nullo e oracolo alla STESSA cifra della regola, percentile, frazione.
    Un riparto vuoto ('fermo') ha g = 0 e nessun nullo: p e f restano NaN."""
    eur = sum(abs(spesa[c] * d / 100.0) for c, d in rip.items()) / 2.0
    Y = S11.contributo(curve, canali, rip)
    g = Y - Ya
    if eur <= 0:
        return dict(Y=Y, g=g, eur=0.0, gd=np.array([]), ge=float("nan"), oracolo="",
                    p=float("nan"), f=float("nan"))
    rng = np.random.default_rng(S11.SEME_NULLO + seed)       # stesso seme di D11
    tutte = S11.coppie(canali)
    gd = []
    while len(gd) < S11.N_CASUALI:
        su, giu = tutte[int(rng.integers(0, len(tutte)))]
        d_giu = -100.0 * eur / spesa[giu]
        if d_giu <= -100.0:
            continue
        gd.append(S11.contributo(curve, canali, {su: 100.0 * eur / spesa[su], giu: d_giu}) - Ya)
    gd = np.array(sorted(gd))
    migliore, ge = None, -np.inf
    for su, giu in tutte:
        d_giu = -100.0 * eur / spesa[giu]
        if d_giu <= -100.0:
            continue
        gg = S11.contributo(curve, canali, {su: 100.0 * eur / spesa[su], giu: d_giu}) - Ya
        if gg > ge:
            ge, migliore = gg, (su, giu)
    return dict(Y=Y, g=g, eur=eur, gd=gd, ge=ge, oracolo=migliore[0] + " <- " + migliore[1],
                p=float((gd < g).mean()), f=(g / ge if ge > 0 else float("nan")))


def controlla_somma(rip, spesa, nome):
    scarto = sum(spesa[c] * d / 100.0 for c, d in rip.items())
    if abs(scarto) > TOLL_SOMMA_EUR:
        raise SystemExit(nome + ": la somma del riparto non e' zero: " + format(scarto, "+.2f") + " EUR")
    return scarto


def testo_rip(rip):
    return ";".join(c + "=" + format(d, "+.4f") for c, d in rip.items())


def cancello():
    """Riproduce (a) e (b) di D11 e le confronta con D11_risultati.csv. Numeri gia' noti."""
    attesi = {(r["disegno"], int(r["mondo"])): r for r in
              csv.DictReader(open(os.path.join(QUI, "D11_risultati.csv"), newline="", encoding="utf-8"))}
    ok = True
    print("CANCELLO D11b: riproduzione di (a) spesa attuale e (b) regola 90/10 di D11")
    for dis, seed, draw, can in CASI:
        canali, spesa, curve = S11.mondo(seed)
        rip_b, _, _ = S11.riparto_90_10(draw, can, seed)
        Ya = S11.contributo(curve, canali)
        vb = valuta(curve, canali, spesa, rip_b, Ya, seed)
        a = attesi[(dis, seed)]
        d = [abs(Ya - float(a["Y_a"])), abs(vb["Y"] - float(a["Y_b"])),
             abs(vb["g"] - float(a["g_b"])), abs(vb["p"] - float(a["p_b"])),
             abs(vb["eur"] - float(a["euro_mossi_b"]))]
        bene = d[0] < 1e-2 and d[1] < 1e-2 and d[2] < 1e-2 and d[3] < 1e-3 and d[4] < 1e-1
        ok &= bene
        print(("  [" + dis + " " + str(seed) + "]").ljust(14) +
              ("OK " if bene else "DIVERSO ") +
              "Y_a " + format(Ya, ".3f") + " Y_b " + format(vb["Y"], ".3f") +
              " g_b " + format(vb["g"], "+.3f") + " p_b " + format(vb["p"], ".4f") +
              " eur " + format(vb["eur"], ".2f"))
    print("CANCELLO: " + ("PASSATO, 8 su 8 identici a D11" if ok else "FALLITO"))
    return ok


def main():
    if not cancello():
        raise SystemExit("il cancello non passa: non si va avanti")
    print()
    righe_out, nulli, h6 = [], {}, []
    for dis, seed, draw, can in CASI:
        canali, spesa, curve = S11.mondo(seed)
        dp = os.path.join(PK, draw)
        Ya = S11.contributo(curve, canali)
        rip = {}
        rip["b"], _, _ = S11.riparto_90_10(draw, can, seed)
        rip["B1"], P1 = riparto_B1(dp, spesa_del_fit(can, seed))
        rip["B2"], P2 = riparto_B2(dp, spesa_del_fit(can, seed))
        rip["H9"], P9, w9, passo9 = riparto_H9(dp, spesa_del_fit(can, seed))
        riga = dict(disegno=dis, mondo=seed, gia_visto=int((dis, seed) == S11.CASO_GIA_VISTO),
                    Y_a=round(Ya, 3))
        for nome in REGOLE:
            scarto = controlla_somma(rip[nome], spesa, nome + " " + dis + "/" + str(seed))
            v = valuta(curve, canali, spesa, rip[nome], Ya, seed)
            riga[nome + "_riparto"] = testo_rip(rip[nome])
            riga[nome + "_scarto_eur"] = round(scarto, 4)
            riga[nome + "_eur"] = round(v["eur"], 2)
            riga[nome + "_Y"] = round(v["Y"], 3)
            riga[nome + "_g"] = round(v["g"], 3)
            riga[nome + "_g_pct"] = round(100.0 * v["g"] / Ya, 5)
            riga[nome + "_p"] = round(v["p"], 4) if v["p"] == v["p"] else ""
            riga[nome + "_f"] = round(v["f"], 4) if v["f"] == v["f"] else ""
            riga[nome + "_oracolo"] = v["oracolo"]
            riga[nome + "_nullo_mediana"] = round(float(np.median(v["gd"])), 3) if len(v["gd"]) else ""
            riga[nome + "_nullo_p90"] = round(float(np.quantile(v["gd"], .90)), 3) if len(v["gd"]) else ""
            nulli[nome + "_" + dis + "_" + str(seed)] = v["gd"].tolist()
        riga["H9_larghezze"] = ";".join(c + "=" + format(w9[c], ".3f") for c in canali)
        riga["H9_passi"] = ";".join(c + "=" + format(passo9[c], ".2f") for c in canali)
        riga["B1_P"] = ";".join(a + "=" + format(P1[a], ".1f") for a in AGGREGATI)
        righe_out.append(riga)
        Y6, marg, roi_med, (q05, q50, q95) = totale_H6(curve, canali, spesa, dp)
        h6.append(dict(disegno=dis, mondo=seed, spesa_totale=round(sum(spesa.values()), 2),
                       roi_medio_vero=round(roi_med, 4), marginale_totale_vero=round(marg, 4),
                       roi_totale_draw_q05=round(q05, 4), roi_totale_draw_q50=round(q50, 4),
                       roi_totale_draw_q95=round(q95, 4),
                       **{"Y_k" + format(k, ".2f"): round(Y6[k], 3) for k in K_TOTALE},
                       **{"g_pct_k" + format(k, ".2f"): round(100.0 * (Y6[k] / Y6[1.0] - 1.0), 4) for k in K_TOTALE}))
        print(("[" + dis + " " + str(seed) + "]").ljust(12) +
              " ".join(n + " " + format(riga[n + "_g_pct"], "+.3f") + "%" +
                       ("(p " + format(riga[n + "_p"], ".2f") + ")" if riga[n + "_p"] != "" else "(fermo)")
                       for n in REGOLE) +
              " | H6 marg " + format(marg, ".3f") + " vs medio " + format(roi_med, ".3f"))
    with open(os.path.join(QUI, "D11b_risultati.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(righe_out[0])); w.writeheader(); w.writerows(righe_out)
    with open(os.path.join(QUI, "D11b_totale_H6.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(h6[0])); w.writeheader(); w.writerows(h6)
    json.dump(nulli, open(os.path.join(QUI, "D11b_controllo_nullo.json"), "w"))
    # --- i conteggi e i rami pre-registrati, per regola
    print()
    print("CONTEGGI (8 casi). S = casi con p >= 0,90. W' = casi con g% > g% della 90/10. F = casi fermi.")
    for nome in ("B1", "B2", "H9"):
        S = sum(1 for r in righe_out if r[nome + "_p"] != "" and r[nome + "_p"] >= 0.90)
        W = sum(1 for r in righe_out if r[nome + "_g_pct"] > r["b_g_pct"])
        F = sum(1 for r in righe_out if r[nome + "_eur"] == 0)
        V = sum(1 for r in righe_out if r[nome + "_g"] > 0)
        ramo = ("1 GUADAGNA E BATTE IL CASO" if S >= 6 else
                "2 MEGLIO DELLA 90/10, NON DEL CASO" if W >= 6 else
                "3 NON MEGLIO DELLA 90/10")
        peggiore = min(r[nome + "_g_pct"] for r in righe_out)
        peggiore_b = min(r["b_g_pct"] for r in righe_out)
        print("  " + nome.ljust(3) + " V=" + str(V) + " S=" + str(S) + " W'=" + str(W) + " F=" + str(F) +
              "  mediana g " + format(float(np.median([r[nome + "_g_pct"] for r in righe_out])), "+.3f") + "%" +
              "  perdita max " + format(peggiore, "+.3f") + "% (90/10: " + format(peggiore_b, "+.3f") + "%)" +
              "  -> RAMO " + ramo)
    m = [r["marginale_totale_vero"] for r in h6]
    print("  H6  marginale vero sul totale: mediana " + format(float(np.median(m)), ".3f") +
          " EUR/EUR (min " + format(min(m), ".3f") + " max " + format(max(m), ".3f") + ")" +
          "; ROI medio vero " + format(float(np.median([r["roi_medio_vero"] for r in h6])), ".3f"))


if __name__ == "__main__":
    if "--cancello" in sys.argv:
        sys.exit(0 if cancello() else 1)
    main()
