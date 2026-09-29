# Costruisce colab_griglia_D12.ipynb e colab_griglia_D13.ipynb a partire dal
# notebook congelato colab_griglia_D10.ipynb: stesso impianto, blob nuovo
# (G6 + runner R8 + tabelle + pre-registrazioni) e le sostituzioni minime
# nelle celle 1 e 2.
#
# ADATTATO il 22/9/2026 al clone del pacchetto (trappola 0 del prompt N1).
# L'originale, controlli_fedelta_D12_D13/fai_notebook.py, e' stato scritto in
# una cartella di lavoro su Windows con percorsi fissi. Qui cambiano SOLO gli
# ingressi e l'uscita, e ogni ingresso e' un file del repository:
#   REPO               -> la cartella che contiene questa cartella
#   nb/D10_blob.json   -> il dizionario in base64 nella variabile _BLOB della
#                         cella 1 di colab_griglia_D10.ipynb, decodificato qui
#   G6.diff            -> patch_G6_generatore_blackout.diff
#   runner_R8.py       -> runner_R8_griglia.py
#   uscita             -> una cartella A PARTE, passata come argomento: mai
#                         sopra i notebook committati
# Prova che l'adattamento non cambia nulla: i due notebook rigenerati devono
# avere lo stesso sha256 di `git show HEAD:<file> | sha256sum`, cioe'
# de2c729914c706c2... (D12) e 3f17879db07d22f8... (D13). Lo script lo verifica
# da se' e si ferma se non tornano.
import base64
import csv
import hashlib
import io
import json
import os
import sys
import textwrap

QUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(QUI)
if len(sys.argv) < 2:
    raise SystemExit("uso: fai_notebook_adattato.py <cartella di uscita, mai il repository>")
USCITA = os.path.abspath(sys.argv[1])
if USCITA == os.path.abspath(REPO):
    raise SystemExit("la cartella di uscita e' il repository: i notebook committati non si toccano")
SHA_ATTESI = {"D12": "de2c729914c706c20e26a02ae324ebbef081b48db657003bb1b26e9e29887def",
              "D13": "3f17879db07d22f80d7bbcdd6c69a10e9414953e4f49fddcce86a58ce6999725"}
NB_D10 = os.path.join(REPO, "colab_griglia_D10.ipynb")
A = chr(39)

CANALI = ["Google Ads", "Meta Ads", "LinkedIn Ads", "Indeed", "Subito Lavoro",
          "Jooble", "Altre job board"]
MONDI = [42, 101, 102, 103, 104, 105, 106, 107]
DOSE_D12 = 23.39
LIVELLI = [0.30, 0.60, 0.90]

# Impronte sha256 dei sette file media, calcolate sul contenuto NORMALIZZATO a
# LF. La normalizzazione non e' un dettaglio: il 21/9/2026 il pre-volo di D12
# su Colab si e' fermato perche' le impronte erano state calcolate su Windows,
# dove pandas scrive CRLF, mentre Colab e' Linux e scrive LF. I file erano
# identici nel contenuto - stesse colonne, stessi numeri, stessi conteggi di
# differenza rispetto al mondo base - e differivano di esattamente (righe + 1)
# byte ciascuno, cioe' di un carattere per riga piu' l'intestazione. Normalizzare
# rende l'impronta indipendente dal sistema senza renderla piu' permissiva.
IMPRONTE_MEDIA = {
    42: ("c3cd1b7bfd480b76", "dccc5657d59142ca"),
    101: ("3bf9db63e3f482a2", "6c982e5614701440"),
    102: ("5e2beb5020b72e71", "553638e8f2993432"),
    103: ("0d4031f2b374c056", "cc3c2f60385b11d9"),
    104: ("336b7304ad73e7df", "1f17620b41329b4f"),
    105: ("ebcd9e7068fede0d", "4484cefbfc007323"),
    106: ("da6ca34ef537a54c", "a4127964e77edf20"),
    107: ("c1de36b8be209b90", "b77671ce04ea3c4d"),
}

nb10 = json.load(open(NB_D10, encoding="utf-8"))
cella1 = "".join(nb10["cells"][1]["source"])
cella2 = "".join(nb10["cells"][2]["source"])
# nb/D10_blob.json: il _BLOB della cella 1 del notebook D10, decodificato
_i0 = cella1.index("_BLOB = (\n")
_i1 = cella1.index("\n)\n", _i0)
blob10 = json.loads(base64.b64decode("".join(
    r.strip().strip(",").strip("'") for r in cella1[_i0:_i1].splitlines()[1:])).decode("utf-8"))

G6 = open(os.path.join(REPO, "patch_G6_generatore_blackout.diff"), encoding="utf-8").read()
RUNNER_R8 = open(os.path.join(REPO, "runner_R8_griglia.py"), encoding="utf-8").read()
SHA_G6 = "8f86eb032d0113c0"

PREREG = {}
for nome in ("PREREGISTRAZIONE_D12_blackout_totale.md",
             "PREREGISTRAZIONE_D13_baseline_osservata.md"):
    PREREG[nome] = open(os.path.join(REPO, "preregistrazioni", nome),
                        encoding="utf-8").read()

COL_ATTESI = ["n", "codice", "nome", "disegno", "seed_mondo", "parametri_disegno",
              "canali_trattati", "dose_per_canale", "controllo_baseline", "regola",
              "atteso", "banda_min_pct", "banda_max_pct", "anomalia_min_pct",
              "anomalia_max_pct", "impronta_attesa", "riduzione_attesa_pct",
              "n_knots", "keep", "n_chains", "adapt", "burnin", "seed_mcmc",
              "revenue_per_kpi", "prior_tipo", "prior_sigma", "prior_mu",
              "decimali_stagionalita", "csv"]


def riga_base(n, codice, nome, disegno, seme, csv_file, prereg):
    return {"codice": codice, "disegno": disegno, "seed_mondo": seme, "nome": nome,
            "parametri_disegno": "", "canali_trattati": "", "dose_per_canale": {},
            "controllo_baseline": None, "regola": "prima_misura", "atteso": None,
            "banda_min_pct": None, "banda_max_pct": None, "anomalia_min_pct": None,
            "anomalia_max_pct": None, "impronta_attesa": "", "riduzione_attesa": None,
            "prior_tipo": "riferimento", "prior_sigma": 0.9, "prior_mu": 0.2,
            "osservativo_atteso": {}, "n": n, "csv": csv_file, "prereg": prereg,
            "attivo_default": True}


def tabella_D12():
    csv_file = "griglia_D12_blackout_totale.csv"
    prereg = "PREREGISTRAZIONE_D12_blackout_totale.md"
    fuori = []
    for i, seme in enumerate(MONDI):
        r = riga_base(i + 1, "D12", "D12_blackout_m%04d" % seme, "blackout",
                      seme, csv_file, prereg)
        r["canali_trattati"] = ";".join(CANALI)
        r["dose_per_canale"] = {ch: DOSE_D12 for ch in CANALI}
        r["riduzione_attesa"] = -100.0
        fuori.append(r)
    return fuori


def tabella_D13():
    csv_file = "griglia_D13_baseline_osservata.csv"
    prereg = "PREREGISTRAZIONE_D13_baseline_osservata.md"
    fuori, n = [], 0
    for f in LIVELLI:
        for seme in MONDI:
            n += 1
            nome = "D13_baseline_f%03d_m%04d" % (round(f * 100), seme)
            r = riga_base(n, "D13", nome, "base", seme, csv_file, prereg)
            r["controllo_baseline"] = f
            # i dati media non sono toccati: l'impronta dell'InputData deve
            # essere quella di D0 dello stesso mondo, che sta nel registro
            # della griglia. E' il controllo 2 della pre-registrazione, fatto
            # a ogni run e non una volta sola.
            r["impronta_attesa"] = blob10["osservativo"][str(seme)]["impronta_input_data"]
            fuori.append(r)
    return fuori


def attesi_csv(tabella):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COL_ATTESI, extrasaction="ignore")
    w.writeheader()
    for r in tabella:
        w.writerow({
            "n": r["n"], "codice": r["codice"], "nome": r["nome"],
            "disegno": r["disegno"], "seed_mondo": r["seed_mondo"],
            "parametri_disegno": r["parametri_disegno"],
            "canali_trattati": r["canali_trattati"],
            "dose_per_canale": ";".join(k + "=" + str(v) for k, v in r["dose_per_canale"].items()),
            "controllo_baseline": "" if r["controllo_baseline"] is None else r["controllo_baseline"],
            "regola": r["regola"],
            "atteso": "" if r["atteso"] is None else r["atteso"],
            "banda_min_pct": "", "banda_max_pct": "",
            "anomalia_min_pct": "", "anomalia_max_pct": "",
            "impronta_attesa": r["impronta_attesa"],
            "riduzione_attesa_pct": "" if r["riduzione_attesa"] is None else r["riduzione_attesa"],
            "n_knots": 96, "keep": 2000, "n_chains": 4, "adapt": 500, "burnin": 500,
            "seed_mcmc": 42, "revenue_per_kpi": 40.0, "prior_tipo": r["prior_tipo"],
            "prior_sigma": r["prior_sigma"], "prior_mu": r["prior_mu"],
            "decimali_stagionalita": 4, "csv": r["csv"]})
    return buf.getvalue()


def blob_per(codice):
    if codice == "D12":
        tab = tabella_D12()
        disegni = [["D12", "blackout totale geografico x 8 mondi",
                    "griglia_D12_blackout_totale.csv",
                    "PREREGISTRAZIONE_D12_blackout_totale.md", True]]
        prereg = {"PREREGISTRAZIONE_D12_blackout_totale.md":
                  PREREG["PREREGISTRAZIONE_D12_blackout_totale.md"]}
    else:
        tab = tabella_D13()
        disegni = [["D13", "baseline parzialmente osservata, 3 livelli x 8 mondi",
                    "griglia_D13_baseline_osservata.csv",
                    "PREREGISTRAZIONE_D13_baseline_osservata.md", True]]
        prereg = {"PREREGISTRAZIONE_D13_baseline_osservata.md":
                  PREREG["PREREGISTRAZIONE_D13_baseline_osservata.md"]}
    d = dict(blob10)
    d["diff_generatore"] = dict(blob10["diff_generatore"])
    d["diff_generatore"]["G6"] = G6
    d["generatore_sha"] = SHA_G6
    d["runner"] = RUNNER_R8
    d["tabella"] = tab
    d["disegni"] = disegni
    d["attesi_csv"] = attesi_csv(tab)
    d["preregistrazioni"] = prereg
    d["impronte_media_attese"] = {str(k): {"base": v[0], "blackout": v[1]}
                                  for k, v in IMPRONTE_MEDIA.items()}
    return d


def blob_testo(d):
    b = base64.b64encode(json.dumps(d, ensure_ascii=False).encode("utf-8")).decode("ascii")
    pezzi = [b[i:i + 100] for i in range(0, len(b), 100)]
    return "_BLOB = (\n" + "".join("    '" + p + "',\n" for p in pezzi) + ")\n"


# ---------------------------------------------------------------------------
# le sostituzioni sulla cella 1
# ---------------------------------------------------------------------------
def sub(src, vecchio, nuovo, etichetta):
    n = src.count(vecchio)
    if n != 1:
        raise SystemExit("notebook, sostituzione '%s': trovata %d volte" % (etichetta, n))
    return src.replace(vecchio, nuovo)


TESTA_D12 = """# D12: il BLACKOUT TOTALE geografico, otto mondi. Unico disegno di questo
# notebook. Tutti e sette i canali a spesa esattamente zero nelle stesse
# cinque regioni (una per strato di popolazione: Lazio, Emilia-Romagna,
# Calabria, Abruzzo, Basilicata) per due blocchi di otto settimane (9-16 e
# 53-60), e la spesa tolta NON viene ridistribuita. E' l'unico disegno della
# griglia che muove il LIVELLO dei media e non solo la loro distribuzione.
# beta e la mezza saturazione ec restano quelli del mondo base dello stesso
# seme (patch G6): senza, la ricalibrazione del passo 7 del generatore
# riporterebbe il contributo vero al suo valore di sempre e il disegno
# misurerebbe zero. La regola di lettura sta nel paragrafo 4 della
# pre-registrazione, fissata prima. La griglia e i notebook D10 e D11 non si
# toccano: questo scrive altrove."""

TESTA_D13 = """# D13: la BASELINE PARZIALMENTE OSSERVATA, tre livelli x otto mondi.
# I dati media non si toccano: il mondo e' quello base, byte per byte, e si
# aggiunge UNA variabile di controllo costruita dalle candidature organiche
# vere, c = f x organico_vero x exp(N(0, 0,15)), con f = 0,30 / 0,60 / 0,90 e
# rng dedicato default_rng(seme + 31). 24 fit. Serve a sapere quanta domanda
# organica bisogna saper contare perche' l'errore si dimezzi. CAVEAT, da
# ripetere accanto a ogni cifra: il controllo e' costruito dalla baseline
# VERA, quindi misura il caso piu' favorevole possibile ed e' un limite
# SUPERIORE di quello che un dato reale potrebbe dare. La regola di lettura
# sta nel paragrafo 4 della pre-registrazione, fissata prima."""

GATE_D12 = '''

def _gate_disegno():
    """Cancello di fedelta' specifico di D12, sul mondo 42: le impronte dei
    sette file media del mondo blackout devono essere quelle dichiarate nella
    pre-registrazione (controllo 5), nelle 80 celle trattate non deve esserci
    NESSUNA riga (spesa zero = nessuna riga, regola gia' della base), e il
    JSON deve dire che beta viene dal mondo base (quota vera del mondo base
    18,5%) e quanto il disegno e' costato."""
    _g = subprocess.run([sys.executable, GEN, '--seed-mondo', '42', '--blackout'],
                        cwd=REPO, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if _g.returncode != 0:
        raise RuntimeError('generatore --blackout fallito: ' + (_g.stderr or _g.stdout)[-300:])
    _m = os.path.join(REPO, 'dati_simulati_mondi', 'mondo_0042_blackout', 'modello')
    _v = os.path.join(REPO, 'dati_simulati_mondi', 'mondo_0042_blackout', 'verita')
    _nomi = ['google_ads_settimanale.csv', 'meta_ads_settimanale.csv',
             'linkedin_ads_settimanale.csv', 'indeed_settimanale.csv',
             'subito_lavoro_settimanale.csv', 'jooble_settimanale.csv',
             'altre_job_board_settimanale.csv']
    _h = hashlib.sha256()
    for _n in _nomi:
        # NORMALIZZATO A LF: il fine riga dipende dal sistema operativo (CRLF su
        # Windows, LF su Linux) e non e' un dato. Senza questa riga l'impronta
        # calcolata su Windows non torna su Colab: e' successo il 21/9/2026 e
        # il cancello si e' fermato, correttamente, su una differenza che non
        # era nei numeri.
        _h.update(open(os.path.join(_m, _n), 'rb').read().replace(bytes([13, 10]), bytes([10])))
    _imp = _h.hexdigest()[:16]
    _atteso = _dati['impronte_media_attese']['42']['blackout']
    if _imp != _atteso:
        raise RuntimeError('impronta dei file media del mondo 42 blackout ' + _imp +
                           ' invece di ' + _atteso + ' della pre-registrazione')
    _j = json.load(open(os.path.join(_v, 'parametri_generazione.json'), encoding='utf-8'))
    _sc = _j.get('scenario_blackout') or {}
    if not _sc:
        raise RuntimeError('il JSON non ha scenario_blackout: il generatore non e' + A + ' quello con G6')
    if abs(float(_sc['quota_media_vera_mondo_base_pct']) - 18.5) > 1e-9:
        raise RuntimeError('quota vera del mondo base ' + str(_sc['quota_media_vera_mondo_base_pct']) +
                           ' invece di 18,5: beta non e' + A + ' quello del mondo base')
    if not 17.5 <= float(_sc['quota_media_vera_di_questo_mondo_pct']) < 18.5:
        raise RuntimeError('quota vera del mondo blackout ' +
                           str(_sc['quota_media_vera_di_questo_mondo_pct']) +
                           ': con beta fisso deve SCENDERE sotto 18,5')
    _reg = set(_sc['regioni_trattate'])
    _bl = [tuple(b) for b in _sc['blocchi_1based_inclusivi']]
    _sett = sorted({r['settimana'] for r in csv.DictReader(
        open(os.path.join(_m, 'candidature_settimanali.csv'), newline='', encoding='utf-8'))})
    _tratt = set()
    for _a, _b in _bl:
        _tratt |= set(_sett[_a - 1:_b])
    _righe = 0
    for _n in _nomi:
        with open(os.path.join(_m, _n), newline='', encoding='utf-8') as _f:
            for _r in csv.DictReader(_f):
                if _r['settimana'] in _tratt and _r['regione'] in _reg:
                    _righe += 1
    if _righe:
        raise RuntimeError(str(_righe) + ' righe di spesa nelle celle trattate: il blackout non e' + A +
                           ' totale')
    _costo = _sc['costo_del_disegno']
    shutil.rmtree(os.path.join(REPO, 'dati_simulati_mondi', 'mondo_0042_blackout'),
                  ignore_errors=True)
    return ('mondo 42 blackout: impronta ' + _imp + ' = pre-registrazione; 0 righe nelle 80 celle '
            'trattate; quota vera ' + str(_sc['quota_media_vera_di_questo_mondo_pct']) + '% (base 18,5%); '
            'costo ' + str(_costo['candidature_vere_perse']) + ' candidature vere e ' +
            str(_sc['spesa_tolta_totale_eur']) + ' EUR di spesa')
'''

GATE_D13 = '''

def _gate_disegno():
    """Cancello di fedelta' specifico di D13, sul mondo 42: costruito il
    controllo con f = 0,60 con la funzione DEL RUNNER (non una copia), i
    dodici file dei dati devono restare identici byte per byte, il file nuovo
    deve avere la colonna dichiarata, e il rapporto e la correlazione col vero
    devono stare nelle bande della pre-registrazione."""
    import importlib.util as _ilu
    import numpy as _np_g
    import pandas as _pd_g
    _g = subprocess.run([sys.executable, GEN, '--seed-mondo', '42'], cwd=REPO,
                        capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if _g.returncode != 0:
        raise RuntimeError('generatore fallito: ' + (_g.stderr or _g.stdout)[-300:])
    _mondo = os.path.join(REPO, 'dati_simulati_mondi', 'mondo_0042')
    _m = os.path.join(_mondo, 'modello')
    _prima = {_n: open(os.path.join(_m, _n), 'rb').read() for _n in sorted(os.listdir(_m))}
    _spec = _ilu.spec_from_file_location('_runner_r8', RUNNER)
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _col0, _rho0, _p0 = _mod.scrivi_controllo_baseline(_mondo, _m, 42, 0.0, _np_g, _pd_g)
    if _col0 or os.path.exists(os.path.join(_m, 'domanda_organica_osservata.csv')):
        raise RuntimeError('con f = 0 il runner ha scritto qualcosa: il run non sarebbe D0')
    _col, _rho, _p = _mod.scrivi_controllo_baseline(_mondo, _m, 42, 0.60, _np_g, _pd_g)
    _dopo = {_n: open(os.path.join(_m, _n), 'rb').read() for _n in sorted(os.listdir(_m))
             if _n in _prima}
    _diversi = [_n for _n in _prima if _prima[_n] != _dopo.get(_n)]
    if _diversi:
        raise RuntimeError('il controllo ha modificato i dati del mondo: ' + ', '.join(_diversi))
    if _col != 'domanda_organica_osservata':
        raise RuntimeError('colonna di controllo inattesa: ' + str(_col))
    _org = _pd_g.read_csv(os.path.join(_mondo, 'verita', 'candidature_organiche.csv'))
    _c = _pd_g.read_csv(_p)[_col].to_numpy(float)
    _vera = _org['candidature_organiche_vere'].to_numpy(float)
    _rap = float(_c.sum() / _vera.sum())
    if not 0.60 <= _rap <= 0.61:
        raise RuntimeError('rapporto controllo/baseline vera ' + str(round(_rap, 4)) +
                           ' fuori da 0,600-0,610 della pre-registrazione')
    if not 0.96 <= float(_rho) <= 0.99:
        raise RuntimeError('correlazione col vero ' + str(_rho) + ' fuori da 0,96-0,99')
    shutil.rmtree(_mondo, ignore_errors=True)
    return ('mondo 42, f = 0,60: 12 file su 12 identici, colonna ' + _col +
            ', rapporto ' + str(round(_rap, 4)) + ', correlazione col vero ' + str(_rho) +
            '; con f = 0 nessun file scritto')
'''


def costruisci(codice):
    c1 = cella1
    c2 = cella2

    # --- testata e costanti -------------------------------------------------
    c1 = sub(c1, """# D10: il calendario a QUATTRO giri, otto mondi. Unico disegno di questo
# notebook. Rispetto a D2 cambia una cosa sola: i giri, da 2 a 4 (32 settimane
# spente per canale invece di 16, quattro transizioni invece di due). Stessi
# gruppi di regioni, stessa lunghezza del blocco, stesso sfasamento, stessa
# rotazione. Serve a sapere se i 7 punti che restano dopo D2 sono poca dose o
# la baseline: la regola sta nel paragrafo 5 della pre-registrazione, fissata
# prima. La griglia a nove disegni resta in colab_griglia.ipynb, che non si
# tocca, e scrive in MMM_griglia: questo notebook scrive altrove.
DISEGNI_ATTIVI = ['D10']""",
              (TESTA_D12 if codice == "D12" else TESTA_D13) +
              "\nDISEGNI_ATTIVI = ['" + codice + "']", "testata")

    c1 = sub(c1, "CARTELLA_DRIVE = '/content/drive/MyDrive/MMM_griglia_D10'      "
                 "# NUOVA: MMM_griglia non si tocca",
             "CARTELLA_DRIVE = '/content/drive/MyDrive/MMM_griglia_" + codice + "'      "
             "# NUOVA: le cartelle dei run precedenti non si toccano", "cartella")

    c1 = sub(c1, """# Il materiale incorporato: le sostituzioni A del generatore (--seed-mondo, 4
# decimali, --sanita), le tre patch G1/G2/G3 come diff unificati, l'impronta
# sha256 del generatore che ne risulta, il runner R5 completo, la tabella dei
# run con le attese per riga, il file degli attesi, le pre-registrazioni.""",
             """# Il materiale incorporato: le sostituzioni A del generatore (--seed-mondo, 4
# decimali, --sanita), le patch G1/G2/G3/G4/G6 come diff unificati, l'impronta
# sha256 del generatore che ne risulta, il runner R8 completo, la tabella dei
# run con le attese per riga, il file degli attesi, le pre-registrazioni e le
# impronte dei file media dichiarate nella pre-registrazione di D12.""",
             "commento blob")

    # --- il blob ------------------------------------------------------------
    i0 = c1.index("_BLOB = (\n")
    i1 = c1.index("\n)\n", i0) + len("\n)\n")
    c1 = c1[:i0] + blob_testo(blob_per(codice)) + c1[i1:]

    # --- patch e autotest ---------------------------------------------------
    c1 = sub(c1, "for _nome_diff in ('G1', 'G2', 'G3', 'G4'):",
             "for _nome_diff in ('G1', 'G2', 'G3', 'G4', 'G6'):", "elenco diff")
    c1 = sub(c1, "raise RuntimeError('il generatore ricostruito da main + A + G1 + G2 + G3 ha impronta ' + _sha +",
             "raise RuntimeError('il generatore ricostruito da main + A + G1..G4 + G6 ha impronta ' + _sha +",
             "messaggio sha")
    c1 = sub(c1, "print('      generatore: ' + str(len(_dati['patches_generatore'])) + ' sostituzioni A + 4 diff a fuzz 0 '",
             "print('      generatore: ' + str(len(_dati['patches_generatore'])) + ' sostituzioni A + 5 diff a fuzz 0 '",
             "stampa generatore")
    c1 = sub(c1, "print(' 5. repo, patch del generatore (A + G1 + G2 + G3 + G4), runner R7')",
             "print(' 5. repo, patch del generatore (A + G1 + G2 + G3 + G4 + G6), runner R8')",
             "titolo controllo 5")
    c1 = sub(c1, "print('      runner R7 scritto: ' + RUNNER)",
             "print('      runner R8 scritto: ' + RUNNER)", "stampa runner")
    c1 = sub(c1, """                  '--geo-sfalsato', '--calendario', '--calendario-rotazione', '--calendario-giri',
                  '--casuale2', '--suffisso-mondo'):""",
             """                  '--geo-sfalsato', '--calendario', '--calendario-rotazione', '--calendario-giri',
                  '--casuale2', '--suffisso-mondo', '--blackout'):""",
             "autotest generatore")
    c1 = sub(c1, """    for _flag in ('--disegno', '--parametri-disegno', '--knots-per-quarter', '--prior', '--prior-mu',
                  '--prior-sigma', 'ancorato-benchmark', '--nome-run'):""",
             """    for _flag in ('--disegno', '--parametri-disegno', '--knots-per-quarter', '--prior', '--prior-mu',
                  '--prior-sigma', 'ancorato-benchmark', '--nome-run', '--controllo-baseline',
                  'blackout'):""",
             "autotest runner")
    c1 = sub(c1, """    for _pezzo in ('def leggi_disegno', 'def parametri_disegno', 'spesa_ridistribuita_eur',
                   'def roas_benchmark', 'prior_mu_per_canale',
                   'REVENUE_PER_KPI_PRESENTE', 'stdin=subprocess.DEVNULL'):""",
             """    for _pezzo in ('def leggi_disegno', 'def parametri_disegno', 'spesa_ridistribuita_eur',
                   'def roas_benchmark', 'prior_mu_per_canale', 'def scrivi_controllo_baseline',
                   'def leggi_costo_blackout', 'spesa_tolta_eur',
                   'REVENUE_PER_KPI_PRESENTE', 'stdin=subprocess.DEVNULL'):""",
             "autotest pezzi")
    c1 = sub(c1, "_ok5 = _registra(5, 'repo e patch', True, 'generatore = main + A + G1 + G2 + G3 + G4 (sha verificato), '\n"
                 "                     'runner R7 (--disegno, --parametri-disegno, prior parametrico, giri); autotest passato')",
             "_ok5 = _registra(5, 'repo e patch', True, 'generatore = main + A + G1..G4 + G6 (sha verificato), '\n"
             "                     'runner R8 (--disegno blackout, --controllo-baseline); autotest passato')",
             "esito controllo 5")

    # --- controlli nella verifica di una riga -------------------------------
    c1 = sub(c1, """    imp = str(riga.get('impronta_input_data'))
    if run['impronta_attesa']:""",
             """    # D12: la verita' di questo mondo deve essere SCESA sotto 18,5 (beta del
    # mondo base), e il costo del disegno deve essere positivo. Se beta fosse
    # stato ricalibrato, la quota vera tornerebbe 18,5 e il run non misurerebbe
    # niente: questo controllo lo intercetta riga per riga.
    if run['disegno'] == 'blackout':
        _qb = _numero(riga.get('quota_media_vera_base_pct'))
        if _qb is None or abs(_qb - 18.5) > 0.001:
            p.append('quota vera del mondo base=' + str(riga.get('quota_media_vera_base_pct')) +
                     ' invece di 18,5: beta non viene dal mondo base')
        _qv = _numero(riga.get('quota_media_vera_pct'))
        if _qv is None or not (17.6 <= _qv <= 18.3):
            p.append('quota vera di questo mondo=' + str(riga.get('quota_media_vera_pct')) +
                     ' fuori da 17,6-18,3: con beta fisso la verita' + A + ' deve scendere sotto 18,5')
        _pe = _numero(riga.get('candidature_vere_perse'))
        if _pe is None or _pe <= 0:
            p.append('candidature vere perse=' + str(riga.get('candidature_vere_perse')) +
                     ': il blackout non ha tolto niente')
    # D13: il livello di f e la presenza effettiva del controllo nel modello.
    if run.get('controllo_baseline'):
        _f = _numero(riga.get('controllo_baseline_f'))
        if _f is None or abs(_f - float(run['controllo_baseline'])) > 1e-9:
            p.append('controllo_baseline_f=' + str(riga.get('controllo_baseline_f')) +
                     ' invece di ' + str(run['controllo_baseline']))
        _cn = str(riga.get('controlli_nel_modello') or '')
        if 'ctrl_domanda_organica_osservata' not in _cn:
            p.append('il controllo di D13 non e' + A + ' fra i controlli del modello: ' + _cn)
        if str(riga.get('controllo_baseline_colonna')) != 'domanda_organica_osservata':
            p.append('colonna del controllo=' + str(riga.get('controllo_baseline_colonna')))
    imp = str(riga.get('impronta_input_data'))
    if run['impronta_attesa']:""",
             "controlli di riga")

    # --- il cancello di fedelta' specifico del disegno ----------------------
    c1 = sub(c1, """_ok6 = False
if not _ok5:""",
             (GATE_D12 if codice == "D12" else GATE_D13) + """

_ok6 = False
if not _ok5:""", "definizione gate")

    c1 = sub(c1, """    if _problemi6:
        _ok6 = _registra(6, 'fedelta' + A, False, '; '.join(_problemi6)[:500],
                         'Il generatore patchato non riproduce piu' + A + ' i dataset della tesi: '
                         'NESSUN disegno nuovo parte con un generatore non fedele. Riportalo in chat.')
    else:
        _ok6 = _registra(6, 'fedelta' + A, True, '5 dataset del mondo 42 rigenerati identici ai committati '
                         '(base, sanita, pause2, casuale2, geo); percorso senza flag invariato')""",
             """    _nota_disegno = ''
    if not _problemi6:
        try:
            _nota_disegno = _gate_disegno()
            print('      """ + codice + """       ' + _nota_disegno)
        except Exception as _e:
            _problemi6.append('""" + codice + """: ' + str(_e)[:250])
            print('      """ + codice + """       ERRORE: ' + str(_e)[:200])
    if _problemi6:
        _ok6 = _registra(6, 'fedelta' + A, False, '; '.join(_problemi6)[:500],
                         'Il generatore patchato non riproduce piu' + A + ' i dataset della tesi, '
                         'oppure il disegno nuovo non e' + A + ' quello dichiarato: NESSUN fit parte. '
                         'Riportalo in chat.')
    else:
        _ok6 = _registra(6, 'fedelta' + A, True, '5 dataset del mondo 42 rigenerati identici ai committati '
                         '(base, sanita, pause2, casuale2, geo); percorso senza flag invariato; ' +
                         _nota_disegno)""",
             "uso del gate")

    # --- cella 2: il flag del controllo -------------------------------------
    c2 = sub(c2, """    if run['parametri_disegno']:
        c += ['--parametri-disegno', run['parametri_disegno']]""",
             """    if run['parametri_disegno']:
        c += ['--parametri-disegno', run['parametri_disegno']]
    # D13: il livello del controllo costruito dalla baseline vera. Assente o 0
    # = nessun file scritto, run identico a D0.
    if run.get('controllo_baseline'):
        c += ['--controllo-baseline', str(run['controllo_baseline'])]""",
             "flag controllo in comando()")

    c2 = sub(c2, """          ' | trattati: ' + (run['canali_trattati'] or '-') +""",
             """          ' | trattati: ' + (run['canali_trattati'] or '-') +
          (' | controllo baseline f=' + str(run['controllo_baseline'])
           if run.get('controllo_baseline') else '') +""",
             "stampa controllo")

    return c1, c2


MD_D12 = """# D12 - il blackout totale geografico, otto mondi

**Autosufficiente.** Carica solo questo file e premi **Esegui tutto**. Quando compare il popup di Google Drive, autorizza l'accesso: e' l'unico momento in cui serve una persona.

**Runtime:** GPU T4. **Durata:** 8 fit, circa un'ora e mezza.

**Cosa fa.** Rigenera gli otto mondi dello studio di copertura (semi 42, 101-107) con il blackout totale - tutti e sette i canali a spesa esattamente zero in cinque regioni fisse (Lazio, Emilia-Romagna, Calabria, Abruzzo, Basilicata: una per strato di popolazione, 23,39% della popolazione) per due blocchi di otto settimane (9-16 e 53-60) - e li fitta con lo stesso runner e la stessa configurazione di tutta la griglia (96 nodi, keep 2000, 4 catene, seme MCMC 42, revenue_per_kpi 40, prior LogNormal(0,2; 0,9)). Generatore = main del repo pubblico + patch A + G1 + G2 + G3 + G4 + **G6** (`--blackout`), impronta `8f86eb032d0113c0`; runner = R7 + **R8** (disegno `blackout`, `--controllo-baseline`).

**Che cosa lo distingue da tutti i disegni precedenti.** La spesa tolta **non viene ridistribuita**: la spesa nazionale settimanale scende (del 23,65% nelle sedici settimane trattate sul mondo 42, del 3,2-3,7% sul biennio). Nessuno degli undici disegni gia' eseguiti cambia *quanta* pubblicita' c'e': cambiano solo dove e quando. D12 e' l'unico che muove il livello.

**Il punto tecnico decisivo.** Al passo 7 il generatore ricalibra `beta` per centrare la quota di contributo dichiarata: con meno spesa il contributo vero resterebbe **identico per costruzione** e il disegno misurerebbe zero. La patch G6 tiene `beta` e la mezza saturazione `ec` fissi a quelli del mondo base dello stesso seme. Verificato prima dei fit: senza G6 il contributo vero non si muove di una cifra; con G6 scende del 3,4%. Conseguenza da dichiarare accanto a ogni cifra: la verita' di questi mondi e' la superficie di risposta implicita nei parametri veri del mondo base.

**Attenzione alla metrica.** La quota vera dei media in questi mondi **non e' 18,5%**: vale fra 17,94% e 18,04%. `E` si calcola contro la quota vera di questo mondo, che il runner scrive nella colonna `quota_media_vera_pct`.

**Il costo.** Il blackout costa davvero: fra 114.433 e 140.428 EUR di spesa non fatta e fra 4.841 e 5.842 candidature vere non arrivate, a seconda del mondo. Il runner lo scrive riga per riga nelle colonne `candidature_vere_perse` e `quota_media_vera_base_pct`.

**Scrive in `MMM_griglia_D12`**, cartella nuova: `MMM_griglia`, `MMM_griglia_D10` e le altre non vengono toccate.

**Alla fine:** scarica la cartella per intera e riporta i riepiloghi in chat. Il ramo si legge solo sulla pre-registrazione `PREREGISTRAZIONE_D12_blackout_totale.md`, dopo il commit dei risultati.
"""

MD_D13 = """# D13 - la baseline parzialmente osservata, tre livelli per otto mondi

**Autosufficiente.** Carica solo questo file e premi **Esegui tutto**. Quando compare il popup di Google Drive, autorizza l'accesso: e' l'unico momento in cui serve una persona.

**Runtime:** GPU T4. **Durata:** 24 fit, circa quattro ore.

**Cosa fa.** Per ognuno degli otto mondi dello studio di copertura (semi 42, 101-107) esegue tre fit, uno per ciascun livello `f` = 0,30 / 0,60 / 0,90. **I dati media non si toccano:** il mondo e' quello base, byte per byte, generato senza alcun flag. L'unica cosa che cambia e' una variabile di controllo in piu', costruita dalle candidature organiche vere del mondo:

`c(t, g) = f x organico_vero(t, g) x exp(eps)`, con `eps ~ Normale(0, 0,15)` e rng dedicato `default_rng(seme + 31)`.

Configurazione di stima identica a tutta la griglia (96 nodi, keep 2000, 4 catene, seme MCMC 42, revenue_per_kpi 40, prior LogNormal(0,2; 0,9)). Generatore = main + A + G1..G4 + G6 (non usato qui, ma l'impronta e' la stessa del notebook D12); runner = **R8** (`--controllo-baseline`).

**La domanda.** Quanto della domanda organica bisogna saper contare perche' l'errore si dimezzi? E' la domanda gemella di D12: invece di creare il contrasto con un esperimento, si porta al modello un dato che oggi non ha. Il riferimento e' D0 sugli stessi otto mondi: eccesso mediano **+22,9 punti**.

**CAVEAT, da ripetere accanto a ogni cifra.** Il controllo e' costruito dalla baseline **vera**: misura il caso piu' favorevole possibile ed e' un **limite superiore** di quello che un dato reale (candidature spontanee, segnalazioni, candidati di ritorno, traffico diretto) potrebbe dare, mai una stima di quello che darebbe. Inoltre, nel simulatore la baseline e' generata indipendentemente dalla spesa, quindi qui e' un controllo legittimo; nel mondo reale e' in parte un mediatore, perche' la pubblicita' genera brand search. Entrambe le cose vanno dichiarate, non attenuate.

**Come e' verificato che i dati non si muovono.** Ogni run pretende che l'impronta dell'`InputData` sia **quella di D0 dello stesso mondo**, registrata nella griglia: se la spesa cambiasse di un centesimo, la riga diventerebbe un'anomalia. Il pre-volo aggiunge il cancello sul mondo 42: dodici file su dodici identici byte per byte dopo aver costruito il controllo.

**Scrive in `MMM_griglia_D13`**, cartella nuova.

**Alla fine:** scarica la cartella per intera e riporta i riepiloghi in chat. Il ramo si legge solo sulla pre-registrazione `PREREGISTRAZIONE_D13_baseline_osservata.md`, dopo il commit dei risultati.
"""

for codice, md in (("D12", MD_D12), ("D13", MD_D13)):
    c1, c2 = costruisci(codice)
    compile(c1, "cella1", "exec")
    compile(c2, "cella2", "exec")
    nb = {
        "nbformat": nb10["nbformat"], "nbformat_minor": nb10["nbformat_minor"],
        "metadata": json.loads(json.dumps(nb10["metadata"])),
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": md.splitlines(keepends=True)},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
             "source": c1.splitlines(keepends=True)},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
             "source": c2.splitlines(keepends=True)},
        ],
    }
    os.makedirs(USCITA, exist_ok=True)
    fuori = os.path.join(USCITA, "colab_griglia_" + codice + ".ipynb")
    with open(fuori, "w", encoding="utf-8", newline="\n") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
        f.write("\n")
    _sha = hashlib.sha256(open(fuori, "rb").read().replace(b"\r\n", b"\n")).hexdigest()
    print(codice, "->", fuori, os.path.getsize(fuori), "byte, cella1",
          len(c1), "caratteri, cella2", len(c2), "| sha256", _sha,
          "= committato" if _sha == SHA_ATTESI[codice] else "DIVERSO dal committato")
    if _sha != SHA_ATTESI[codice]:
        raise SystemExit("ADATTAMENTO SBAGLIATO: " + codice + " rigenerato non e' identico al committato")
