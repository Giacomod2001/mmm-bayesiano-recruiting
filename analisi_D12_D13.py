"""Legge i CSV prodotti dai notebook D12 e D13 e calcola il RAMO, le metriche
pre-registrate e le righe pronte per le Sezioni A.2 e A.3 dell'Appendice A.

Non inventa niente: ogni cifra viene dai CSV dei run. Si usa dopo aver scaricato
le cartelle `MMM_griglia_D12` e `MMM_griglia_D13` da Drive.

    python analisi_D12_D13.py griglia_D12 griglia_D13

dove i due argomenti sono le cartelle scaricate (uno solo va bene: fa quello).
Scrive a schermo, e con --scrivi anche `analisi_D12_D13_<data>.md`.

Le soglie e i rami sono quelli delle pre-registrazioni del 21 settembre 2026 e
non si toccano:
  D12  E mediano <= 4,0 e C_tot >= 4/8 -> ramo 1; 4,0 < E <= 6,0 -> ramo 2;
       E > 6,0 -> ramo 3
  D13  E(0,30) <= 4,0 -> ramo 1; E(0,60) <= 4,0 < E(0,30) -> ramo 2;
       E(0,90) <= 4,0 < E(0,60) -> ramo 3; E(0,90) > 4,0 -> ramo 4
"""
from __future__ import annotations

import csv
import os
import statistics
import sys
import time

MONDI = [42, 101, 102, 103, 104, 105, 106, 107]
LIVELLI = [0.30, 0.60, 0.90]
# riferimento: D0 osservativo sugli stessi otto mondi (griglia/griglia_D0_osservativo.csv)
E_D0 = {42: 23.32, 101: 27.28, 102: 22.53, 103: 29.50, 104: 28.91,
        105: 18.39, 106: 19.30, 107: 11.84}


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


def it(x, dec=2, segno=False):
    """Numero all'italiana: virgola decimale."""
    if x is None:
        return "n/d"
    s = format(x, ("+" if segno else "") + "." + str(dec) + "f")
    return s.replace(".", ",")


def ammissibile(r):
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


def eccesso(r):
    """E = quota stimata - quota vera, in punti percentuali, con la quota vera
    DI QUEL MONDO (per D12 non e' 18,5: vedi il paragrafo 0 della sua
    pre-registrazione)."""
    s, v = num(r.get("quota_media_stimata_pct")), num(r.get("quota_media_vera_pct"))
    return None if (s is None or v is None) else s - v


def sintesi(righe):
    ok = [r for r in righe if r.get("esito") == "ok"]
    amm = [r for r in ok if ammissibile(r)]
    E = [eccesso(r) for r in ok if eccesso(r) is not None]
    rap = [num(r.get("rapporto_mediana")) for r in ok if num(r.get("rapporto_mediana"))]
    dentro = sum(1 for r in ok if str(r.get("dentro")) == "1")
    pit = [num(r.get("pit")) for r in ok if num(r.get("pit")) is not None]
    div = []
    for r in ok:
        d, tot = num(r.get("divergenze")), (num(r.get("n_chains")) or 0) * (num(r.get("keep")) or 0)
        if d is not None and tot:
            div.append(100.0 * d / tot)
    ess = [num(r.get("ess_roi_m")) for r in ok if num(r.get("ess_roi_m"))]
    E_amm = [eccesso(r) for r in amm if eccesso(r) is not None]
    return {
        "n": len(righe), "ok": len(ok), "ammissibili": len(amm),
        "E_mediano": statistics.median(E) if E else None,
        "E_mediano_amm": statistics.median(E_amm) if E_amm else None,
        "E_min": min(E) if E else None, "E_max": max(E) if E else None,
        "E_per_mondo": {int(float(r["seed_mondo"])): eccesso(r) for r in ok},
        "rapporto_mediano": statistics.median(rap) if rap else None,
        "C_tot": dentro, "pit_mediano": statistics.median(pit) if pit else None,
        "div_mediana": statistics.median(div) if div else None,
        "ess_mediano": statistics.median(ess) if ess else None,
        "righe_ok": ok,
    }


def per_canale(percorso, filtro=lambda r: True):
    """{canale: {rapporto mediano stimato/vero, C_k, larghezza mediana}}"""
    righe = [r for r in leggi(percorso) if filtro(r)]
    fuori = {}
    for r in righe:
        ch = r.get("canale")
        rv, rs = num(r.get("roi_vero")), num(r.get("roi_stimato"))
        larg = num(r.get("larghezza_relativa"))
        d = fuori.setdefault(ch, {"rapporti": [], "dentro": 0, "n": 0, "largh": [],
                                  "roi_vero": []})
        d["n"] += 1
        d["dentro"] += 1 if str(r.get("dentro")) == "1" else 0
        if rv and rs:
            d["rapporti"].append(rs / rv)
            d["roi_vero"].append(rv)
        if larg is not None:
            d["largh"].append(larg)
    for ch, d in fuori.items():
        d["rapporto"] = statistics.median(d["rapporti"]) if d["rapporti"] else None
        d["larghezza"] = statistics.median(d["largh"]) if d["largh"] else None
        d["roi_vero_mediano"] = statistics.median(d["roi_vero"]) if d["roi_vero"] else None
    return fuori


def ramo_D12(s):
    E, C = s["E_mediano"], s["C_tot"]
    if E is None:
        return "NON CALCOLABILE", "nessun run con esito ok"
    if E <= 4.0 and C >= 4:
        return ("1 - IL BLACKOUT TOTALE RECUPERA LA BASELINE",
                "E mediano " + it(E, 1, True) + " <= 4,0 e C_tot " + str(C) + "/8 >= 4/8")
    if E <= 6.0:
        return ("2 - RECUPERO PARZIALE",
                "E mediano " + it(E, 1, True) + " nella fascia 4,0-6,0" +
                ("" if E > 4.0 else "; E <= 4,0 ma C_tot " + str(C) + "/8 < 4/8, "
                 "e la copertura e' parte della prima riga della regola"))
    return ("3 - NEMMENO IL LIVELLO BASTA",
            "E mediano " + it(E, 1, True) + " > 6,0")


def ramo_D13(per_livello):
    E = {f: per_livello[f]["E_mediano"] for f in LIVELLI}
    if any(E[f] is None for f in LIVELLI):
        return "NON CALCOLABILE", "manca almeno un livello"
    if E[0.30] <= 4.0:
        return ("1 - BASTA OSSERVARNE UN TERZO", "E(0,30) = " + it(E[0.30], 1, True) + " <= 4,0")
    if E[0.60] <= 4.0:
        return ("2 - SERVE META'", "E(0,60) = " + it(E[0.60], 1, True) + " <= 4,0 < E(0,30) = " +
                it(E[0.30], 1, True))
    if E[0.90] <= 4.0:
        return ("3 - SERVE QUASI TUTTA", "E(0,90) = " + it(E[0.90], 1, True) + " <= 4,0 < E(0,60) = " +
                it(E[0.60], 1, True))
    return ("4 - OSSERVARE LA BASELINE NON BASTA", "E(0,90) = " + it(E[0.90], 1, True) + " > 4,0")


def blocco_D12(cartella, out):
    csv_p = os.path.join(cartella, "griglia_D12_blackout_totale.csv")
    righe = leggi(csv_p)
    if not righe:
        out.append("D12: nessun CSV in " + csv_p)
        return
    s = sintesi(righe)
    ramo, perche = ramo_D12(s)
    out.append("# D12 - blackout totale geografico")
    out.append("")
    out.append("**RAMO " + ramo + "** (" + perche + ").")
    out.append("")
    out.append("Previsione dichiarata: ramo 1, con E fra 3 e 4 punti. -> " +
               ("CONFERMATA" if ramo.startswith("1") and s["E_mediano"] is not None
                and 3.0 <= s["E_mediano"] <= 4.0 else
                "CONFERMATA NEL RAMO, NON NELLA CIFRA" if ramo.startswith("1") else
                "SMENTITA"))
    out.append("")
    out.append("| Mondo | Quota vera | Quota stimata | E | Rapporto | PIT | Copre | Ammissibile |")
    out.append("|---|---:|---:|---:|---:|---:|:---:|:---:|")
    for r in sorted(s["righe_ok"], key=lambda x: MONDI.index(int(float(x["seed_mondo"])))):
        out.append("| " + str(int(float(r["seed_mondo"]))) + " | " +
                   it(num(r.get("quota_media_vera_pct")), 2) + "% | " +
                   it(num(r.get("quota_media_stimata_pct")), 2) + "% | " +
                   it(eccesso(r), 2, True) + " | " + it(num(r.get("rapporto_mediana")), 4) + " | " +
                   it(num(r.get("pit")), 6) + " | " + ("si" if str(r.get("dentro")) == "1" else "no") +
                   " | " + ("si" if ammissibile(r) else "NO") + " |")
    out.append("")
    out.append("E mediano **" + it(s["E_mediano"], 2, True) + "** (min " + it(s["E_min"], 2, True) +
               ", max " + it(s["E_max"], 2, True) + "); rapporto mediano " +
               it(s["rapporto_mediano"], 2) + "; C_tot " + str(s["C_tot"]) + "/8; " +
               str(s["ammissibili"]) + " run ammissibili su " + str(s["ok"]) + ".")
    out.append("")
    out.append("Confronto con i disegni gia' eseguiti: D0 +22,9 | D2 +7,2 (C 4/8) | D10 +8,3 (C 2/8) | "
               "D12 " + it(s["E_mediano"], 1, True) + " (C " + str(s["C_tot"]) + "/8).")
    out.append("")
    pc = per_canale(csv_p[:-4] + "_canali.csv")
    out.append("| Canale | ROI vero | D12 rapp. | D12 C_k | D12 largh. |")
    out.append("|---|---:|---:|:---:|---:|")
    for ch in sorted(pc, key=lambda c: -(pc[c]["roi_vero_mediano"] or 0)):
        d = pc[ch]
        out.append("| " + ch + " | " + it(d["roi_vero_mediano"], 2) + " | " +
                   it(d["rapporto"], 2) + " | " + str(d["dentro"]) + "/" + str(d["n"]) + " | " +
                   it(d["larghezza"], 2) + " |")
    out.append("")
    perse = [num(r.get("candidature_vere_perse")) for r in s["righe_ok"]
             if num(r.get("candidature_vere_perse"))]
    if perse:
        out.append("**Costo del disegno**: candidature vere perse per mondo, mediana " +
                   it(statistics.median(perse), 0) + " (min " + it(min(perse), 0) + ", max " +
                   it(max(perse), 0) + ").")
    out.append("")
    out.append("### Riga per la Sezione A.2 (registro dei run per disegno)")
    out.append("")
    out.append("| D12 blackout totale | " + str(s["ok"]) + " | " + it(s["rapporto_mediano"], 2) +
               " | " + it(s["E_mediano"], 1, True) + " | " + str(s["C_tot"]) + "/8 | " +
               it(s["div_mediana"], 2) + "% | " + it(s["ess_mediano"], 0) + " |")
    out.append("")
    out.append("(nota per il testo: in D12 la quota vera non e' 18,5% ma quella di ogni mondo, "
               "fra 17,94% e 18,04%, perche' beta e' tenuto fisso a quello del mondo base.)")
    out.append("")


def blocco_D13(cartella, out):
    csv_p = os.path.join(cartella, "griglia_D13_baseline_osservata.csv")
    righe = leggi(csv_p)
    if not righe:
        out.append("D13: nessun CSV in " + csv_p)
        return
    per_livello = {}
    for f in LIVELLI:
        per_livello[f] = sintesi([r for r in righe
                                  if abs((num(r.get("controllo_baseline_f")) or -1) - f) < 1e-9])
    ramo, perche = ramo_D13(per_livello)
    out.append("# D13 - baseline parzialmente osservata")
    out.append("")
    out.append("**CAVEAT, prima di ogni cifra.** Il controllo e' costruito dalla baseline VERA: "
               "misura il caso piu' favorevole possibile ed e' un LIMITE SUPERIORE di quello che un "
               "dato reale potrebbe dare, mai una stima di quello che darebbe. Inoltre, nel "
               "simulatore la baseline e' generata indipendentemente dalla spesa, quindi qui e' un "
               "controllo legittimo; nel mondo reale e' in parte un mediatore, perche' la "
               "pubblicita' genera brand search.")
    out.append("")
    out.append("**RAMO " + ramo + "** (" + perche + ").")
    out.append("")
    E = {f: per_livello[f]["E_mediano"] for f in LIVELLI}
    completi = [f for f in LIVELLI if per_livello[f]["ok"] == len(MONDI)]
    valutabile = len(completi) == len(LIVELLI)
    monotona = (all(E[a] >= E[b] - 1e-9 for a, b in zip(LIVELLI, LIVELLI[1:]))
                if valutabile else None)
    # La previsione REGISTRATA (commit 4cdaf72, par. 5): ramo 3 o 4. La prima
    # stesura diceva 2-3 e non e' mai stata registrata: citarla qui sarebbe
    # presentare come registrata una previsione superata (par. 6, punto 9).
    if not valutabile:
        esclusi = []
        if per_livello[0.30]["ok"] == len(MONDI) and E[0.30] is not None and E[0.30] > 4.0:
            esclusi.append("ramo 1 (E(0,30) = " + it(E[0.30], 2, True) + " > 4,0)")
        out.append("Previsione registrata: ramo 3 o 4, con E monotono decrescente in f. -> "
                   "NON ANCORA VALUTABILE: livelli completi " +
                   (", ".join(it(f, 2) for f in completi) or "nessuno") + " su 3." +
                   (" Gia' escluso: " + "; ".join(esclusi) + "." if esclusi else ""))
    else:
        out.append("Previsione registrata: ramo 3 o 4, con E monotono decrescente in f. -> " +
                   ("CONFERMATA" if ramo[0] in "34" and monotona else
                    "SMENTITA NEL RAMO" if ramo[0] in "12" else
                    "SMENTITA NELLA MONOTONIA"))
    out.append("")
    out.append("| f | Fit | E mediano | E mediano, soli ammissibili | E min | E max | Rapporto mediano | C_tot | Ammissibili |")
    out.append("|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|")
    out.append("| D0 (riferimento) | 8 | +22,9 | +22,9 | +11,8 | +29,5 | 2,22 | 0/8 | 8/8 |")
    for f in LIVELLI:
        s = per_livello[f]
        out.append("| " + it(f, 2) + " | " + str(s["ok"]) + " | " + it(s["E_mediano"], 2, True) +
                   " | " + it(s["E_mediano_amm"], 2, True) +
                   " | " + it(s["E_min"], 2, True) + " | " + it(s["E_max"], 2, True) + " | " +
                   it(s["rapporto_mediano"], 2) + " | " + str(s["C_tot"]) + "/8 | " +
                   str(s["ammissibili"]) + "/" + str(s["ok"]) + " |")
    out.append("")
    out.append("**Monotonia di E in f**: " + (
        "non valutabile: servono tutti e tre i livelli completi" if monotona is None else
        "rispettata in mediana" if monotona else "NON rispettata in mediana") + ".")
    out.append("")
    out.append("| Mondo | E(D0) | E(0,30) | E(0,60) | E(0,90) | monotono |")
    out.append("|---|---:|---:|---:|---:|:---:|")
    for m in MONDI:
        v = [per_livello[f]["E_per_mondo"].get(m) for f in LIVELLI]
        if any(x is None for x in v):
            mono_txt = "n/d"
        else:
            mono_txt = "si" if all(a >= b - 1e-9 for a, b in zip(v, v[1:])) else "NO"
        out.append("| " + str(m) + " | " + it(E_D0.get(m), 2, True) + " | " +
                   " | ".join(it(x, 2, True) for x in v) + " | " + mono_txt + " |")
    out.append("")
    for f in LIVELLI:
        pc = per_canale(csv_p[:-4] + "_canali.csv",
                        lambda r, f=f: ("_f%03d_" % round(f * 100)) in str(r.get("mondo", "")))
        out.append("Per canale, f = " + it(f, 2) + ":")
        out.append("")
        out.append("| Canale | ROI vero | rapp. | C_k | largh. |")
        out.append("|---|---:|---:|:---:|---:|")
        for ch in sorted(pc, key=lambda c: -(pc[c]["roi_vero_mediano"] or 0)):
            d = pc[ch]
            out.append("| " + ch + " | " + it(d["roi_vero_mediano"], 2) + " | " +
                       it(d["rapporto"], 2) + " | " + str(d["dentro"]) + "/" + str(d["n"]) +
                       " | " + it(d["larghezza"], 2) + " |")
        out.append("")
    out.append("### Righe per la Sezione A.2 (registro dei run per disegno)")
    out.append("")
    for f in LIVELLI:
        s = per_livello[f]
        out.append("| D13 baseline osservata f = " + it(f, 2) + " | " + str(s["ok"]) + " | " +
                   it(s["rapporto_mediano"], 2) + " | " + it(s["E_mediano"], 1, True) + " | " +
                   str(s["C_tot"]) + "/8 | " + it(s["div_mediana"], 2) + "% | " +
                   it(s["ess_mediano"], 0) + " |")
    out.append("")


def main():
    cartelle = sys.argv[1:] or ["griglia_D12", "griglia_D13"]
    scrivi = "--scrivi" in cartelle
    cartelle = [c for c in cartelle if not c.startswith("--")]
    out = []
    for c in cartelle:
        if os.path.exists(os.path.join(c, "griglia_D12_blackout_totale.csv")):
            blocco_D12(c, out)
        if os.path.exists(os.path.join(c, "griglia_D13_baseline_osservata.csv")):
            blocco_D13(c, out)
    if not out:
        out = ["Nessun CSV di D12 o D13 trovato in: " + ", ".join(cartelle)]
    testo = "\n".join(out)
    print(testo)
    if scrivi:
        p = "analisi_D12_D13_" + time.strftime("%Y-%m-%d") + ".md"
        open(p, "w", encoding="utf-8").write(testo + "\n")
        print()
        print("scritto " + p)


if __name__ == "__main__":
    main()
