# CONTROLLO DI FEDELTA' 1 (D12): senza --blackout il generatore G6 produce
# mondi BIT-IDENTICI a quelli del generatore della griglia (A + G1..G4).
# Confronto file per file, byte per byte.
import filecmp
import hashlib
import os
import shutil
import subprocess
import sys

SP = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(SP, "A")          # generatore della griglia (sha c57be0b1e94c0bbd)
B = os.path.join(SP, "B")          # generatore + G6

CASI = [
    ("base m42", ["--seed-mondo", "42"], "mondo_0042"),
    ("base m101", ["--seed-mondo", "101"], "mondo_0101"),
    ("base m107", ["--seed-mondo", "107"], "mondo_0107"),
    ("sanita m42", ["--seed-mondo", "42", "--sanita"], "mondo_0042_sanita"),
    ("pause2 m42", ["--seed-mondo", "42", "--pause2"], "mondo_0042_pause2"),
    ("casuale2 m42", ["--seed-mondo", "42", "--casuale2"], "mondo_0042_casuale2"),
    ("geo m42", ["--seed-mondo", "42", "--geo"], "mondo_0042_geo"),
    ("calendario 2 giri m42", ["--seed-mondo", "42", "--calendario",
                               "--calendario-rotazione", "0"], "mondo_0042_calendario"),
    ("calendario 4 giri m103", ["--seed-mondo", "103", "--calendario",
                                "--calendario-rotazione", "3",
                                "--calendario-giri", "4"], "mondo_0103_calendario"),
]


def genera(radice, flag):
    r = subprocess.run([sys.executable, "genera_dati_simulati.py"] + flag,
                       cwd=radice, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("generazione fallita in " + radice + " con " +
                         " ".join(flag) + "\n" + (r.stdout + r.stderr)[-2000:])


def files_di(d):
    out = {}
    for radice, _dirs, nomi in os.walk(d):
        for nome in nomi:
            pieno = os.path.join(radice, nome)
            out[os.path.relpath(pieno, d).replace("\\", "/")] = pieno
    return out


tot_file, tot_diversi = 0, 0
for etichetta, flag, cartella in CASI:
    for radice in (A, B):
        shutil.rmtree(os.path.join(radice, "dati_simulati_mondi"), ignore_errors=True)
        genera(radice, flag)
    fa = files_di(os.path.join(A, "dati_simulati_mondi", cartella))
    fb = files_di(os.path.join(B, "dati_simulati_mondi", cartella))
    if set(fa) != set(fb):
        print(etichetta, "ELENCO FILE DIVERSO:", sorted(set(fa) ^ set(fb)))
        tot_diversi += 1
        continue
    diversi = []
    for nome in sorted(fa):
        if not filecmp.cmp(fa[nome], fb[nome], shallow=False):
            diversi.append(nome)
    tot_file += len(fa)
    tot_diversi += len(diversi)
    print("%-26s %2d file, %s" % (etichetta, len(fa),
                                  "TUTTI IDENTICI" if not diversi
                                  else "DIVERSI: " + ", ".join(diversi)))

print()
print("TOTALE: %d file confrontati, %d diversi" % (tot_file, tot_diversi))
print("ESITO CONTROLLO 1:", "PASSATO" if tot_diversi == 0 else "FALLITO")
