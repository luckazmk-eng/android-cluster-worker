#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/luckazmk-eng/android-cluster-worker/main}"
BASE="$HOME/android-cluster-worker"
mkdir -p "$BASE"
cd "$BASE"
for file in worker_agent.py start.sh stop.sh requirements.txt; do
  curl -fsSL "$REPO_RAW/$file" -o "$file.new"
  mv "$file.new" "$file"
done
python -m pip install -r requirements.txt
chmod 700 start.sh stop.sh update.sh
echo "Arquivos atualizados. Credenciais preservadas."
echo "Reinicie o agente com: ./stop.sh && ./start.sh"
