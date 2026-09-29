# Collaudo locale dei notebook D12 e D13: esegue le parti della CELLA 1 che
# non richiedono Colab (blob, ricostruzione del generatore, runner e autotest,
# cancello di fedelta' sui cinque dataset committati + cancello specifico del
# disegno). GPU, Drive e Meridian non si possono collaudare qui.
#
# ADATTATO il 22/9/2026 al clone del pacchetto (trappola 0 del prompt N1).
# L'originale, controlli_fedelta_D12_D13/collaudo_notebook.py, clonava il repo
# pubblico da una cartella locale di Windows (_repo_pubblico) che non e' nel
# pacchetto: qui si clona dall'URL, che e' quello che clonano i notebook su
# Colab. Il notebook e la cartella di lavoro si passano come argomenti:
#     python collaudo_notebook_adattato.py <codice> <notebook> [cartella di lavoro]
# <codice> e' il suffisso della cartella di Drive (D12, D13, N1).
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SORGENTE = "https://github.com/Giacomod2001/mmm-bayesiano-recruiting"
codice = sys.argv[1] if len(sys.argv) > 1 else "D12"
NB = os.path.abspath(sys.argv[2])
SCR = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else tempfile.mkdtemp(prefix="collaudo_")
os.makedirs(SCR, exist_ok=True)
REPO = os.path.join(SCR, "collaudo_repo_" + codice)

if os.path.isdir(REPO):
    shutil.rmtree(REPO, ignore_errors=True)
print("clone locale del repo pubblico...")
r = subprocess.run(["git", "clone", "--quiet", SORGENTE, REPO], capture_output=True, text=True)
if r.returncode != 0:
    raise SystemExit("clone fallito: " + r.stderr[-500:])

cella1 = "".join(json.load(open(NB, encoding="utf-8"))["cells"][1]["source"])

# Il contesto che le parti eseguite si aspettano: le costanti della cella,
# fino a `def csv_di`, e le funzioni di lettura CSV / verifica.
ns = {"__name__": "collaudo"}
testa = cella1[:cella1.index("# ======================================"
                             "======================================\n"
                             "# IL CONTROLLO DI UNA RIGA")]
# niente Drive: si sostituisce la cartella con una locale
testa = testa.replace("/content/drive/MyDrive/MMM_griglia_" + codice,
                      os.path.join(SCR, "collaudo_drive_" + codice).replace("\\", "/"))
testa = testa.replace("REPO = '/content/mmm-bayesiano-recruiting'",
                      "REPO = " + repr(REPO.replace("\\", "/")))
exec(compile(testa, "cella1-testa", "exec"), ns)
print("blob decodificato: %d run, %d disegni, generatore_sha %s, runner %d caratteri"
      % (len(ns["TABELLA"]), len(ns["DISEGNI"]), ns["_dati"]["generatore_sha"],
         len(ns["_dati"]["runner"])))
print("diff incorporati:", sorted(ns["_dati"]["diff_generatore"]))
print("pre-registrazioni:", list(ns["_dati"]["preregistrazioni"]))
print("primi 3 run:", [r["nome"] for r in ns["TABELLA"][:3]], "...",
      [r["nome"] for r in ns["TABELLA"][-1:]])

# le funzioni di verifica (servono al gate e al controllo 3)
mezzo = cella1[cella1.index("def leggi_csv(percorso):"):
               cella1.index("# ============================================"
                            "================================\n# PRE-VOLO")]
exec(compile(mezzo, "cella1-verifica", "exec"), ns)

# il registro degli esiti del pre-volo (definito nella sezione PRE-VOLO)
iP = cella1.index("_ESITI = []")
exec(compile(cella1[iP:cella1.index("print('PRE-VOLO della griglia sperimentale')")],
             "cella1-registra", "exec"), ns)

# il blocco 5 (repo, patch, runner, autotest) e il blocco 6 (fedelta')
i5 = cella1.index("# --- 5. repo, generatore ricostruito da main + patch, runner ---")
i7 = cella1.index("# --- 7. i semi contro lo studio osservativo ---")
blocco = cella1[i5:i7]
blocco = blocco.replace("subprocess.run(['git', 'clone', URL_REPO, REPO], check=True)",
                        "subprocess.run(['git', 'clone', '--quiet', " + repr(SORGENTE.replace("\\", "/")) +
                        ", REPO], check=True)")
exec(compile(blocco, "cella1-5-6", "exec"), ns)
print()
print("ESITI:", [(n, t, ok) for n, t, ok, _d in ns["_ESITI"]])
if ns["_RIMEDI"]:
    print()
    print("RIMEDI:")
    print("\n\n".join(ns["_RIMEDI"]))
    raise SystemExit(1)
print()
print("COLLAUDO " + codice + ": controlli 5 e 6 PASSATI")
