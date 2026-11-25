#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/android-cluster-worker"
if [[ ! -f worker.json ]]; then
  echo "worker.json não encontrado. Execute install.sh."
  exit 1
fi
if [[ -f worker.pid ]] && kill -0 "$(cat worker.pid)" 2>/dev/null; then
  echo "Agente já está em execução (PID $(cat worker.pid))."
  exit 0
fi
nohup python worker_agent.py >> worker.log 2>&1 < /dev/null &
echo $! > worker.pid
sleep 2
if kill -0 "$(cat worker.pid)" 2>/dev/null; then
  echo "Agente iniciado. PID $(cat worker.pid)"
else
  echo "Falha ao iniciar. Consulte worker.log"
  exit 1
fi
