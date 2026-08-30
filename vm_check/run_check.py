#!/usr/bin/env python3
"""
Collaudo della VM: ambiente → ingestion → Excel → registro → catena completa.

Da lanciare dalla radice del repo (la cartella che contiene `pipeline/`):

    python3 vm_check/run_check.py            # collaudo standard (26 settimane)
    python3 vm_check/run_check.py --rapido   # versione veloce (13 settimane)
    python3 vm_check/run_check.py --settimane 52

Codice di uscita: 0 se nessun controllo è FAIL, 1 altrimenti — così lo
script si può usare anche dentro un altro comando o in CI.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import platform
import sys
import traceback

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RADICE not in sys.path:
    sys.path.insert(0, RADICE)

from vm_check.checks import _util as U           # noqa: E402
from vm_check.checks import c01_ambiente         # noqa: E402
from vm_check.checks import c02_ingestion        # noqa: E402
from vm_check.checks import c03_excel            # noqa: E402
from vm_check.checks import c04_registro         # noqa: E402
from vm_check.checks import c05_produzione       # noqa: E402

MODULI = (c01_ambiente, c02_ingestion, c03_excel, c04_registro,
          c05_produzione)
LARGH = 72


def _titolo(testo: str) -> str:
    return f"\n{testo}\n{'-' * min(len(testo), LARGH)}"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Collaudo dell'ambiente MMM su VM")
    ap.add_argument("--rapido", action="store_true",
                    help="mondo sintetico da 13 settimane invece di 26")
    ap.add_argument("--settimane", type=int, default=None,
                    help="settimane del mondo sintetico di prova")
    ap.add_argument("--out", default=os.path.join(RADICE, "vm_check", "out"),
                    help="cartella dove scrivere log e file di prova")
    ap.add_argument("--traceback", action="store_true",
                    help="stampa il traceback completo sugli errori inattesi")
    args = ap.parse_args()

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    ctx = {
        "root": RADICE,
        "out_dir": out_dir,
        "n_weeks": args.settimane or (13 if args.rapido else 26),
    }

    avvio = dt.datetime.now()
    righe: list[str] = [
        "=" * LARGH,
        "COLLAUDO VM — ambiente, ingestion, Excel, registro, produzione",
        f"avvio      {avvio:%Y-%m-%d %H:%M:%S}",
        f"macchina   {platform.node()} ({platform.system()})",
        f"repo       {RADICE}",
        f"output     {out_dir}",
        "=" * LARGH,
    ]
    for r in righe:
        print(r)

    tutti: list[U.Result] = []
    for mod in MODULI:
        titolo = _titolo(getattr(mod, "TITOLO", mod.__name__))
        print(titolo)
        righe.append(titolo)
        try:
            esiti = mod.run(ctx)
        except Exception as e:  # noqa: BLE001 — un controllo non deve bloccare gli altri
            dettaglio = f"{type(e).__name__}: {e}"
            if args.traceback:
                dettaglio += "\n" + traceback.format_exc()
            esiti = [U.fail(f"{getattr(mod, 'TITOLO', mod.__name__)} "
                            "(errore inatteso)", dettaglio)]
        for r in esiti:
            print(" ", r.line())
            righe.append("  " + r.line())
        tutti.extend(esiti)

    conta = {s: sum(1 for r in tutti if r.status == s)
             for s in (U.PASS, U.WARN, U.SKIP, U.FAIL)}
    durata = (dt.datetime.now() - avvio).total_seconds()
    falliti = [r for r in tutti if r.status == U.FAIL]

    coda = [
        "\n" + "=" * LARGH,
        f"ESITO: {conta[U.PASS]} ok · {conta[U.WARN]} avvisi · "
        f"{conta[U.SKIP]} saltati · {conta[U.FAIL]} falliti "
        f"— {durata:.0f}s",
    ]
    if falliti:
        coda.append("\nDa sistemare prima di lavorare sulla VM:")
        coda += [f"  · {r.name}: {r.detail}" for r in falliti]
    else:
        coda.append("La VM è pronta: la catena gira per intero, dall'ingestion\n"
                    "alle tabelle. Si può passare ai dati reali.")
        if any(r.status == U.WARN for r in tutti):
            coda.append("Gli avvisi non bloccano nulla: leggili sopra "
                        "(tipicamente GPU o pacchetti del solo fit).")
    coda.append("=" * LARGH)
    for r in coda:
        print(r)
    righe += coda

    log = os.path.join(out_dir, "report_check.txt")
    with open(log, "w", encoding="utf-8") as fh:
        fh.write("\n".join(righe) + "\n")
    print(f"\nReport salvato in {log}")

    return 1 if falliti else 0


if __name__ == "__main__":
    raise SystemExit(main())
