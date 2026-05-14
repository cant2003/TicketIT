import os
import signal
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PANEL_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path(os.getenv("PROJECT_DIR", "..")).resolve()

WEBHOOK_CMD = os.getenv(
    "WEBHOOK_CMD",
    r".\venv\Scripts\python.exe -m uvicorn webhook_app:app --host 0.0.0.0 --port 8000",
)

WORKER_CMD = os.getenv(
    "WORKER_CMD",
    r".\venv\Scripts\python.exe run_worker.py",
)

NGROK_CMD = os.getenv(
    "NGROK_CMD",
    "ngrok http 8000",
)

CREATE_NEW_PROCESS_GROUP = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0

processes = {}


SERVICES = {
    "webhook": WEBHOOK_CMD,
    "worker": WORKER_CMD,
    "ngrok": NGROK_CMD,
}


def is_running(service):
    process = processes.get(service)
    return bool(process and process.poll() is None)


def get_status():
    return {
        service: is_running(service)
        for service in SERVICES
    }


def start_service(service):
    if service not in SERVICES:
        return False, "Servicio no válido"

    if is_running(service):
        return True, f"{service} ya está encendido"

    command = SERVICES[service]

    process = subprocess.Popen(
        command,
        cwd=PROJECT_DIR,
        shell=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=CREATE_NEW_PROCESS_GROUP,
    )

    processes[service] = process
    return True, f"{service} iniciado"


def stop_service(service):
    if service not in SERVICES:
        return False, "Servicio no válido"

    process = processes.get(service)

    if not process:
        return True, f"{service} ya está apagado"

    try:
        if process.poll() is None:
            if os.name == "nt":
                process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                process.terminate()

            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        processes.pop(service, None)
        return True, f"{service} detenido"

    except Exception as e:
        return False, str(e)


def start_all():
    results = {}
    for service in SERVICES:
        ok, msg = start_service(service)
        results[service] = {"ok": ok, "msg": msg}
    return results


def stop_all():
    results = {}
    for service in list(SERVICES.keys()):
        ok, msg = stop_service(service)
        results[service] = {"ok": ok, "msg": msg}
    return results