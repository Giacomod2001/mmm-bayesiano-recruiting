"""
Test del registro dei run e dei costruttori di tabella.

Girano tutti offline: il backend BigQuery non viene mai istanziato, quello
locale scrive in una tmpdir. Non serve rete ne' credenziali — il registro
deve poter essere verificato anche da chi non ha accesso al progetto GCP.
"""
from __future__ import annotations

import os

import pandas as pd
import pytest

import mmm_registry as R
import mmm_tables as T


# --------------------------------------------------------------- utilita'

def test_hash_indipendente_dall_ordine(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    a.write_text("x\n1\n"); b.write_text("y\n2\n")
    assert R.hash_inputs([str(a), str(b)]) == R.hash_inputs([str(b), str(a)])


def test_hash_cambia_col_contenuto(tmp_path):
    a = tmp_path / "a.csv"
    a.write_text("x\n1\n"); h1 = R.hash_inputs([str(a)])
    a.write_text("x\n2\n"); h2 = R.hash_inputs([str(a)])
    assert h1 != h2


def test_hash_file_mancante_non_esplode(tmp_path):
    h = R.hash_inputs([str(tmp_path / "non-esiste.csv")])
    assert len(h) == 64


def test_versioni_librerie_marca_gli_assenti():
    v = R.library_versions(["pandas", "pacchetto-che-non-esiste-xyz"])
    assert v["pandas"] != "assente"
    assert v["pacchetto-che-non-esiste-xyz"] == "assente"


# --------------------------------------------------------------- backend

def test_backend_off_non_scrive():
    b = R.make_backend("off")
    assert b.kind == "off"
    assert b.write("runs", pd.DataFrame([{"a": 1}])) == 0


def test_backend_locale_appende_una_sola_intestazione(tmp_path):
    b = R._LocalBackend(str(tmp_path))
    df = pd.DataFrame([{"run_id": "r1", "v": 1}])
    b.write("runs", df)
    b.write("runs", pd.DataFrame([{"run_id": "r2", "v": 2}]))
    righe = open(b.path("runs")).read().strip().split("\n")
    assert len(righe) == 3                      # header + 2 record
    assert b.existing_run_ids() == {"r1", "r2"}


def test_auto_ricade_su_locale_senza_progetto(tmp_path, monkeypatch):
    monkeypatch.delenv("MMM_BQ_PROJECT", raising=False)
    monkeypatch.delenv("MMM_REGISTRY", raising=False)
    assert R.make_backend(local_root=str(tmp_path)).kind == "local"


def test_bigquery_esplicito_senza_progetto_e_errore(monkeypatch):
    monkeypatch.delenv("MMM_BQ_PROJECT", raising=False)
    with pytest.raises(RuntimeError, match="MMM_BQ_PROJECT"):
        R.make_backend("bigquery")


# --------------------------------------------------------------- registro

def _reg(tmp_path, **kw):
    return R.RunRegistry.start(mode="local", local_root=str(tmp_path), **kw)


def test_write_inietta_run_id_e_data(tmp_path):
    reg = _reg(tmp_path, seed=42)
    reg.write("channel_roi", pd.DataFrame([{"channel": "meta", "roi_q50": 1.2}]))
    out = pd.read_csv(os.path.join(tmp_path, "channel_roi.csv"))
    assert out.loc[0, "run_id"] == reg.run_id
    assert list(out.columns)[:2] == ["run_id", "run_date"]


def test_dataframe_vuoto_non_scrive_nulla(tmp_path):
    reg = _reg(tmp_path)
    assert reg.write("allocation", pd.DataFrame()) == 0
    assert not os.path.exists(os.path.join(tmp_path, "allocation.csv"))


def test_tabella_sconosciuta_rifiutata(tmp_path):
    reg = _reg(tmp_path)
    with pytest.raises(ValueError, match="sconosciuta"):
        reg.write("tabella_inventata", pd.DataFrame([{"a": 1}]))


def test_finish_registra_conteggi_ed_esito(tmp_path):
    reg = _reg(tmp_path, seed=7, config={"budget": 450000})
    reg.write("channel_roi", pd.DataFrame([{"channel": "meta", "roi_q50": 1.1},
                                           {"channel": "google", "roi_q50": 1.4}]))
    reg.diagnostics({"r_hat_max": 1.01, "sampler": "NUTS"})
    row = reg.finish(excel_path="/qualche/dove/risultati.xlsx").iloc[0]
    assert row["status"] == "ok"
    assert row["seed"] == 7
    assert row["excel_file"] == "risultati.xlsx"          # solo il nome, non il path
    assert '"channel_roi": 2' in row["rows_json"]
    assert "450000" in row["config_json"]


def test_diagnostica_separa_numeri_e_testo(tmp_path):
    reg = _reg(tmp_path)
    reg.diagnostics({"r_hat_max": 1.02, "note": "catene convergono"})
    d = pd.read_csv(os.path.join(tmp_path, "diagnostics.csv")).set_index("metric")
    assert d.loc["r_hat_max", "value_num"] == pytest.approx(1.02)
    assert pd.isna(d.loc["r_hat_max", "value_txt"])
    assert d.loc["note", "value_txt"] == "catene convergono"


def test_context_manager_marca_errore_e_propaga(tmp_path):
    with pytest.raises(ZeroDivisionError):
        with _reg(tmp_path) as reg:
            reg.write("channel_roi", pd.DataFrame([{"channel": "meta"}]))
            1 / 0
    runs = pd.read_csv(os.path.join(tmp_path, "runs.csv"))
    assert runs.loc[0, "status"] == "error"
    assert "ZeroDivisionError" in runs.loc[0, "note"]


def test_run_id_unici():
    ids = {R._new_run_id(__import__("datetime").datetime.now()) for _ in range(50)}
    assert len(ids) == 50


# --------------------------------------------------------------- tabelle

SUMMARY = {"channels": {
    "meta": {"roi": {"q05": 0.6, "q50": 0.9, "q95": 1.3}},
    "linkedin": {"roi": {"q05": 0.9, "q50": 1.6, "q95": 2.4}},
    "indeed": {"roi": {"q05": 0.8, "q50": 1.1, "q95": 1.5}},
}}
ROAS = {"meta": 1.8, "linkedin": 1.0}     # indeed: benchmark assente


def test_channel_roi_k_e_divario():
    df = T.channel_roi(SUMMARY, ROAS).set_index("channel")
    assert df.loc["meta", "k_factor"] == pytest.approx(0.5)      # sovra-attribuisce
    assert df.loc["meta", "gap_pct"] == pytest.approx(-50.0)
    assert df.loc["linkedin", "k_factor"] == pytest.approx(1.6)  # sotto-attribuisce
    assert pd.isna(df.loc["indeed", "k_factor"])                 # nessun benchmark


def test_channel_roi_conserva_i_quantili():
    df = T.channel_roi(SUMMARY).set_index("channel")
    assert {"roi_q05", "roi_q50", "roi_q95"} <= set(df.columns)
    assert df.loc["linkedin", "roi_q05"] == pytest.approx(0.9)


ALLOC = pd.DataFrame([
    {"channel": "meta", "hist_weekly_spend": 1000.0, "budget_quarter": 10000.0},
    {"channel": "linkedin", "hist_weekly_spend": 500.0, "budget_quarter": 50000.0},
])


def test_allocation_rileva_il_vincolo_attivo():
    df = T.allocation(ALLOC, min_spend={"linkedin": 50000.0},
                      max_spend={"meta": 99999.0}).set_index("channel")
    assert df.loc["linkedin", "constraint_active"] == "min"
    assert df.loc["meta", "constraint_active"] == ""      # libero


def test_allocation_calcola_la_variazione():
    df = T.allocation(ALLOC, weeks=13).set_index("channel")
    assert df.loc["meta", "spend_current"] == pytest.approx(13000.0)
    assert df.loc["meta", "delta_pct"] == pytest.approx((10000 / 13000 - 1) * 100)


def test_allocation_senza_spesa_storica_non_divide_per_zero():
    a = pd.DataFrame([{"channel": "nuovo", "hist_weekly_spend": 0.0,
                       "budget_quarter": 5000.0}])
    assert pd.isna(T.allocation(a).loc[0, "delta_pct"])


CAMP = pd.DataFrame([
    {"channel": "meta", "campaign": "dpa", "spend": 100.0,
     "budget_proposed": 120.0, "share_hist": 0.4, "share_proposed": 0.5,
     "roas": 2.0},
])


def test_campaign_split_riscala_col_fattore_k():
    df = T.campaign_split(CAMP, k_factor={"meta": 0.5})
    assert df.loc[0, "adjusted_roas"] == pytest.approx(1.0)
    assert "budget_proposed" in df.columns


def test_campaign_split_senza_roas_non_inventa_colonne():
    df = T.campaign_split(CAMP.drop(columns=["roas"]))
    assert "adjusted_roas" not in df.columns


def test_weekly_plan_normalizza_il_nome_canale():
    plan = pd.DataFrame([{"week": "2026-01-05", "canale": "meta", "spend": 10.0}])
    df = T.weekly_plan(plan)
    assert list(df.columns) == ["week", "channel", "spend"]
    assert str(df.loc[0, "week"]) == "2026-01-05"


def test_response_curves_griglia_fino_al_doppio():
    df = T.response_curves(lambda ch, x: x * 2, ["meta"], {"meta": 1000.0},
                           n_points=5)
    assert len(df) == 5
    assert df["weekly_spend"].max() == pytest.approx(2000.0)
    assert df["expected_response"].max() == pytest.approx(4000.0)


def test_response_curves_salta_i_canali_senza_spesa():
    df = T.response_curves(lambda ch, x: x, ["meta", "vuoto"],
                           {"meta": 100.0, "vuoto": 0.0})
    assert set(df["channel"]) == {"meta"}


# --------------------------------------- stage 2 con le colonne reali

CAMP_REALE = pd.DataFrame([
    {"channel": "meta", "campaign": "dpa", "spend": 100.0,
     "platform_roas": 2.0, "k_channel": 0.5, "roas_adjusted": 1.0,
     "share_hist": 0.4, "share_proposed": 0.5, "budget_proposed": 120.0},
    {"channel": "meta", "campaign": "lead", "spend": 150.0,
     "platform_roas": 1.2, "k_channel": 0.5, "roas_adjusted": 0.6,
     "share_hist": 0.6, "share_proposed": 0.5, "budget_proposed": 120.0},
])


def test_campaign_split_usa_le_colonne_dell_allocator():
    df = T.campaign_split(CAMP_REALE).set_index("campaign")
    assert df.loc["dpa", "adjusted_roas"] == pytest.approx(1.0)
    assert df.loc["dpa", "k_factor"] == pytest.approx(0.5)
    assert df.loc["lead", "budget_proposed"] == pytest.approx(120.0)


def test_channel_platform_roas_pesa_sulla_spesa():
    # (2.0*100 + 1.2*150) / 250 = 1.52
    assert T.channel_platform_roas(CAMP_REALE)["meta"] == pytest.approx(1.52)


def test_channel_platform_roas_tabella_vuota():
    assert T.channel_platform_roas(pd.DataFrame()) == {}


# --------------------------------------- giro completo, come in _persist

def test_giro_completo_scrive_tutte_le_tabelle(tmp_path):
    """Riproduce la sequenza di `_persist` con dati finti ma di forma reale.

    Verifica il contratto fra allocator e registro: tutte le tabelle
    popolate, tutte marcate con lo stesso run_id, e il record in `runs`
    che ne tiene il conto.
    """
    reg = R.RunRegistry.start(mode="local", local_root=str(tmp_path),
                              seed=42, config={"budget_quarter": 450000},
                              label="Q1 2026")
    bench = T.channel_platform_roas(CAMP_REALE)
    reg.write("channel_roi", T.channel_roi(SUMMARY, bench))
    reg.write("allocation", T.allocation(ALLOC, min_spend={"linkedin": 50000.0}))
    reg.write("campaign_split", T.campaign_split(CAMP_REALE))
    reg.write("weekly_plan", pd.DataFrame(
        [{"week": "2026-01-05", "channel": "meta", "spend": 800.0},
         {"week": "2026-01-12", "channel": "meta", "spend": 850.0}]))
    reg.write("response_curves",
              T.response_curves(lambda ch, x: x * 1.5, ["meta"],
                                {"meta": 1000.0}, n_points=10))
    reg.diagnostics({"r_hat_max": 1.01})
    row = reg.finish(excel_path="risultati.xlsx").iloc[0]

    scritte = {t for t in R.TABLES
               if os.path.exists(os.path.join(tmp_path, f"{t}.csv"))}
    assert scritte == set(R.TABLES)                  # nessuna tabella dimenticata

    for t in R.TABLES:
        df = pd.read_csv(os.path.join(tmp_path, f"{t}.csv"))
        assert set(df["run_id"]) == {reg.run_id}, t
    assert row["label"] == "Q1 2026"
    assert row["status"] == "ok"


def test_due_run_convivono_e_si_confrontano(tmp_path):
    """Il punto dell'esercizio: due esecuzioni nella stessa tabella,
    distinguibili per run_id e confrontabili con un raggruppamento."""
    for i in range(2):
        reg = R.RunRegistry.start(mode="local", local_root=str(tmp_path))
        reg.write("channel_roi", T.channel_roi(SUMMARY, {"meta": 1.8 + i}))
        reg.finish()
    df = pd.read_csv(os.path.join(tmp_path, "channel_roi.csv"))
    assert df["run_id"].nunique() == 2
    meta = df[df["channel"] == "meta"].sort_values("run_id")
    # stesso ROI stimato, benchmark diverso -> divario diverso: e' la serie
    # che la Sez. 5.6 segue nel tempo
    assert meta["gap_pct"].nunique() == 2
