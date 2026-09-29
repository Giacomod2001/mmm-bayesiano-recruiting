# Costruisce colab_griglia_D13b_1nodo.ipynb a partire dal notebook congelato
# colab_griglia_D13.ipynb, con le stesse sostituzioni che
# controlli_fedelta_N1/fai_notebook_N1.py ha fatto per N1 (nodi dalla riga del
# run, n_knots controllato sulla riga, cancello di replica) e tre differenze:
#
#   1. i run hanno il controllo organico di D13, f = 0,30 (runner R8,
#      --controllo-baseline), e 1 nodo per trimestre (8 nodi);
#   2. il fit di replica e' D13 a f = 0,30 sul MONDO 101 a 12 nodi per
#      trimestre, e deve riprodurre la riga di D13 (non quella di D0): il run di
#      D13 sul mondo 42 a f = 0,30 non era ammissibile;
#   3. il cancello di fedelta' specifico tiene ENTRAMBI i controlli: quello di
#      D13 sul controllo organico (copiato dal notebook congelato, non riscritto)
#      e quello di N1 sui nodi.
#
# Pre-registrazione: preregistrazioni/PREREGISTRAZIONE_D13b_baseline_osservata_1nodo.md
#
#     python controlli_fedelta_D13b/fai_notebook_D13b.py <cartella di uscita>
import base64
import csv
import hashlib
import io
import json
import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(QUI)
if len(sys.argv) < 2:
    raise SystemExit("uso: fai_notebook_D13b.py <cartella di uscita>")
USCITA = os.path.abspath(sys.argv[1])
A = chr(39)

NB_D13 = os.path.join(REPO, "colab_griglia_D13.ipynb")
SHA_D13 = "3f17879db07d22f80d7bbcdd6c69a10e9414953e4f49fddcce86a58ce6999725"
SHA_G6 = "8f86eb032d0113c0"
PREREG = "PREREGISTRAZIONE_D13b_baseline_osservata_1nodo.md"
MONDI = [42, 101, 102, 103, 104, 105, 106, 107]
F = 0.30
MONDO_REPLICA = 101
NOME_REPLICA = "D13b_k12_replica_f030_m0101"
NODI = {1: 8, 12: 96}
CODICI = {12: "D13bR", 1: "D13b"}
CSV = {12: "griglia_D13b_replica_k12.csv", 1: "griglia_D13b_k01.csv"}
NOME_NB = "colab_griglia_D13b_1nodo.ipynb"


def sha_lf(percorso):
    return hashlib.sha256(open(percorso, "rb").read().replace(b"\r\n", b"\n")).hexdigest()


if sha_lf(NB_D13) != SHA_D13:
    raise SystemExit("colab_griglia_D13.ipynb non e' quello committato: " + sha_lf(NB_D13))
nb13 = json.load(open(NB_D13, encoding="utf-8"))
cella1 = "".join(nb13["cells"][1]["source"])
cella2 = "".join(nb13["cells"][2]["source"])

i0 = cella1.index("_BLOB = (\n")
i1 = cella1.index("\n)\n", i0) + len("\n)\n")
pezzi = [r.strip().strip(",").strip("'") for r in cella1[i0:i1].splitlines()[1:-1]]
blob13 = json.loads(base64.b64decode("".join(pezzi)).decode("utf-8"))
if blob13["generatore_sha"] != SHA_G6:
    raise SystemExit("il blob di D13 ha generatore " + blob13["generatore_sha"])
if blob13["runner"] != open(os.path.join(REPO, "runner_R8_griglia.py"), encoding="utf-8").read().replace("\r\n", "\n"):
    raise SystemExit("il runner nel blob di D13 non e' runner_R8_griglia.py")

# l'impronta attesa di ogni run e' quella di D0 dello stesso mondo (i dati media
# sono quelli di D0 byte per byte; il controllo organico non entra nell'impronta)
with open(os.path.join(REPO, "griglia", "griglia_D0_osservativo.csv"), newline="", encoding="utf-8") as f:
    D0 = {int(r["seed_mondo"]): r for r in csv.DictReader(f)}
for m in MONDI:
    if D0[m]["impronta_input_data"] != blob13["osservativo"][str(m)]["impronta_input_data"]:
        raise SystemExit("impronta di D0 del mondo %d diversa fra CSV e blob" % m)

# la riga di D13 che la replica deve riprodurre
with open(os.path.join(REPO, "griglia_D13", "griglia_D13_baseline_osservata.csv"), newline="",
          encoding="utf-8") as f:
    _r13 = [r for r in csv.DictReader(f)
            if int(r["seed_mondo"]) == MONDO_REPLICA and abs(float(r["controllo_baseline_f"]) - F) < 1e-9]
if len(_r13) != 1 or _r13[0]["esito"] != "ok" or int(_r13[0]["n_knots"]) != 96:
    raise SystemExit("riga di D13 per la replica non trovata o non valida")
D13_REPLICA = _r13[0]
if D13_REPLICA["impronta_input_data"] != D0[MONDO_REPLICA]["impronta_input_data"]:
    raise SystemExit("la riga di D13 del mondo 101 ha un'impronta diversa da D0")

COL_ATTESI = ["n", "codice", "nome", "disegno", "seed_mondo", "parametri_disegno",
              "canali_trattati", "dose_per_canale", "controllo_baseline", "regola",
              "atteso", "banda_min_pct", "banda_max_pct", "anomalia_min_pct",
              "anomalia_max_pct", "impronta_attesa", "riduzione_attesa_pct",
              "knots_per_quarter", "n_knots", "keep", "n_chains", "adapt", "burnin",
              "seed_mcmc", "revenue_per_kpi", "prior_tipo", "prior_sigma", "prior_mu",
              "decimali_stagionalita", "csv"]


def riga(n, k, seme, nome):
    return {"codice": CODICI[k], "disegno": "base", "seed_mondo": seme, "nome": nome,
            "parametri_disegno": "", "canali_trattati": "", "dose_per_canale": {},
            "controllo_baseline": F, "regola": "prima_misura", "atteso": None,
            "banda_min_pct": None, "banda_max_pct": None, "anomalia_min_pct": None,
            "anomalia_max_pct": None,
            "impronta_attesa": D0[seme]["impronta_input_data"],
            "riduzione_attesa": None, "prior_tipo": "riferimento", "prior_sigma": 0.9,
            "prior_mu": 0.2, "osservativo_atteso": {}, "n": n, "csv": CSV[k],
            "prereg": PREREG, "attivo_default": True,
            "knots_per_quarter": k, "n_knots": NODI[k]}


def tabella_D13b():
    # run 1 = replica di D13 (f = 0,30, mondo 101, 12 nodi): regola identico_osservativo,
    # con gli attesi presi dalla RIGA DI D13 (rapporto alla quarta cifra, pit, forbice, dentro)
    r = riga(1, 12, MONDO_REPLICA, NOME_REPLICA)
    r["regola"] = "identico_osservativo"
    r["atteso"] = float(D13_REPLICA["rapporto_mediana"])
    r["osservativo_atteso"] = {c: D13_REPLICA[c] for c in
                               ("rapporto_mediana", "pit", "rapporto_ci05", "rapporto_ci95", "dentro",
                                "impronta_input_data")}
    fuori, n = [r], 1
    for seme in MONDI:
        n += 1
        fuori.append(riga(n, 1, seme, "D13b_k01_f030_m%04d" % seme))
    return fuori


def attesi_csv(tabella):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COL_ATTESI, extrasaction="ignore")
    w.writeheader()
    for r in tabella:
        w.writerow({
            "n": r["n"], "codice": r["codice"], "nome": r["nome"], "disegno": r["disegno"],
            "seed_mondo": r["seed_mondo"], "parametri_disegno": "", "canali_trattati": "",
            "dose_per_canale": "", "controllo_baseline": r["controllo_baseline"], "regola": r["regola"],
            "atteso": "" if r["atteso"] is None else r["atteso"],
            "banda_min_pct": "", "banda_max_pct": "", "anomalia_min_pct": "", "anomalia_max_pct": "",
            "impronta_attesa": r["impronta_attesa"], "riduzione_attesa_pct": "",
            "knots_per_quarter": r["knots_per_quarter"], "n_knots": r["n_knots"],
            "keep": 2000, "n_chains": 4, "adapt": 500, "burnin": 500, "seed_mcmc": 42,
            "revenue_per_kpi": 40.0, "prior_tipo": r["prior_tipo"], "prior_sigma": r["prior_sigma"],
            "prior_mu": r["prior_mu"], "decimali_stagionalita": 4, "csv": r["csv"]})
    return buf.getvalue()


def blob_D13b():
    tab = tabella_D13b()
    d = dict(blob13)
    d["tabella"] = tab
    d["disegni"] = [
        ["D13bR", "replica di D13: f = 0,30, mondo 101, 12 nodi per trimestre (96 nodi) - CANCELLO",
         CSV[12], PREREG, True],
        ["D13b", "controllo organico f = 0,30, 1 nodo per trimestre (8 nodi) x 8 mondi", CSV[1], PREREG, True]]
    d["attesi_csv"] = attesi_csv(tab)
    d["preregistrazioni"] = {PREREG: open(os.path.join(REPO, "preregistrazioni", PREREG),
                                          encoding="utf-8").read().replace("\r\n", "\n")}
    return d


def blob_testo(d):
    b = base64.b64encode(json.dumps(d, ensure_ascii=False).encode("utf-8")).decode("ascii")
    pezzi = [b[i:i + 100] for i in range(0, len(b), 100)]
    return "_BLOB = (\n" + "".join("    '" + p + "',\n" for p in pezzi) + ")\n"


def sub(src, vecchio, nuovo, etichetta):
    n = src.count(vecchio)
    if n != 1:
        raise SystemExit("notebook, sostituzione '%s': trovata %d volte" % (etichetta, n))
    return src.replace(vecchio, nuovo)


TESTA_D13 = """# D13: la BASELINE PARZIALMENTE OSSERVATA, tre livelli x otto mondi.
# I dati media non si toccano: il mondo e' quello base, byte per byte, e si
# aggiunge UNA variabile di controllo costruita dalle candidature organiche
# vere, c = f x organico_vero x exp(N(0, 0,15)), con f = 0,30 / 0,60 / 0,90 e
# rng dedicato default_rng(seme + 31). 24 fit. Serve a sapere quanta domanda
# organica bisogna saper contare perche' l'errore si dimezzi. CAVEAT, da
# ripetere accanto a ogni cifra: il controllo e' costruito dalla baseline
# VERA, quindi misura il caso piu' favorevole possibile ed e' un limite
# SUPERIORE di quello che un dato reale potrebbe dare. La regola di lettura
# sta nel paragrafo 4 della pre-registrazione, fissata prima.
DISEGNI_ATTIVI = ['D13']"""

TESTA_D13B = """# D13b: la DOMANDA ORGANICA OSSERVATA CON LA BASELINE A 1 NODO PER TRIMESTRE.
# Due disegni in questo notebook, nell'ordine: il fit di REPLICA (D13 a f = 0,30
# sul mondo 101 a 12 nodi per trimestre, cioe' la riga di D13 rifatta) e gli
# otto mondi di D0 con il controllo organico di D13 a f = 0,30 e la baseline a
# 1 nodo per trimestre (8 nodi), mondo 42 per primo. I dati media sono quelli di
# D0 byte per byte e ogni run pretende l'impronta di D0 dello stesso mondo. La
# replica e' un CANCELLO: se non riproduce la riga di D13 alla quarta cifra,
# nessun altro fit parte, nemmeno al rilancio. CAVEAT di D13, da ripetere
# accanto a ogni cifra: il controllo e' costruito dalla baseline VERA, ed e' un
# limite SUPERIORE di quello che un dato reale potrebbe dare. I rami li stampa
# analisi_D13b.py, non una persona.
DISEGNI_ATTIVI = ['D13bR', 'D13b']"""

GATE_D13_INIZIO = "\n\ndef _gate_disegno():\n    \"\"\"Cancello di fedelta' specifico di D13"
GATE_D13_FINE = "            '; con f = 0 nessun file scritto')\n"

# il cancello dei nodi di N1, identico a quello di fai_notebook_N1.py salvo il nome
GATE_NODI = '''

def _gate_nodi():
    """Cancello dei nodi, lo stesso di N1: la formula e' quella della CELLA 9 del
    notebook congelato colab_end_to_end.ipynb, che il runner esegue; la si legge
    da li' (non da una copia) e la si valuta con le settimane del mondo 42
    rigenerato. Poi: il runner R8 passa davvero --knots-per-quarter alla cella,
    e l'impronta attesa di ogni run e' quella di D0 dello stesso mondo."""
    _g = subprocess.run([sys.executable, GEN, '--seed-mondo', '42'], cwd=REPO,
                        capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if _g.returncode != 0:
        raise RuntimeError('generatore fallito: ' + (_g.stderr or _g.stdout)[-300:])
    _mondo = os.path.join(REPO, 'dati_simulati_mondi', 'mondo_0042')
    with open(os.path.join(_mondo, 'modello', 'candidature_settimanali.csv'), newline='',
              encoding='utf-8') as _f:
        _n_sett = len({r['settimana'] for r in csv.DictReader(_f)})
    _nb = json.load(open(os.path.join(REPO, 'colab_end_to_end.ipynb'), encoding='utf-8'))
    _formule = [l.strip() for c in _nb['cells'] for l in ''.join(c['source']).splitlines()
                if l.strip().startswith('N_KNOTS = ')]
    _attesa = 'N_KNOTS = min(N_SETTIMANE, max(1, int(round(N_SETTIMANE / 13.0 * KNOTS_PER_QUARTER))))'
    if _formule != [_attesa]:
        raise RuntimeError('formula dei nodi nel notebook congelato: ' + str(_formule)[:200])
    _src = open(RUNNER, encoding='utf-8').read()
    if 'ns["KNOTS_PER_QUARTER"] = int(args.knots_per_quarter)' not in _src:
        raise RuntimeError('il runner non passa --knots-per-quarter alla cella del fit')
    _ottenuti = {}
    for _kpq in sorted({int(r['knots_per_quarter']) for r in TABELLA}):
        _ns = {'N_SETTIMANE': _n_sett, 'KNOTS_PER_QUARTER': _kpq}
        exec(_formule[0], _ns)
        _ottenuti[_kpq] = int(_ns['N_KNOTS'])
    _tab = {int(r['knots_per_quarter']): int(r['n_knots']) for r in TABELLA}
    if _ottenuti != _tab:
        raise RuntimeError('nodi calcolati ' + str(_ottenuti) + ' invece di ' + str(_tab) +
                           ' della tabella (settimane ' + str(_n_sett) + ')')
    _diverse = [r['nome'] for r in TABELLA
                if r['impronta_attesa'] != OSSERVATIVO[int(r['seed_mondo'])]['impronta_input_data']]
    if _diverse:
        raise RuntimeError('impronta attesa diversa da D0 in: ' + ', '.join(_diverse))
    _senza = [r['nome'] for r in TABELLA if abs(float(r.get('controllo_baseline') or 0) - 0.30) > 1e-9]
    if _senza:
        raise RuntimeError('run senza il controllo organico a f = 0,30: ' + ', '.join(_senza))
    shutil.rmtree(_mondo, ignore_errors=True)
    return ('settimane ' + str(_n_sett) + '; nodi per trimestre -> nodi ' +
            ', '.join(str(k) + '->' + str(v) for k, v in sorted(_ottenuti.items())) +
            ' = tabella (formula della CELLA 9 congelata, runner R8); impronta attesa = D0 e f = 0,30 in ' +
            str(len(TABELLA)) + ' run su ' + str(len(TABELLA)))


def _gate_disegno():
    """Cancello di fedelta' specifico di D13b: il controllo organico (lo stesso
    di D13) e i nodi (lo stesso di N1), uno dopo l'altro."""
    return 'controllo: ' + _gate_controllo() + ' | nodi: ' + _gate_nodi()
'''

CANCELLO_CELLA2 = """# ============================================================================
# D13b: IL CANCELLO DI REPLICA (paragrafo 2 della pre-registrazione)
# ============================================================================
# Il run 1 e' D13 a f = 0,30 sul mondo 101 rifatto a 12 nodi per trimestre: deve
# riprodurre la riga di D13 alla quarta cifra (rapporto_mediana 2,4593, pit 0,0,
# forbice 1,8321-3,1253, dentro 0, impronta 7eaa88ed1323). Nessuno degli 8 fit a
# 1 nodo parte finche' non l'ha fatto. Se l'ha mancata non parte mai, nemmeno al
# rilancio: la pipeline non sarebbe piu' quella di D13. Se il fit di replica e'
# morto senza una riga ok (errore tecnico), al rilancio si ritenta la replica.
NOME_REPLICA = 'D13b_k12_replica_f030_m0101'


def stato_cancello():
    run_r = RUN_PER_NOME[NOME_REPLICA]
    riga_r = righe_ok(csv_di(run_r)).get(NOME_REPLICA)
    if riga_r is None:
        return 'da_fare', None, None
    v_r = verifica_sicura(run_r, riga_r, leggi_impronte())
    return ('riuscita' if v_r['esito'] == 'ok' else 'fallita'), v_r, riga_r


def stampa_cancello(v_r, riga_r):
    oss = RUN_PER_NOME[NOME_REPLICA]['osservativo_atteso']
    print('CANCELLO DI REPLICA (run 1, D13 a f = 0,30, mondo 101, 12 nodi per trimestre):')
    print('  rapporto_mediana ' + str(riga_r.get('rapporto_mediana')) + ' (atteso ' +
          str(oss.get('rapporto_mediana')) + ', riga di D13) | pit ' + str(riga_r.get('pit')) + ' (atteso ' +
          str(oss.get('pit')) + ') | impronta_input_data ' + str(riga_r.get('impronta_input_data')) +
          ' (attesa ' + str(oss.get('impronta_input_data')) + ') | n_knots ' + str(riga_r.get('n_knots')) +
          ' | f ' + str(riga_r.get('controllo_baseline_f')))
    print('  esito: ' + v_r['esito'].upper() + ' - ' + str(v_r['messaggio']))


def ferma_cancello(v_r, riga_r):
    p = os.path.join(CARTELLA_DRIVE, 'ANOMALIA_CANCELLO_REPLICA.txt')
    with open(p, 'w', encoding='utf-8') as f:
        f.write('CANCELLO DI REPLICA NON RIUSCITO - ' + time.strftime('%Y-%m-%d %H:%M:%S') + '\\n\\n' +
                'rapporto_mediana ' + str(riga_r.get('rapporto_mediana')) + ' | pit ' + str(riga_r.get('pit')) +
                ' | impronta ' + str(riga_r.get('impronta_input_data')) + ' | n_knots ' +
                str(riga_r.get('n_knots')) + '\\nesito del controllo: ' + v_r['esito'] + '\\nmessaggio: ' +
                str(v_r['messaggio']) + '\\n\\nLa pipeline non riproduce la riga di D13: nessun fit a 1 nodo parte, '
                'ne' + A + ' ora ne' + A + ' al rilancio (pre-registrazione, paragrafo 2).\\n')
    print()
    print('!' * 72)
    print('CANCELLO DI REPLICA NON RIUSCITO: nessun altro fit parte (scritto ' + p + ')')
    print('!' * 72)
    raise SystemExit('CANCELLO DI REPLICA NON RIUSCITO: ' + str(v_r['messaggio'])[:300] +
                     '\\nNessun fit a 1 nodo parte. Riportalo in chat con le righe qui sopra.')


_st0, _v0, _r0 = stato_cancello()
if _st0 == 'fallita':
    stampa_cancello(_v0, _r0)
    ferma_cancello(_v0, _r0)
elif _st0 == 'riuscita':
    stampa_cancello(_v0, _r0)
    print('  -> replica gia' + A + ' riuscita in un lancio precedente: gli 8 fit possono partire.')

t_inizio = time.time()
durate = []
for run in SEQUENZA:
    if run['nome'] in fatti:
        print('run ' + str(run['n']) + ' ' + run['nome'] + ': gia' + A + ' registrato con esito ok, salto.')
        continue
    if run['nome'] != NOME_REPLICA:
        _st, _v_r, _riga_r = stato_cancello()
        if _st == 'da_fare':
            raise SystemExit('Il fit di replica non ha una riga ok (processo morto o errore tecnico): '
                             'nessun fit a 1 nodo parte. Esegui tutto di nuovo: si ritenta la replica, '
                             'e solo quella.')
        if _st == 'fallita':
            stampa_cancello(_v_r, _riga_r)
            ferma_cancello(_v_r, _riga_r)
"""


def costruisci():
    c1, c2 = cella1, cella2

    # --- testata, cartella, blob ------------------------------------------------
    c1 = sub(c1, TESTA_D13, TESTA_D13B, "testata")
    c1 = sub(c1, "CARTELLA_DRIVE = '/content/drive/MyDrive/MMM_griglia_D13'      ",
             "CARTELLA_DRIVE = '/content/drive/MyDrive/MMM_griglia_D13b_1nodo'", "cartella")
    c1 = sub(c1, """# run con le attese per riga, il file degli attesi, le pre-registrazioni e le
# impronte dei file media dichiarate nella pre-registrazione di D12.""",
             """# run con le attese per riga (nodi per trimestre, nodi, f = 0,30 e impronta di
# D0 dello stesso mondo), il file degli attesi, la pre-registrazione di D13b e
# le impronte dei file media di D12 (restano nel blob, qui non servono).""", "commento blob")
    j0 = c1.index("_BLOB = (\n")
    j1 = c1.index("\n)\n", j0) + len("\n)\n")
    c1 = c1[:j0] + blob_testo(blob_D13b()) + c1[j1:]

    # --- n_knots della RIGA, non di CONFIG (trappola 2 di N1) ---------------------
    c1 = sub(c1, "    attese = [('n_knots', CONFIG['n_knots']), ('keep', CONFIG['keep']),",
             "    # D13b: i nodi attesi sono quelli della RIGA (8 o 96), non la costante\n"
             "    # globale: con CONFIG['n_knots'] = 96 ogni run a 1 nodo sarebbe un'anomalia.\n"
             "    attese = [('n_knots', run['n_knots']), ('keep', CONFIG['keep']),",
             "trappola 2")

    # --- il cancello specifico: quello di D13 rinominato, piu' quello dei nodi ----
    g0 = c1.index(GATE_D13_INIZIO)
    g1 = c1.index(GATE_D13_FINE, g0) + len(GATE_D13_FINE)
    gate_d13 = c1[g0:g1]
    gate_ctrl = sub(gate_d13, "\n\ndef _gate_disegno():\n", "\n\ndef _gate_controllo():\n", "nome gate D13")
    c1 = c1[:g0] + gate_ctrl + GATE_NODI + c1[g1:]
    c1 = sub(c1, "            print('      D13       ' + _nota_disegno)",
             "            print('      D13b      ' + _nota_disegno)", "stampa gate")
    c1 = sub(c1, "            _problemi6.append('D13: ' + str(_e)[:250])\n"
                 "            print('      D13       ERRORE: ' + str(_e)[:200])",
             "            _problemi6.append('D13b: ' + str(_e)[:250])\n"
             "            print('      D13b      ERRORE: ' + str(_e)[:200])", "errore gate")

    # --- cella 2: i nodi dalla RIGA del run (trappola 1 di N1) ---------------------
    c2 = sub(c2, "         '--knots-per-quarter', str(CONFIG['knots_per_quarter']),",
             "         # D13b: i nodi dalla RIGA del run, non dalla costante globale: con\n"
             "         # CONFIG['knots_per_quarter'] tutti i 9 fit girerebbero a 12.\n"
             "         '--knots-per-quarter', str(run['knots_per_quarter']),",
             "trappola 1")
    c2 = sub(c2, "    print('  mondo ' + str(run['seed_mondo']) + ' | prior ' + run['prior_tipo'] +",
             "    print('  mondo ' + str(run['seed_mondo']) + ' | nodi per trimestre ' + str(run['knots_per_quarter']) +\n"
             "          ' (' + str(run['n_knots']) + ' nodi) | prior ' + run['prior_tipo'] +",
             "stampa nodi")

    # --- cella 2: il cancello di replica ------------------------------------------
    c2 = sub(c2, """t_inizio = time.time()
durate = []
for run in SEQUENZA:
    if run['nome'] in fatti:
        print('run ' + str(run['n']) + ' ' + run['nome'] + ': gia' + A + ' registrato con esito ok, salto.')
        continue
""", CANCELLO_CELLA2, "cancello prima dei run")
    c2 = sub(c2, """    if v['esito'] == 'anomalia':
        segnala_anomalia(run, v)
    elif v['esito'] == 'errore_tecnico':
        print('[ATTENZIONE] errore tecnico: proseguo, questo viene ritentato al rilancio.')
""", """    if v['esito'] == 'anomalia':
        segnala_anomalia(run, v)
    elif v['esito'] == 'errore_tecnico':
        print('[ATTENZIONE] errore tecnico: proseguo, questo viene ritentato al rilancio.')
    if run['nome'] == NOME_REPLICA:
        _st, _v_r, _riga_r = stato_cancello()
        if _st == 'riuscita':
            stampa_cancello(_v_r, _riga_r)
            print('  -> REPLICA RIUSCITA: partono gli 8 fit a 1 nodo per trimestre con f = 0,30.')
        elif _st == 'fallita':
            stampa_cancello(_v_r, _riga_r)
            ferma_cancello(_v_r, _riga_r)
        # 'da_fare' (nessuna riga ok): lo ferma il controllo prima del run successivo
""", "cancello dopo la replica")
    c2 = sub(c2, """print('2. Riporta in chat i riepiloghi qui sopra per intero. I rami si leggono SOLO sulle')
print('   pre-registrazioni approvate, dopo il commit dei risultati.')""",
             """print('2. Riporta in chat i riepiloghi qui sopra per intero. I rami si leggono SOLO sulle')
print('   pre-registrazioni approvate, dopo il commit dei risultati.')
print('3. I rami di D13b li stampa lo script, non una persona:')
print('   python analisi_D13b.py <cartella MMM_griglia_D13b_1nodo scaricata>')""", "da fare")
    return c1, c2


MD_D13B = """# D13b - la domanda organica osservata, con la baseline a 1 nodo per trimestre

**Autosufficiente.** Carica solo questo file e premi **Esegui tutto**. Quando compare il popup di Google Drive, autorizza l'accesso: e' l'unico momento in cui serve una persona.

**Prima di lanciare:** nel Drive usato deve esserci `/content/drive/MyDrive/MMM_copertura/copertura_risultati.csv` (lo studio osservativo del 13/9). Il controllo 7 del pre-volo lo legge e, se manca, si ferma.

**Runtime:** GPU T4. **Durata:** 9 fit, circa un'ora e mezza (i fit di N1 e D13 sono durati fra 9 e 15 minuti).

**Cosa fa.** Rifitta Meridian sui dati di D0 - gli otto mondi 42, 101-107, byte per byte - con **due cose insieme**: il controllo organico di D13 a f = 0,30 (`--controllo-baseline 0.3`, la stessa funzione del runner R8) e la baseline a **1 nodo per trimestre** (8 nodi), come il livello 1 di N1. Tutto il resto identico alla griglia: keep 2000, 4 catene, adapt 500, burnin 500, seme MCMC 42, revenue_per_kpi 40, prior LogNormal(0,2; 0,9), stagionalita' a 4 decimali. Generatore = main + A + G1..G4 + G6, impronta `8f86eb032d0113c0`; runner = **R8** con `--knots-per-quarter` preso **dalla riga di ogni run**.

**Il cancello di replica, prima di tutto.** Il run 1 e' D13 a f = 0,30 sul mondo 101 a 12 nodi per trimestre, cioe' la riga di D13 rifatta: deve dare `rapporto_mediana` 2,4593, `pit` 0,0, forbice 1,8321-3,1253 e impronta `7eaa88ed1323`. Se non li riproduce, il ciclo **si ferma** e nessun altro fit parte, nemmeno al rilancio.

**Ordine:** replica; poi gli 8 mondi a 1 nodo per trimestre, il 42 per primo.

**Scrive in `MMM_griglia_D13b_1nodo`**, cartella nuova: le cartelle dei run precedenti non vengono toccate.

**Alla fine:** scarica la cartella per intera. I rami li stampa `analisi_D13b.py` sulla cartella scaricata, e si leggono solo sulla pre-registrazione `PREREGISTRAZIONE_D13b_baseline_osservata_1nodo.md`.
"""

if __name__ == "__main__":
    os.makedirs(USCITA, exist_ok=True)
    c1, c2 = costruisci()
    compile(c1, "cella1", "exec")
    compile(c2, "cella2", "exec")
    nb = {
        "nbformat": nb13["nbformat"], "nbformat_minor": nb13["nbformat_minor"],
        "metadata": json.loads(json.dumps(nb13["metadata"])),
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": MD_D13B.splitlines(keepends=True)},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
             "source": c1.splitlines(keepends=True)},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
             "source": c2.splitlines(keepends=True)},
        ],
    }
    fuori = os.path.join(USCITA, NOME_NB)
    for vietato in ("colab_griglia.ipynb", "colab_griglia_D10.ipynb", "colab_griglia_D12.ipynb",
                    "colab_griglia_D13.ipynb", "colab_griglia_N1_nodi.ipynb", "colab_end_to_end.ipynb"):
        if os.path.basename(fuori) == vietato:
            raise SystemExit("non si scrive mai sopra " + vietato)
    with open(fuori, "w", encoding="utf-8", newline="\n") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("D13b ->", fuori, os.path.getsize(fuori), "byte, cella1", len(c1), "caratteri, cella2", len(c2),
          "| sha256", sha_lf(fuori))
