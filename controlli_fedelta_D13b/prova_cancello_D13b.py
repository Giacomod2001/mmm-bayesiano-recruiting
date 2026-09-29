# Prova della logica del cancello di replica e del controllo dei nodi del notebook
# D13b con righe finte: esegue le funzioni di verifica della CELLA 1 (non il pre-volo).
import csv, json, os, sys, tempfile
PROG = r"C:/Users/giaco/Claude/Projects/tesi magistrale"
SCR = os.path.dirname(os.path.abspath(__file__))
cella1 = "".join(json.load(open(os.path.join(PROG, "colab_griglia_D13b_1nodo.ipynb"), encoding="utf-8"))["cells"][1]["source"])
ns = {"__name__": "prova"}
testa = cella1[:cella1.index("# ============================================================================\n# IL CONTROLLO DI UNA RIGA")]
drive = tempfile.mkdtemp(prefix="prova_drive_D13b_").replace("\\", "/")
testa = testa.replace("/content/drive/MyDrive/MMM_griglia_D13b_1nodo", drive)
exec(compile(testa, "testa", "exec"), ns)
mezzo = cella1[cella1.index("def leggi_csv(percorso):"):cella1.index("# ============================================================================\n# PRE-VOLO")]
exec(compile(mezzo, "mezzo", "exec"), ns)
R = ns["RUN_PER_NOME"]
# un file dei draw finto per ogni run: il controllo ne verifica solo l'esistenza
for _r in ns["TABELLA"]:
    _d = os.path.join(ns["affiancato"](ns["csv_di"](_r), "_draw"), _r["nome"] + "_draw.csv.gz")
    os.makedirs(os.path.dirname(_d), exist_ok=True); open(_d, "wb").write(b"x")
riga13 = [r for r in csv.DictReader(open(os.path.join(PROG, "griglia_D13", "griglia_D13_baseline_osservata.csv"), encoding="utf-8"))
          if r["seed_mondo"] == "101" and r["controllo_baseline_f"] == "0.3"][0]
def prova(nome, run, riga, atteso):
    ns["controllo_canali"] = lambda run: ([], "")        # i CSV per canale non ci sono qui
    v = ns["verifica"](run, dict(riga), {})
    esito = "OK  " if v["esito"] == atteso else "FALLITA"
    print(esito, nome, "->", v["esito"], "|", str(v["messaggio"])[:150])
    return v["esito"] == atteso
rep = R["D13b_k12_replica_f030_m0101"]
esiti = [prova("replica = riga di D13", rep, riga13, "ok")]
r2 = dict(riga13); r2["rapporto_mediana"] = "2.4594"
esiti.append(prova("replica con rapporto 2,4594", rep, r2, "anomalia"))
r3 = dict(riga13); r3["rapporto_ci95"] = "3.1254"
esiti.append(prova("replica con forbice diversa", rep, r3, "anomalia"))
r4 = dict(riga13); r4["controllo_baseline_f"] = "0.6"
esiti.append(prova("replica con f = 0,60", rep, r4, "anomalia"))
liv = R["D13b_k01_f030_m0101"]
r5 = dict(riga13); r5["n_knots"] = "8"
esiti.append(prova("livello 1 nodo, riga a 8 nodi", liv, r5, "ok"))
esiti.append(prova("livello 1 nodo, riga a 96 nodi (trappola 2)", liv, riga13, "anomalia"))
r6 = dict(r5); r6["impronta_input_data"] = "000000000000"
esiti.append(prova("livello con impronta diversa da D0", liv, r6, "anomalia"))
r7 = dict(r5); r7["controllo_baseline_colonna"] = ""
esiti.append(prova("livello senza colonna di controllo", liv, r7, "anomalia"))
print("\n%d prove su %d come atteso" % (sum(esiti), len(esiti)))
if not all(esiti):
    sys.exit(1)

# --- la sequenza del cancello della CELLA 2: da_fare / riuscita / fallita ---------
cella2 = "".join(json.load(open(os.path.join(PROG, "colab_griglia_D13b_1nodo.ipynb"), encoding="utf-8"))["cells"][2]["source"])
i0 = cella2.index("NOME_REPLICA = 'D13b_k12_replica_f030_m0101'")
i1 = cella2.index("_st0, _v0, _r0 = stato_cancello()")
pre = cella2[:cella2.index("# ============================================================================\n# D13b: IL CANCELLO DI REPLICA")]
defs = [l for l in pre.split("\n\n\n") if l.lstrip().startswith("def righe_ok") or l.lstrip().startswith("def verifica_sicura")]
for d in defs:
    exec(compile(d, "cella2-def", "exec"), ns)
ns["controllo_canali"] = lambda run: ([], "")
ns["leggi_impronte"] = lambda: {}
exec(compile(cella2[i0:i1], "cella2-cancello", "exec"), ns)
csv_rep = ns["csv_di"](rep)
os.makedirs(os.path.dirname(csv_rep), exist_ok=True)
if os.path.exists(csv_rep):
    os.remove(csv_rep)
st = ns["stato_cancello"]()[0]; ok1 = st == "da_fare"; print("OK  " if ok1 else "FALLITA", "nessuna riga ->", st)
def scrivi(riga):
    with open(csv_rep, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(riga)); w.writeheader(); w.writerow(riga)
r_ok = dict(riga13); r_ok["mondo"] = "D13b_k12_replica_f030_m0101"; scrivi(r_ok)
st = ns["stato_cancello"]()[0]; ok2 = st == "riuscita"; print("OK  " if ok2 else "FALLITA", "riga identica a D13 ->", st)
r_ko = dict(r_ok); r_ko["rapporto_mediana"] = "2.4600"; scrivi(r_ko)
st = ns["stato_cancello"]()[0]; ok3 = st == "fallita"; print("OK  " if ok3 else "FALLITA", "riga diversa ->", st)
try:
    ns["ferma_cancello"](*ns["stato_cancello"]()[1:]); ok4 = False
except SystemExit as e:
    ok4 = "NON RIUSCITO" in str(e) and os.path.exists(os.path.join(ns["CARTELLA_DRIVE"], "ANOMALIA_CANCELLO_REPLICA.txt"))
print("OK  " if ok4 else "FALLITA", "ferma_cancello si ferma e scrive il file di anomalia")
print("sequenza del cancello: %d su 4" % sum([ok1, ok2, ok3, ok4]))
sys.exit(0 if all([ok1, ok2, ok3, ok4]) else 1)
