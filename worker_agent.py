#!/usr/bin/env python
"""Agente Android/Termux para o Android Cluster. Sem execução arbitrária de shell."""
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import traceback
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "worker.json"
LOG = ROOT / "worker.log"
SESSION = requests.Session()
SESSION.headers.update({"Content-Type": "application/json"})


def log(message):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_config():
    if not CONFIG.exists():
        raise RuntimeError("worker.json ausente. Execute install.sh primeiro.")
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    for key in ("server", "worker_id", "worker_token"):
        if not data.get(key):
            raise RuntimeError(f"Configuração incompleta: {key}")
    data["server"] = data["server"].rstrip("/")
    return data


def run_getprop(prop):
    try:
        return subprocess.check_output(
            ["getprop", prop], stderr=subprocess.DEVNULL, text=True, timeout=2
        ).strip()
    except Exception:
        return ""


def memory_info():
    result = {"ram_total_kb": None, "ram_available_kb": None}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                result["ram_total_kb"] = int(line.split()[1])
            elif line.startswith("MemAvailable:"):
                result["ram_available_kb"] = int(line.split()[1])
    except Exception:
        pass
    return result


def storage_info():
    try:
        usage = shutil.disk_usage(str(Path.home()))
        return {"storage_total_bytes": usage.total, "storage_free_bytes": usage.free}
    except Exception:
        return {}


def detect_device():
    cpuinfo = ""
    try:
        cpuinfo = Path("/proc/cpuinfo").read_text(errors="ignore")
    except Exception:
        pass

    cpu_model = ""
    for line in cpuinfo.splitlines():
        low = line.lower()
        if low.startswith(("model name", "hardware", "processor")):
            parts = line.split(":", 1)
            if len(parts) == 2 and parts[1].strip():
                cpu_model = parts[1].strip()
                break

    cores = os.cpu_count() or 1
    android_release = run_getprop("ro.build.version.release")
    device = {
        "hostname": socket.gethostname(),
        "manufacturer": run_getprop("ro.product.manufacturer"),
        "model": run_getprop("ro.product.model"),
        "device": run_getprop("ro.product.device"),
        "android_version": android_release,
        "sdk": run_getprop("ro.build.version.sdk"),
        "architecture": platform.machine(),
        "platform": platform.platform(),
        "cpu_model": cpu_model,
        "cpu_cores": cores,
        "python": sys.version.split()[0],
    }
    resources = {}
    resources.update(memory_info())
    resources.update(storage_info())
    return device, resources


def api_headers(cfg):
    return {
        "X-Worker-Id": cfg["worker_id"],
        "X-Worker-Token": cfg["worker_token"],
    }


def request_json(method, url, cfg, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.update(api_headers(cfg))
    response = SESSION.request(method, url, headers=headers, timeout=20, **kwargs)
    response.raise_for_status()
    if response.content:
        return response.json()
    return {}


def register(cfg):
    device, resources = detect_device()
    payload = {
        "device": device,
        "capabilities": ["android", "termux", "cpu", "hardware_detection"],
        "resources": resources,
    }
    result = request_json("POST", cfg["server"] + "/workers/register", cfg, json=payload)
    log("Registro enviado ao coordenador.")
    return result


def heartbeat(cfg):
    device, resources = detect_device()
    payload = {"device": device, "capabilities": ["android", "termux", "cpu", "hardware_detection"], "resources": resources}
    request_json("POST", cfg["server"] + "/workers/heartbeat", cfg, json=payload)


def poll_command(cfg):
    return request_json("GET", cfg["server"] + "/workers/commands/next", cfg)


def send_result(cfg, command_id, result):
    return request_json(
        "POST",
        cfg["server"] + f"/workers/commands/{command_id}/result",
        cfg,
        json=result,
    )


def handle_command(command):
    action = command.get("action") or command.get("command")
    if action == "ping":
        return {"ok": True, "message": "pong"}
    if action == "collect_diagnostics":
        device, resources = detect_device()
        return {"ok": True, "device": device, "resources": resources}
    if action == "restart_agent":
        return {"ok": True, "message": "agent will restart"}
    return {"ok": False, "error": "command_not_allowed"}


def main():
    cfg = load_config()
    heartbeat_seconds = max(15, int(cfg.get("heartbeat_seconds", 30)))
    poll_seconds = max(5, int(cfg.get("poll_seconds", 10)))
    log(f"Worker iniciado: {cfg['worker_id']}")
    try:
        register(cfg)
    except Exception as exc:
        log(f"Falha no registro inicial: {exc}")

    last_heartbeat = 0
    while True:
        try:
            now = time.time()
            if now - last_heartbeat >= heartbeat_seconds:
                heartbeat(cfg)
                last_heartbeat = now
            command = poll_command(cfg)
            if command and command.get("command_id"):
                command_id = command["command_id"]
                result = handle_command(command)
                send_result(cfg, command_id, result)
                if (command.get("action") or command.get("command")) == "restart_agent":
                    log("Reinício solicitado; encerrando agente.")
                    return
        except requests.RequestException as exc:
            log(f"Falha de comunicação: {exc}")
        except Exception as exc:
            log(f"Erro: {exc}")
            log(traceback.format_exc())
        time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
