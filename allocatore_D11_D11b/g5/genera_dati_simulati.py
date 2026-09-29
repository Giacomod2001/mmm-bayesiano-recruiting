# -*- coding: utf-8 -*-
"""
Generatore del dataset SIMULATO per il Capitolo 5.

I dati reali dell'azienda sono bloccati da vincoli di compliance aziendale: il
Capitolo 5 viene scritto su questo dataset sintetico, dichiarato tale.

Il generatore NON modifica la pipeline: produce file nello stesso vocabolario
di colonne del formato richiesto all'azienda (il modulo di richiesta dati
resta fuori dal repo; lo schema e' documentato in dati_simulati/README.md), che
l'ingestion generica del notebook legge senza adattamenti.

    python genera_dati_simulati.py                  # variante primaria
    python genera_dati_simulati.py --tutte          # primaria + diagnostica 30%
    python genera_dati_simulati.py --quota 0.30 --suffisso _q30
    python genera_dati_simulati.py --pause2         # variante blackout
    python genera_dati_simulati.py --sanita         # variante spesa casuale

Cartelle prodotte (vedi dati_simulati/README.md):
    dati_simulati/modello/      input del modello   -> cella 4 del notebook
    dati_simulati/benchmark/    confronto a valle   -> cella 11 del notebook
    dati_simulati/verita/       parametri veri e serie nascoste: MAI in input

AVVERTENZA SUI PARAMETRI (vale anche per parametri_generazione.json):
i valori qui sotto servono a ILLUSTRARE il comportamento del sistema nel
Capitolo 5, non a rivendicare una validazione per parameter recovery. Nel testo
della tesi non si scrive mai "validato".

AVVERTENZA SUI PESI DI SPESA:
la ripartizione della spesa tra canali e tra job board e' un parametro di
generazione scelto per plausibilita', NON una stima di quote di mercato. Gli
unici fatti di mercato usati sono: Indeed prima per traffico nella categoria
lavoro in Italia, e la chiusura di InfoJobs il 31/12/2025 (annunci confluiti
in Subito). Tutto il resto e' calibrazione dell'autore.
"""
from __future__ import annotations

import argparse
import re
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# CONFIG - tutto cio' che si puo' voler cambiare sta qui
# =============================================================================

SEED = 42
N_SETTIMANE = 104                 # 2 anni
INIZIO = "2024-01-01"             # lunedi'
VALUTA = "EUR"

# --- outcome -----------------------------------------------------------------
BASELINE_NAZIONALE = 6_500.0      # candidature organiche/settimana, nazionale
BASELINE_TREND_SETT = 4.0         # crescita strutturale lenta
BASELINE_DISPERSIONE_GEO = 0.18   # eterogeneita' regionale (analogo di tau_g)
VALORE_CANDIDATURA_EUR = 40.0     # margine atteso per candidatura

# Quota delle candidature spiegata dai media. Nel recruiting la maggior parte
# arriva da organico: 18-20% e' il caso realistico (ed e' il caso difficile).
# La variante al 30% serve come DIAGNOSTICA nel Cap. 6: distingue "il metodo
# non identifica" da "questo settore e' difficile". Se al 18-20% gli intervalli
# restano larghi NON si alza la quota per stringerli: si riporta come risultato.
QUOTA_MEDIA_TARGET = 0.185

# --- rumore osservativo ------------------------------------------------------
# "nb" = binomiale negativa sul conteggio (Var = mu + mu^2/phi): realistica,
# ma introduce eteroschedasticita' rispetto alla verosimiglianza normale di
# Meridian. "normale" isola l'effetto se il fit soffre.
RUMORE = "nb"
NB_PHI = 140.0                    # CV ~9% su una regione grande
RUMORE_NORMALE_CV = 0.09

# --- trasformazioni (forma funzionale di Meridian) ---------------------------
MAX_LAG = 8                       # troncamento adstock, come ModelSpec(max_lag=8)
DISPERSIONE_BETA_GEO = 0.25       # analogo di eta_m: il partial pooling lavora QUI
                                  # (in Meridian adstock e Hill sono NAZIONALI:
                                  #  estrarli per regione sarebbe misspecificazione)

# --- geografia ---------------------------------------------------------------
POPOLAZIONE_ITALIA = 58_990_000
REGIONI = {
    "Lombardia": 0.169, "Lazio": 0.097, "Campania": 0.095, "Veneto": 0.082,
    "Sicilia": 0.081, "Emilia-Romagna": 0.075, "Piemonte": 0.072,
    "Puglia": 0.066, "Toscana": 0.062, "Calabria": 0.031, "Sardegna": 0.027,
    "Liguria": 0.025, "Marche": 0.025, "Abruzzo": 0.021,
    "Friuli-Venezia Giulia": 0.020, "Trentino-Alto Adige": 0.018,
    "Umbria": 0.014, "Basilicata": 0.009, "Molise": 0.005,
    "Valle d'Aosta": 0.002,
}

# Vocazione stagionale: 1 = domanda tutta estiva (turismo, agricoltura),
# 0 = domanda tutta Q4 (logistica, GDO). Parametro di generazione plausibile,
# non una misura: serve a dare alla stagionalita' una struttura REGIONALE, cosi'
# l'indice nazionale pubblicato non spiega tutto (come nella realta').
VOCAZIONE_ESTIVA = {
    "Lombardia": 0.20, "Lazio": 0.45, "Campania": 0.60, "Veneto": 0.45,
    "Sicilia": 0.80, "Emilia-Romagna": 0.50, "Piemonte": 0.25,
    "Puglia": 0.75, "Toscana": 0.60, "Calabria": 0.80, "Sardegna": 0.85,
    "Liguria": 0.65, "Marche": 0.50, "Abruzzo": 0.55,
    "Friuli-Venezia Giulia": 0.40, "Trentino-Alto Adige": 0.75,
    "Umbria": 0.45, "Basilicata": 0.55, "Molise": 0.55,
    "Valle d'Aosta": 0.70,
}

# --- canali ------------------------------------------------------------------
# spesa_sett : spesa media settimanale nazionale (EUR)
# lam        : ritenzione adstock geometrico
# ec_mult    : mezza saturazione di Hill, in multipli dell'esecuzione media
#              settimanale del canale (>1 satura tardi, <1 satura presto)
# slope      : pendenza di Hill (1.0 = risposta quasi lineare nel range)
# quota_kpi  : quota delle candidature TOTALI attribuita al canale (verita')
# misattr    : sovra/sotto-attribuzione delle conversioni DICHIARATE DALLA
#              PIATTAFORMA rispetto al contributo vero
# bias_bench : bias del BENCHMARK INTERNO (GA4 x database) rispetto al vero.
#              Due componenti opposte: il last-click assorbe domanda spontanea
#              (gonfia), la copertura GA4 manca dove le candidature non passano
#              dal sito (lead form in-app, candidature avviate on-platform).
# pavimento  : spesa minima settimanale garantita (presidio strategico)
#
# NB: i quattro job board sono canali SEPARATI (la categoria non e' omogenea:
# modelli d'asta e audience diversi). Per accorparli basta togliere una voce da
# JOB_BOARD_QUOTE: le quote vengono rinormalizzate.
JOB_BOARD_SPESA_SETT = 9_000.0
JOB_BOARD_QUOTE = {
    "Indeed": 0.55,             # primo per traffico nella categoria lavoro in Italia
    "Subito Lavoro": 0.20,      # slot/abbonamento + display (raccoglie l'eredita' InfoJobs)
    "Jooble": 0.08,             # aggregatore CPC puro
    "Altre job board": 0.17,    # Bakeca, TrovoLavoro, CareerJet/Talent.com
}

CANALI = {
    "Google Ads": dict(
        spesa_sett=12_000.0, lam=0.20, ec_mult=2.20, slope=1.30,
        quota_kpi=0.055, misattr=1.20, bias_bench=1.30, pavimento=0.0,
        settimane_spente=(),
        nota="asta su domanda esplicita: ritenzione breve, satura tardi"),
    "Meta Ads": dict(
        spesa_sett=9_000.0, lam=0.50, ec_mult=1.50, slope=1.10,
        quota_kpi=0.045, misattr=1.80, bias_bench=1.05, pavimento=0.0,
        settimane_spente=(31, 83),
        nota="domanda latente: ritenzione media, saturazione media"),
    "LinkedIn Ads": dict(
        spesa_sett=5_000.0, lam=0.70, ec_mult=2.40, slope=1.30,
        # TARATURA DICHIARATA: quota_kpi abbassata da 0,015 a 0,013 dopo aver visto
        # i numeri. A 0,015 il ROI vero usciva 1,00 esatto e il pavimento di spesa
        # non avrebbe avuto mordente, quindi lo scenario non avrebbe potuto
        # illustrare la Sez. 3.7 (vincolo attivo, eguaglianza marginale tra i soli
        # canali liberi). E' una scelta di progetto dello scenario dimostrativo,
        # non una stima: va dichiarata nel Cap. 5 e sta nel README.
        quota_kpi=0.013, misattr=0.70, bias_bench=0.85, pavimento=3_200.0,
        settimane_spente=(),
        nota="employer branding: coda lunga, satura tardi, pavimento di spesa"),
    "Indeed": dict(
        spesa_sett=JOB_BOARD_SPESA_SETT * JOB_BOARD_QUOTE["Indeed"],
        lam=0.15, ec_mult=0.55, slope=1.80,
        quota_kpi=0.040, misattr=1.05, bias_bench=0.80, pavimento=0.0,
        settimane_spente=(60, 61, 62),
        nota="audience attiva finita: ritenzione breve, satura PRESTO"),
    "Subito Lavoro": dict(
        spesa_sett=JOB_BOARD_SPESA_SETT * JOB_BOARD_QUOTE["Subito Lavoro"],
        lam=0.30, ec_mult=0.90, slope=1.40,
        quota_kpi=0.014, misattr=1.15, bias_bench=0.95, pavimento=0.0,
        settimane_spente=(13, 14, 65, 66),
        nota="slot/abbonamento + display: ritenzione media-bassa, satura presto"),
    "Jooble": dict(
        spesa_sett=JOB_BOARD_SPESA_SETT * JOB_BOARD_QUOTE["Jooble"],
        lam=0.10, ec_mult=2.00, slope=1.00,
        quota_kpi=0.005, misattr=1.30, bias_bench=1.10, pavimento=0.0,
        settimane_spente=(5, 6, 31, 32, 33, 50, 51, 84, 85, 86, 98, 99),
        nota="aggregatore CPC puro: costo marginale piu' lineare, risposta immediata"),
    "Altre job board": dict(
        spesa_sett=JOB_BOARD_SPESA_SETT * JOB_BOARD_QUOTE["Altre job board"],
        lam=0.15, ec_mult=1.20, slope=1.30,
        quota_kpi=0.011, misattr=1.20, bias_bench=0.95, pavimento=0.0,
        settimane_spente=(7, 33, 51, 85, 86, 99),
        nota="residuo aggregatori CPC (Bakeca, TrovoLavoro, CareerJet/Talent.com)"),
}

# --- campagne ----------------------------------------------------------------
# quota   : quota della spesa di canale (rinormalizzata tra le attive)
# cpm/ctr : prezzo e resa dell'esposizione (CPC implicito = cpm/(1000*ctr))
# qualita : efficacia relativa intra-canale. E' l'ordinamento che lo stage 2
#           deve recuperare dai ROAS dichiarati (assunzione della Sez. 3.8).
# attiva  : (settimana_inizio, settimana_fine) inclusive, oppure lista di flight
CAMPAGNE = {
    # ---- Google Ads (6) -----------------------------------------------------
    "AZ_IT_GOOGLE_SEARCH_BRAND":     dict(canale="Google Ads", quota=0.12, cpm=30.0, ctr=0.075, qualita=1.15),
    "AZ_IT_GOOGLE_SEARCH_GENERICA":  dict(canale="Google Ads", quota=0.30, cpm=55.0, ctr=0.050, qualita=1.30),
    "AZ_IT_GOOGLE_SEARCH_LOCALE":    dict(canale="Google Ads", quota=0.16, cpm=48.0, ctr=0.045, qualita=1.20),
    "AZ_IT_GOOGLE_PMAX":             dict(canale="Google Ads", quota=0.22, cpm=14.0, ctr=0.020, qualita=0.85,
                                           attiva=(26, 103)),
    "AZ_IT_GOOGLE_DISPLAY":          dict(canale="Google Ads", quota=0.12, cpm=6.0,  ctr=0.006, qualita=0.55),
    "AZ_IT_GOOGLE_VIDEO_YOUTUBE":    dict(canale="Google Ads", quota=0.08, cpm=9.0,  ctr=0.008, qualita=0.60,
                                           flight=[(10, 17), (48, 55), (86, 95)]),
    # ---- Meta Ads (5) -------------------------------------------------------
    "AZ_IT_META_LEAD_GEN_FORMS":     dict(canale="Meta Ads", quota=0.32, cpm=9.0, ctr=0.012, qualita=1.25),
    "AZ_IT_META_PROSPECTING_DABA":   dict(canale="Meta Ads", quota=0.28, cpm=7.5, ctr=0.014, qualita=1.10),
    "AZ_IT_META_RETARGETING_SITO":   dict(canale="Meta Ads", quota=0.14, cpm=8.5, ctr=0.022, qualita=1.35),
    "AZ_IT_META_VIDEO_REELS":        dict(canale="Meta Ads", quota=0.14, cpm=5.0, ctr=0.009, qualita=0.70),
    "AZ_IT_META_ADVANTAGE_PLUS":     dict(canale="Meta Ads", quota=0.12, cpm=7.0, ctr=0.013, qualita=0.95,
                                           attiva=(0, 77)),
    # ---- LinkedIn Ads (4) ---------------------------------------------------
    "AZ_IT_LINKEDIN_SPONSORED_CONTENT": dict(canale="LinkedIn Ads", quota=0.42, cpm=28.0, ctr=0.0060, qualita=0.95),
    "AZ_IT_LINKEDIN_LEAD_GEN_FORMS":    dict(canale="LinkedIn Ads", quota=0.30, cpm=34.0, ctr=0.0085, qualita=1.30),
    "AZ_IT_LINKEDIN_VIDEO_EMPLOYER":    dict(canale="LinkedIn Ads", quota=0.16, cpm=24.0, ctr=0.0045, qualita=0.70),
    "AZ_IT_LINKEDIN_TEXT_ADS":          dict(canale="LinkedIn Ads", quota=0.12, cpm=18.0, ctr=0.0035, qualita=0.60),
    # ---- Indeed (4) ---------------------------------------------------------
    "AZ_IT_INDEED_SPONSORED_JOBS":       dict(canale="Indeed", quota=0.55, cpm=22.0, ctr=0.041, qualita=1.20),
    "AZ_IT_INDEED_PPA_STAGIONALI":       dict(canale="Indeed", quota=0.18, cpm=20.0, ctr=0.038, qualita=1.05,
                                               flight=[(22, 34), (40, 50), (74, 86), (92, 100)]),
    "AZ_IT_INDEED_DISPLAY_RETE":         dict(canale="Indeed", quota=0.15, cpm=6.0,  ctr=0.005, qualita=0.55),
    "AZ_IT_INDEED_RETARGETING_CANDIDATI":dict(canale="Indeed", quota=0.12, cpm=9.0,  ctr=0.018, qualita=1.10),
    # ---- Subito Lavoro (4) --------------------------------------------------
    "AZ_IT_SUBITO_SLOT_PREMIUM":      dict(canale="Subito Lavoro", quota=0.45, cpm=11.0, ctr=0.014, qualita=1.00),
    "AZ_IT_SUBITO_SPONSORED_ANNUNCI": dict(canale="Subito Lavoro", quota=0.25, cpm=13.0, ctr=0.017, qualita=1.15),
    "AZ_IT_SUBITO_DISPLAY_HOME":      dict(canale="Subito Lavoro", quota=0.18, cpm=5.0,  ctr=0.004, qualita=0.50,
                                            flight=[(40, 51), (92, 103)]),
    "AZ_IT_SUBITO_RETARGETING":       dict(canale="Subito Lavoro", quota=0.12, cpm=7.0,  ctr=0.012, qualita=1.05),
    # ---- Jooble (4) ---------------------------------------------------------
    "AZ_IT_JOOBLE_CPC_ANNUNCI":         dict(canale="Jooble", quota=0.48, cpm=12.0, ctr=0.030, qualita=1.05),
    "AZ_IT_JOOBLE_SPONSORED_FEED":      dict(canale="Jooble", quota=0.24, cpm=14.0, ctr=0.028, qualita=1.15),
    "AZ_IT_JOOBLE_PROSPECTING_REGIONI": dict(canale="Jooble", quota=0.16, cpm=10.0, ctr=0.022, qualita=0.85,
                                              attiva=(53, 103)),
    "AZ_IT_JOOBLE_RETARGETING":         dict(canale="Jooble", quota=0.12, cpm=8.0,  ctr=0.020, qualita=0.95),
    # ---- Altre job board (4) ------------------------------------------------
    "AZ_IT_BAKECA_LAVORO_ANNUNCI":  dict(canale="Altre job board", quota=0.34, cpm=8.0,  ctr=0.020, qualita=0.90),
    "AZ_IT_TROVOLAVORO_SPONSORED":  dict(canale="Altre job board", quota=0.28, cpm=12.0, ctr=0.018, qualita=1.05),
    "AZ_IT_CAREERJET_CPC":          dict(canale="Altre job board", quota=0.22, cpm=9.0,  ctr=0.026, qualita=1.00),
    "AZ_IT_TALENT_COM_FEED":        dict(canale="Altre job board", quota=0.16, cpm=10.0, ctr=0.024, qualita=0.95,
                                          attiva=(0, 59)),
}

# --- rumore di attribuzione intra-canale --------------------------------------
# La piattaforma misura male il MERITO RELATIVO delle proprie campagne: alcune
# risultano sistematicamente sovra-riportate (piu' view-through, finestre di
# conversione piu' generose, deduplicazione interna imperfetta). Serve a non
# rendere VERA PER COSTRUZIONE l'assunzione della Sez. 3.8: la tesi sostiene che
# l'ordinamento intra-canale e' informativo ma IMPERFETTO, e il dataset deve
# mostrare quello, non un ordinamento perfetto.
#
# Tre proprieta' deliberate:
#  - persistente ENTRO il trimestre e correlato fra trimestri (un rumore bianco
#    per osservazione si medierebbe via nell'aggregazione trimestrale e lo
#    Spearman tornerebbe a 1,00);
#  - INDIPENDENTE dalla qualita' vera (altrimenti comprime la scala invece di
#    disordinare l'ordinamento);
#  - rinormalizzato dentro il canale, quindi sposta solo lo SPLIT fra campagne:
#    totale dichiarato di canale, ROAS di canale e fattore k restano calibrati.
#
# TARATURA DICHIARATA: sigma scelta con ricerca su griglia per portare lo
# Spearman medio fra canali dentro la banda 0,70-0,90. A sigma = 0 lo Spearman
# e' 1,00 su sei canali su sette: l'assunzione della Sez. 3.8 risulterebbe vera
# per costruzione. La scelta e' fatta sul valore ATTESO (media su 8 seed), non
# sul valore realizzato a seed 42: con 4-6 campagne per canale lo Spearman e'
# granuloso (con 4 campagne uno scambio adiacente vale gia' 0,80) e tarare su
# una sola realizzazione sarebbe tarare sul rumore. A sigma 0,25 l'atteso e'
# 0,73 sui due anni e 0,69 sull'ultimo trimestre (la finestra che lo stage 2
# consuma davvero); a seed 42 si realizza 0,86.
# E' una decisione di progetto dello scenario dimostrativo, non una stima di
# quanto sbagliano davvero le piattaforme: va dichiarata nel Cap. 5.
RUMORE_ATTRIBUZIONE_SD = 0.25
RUMORE_ATTRIBUZIONE_RHO = 0.70   # persistenza del mis-riporto fra trimestri

# --- pianificazione della spesa ----------------------------------------------
# Il budget segue la domanda, ma imperfettamente: se la spesa fosse collineare
# con l'indice stagionale il fit non identificherebbe nulla.
CORR_SPESA_STAGIONALITA_TARGET = 0.50   # calibrata per canale, banda accettata sotto
CORR_BANDA = (0.40, 0.60)
AR_RHO = 0.55                 # inerzia di pianificazione (AR1 sul log-budget)
CAMPAGNA_QUOTA_SD = 0.13      # oscillazione della quota di campagna dentro il canale
AR_SD = 0.18                  # ampiezza della componente idiosincratica
QUOTA_COMUNE_SD = 0.05        # ciclo di budget comune a tutti i canali
STEP_TRIMESTRALE_SD = 0.10    # gradini di budget per trimestre

# Spinte regionali: la spesa segue anche domanda LOCALE. Servono a creare
# contrasto geo x tempo, senza il quale l'identificazione torna nazionale
# in silenzio (Sez. 3.4).
SPINTE_REGIONALI = [
    dict(regioni=["Lombardia", "Veneto", "Emilia-Romagna", "Piemonte"],
         woy=(40, 48), forza=1.35, nota="picco logistica/GDO pre-natalizio"),
    dict(regioni=["Puglia", "Sicilia", "Calabria", "Sardegna",
                  "Trentino-Alto Adige", "Emilia-Romagna"],
         woy=(24, 32), forza=1.30, nota="picco turismo/agricoltura"),
]
N_SPINTE_CASUALI = 6          # push canale x regione x finestra, estratti dal seed

# --- scenario "pause2": blackout veri, con gruppo di controllo interno -------
# Il campo `settimane_spente` dei CANALI spegne settimane SINGOLE e sparse. Con
# MAX_LAG = 8 e adstock geometrico normalizzato una pausa di una settimana viene
# riempita dal carryover: non produce variazione identificante. Qui invece:
#   - 3 canali trattati hanno 2 blocchi di 8 settimane CONSECUTIVE (8 = MAX_LAG,
#     cosi' il blackout supera il carryover);
#   - 4 canali restano intatti e fanno da gruppo di controllo interno, appaiati
#     ai trattati per dimensione (Google/Meta, Indeed/LinkedIn,
#     Jooble/Altre+Subito), cosi' l'effetto della pausa non si confonde con la
#     dimensione del canale;
#   - la spesa delle settimane spente NON viene tolta: viene ridistribuita sulle
#     settimane attive dello stesso canale in proporzione al profilo di spesa
#     che quel canale ha nella base. La spesa totale per canale resta quella
#     della base, quindi base-vs-pause2 non e' confuso dal livello di spesa.
# Gli estremi sono 1-based inclusivi come si leggono nel disegno; la conversione
# a 0-based avviene in blocchi_0based(). Tutti i blocchi stanno fuori dalle
# prime 8 e dalle ultime 8 settimane: il notebook taglia la prima e l'ultima
# settimana, e nelle prime MAX_LAG l'adstock e' parziale.
PAUSE2_BLOCCHI_1BASED = {
    # Gli indici evitano anche le pause che i canali ereditano dalla base:
    # 61-68 su Google copriva la pausa base di Indeed (61-63) e 25-32 su Indeed
    # toccava quella di Jooble (32-34). Con 53-60 e 24-31 le settimane a spesa
    # zero dei tre trattati non si intersecano piu' a coppie, e non e' stato
    # necessario rimuovere le pause ereditate, cioe' introdurre una seconda
    # differenza rispetto alla base. (57-64 non basterebbe: contiene 61-63.)
    "Google Ads": [(13, 20), (53, 60)],
    "Indeed":     [(24, 31), (73, 80)],
    "Jooble":     [(37, 44), (85, 92)],
}
PAUSE2_CONTROLLI = ["Meta Ads", "LinkedIn Ads", "Altre job board", "Subito Lavoro"]
PAUSE2_LUNGHEZZA_BLOCCO = 8


def blocchi_0based(blocchi_1based: dict) -> dict:
    return {ch: [(a - 1, b - 1) for a, b in bl]
            for ch, bl in blocchi_1based.items()}


PAUSE2_SPEC = dict(
    nome="pause2",
    blocchi=blocchi_0based(PAUSE2_BLOCCHI_1BASED),
    blocchi_1based=PAUSE2_BLOCCHI_1BASED,
    controlli=PAUSE2_CONTROLLI,
    lunghezza_blocco=PAUSE2_LUNGHEZZA_BLOCCO,
)


def applica_blackout_conservando_spesa(x: np.ndarray,
                                       blocchi: list) -> tuple[np.ndarray, dict]:
    """Spegne i blocchi indicati e ridistribuisce la spesa tolta sulle settimane
    attive dello stesso canale, in proporzione al profilo settimanale di
    partenza. Il totale a n settimane resta invariato per costruzione:
    y[attive] = x[attive] * (1 + tolta/resto), e tolta + resto = x.sum().
    """
    n = len(x)
    spento = np.zeros(n, dtype=bool)
    for a, b in blocchi:
        spento[a:b + 1] = True
    tolta = float(x[spento].sum())
    resto = float(x[~spento].sum())
    if resto <= 0.0:
        raise ValueError("blackout su tutte le settimane con spesa: "
                         "non c'e' dove ridistribuire")
    y = x.copy()
    y[spento] = 0.0
    y[~spento] = x[~spento] * (1.0 + tolta / resto)
    return y, dict(spesa_tolta_eur=round(tolta, 2),
                   settimane_spente_dal_blackout=int(spento.sum()),
                   fattore_di_riscalatura=round(1.0 + tolta / resto, 6))

# --- scenario "sanita": spesa completamente randomizzata ---------------------
# E' un controllo di sanita' sul METODO, non uno scenario realizzabile in
# azienda. Tutti gli altri dataset misurano quanto il modello sbaglia in
# condizioni difficili; questo misura il contrario, cioe' il caso in cui il
# modello DEVE riuscire. La spesa non e' piu' pianificata: e' estratta a sorte,
# indipendente dalla stagionalita', dai controlli di domanda, dalla spesa degli
# altri canali e dalla propria spesa delle settimane precedenti. Se qui il
# contributo vero non viene recuperato, il problema non e' l'identificazione ma
# l'implementazione, e le conclusioni degli altri run vanno riviste.
#
# Come per pause2, l'intervento agisce sulla PIANIFICAZIONE della spesa dentro
# genera(), PRIMA del passo di risposta media (adstock + Hill): impression,
# clic, KPI, benchmark e verita' discendono tutti dal nuovo percorso di spesa.
# I CSV non vengono mai post-processati.
#
# DISTRIBUZIONE. Lognormale centrata sulla media settimanale REALIZZATA del
# canale nella base (mu = log(media) - sigma^2/2, cosi' E[x] = media), sd del
# logaritmo 0,60. E' la distribuzione positiva piu' semplice con un solo
# parametro di ampiezza e non ha bisogno di troncature. Sigma e' scelta perche'
# il rapporto atteso fra decile alto e decile basso vale
# exp(2 x 1,2816 x sigma) = 4,65, sopra il fattore 4 chiesto dal disegno
# (realizzato a seed 42: fra 4,4 e 5,6 sui sette canali). E' l'ampiezza a
# rendere facile il problema: la spesa spazza tutta la curva di risposta invece
# di oscillare attorno al proprio livello.
#
# CONSERVAZIONE. Dopo l'estrazione la serie di ogni canale viene moltiplicata
# per totale_base / somma_estratta: il totale sulle 104 settimane torna quello
# della base (entro l'arrotondamento ai centesimi, molto sotto lo 0,1%
# richiesto). Il fattore e' costante, quindi non tocca ne' le correlazioni, ne'
# l'autocorrelazione, ne' il rapporto fra i decili: la serie resta iid. Serve
# perche' il confronto base-vs-sanita non sia confuso dal livello di spesa,
# come gia' fatto per pause2.
#
# RIPARTO REGIONALE. Randomizzato anche quello, perche' il disegno chiede
# indipendenza su ogni coppia regione-settimana: quota(g,t) proporzionale alla
# popolazione per uno shock lognormale iid (sd del log 0,25, la stessa
# dispersione regionale complessiva della base, che li' e' pero' persistente -
# tilt fisso di campagna piu' AR(1) - e in parte stagionale, per via delle
# spinte regionali agganciate alla settimana dell'anno). Restare proporzionali
# alla popolazione IN MEDIA e' deliberato: un riparto uniforme fra regioni
# darebbe alla Valle d'Aosta la stessa spesa della Lombardia, saturerebbe la
# Hill nelle regioni piccole e renderebbe il problema piu' difficile, non piu'
# facile.
#
# COSA SPARISCE. Due regole di pianificazione della base non sopravvivono,
# perche' sono pattern di pianificazione e il disegno chiede che non ce ne
# siano: le settimane spente (`settimane_spente`) e il pavimento di spesa di
# LinkedIn (`pavimento`). Il livello di spesa non ne risente, perche' la
# conservazione e' fatta sul totale della base, che quelle regole le contiene.
#
# COSA RESTA. Tutto il resto e' identico alla base: stesso seed, stessi
# parametri veri (adstock, Hill, beta ricalibrato sullo stesso target del
# 18,5%), stessi controlli di domanda, stessa stagionalita' sottostante della
# DOMANDA, stesse campagne con le stesse finestre di attivita' e lo stesso
# rumore sulla quota di campagna. Le finestre di campagna restano perche'
# spostano solo lo SPLIT dentro il canale, non la spesa del canale, che e' il
# livello su cui il disegno chiede l'indipendenza.
SANITA_SIGMA_LOG_NAZIONALE = 0.60
SANITA_SIGMA_LOG_REGIONALE = 0.25
SANITA_SEED_OFFSET = 23        # rng dedicato: il resto del mondo non si sposta

SANITA_SPEC = dict(
    nome="sanita",
    sigma_log_nazionale=SANITA_SIGMA_LOG_NAZIONALE,
    sigma_log_regionale=SANITA_SIGMA_LOG_REGIONALE,
    seed_offset=SANITA_SEED_OFFSET,
)

# --- variante casuale2: spesa scorrelata dalla stagionalita', ma pianificata --
# Regime intermedio fra l'osservativo (spesa che segue la domanda) e la sanita'
# (spesa a sorte): restano l'AR(1), i gradini trimestrali, le settimane spente e
# il pavimento; sparisce solo l'accoppiamento con l'indice stagionale. Cambiano
# DUE costanti della calibrazione di kappa: il target di correlazione (0 invece
# di 0,50) e la griglia (bilaterale, 239 punti, passo 10/238: contiene lo zero
# esatto). Sono i valori che riproducono byte per byte dati_simulati/casuale2
# (ricostruiti il 15/9/2026: il generatore che lo produsse non era stato
# committato; verificato su 7 file media su 7 e sul KPI).
# La spesa TOTALE per canale NON e' conservata (-0,8..-3% rispetto alla base:
# un kappa diverso sposta la media dell'esponenziale); il diario lo riporta.
CASUALE2_SPEC = dict(
    nome="casuale2",
    corr_target=0.0,
    griglia_min=-5.0,
    griglia_max=5.0,
    griglia_punti=239,
)

# --- variante geo: esperimento geografico dentro il mondo --------------------
# Per ogni canale trattato, in alcune regioni e in alcuni blocchi di settimane
# la spesa viene spenta (o ridotta) e RIDISTRIBUITA sulle altre regioni della
# stessa settimana: la spesa nazionale settimanale del canale resta quella della
# base, cambia solo DOVE viene spesa. Regioni e blocchi sono estratti da un rng
# dedicato (seed + GEO_SEED_OFFSET), cosi' i canali non trattati e i parametri
# veri del mondo restano quelli della base con lo stesso seme.
# Con i default riproduce byte per byte dati_simulati/geo (Google Ads e
# LinkedIn Ads, 6 regioni, due blocchi da 8 settimane uno per anno, spente).
# Il protocollo di estrazione e' stato ricostruito dai dati il 15/9/2026 (il
# generatore che produsse il geo non era stato committato; il messaggio del
# commit f44f5f1 diceva "rng seed+77"): e' l'unico fra 34 protocolli plausibili
# che riproduce regioni e blocchi di entrambi i canali.
GEO_SEED_OFFSET = 77
GEO_SPEC_DEFAULT = dict(
    nome="geo",
    canali=["Google Ads", "LinkedIn Ads"],
    n_regioni=6,
    n_blocchi=2,
    lunghezza_blocco=8,
    intensita=0.0,          # moltiplicatore della quota delle regioni trattate
    sfalsato=False,         # True: ogni regione trattata ha i suoi blocchi
    seed_offset=GEO_SEED_OFFSET,
)


# --- variante calendario: sette canali a rotazione, regioni disgiunte ---------
# Un piano, non un'estrazione: nessun generatore casuale. Le 20 regioni,
# ordinate per popolazione, sono assegnate a 7 gruppi disgiunti a serpentina
# (3, 3, 3, 3, 3, 3, 2). Nel mondo con rotazione i il canale k di CANALI riceve
# il gruppo (k + i) mod 7: sugli 8 mondi (i = 0..7) la dose per canale si media
# invece di favorire il primo canale dell'elenco. Ogni canale ha due blocchi da
# 8 settimane, uno per anno, sfalsati di 7 settimane fra canali consecutivi:
# inizi 1-based 9, 16, ..., 51 e 53, 60, ..., 95 (l'ultimo finisce alla 102).
# Nessuna coppia canale x regione x settimana si sovrappone (i gruppi sono
# disgiunti); le prime 8 settimane restano libere (adstock parziale). La spesa
# nazionale settimanale per canale e' conservata come nel geo (intensita' 0).
# Dose per canale ~14% della popolazione contro il 27,6% delle sei regioni di
# Google nel geo canonico: confondimento strutturale dichiarato, controllato
# dal geo a 3 regioni (D7) a dose pari.
CALENDARIO_N_GRUPPI = 7
CALENDARIO_LUNGHEZZA_BLOCCO = 8
CALENDARIO_SFASAMENTO = 7
CALENDARIO_PRIMO_INIZIO_0BASED = 8          # settimana 9 (1-based)
CALENDARIO_SECONDO_INIZIO_0BASED = 52       # settimana 53 (1-based)
# G4: numero di giri del calendario. 2 = il disegno di D2, invariato (le due
# partenze restano le costanti qui sopra, bit per bit). 4 = D10: stessi gruppi,
# stessa lunghezza del blocco, stesso sfasamento, solo il doppio dei giri;
# partenze ogni 15 settimane, pausa di 7 fra un blocco e il successivo dello
# stesso canale (l'adstock si spegne), ultimo blocco del canale 7 alla 103.
CALENDARIO_INIZI_0BASED = {
    2: [CALENDARIO_PRIMO_INIZIO_0BASED, CALENDARIO_SECONDO_INIZIO_0BASED],
    4: [8, 23, 38, 53],
}


def gruppi_calendario() -> list:
    """7 gruppi disgiunti di regioni, a serpentina per popolazione decrescente:
    giro 1 gruppi 0..6, giro 2 gruppi 6..0, giro 3 gruppi 0..5."""
    ordinate = sorted(REGIONI, key=lambda r: (-REGIONI[r], r))
    gruppi = [[] for _ in range(CALENDARIO_N_GRUPPI)]
    ordine = list(range(CALENDARIO_N_GRUPPI))
    giro = 0
    while ordinate:
        for g in (ordine if giro % 2 == 0 else ordine[::-1]):
            if not ordinate:
                break
            gruppi[g].append(ordinate.pop(0))
        giro += 1
    return [sorted(g) for g in gruppi]


def piano_calendario(rotazione: int, giri: int = 2) -> dict:
    """{canale: {regioni, blocchi (0-based inclusivi), gruppo}} per il mondo con
    questa rotazione. Deterministico."""
    gruppi = gruppi_calendario()
    L = CALENDARIO_LUNGHEZZA_BLOCCO
    inizi = CALENDARIO_INIZI_0BASED[giri]
    piano = {}
    for k, ch in enumerate(CANALI):
        g = (k + rotazione) % CALENDARIO_N_GRUPPI
        blocchi = [(a + CALENDARIO_SFASAMENTO * k,
                    a + CALENDARIO_SFASAMENTO * k + L - 1) for a in inizi]
        piano[ch] = dict(regioni=list(gruppi[g]), gruppo=g, blocchi=blocchi)
    return piano


def calendario_spec(rotazione: int, giri: int = 2) -> dict:
    if not 0 <= rotazione < CALENDARIO_N_GRUPPI:
        raise ValueError("calendario: rotazione fra 0 e " + str(CALENDARIO_N_GRUPPI - 1))
    if giri not in CALENDARIO_INIZI_0BASED:
        raise ValueError("calendario: giri ammessi " + str(sorted(CALENDARIO_INIZI_0BASED)))
    piano = piano_calendario(rotazione, giri)
    return dict(GEO_SPEC_DEFAULT, nome="calendario", canali=list(CANALI),
                n_regioni=None, n_blocchi=giri, giri=giri,
                lunghezza_blocco=CALENDARIO_LUNGHEZZA_BLOCCO, intensita=0.0,
                sfalsato=False, rotazione=rotazione,
                piano_fisso={ch: {"regioni": v["regioni"], "blocchi": v["blocchi"]}
                             for ch, v in piano.items()},
                gruppi=gruppi_calendario(),
                gruppo_per_canale={ch: v["gruppo"] for ch, v in piano.items()})


def piano_geo(spec: dict, rng_geo: np.random.Generator, regioni: list,
              n: int) -> dict:
    """Estrae regioni e blocchi per ogni canale trattato, nell'ordine di CANALI.
    Con n_blocchi=2 un blocco cade nel primo anno e uno nel secondo (inizio
    uniforme in [0, 52-L)); con n_blocchi=1 un solo inizio in [0, n-L).
    Con sfalsato, DOPO le estrazioni standard di tutti i canali, ogni regione
    trattata riceve i propri inizi dallo stesso rng: cosi' il piano non
    sfalsato resta bit-identico a quello di default."""
    L = int(spec["lunghezza_blocco"])
    nb = int(spec["n_blocchi"])
    # G4: la guardia su n_blocchi vale per l'ESTRAZIONE a sorte (estrai_blocchi
    # sa fare 1 o 2 inizi). Con un piano fisso i blocchi sono gia' decisi e il
    # numero lo fissa il piano: il calendario a 4 giri passa di qui.
    if spec.get("piano_fisso"):
        piano = {ch: dict(regioni=list(v["regioni"]), blocchi=[tuple(b) for b in v["blocchi"]])
                 for ch, v in spec["piano_fisso"].items()}
        for v in piano.values():
            v["per_regione"] = {r: list(v["blocchi"]) for r in v["regioni"]}
        return piano
    if nb not in (1, 2):
        raise ValueError("geo: n_blocchi deve essere 1 o 2")

    def estrai_blocchi():
        if nb == 2:
            a1 = int(rng_geo.integers(0, 52 - L))
            a2 = 52 + int(rng_geo.integers(0, 52 - L))
            return [(a1, a1 + L - 1), (a2, a2 + L - 1)]
        a = int(rng_geo.integers(0, n - L))
        return [(a, a + L - 1)]

    piano = {}
    n_reg = int(spec["n_regioni"])
    for ch in CANALI:
        if ch not in spec["canali"]:
            continue
        # Con n_regioni <= 6 si estraggono comunque 6 regioni e si tengono le
        # prime n: cosi' un disegno a dose ridotta (D7: 3 regioni) tratta un
        # SOTTOINSIEME delle regioni del canonico, con gli stessi blocchi, e
        # fra i due cambia solo la dose. (choice(size=3) di numpy non e' un
        # sottoinsieme di choice(size=6), e sposterebbe anche i blocchi.)
        regs = [str(r) for r in rng_geo.choice(
            regioni, size=max(n_reg, GEO_SPEC_DEFAULT["n_regioni"]), replace=False)][:n_reg]
        blocchi = estrai_blocchi()
        piano[ch] = dict(regioni=regs, blocchi=blocchi,
                         per_regione={r: list(blocchi) for r in regs})
    if spec.get("sfalsato"):
        for ch in piano:
            for r in piano[ch]["regioni"]:
                piano[ch]["per_regione"][r] = estrai_blocchi()
    return piano


def maschera_geo(piano_ch: dict, regioni: list, n: int) -> np.ndarray:
    """(n, R) booleana: True nelle celle settimana x regione trattate."""
    m = np.zeros((n, len(regioni)), dtype=bool)
    for r, blocchi in piano_ch["per_regione"].items():
        j = regioni.index(r)
        for a, b in blocchi:
            m[a:b + 1, j] = True
    return m


def applica_geo_alle_quote(shares: np.ndarray, maschera: np.ndarray,
                           intensita: float) -> np.ndarray:
    """Moltiplica per `intensita` la quota delle celle trattate e rinormalizza
    ogni settimana a 1: la spesa nazionale della settimana e' conservata e la
    spesa tolta finisce alle altre regioni in proporzione alle loro quote
    (fattore uniforme dentro la campagna x settimana). La riduzione EFFETTIVA
    nelle regioni trattate e' minore di (1 - intensita) perche' anche loro
    ricevono la rinormalizzazione: con il 27,5% di popolazione trattata e
    intensita 0,5 e' -42%, non -50%. Il diario la riporta."""
    q = shares.copy()
    q[maschera] *= intensita
    tot = q.sum(axis=1, keepdims=True)
    return q / np.where(tot > 0, tot, 1.0)


def spesa_casuale_conservando_totale(rng_s: np.random.Generator,
                                     x_base: np.ndarray,
                                     sigma_log: float) -> tuple[np.ndarray, dict]:
    """Sostituisce il percorso di spesa nazionale di un canale con estrazioni
    lognormali indipendenti, poi riscala per conservare il totale della base.

        x[t] = media_base * LogN(-sigma^2/2, sigma),  iid su t
        y    = x * totale_base / somma(x)

    Del percorso base resta solo il TOTALE: livello e forma temporale restano
    separati, e il confronto base-vs-sanita non e' confuso dal livello di spesa.
    """
    n = len(x_base)
    totale = float(x_base.sum())
    if totale <= 0.0:
        raise ValueError("canale senza spesa nella base: non c'e' un totale "
                         "da conservare")
    media = totale / n
    y = media * rng_s.lognormal(-0.5 * sigma_log ** 2, sigma_log, n)
    fattore = totale / float(y.sum())
    y = y * fattore
    d1, d9 = np.percentile(y, [10, 90])
    return y, dict(
        totale_base_eur=round(totale, 2),
        media_settimanale_base_eur=round(media, 2),
        sigma_log=sigma_log,
        fattore_di_riscalatura=round(float(fattore), 6),
        rapporto_decile_alto_su_basso=round(float(d9 / d1), 2),
        cv_realizzato=round(float(y.std() / y.mean()), 3),
        settimane_spente_della_base_rimosse=int((x_base == 0).sum()),
    )


def quote_regionali_casuali(rng_s: np.random.Generator, n: int, R: int,
                            pop: np.ndarray, sigma_log: float) -> np.ndarray:
    """Riparto regionale iid su ogni coppia regione-settimana: proporzionale
    alla popolazione a meno di uno shock lognormale indipendente. Nessuna
    persistenza temporale, nessun tilt fisso di campagna, nessuna spinta
    regionale agganciata alla settimana dell'anno."""
    m = pop[None, :] * rng_s.lognormal(-0.5 * sigma_log ** 2, sigma_log, (n, R))
    return m / m.sum(axis=1, keepdims=True)


# --- controlli di domanda ----------------------------------------------------
CONTROLLI = {
    "richieste_clienti": dict(livello=2_400.0, trend=1.2, accoppiamento=0.55,
                              rumore_sd=90.0, coef_vero=0.55),
    "ricerche_candidati": dict(livello=5_200.0, trend=-1.0, accoppiamento=0.80,
                               rumore_sd=160.0, coef_vero=0.22),
}

# --- formato di scrittura ----------------------------------------------------
# False = date ISO e punto decimale (formato del modulo di richiesta dati).
# True  = varianti "sporche" all'italiana, per stressare l'ingestion.
FORMATO_SPORCO = False


# =============================================================================
# Trasformazioni: la forma funzionale che assume Meridian
# =============================================================================

def adstock_geometrico(x: np.ndarray, lam: float,
                       max_lag: int = MAX_LAG) -> np.ndarray:
    """Adstock geometrico NORMALIZZATO sull'asse 0 (tempo).

    Adstock(x)_t = sum_l lam^l x_{t-l} / sum_l lam^l , l = 0..max_lag

    La normalizzazione e' quella di Meridian (i pesi sommano a 1, cosi'
    l'adstock resta sulla scala della variabile). La storia precedente alla
    finestra e' posta a zero: le prime max_lag settimane hanno adstock
    leggermente sottostimato, esattamente come nel modello stimato.
    """
    pesi = lam ** np.arange(max_lag + 1)
    pesi = pesi / pesi.sum()
    out = np.zeros_like(x, dtype=float)
    n = x.shape[0]
    for lag, w in enumerate(pesi):
        if lag == 0:
            out += w * x
        else:
            out[lag:] += w * x[:n - lag]
    return out


def hill(a: np.ndarray, ec: float, slope: float) -> np.ndarray:
    """Saturazione di Hill: a^s / (a^s + ec^s). ec = mezza saturazione."""
    a = np.maximum(np.asarray(a, dtype=float), 0.0)
    num = a ** slope
    return num / (num + ec ** slope + 1e-12)


# =============================================================================
# Stagionalita'
# =============================================================================

def _bump(woy: np.ndarray, centro: float, ampiezza: float,
          altezza: float) -> np.ndarray:
    d = np.minimum(np.abs(woy - centro), 52.0 - np.abs(woy - centro))
    return altezza * np.exp(-0.5 * (d / ampiezza) ** 2)


def curve_stagionali(woy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Due componenti stagionali del mercato staffing (media ~0 ciascuna).

    estiva : turismo e agricoltura, picco tra giugno e agosto
    q4     : logistica e GDO, picco tra ottobre e novembre
    Entrambe scontano il fermo natalizio.
    """
    natale = _bump(woy, 51.5, 1.3, 0.30)
    estiva = _bump(woy, 27.0, 5.0, 0.34) - _bump(woy, 33.5, 1.6, 0.14) - natale
    q4 = _bump(woy, 45.0, 4.2, 0.32) - _bump(woy, 32.0, 2.2, 0.18) - natale
    return estiva - estiva.mean(), q4 - q4.mean()


# =============================================================================
# Generazione
# =============================================================================

# --- riparto: sposta budget fra canali, a spesa totale costante ---------------
# Serve a D11: misurare sulla verita' se seguire una regola di allocazione fa
# guadagnare. Il riparto scala il percorso di spesa settimanale del canale con un
# MOLTIPLICATORE COSTANTE (la forma non cambia: il rapporto fra due settimane
# dello stesso canale resta quello), e si applica a tutte le campagne del canale
# con lo stesso fattore, cosi' il cpm miscelato non si muove e le impressioni
# restano lineari nella spesa.
#
# ATTENZIONE, ed e' il motivo per cui questa patch non e' banale: al passo 7
# `beta` viene calibrato in modo che il contributo del canale valga
# `quota_kpi x totale_atteso` QUALUNQUE sia la spesa. Con la calibrazione
# lasciata libera, cambiare il budget non cambierebbe di una virgola il
# contributo vero, e qualunque confronto fra ripartizioni darebbe numeri
# identici. Quindi: `beta` si calibra sul mondo NON modificato, e il riparto
# agisce solo attraverso le curve di Hill. Il numero che si legge non e' piu'
# "un mondo che il generatore produrrebbe" ma "la superficie di risposta
# implicita nei parametri veri di quel mondo": e' un'altra cosa, ed e'
# dichiarata nella pre-registrazione di D11.
# Tolleranza sulla somma, in euro. Non e' una cifra a caso: una percentuale
# scritta con DECIMALI_RIPARTO cifre porta con se' un errore fino a mezza unita'
# dell'ultima cifra, cioe' 0,005% della spesa del canale con 2 decimali. La
# tolleranza copre esattamente quello, sommato sui canali toccati, e niente
# altro: un riparto che sbaglia piu' di cosi' non e' arrotondato, e' sbagliato.
RIPARTO_TOLLERANZA_EUR = 1.0     # pavimento, per i casi minuscoli
DECIMALI_RIPARTO = 2


def tolleranza_riparto(spese_toccate) -> float:
    mezza_cifra = 0.5 * 10.0 ** (-DECIMALI_RIPARTO) / 100.0
    return max(RIPARTO_TOLLERANZA_EUR, mezza_cifra * float(sum(spese_toccate)))


def analizza_riparto(testo: str) -> dict:
    """'Canale=+13.95;Canale=-15.00' -> {canale: variazione percentuale}."""
    out: dict[str, float] = {}
    for pezzo in [x for x in (testo or "").split(";") if x.strip()]:
        if "=" not in pezzo:
            raise ValueError("--riparto: atteso Canale=+n.nn, trovato " + repr(pezzo))
        ch, v = (x.strip() for x in pezzo.split("=", 1))
        if ch not in CANALI:
            raise ValueError("--riparto: canale sconosciuto " + repr(ch) +
                             "; ammessi: " + ", ".join(CANALI))
        if ch in out:
            raise ValueError("--riparto: canale ripetuto " + repr(ch))
        try:
            out[ch] = float(v)
        except ValueError:
            raise ValueError("--riparto: variazione non numerica " + repr(v))
        if out[ch] <= -100.0:
            raise ValueError("--riparto: " + ch + " non puo' scendere di " + v + "%")
    return out


def genera(seed: int = SEED, n_settimane: int = N_SETTIMANE,
           quota_media: float = QUOTA_MEDIA_TARGET,
           rumore: str = RUMORE,
           sigma_attr: float = RUMORE_ATTRIBUZIONE_SD,
           pause_spec: dict | None = None,
           sanita_spec: dict | None = None,
           casuale2_spec: dict | None = None,
           geo_spec: dict | None = None,
           riparto_spec: dict | None = None) -> dict:
    rng = np.random.default_rng(seed)
    # riparto: nessuna estrazione casuale, e' un moltiplicatore deterministico
    riparto_spec = dict(riparto_spec) if riparto_spec else None
    riparto_k = {ch: 1.0 + d / 100.0 for ch, d in (riparto_spec or {}).items()}
    riparto_diario: dict[str, dict] = {}
    # Registro di cosa il blackout ha fatto, canale per canale: finisce nel JSON
    # dei parametri, cosi' il disegno resta documentato insieme ai dati.
    pause_diario: dict[str, dict] = {}
    # La randomizzazione della spesa usa un rng DEDICATO (seed+offset), come il
    # rumore di attribuzione: cosi' tutte le altre estrazioni - riparto regionale
    # della base, rumore su impression e clic, beta per regione, moltiplicatori
    # di baseline, controlli, rumore osservativo - restano bit-identiche alla
    # base, e i PARAMETRI VERI del mondo sono gli stessi del dataset base.
    sanita_diario: dict[str, dict] = {}
    rng_sanita = (np.random.default_rng(seed + sanita_spec["seed_offset"])
                  if sanita_spec is not None else None)
    # casuale2: nessuna estrazione in piu' (cambia solo la calibrazione di
    # kappa), quindi nessun rng dedicato; solo il diario per il JSON.
    casuale2_diario: dict[str, dict] = {}
    # geo: rng dedicato per regioni e blocchi (come sanita e pause2, il flusso
    # principale non si sposta di un passo: i canali non trattati e i
    # parametri veri restano quelli della base con lo stesso seme).
    rng_geo = (np.random.default_rng(seed + geo_spec["seed_offset"])
               if geo_spec is not None else None)
    geo_diario: dict[str, dict] = {}

    regioni = sorted(REGIONI)
    R = len(regioni)
    n = n_settimane
    pop = np.array([REGIONI[r] for r in regioni])
    pop = pop / pop.sum()
    settimane = pd.date_range(INIZIO, periods=n, freq="W-MON")
    woy = settimane.isocalendar().week.to_numpy().astype(float)
    t = np.arange(n, dtype=float)
    canali = list(CANALI)
    geo_piano = piano_geo(geo_spec, rng_geo, regioni, n) if geo_spec is not None else {}
    geo_maschere = {ch: maschera_geo(geo_piano[ch], regioni, n) for ch in geo_piano}

    # ---- 1. stagionalita' regionale e indice nazionale pubblicato ----------
    estiva, q4 = curve_stagionali(woy)
    w_est = np.array([VOCAZIONE_ESTIVA[r] for r in regioni])
    seas_reg = 1.0 + (w_est[None, :] * estiva[:, None]
                      + (1.0 - w_est)[None, :] * q4[:, None])          # (n, R)
    seas_reg = seas_reg / seas_reg.mean(axis=0, keepdims=True)
    seas_naz = (seas_reg * pop[None, :]).sum(axis=1)                   # (n,)
    seas_naz = seas_naz / seas_naz.mean()

    # ---- 2. spesa nazionale per canale -------------------------------------
    comune = rng.normal(0.0, QUOTA_COMUNE_SD, n)
    spesa_naz: dict[str, np.ndarray] = {}
    kappa_scelto: dict[str, float] = {}
    for ch in canali:
        c = CANALI[ch]
        # componente idiosincratica AR(1): estratta PRIMA della calibrazione,
        # cosi' kappa e' l'unico grado di liberta'
        eps = rng.normal(0.0, AR_SD * np.sqrt(1 - AR_RHO ** 2), n)
        ar = np.empty(n)
        ar[0] = rng.normal(0.0, AR_SD)
        for i in range(1, n):
            ar[i] = AR_RHO * ar[i - 1] + eps[i]
        n_trim = int(np.ceil(n / 13))
        gradini = np.repeat(rng.normal(0.0, STEP_TRIMESTRALE_SD, n_trim), 13)[:n]
        spenta = np.zeros(n, dtype=bool)
        spenta[list(c["settimane_spente"])] = True

        def costruisci(kappa: float, c=c, ar=ar, gradini=gradini, spenta=spenta):
            x = c["spesa_sett"] * np.exp(kappa * (seas_naz - 1.0) + ar
                                         + gradini + comune)
            if c["pavimento"] > 0:
                x = np.maximum(x, c["pavimento"])
            x[spenta] = 0.0
            return x

        # calibrazione di kappa sulla correlazione con l'indice stagionale.
        # TARATURA DICHIARATA: la griglia e' stata allargata (estremo superiore
        # da 2,0 a 5,0) perche' su Jooble e Altre job board la correlazione si
        # fermava a 0,32-0,36, sotto la banda 0,40-0,60 richiesta. Allargarla
        # e' un intervento sul mondo simulato, non sulla stima: dichiarato nel
        # README e da riportare nel Cap. 5.
        griglia = np.linspace(0.0, 5.0, 120)
        corr_target = CORR_SPESA_STAGIONALITA_TARGET
        if casuale2_spec is not None:
            # casuale2: stesse estrazioni della base (ar, gradini, comune sono
            # gia' stati estratti), cambiano solo target e griglia. Vedi
            # CASUALE2_SPEC.
            griglia = np.linspace(casuale2_spec["griglia_min"],
                                  casuale2_spec["griglia_max"],
                                  casuale2_spec["griglia_punti"])
            corr_target = casuale2_spec["corr_target"]
        corrs = np.array([np.corrcoef(costruisci(k), seas_naz)[0, 1]
                          for k in griglia])
        i_kappa = int(np.argmin(np.abs(corrs - corr_target)))
        kappa = float(griglia[i_kappa])
        kappa_scelto[ch] = kappa
        x_naz = costruisci(kappa)
        if casuale2_spec is not None:
            # Diario: la calibrazione che la BASE farebbe su queste stesse
            # estrazioni (nessuna estrazione casuale: costruisci() e' pura),
            # per dire di quanto cambia la spesa totale del canale.
            g0 = np.linspace(0.0, 5.0, 120)
            c0 = np.array([np.corrcoef(costruisci(k), seas_naz)[0, 1]
                           for k in g0])
            i0 = int(np.argmin(np.abs(c0 - CORR_SPESA_STAGIONALITA_TARGET)))
            tot0 = float(np.round(costruisci(float(g0[i0])), 2).sum())
            tot1 = float(np.round(x_naz, 2).sum())
            casuale2_diario[ch] = {
                "kappa_base": round(float(g0[i0]), 4),
                "corr_spesa_stagionalita_base": round(float(c0[i0]), 4),
                "kappa": round(kappa, 4),
                "corr_spesa_stagionalita": round(float(corrs[i_kappa]), 4),
                "spesa_totale_base_eur": round(tot0, 2),
                "spesa_totale_eur": round(tot1, 2),
                "spesa_vs_base_pct": round((tot1 / tot0 - 1.0) * 100.0, 3),
            }
        # Il blackout si applica QUI, sulla pianificazione della spesa, prima
        # del passo di risposta media: cosi' impression, clic, KPI, benchmark e
        # verita' discendono tutti dal nuovo percorso di spesa. Post-processare
        # i CSV renderebbe la verita' incoerente con la spesa.
        # kappa e' gia' stato calibrato sul profilo BASE: il blackout non tocca
        # la calibrazione, e i canali di controllo restano bit-identici a base.
        if pause_spec is not None and ch in pause_spec["blocchi"]:
            x_naz, _diario = applica_blackout_conservando_spesa(
                x_naz, pause_spec["blocchi"][ch])
            _diario["blocchi_1based"] = pause_spec["blocchi_1based"][ch]
            pause_diario[ch] = _diario
        # La randomizzazione agisce nello stesso punto del blackout, sulla
        # pianificazione: del percorso base resta solo il TOTALE da conservare.
        # Con esso spariscono le settimane spente e il pavimento di spesa, che
        # sono pattern di pianificazione: qui non ce ne devono essere.
        if sanita_spec is not None:
            x_naz, _diario = spesa_casuale_conservando_totale(
                rng_sanita, x_naz, sanita_spec["sigma_log_nazionale"])
            sanita_diario[ch] = _diario
        spesa_naz[ch] = np.round(x_naz, 2)

    # ---- 2-bis. il riparto deve quadrare IN EURO, non in punti percentuali ---
    # Il totale non si tocca: e' la grandezza che il modello sbaglia di circa otto
    # punti e che nessun disegno sperimentale corregge. Un riparto che non quadra
    # userebbe proprio quel numero, quindi e' un errore, non un avviso.
    if riparto_spec:
        _euro = {ch: float(np.sum(spesa_naz[ch])) * d / 100.0
                 for ch, d in riparto_spec.items()}
        _scarto = float(sum(_euro.values()))
        _toll = tolleranza_riparto([abs(float(np.sum(spesa_naz[ch]))) for ch in riparto_spec])
        if abs(_scarto) > _toll:
            raise ValueError(
                "--riparto non quadra: la somma vale " + format(_scarto, "+,.2f") +
                " EUR (tolleranza " + format(_toll, ",.2f") + ", cioe' l'arrotondamento "
                "delle percentuali a " + str(DECIMALI_RIPARTO) + " decimali). "
                "Dettaglio: " + "; ".join(ch + " " + format(v, "+,.2f") + " EUR"
                                          for ch, v in _euro.items()) +
                ". Il totale non si tocca: si alza solo con i soldi che si sono tagliati.")
        for ch, d in riparto_spec.items():
            riparto_diario[ch] = {"variazione_pct": round(d, 4),
                                  "moltiplicatore": round(riparto_k[ch], 6),
                                  "spesa_nazionale_base_eur": round(float(np.sum(spesa_naz[ch])), 2),
                                  "euro_spostati": round(_euro[ch], 2)}
        riparto_diario["_scarto_eur"] = round(_scarto, 4)

    # ---- 3. riparto regionale: MAI a quote fisse ---------------------------
    # quota(g,t) = pop_g x tilt_campagna,g x AR(1)_g x spinte locali
    spinte = [dict(s) for s in SPINTE_REGIONALI]
    for _ in range(N_SPINTE_CASUALI):
        g = rng.choice(regioni, size=int(rng.integers(1, 4)), replace=False)
        inizio = int(rng.integers(0, n - 12))
        spinte.append(dict(regioni=list(g), sett=(inizio, inizio + int(rng.integers(6, 16))),
                           forza=float(rng.uniform(1.15, 1.5)), canale=rng.choice(canali),
                           nota="spinta locale di canale"))

    def quote_regionali(camp: str, canale: str) -> np.ndarray:
        tilt = rng.lognormal(0.0, 0.22, R)
        ar_g = np.zeros((n, R))
        eps_g = rng.normal(0.0, 0.12 * np.sqrt(1 - 0.6 ** 2), (n, R))
        ar_g[0] = rng.normal(0.0, 0.12, R)
        for i in range(1, n):
            ar_g[i] = 0.6 * ar_g[i - 1] + eps_g[i]
        m = pop[None, :] * tilt[None, :] * np.exp(ar_g)
        for s in spinte:
            if s.get("canale") not in (None, canale):
                continue
            idx_r = [regioni.index(r) for r in s["regioni"] if r in regioni]
            if "woy" in s:
                mask = (woy >= s["woy"][0]) & (woy <= s["woy"][1])
            else:
                mask = np.zeros(n, dtype=bool)
                mask[s["sett"][0]:s["sett"][1] + 1] = True
            for j in idx_r:
                m[mask, j] *= s["forza"]
        return m / m.sum(axis=1, keepdims=True)

    # ---- 4. spesa, impression e clic per campagna --------------------------
    attive: dict[str, np.ndarray] = {}
    for camp, c in CAMPAGNE.items():
        att = np.zeros(n, dtype=bool)
        if "flight" in c:
            for a, b in c["flight"]:
                att[a:b + 1] = True
        else:
            a, b = c.get("attiva", (0, n - 1))
            att[a:min(b, n - 1) + 1] = True
        attive[camp] = att

    camp_spesa, camp_impr, camp_clic = {}, {}, {}
    camp_spesa_base, camp_impr_base = {}, {}      # il mondo senza riparto: serve a beta
    for ch in canali:
        camps = [cp for cp, c in CAMPAGNE.items() if c["canale"] == ch]
        # quota di campagna con oscillazione idiosincratica: le campagne di uno
        # stesso canale restano molto correlate (sono pianificate insieme: e'
        # l'argomento della Sez. 3.8), ma non ESATTAMENTE proporzionali
        rumore_q = np.zeros((len(camps), n))
        for i in range(len(camps)):
            e = rng.normal(0.0, CAMPAGNA_QUOTA_SD * np.sqrt(1 - 0.6 ** 2), n)
            for k in range(1, n):
                rumore_q[i, k] = 0.6 * rumore_q[i, k - 1] + e[k]
        quote = np.stack([CAMPAGNE[cp]["quota"] * attive[cp] for cp in camps])
        quote = quote * np.exp(rumore_q)
        tot = quote.sum(axis=0)
        quote = np.divide(quote, np.where(tot > 0, tot, 1.0)[None, :])
        for i, cp in enumerate(camps):
            sp_naz = spesa_naz[ch] * quote[i]
            shares = quote_regionali(cp, ch)
            if sanita_spec is not None:
                # quote_regionali() viene chiamata comunque e il suo risultato
                # scartato: consuma il flusso di rng condiviso esattamente come
                # nella base, cosi' tutte le estrazioni successive non si
                # spostano di un passo e i parametri veri restano quelli.
                shares = quote_regionali_casuali(
                    rng_sanita, n, R, pop,
                    sanita_spec["sigma_log_regionale"])
            if ch in geo_maschere:
                # Il geo agisce QUI, sulle quote regionali della campagna,
                # dopo che quote_regionali() ha consumato il suo rng: la
                # spesa nazionale della settimana non cambia, cambia dove va.
                m_geo = geo_maschere[ch]
                sp_prima = np.round(sp_naz[:, None] * shares, 2)
                shares = applica_geo_alle_quote(shares, m_geo, geo_spec["intensita"])
                sp_dopo = np.round(sp_naz[:, None] * shares, 2)
                d = geo_diario.setdefault(ch, {
                    "spesa_trattata_prima_eur": 0.0, "spesa_trattata_dopo_eur": 0.0,
                    "spesa_non_trattata_stesse_settimane_prima_eur": 0.0,
                    "spesa_non_trattata_stesse_settimane_dopo_eur": 0.0})
                sett_tratt = m_geo.any(axis=1)
                m_non = sett_tratt[:, None] & ~m_geo
                d["spesa_trattata_prima_eur"] += float(sp_prima[m_geo].sum())
                d["spesa_trattata_dopo_eur"] += float(sp_dopo[m_geo].sum())
                d["spesa_non_trattata_stesse_settimane_prima_eur"] += float(sp_prima[m_non].sum())
                d["spesa_non_trattata_stesse_settimane_dopo_eur"] += float(sp_dopo[m_non].sum())
            sp = sp_naz[:, None] * shares
            impr = (sp / CAMPAGNE[cp]["cpm"] * 1000.0
                    * rng.normal(1.0, 0.03, (n, R)).clip(0.85, 1.15))
            clic = (impr * CAMPAGNE[cp]["ctr"]
                    * rng.normal(1.0, 0.07, (n, R)).clip(0.6, 1.4))
            # Il riparto scala spesa, impressioni e clic dello STESSO fattore, a
            # partire dagli stessi valori non arrotondati e dagli stessi rumori:
            # niente estrazioni in piu', quindi con k = 1 il risultato e'
            # bit-identico al percorso senza flag.
            k = riparto_k.get(ch, 1.0)
            camp_spesa_base[cp] = np.round(sp, 2)
            camp_impr_base[cp] = np.round(impr)
            camp_spesa[cp] = np.round(sp * k, 2)
            camp_impr[cp] = np.round(impr * k)
            camp_clic[cp] = np.round(clic * k)

    ch_spesa = {ch: sum(camp_spesa[cp] for cp, c in CAMPAGNE.items()
                        if c["canale"] == ch) for ch in canali}
    ch_spesa_base = {ch: sum(camp_spesa_base[cp] for cp, c in CAMPAGNE.items()
                             if c["canale"] == ch) for ch in canali}
    for ch in geo_piano:
        d = geo_diario[ch]
        pr, dp = d["spesa_trattata_prima_eur"], d["spesa_trattata_dopo_eur"]
        npr, ndp = (d["spesa_non_trattata_stesse_settimane_prima_eur"],
                    d["spesa_non_trattata_stesse_settimane_dopo_eur"])
        pi = geo_piano[ch]
        d.update({
            "regioni": list(pi["regioni"]),
            "blocchi_1based_inclusivi": [[a + 1, b + 1] for a, b in pi["blocchi"]],
            "blocchi_per_regione_1based": {r: [[a + 1, b + 1] for a, b in bl]
                                           for r, bl in pi["per_regione"].items()},
            "intensita_moltiplicatore_quota": geo_spec["intensita"],
            "dose_popolazione_pct": round(100.0 * float(sum(
                pop[regioni.index(r)] for r in pi["regioni"])), 2),
            "settimane_trattate": int(geo_maschere[ch].any(axis=1).sum()),
            "celle_trattate": int(geo_maschere[ch].sum()),
            "riduzione_effettiva_pct": round((dp / pr - 1.0) * 100.0, 2) if pr > 0 else None,
            "spesa_ridistribuita_eur": round(pr - dp, 2),
            "fattore_riscalo_non_trattate_stesse_settimane": round(ndp / npr, 4) if npr > 0 else None,
        })
        for k in list(d):
            if k.endswith("_eur"):
                d[k] = round(float(d[k]), 2)
        # guardia: spesa nazionale settimanale del canale conservata
        _tot = ch_spesa[ch].sum(axis=1)
        if not np.allclose(_tot, np.round(spesa_naz[ch], 2), atol=0.05 * len(
                [cp for cp, c in CAMPAGNE.items() if c["canale"] == ch]) * R):
            raise RuntimeError("geo: spesa nazionale non conservata su " + ch)
    ch_impr = {ch: sum(camp_impr[cp] for cp, c in CAMPAGNE.items()
                       if c["canale"] == ch) for ch in canali}
    ch_impr_base = {ch: sum(camp_impr_base[cp] for cp, c in CAMPAGNE.items()
                            if c["canale"] == ch) for ch in canali}

    # ---- 5. risposta media: adstock + Hill sulla metrica di esecuzione ------
    # La metrica di esecuzione e' l'IMPRESSION (quella che il notebook passa a
    # Meridian). Con CPM di canale stabile spesa e impression sono quasi
    # proporzionali, quindi il ramo che usa la spesa vede la stessa curva.
    mult_base = rng.lognormal(0.0, BASELINE_DISPERSIONE_GEO, R)
    mult_base /= (mult_base * pop).sum()
    beta_geo, risposta_grezza = {}, {}
    risposta_grezza_base = {}     # stessa curva, valutata sulla spesa NON modificata
    for ch in canali:
        c = CANALI[ch]
        mg = rng.lognormal(0.0, DISPERSIONE_BETA_GEO, R)
        mg /= (mg * pop).sum()
        beta_geo[ch] = mg
        # esecuzione "pro-capite" = per quota di popolazione: stessa curva
        # in ogni regione, come assume il modello geo-gerarchico
        impr_pc = ch_impr[ch] / pop[None, :]
        # La mezza saturazione e' una PROPRIETA' DEL MONDO, non della proposta di
        # budget: si calibra sulle impressioni non modificate, altrimenti il
        # riparto sposterebbe anche il metro con cui lo si misura.
        ec = c["ec_mult"] * float(np.mean(ch_impr_base[ch].sum(axis=1)))
        c["_ec_impr"] = ec
        a = adstock_geometrico(impr_pc, c["lam"])
        risposta_grezza[ch] = (hill(a, ec, c["slope"])
                               * (pop * mg)[None, :])                  # (n, R)
        a_base = adstock_geometrico(ch_impr_base[ch] / pop[None, :], c["lam"])
        risposta_grezza_base[ch] = (hill(a_base, ec, c["slope"])
                                    * (pop * mg)[None, :])

    # ---- 6. baseline organica dominante + controlli -------------------------
    base_naz = BASELINE_NAZIONALE + BASELINE_TREND_SETT * t
    baseline = base_naz[:, None] * (pop * mult_base)[None, :] * seas_reg

    controlli, effetto_ctrl = {}, np.zeros((n, R))
    for nome, d in CONTROLLI.items():
        livello = (d["livello"] + d["trend"] * t)[:, None] * pop[None, :]
        parte_seas = 1.0 + d["accoppiamento"] * (seas_reg - 1.0)
        rumore_ctrl = rng.normal(0.0, d["rumore_sd"] * np.sqrt(pop)[None, :], (n, R))
        serie = np.maximum(livello * parte_seas + rumore_ctrl, 0.0).round(0)
        controlli[nome] = serie
        effetto_ctrl += d["coef_vero"] * (serie - serie.mean(axis=0, keepdims=True))

    # ---- 7. calibrazione di beta sulla quota di contributo media ------------
    organico_tot = float(baseline.sum() + effetto_ctrl.sum())
    quote_ch = {ch: CANALI[ch]["quota_kpi"] for ch in canali}
    S = sum(quote_ch.values())
    if abs(S - quota_media) > 1e-9:              # riscala per centrare il target
        quote_ch = {ch: q * quota_media / S for ch, q in quote_ch.items()}
        S = quota_media
    totale_atteso = organico_tot / (1.0 - S)
    beta, risposta = {}, {}
    for ch in canali:
        # beta dal mondo NON modificato: e' il punto della patch. Calibrandolo
        # sulla spesa modificata, il contributo del canale tornerebbe per
        # costruzione a quota_kpi x totale_atteso e il riparto non si vedrebbe.
        grezzo = float(risposta_grezza_base[ch].sum())
        beta[ch] = quote_ch[ch] * totale_atteso / max(grezzo, 1e-12)
        risposta[ch] = beta[ch] * risposta_grezza[ch]

    media_tot = sum(r.sum() for r in risposta.values())

    # ---- 8. outcome osservato: conteggi interi, rumore non gaussiano --------
    mu = np.maximum(baseline + effetto_ctrl + sum(risposta.values()), 0.1)
    if rumore == "nb":
        # NB2: Var = mu + mu^2/phi, come mistura Gamma-Poisson
        lam_g = rng.gamma(shape=NB_PHI, scale=mu / NB_PHI)
        candidature = rng.poisson(lam_g)
    else:
        candidature = np.maximum(np.round(
            mu + rng.normal(0.0, RUMORE_NORMALE_CV * mu)), 0).astype(int)

    # ---- 9. conversioni dichiarate dalle piattaforme ------------------------
    # per campagna: contributo vero del canale x misattribuzione x quota di
    # qualita' (e' l'ordinamento intra-canale che lo stage 2 assume informativo)
    # x rumore di attribuzione (la piattaforma sbaglia il MERITO RELATIVO).
    #
    # Il rumore di attribuzione usa un rng DEDICATO (seed+11): cosi' tutto il
    # resto del mondo - spesa, impression, clic, candidature, contributo vero -
    # resta bit-identico a prima che questo meccanismo esistesse.
    rng_attr = np.random.default_rng(seed + 11)
    n_trim = int(np.ceil(n / 13))
    trimestre_di = np.repeat(np.arange(n_trim), 13)[:n]
    fattori_attr = {}
    camp_conv = {}
    for ch in canali:
        camps = [cp for cp, c in CAMPAGNE.items() if c["canale"] == ch]
        qual_spesa = np.stack([CAMPAGNE[cp]["qualita"] * camp_spesa[cp]
                               for cp in camps])
        quota_q = qual_spesa / np.maximum(qual_spesa.sum(axis=0), 1e-9)

        # fattore di mis-riporto per campagna, costante ENTRO il trimestre e
        # correlato fra trimestri: una campagna sovra-riportata tende a restare
        # tale (piu' view-through, finestre di conversione piu' generose).
        # Un rumore bianco per osservazione si medierebbe via nell'aggregazione
        # e l'ordinamento tornerebbe perfetto.
        z = np.empty((len(camps), n_trim))
        z[:, 0] = rng_attr.normal(0.0, sigma_attr, len(camps))
        sd_innov = sigma_attr * np.sqrt(max(1.0 - RUMORE_ATTRIBUZIONE_RHO ** 2, 0.0))
        for q in range(1, n_trim):
            z[:, q] = (RUMORE_ATTRIBUZIONE_RHO * z[:, q - 1]
                       + rng_attr.normal(0.0, sd_innov, len(camps)))
        fatt = np.exp(z)[:, trimestre_di]                    # (C, n)
        for i, cp in enumerate(camps):
            fattori_attr[cp] = fatt[i].copy()

        # rinormalizzazione dentro il canale: il fattore sposta solo lo SPLIT
        # fra campagne, non il totale dichiarato di canale. ROAS di canale,
        # misattribuzione e fattore k restano quelli calibrati.
        quota_mod = quota_q * fatt[:, :, None]
        quota_mod = quota_mod / np.maximum(quota_mod.sum(axis=0), 1e-12)

        dichiarate = CANALI[ch]["misattr"] * risposta[ch]
        for i, cp in enumerate(camps):
            v = (dichiarate * quota_mod[i]
                 * rng.normal(1.0, 0.08, (n, R)).clip(0.6, 1.5))
            camp_conv[cp] = np.round(v).astype(int)

    return dict(
        settimane=settimane, regioni=regioni, pop=pop, canali=canali,
        seas_reg=seas_reg, seas_naz=seas_naz,
        spesa_naz=spesa_naz, kappa=kappa_scelto,
        camp_spesa=camp_spesa, camp_impr=camp_impr, camp_clic=camp_clic,
        camp_conv=camp_conv, attive=attive,
        ch_spesa=ch_spesa, ch_impr=ch_impr,
        baseline=baseline, controlli=controlli, effetto_ctrl=effetto_ctrl,
        risposta=risposta, beta=beta, beta_geo=beta_geo, mult_base=mult_base,
        mu=mu, candidature=candidature,
        quota_media_realizzata=float(media_tot / (organico_tot + media_tot)),
        quote_canale=quote_ch, rumore=rumore, seed=seed,
        pause_spec=pause_spec, pause_diario=pause_diario,
        sanita_spec=sanita_spec, sanita_diario=sanita_diario,
        casuale2_spec=casuale2_spec, casuale2_diario=casuale2_diario,
        geo_spec=geo_spec, geo_piano=geo_piano, geo_diario=geo_diario,
        riparto_spec=riparto_spec, riparto_diario=riparto_diario,
        ch_spesa_base=ch_spesa_base,
    )


# =============================================================================
# Scrittura dei file
# =============================================================================

def _data(s: pd.Timestamp) -> str:
    return (pd.Timestamp(s).strftime("%d/%m/%Y") if FORMATO_SPORCO
            else pd.Timestamp(s).strftime("%Y-%m-%d"))


def _num(x: float, dec: int = 2) -> str:
    if not FORMATO_SPORCO:
        return f"{x:.{dec}f}"
    return f"{x:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _lungo(arr_per_camp: dict, camps: list[str], nome: str,
           settimane, regioni) -> pd.DataFrame:
    frames = []
    for cp in camps:
        f = pd.DataFrame(arr_per_camp[cp], index=settimane, columns=regioni)
        f = f.stack().rename(nome).reset_index()
        f.columns = ["settimana", "regione", nome]
        f["campagna"] = cp
        frames.append(f)
    return pd.concat(frames, ignore_index=True)


def scrivi_media(p: dict, dir_out: str) -> list[str]:
    """Un file per piattaforma, colonne del formato richiesto all'azienda."""
    nomi_file = {
        "Google Ads": "google_ads_settimanale.csv",
        "Meta Ads": "meta_ads_settimanale.csv",
        "LinkedIn Ads": "linkedin_ads_settimanale.csv",
        "Indeed": "indeed_settimanale.csv",
        "Subito Lavoro": "subito_lavoro_settimanale.csv",
        "Jooble": "jooble_settimanale.csv",
        "Altre job board": "altre_job_board_settimanale.csv",
    }
    scritti = []
    for ch in p["canali"]:
        camps = [cp for cp, c in CAMPAGNE.items() if c["canale"] == ch]
        df = _lungo(p["camp_spesa"], camps, "spesa", p["settimane"], p["regioni"])
        for nome, src in (("impressioni", p["camp_impr"]),
                          ("clic", p["camp_clic"]),
                          ("conversioni_piattaforma", p["camp_conv"])):
            df = df.merge(_lungo(src, camps, nome, p["settimane"], p["regioni"]),
                          on=["settimana", "regione", "campagna"])
        df = df[df["spesa"] > 0].copy()          # settimane spente: nessuna riga
        df["canale"] = ch
        df["settimana"] = df["settimana"].map(_data)
        df["spesa"] = df["spesa"].map(lambda v: _num(v, 2))
        for c in ("impressioni", "clic", "conversioni_piattaforma"):
            df[c] = df[c].astype(int)
        df = df[["settimana", "regione", "canale", "campagna", "spesa",
                 "impressioni", "clic", "conversioni_piattaforma"]]
        df = df.sort_values(["settimana", "regione", "campagna"])
        path = os.path.join(dir_out, nomi_file[ch])
        df.to_csv(path, index=False, sep=";" if FORMATO_SPORCO else ",",
                  encoding="utf-8")
        scritti.append(os.path.basename(path))
    return scritti


def scrivi_kpi_e_controlli(p: dict, dir_out: str) -> list[str]:
    settimane, regioni = p["settimane"], p["regioni"]
    n, R = len(settimane), len(regioni)
    scritti = []

    kpi = pd.DataFrame({
        "settimana": np.repeat([_data(s) for s in settimane], R),
        "regione": np.tile(regioni, n),
        "candidature": p["candidature"].ravel().astype(int)})
    kpi.to_csv(os.path.join(dir_out, "candidature_settimanali.csv"), index=False)
    scritti.append("candidature_settimanali.csv")

    for nome, file_out in (("richieste_clienti", "richieste_clienti.csv"),
                           ("ricerche_candidati", "ricerche_candidati.csv")):
        df = pd.DataFrame({
            "settimana": np.repeat([_data(s) for s in settimane], R),
            "regione": np.tile(regioni, n),
            nome: p["controlli"][nome].ravel().astype(int)})
        df.to_csv(os.path.join(dir_out, file_out), index=False)
        scritti.append(file_out)

    stag = pd.DataFrame({
        "settimana": [_data(s) for s in settimane],
        "indice_stagionale": np.round(p["seas_naz"], 4)})
    # float_format: senza, pandas scrive 0.9290 come 0.929 e il parser
    # dell'ingestion lo scambia per un migliaia italiano (929.0). Sono le
    # 8 righe su 104 del bug del controllo stagionale: quarta cifra zero.
    stag.to_csv(os.path.join(dir_out, "stagionalita.csv"), index=False,
                float_format="%.4f")
    scritti.append("stagionalita.csv")

    popol = pd.DataFrame({
        "regione": regioni,
        "popolazione": np.round(p["pop"] * POPOLAZIONE_ITALIA).astype(int)})
    popol.to_csv(os.path.join(dir_out, "popolazione_regioni.csv"), index=False)
    scritti.append("popolazione_regioni.csv")
    return scritti


def _trimestre(s: pd.Timestamp) -> str:
    s = pd.Timestamp(s)
    return f"{s.year}Q{(s.month - 1) // 3 + 1}"


def scrivi_benchmark(p: dict, dir_out: str, suffisso: str = "") -> dict:
    """Due oggetti diversi, che la tesi tiene distinti.

    roas_piattaforma_trimestrale.csv
        cio' che ogni piattaforma dichiara di aver generato, per campagna.
        NON deduplicato tra piattaforme, regole di attribuzione proprietarie.
        Serve all'ORDINAMENTO intra-canale dello stage 2.

    benchmark_interno_trimestrale.csv
        calcolo interno GA4 x database: regola unica per tutti i canali,
        deduplicato, ancorato alle candidature vere. Si ferma al CANALE.
        E' la fonte del fattore k della Sez. 3.8.
    """
    settimane = p["settimane"]
    tri = np.array([_trimestre(s) for s in settimane])
    val = VALORE_CANDIDATURA_EUR

    righe = []
    for cp, c in CAMPAGNE.items():
        for q in pd.unique(tri):
            m = tri == q
            spesa = float(p["camp_spesa"][cp][m].sum())
            conv = int(p["camp_conv"][cp][m].sum())
            if spesa <= 0:
                continue
            righe.append({
                "trimestre": q, "canale": c["canale"], "campagna": cp,
                "spesa": round(spesa, 2), "conversioni_dichiarate": conv,
                "roas_dichiarato": round(conv * val / spesa, 3)})
    plat = pd.DataFrame(righe).sort_values(["trimestre", "canale", "campagna"])
    f1 = f"roas_piattaforma_trimestrale{suffisso}.csv"
    plat.to_csv(os.path.join(dir_out, f1), index=False)

    righe = []
    for ch in p["canali"]:
        bias = CANALI[ch]["bias_bench"]
        for q in pd.unique(tri):
            m = tri == q
            spesa = float(p["ch_spesa"][ch][m].sum())
            if spesa <= 0:
                continue
            attribuite = float(p["risposta"][ch][m].sum()) * bias
            righe.append({
                "trimestre": q, "canale": ch, "spesa": round(spesa, 2),
                "candidature_attribuite": int(round(attribuite)),
                "roas_attribuito": round(attribuite * val / spesa, 3)})
    interno = pd.DataFrame(righe).sort_values(["trimestre", "canale"])
    f2 = f"benchmark_interno_trimestrale{suffisso}.csv"
    interno.to_csv(os.path.join(dir_out, f2), index=False)
    return {"piattaforma": plat, "interno": interno, "file": [f1, f2]}


def costruisci_parametri(p: dict, quota_media: float) -> dict:
    """Verita' del processo generativo (parametri_generazione.json)."""
    val = VALORE_CANDIDATURA_EUR
    canali = {}
    for ch in p["canali"]:
        spesa = float(p["ch_spesa"][ch].sum())
        inc = float(p["risposta"][ch].sum())
        canali[ch] = {
            "nota_economica": CANALI[ch]["nota"],
            "adstock_lambda": CANALI[ch]["lam"],
            "hill_slope": CANALI[ch]["slope"],
            "hill_ec_moltiplicatore_esecuzione_media": CANALI[ch]["ec_mult"],
            "hill_ec_in_impression_procapite": round(CANALI[ch]["_ec_impr"], 1),
            "beta": round(float(p["beta"][ch]), 4),
            "dispersione_beta_geo_sd_log": DISPERSIONE_BETA_GEO,
            "spesa_totale_eur": round(spesa, 2),
            "spesa_media_settimanale_eur": round(spesa / N_SETTIMANE, 2),
            "candidature_incrementali_vere": round(inc, 1),
            "quota_sulle_candidature_totali": round(
                inc / float(p["candidature"].sum()), 4),
            "roi_vero_eur_per_eur": round(inc * val / spesa, 3),
            "cpa_incrementale_vero_eur": round(spesa / inc, 2),
            "misattribuzione_piattaforma": CANALI[ch]["misattr"],
            "bias_benchmark_interno": CANALI[ch]["bias_bench"],
            "k_atteso_roi_su_benchmark": round(1.0 / CANALI[ch]["bias_bench"], 3),
            "settimane_a_spesa_zero": int((p["ch_spesa"][ch].sum(axis=1) == 0).sum()),
            "pavimento_settimanale_eur": CANALI[ch]["pavimento"],
            "kappa_accoppiamento_stagionale": round(p["kappa"][ch], 3),
            "beta_per_regione": {r: round(float(v * p["beta"][ch]), 5)
                                 for r, v in zip(p["regioni"], p["beta_geo"][ch])},
        }
    campagne = {}
    for cp, c in CAMPAGNE.items():
        spesa = float(p["camp_spesa"][cp].sum())
        campagne[cp] = {
            "canale": c["canale"],
            "qualita_relativa_vera": c["qualita"],
            "quota_spesa_di_canale": round(
                spesa / float(p["ch_spesa"][c["canale"]].sum()), 4),
            "cpm_eur": c["cpm"], "ctr": c["ctr"],
            "cpc_implicito_eur": round(c["cpm"] / (1000 * c["ctr"]), 3),
            "settimane_attive": int(p["attive"][cp].sum()),
            "finestra": ("flight " + str(c["flight"]) if "flight" in c
                         else str(c.get("attiva", (0, N_SETTIMANE - 1)))),
        }
    return {
        "_AVVERTENZA": (
            "Questi parametri servono a ILLUSTRARE il comportamento del sistema "
            "nel Capitolo 5, NON a rivendicare una validazione per parameter "
            "recovery. Nel testo della tesi non si scrive mai 'validato'. Il "
            "dataset e' simulato e va dichiarato tale."),
        "_AVVERTENZA_PESI": (
            "La ripartizione della spesa tra canali e tra job board e' un "
            "parametro di generazione scelto per plausibilita', NON una stima "
            "di quote di mercato. Gli unici fatti di mercato usati sono: Indeed "
            "prima per traffico nella categoria lavoro in Italia, e la chiusura "
            "di InfoJobs il 31/12/2025 (annunci confluiti in Subito). Monster "
            "non e' piu' operativa e non compare. Tutto il resto e' calibrazione "
            "dell'autore."),
        "_AVVERTENZA_TARATURA": (
            "Tre parametri sono stati tarati DOPO aver visto i numeri, e la cosa va dichiarata nel Cap. 5. (1) La quota KPI di LinkedIn e' stata portata da 0,015 a 0,013: a 0,015 il ROI vero usciva 1,00 esatto e il pavimento di spesa non avrebbe avuto mordente, quindi lo scenario non avrebbe illustrato la Sez. 3.7. (2) La griglia di calibrazione dell'accoppiamento stagionale e' stata allargata perche' su Jooble e Altre job board la correlazione si fermava a 0,32-0,36, sotto la banda richiesta. (3) La sd del rumore di attribuzione intra-canale e' stata scelta per ricerca su griglia (banda obiettivo per lo Spearman medio fra canali: 0,70-0,90, fissata PRIMA di vedere i risultati). Senza quel rumore lo Spearman fra ROAS dichiarato e qualita' vera era 1,00 su sei canali su sette: l'assunzione della Sez. 3.8 sarebbe stata vera per costruzione. La scelta e' fatta sul valore ATTESO su 8 seed, non sul realizzato a seed 42, perche' con 4-6 campagne per canale una sola realizzazione dice piu' sul seed che sul meccanismo. Sono scelte di progetto dello scenario dimostrativo, non stime; dichiararle e' cio' che distingue una simulation study da un risultato costruito."
        ),
        "_AVVERTENZA_FINESTRA_STAGE2": (
            "Lo Spearman intra-canale dipende dalla finestra: con la sd scelta l'atteso e' 0,73 sui due anni ma 0,69 sull'ultimo trimestre, ed e' l'ultimo trimestre che lo stage 2 consuma davvero (window_weeks=13 in pipeline/allocator/campaigns.py; il trimestre piu' recente nel notebook). L'assunzione della Sez. 3.8 si indebolisce proprio nella finestra che il sistema usa. Non e' un difetto della calibrazione: e' un limite del metodo, da dichiarare nel Cap. 5 e da mettere in roadmap nel Cap. 7 (allungare la finestra dello stage 2, o pesare piu' trimestri). Avvertenza di lettura: con 4-6 campagne per canale lo Spearman e' grossolano (con 4 campagne uno scambio adiacente vale gia' 0,80), quindi va letto come indicatore aggregato e non canale per canale."
        ),
        "_AVVERTENZA_K": (
            "k = ROI_MMM / ROAS_benchmark e' costante dentro il canale: si "
            "semplifica nella normalizzazione delle quote dello stage 2, quindi "
            "NON sposta budget e NON cambia l'ordinamento delle campagne. Serve "
            "a riportare i ROAS di campagna sulla scala incrementale, cioe' a "
            "renderli confrontabili TRA canali. E' una correzione di lettura."),
        "seed": p["seed"],
        "n_settimane": N_SETTIMANE,
        "prima_settimana": str(p["settimane"][0].date()),
        "ultima_settimana": str(p["settimane"][-1].date()),
        "valuta": VALUTA,
        "valore_candidatura_eur": val,
        "rumore_osservativo": {
            "tipo": p["rumore"],
            "nb_phi": NB_PHI if p["rumore"] == "nb" else None,
            "nota": ("binomiale negativa sul conteggio (Var = mu + mu^2/phi): "
                     "realistica, ma eteroschedastica rispetto alla "
                     "verosimiglianza normale di Meridian. Switch in CONFIG "
                     "(RUMORE='normale') per isolarne l'effetto."),
        },
        "rumore_attribuzione_intra_canale": {
            "sd_log": RUMORE_ATTRIBUZIONE_SD,
            "rho_fra_trimestri": RUMORE_ATTRIBUZIONE_RHO,
            "dove_agisce": ("solo sulle conversioni DICHIARATE dalle "
                            "piattaforme, per campagna"),
            "nota": ("fattore moltiplicativo per campagna, costante entro il "
                     "trimestre e correlato fra trimestri, indipendente dalla "
                     "qualita' vera e rinormalizzato dentro il canale: sposta "
                     "lo SPLIT fra campagne, non il totale dichiarato di "
                     "canale. Il benchmark interno (livello canale, regola "
                     "unica) non lo riceve. Estratto da un rng dedicato "
                     "(seed+11), cosi' spesa, impression, clic, candidature e "
                     "contributo vero restano identici a sigma qualunque."),
        },
        "trasformazioni": {
            "adstock": "geometrico normalizzato, pesi lam^l / somma(lam^l), max_lag=8",
            "saturazione": "Hill: a^slope / (a^slope + ec^slope)",
            "metrica_di_esecuzione": "impression (quella che il notebook passa a Meridian)",
            "scala": "per quota di popolazione: stessa curva in ogni regione",
            "nota_geo": ("la dispersione regionale e' SOLO su beta (analogo di "
                         "beta_gm/eta_m) e sull'intercetta di baseline: in "
                         "Meridian adstock e Hill sono nazionali, estrarli per "
                         "regione sarebbe una misspecificazione, non partial pooling."),
        },
        "quota_media_target": quota_media,
        "quota_media_realizzata": round(p["quota_media_realizzata"], 4),
        "candidature_totali": int(p["candidature"].sum()),
        "spesa_totale_eur": round(sum(float(v.sum()) for v in p["ch_spesa"].values()), 2),
        "baseline": {
            "livello_nazionale_settimanale": BASELINE_NAZIONALE,
            "trend_per_settimana": BASELINE_TREND_SETT,
            "dispersione_geo_sd_log": BASELINE_DISPERSIONE_GEO,
            "moltiplicatori_regionali": {r: round(float(v), 4) for r, v
                                         in zip(p["regioni"], p["mult_base"])},
        },
        "controlli": {k: {"coef_vero": v["coef_vero"],
                          "accoppiamento_stagionale": v["accoppiamento"]}
                      for k, v in CONTROLLI.items()},
        "stagionalita": {
            "struttura": ("composita: picco estivo (turismo/agricoltura) + picco "
                          "Q4 (logistica/GDO), con pesi REGIONALI diversi"),
            "indice_nazionale_pubblicato": (
                "media pesata per popolazione: e' il solo indice che l'azienda "
                "osserva; la parte regionale resta non osservata, come nella realta'"),
            "vocazione_estiva_per_regione": VOCAZIONE_ESTIVA,
            "indice_nazionale_per_settimana": {
                str(s.date()): round(float(v), 4)
                for s, v in zip(p["settimane"], p["seas_naz"])},
        },
        "canali": canali,
        "campagne": campagne,
        "scenario_allocatore": {
            "descrizione": (
                "Pavimento di spesa su LinkedIn (employer branding): il canale "
                "non scende sotto la soglia anche se il ROI di breve non lo "
                "giustifica. Con il vincolo attivo l'eguaglianza dei rendimenti "
                "marginali vale tra i soli canali liberi (Sez. 3.7)."),
            "pavimento_settimanale_eur": CANALI["LinkedIn Ads"]["pavimento"],
            "pavimento_trimestrale_eur": CANALI["LinkedIn Ads"]["pavimento"] * 13,
            "notebook_cella_12": {
                "VINCOLI_PER_CANALE": {"LinkedIn Ads": [0.0, 0.30]},
                "nota": "limite inferiore 0.0 = non scendere sotto la spesa storica",
            },
            "pipeline_allocator": (
                "python -m pipeline.allocator.run --budget <B> --min linkedin="
                + str(int(CANALI["LinkedIn Ads"]["pavimento"] * 13))),
        },
        **({"scenario_pause": {
            "descrizione": (
                "Blackout veri su una parte dei canali, per misurare se "
                "interrompere la spesa basta a rendere misurabile un canale. "
                "Rispetto alla base cambia UNA cosa sola: il momento in cui la "
                "spesa avviene. Il livello di spesa per canale e' identico."),
            "canali_trattati": sorted(p["pause_spec"]["blocchi"]),
            "canali_di_controllo": list(p["pause_spec"]["controlli"]),
            "lunghezza_blocco_settimane": p["pause_spec"]["lunghezza_blocco"],
            "blocchi_per_canale_1based_inclusivi":
                {ch: [list(b) for b in bl]
                 for ch, bl in p["pause_spec"]["blocchi_1based"].items()},
            "effetto_per_canale": p["pause_diario"],
            "regola_di_ridistribuzione": (
                "La spesa delle settimane spente e' ridistribuita sulle "
                "settimane attive dello STESSO canale, in proporzione al "
                "profilo settimanale che il canale ha nella base: "
                "y[attive] = x[attive] * (1 + tolta/resto). Il totale a 104 "
                "settimane per canale resta quello della base. I canali di "
                "controllo non vengono toccati."),
            "perche_questo_disegno": {
                "blocco_piu_lungo_del_carryover": (
                    "MAX_LAG = 8 con adstock geometrico normalizzato: una pausa "
                    "di una o due settimane viene riempita dal carryover e non "
                    "produce variazione identificante. Il blocco e' lungo 8 "
                    "settimane proprio per superare la memoria dell'adstock."),
                "gruppo_di_controllo_interno": (
                    "Se si fermassero tutti i canali non ci sarebbe un termine "
                    "di paragone dentro lo stesso dataset. I 4 canali di "
                    "controllo restano identici alla base e sono appaiati ai "
                    "trattati per dimensione (Google/Meta, Indeed/LinkedIn, "
                    "Jooble/Altre+Subito), cosi' l'effetto della pausa non si "
                    "confonde con la dimensione del canale."),
                "spesa_conservata": (
                    "Togliendo e basta la spesa delle settimane spente, il "
                    "confronto base-vs-pause2 sarebbe confuso dal livello di "
                    "spesa oltre che dal suo profilo temporale. Ridistribuendola "
                    "resta una sola differenza."),
                "blocchi_lontani_dai_bordi": (
                    "Tutti i blocchi stanno fuori dalle prime 8 e dalle ultime 8 "
                    "settimane: il notebook taglia la prima e l'ultima settimana, "
                    "e nelle prime MAX_LAG settimane l'adstock e' parziale."),
                "blocchi_non_sovrapposti": (
                    "I blocchi dei tre trattati non condividono nessuna "
                    "settimana: i canali restano distinguibili fra loro."),
            },
            "nota_sulle_pause_ereditate_dalla_base": (
                "Oltre ai blocchi, i canali conservano le settimane_spente che "
                "hanno gia' nella base (Indeed 3, Jooble 12): non sono state "
                "rimosse per non introdurre una seconda differenza rispetto "
                "alla base, dove quelle stesse settimane sono spente."),
        }} if p.get("pause_spec") else {}),
        **({"scenario_sanita": {
            "descrizione": (
                "Spesa completamente randomizzata. Per ogni canale la spesa "
                "settimanale nazionale e il riparto regionale sono estratti in "
                "modo indipendente: nessun legame con la stagionalita', con i "
                "controlli di domanda, con la spesa degli altri canali, ne' con "
                "la propria spesa delle settimane precedenti. Rispetto alla base "
                "cambia UNA cosa sola: come viene decisa la spesa. Il livello di "
                "spesa per canale e' identico."),
            "a_cosa_serve": (
                "E' il caso limite in cui l'identificazione e' massimamente "
                "facilitata, e serve come CONTROLLO DI SANITA' sul metodo, non "
                "come scenario realizzabile in azienda: nessun reparto media "
                "pianifica a sorte, e nemmeno potrebbe. Tutti gli altri dataset "
                "misurano quanto il modello sbaglia in condizioni difficili; "
                "questo misura il caso opposto, quello in cui il modello DEVE "
                "riuscire. Se qui il contributo vero non viene recuperato, il "
                "problema non e' l'identificazione ma l'implementazione, e le "
                "conclusioni degli altri run vanno riviste. E' il test che rende "
                "credibile il resto del lavoro."),
            "distribuzione": {
                "famiglia": "lognormale, estrazioni iid sulle 104 settimane",
                "centratura": (
                    "mu = log(media) - sigma^2/2, con media = media settimanale "
                    "REALIZZATA del canale nella base (totale base / 104): cosi' "
                    "il valore atteso coincide con la media della base"),
                "sigma_log_nazionale": SANITA_SIGMA_LOG_NAZIONALE,
                "sigma_log_regionale": SANITA_SIGMA_LOG_REGIONALE,
                "perche_questa": (
                    "e' la distribuzione positiva piu' semplice con un solo "
                    "parametro di ampiezza e non richiede troncature. La sigma "
                    "nazionale 0,60 e' scelta sul requisito del disegno: il "
                    "rapporto atteso fra decile alto e decile basso vale "
                    "exp(2 x 1,2816 x sigma) = 4,65, sopra il fattore 4 "
                    "richiesto. E' l'ampiezza a rendere facile il problema: la "
                    "spesa spazza tutta la curva di risposta invece di oscillare "
                    "attorno al proprio livello."),
            },
            "regola_di_riscalatura": (
                "Dopo l'estrazione la serie di ogni canale viene moltiplicata "
                "per totale_base / somma_estratta, cosi' il totale sulle 104 "
                "settimane coincide con quello della base. Il fattore e' "
                "costante: non tocca ne' le correlazioni, ne' l'autocorrelazione, "
                "ne' il rapporto fra i decili, quindi la serie resta iid. Serve "
                "perche' il confronto base-vs-sanita non sia confuso dal livello "
                "di spesa, come gia' fatto per pause2."),
            "riparto_regionale": (
                "Randomizzato anche quello, perche' il disegno chiede "
                "indipendenza su ogni coppia regione-settimana: la quota di ogni "
                "regione e' proporzionale alla popolazione a meno di uno shock "
                "lognormale iid (sd del log 0,25, la stessa dispersione "
                "regionale complessiva della base, che li' e' pero' persistente "
                "- tilt fisso di campagna piu' AR(1) - e in parte stagionale, "
                "per via delle spinte regionali agganciate alla settimana "
                "dell'anno). Restare proporzionali alla popolazione IN MEDIA e' "
                "deliberato: un riparto uniforme fra regioni darebbe alla Valle "
                "d'Aosta la stessa spesa della Lombardia, saturerebbe la Hill "
                "nelle regioni piccole e renderebbe il problema piu' difficile, "
                "non piu' facile."),
            "dove_agisce": (
                "sulla pianificazione della spesa dentro genera(), PRIMA del "
                "passo di risposta media (adstock + Hill), come per pause2: "
                "impression, clic, KPI, benchmark e verita' discendono tutti dal "
                "nuovo percorso di spesa. I CSV non sono mai post-processati."),
            "cosa_sparisce_rispetto_alla_base": {
                "settimane_spente": (
                    "il campo settimane_spente dei canali non viene applicato: "
                    "una settimana spenta a indice fisso e' un pattern di "
                    "pianificazione, e il disegno chiede che non ce ne siano. "
                    "Nella base erano 27 in tutto (Meta 2, Indeed 3, Subito "
                    "Lavoro 4, Jooble 12, Altre job board 6); qui nessun canale "
                    "ha settimane a spesa zero."),
                "pavimento_di_spesa": (
                    "il pavimento settimanale di LinkedIn non viene applicato: "
                    "troncherebbe la lognormale dal basso e reintrodurrebbe una "
                    "regola di pianificazione. La chiave scenario_allocatore "
                    "qui sopra descrive la base, non questa variante."),
                "nota_sul_livello": (
                    "toglierle non sposta il livello di spesa: la conservazione "
                    "e' fatta sul TOTALE della base, che quelle regole le "
                    "contiene gia'."),
            },
            "cosa_resta_identico_alla_base": (
                "seed 42, 20 regioni, 104 settimane, 7 canali, parametri veri "
                "(adstock lambda, Hill ec e slope, beta ricalibrato sullo stesso "
                "target del 18,5%), controlli di domanda, stagionalita' "
                "sottostante della DOMANDA, campagne con le stesse finestre di "
                "attivita' e lo stesso rumore sulla quota di campagna, rumore di "
                "attribuzione intra-canale, rumore osservativo. Le finestre di "
                "campagna restano perche' spostano solo lo SPLIT dentro il "
                "canale, non la spesa del canale, che e' il livello su cui il "
                "disegno chiede l'indipendenza. La randomizzazione usa un rng "
                "dedicato (seed+" + str(SANITA_SEED_OFFSET) + "), quindi i beta "
                "per regione e i moltiplicatori di baseline sono gli STESSI "
                "numeri della base."),
            "campi_inerti_in_questa_variante": [
                "canali[*].kappa_accoppiamento_stagionale: e' il valore calibrato "
                "sul percorso di spesa della base, che qui viene scartato. In "
                "sanita l'accoppiamento stagionale della spesa e' zero per "
                "costruzione.",
                "canali[*].pavimento_settimanale_eur: riportato per confronto con "
                "la base, ma non applicato.",
                "scenario_allocatore: descrive il vincolo della base.",
            ],
            "effetto_per_canale": p["sanita_diario"],
        }} if p.get("sanita_spec") else {}),
        **({"scenario_casuale2": {
            "descrizione": (
                "Spesa SCORRELATA dalla stagionalita' ma pianificata: restano "
                "l'AR(1), i gradini trimestrali, le settimane spente e il "
                "pavimento della base; sparisce solo l'accoppiamento con "
                "l'indice stagionale. Regime intermedio fra l'osservativo e la "
                "sanita'."),
            "cosa_cambia_nel_generatore": (
                "Due costanti della calibrazione di kappa: il target di "
                "correlazione spesa-stagionalita' (corr_target invece di "
                + str(CORR_SPESA_STAGIONALITA_TARGET) + ") e la griglia su cui "
                "kappa viene scelto (bilaterale, con lo zero esatto dentro, "
                "invece di [0, 5] a 120 punti). Nessuna estrazione casuale in "
                "piu': tutti gli altri numeri del mondo sono quelli della base "
                "con lo stesso seme."),
            "corr_target": p["casuale2_spec"]["corr_target"],
            "griglia_kappa": [p["casuale2_spec"]["griglia_min"],
                              p["casuale2_spec"]["griglia_max"],
                              p["casuale2_spec"]["griglia_punti"]],
            "spesa_totale_per_canale_NON_conservata": (
                "un kappa diverso sposta la media dell'esponenziale: la spesa "
                "totale per canale differisce dalla base (vedi "
                "effetto_per_canale.spesa_vs_base_pct). La verita' per canale "
                "resta quella della base perche' beta e' ricalibrato sullo "
                "stesso target. Va riportata accanto ai risultati, non solo "
                "dichiarata."),
            "effetto_per_canale": p["casuale2_diario"],
        }} if p.get("casuale2_spec") else {}),
        **({"scenario_geo": {
            "descrizione": (
                "Esperimento geografico: per ogni canale trattato la spesa "
                "delle regioni trattate, nei blocchi di settimane trattati, e' "
                "moltiplicata per l'intensita' (0 = spenta) e ridistribuita "
                "sulle altre regioni della stessa settimana. La spesa nazionale "
                "settimanale del canale e' quella della base: cambia solo DOVE "
                "viene spesa. I canali non trattati sono bit-identici alla base "
                "dello stesso seme in spesa, impression e clic."),
            "canali_trattati": list(p["geo_piano"]),
            "n_regioni_per_canale": {ch: len(p["geo_piano"][ch]["regioni"])
                                     for ch in p["geo_piano"]},
            "n_blocchi": p["geo_spec"]["n_blocchi"],
            "lunghezza_blocco_settimane": p["geo_spec"]["lunghezza_blocco"],
            "sfalsato_per_regione": bool(p["geo_spec"].get("sfalsato")),
            "intensita": {
                "moltiplicatore_quota_regioni_trattate": p["geo_spec"]["intensita"],
                "definizione": (
                    "moltiplicatore della quota delle regioni trattate PRIMA "
                    "della rinormalizzazione della settimana. Poiche' la spesa "
                    "nazionale e' conservata, la riduzione effettiva nelle "
                    "regioni trattate e' minore di (1 - moltiplicatore): con il "
                    "27,5% di popolazione trattata e 0,5 e' -42%, non -50%. In "
                    "tesi va effetto_per_canale.riduzione_effettiva_pct."),
            },
            "estrazione": (
                "rng dedicato numpy default_rng(seed + " + str(p["geo_spec"]["seed_offset"]) +
                "); per ogni canale trattato nell'ordine di CANALI: "
                "choice(regioni ordinate, n_regioni, senza reimmissione), poi "
                "inizio del blocco nel primo anno integers(0, 52-L) e nel "
                "secondo 52 + integers(0, 52-L)"
                + ("; poi, per ogni regione trattata, due inizi propri"
                   if p["geo_spec"].get("sfalsato") else "")
                + (". Piano fisso (calendario), nessuna estrazione"
                   if p["geo_spec"].get("piano_fisso") else "")),
            "dove_agisce": (
                "sulle quote regionali di ogni campagna, subito dopo "
                "quote_regionali(), PRIMA del passo di risposta media: "
                "impression, clic, KPI, benchmark e verita' discendono dal nuovo "
                "riparto. Il fattore di riscalo e' uniforme dentro la campagna x "
                "settimana. Le celle a spesa zero non compaiono nei file media "
                "(regola gia' della base: settimane spente = nessuna riga)."),
            "effetto_per_canale": p["geo_diario"],
        }} if p.get("geo_spec") else {}),
        **({"scenario_riparto": {
            "descrizione": (
                "Proposta di riallocazione del budget: il percorso di spesa "
                "settimanale di ogni canale toccato e' scalato da un "
                "moltiplicatore costante, quindi la FORMA del percorso non cambia "
                "e il cpm miscelato del canale resta quello. La spesa totale del "
                "portafoglio e' invariata: la somma dei riparti quadra in euro."),
            "a_cosa_serve": (
                "Misurare sulla verita' del generatore se seguire una regola di "
                "allocazione fa guadagnare candidature rispetto al non far niente "
                "(disegno D11). Non e' uno scenario aziendale ne' un mondo nuovo."),
            "AVVERTENZA_beta_fisso": (
                "beta NON e' ricalibrato sulla spesa modificata. Al passo 7 di "
                "genera(), beta[ch] = quota_kpi x totale_atteso / risposta_grezza, "
                "il che rende il contributo del canale indipendente dalla spesa PER "
                "COSTRUZIONE: con la calibrazione libera, ogni riparto darebbe "
                "esattamente lo stesso contributo vero e qualunque confronto fra "
                "ripartizioni misurerebbe zero. Qui beta viene calibrato sul mondo "
                "NON modificato e il riparto agisce solo attraverso le curve di "
                "Hill. Conseguenza da dichiarare: il numero letto non e' 'un mondo "
                "che il generatore produrrebbe', ma la SUPERFICIE DI RISPOSTA "
                "IMPLICITA nei parametri veri di quel mondo. Anche la mezza "
                "saturazione (ec) resta quella del mondo non modificato, per lo "
                "stesso motivo."),
            "tolleranza_somma_eur": round(tolleranza_riparto(
                [abs(float(np.sum(p["spesa_naz"][ch]))) for ch in p["riparto_spec"]]), 2),
            "effetto_per_canale": {k: v for k, v in p["riparto_diario"].items()
                                   if not k.startswith("_")},
            "scarto_somma_eur": p["riparto_diario"].get("_scarto_eur"),
            "spesa_totale_base_eur": round(float(sum(
                float(np.sum(v)) for v in p["ch_spesa_base"].values())), 2),
            "spesa_totale_dopo_eur": round(float(sum(
                float(np.sum(v)) for v in p["ch_spesa"].values())), 2),
        }} if p.get("riparto_spec") else {}),
        **({"scenario_calendario": {
            "descrizione": (
                "Calendario di esperimenti a rotazione: tutti e sette i canali "
                "trattati, ognuno in un gruppo di regioni DISGIUNTO dagli altri "
                "e in due blocchi da " + str(CALENDARIO_LUNGHEZZA_BLOCCO) +
                " settimane sfalsati di " + str(CALENDARIO_SFASAMENTO) +
                " settimane fra canali consecutivi. Un piano, non "
                "un'estrazione: nessun generatore casuale. La meccanica della "
                "spesa (spenta nelle celle trattate, ridistribuita nella stessa "
                "settimana, spesa nazionale conservata) e' quella di "
                "scenario_geo, che riporta l'effetto per canale."),
            "rotazione": p["geo_spec"]["rotazione"],
            "regola_di_rotazione": (
                "nel mondo con rotazione i il canale k (ordine di CANALI) riceve "
                "il gruppo (k + i) mod " + str(CALENDARIO_N_GRUPPI) + ": sugli 8 "
                "mondi la dose per canale si media invece di favorire il primo "
                "canale dell'elenco. i = posizione del mondo nell'ordine 42, "
                "101, ..., 107 (0..7; 7 mod 7 = 0)."),
            "gruppi_di_regioni": {
                str(g): {"regioni": regs,
                         "quota_popolazione_pct": round(100.0 * sum(
                             REGIONI[r] for r in regs) / sum(REGIONI.values()), 2)}
                for g, regs in enumerate(p["geo_spec"]["gruppi"])},
            "costruzione_dei_gruppi": (
                "regioni ordinate per popolazione decrescente e assegnate a "
                "serpentina: giro 1 gruppi 0..6, giro 2 gruppi 6..0, giro 3 "
                "gruppi 0..5 (3, 3, 3, 3, 3, 3, 2 regioni)"),
            "gruppo_per_canale": p["geo_spec"]["gruppo_per_canale"],
            "blocchi_1based_per_canale": {
                ch: [[a + 1, b + 1] for a, b in p["geo_piano"][ch]["blocchi"]]
                for ch in p["geo_piano"]},
            "dose_per_canale_pct": {
                ch: p["geo_diario"][ch]["dose_popolazione_pct"] for ch in p["geo_piano"]},
            "confondimento_di_dose_dichiarato": (
                "la dose per canale (~14% della popolazione in media) e' circa "
                "meta' di quella del geo canonico (27,6% per Google Ads): un "
                "confronto D2-D1 non distingue interferenza fra canali e dose. "
                "Il controllo a dose pari e' il geo su Google a 3 regioni (D7)."),
        }} if (p.get("geo_spec") or {}).get("nome") == "calendario" else {}),
        "regole_canali_da_aggiungere_in_CONFIG": [
            ["indeed", "Indeed"],
            ["subito|infojobs", "Subito Lavoro"],
            ["jooble", "Jooble"],
            ["bakeca.*lavoro|trovolavoro|careerjet|talent[ _-]?com|adzuna|"
             "jobrapido|monster|job[ _-]?board", "Altre job board"],
        ],
    }


def scrivi_verita(p: dict, dir_out: str, parametri: dict,
                  suffisso: str = "") -> list[str]:
    scritti = []
    path = os.path.join(dir_out, f"parametri_generazione{suffisso}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(parametri, f, indent=2, ensure_ascii=False)
    scritti.append(os.path.basename(path))

    # serie osservata delle candidature organiche: NON entra nel modello
    # (Sez. 3.5: sarebbe un mediatore, non un confondente). Sta qui per la
    # validazione a valle della baseline stimata nel Capitolo 5.
    organico = p["baseline"] + p["effetto_ctrl"]
    obs = np.maximum(organico * np.random.default_rng(p["seed"] + 7)
                     .lognormal(0.0, 0.20, organico.shape), 0.0).round(0)
    n, R = organico.shape
    df = pd.DataFrame({
        "settimana": np.repeat([str(s.date()) for s in p["settimane"]], R),
        "regione": np.tile(p["regioni"], n),
        "candidature_organiche_vere": organico.round(1).ravel(),
        "candidature_organiche_osservate": obs.ravel().astype(int)})
    df.to_csv(os.path.join(dir_out, f"candidature_organiche{suffisso}.csv"),
              index=False)
    scritti.append(f"candidature_organiche{suffisso}.csv")

    # contributo incrementale vero per canale x settimana x regione
    righe = []
    for ch in p["canali"]:
        f = pd.DataFrame(p["risposta"][ch], index=p["settimane"],
                         columns=p["regioni"]).stack().reset_index()
        f.columns = ["settimana", "regione", "candidature_incrementali_vere"]
        f["canale"] = ch
        righe.append(f)
    inc = pd.concat(righe, ignore_index=True)
    inc["settimana"] = inc["settimana"].map(lambda s: str(pd.Timestamp(s).date()))
    inc["candidature_incrementali_vere"] = inc["candidature_incrementali_vere"].round(3)
    inc = inc[["settimana", "regione", "canale", "candidature_incrementali_vere"]]
    # stesso rischio del file stagionale: round(3) + zeri finali cadono ->
    # se mai passasse dall'ingestion, 45.678 diventerebbe 45678
    inc.to_csv(os.path.join(dir_out, f"contributo_vero{suffisso}.csv"), index=False,
               float_format="%.4f")
    scritti.append(f"contributo_vero{suffisso}.csv")
    return scritti


# =============================================================================
# Entry point
# =============================================================================

def esegui(quota_media: float, suffisso: str, rumore: str,
           radice: str | None = None, pause_spec: dict | None = None,
           sanita_spec: dict | None = None, seed: int = SEED,
           casuale2_spec: dict | None = None,
           geo_spec: dict | None = None,
           riparto_spec: dict | None = None) -> dict:
    radice = radice or os.path.join(ROOT, "dati_simulati")
    dir_modello = os.path.join(radice, f"modello{suffisso}")
    dir_bench = os.path.join(radice, "benchmark")
    dir_verita = os.path.join(radice, "verita")
    for d in (dir_modello, dir_bench, dir_verita):
        os.makedirs(d, exist_ok=True)

    print(f"Generazione (seed={seed}, {N_SETTIMANE} settimane, "
          f"quota media target={quota_media:.0%}, rumore={rumore})...")
    p = genera(seed=seed, quota_media=quota_media, rumore=rumore,
               pause_spec=pause_spec, sanita_spec=sanita_spec,
               casuale2_spec=casuale2_spec, geo_spec=geo_spec,
               riparto_spec=riparto_spec)

    files = scrivi_media(p, dir_modello)
    files += scrivi_kpi_e_controlli(p, dir_modello)
    bench = scrivi_benchmark(p, dir_bench, suffisso)
    parametri = costruisci_parametri(p, quota_media)
    ver = scrivi_verita(p, dir_verita, parametri, suffisso)

    print(f"  modello{suffisso}/  " + ", ".join(files))
    print(f"  benchmark/  " + ", ".join(bench["file"]))
    print(f"  verita/     " + ", ".join(ver))
    print(f"\n  candidature totali : {int(p['candidature'].sum()):,}")
    print(f"  spesa totale       : {sum(float(v.sum()) for v in p['ch_spesa'].values()):,.0f} EUR")
    print(f"  quota media (vera) : {p['quota_media_realizzata']:.1%}")
    print("  ROI veri per canale:")
    for ch in p["canali"]:
        d = parametri["canali"][ch]
        print(f"    {ch:<18} ROI {d['roi_vero_eur_per_eur']:>5.2f}   "
              f"quota KPI {d['quota_sulle_candidature_totali']:>6.1%}   "
              f"spesa {d['spesa_totale_eur']:>10,.0f}   "
              f"settimane a zero {d['settimane_a_spesa_zero']:>2}")
    return {"panel": p, "parametri": parametri, "benchmark": bench,
            "dir_modello": dir_modello}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--quota", type=float, default=QUOTA_MEDIA_TARGET,
                    help="quota delle candidature spiegata dai media")
    ap.add_argument("--suffisso", default="",
                    help="suffisso della cartella modello e dei file verita")
    ap.add_argument("--rumore", choices=("nb", "normale"), default=RUMORE)
    ap.add_argument("--tutte", action="store_true",
                    help="genera primaria (18,5%%) + diagnostica (30%%)")
    ap.add_argument("--pause2", action="store_true",
                    help="variante pause2: blackout di 8 settimane su 3 canali, "
                         "spesa conservata, 4 canali di controllo intatti")
    ap.add_argument("--seed-mondo", type=int, default=None,
                    help="studio di copertura: rigenera un MONDO completo con "
                         "questo seme (spesa, rumore, tutto cio' che e' "
                         "casuale). Struttura identica alla base (20 regioni x "
                         "104 settimane x 7 canali, stessi file); output "
                         "autonomo in dati_simulati_mondi/mondo_<N>/ con la SUA "
                         "verita'. Stesso seme = dataset identico byte per "
                         "byte. Indipendente dal seme MCMC del fit (che resta "
                         "42 per tutti i mondi)")
    ap.add_argument("--sanita", action="store_true",
                    help="variante sanita: spesa estratta a sorte (lognormale "
                         "iid, nessun legame con stagionalita', controlli di "
                         "domanda, altri canali o propria storia), totale per "
                         "canale conservato. Controllo di sanita' sul metodo, "
                         "non uno scenario aziendale")
    ap.add_argument("--casuale2", action="store_true",
                    help="variante casuale2: spesa scorrelata dalla "
                         "stagionalita' ma pianificata (AR(1), gradini, "
                         "settimane spente e pavimento restano). Cambiano due "
                         "costanti della calibrazione di kappa (target 0, "
                         "griglia bilaterale a 239 punti): riproduce byte per "
                         "byte dati_simulati/casuale2. Spesa totale per canale "
                         "NON conservata (riportata nel JSON)")
    ap.add_argument("--geo", action="store_true",
                    help="variante geo: esperimento geografico dentro il mondo. "
                         "Default = dati_simulati/geo byte per byte (Google Ads "
                         "e LinkedIn Ads spenti in 6 regioni per canale, due "
                         "blocchi da 8 settimane, spesa nazionale conservata). "
                         "Parametri diversi dai default richiedono --seed-mondo")
    ap.add_argument("--geo-canali", default=",".join(GEO_SPEC_DEFAULT["canali"]),
                    help="canali trattati, separati da virgola (default: "
                         "'Google Ads,LinkedIn Ads')")
    ap.add_argument("--geo-regioni", type=int, default=GEO_SPEC_DEFAULT["n_regioni"],
                    help="regioni trattate per canale (default 6). Con meno "
                         "di 6: le prime n delle stesse 6 estratte per il "
                         "canonico, stessi blocchi (cambia solo la dose)")
    ap.add_argument("--geo-blocchi", default="2x8",
                    help="numero x lunghezza dei blocchi (default 2x8: uno per "
                         "anno; con 1xL un solo blocco)")
    ap.add_argument("--geo-intensita", type=float, default=GEO_SPEC_DEFAULT["intensita"],
                    help="moltiplicatore della quota delle regioni trattate "
                         "prima della rinormalizzazione: 0 = spento (default), "
                         "0,5 = quota dimezzata (riduzione effettiva -42%% con "
                         "il 27,5%% di popolazione trattata: la riporta il JSON)")
    ap.add_argument("--geo-sfalsato", action="store_true",
                    help="blocchi propri per ogni regione trattata (estratti "
                         "dopo quelli standard: i default restano identici)")
    ap.add_argument("--calendario", action="store_true",
                    help="variante calendario: sette canali a rotazione in "
                         "gruppi disgiunti di regioni (3-3-3-3-3-3-2 a "
                         "serpentina per popolazione), due blocchi da 8 "
                         "settimane per canale sfalsati di 7, spesa nazionale "
                         "conservata. Richiede --seed-mondo (nessun dataset "
                         "canonico da sovrascrivere)")
    ap.add_argument("--calendario-rotazione", type=int, default=0,
                    help="rotazione i (0..6): il canale k riceve il gruppo "
                         "(k + i) mod 7. Il notebook la passa dalla posizione "
                         "del mondo nell'ordine 42, 101..107")
    ap.add_argument("--calendario-giri", type=int, default=2,
                    help="giri del calendario: 2 = disegno di D2 (invariato), "
                         "4 = D10, stesso disegno col doppio dei giri")
    ap.add_argument("--riparto", default="",
                    help="sposta budget fra canali a spesa totale costante: "
                         "'Canale=+13.95;Canale=-15.00', percentuali sulla spesa "
                         "nazionale del canale. Scala il percorso settimanale con "
                         "un moltiplicatore costante (la forma non cambia) e vale "
                         "per tutte le campagne del canale. La somma deve essere "
                         "zero IN EURO, altrimenti e' un errore: il totale non si "
                         "tocca. beta resta calibrato sul mondo NON modificato, "
                         "altrimenti il riparto sarebbe invisibile per costruzione "
                         "(vedi il commento accanto ad analizza_riparto)")
    ap.add_argument("--suffisso-mondo", default="",
                    help="con --seed-mondo: etichetta aggiunta al nome della "
                         "cartella del mondo (dati_simulati_mondi/mondo_<N>"
                         "<variante><suffisso-mondo>), per tenere distinte piu' "
                         "varianti dello stesso disegno sullo stesso mondo")
    args = ap.parse_args()

    varianti = [f for f, on in (("--pause2", args.pause2), ("--sanita", args.sanita),
                                ("--casuale2", args.casuale2), ("--geo", args.geo),
                                ("--calendario", args.calendario)) if on]
    if len(varianti) > 1:
        ap.error(" e ".join(varianti) + " si escludono: sono varianti diverse "
                 "dello stesso mondo")
    if args.seed_mondo is not None and args.tutte:
        ap.error("--seed-mondo non si combina con --tutte")
    if args.suffisso_mondo and args.seed_mondo is None:
        ap.error("--suffisso-mondo ha senso solo con --seed-mondo")
    if args.suffisso_mondo and not re.fullmatch(r"[A-Za-z0-9_.-]+", args.suffisso_mondo):
        ap.error("--suffisso-mondo: solo lettere, cifre, _ . -")
    riparto_spec = None
    if args.riparto.strip():
        try:
            riparto_spec = analizza_riparto(args.riparto)
        except ValueError as _e:
            ap.error(str(_e))
        if args.seed_mondo is None:
            ap.error("--riparto richiede --seed-mondo: i dataset di dati_simulati/ "
                     "sono congelati e non si sovrascrivono con una proposta di budget")
    geo_spec = None
    if args.calendario:
        if args.seed_mondo is None:
            ap.error("--calendario richiede --seed-mondo: non esiste un dataset "
                     "canonico del calendario in dati_simulati/")
        if not 0 <= args.calendario_rotazione < CALENDARIO_N_GRUPPI:
            ap.error("--calendario-rotazione fra 0 e " + str(CALENDARIO_N_GRUPPI - 1))
        if args.calendario_giri not in CALENDARIO_INIZI_0BASED:
            ap.error("--calendario-giri ammessi: " + str(sorted(CALENDARIO_INIZI_0BASED)))
        geo_spec = calendario_spec(args.calendario_rotazione, args.calendario_giri)
    if args.geo:
        m = re.fullmatch(r"(\d+)x(\d+)", args.geo_blocchi)
        if not m:
            ap.error("--geo-blocchi: formato NxL, es. 2x8")
        canali_geo = [c.strip() for c in args.geo_canali.split(",") if c.strip()]
        sconosciuti = [c for c in canali_geo if c not in CANALI]
        if sconosciuti or not canali_geo:
            ap.error("--geo-canali: canali sconosciuti " + repr(sconosciuti) +
                     "; ammessi: " + ", ".join(CANALI))
        if not 1 <= args.geo_regioni <= len(REGIONI):
            ap.error("--geo-regioni fra 1 e " + str(len(REGIONI)))
        if not 0.0 <= args.geo_intensita < 1.0:
            ap.error("--geo-intensita in [0, 1)")
        geo_spec = dict(GEO_SPEC_DEFAULT,
                        canali=[c for c in CANALI if c in canali_geo],
                        n_regioni=args.geo_regioni,
                        n_blocchi=int(m.group(1)), lunghezza_blocco=int(m.group(2)),
                        intensita=args.geo_intensita, sfalsato=bool(args.geo_sfalsato))
        if int(m.group(1)) not in (1, 2) or not 1 <= int(m.group(2)) <= 52:
            ap.error("--geo-blocchi: 1 o 2 blocchi, lunghezza 1..52")
        default = all(geo_spec[k] == GEO_SPEC_DEFAULT[k] for k in GEO_SPEC_DEFAULT)
        if not default and args.seed_mondo is None:
            ap.error("--geo con parametri diversi dai default richiede "
                     "--seed-mondo: dati_simulati/geo e' il disegno canonico "
                     "della tesi e non si sovrascrive")

    if args.seed_mondo is not None:
        # Un mondo per lo studio di copertura o per la griglia sperimentale:
        # mai dentro dati_simulati/ (i dataset della tesi sono congelati),
        # sempre nella sua radice. Ogni variante (sanita, pause2, casuale2)
        # e' lo STESSO mondo con una spesa diversa: stesso seme, stessa
        # verita' per canale, cartella col nome della variante.
        variante = ("_sanita" if args.sanita else "_pause2" if args.pause2
                    else "_casuale2" if args.casuale2 else "_geo" if args.geo
                    else "_calendario" if args.calendario else "")
        esegui(args.quota, args.suffisso, args.rumore,
               radice=os.path.join(ROOT, "dati_simulati_mondi",
                                   f"mondo_{args.seed_mondo:04d}"
                                   + variante + args.suffisso_mondo),
               pause_spec=PAUSE2_SPEC if args.pause2 else None,
               sanita_spec=SANITA_SPEC if args.sanita else None,
               casuale2_spec=CASUALE2_SPEC if args.casuale2 else None,
               geo_spec=geo_spec, riparto_spec=riparto_spec,
               seed=args.seed_mondo)
    elif args.geo:
        esegui(args.quota, "_geo", args.rumore,
               radice=os.path.join(ROOT, "dati_simulati", "geo"),
               geo_spec=geo_spec)
    elif args.casuale2:
        esegui(args.quota, "_casuale2", args.rumore,
               radice=os.path.join(ROOT, "dati_simulati", "casuale2"),
               casuale2_spec=CASUALE2_SPEC)
    elif args.pause2:
        esegui(args.quota, "_pause2", args.rumore,
               radice=os.path.join(ROOT, "dati_simulati", "pause2"),
               pause_spec=PAUSE2_SPEC)
    elif args.sanita:
        esegui(args.quota, "_sanita", args.rumore,
               radice=os.path.join(ROOT, "dati_simulati", "sanita"),
               sanita_spec=SANITA_SPEC)
    elif args.tutte:
        esegui(QUOTA_MEDIA_TARGET, "", args.rumore)
        print()
        esegui(0.30, "_diagnostica_q30", args.rumore)
    else:
        esegui(args.quota, args.suffisso, args.rumore)


if __name__ == "__main__":
    main()
