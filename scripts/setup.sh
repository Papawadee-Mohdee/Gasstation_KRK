#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# Never build a virtual environment using another virtual environment's Python.
PYTHON="$(command -v python3)"
if [[ -n "${VIRTUAL_ENV:-}" && "$PYTHON" == "$VIRTUAL_ENV/"* ]]; then
  PYTHON="$("$PYTHON" -c 'import sys; print(sys._base_executable)')"
fi
if [[ -e .venv || -L .venv ]]; then
  if ! .venv/bin/python -c 'import sys; assert sys.prefix != sys.base_prefix' >/dev/null 2>&1; then
    BACKUP="$(dirname "$ROOT")/gasstation-env-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP"
    mv .venv "$BACKUP/.venv"
    echo "Saved invalid environment to $BACKUP/.venv"
  fi
fi
if [[ ! -x .venv/bin/python ]]; then
  "$PYTHON" -m venv --copies .venv
fi
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
echo "Ready: source .venv/bin/activate && streamlit run app.py"
