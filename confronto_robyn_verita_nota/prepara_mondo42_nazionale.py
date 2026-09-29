"""PASSO 1 del confronto Robyn a verita' nota: dal panel regionale del mondo 42
al CSV nazionale settimanale che Robyn sa leggere.

Robyn e' nazionale: le 20 regioni si sommano. E' la prima avvertenza del
confronto e va dichiarata accanto a ogni cifra: l'aggregazione toglie la
dimensione geografica, che e' proprio cio' che nel panel di Meridian dovrebbe
aiutare l'identificazione.

    python prepara_mondo42_nazionale.py

Legge `dati_simulati/modello/` (il dataset congelato della tesi, mondo 42) e
scrive `confronto_robyn_verita_nota/mondo42_nazionale.csv` con 104 righe.
Esegue e riporta i quattro controlli obbligatori (a, b, c, d): se uno fallisce
il file non viene scritto.

La verita' con cui confrontare (non entra nel CSV, sta qui per memoria):
  quota media vera dei media  18,51%
  ROI vero per canale         griglia/griglia_D0_osservativo_canali.csv, seed_mondo = 42
  valore per candidatura      40,00 EUR

COME E' DEFINITA QUELLA QUOTA, E PERCHE' IMPORTA PER ROBYN
----------------------------------------------------------
`quota_media_vera_pct` della griglia e' una QUOTA DI TOTALI, non una media di
quote. Letto dal codice che la calcola (runner della griglia, passo 3):

    vero_conv, _ = verita_del_mondo(percorso_verita, SETTIMANE, canali, pd)
    kpi_tot = float(DF_BASE["kpi"].sum())
    quota_media_vera_pct = round(100 * vero_conv / kpi_tot, 2)

cioe' (somma del contributo vero su canali, settimane e regioni) diviso (somma
del KPI osservato sulla stessa finestra). Stessa forma per la quota STIMATA:
media sui draw del contributo totale, divisa per lo stesso `kpi_tot`.
Nota sul nome: "media" sta per "dei media" (i canali a pagamento), NON per
"valore medio". E' il punto in cui e' facile sbagliare.

Le tre definizioni possibili, misurate sul mondo 42 (totale KPI 855.534,
totale contributo vero 158.330,7):

    A) quota di totali, somma / somma          18,5066%   <- QUESTA usa la griglia
    B) media delle quote settimanali           18,5363%   (+254 candidature)
    C) media delle quote per cella sett. x reg. 19,5517%   (+8.941 candidature)

La quota attribuita da Robyn va calcolata con la definizione A, altrimenti il
rapporto della regola di lettura (la banda 1,8-2,6) si misurerebbe contro un
denominatore diverso da quello di Meridian e il confronto non direbbe piu'
niente. In pratica, dal modello selezionato:

    quota_robyn = somma di xDecompAgg dei SETTE canali paid, sulla finestra di
                  modellazione, diviso la somma di `candidature` osservate
                  sulla stessa finestra

e si riporta ACCANTO, per trasparenza, anche la somma degli `effect_share` dei
sette canali, che Robyn calcola sul dipendente FITTATO e non su quello
osservato: le due cifre non coincidono esattamente e la differenza va scritta,
non scelta. Il controllo (e) qui sotto verifica il denominatore.
"""
from __future__ import annotations

import os
import sys

import pandas as pd

QUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(QUI)
DIR_DATI = os.path.join(ROOT, "dati_simulati", "modello")
FUORI = os.path.join(QUI, "mondo42_nazionale.csv")

# file media -> nome della colonna nel CSV nazionale (minuscole, senza spazi:
# Robyn li usa come nomi di variabile in R)
CANALI = [
    ("google_ads_settimanale.csv", "google_ads"),
    ("meta_ads_settimanale.csv", "meta_ads"),
    ("linkedin_ads_settimanale.csv", "linkedin_ads"),
    ("indeed_settimanale.csv", "indeed"),
    ("subito_lavoro_settimanale.csv", "subito_lavoro"),
    ("jooble_settimanale.csv", "jooble"),
    ("altre_job_board_settimanale.csv", "altre_job_board"),
]


def virgola(x, dec=2):
    return format(x, "." + str(dec) + "f").replace(".", ",")


def main() -> int:
    if not os.path.isdir(DIR_DATI):
        print("cartella dei dati non trovata: " + DIR_DATI)
        return 1

    kpi = pd.read_csv(os.path.join(DIR_DATI, "candidature_settimanali.csv"))
    kpi["settimana"] = pd.to_datetime(kpi["settimana"])
    settimane = pd.Index(sorted(kpi["settimana"].unique()), name="DATE")

    df = pd.DataFrame({"DATE": settimane})
    df["candidature"] = (kpi.groupby("settimana")["candidature"].sum()
                         .reindex(settimane).to_numpy())

    controllo_a = []
    for nome_file, colonna in CANALI:
        m = pd.read_csv(os.path.join(DIR_DATI, nome_file))
        m["settimana"] = pd.to_datetime(m["settimana"])
        # le settimane a spesa zero NON hanno righe nei file media (regola del
        # generatore): il reindex le riporta, e fillna(0) le tiene a ZERO, non
        # a NaN. E' il controllo (d).
        serie = (m.groupby("settimana")["spesa"].sum()
                 .reindex(settimane).fillna(0.0))
        df[colonna] = serie.to_numpy()
        controllo_a.append((colonna, float(m["spesa"].sum()), float(serie.sum()),
                            int((serie == 0.0).sum())))

    stag = pd.read_csv(os.path.join(DIR_DATI, "stagionalita.csv"))
    stag["settimana"] = pd.to_datetime(stag["settimana"])
    df["stagionalita"] = (stag.set_index("settimana")["indice_stagionale"]
                          .reindex(settimane).to_numpy())

    # I due controlli di domanda del mondo, sommati sulle regioni. Meridian ne
    # riceve tre (questi due piu' l'indice stagionale): darne meno a Robyn
    # sarebbe un handicap, e il confronto non sarebbe piu' sulla stessa
    # informazione. Scelta dichiarata nella pre-registrazione, prima del run.
    for file_ctrl, colonna in (("richieste_clienti.csv", "domanda_clienti"),
                               ("ricerche_candidati.csv", "ricerche_candidati")):
        c = pd.read_csv(os.path.join(DIR_DATI, file_ctrl))
        c["settimana"] = pd.to_datetime(c["settimana"])
        nome_col = [x for x in c.columns if x not in ("settimana", "regione")][0]
        df[colonna] = (c.groupby("settimana")[nome_col].sum()
                       .reindex(settimane).to_numpy())

    df["DATE"] = df["DATE"].dt.strftime("%Y-%m-%d")

    # ---- i quattro controlli obbligatori -------------------------------
    print("=" * 74)
    print("CONTROLLI OBBLIGATORI - PASSO 1")
    print("=" * 74)
    ok = True

    print()
    print("(a) spesa per canale: nazionale contro regionale (tolleranza 0,01 EUR)")
    for colonna, dai_file, aggregata, zeri in controllo_a:
        scarto = abs(dai_file - aggregata)
        stato = "ok" if scarto <= 0.01 else "FALLITO"
        ok = ok and scarto <= 0.01
        print("    %-16s regionale %14s  nazionale %14s  scarto %s  %s  (settimane a zero: %d)"
              % (colonna, virgola(dai_file), virgola(aggregata), virgola(scarto, 4), stato, zeri))

    print()
    print("(b) candidature: nazionale contro KPI totale del mondo")
    tot_kpi = float(kpi["candidature"].sum())
    tot_naz = float(df["candidature"].sum())
    stato = "ok" if abs(tot_kpi - tot_naz) < 0.5 else "FALLITO"
    ok = ok and abs(tot_kpi - tot_naz) < 0.5
    print("    panel %s   nazionale %s   %s"
          % (virgola(tot_kpi, 0), virgola(tot_naz, 0), stato))

    print()
    print("(c) 104 righe, nessuna settimana mancante, nessun NaN")
    d = pd.to_datetime(df["DATE"])
    passi = d.diff().dropna().dt.days.unique().tolist()
    nan = {c: int(df[c].isna().sum()) for c in df.columns if int(df[c].isna().sum())}
    cond = (len(df) == 104 and passi == [7] and not nan)
    ok = ok and cond
    print("    righe %d | passi fra settimane consecutive %s | colonne con NaN %s | %s"
          % (len(df), passi, nan or "nessuna", "ok" if cond else "FALLITO"))
    print("    periodo %s -> %s" % (df["DATE"].iloc[0], df["DATE"].iloc[-1]))

    print()
    print("(d) le settimane a spesa zero restano zero e non diventano NaN")
    zeri_tot = int((df[[c for _f, c in CANALI]] == 0.0).sum().sum())
    nan_media = int(df[[c for _f, c in CANALI]].isna().sum().sum())
    cond = (nan_media == 0)
    ok = ok and cond
    print("    celle a zero nei sette canali: %d | celle NaN: %d | %s"
          % (zeri_tot, nan_media, "ok" if cond else "FALLITO"))
    for colonna, _dai, _agg, zeri in controllo_a:
        if zeri:
            print("        %-16s %d settimane a zero" % (colonna, zeri))

    # ---- (e) il denominatore della quota, che Robyn dovra' usare uguale ----
    print()
    print("(e) definizione della quota attribuita ai media (vedi la testa del file)")
    percorso_ver = os.path.join(ROOT, "dati_simulati", "verita", "contributo_vero.csv")
    if not os.path.exists(percorso_ver):
        print("    verita' non trovata: " + percorso_ver + "  FALLITO")
        ok = False
    else:
        ver = pd.read_csv(percorso_ver)
        ver["settimana"] = pd.to_datetime(ver["settimana"])
        tot_con = float(ver["candidature_incrementali_vere"].sum())
        qa = 100.0 * tot_con / tot_naz
        c_s = ver.groupby("settimana")["candidature_incrementali_vere"].sum()
        k_s = kpi.groupby("settimana")["candidature"].sum()
        qb = float((c_s / k_s.reindex(c_s.index)).mean()) * 100.0
        print("    A) quota di TOTALI (quella della griglia): %s%%" % virgola(qa, 4))
        print("    B) media delle quote settimanali         : %s%%  (scarto %s candidature)"
              % (virgola(qb, 4), virgola((qb - qa) / 100.0 * tot_naz, 0)))
        # la riga della griglia arrotonda a 2 decimali: deve tornare 18,51
        atteso = 18.51
        cond = abs(round(qa, 2) - atteso) < 1e-9
        ok = ok and cond
        print("    la griglia registra %s%% per il mondo 42 -> ricalcolata %s%%   %s"
              % (virgola(atteso), virgola(round(qa, 2)), "ok" if cond else "FALLITO"))
        print("    DENOMINATORE DA USARE PER ROBYN: %s candidature osservate sulle 104 settimane"
              % virgola(tot_naz, 0))
        print("    (quota_robyn = somma xDecompAgg dei 7 canali paid / questo denominatore;")
        print("     riportare accanto anche la somma degli effect_share, che usa il fittato)")

    print()
    if not ok:
        print("UN CONTROLLO E' FALLITO: il file NON viene scritto.")
        return 1

    df.to_csv(FUORI, index=False)
    print("=" * 74)
    print("scritto " + FUORI)
    print("   %d righe x %d colonne: %s" % (len(df), len(df.columns), ", ".join(df.columns)))
    print("   spesa totale nazionale: %s EUR" %
          virgola(float(df[[c for _f, c in CANALI]].sum().sum())))
    print("   candidature totali:     %s" % virgola(tot_naz, 0))
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
