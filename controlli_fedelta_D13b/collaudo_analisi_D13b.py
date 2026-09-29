# Collaudo di analisi_D13b.py su casi sintetici, prima di qualunque fit: per ogni
# caso costruisce una cartella finta con lo stesso schema dei CSV del runner
# (righe di N1 a 1 nodo riscritte con f = 0,30 e le quote volute, la replica
# presa dalla riga di D13), lancia lo script e confronta la prima riga con il
# ramo atteso. Nessun numero di D13b esiste quando gira.
#
#     python controlli_fedelta_D13b/collaudo_analisi_D13b.py
import csv
import os
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction

QUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(QUI)
MONDI = [42, 101, 102, 103, 104, 105, 106, 107]


def leggi(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def scrivi(p, righe):
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(righe[0]))
        w.writeheader()
        w.writerows(righe)


N1 = {int(r["seed_mondo"]): r for r in leggi(os.path.join(REPO, "griglia_N1", "griglia_N1_k01.csv"))}
N1C = leggi(os.path.join(REPO, "griglia_N1", "griglia_N1_k01_canali.csv"))
D13 = [r for r in leggi(os.path.join(REPO, "griglia_D13", "griglia_D13_baseline_osservata.csv"))
       if r["seed_mondo"] == "101" and r["controllo_baseline_f"] == "0.3"][0]


def e_n1(w):
    return Fraction(N1[w]["quota_media_stimata_pct"]) - Fraction(N1[w]["quota_media_vera_pct"])


def cartella(dE=None, E=None, rho28=None, non_amm=(), replica="ok", manca=()):
    """dE: {mondo: punti} rispetto a N1 a 1 nodo; E: {mondo: punti} assoluto."""
    d = tempfile.mkdtemp(prefix="collaudo_D13b_")
    rep = dict(D13)
    rep["mondo"] = "D13b_k12_replica_f030_m0101"
    if replica == "diversa":
        rep["rapporto_mediana"] = "2.4600"
    if replica != "assente":
        scrivi(os.path.join(d, "griglia_D13b_replica_k12.csv"), [rep])
    righe, canali = [], []
    for w in MONDI:
        if w in manca:
            continue
        r = dict(N1[w])
        r["mondo"] = "D13b_k01_f030_m%04d" % w
        r["controllo_baseline_f"] = "0.3"
        r["controllo_baseline_colonna"] = "domanda_organica_osservata"
        vera = Fraction(r["quota_media_vera_pct"])
        e = E[w] if E is not None else e_n1(w) + Fraction(str(dE[w]))
        r["quota_media_stimata_pct"] = format(float(vera + Fraction(str(e))), ".2f")
        if w in non_amm:
            r["rhat_roi_m"] = "1.25"
        righe.append(r)
        for c in N1C:
            if int(c["seed_mondo"]) == w:
                c2 = dict(c)
                c2["mondo"] = r["mondo"]
                if rho28 is not None:
                    c2["rho_spearman"] = format(rho28[w] / 28, ".4f")
                canali.append(c2)
    scrivi(os.path.join(d, "griglia_D13b_k01.csv"), righe)
    scrivi(os.path.join(d, "griglia_D13b_k01_canali.csv"), canali)
    return d


def lancia(d):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, os.path.join(REPO, "analisi_D13b.py"), d, "--repo", REPO],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    shutil.rmtree(d, ignore_errors=True)
    return p.returncode, (p.stdout.splitlines() or [p.stderr.strip()[-200:]])[0]


tutti = lambda v: {w: v for w in MONDI}
CASI = [
    # (nome, cartella, ramo livello atteso, ramo ordine atteso)   None = nessun ramo
    ("E mediano 3,00 -> livello 1", cartella(E=tutti(3)), "1", "C"),
    ("E mediano esattamente 4,00 -> livello 1", cartella(E=tutti(4)), "1", "C"),
    ("E mediano 4,01 e dE piccoli -> non 1", cartella(E=tutti(Fraction(401, 100))), "2", "C"),
    ("dE -6 in 8 su 8 -> livello 2", cartella(dE=tutti(-6)), "2", "C"),
    ("dE mediano esattamente -5,00 in 8 su 8 -> livello 2", cartella(dE=tutti(-5)), "2", "C"),
    ("dE -4,99 in 8 su 8 -> livello 4", cartella(dE=tutti(Fraction(-499, 100))), "4", "C"),
    ("dE -6 in 5 mondi, +1 in 3 -> livello 4 (conteggio)",
     cartella(dE={42: -6, 101: -6, 102: -6, 103: -6, 104: -6, 105: 1, 106: 1, 107: 1}), "4", "C"),
    ("dE +6 in 8 su 8 -> livello 3", cartella(dE=tutti(6)), "3", "C"),
    ("dE +5,00 in 6, -1 in 2 -> livello 3",
     cartella(dE={42: 5, 101: 5, 102: 5, 103: 5, 104: 5, 105: 5, 106: -1, 107: -1}), "3", "C"),
    ("dE nulli -> livello 4", cartella(dE=tutti(0)), "4", "C"),
    ("4 non ammissibili -> 0 e 0", cartella(dE=tutti(-6), non_amm=(42, 101, 102, 103)), "0", "0"),
    ("7 ammissibili, soglia 5, dE -6 in 5 -> livello 2",
     cartella(dE={42: -6, 101: -6, 102: -6, 103: -6, 104: -6, 105: 1, 106: 1, 107: -6}, non_amm=(107,)),
     "2", "C"),
    ("un mondo senza riga ok, 7 ammissibili -> letto su 7",
     cartella(dE=tutti(-6), manca=(107,)), "2", "C"),
    ("rho 18/28 ovunque -> ordine A", cartella(dE=tutti(0), rho28=tutti(18)), "4", "A"),
    ("rho esattamente 17/28 -> ordine A", cartella(dE=tutti(0), rho28=tutti(17)), "4", "A"),
    ("rho 16/28 -> ordine B", cartella(dE=tutti(0), rho28=tutti(16)), "4", "B"),
    ("rho mediano esattamente 13/56 -> ordine C (stretto)",
     cartella(dE=tutti(0), rho28={42: 6, 101: 6, 102: 6, 103: 6, 104: 7, 105: 7, 106: 7, 107: 7}), "4", "C"),
    ("rho 7/28 -> ordine B", cartella(dE=tutti(0), rho28=tutti(7)), "4", "B"),
    ("rho 0 -> ordine C", cartella(dE=tutti(0), rho28=tutti(0)), "4", "C"),
    ("replica diversa -> nessun ramo", cartella(dE=tutti(-6), replica="diversa"), None, None),
    ("replica assente -> nessun ramo", cartella(dE=tutti(-6), replica="assente"), None, None),
]

passati = 0
for nome, d, rl, ro in CASI:
    rc, prima = lancia(d)
    if rl is None:
        ok = rc == 2 and prima.startswith("D13b - NESSUN RAMO")
    else:
        ok = rc == 0 and prima.startswith("D13b - LIVELLO: ramo " + rl + " ") and ("| ORDINE: ramo " + ro + " ") in prima
    passati += ok
    print(("OK      " if ok else "FALLITO ") + nome + "\n         " + prima[:150])
print("\n%d casi su %d come atteso" % (passati, len(CASI)))
sys.exit(0 if passati == len(CASI) else 1)
