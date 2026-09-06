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

def genera(seed: int = SEED, n_settimane: int = N_SETTIMANE,
           quota_media: float = QUOTA_MEDIA_TARGET,
           rumore: str = RUMORE,
           sigma_attr: float = RUMORE_ATTRIBUZIONE_SD,
           pause_spec: dict | None = None) -> dict:
    rng = np.random.default_rng(seed)
    # Registro di cosa il blackout ha fatto, canale per canale: finisce nel JSON
    # dei parametri, cosi' il disegno resta documentato insieme ai dati.
    pause_diario: dict[str, dict] = {}

    regioni = sorted(REGIONI)
    R = len(regioni)
    n = n_settimane
    pop = np.array([REGIONI[r] for r in regioni])
    pop = pop / pop.sum()
    settimane = pd.date_range(INIZIO, periods=n, freq="W-MON")
    woy = settimane.isocalendar().week.to_numpy().astype(float)
    t = np.arange(n, dtype=float)
    canali = list(CANALI)

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
        corrs = np.array([np.corrcoef(costruisci(k), seas_naz)[0, 1]
                          for k in griglia])
        kappa = float(griglia[int(np.argmin(np.abs(
            corrs - CORR_SPESA_STAGIONALITA_TARGET)))])
        kappa_scelto[ch] = kappa
        x_naz = costruisci(kappa)
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
        spesa_naz[ch] = np.round(x_naz, 2)

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
            sp = sp_naz[:, None] * shares
            impr = (sp / CAMPAGNE[cp]["cpm"] * 1000.0
                    * rng.normal(1.0, 0.03, (n, R)).clip(0.85, 1.15))
            clic = (impr * CAMPAGNE[cp]["ctr"]
                    * rng.normal(1.0, 0.07, (n, R)).clip(0.6, 1.4))
            camp_spesa[cp] = np.round(sp, 2)
            camp_impr[cp] = np.round(impr)
            camp_clic[cp] = np.round(clic)

    ch_spesa = {ch: sum(camp_spesa[cp] for cp, c in CAMPAGNE.items()
                        if c["canale"] == ch) for ch in canali}
    ch_impr = {ch: sum(camp_impr[cp] for cp, c in CAMPAGNE.items()
                       if c["canale"] == ch) for ch in canali}

    # ---- 5. risposta media: adstock + Hill sulla metrica di esecuzione ------
    # La metrica di esecuzione e' l'IMPRESSION (quella che il notebook passa a
    # Meridian). Con CPM di canale stabile spesa e impression sono quasi
    # proporzionali, quindi il ramo che usa la spesa vede la stessa curva.
    mult_base = rng.lognormal(0.0, BASELINE_DISPERSIONE_GEO, R)
    mult_base /= (mult_base * pop).sum()
    beta_geo, risposta_grezza = {}, {}
    for ch in canali:
        c = CANALI[ch]
        mg = rng.lognormal(0.0, DISPERSIONE_BETA_GEO, R)
        mg /= (mg * pop).sum()
        beta_geo[ch] = mg
        # esecuzione "pro-capite" = per quota di popolazione: stessa curva
        # in ogni regione, come assume il modello geo-gerarchico
        impr_pc = ch_impr[ch] / pop[None, :]
        ec = c["ec_mult"] * float(np.mean(ch_impr[ch].sum(axis=1)))
        c["_ec_impr"] = ec
        a = adstock_geometrico(impr_pc, c["lam"])
        risposta_grezza[ch] = (hill(a, ec, c["slope"])
                               * (pop * mg)[None, :])                  # (n, R)

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
        grezzo = float(risposta_grezza[ch].sum())
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
    stag.to_csv(os.path.join(dir_out, "stagionalita.csv"), index=False)
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
    inc.to_csv(os.path.join(dir_out, f"contributo_vero{suffisso}.csv"), index=False)
    scritti.append(f"contributo_vero{suffisso}.csv")
    return scritti


# =============================================================================
# Entry point
# =============================================================================

def esegui(quota_media: float, suffisso: str, rumore: str,
           radice: str | None = None, pause_spec: dict | None = None) -> dict:
    radice = radice or os.path.join(ROOT, "dati_simulati")
    dir_modello = os.path.join(radice, f"modello{suffisso}")
    dir_bench = os.path.join(radice, "benchmark")
    dir_verita = os.path.join(radice, "verita")
    for d in (dir_modello, dir_bench, dir_verita):
        os.makedirs(d, exist_ok=True)

    print(f"Generazione (seed={SEED}, {N_SETTIMANE} settimane, "
          f"quota media target={quota_media:.0%}, rumore={rumore})...")
    p = genera(quota_media=quota_media, rumore=rumore,
               pause_spec=pause_spec)

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
    args = ap.parse_args()

    if args.pause2:
        esegui(args.quota, "_pause2", args.rumore,
               radice=os.path.join(ROOT, "dati_simulati", "pause2"),
               pause_spec=PAUSE2_SPEC)
    elif args.tutte:
        esegui(QUOTA_MEDIA_TARGET, "", args.rumore)
        print()
        esegui(0.30, "_diagnostica_q30", args.rumore)
    else:
        esegui(args.quota, args.suffisso, args.rumore)


if __name__ == "__main__":
    main()
