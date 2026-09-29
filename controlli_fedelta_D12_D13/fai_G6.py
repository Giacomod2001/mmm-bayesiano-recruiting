# Costruisce gen_G6.py da base_G4.py con sostituzioni esatte (una sola
# occorrenza ciascuna: una sostituzione ambigua ferma tutto).
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
p = "base_G4.py"
src = open(p, encoding="utf-8").read()
orig = src


def sub(vecchio, nuovo, etichetta):
    global src
    n = src.count(vecchio)
    if n != 1:
        raise SystemExit("G6 sostituzione '%s': trovata %d volte" % (etichetta, n))
    src = src.replace(vecchio, nuovo)
    print("ok", etichetta)


# --- 1. costanti e funzioni del blackout, prima di piano_geo() ---------------
sub(
'''def piano_geo(spec: dict, rng_geo: np.random.Generator, regioni: list,
              n: int) -> dict:''',
'''# --- variante blackout totale: il LIVELLO nazionale si muove ----------------
# G6 (D12). Tutti e sette i canali a spesa esattamente zero in cinque regioni
# fisse, per due blocchi di 8 settimane. A differenza del geo e del calendario
# la spesa tolta NON viene ridistribuita: la spesa nazionale settimanale SCENDE.
# E' l'unico disegno della griglia che muove il LIVELLO dei media e non solo la
# loro distribuzione.
#
# PERCHE' beta DEVE RESTARE FISSO. Al passo 7 di genera() il coefficiente di
# ogni canale viene ricalibrato per centrare la quota di contributo dichiarata:
#     beta[ch] = quota_kpi[ch] / S x totale_atteso / somma(risposta_grezza[ch])
# e `totale_atteso` non dipende dalla spesa. Con meno spesa il contributo vero
# del canale resterebbe IDENTICO per costruzione, e il blackout misurerebbe
# zero anche se funzionasse benissimo. Qui beta - e con lui la mezza
# saturazione `ec`, che e' una proprieta' del mondo e non del disegno - restano
# quelli del mondo BASE dello stesso seme, rigenerato per intero in questo
# stesso processo (una chiamata ricorsiva a genera() senza geo_spec). E' la
# stessa scelta della patch G5 per D11 e va dichiarata accanto a ogni cifra:
# cio' che si legge non e' un mondo che il generatore produrrebbe da solo, ma
# la superficie di risposta implicita nei parametri veri di quel mondo.
BLACKOUT_N_REGIONI = 5
BLACKOUT_POSIZIONE_NELLO_STRATO = 1     # 0-based: la SECONDA di ogni strato
BLACKOUT_LUNGHEZZA_BLOCCO = 8
BLACKOUT_INIZI_0BASED = (8, 52)         # settimane 9-16 e 53-60 (1-based)


def strati_blackout(n_regioni: int = BLACKOUT_N_REGIONI) -> list:
    """Le regioni ordinate per popolazione decrescente, divise in `n_regioni`
    strati contigui di pari numerosita'. Con 20 regioni e 5 strati: quattro
    regioni per strato. Nessuna estrazione casuale."""
    ordinate = sorted(REGIONI, key=lambda r: (-REGIONI[r], r))
    if len(ordinate) % n_regioni:
        raise ValueError("blackout: " + str(len(ordinate)) + " regioni non si "
                         "dividono in " + str(n_regioni) + " strati uguali")
    passo = len(ordinate) // n_regioni
    return [ordinate[i * passo:(i + 1) * passo] for i in range(n_regioni)]


def regioni_blackout(n_regioni: int = BLACKOUT_N_REGIONI,
                     posizione: int = BLACKOUT_POSIZIONE_NELLO_STRATO) -> list:
    """Una regione per strato, sempre nella stessa posizione. Con posizione 1
    (la seconda dello strato) la quota di popolazione trattata e' quella piu'
    vicina al 25% nominale di un campione di 5 regioni su 20: e' il criterio
    di rappresentativita' dichiarato nella pre-registrazione, fissato prima di
    generare qualunque mondo e uguale in tutti gli otto."""
    strati = strati_blackout(n_regioni)
    if not 0 <= posizione < len(strati[0]):
        raise ValueError("blackout: posizione fra 0 e " + str(len(strati[0]) - 1))
    return sorted(s[posizione] for s in strati)


def blackout_spec(n_regioni: int = BLACKOUT_N_REGIONI,
                  posizione: int = BLACKOUT_POSIZIONE_NELLO_STRATO) -> dict:
    """Piano fisso, identico in tutti i mondi: stesse regioni, stessi blocchi,
    tutti e sette i canali insieme. Nessun rng."""
    regs = regioni_blackout(n_regioni, posizione)
    L = BLACKOUT_LUNGHEZZA_BLOCCO
    blocchi = [(a, a + L - 1) for a in BLACKOUT_INIZI_0BASED]
    return dict(GEO_SPEC_DEFAULT, nome="blackout", canali=list(CANALI),
                n_regioni=n_regioni, n_blocchi=len(blocchi),
                lunghezza_blocco=L, intensita=0.0, sfalsato=False,
                ridistribuisci=False, posizione_nello_strato=posizione,
                strati=strati_blackout(n_regioni), regioni_trattate=list(regs),
                piano_fisso={ch: {"regioni": list(regs), "blocchi": list(blocchi)}
                             for ch in CANALI})


def piano_geo(spec: dict, rng_geo: np.random.Generator, regioni: list,
              n: int) -> dict:''',
    "1 costanti blackout")

# --- 2. applica_geo_alle_quote: ridistribuzione opzionale -------------------
sub(
'''def applica_geo_alle_quote(shares: np.ndarray, maschera: np.ndarray,
                           intensita: float) -> np.ndarray:''',
'''def applica_geo_alle_quote(shares: np.ndarray, maschera: np.ndarray,
                           intensita: float,
                           ridistribuisci: bool = True) -> np.ndarray:''',
    "2a firma applica_geo_alle_quote")

sub(
'''    intensita 0,5 e' -42%, non -50%. Il diario la riporta."""
    q = shares.copy()
    q[maschera] *= intensita
    tot = q.sum(axis=1, keepdims=True)
    return q / np.where(tot > 0, tot, 1.0)''',
'''    intensita 0,5 e' -42%, non -50%. Il diario la riporta.

    Con ridistribuisci=False (G6, blackout totale) la rinormalizzazione NON
    avviene: le quote della settimana non tornano a sommare 1, la spesa tolta
    non va a nessuno e la spesa nazionale del canale SCENDE. E' l'unico modo
    di far muovere il livello, e la riduzione effettiva nelle regioni trattate
    e' esattamente -100%."""
    q = shares.copy()
    q[maschera] *= intensita
    if not ridistribuisci:
        return q
    tot = q.sum(axis=1, keepdims=True)
    return q / np.where(tot > 0, tot, 1.0)''',
    "2b corpo applica_geo_alle_quote")

# --- 3. genera(): mondo base per beta e ec ----------------------------------
sub(
'''    geo_piano = piano_geo(geo_spec, rng_geo, regioni, n) if geo_spec is not None else {}
    geo_maschere = {ch: maschera_geo(geo_piano[ch], regioni, n) for ch in geo_piano}''',
'''    geo_piano = piano_geo(geo_spec, rng_geo, regioni, n) if geo_spec is not None else {}
    geo_maschere = {ch: maschera_geo(geo_piano[ch], regioni, n) for ch in geo_piano}
    # G6: il blackout totale ha bisogno di beta e ec del mondo BASE dello stesso
    # seme (vedi il commento di blackout_spec). Il mondo base si rigenera qui,
    # per intero, con una chiamata ricorsiva senza geo_spec: il suo rng e' un
    # oggetto nuovo e non sposta di un passo il flusso di questo mondo.
    _blackout = bool(geo_spec is not None and geo_spec.get("nome") == "blackout")
    beta_base = ec_base = ch_spesa_base = blackout_base = None
    if _blackout:
        _p_base = genera(seed=seed, n_settimane=n_settimane,
                         quota_media=quota_media, rumore=rumore,
                         sigma_attr=sigma_attr)
        beta_base = dict(_p_base["beta"])
        ec_base = dict(_p_base["ec_impr"])
        ch_spesa_base = {ch: v.copy() for ch, v in _p_base["ch_spesa"].items()}
        # Il COSTO del disegno si misura qui, dove il mondo base e' ancora in
        # memoria: e' l'unica cifra che il blackout paga davvero, e in tesi va
        # scritta accanto al risultato.
        blackout_base = dict(
            contributo_vero_totale=float(sum(v.sum() for v in _p_base["risposta"].values())),
            contributo_vero_per_canale={ch: float(v.sum())
                                        for ch, v in _p_base["risposta"].items()},
            quota_media_realizzata=float(_p_base["quota_media_realizzata"]),
            spesa_totale=float(sum(float(v.sum()) for v in _p_base["ch_spesa"].values())),
            candidature_totali=int(_p_base["candidature"].sum()),
        )
        del _p_base''',
    "3 mondo base")

# --- 4. passo 4: niente ridistribuzione quando il disegno lo dice -----------
sub(
'''                shares = applica_geo_alle_quote(shares, m_geo, geo_spec["intensita"])''',
'''                shares = applica_geo_alle_quote(
                    shares, m_geo, geo_spec["intensita"],
                    ridistribuisci=geo_spec.get("ridistribuisci", True))''',
    "4 chiamata applica_geo_alle_quote")

# --- 5. guardia di spesa: due regimi ----------------------------------------
sub(
'''        # guardia: spesa nazionale settimanale del canale conservata
        _tot = ch_spesa[ch].sum(axis=1)''',
'''        if not geo_spec.get("ridistribuisci", True):
            # G6: qui la spesa nazionale NON e' conservata, ed e' il punto del
            # disegno. Si controllano le due cose che devono valere: zero
            # esatto nelle celle trattate, e fuori da quelle celle la spesa
            # del mondo base, valore per valore.
            _m = geo_maschere[ch]
            if float(ch_spesa[ch][_m].sum()) != 0.0:
                raise RuntimeError("blackout: spesa non nulla in una cella "
                                   "trattata di " + ch)
            if ch_spesa_base is not None and not np.array_equal(
                    ch_spesa[ch][~_m], ch_spesa_base[ch][~_m]):
                raise RuntimeError("blackout: fuori dalle celle trattate la "
                                   "spesa di " + ch + " non e' quella del "
                                   "mondo base")
            d["spesa_tolta_eur"] = round(pr - dp, 2)
            d["spesa_ridistribuita_eur"] = 0.0
            d["fattore_riscalo_non_trattate_stesse_settimane"] = 1.0
            continue
        # guardia: spesa nazionale settimanale del canale conservata
        _tot = ch_spesa[ch].sum(axis=1)''',
    "5 guardia spesa")

# --- 6. passo 5: ec del mondo base ------------------------------------------
sub(
'''        ec = c["ec_mult"] * float(np.mean(ch_impr[ch].sum(axis=1)))
        c["_ec_impr"] = ec''',
'''        ec = c["ec_mult"] * float(np.mean(ch_impr[ch].sum(axis=1)))
        if _blackout:
            # la mezza saturazione e' una proprieta' del MONDO, non del
            # disegno: con meno impression scenderebbe, e la curva di risposta
            # vera cambierebbe insieme alla cosa che il disegno misura.
            ec = ec_base[ch]
        c["_ec_impr"] = ec''',
    "6 ec fisso")

# --- 7. passo 7: beta del mondo base ----------------------------------------
sub(
'''        grezzo = float(risposta_grezza[ch].sum())
        beta[ch] = quote_ch[ch] * totale_atteso / max(grezzo, 1e-12)
        risposta[ch] = beta[ch] * risposta_grezza[ch]''',
'''        grezzo = float(risposta_grezza[ch].sum())
        beta[ch] = quote_ch[ch] * totale_atteso / max(grezzo, 1e-12)
        if _blackout:
            # Senza questa riga il blackout misurerebbe zero: la ricalibrazione
            # riporterebbe il contributo totale del canale al suo valore di
            # sempre, quota_kpi/S x totale_atteso, qualunque sia la spesa.
            beta[ch] = beta_base[ch]
        risposta[ch] = beta[ch] * risposta_grezza[ch]''',
    "7 beta fisso")

# --- 8. dizionario di ritorno: ec esposto -----------------------------------
sub(
'''        risposta=risposta, beta=beta, beta_geo=beta_geo, mult_base=mult_base,''',
'''        risposta=risposta, beta=beta, beta_geo=beta_geo, mult_base=mult_base,
        ec_impr={ch: float(CANALI[ch]["_ec_impr"]) for ch in canali},
        blackout_base=blackout_base,''',
    "8 ec_impr nel ritorno")

open("gen_G6.py", "w", encoding="utf-8", newline="\n").write(src)
print("scritto gen_G6.py, delta", len(src) - len(orig), "caratteri")
