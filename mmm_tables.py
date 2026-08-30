"""
Costruttori delle tabelle del registro (vedi `mmm_registry.py`).

Sono funzioni pure: ricevono DataFrame e dizionari, restituiscono DataFrame
gia' normalizzati, con nomi colonna in inglese coerenti con lo schema
canonico della pipeline (`pipeline/schema.py`) e non con le intestazioni
italiane dell'Excel, che sono di presentazione e possono cambiare senza che
cambi il dato.

Tre regole che valgono per tutte:

1. **Si salva la distribuzione, non la media.** Dove il modello produce un
   posterior, la tabella porta q05/q50/q95. Ridurre a un numero solo
   butterebbe via proprio cio' che giustifica l'approccio bayesiano.
2. **Formato lungo.** Una riga per (entita', periodo), mai colonne che si
   moltiplicano al crescere dei canali: cosi' aggiungere un canale non
   richiede una migrazione di schema.
3. **Tipi stabili.** Le tabelle si creano da sole al primo caricamento con
   lo schema inferito: una colonna che cambia tipo tra un run e l'altro
   romperebbe i caricamenti successivi.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

_TOL = 1e-6


def _f(x: Any, default: float = float("nan")) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v


# --------------------------------------------------------------- ROI canale

def channel_roi(summary: Mapping[str, Any],
                platform_roas: Mapping[str, float] | None = None) -> pd.DataFrame:
    """ROI incrementale per canale, con il confronto verso il benchmark.

    `summary` e' il riepilogo posterior prodotto dal modello
    (`output/model_fit.json`), `platform_roas` i ROAS dichiarati dalle
    piattaforme. Il rapporto fra i due e' il fattore k dello stage 2
    (Sez. 3.8); il divario percentuale e' la quantita' che la Sez. 5.6
    segue nel tempo, ed e' il motivo principale per cui questo registro
    esiste: da un solo run non si vede, da quattro si'.
    """
    roas = dict(platform_roas or {})
    rows = []
    for ch, entry in (summary.get("channels") or {}).items():
        roi = entry.get("roi", {}) if isinstance(entry, Mapping) else {}
        q50 = _f(roi.get("q50"))
        bench = _f(roas.get(ch), float("nan"))
        rows.append({
            "channel": str(ch),
            "roi_q05": _f(roi.get("q05")),
            "roi_q50": q50,
            "roi_q95": _f(roi.get("q95")),
            "platform_roas": bench,
            # k < 1: la piattaforma sovra-attribuisce; k > 1: sotto-attribuisce
            "k_factor": q50 / bench if bench and bench == bench and bench > 0
                        else float("nan"),
            "gap_pct": (q50 / bench - 1.0) * 100 if bench and bench == bench
                       and bench > 0 else float("nan"),
        })
    return pd.DataFrame(rows).sort_values("channel").reset_index(drop=True)


# --------------------------------------------------------------- stage 1

def allocation(alloc: pd.DataFrame,
               readable: pd.DataFrame | None = None,
               min_spend: Mapping[str, float] | None = None,
               max_spend: Mapping[str, float] | None = None,
               weeks: int = 13) -> pd.DataFrame:
    """Esito dello stage 1: budget per canale, vincoli, effetto atteso.

    `alloc` e' l'output dell'ottimizzatore (colonne `channel`,
    `hist_weekly_spend`, `budget_quarter`); `readable` la tabella in chiaro
    con le candidature attese, se disponibile.

    La colonna `constraint_active` e' la piu' interessante da conservare:
    dice se il canale si e' fermato su un paletto manageriale invece che
    sul punto di pareggio dei rendimenti marginali. E' l'informazione che
    la Sez. 6.4 usa per stimare il costo dei vincoli, e a run concluso non
    e' piu' ricostruibile dai soli numeri di budget.
    """
    mn, mx = dict(min_spend or {}), dict(max_spend or {})
    conv_now, conv_exp = {}, {}
    if readable is not None and "canale" in readable.columns:
        r = readable[readable["canale"] != "TOTALE"]
        conv_now = dict(zip(r["canale"], r.get("candidature ora", [])))
        conv_exp = dict(zip(r["canale"], r.get("candidature attese", [])))

    rows = []
    for _, a in alloc.iterrows():
        ch = str(a["channel"])
        cur = _f(a.get("hist_weekly_spend"), 0.0) * weeks
        rec = _f(a.get("budget_quarter"), 0.0)
        lo, hi = mn.get(ch), mx.get(ch)
        active = ""
        if lo is not None and abs(rec - lo) <= max(_TOL, abs(lo) * 1e-6):
            active = "min"
        elif hi is not None and abs(rec - hi) <= max(_TOL, abs(hi) * 1e-6):
            active = "max"
        rows.append({
            "channel": ch,
            "spend_current": cur,
            "spend_recommended": rec,
            "delta_pct": (rec / cur - 1.0) * 100 if cur > 0 else float("nan"),
            "min_constraint": _f(lo) if lo is not None else float("nan"),
            "max_constraint": _f(hi) if hi is not None else float("nan"),
            "constraint_active": active,
            "conversions_now": _f(conv_now.get(ch)),
            "conversions_expected": _f(conv_exp.get(ch)),
            "weeks": int(weeks),
        })
    return pd.DataFrame(rows).sort_values("channel").reset_index(drop=True)


# --------------------------------------------------------------- stage 2

def campaign_split(camp: pd.DataFrame,
                   k_factor: Mapping[str, float] | None = None) -> pd.DataFrame:
    """Riparto descrittivo dentro il canale (stage 2, Sez. 3.8).

    Accetta direttamente l'output di `allocate_campaigns`, che porta gia'
    `platform_roas`, `roas_adjusted` e `k_channel`; se quelle colonne non ci
    sono, il ROAS aggiustato viene ricalcolato dal fattore k passato a parte.

    Il vocabolario delle colonne resta deliberatamente contabile —
    `budget_proposed`, `share_*` — e non causale: queste righe non sono
    effetti incrementali stimati, sono una ripartizione di un budget gia'
    deciso a monte. Chi interroghera' la tabella fra sei mesi deve poterlo
    capire dai nomi, senza risalire alla tesi.
    """
    k = dict(k_factor or {})
    out = pd.DataFrame({
        "channel": camp["channel"].astype(str).values,
        "campaign": camp["campaign"].astype(str).values,
        "spend_current": pd.to_numeric(camp.get("spend"), errors="coerce").values,
        "budget_proposed": pd.to_numeric(camp.get("budget_proposed"),
                                         errors="coerce").values,
        "share_current": pd.to_numeric(camp.get("share_hist"), errors="coerce").values,
        "share_proposed": pd.to_numeric(camp.get("share_proposed"),
                                        errors="coerce").values,
    })
    roas_col = ("platform_roas" if "platform_roas" in camp.columns
                else "roas" if "roas" in camp.columns else None)
    if roas_col:
        out["platform_roas"] = pd.to_numeric(camp[roas_col], errors="coerce").values
    if "k_channel" in camp.columns:
        out["k_factor"] = pd.to_numeric(camp["k_channel"], errors="coerce").values
    elif k:
        out["k_factor"] = out["channel"].map(lambda c: k.get(c, float("nan")))
    if "roas_adjusted" in camp.columns:
        out["adjusted_roas"] = pd.to_numeric(camp["roas_adjusted"],
                                             errors="coerce").values
    elif roas_col and "k_factor" in out.columns:
        out["adjusted_roas"] = out["platform_roas"] * out["k_factor"]
    return out.sort_values(["channel", "campaign"]).reset_index(drop=True)


def channel_platform_roas(roas_table: pd.DataFrame) -> dict[str, float]:
    """ROAS di piattaforma aggregato per canale, pesato sulla spesa.

    Stessa formula usata dallo stage 2 per calcolare k (`campaigns.py`):
    va tenuta identica, altrimenti il `k_factor` registrato in
    `channel_roi` e quello applicato alle campagne divergerebbero, e il
    confronto multi-trimestre della Sez. 5.6 misurerebbe un artefatto.
    """
    if roas_table is None or len(roas_table) == 0:
        return {}
    col = ("platform_roas" if "platform_roas" in roas_table.columns
           else "roas" if "roas" in roas_table.columns else None)
    if col is None or "spend" not in roas_table.columns:
        return {}
    out: dict[str, float] = {}
    for ch, t in roas_table.groupby("channel"):
        spend = float(pd.to_numeric(t["spend"], errors="coerce").sum())
        num = float((pd.to_numeric(t[col], errors="coerce")
                     * pd.to_numeric(t["spend"], errors="coerce")).sum())
        out[str(ch)] = num / max(spend, 1e-9)
    return out


# --------------------------------------------------------------- calendario

def weekly_plan(plan: pd.DataFrame) -> pd.DataFrame:
    """Spaccato settimanale della spesa consigliata, in formato lungo."""
    if plan is None or len(plan) == 0:
        return pd.DataFrame(columns=["week", "channel", "spend"])
    df = plan.copy()
    if "channel" not in df.columns and "canale" in df.columns:
        df = df.rename(columns={"canale": "channel"})
    keep = [c for c in ("week", "channel", "spend") if c in df.columns]
    df = df[keep].copy()
    if "week" in df:
        df["week"] = pd.to_datetime(df["week"]).dt.date
    if "spend" in df:
        df["spend"] = pd.to_numeric(df["spend"], errors="coerce")
    return df.reset_index(drop=True)


# --------------------------------------------------------------- curve

def response_curves(curve_fn, channels: Sequence[str],
                    max_weekly_spend: Mapping[str, float],
                    n_points: int = 25) -> pd.DataFrame:
    """Curve di risposta campionate su una griglia di spesa settimanale.

    `curve_fn(channel, spend)` restituisce la risposta attesa a regime.
    Si campiona fino al doppio della spesa storica del canale: e' l'intervallo
    in cui una raccomandazione e' credibile, e oltre il quale la curva
    estrapolerebbe fuori dal supporto dei dati.

    Salvare i punti anziche' i soli parametri (lambda, EC, slope) e' una
    scelta di leggibilita': la curva resta interrogabile e disegnabile con
    una query, senza dover reimplementare altrove la trasformazione.
    """
    rows = []
    for ch in channels:
        top = _f(max_weekly_spend.get(ch), 0.0)
        if not (top > 0):
            continue
        for x in np.linspace(0.0, top * 2.0, n_points):
            try:
                y = _f(curve_fn(ch, float(x)))
            except Exception:                              # pragma: no cover
                y = float("nan")
            rows.append({"channel": str(ch),
                         "weekly_spend": float(x),
                         "expected_response": y})
    return pd.DataFrame(rows, columns=["channel", "weekly_spend",
                                       "expected_response"])
