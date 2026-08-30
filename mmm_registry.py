"""
Registro dei run: persistenza tabellare dei risultati della pipeline MMM.

Perche' esiste
--------------
Fino a qui ogni esecuzione produceva un workbook Excel e alcuni PNG: artefatti
che circolano bene ma non si interrogano. Confrontare due trimestri significava
aprire due file e guardarli. Questo modulo aggiunge una seconda destinazione —
tabelle — senza togliere la prima: l'Excel continua a uscire identico, e in piu'
ogni run deposita le proprie righe in un registro con un `run_id`.

Da li' discendono tre cose che i file non davano:
  * confronto tra esecuzioni (Sez. 5.6: stabilita' nel tempo del divario
    fra ROI incrementale del modello e ROAS dichiarati dalle piattaforme);
  * un registro di riproducibilita' esterno al singolo artefatto (seed,
    versioni delle librerie, impronta dei dati di input, configurazione);
  * la possibilita' di rigenerare una vista senza rilanciare il fit.

Due backend, stessa interfaccia
-------------------------------
    bigquery   scrive su un dataset BigQuery dedicato (default `mmm_output`)
    local      scrive CSV in append sotto output/registry/

Il backend si sceglie da solo: se le variabili d'ambiente per BigQuery ci sono
e il client si connette, usa quello; altrimenti ricade sul locale e lo dice.
La pipeline non cambia comportamento a seconda di dove gira — la stessa
proprieta' di indipendenza dall'ambiente gia' adottata per il notebook.

Configurazione (variabili d'ambiente, tutte opzionali)
------------------------------------------------------
    MMM_BQ_PROJECT    progetto GCP (es. mmm-archivio)
    MMM_BQ_DATASET    dataset di scrittura            [mmm_output]
    MMM_BQ_LOCATION   location del dataset            [EU]
    MMM_REGISTRY      forza il backend: bigquery|local|off  [auto]

Uso tipico
----------
    reg = RunRegistry.start(seed=42, config={...}, inputs=[...paths...])
    reg.write("channel_roi", df_roi)
    reg.write("allocation", df_alloc)
    reg.finish(excel_path="output/risultati.xlsx")

Nessuna riga di questo modulo tocca i dati personali: le tabelle contengono
aggregati per canale, campagna, regione e settimana, coerenti con la
minimizzazione applicata a monte nell'ingestion.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import uuid
from typing import Any, Iterable, Sequence

import pandas as pd

# --------------------------------------------------------------- costanti

DATASET_DEFAULT = "mmm_output"
LOCATION_DEFAULT = "EU"

#: tabelle del registro. `runs` e' l'indice, le altre sono i risultati.
TABLES: tuple[str, ...] = (
    "runs",             # un record per esecuzione: ambiente, config, esito
    "channel_roi",      # ROI incrementale per canale, con i quantili
    "allocation",       # stage 1: budget di canale, vincoli, effetto atteso
    "campaign_split",   # stage 2: riparto descrittivo dentro il canale
    "weekly_plan",      # spaccato settimanale della spesa consigliata
    "response_curves",  # curve di risposta campionate
    "diagnostics",      # diagnostica del fit, formato lungo
)

#: colonna di clustering per tabella (le altre restano solo partizionate)
_CLUSTER_BY: dict[str, list[str]] = {
    "channel_roi": ["channel"],
    "allocation": ["channel"],
    "campaign_split": ["channel"],
    "weekly_plan": ["channel"],
    "response_curves": ["channel"],
}

#: librerie di cui registrare la versione nel record di run
_TRACKED_PACKAGES = (
    "google-meridian", "tensorflow", "tensorflow-probability", "arviz",
    "pandas", "numpy", "scipy", "openpyxl", "google-cloud-bigquery",
)


# --------------------------------------------------------------- utilita'

def library_versions(packages: Iterable[str] = _TRACKED_PACKAGES) -> dict[str, str]:
    """Versioni installate delle librerie che influenzano il risultato.

    Una libreria assente non e' un errore: viene marcata "assente". Serve a
    distinguere «non c'era» da «non l'ho guardata», che in un registro di
    riproducibilita' sono cose diverse.
    """
    try:
        from importlib import metadata
    except ImportError:                                   # pragma: no cover
        return {}
    out: dict[str, str] = {}
    for pkg in packages:
        try:
            out[pkg] = metadata.version(pkg)
        except Exception:
            out[pkg] = "assente"
    return out


def hash_inputs(paths: Sequence[str], chunk: int = 1 << 20) -> str:
    """Impronta SHA-256 dei file di input, stabile rispetto all'ordine.

    Serve a rispondere alla domanda «questo run e quello di tre mesi fa
    hanno visto gli stessi dati?» senza conservare i dati stessi. I file
    mancanti vengono inclusi nell'impronta come tali, cosi' che una lista
    di input incompleta non produca l'hash di una lista diversa.
    """
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(os.path.basename(p).encode("utf-8"))
        if not os.path.exists(p):
            h.update(b"<mancante>")
            continue
        with open(p, "rb") as f:
            while True:
                block = f.read(chunk)
                if not block:
                    break
                h.update(block)
    return h.hexdigest()


def _json(value: Any) -> str:
    """Serializza config e metadati in JSON compatto e deterministico."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _new_run_id(now: dt.datetime) -> str:
    """`20260819T143000Z-3f9a1c` — ordinabile a occhio, unico in pratica."""
    return f"{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"


# --------------------------------------------------------------- backend

class _LocalBackend:
    """CSV in append sotto `root`. Nessuna dipendenza, file ispezionabili.

    E' il backend di riserva, ma non e' un ripiego: se BigQuery non e'
    disponibile — per policy, per permessi o perche' si sta lavorando in
    locale — il registro continua a esistere e la storia dei run non si
    interrompe.
    """

    kind = "local"

    def __init__(self, root: str):
        self.root = root
        os.makedirs(root, exist_ok=True)

    def path(self, table: str) -> str:
        return os.path.join(self.root, f"{table}.csv")

    def write(self, table: str, df: pd.DataFrame) -> int:
        p = self.path(table)
        df.to_csv(p, mode="a", header=not os.path.exists(p), index=False)
        return len(df)

    def existing_run_ids(self, table: str = "runs") -> set[str]:
        p = self.path(table)
        if not os.path.exists(p):
            return set()
        try:
            return set(pd.read_csv(p, usecols=["run_id"])["run_id"].astype(str))
        except Exception:                                 # pragma: no cover
            return set()

    def describe(self) -> str:
        return f"locale ({self.root})"


class _BigQueryBackend:
    """Load job per tabella, partizionata per `run_date`.

    Le tabelle si creano da sole al primo write (schema inferito dal
    DataFrame): non serve DDL a mano, ma proprio per questo i costruttori
    di tabella in `tables.py` devono produrre tipi stabili — una colonna
    che cambia tipo tra un run e l'altro fallirebbe il load.
    """

    kind = "bigquery"

    def __init__(self, project: str, dataset: str = DATASET_DEFAULT,
                 location: str = LOCATION_DEFAULT):
        from google.cloud import bigquery          # import pigro: opzionale

        self._bq = bigquery
        self.project = project
        self.dataset = dataset
        self.location = location
        self.client = bigquery.Client(project=project)
        ref = bigquery.Dataset(f"{project}.{dataset}")
        ref.location = location
        self.client.create_dataset(ref, exists_ok=True)

    def _table_id(self, table: str) -> str:
        return f"{self.project}.{self.dataset}.{table}"

    def write(self, table: str, df: pd.DataFrame) -> int:
        bq = self._bq
        cluster = [c for c in _CLUSTER_BY.get(table, []) if c in df.columns]
        cfg = bq.LoadJobConfig(
            write_disposition=bq.WriteDisposition.WRITE_APPEND,
            time_partitioning=bq.TimePartitioning(field="run_date")
            if "run_date" in df.columns else None,
            clustering_fields=cluster or None,
        )
        job = self.client.load_table_from_dataframe(
            df, self._table_id(table), job_config=cfg)
        job.result()
        return len(df)

    def existing_run_ids(self, table: str = "runs") -> set[str]:
        q = f"SELECT DISTINCT run_id FROM `{self._table_id(table)}`"
        try:
            return {r["run_id"] for r in self.client.query(q).result()}
        except Exception:
            return set()                                  # tabella non ancora creata

    def describe(self) -> str:
        return f"BigQuery ({self.project}.{self.dataset}, {self.location})"


class _NullBackend:
    """Registro disabilitato: accetta le scritture e non fa nulla."""

    kind = "off"

    def write(self, table: str, df: pd.DataFrame) -> int:
        return 0

    def existing_run_ids(self, table: str = "runs") -> set[str]:
        return set()

    def describe(self) -> str:
        return "disattivato"


def make_backend(mode: str | None = None, local_root: str | None = None):
    """Sceglie il backend. `mode` in {auto, bigquery, local, off}.

    In `auto` BigQuery viene tentato solo se il progetto e' configurato, e
    ogni fallimento (libreria assente, credenziali mancanti, permessi, scope
    della VM) degrada al backend locale con un messaggio esplicito, mai con
    un'eccezione: un problema di persistenza non deve far perdere un fit da
    quaranta minuti.
    """
    mode = (mode or os.environ.get("MMM_REGISTRY") or "auto").lower()
    local_root = local_root or os.path.join("output", "registry")

    if mode == "off":
        return _NullBackend()
    if mode == "local":
        return _LocalBackend(local_root)

    project = os.environ.get("MMM_BQ_PROJECT")
    if mode == "bigquery" and not project:
        raise RuntimeError(
            "MMM_REGISTRY=bigquery ma MMM_BQ_PROJECT non e' impostata.")
    if project:
        try:
            return _BigQueryBackend(
                project,
                os.environ.get("MMM_BQ_DATASET", DATASET_DEFAULT),
                os.environ.get("MMM_BQ_LOCATION", LOCATION_DEFAULT),
            )
        except Exception as exc:
            if mode == "bigquery":
                raise
            print(f"[registry] BigQuery non disponibile ({exc.__class__.__name__}: "
                  f"{exc}); uso il registro locale.")
    return _LocalBackend(local_root)


# --------------------------------------------------------------- registro

class RunRegistry:
    """Un'esecuzione della pipeline e le sue tabelle.

    Il ciclo di vita e' `start()` → `write()` ripetuti → `finish()`. Il
    record in `runs` viene scritto alla fine, non all'inizio: cosi' contiene
    l'esito reale (`ok` / `error`) e la durata, e un run interrotto a meta'
    non lascia nel registro una riga che sembra buona.
    """

    def __init__(self, run_id: str, started_at: dt.datetime, backend,
                 meta: dict[str, Any]):
        self.run_id = run_id
        self.started_at = started_at
        self.backend = backend
        self.meta = meta
        self.rows_written: dict[str, int] = {}

    # ---------------------------------------------------------- ciclo vita
    @classmethod
    def start(cls, seed: int | None = None,
              config: dict[str, Any] | None = None,
              inputs: Sequence[str] = (),
              label: str = "",
              mode: str | None = None,
              local_root: str | None = None) -> "RunRegistry":
        now = dt.datetime.now(dt.timezone.utc)
        backend = make_backend(mode, local_root)
        meta = {
            "label": label,
            "seed": seed,
            "config": config or {},
            "input_hash": hash_inputs(list(inputs)) if inputs else "",
            "input_files": [os.path.basename(p) for p in inputs],
            "libraries": library_versions(),
            "python": platform.python_version(),
            "platform": platform.platform(),
        }
        reg = cls(_new_run_id(now), now, backend, meta)
        print(f"[registry] run {reg.run_id} — backend {backend.describe()}")
        return reg

    def write(self, table: str, df: pd.DataFrame) -> int:
        """Scrive un DataFrame nella tabella, aggiungendo run_id e run_date.

        Un DataFrame vuoto non viene scritto: una tabella con righe fantasma
        e' peggio di una tabella che, per quel run, non ha nulla da dire.
        """
        if table not in TABLES:
            raise ValueError(f"tabella sconosciuta: {table!r}; attese {TABLES}")
        if df is None or len(df) == 0:
            return 0
        out = df.copy()
        out.insert(0, "run_id", self.run_id)
        out.insert(1, "run_date", self.started_at.date())
        n = self.backend.write(table, out)
        self.rows_written[table] = self.rows_written.get(table, 0) + n
        return n

    def diagnostics(self, values: dict[str, Any]) -> int:
        """Diagnostica in formato lungo (metrica, valore).

        Formato lungo e non largo di proposito: le metriche di fit cambiano
        nel tempo — si aggiunge un ESS, si toglie un R-hat — e una tabella
        larga costringerebbe a migrare lo schema a ogni aggiunta.
        """
        if not values:
            return 0
        rows = [{"metric": k,
                 "value_num": float(v) if isinstance(v, (int, float)) else None,
                 "value_txt": None if isinstance(v, (int, float)) else str(v)}
                for k, v in values.items()]
        return self.write("diagnostics", pd.DataFrame(rows))

    def finish(self, excel_path: str | None = None,
               artifact_uri: str = "", status: str = "ok",
               note: str = "") -> pd.DataFrame:
        """Chiude il run scrivendo il record in `runs`. Ritorna quel record."""
        now = dt.datetime.now(dt.timezone.utc)
        m = self.meta
        row = {
            "run_id": self.run_id,
            "run_date": self.started_at.date(),
            "started_at": self.started_at,
            "finished_at": now,
            "duration_s": round((now - self.started_at).total_seconds(), 1),
            "status": status,
            "label": m["label"],
            "seed": m["seed"],
            "config_json": _json(m["config"]),
            "input_hash": m["input_hash"],
            "input_files": ",".join(m["input_files"]),
            "libraries_json": _json(m["libraries"]),
            "python": m["python"],
            "platform": m["platform"],
            "excel_file": os.path.basename(excel_path) if excel_path else "",
            "artifact_uri": artifact_uri,
            "rows_json": _json(self.rows_written),
            "note": note,
        }
        df = pd.DataFrame([row])
        self.backend.write("runs", df)
        tot = sum(self.rows_written.values())
        print(f"[registry] run {self.run_id} chiuso ({status}): "
              f"{tot} righe in {len(self.rows_written)} tabelle "
              f"→ {self.backend.describe()}")
        return df

    # ---------------------------------------------------------- comodita'
    def __enter__(self) -> "RunRegistry":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.finish(status="ok" if exc_type is None else "error",
                    note="" if exc_type is None else f"{exc_type.__name__}: {exc}")
        return False        # non sopprime l'eccezione
