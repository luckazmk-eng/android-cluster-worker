# Android Cluster Worker

Agente leve para registrar celulares Android com Termux em um coordenador Android Cluster.

## O que este repositório faz

- Instala dependências Python no Termux nativo.
- Recebe uma credencial de inscrição de uso único do servidor de distribuição.
- Salva as credenciais localmente com permissão restrita.
- Detecta informações básicas do dispositivo (modelo, Android, arquitetura, CPU, RAM e armazenamento).
- Registra o worker, envia heartbeats e consulta comandos permitidos.

## O que ele NÃO faz

- Não instala ComfyUI nem PyTorch no celular.
- Não transforma automaticamente vários celulares em uma única GPU/instância de difusão.
- Não executa comandos shell arbitrários recebidos do servidor.
- Não inclui tokens, senhas ou códigos de inscrição.

## Requisitos

- Android com Termux instalado de fonte compatível (recomendado: F-Droid ou GitHub oficial do Termux).
- Acesso à internet.
- URL HTTPS pública do gateway do cluster, que encaminhe as rotas de worker ao coordenador e as rotas de instalação ao servidor de distribuição.
- Código de inscrição válido, emitido pelo servidor principal.

> O gateway público ainda precisa ser configurado no servidor principal. Não use diretamente a URL privada do Tailscale em celulares que não estejam no mesmo tailnet.

## Instalação

No Termux do celular worker, baixe/clique no script ou execute os comandos abaixo depois de hospedar este repositório no GitHub:

```bash
pkg update -y
pkg install -y curl
curl -fsSL https://raw.githubusercontent.com/luckazmk-eng/android-cluster-worker/main/install.sh -o install.sh
bash install.sh
```

O instalador perguntará:
1. URL pública HTTPS do gateway (ex.: `https://seu-endereco.trycloudflare.com`).
2. Código de inscrição de uso único emitido pelo servidor principal.

O código é enviado ao endpoint `/enroll` por HTTPS. O instalador não imprime o token recebido.

## Iniciar / parar

```bash
cd ~/android-cluster-worker
./start.sh
./stop.sh
```

O agente grava logs em `worker.log`.

## Atualizar

```bash
cd ~/android-cluster-worker
./update.sh
```

O atualizador baixa apenas os arquivos do agente e scripts deste repositório. Ele preserva `worker.json` e `worker_id`.

## Inicialização após reiniciar o Android

A inicialização automática exige o aplicativo adicional Termux:Boot, instalado da mesma fonte do Termux. Este repositório não instala esse aplicativo automaticamente.

Depois de instalar Termux:Boot:

```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start-cluster-worker <<'EOF'
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
cd "$HOME/android-cluster-worker"
./start.sh
EOF
chmod +x ~/.termux/boot/start-cluster-worker
```

## Segurança

- Nunca publique `worker.json`, tokens, códigos de inscrição ou logs que possam conter dados sensíveis.
- O repositório deve ser privado se você adicionar informações internas.
- O coordenador deve validar `X-Worker-Id` e `X-Worker-Token`.
- Exponha publicamente somente as rotas de worker e instalação necessárias. Não exponha `/admin/*`.
- Use HTTPS no gateway público.
- As credenciais ficam em `~/android-cluster-worker/worker.json` com permissão `600`.

## Rotas esperadas

O agente usa estas rotas no gateway:
- `POST /workers/register`
- `POST /workers/heartbeat`
- `GET /workers/commands/next`
- `POST /workers/commands/{command_id}/result`

O servidor de distribuição precisa disponibilizar:
- `GET /health`
- `GET /worker_agent.py`
- `GET /enroll?code=...`

A rota `/enroll` deve consumir o código uma única vez e devolver JSON com `worker_id` e `worker_token`. O agente usa a URL do gateway informada durante a instalação como base da API.

## Comandos aceitos

- `ping`
- `collect_diagnostics`
- `restart_agent`

Comandos desconhecidos são recusados. Não existe execução remota arbitrária de shell.
