#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/luckazmk-eng/android-cluster-worker/main}"
BASE="$HOME/android-cluster-worker"
mkdir -p "$BASE/config"
cd "$BASE"
for file in worker_agent.py start.sh stop.sh requirements.txt; do
  curl -fsSL "$REPO_RAW/$file" -o "$file.new"
  mv "$file.new" "$file"
done
curl -fsSL "$REPO_RAW/config/worker.example.json" -o config/worker.example.json.new
mv config/worker.example.json.new config/worker.example.json
python -m pip install -r requirements.txt
chmod 700 start.sh stop.sh update.sh
echo "Arquivos atualizados. Credenciais preservadas."
echo "Reinicie o agente com: ./stop.sh && ./start.sh"
