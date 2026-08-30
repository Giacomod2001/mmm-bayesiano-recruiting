"""
Controllo 1 — ambiente della VM.

Verifica che ci sia tutto il necessario PRIMA di provare la pipeline:
versione di Python, pacchetti, risorse macchina, permessi di scrittura.
TensorFlow/Meridian e la GPU sono segnalati come `warn` se assenti: non
servono ai controlli di ingestion/Excel, ma servono al fit.
"""
from __future__ import annotations

import contextlib
import importlib
import os
import platform
import shutil
import sys

from ._util import Result, Timer, fail, ok, skip, verdict, warn

TITOLO = "Ambiente"

# pacchetto -> (obbligatorio?, a cosa serve)
PACCHETTI = {
    "pandas": (True, "tabelle: ingestion e allocator"),
    "numpy": (True, "calcolo numerico"),
    "openpyxl": (True, "lettura/scrittura .xlsx"),
    "pytest": (False, "suite di test pipeline/tests"),
    "statsmodels": (False, "diagnostica del notebook"),
    "matplotlib": (False, "grafici del notebook"),
    "pdfplumber": (False, "parser PDF dell'app di ingestion"),
    "tensorflow": (False, "fit Meridian (serve solo alla fase modello)"),
    "meridian": (False, "fit Meridian (serve solo alla fase modello)"),
}

MIN_DISCO_GB = 20
MIN_RAM_GB = 8


def _versione(mod: str) -> str:
    try:
        m = importlib.import_module(mod)
    except Exception as e:  # noqa: BLE001 — vogliamo il motivo esatto
        raise ImportError(str(e)) from e
    return getattr(m, "__version__", "versione ignota")


def _ram_gb() -> float | None:
    try:
        with open("/proc/meminfo", encoding="utf-8") as fh:
            for riga in fh:
                if riga.startswith("MemTotal:"):
                    return int(riga.split()[1]) / 1024 / 1024
    except OSError:
        return None
    return None


def run(ctx: dict) -> list[Result]:
    res: list[Result] = []

    # --- Python ------------------------------------------------------------
    v = sys.version_info
    res.append(verdict(
        "Python >= 3.10",
        v >= (3, 10),
        detail_ok=f"{v.major}.{v.minor}.{v.micro} ({sys.executable})",
        detail_ko=f"trovato {v.major}.{v.minor}: la pipeline usa la sintassi "
                  "`str | None`, serve almeno 3.10",
    ))
    res.append(ok("Sistema", f"{platform.system()} {platform.release()} "
                             f"({platform.machine()})"))

    # --- pacchetti ---------------------------------------------------------
    for nome, (obbligatorio, scopo) in PACCHETTI.items():
        try:
            ver = _versione(nome)
        except ImportError as e:
            msg = f"assente — {scopo}. Installa con: pip install {nome}"
            res.append(fail(f"pacchetto {nome}", msg) if obbligatorio
                       else warn(f"pacchetto {nome}", msg))
            if nome == "tensorflow":
                ctx["tf_assente"] = True
            continue
        res.append(ok(f"pacchetto {nome}", f"{ver} — {scopo}"))

    # --- GPU ---------------------------------------------------------------
    if ctx.get("tf_assente"):
        res.append(skip("GPU per il fit",
                        "TensorFlow non installato: controllo rimandato"))
    else:
        with Timer() as t:
            try:
                import tensorflow as tf  # noqa: PLC0415 — import volutamente pigro
                gpu = tf.config.list_physical_devices("GPU")
            except Exception as e:  # noqa: BLE001
                gpu, errore = [], str(e)
            else:
                errore = ""
        if errore:
            res.append(warn("GPU per il fit",
                            f"TensorFlow non si inizializza: {errore}",
                            t.elapsed))
        elif gpu:
            res.append(ok("GPU per il fit",
                          f"{len(gpu)} dispositivo/i: "
                          + ", ".join(d.name for d in gpu), t.elapsed))
        else:
            res.append(warn("GPU per il fit",
                            "nessuna GPU vista da TensorFlow: il fit gira su "
                            "CPU (~2-4h invece di 20-40 min)", t.elapsed))

    # --- risorse -----------------------------------------------------------
    cpu = os.cpu_count() or 0
    res.append(verdict("CPU disponibili", cpu >= 4, f"{cpu} core",
                       f"solo {cpu} core: il fit sarà lento", soft=True))

    ram = _ram_gb()
    if ram is None:
        res.append(skip("RAM", "non leggibile su questo sistema"))
    else:
        res.append(verdict("RAM", ram >= MIN_RAM_GB, f"{ram:.1f} GB",
                           f"{ram:.1f} GB: sotto i {MIN_RAM_GB} GB consigliati",
                           soft=True))

    libero = shutil.disk_usage(ctx["root"]).free / 1024 ** 3
    res.append(verdict("Spazio disco", libero >= MIN_DISCO_GB,
                       f"{libero:.1f} GB liberi",
                       f"{libero:.1f} GB liberi: sotto i {MIN_DISCO_GB} GB "
                       "consigliati (l'immagine Deep Learning + TF occupano "
                       "parecchio)", soft=True))

    # --- scrittura ---------------------------------------------------------
    prova = os.path.join(ctx["out_dir"], "_prova_scrittura.txt")
    try:
        with open(prova, "w", encoding="utf-8") as fh:
            fh.write("ok")
        with contextlib.suppress(OSError):   # su alcuni mount la cancellazione
            os.remove(prova)                 # non è concessa: non è un problema
        res.append(ok("Scrittura su disco", ctx["out_dir"]))
    except OSError as e:
        res.append(fail("Scrittura su disco",
                        f"non riesco a scrivere in {ctx['out_dir']}: {e}"))

    # --- pipeline importabile ---------------------------------------------
    try:
        from pipeline import config, schema  # noqa: F401,PLC0415
    except Exception as e:  # noqa: BLE001
        res.append(fail("Import del pacchetto `pipeline`",
                        f"{e}. Lancia lo script dalla radice del repo "
                        "(la cartella che contiene `pipeline/`)"))
    else:
        res.append(ok("Import del pacchetto `pipeline`",
                      f"{len(config.REGION_LIST)} regioni, "
                      f"granularità {config.WEEK_FREQ}"))
    return res
