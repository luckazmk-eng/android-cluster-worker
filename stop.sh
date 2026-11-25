#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/android-cluster-worker"
if [[ -f worker.pid ]]; then
  PID="$(cat worker.pid)"
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    echo "Sinal de parada enviado ao agente (PID $PID)."
  else
    echo "Agente não está em execução."
  fi
  rm -f worker.pid
else
  echo "PID do agente não encontrado."
fi
