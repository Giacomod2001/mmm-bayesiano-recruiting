# Costruisce il runner R8 = R7 (notebook D10) + disegno 'blackout' (D12)
# + --controllo-baseline (D13). Sostituzioni esatte, una occorrenza ciascuna.
import hashlib
import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
blob = json.load(open("../nb/D10_blob.json", encoding="utf-8"))
src = blob["runner"]


def sub(vecchio, nuovo, etichetta):
    global src
    n = src.count(vecchio)
    if n != 1:
        raise SystemExit("R8 sostituzione '%s': trovata %d volte" % (etichetta, n))
    src = src.replace(vecchio, nuovo)
    print("ok", etichetta)


# --- 1. colonne nuove -------------------------------------------------------
sub(
'''COLONNE_CANALI += ["trattato", "dose_pct", "riduzione_effettiva_pct",
                   "spesa_vs_base_pct", "spesa_ridistribuita_eur"]''',
'''COLONNE_CANALI += ["trattato", "dose_pct", "riduzione_effettiva_pct",
                   "spesa_vs_base_pct", "spesa_ridistribuita_eur"]
# R8 (D12): nel blackout la spesa non e' ridistribuita, e' TOLTA. Sono due
# colonne diverse perche' sono due cose diverse: confonderle farebbe leggere
# come "spostata" una spesa che nel mondo non c'e' piu'.
COLONNE_CANALI += ["spesa_tolta_eur"]
# R8 (D12): il costo del disegno e la quota vera del mondo BASE, dal JSON del
# generatore. Senza queste due colonne il costo andrebbe ricostruito a mano.
COLONNE += ["quota_media_vera_base_pct", "candidature_vere_perse"]
# R8 (D13): il controllo costruito dalla baseline vera. f = 0 significa
# nessun file scritto e run identico a D0.
COLONNE += ["controllo_baseline_f", "controllo_baseline_colonna",
            "controllo_baseline_rho", "controlli_nel_modello"]''',
    "1 colonne")

# --- 2. disegni e flag ------------------------------------------------------
sub(
'''DISEGNI = ("base", "randomizzato", "sanita", "geo", "calendario", "casuale2",
           "pause2")
FLAG_DISEGNO = {"base": [], "randomizzato": ["--sanita"], "sanita": ["--sanita"],
                "geo": ["--geo"], "calendario": ["--calendario"],
                "casuale2": ["--casuale2"], "pause2": ["--pause2"]}''',
'''DISEGNI = ("base", "randomizzato", "sanita", "geo", "calendario", "casuale2",
           "pause2", "blackout")
FLAG_DISEGNO = {"base": [], "randomizzato": ["--sanita"], "sanita": ["--sanita"],
                "geo": ["--geo"], "calendario": ["--calendario"],
                "casuale2": ["--casuale2"], "pause2": ["--pause2"],
                "blackout": ["--blackout"]}''',
    "2 disegni")

# --- 3. lettura del disegno blackout ---------------------------------------
sub(
'''    sc = j["scenario_geo"]                         # geo e calendario
    canali = list(sc["canali_trattati"])
    for c in canali:
        e = sc["effetto_per_canale"][c]
        dett[c] = {"trattato": 1, "dose_pct": e["dose_popolazione_pct"],
                   "riduzione_effettiva_pct": e["riduzione_effettiva_pct"],
                   "spesa_vs_base_pct": 0.0,
                   "spesa_ridistribuita_eur": e["spesa_ridistribuita_eur"]}
    return ";".join(canali), dett''',
'''    sc = j["scenario_geo"]                         # geo, calendario, blackout
    canali = list(sc["canali_trattati"])
    for c in canali:
        e = sc["effetto_per_canale"][c]
        dett[c] = {"trattato": 1, "dose_pct": e["dose_popolazione_pct"],
                   "riduzione_effettiva_pct": e["riduzione_effettiva_pct"],
                   "spesa_vs_base_pct": 0.0,
                   "spesa_ridistribuita_eur": e["spesa_ridistribuita_eur"],
                   "spesa_tolta_eur": e.get("spesa_tolta_eur", "")}
    return ";".join(canali), dett


def leggi_costo_blackout(percorso_json: str) -> dict:
    """D12: quota vera del mondo BASE e candidature vere perse, dal JSON del
    generatore. Sono le due cifre che dicono quanto il disegno e' costato, e
    stanno nel file scritto dal generatore, non ricostruite qui."""
    with open(percorso_json, encoding="utf-8") as f:
        j = json.load(f)
    sc = j.get("scenario_blackout")
    if not sc:
        raise SystemExit("--disegno blackout ma il JSON del mondo non ha "
                         "scenario_blackout: il generatore non e' quello con G6")
    costo = sc.get("costo_del_disegno") or {}
    return {"quota_media_vera_base_pct": sc.get("quota_media_vera_mondo_base_pct", ""),
            "candidature_vere_perse": costo.get("candidature_vere_perse", "")}


def scrivi_controllo_baseline(mondo_dir: str, dir_dati: str, seed_mondo: int,
                              f: float, np, pd) -> tuple:
    """D13: aggiunge ai dati del modello UNA variabile di controllo costruita
    dalla baseline vera del mondo.

        c(t, g) = f x organico_vero(t, g) x exp(eps),  eps ~ Normale(0, 0,15)

    con rng dedicato numpy.random.default_rng(seed_mondo + 31) ed eps estratto
    nell'ordine in cui verita/candidature_organiche.csv e' scritto (settimana
    esterna, regione interna): l'ordine e' quello del file, non una scelta di
    questa funzione.

    I file media e il KPI non vengono toccati: il generatore ha girato senza
    alcun flag e la cartella e' quella del mondo base. Con f = 0 non viene
    scritto NIENTE (una colonna di soli zeri non sarebbe un controllo e il
    file verrebbe letto come elenco di eventi): il run e' identico a D0.

    IL CAVEAT, che va ripetuto ovunque compaia una cifra di D13: questo
    controllo e' costruito dalla baseline VERA, quindi misura il caso piu'
    favorevole possibile. E' un limite SUPERIORE di quello che un dato reale
    potrebbe dare, mai una stima di quello che darebbe."""
    if f <= 0:
        return "", "", ""
    percorso = os.path.join(mondo_dir, "verita", "candidature_organiche.csv")
    if not os.path.exists(percorso):
        raise SystemExit("--controllo-baseline: manca " + percorso)
    d = pd.read_csv(percorso)
    vera = d["candidature_organiche_vere"].to_numpy(dtype=float)
    rng = np.random.default_rng(int(seed_mondo) + 31)
    eps = rng.normal(0.0, 0.15, len(d))
    c = float(f) * vera * np.exp(eps)
    colonna = "domanda_organica_osservata"
    pd.DataFrame({"settimana": d["settimana"], "regione": d["regione"],
                  colonna: np.round(c, 3)}).to_csv(
        os.path.join(dir_dati, colonna + ".csv"), index=False)
    rho = float(np.corrcoef(c, vera)[0, 1])
    print("[D13] controllo " + colonna + " scritto: f=" + str(f) +
          ", corr con la baseline vera " + str(round(rho, 4)))
    return colonna, round(rho, 4), os.path.join(dir_dati, colonna + ".csv")''',
    "3 leggi_disegno blackout + D13")

# --- 4. scrittura del controllo dopo la generazione ------------------------
sub(
'''            riga["canali_trattati"], dettaglio_canali = leggi_disegno(
                os.path.join(mondo_dir, "verita", "parametri_generazione.json"),
                args.disegno)''',
'''            riga["canali_trattati"], dettaglio_canali = leggi_disegno(
                os.path.join(mondo_dir, "verita", "parametri_generazione.json"),
                args.disegno)
            if args.disegno == "blackout":
                riga.update(leggi_costo_blackout(
                    os.path.join(mondo_dir, "verita",
                                 "parametri_generazione.json")))
            if args.controllo_baseline:
                import numpy as _np_c
                import pandas as _pd_c
                _col, _rho, _ = scrivi_controllo_baseline(
                    mondo_dir, dir_dati, args.seed_mondo,
                    args.controllo_baseline, _np_c, _pd_c)
                riga["controllo_baseline_colonna"] = _col
                riga["controllo_baseline_rho"] = _rho
            riga["controllo_baseline_f"] = args.controllo_baseline or 0.0''',
    "4 scrittura controllo")

# --- 5. quanti controlli sono davvero entrati nel modello ------------------
sub(
'''        riga["unita_outcome"] = "EUR per EUR speso"
        riga["revenue_per_kpi"] = 40.0''',
'''        riga["unita_outcome"] = "EUR per EUR speso"
        riga["revenue_per_kpi"] = 40.0
        # D13: il controllo deve essere entrato come CONTROLLO. Se f > 0 e i
        # controlli restano due (i due del mondo base), il file e' stato letto
        # come altro e la riga mentirebbe.
        _ctrl = list(ns.get("CONTROLLI") or [])
        riga["controlli_nel_modello"] = ";".join(_ctrl)
        if args.controllo_baseline:
            _atteso = "ctrl_" + str(riga.get("controllo_baseline_colonna") or "")
            if _atteso not in _ctrl:
                raise SystemExit(
                    "--controllo-baseline: la colonna " + _atteso + " NON e' "
                    "fra i controlli del modello (" + ", ".join(_ctrl) + "): "
                    "l'ingestion l'ha classificata diversamente e il run "
                    "misurerebbe un'altra cosa.")
            if str(riga.get("controllo_baseline_colonna")) in \\
                    [str(x) for x in ns.get("CANALI_MODELLO", [])]:
                raise SystemExit("--controllo-baseline: la colonna e' finita "
                                 "fra i canali media")''',
    "5 guardia controlli")

# --- 6. riga di comando -----------------------------------------------------
sub(
'''    ap.add_argument("--parametri-disegno", default=None,''',
'''    ap.add_argument("--controllo-baseline", type=float, default=None,
                    help="D13: aggiunge ai dati del modello una variabile di "
                         "controllo costruita dalla baseline VERA del mondo, "
                         "c = f x organico_vero x exp(N(0, 0,15)), rng "
                         "default_rng(seed_mondo + 31). f e' questo valore "
                         "(0,30 / 0,60 / 0,90 nella griglia D13); 0 o assente "
                         "= nessun file scritto, run identico a D0. I file "
                         "media e il KPI non vengono toccati")
    ap.add_argument("--parametri-disegno", default=None,''',
    "6 flag --controllo-baseline")

# --- 7. guardia: il controllo ha senso solo sui mondi generati -------------
sub(
'''    sys.exit(esegui_mondo(ap.parse_args()))''',
'''    _a = ap.parse_args()
    if _a.controllo_baseline is not None:
        if not 0.0 <= _a.controllo_baseline <= 1.0:
            ap.error("--controllo-baseline fra 0 e 1")
        if _a.dati_modello is not None:
            ap.error("--controllo-baseline richiede un mondo generato: la "
                     "baseline vera sta in verita/candidature_organiche.csv "
                     "del mondo, non in un dataset gia' presente")
    sys.exit(esegui_mondo(_a))''',
    "7 guardia parametri")

# --- 8. intestazione --------------------------------------------------------
sub(
'''"""Runner di UN mondo per lo studio di copertura degli intervalli di credibilita'.''',
'''"""Runner di UN mondo per lo studio di copertura degli intervalli di credibilita'.

R8 = R7 + due cose, per D12 e D13:
  - disegno 'blackout' (D12): tutti e sette i canali a zero in cinque regioni
    fisse per due blocchi da otto settimane, spesa NON ridistribuita. Dal JSON
    del generatore arrivano anche la quota vera del mondo base e le
    candidature vere perse, cioe' il costo del disegno;
  - --controllo-baseline f (D13): una variabile di controllo costruita dalla
    baseline VERA del mondo, aggiunta ai dati del modello DOPO la generazione.
    Il generatore gira senza alcun flag e i file media e il KPI restano quelli
    del mondo base.''',
    "8 intestazione")

open("runner_R8.py", "w", encoding="utf-8", newline="\n").write(src)
compile(src, "runner_R8.py", "exec")
print("runner R8 scritto, sha16", hashlib.sha256(src.encode("utf-8")).hexdigest()[:16],
      "-", len(src), "caratteri")
