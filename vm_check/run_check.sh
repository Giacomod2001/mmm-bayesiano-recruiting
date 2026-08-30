#!/usr/bin/env bash
# ============================================================================
# Collaudo della VM: ambiente -> ingestion -> Excel.
#
#   bash vm_check/run_check.sh              collaudo standard
#   bash vm_check/run_check.sh --rapido     versione veloce (13 settimane)
#   bash vm_check/run_check.sh --installa   installa prima le dipendenze
#
# Trova da solo l'interprete giusto: venv attivo > ~/mmm-venv > python3.
# Esce con codice 1 se almeno un controllo fallisce.
# ============================================================================
set -uo pipefail

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RADICE="$(dirname "$QUI")"
OUT="$QUI/out"
mkdir -p "$OUT"

# --- interprete -------------------------------------------------------------
if [ -n "${VIRTUAL_ENV:-}" ]; then
    PY="$VIRTUAL_ENV/bin/python"
elif [ -x "$HOME/mmm-venv/bin/python" ]; then
    PY="$HOME/mmm-venv/bin/python"        # venv creato da setup_vm.sh
elif command -v python3 >/dev/null 2>&1; then
    PY="python3"
else
    echo "ERRORE: nessun python3 trovato. Su Ubuntu: sudo apt-get install -y python3 python3-venv" >&2
    exit 1
fi
echo "Interprete: $PY  ($("$PY" --version 2>&1))"

# --- installazione dipendenze (facoltativa) ---------------------------------
ARGS=()
for a in "$@"; do
    if [ "$a" = "--installa" ] || [ "$a" = "--install" ]; then
        echo "Installo le dipendenze minime per il collaudo..."
        "$PY" -m pip install --upgrade pip
        "$PY" -m pip install "pandas>=2.0" "numpy>=1.24" "openpyxl>=3.1" pytest
    else
        ARGS+=("$a")
    fi
done

# --- esecuzione --------------------------------------------------------------
cd "$RADICE"
LOG="$OUT/ultimo_check.log"
"$PY" vm_check/run_check.py ${ARGS[@]+"${ARGS[@]}"} 2>&1 | tee "$LOG"
ESITO=${PIPESTATUS[0]}

echo
if [ "$ESITO" -eq 0 ]; then
    echo "Collaudo superato. Log completo: $LOG"
else
    echo "Collaudo FALLITO: leggi le righe [FAIL] qui sopra o in $LOG"
fi
exit "$ESITO"
