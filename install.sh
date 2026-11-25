#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/luckazmk-eng/android-cluster-worker/main}"
BASE="$HOME/android-cluster-worker"
mkdir -p "$BASE/config"
cd "$BASE"

echo "== Android Cluster Worker =="
echo "Instalando dependências no Termux..."
pkg update -y
pkg install -y python curl
python -m pip install --upgrade pip
curl -fsSL "$REPO_RAW/requirements.txt" -o requirements.txt
python -m pip install -r requirements.txt
curl -fsSL "$REPO_RAW/config/worker.example.json" -o config/worker.example.json

read -r -p "URL HTTPS pública do gateway do cluster: " SERVER
SERVER="${SERVER%/}"
if [[ "$SERVER" != https://* ]]; then
  echo "ERRO: informe uma URL HTTPS válida."
  exit 1
fi

read -r -s -p "Código de inscrição de uso único: " CODE
echo
if [[ -z "$CODE" ]]; then
  echo "ERRO: código vazio."
  exit 1
fi

echo "Solicitando inscrição..."
TMP="$(mktemp)"
if ! curl -fsS --get \
  --data-urlencode "code=$CODE" \
  "$SERVER/enroll" -o "$TMP"; then
  rm -f "$TMP"
  echo "Falha na inscrição. Verifique URL e código."
  exit 1
fi
unset CODE

python - "$TMP" "$SERVER" "$BASE/worker.json" <<'PY'
import json, os, sys
src, server, dest = sys.argv[1:]
with open(src, encoding="utf-8") as source:
    data = json.load(source)
if not data.get("worker_id") or not data.get("worker_token"):
    raise SystemExit("Resposta de inscrição inválida.")
data["server"] = server
data.setdefault("heartbeat_seconds", 30)
data.setdefault("poll_seconds", 10)
with open(dest, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
os.chmod(dest, 0o600)
PY
rm -f "$TMP"

curl -fsSL "$REPO_RAW/worker_agent.py" -o worker_agent.py
curl -fsSL "$REPO_RAW/start.sh" -o start.sh
curl -fsSL "$REPO_RAW/stop.sh" -o stop.sh
curl -fsSL "$REPO_RAW/update.sh" -o update.sh
chmod 700 start.sh stop.sh update.sh
chmod 600 worker.json

echo
echo "Inscrição concluída. Iniciando agente..."
./start.sh
echo "Worker instalado em: $BASE"
