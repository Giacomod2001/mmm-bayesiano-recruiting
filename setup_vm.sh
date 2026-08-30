#!/usr/bin/env bash
# ============================================================================
# Setup ambiente MMM Meridian su VM Linux (Ubuntu 22.04/24.04) o WSL2.
# Uso:  bash setup_vm.sh          poi:  bash setup_vm.sh jupyter
# ============================================================================
set -euo pipefail

VENV_DIR="$HOME/mmm-venv"

if [ "${1:-}" = "jupyter" ]; then
    # --- Avvio JupyterLab (dopo il setup) ---------------------------------
    source "$VENV_DIR/bin/activate"
    echo "JupyterLab su porta 8888."
    echo "Dal tuo PC apri un tunnel:  ssh -L 8888:localhost:8888 utente@ip-della-vm"
    echo "poi vai su http://localhost:8888 (token stampato qui sotto)."
    jupyter lab --no-browser --port 8888 --ip 0.0.0.0
    exit 0
fi

# --- 1. Pacchetti di sistema -----------------------------------------------
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip

# --- 2. Ambiente virtuale ---------------------------------------------------
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip

# --- 3. Dipendenze del notebook (google-meridian trascina TensorFlow) -------
pip install "google-meridian>=1.6" openpyxl statsmodels jupyterlab

# --- 4. Verifica GPU (facoltativa: su CPU funziona, solo piu' lento) --------
python3 - <<'EOF'
import tensorflow as tf
gpu = tf.config.list_physical_devices('GPU')
print('GPU rilevata:', gpu[0].name if gpu else 'NESSUNA (fit su CPU: ~2-4h invece di 20-40min)')
EOF

echo
echo "Setup completato. Prossimi passi:"
echo "  1. copia kaggle_end_to_end.ipynb e i file dati sulla VM (scp o drag&drop Jupyter)"
echo "  2. avvia:  bash setup_vm.sh jupyter"
echo "  3. nel notebook, alla cella dati, indica la cartella dove hai messo i file"
