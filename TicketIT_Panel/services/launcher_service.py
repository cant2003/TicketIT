import os
import signal
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PANEL_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path(os.getenv("PROJECT_DIR", "..")).resolve()
LOG_DIR = PROJECT_DIR / "logs"

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
log_files = {}

SERVICES = {
    "webhook": WEBHOOK_CMD,
    "worker": WORKER_CMD,
    "ngrok": NGROK_CMD,
}


def is_running(service):
    process = processes.get(service)
    return bool(process and process.poll() is None)


def get_status():
    return {service: is_running(service) for service in SERVICES}


def start_service(service):
    if service not in SERVICES:
        return False, "Servicio no válido"

    if is_running(service):
        return True, f"{service} ya está encendido"

    LOG_DIR.mkdir(exist_ok=True)

    command = SERVICES[service]
    log_path = LOG_DIR / f"{service}.log"

    log_file = open(
        log_path,
        "a",
        encoding="utf-8",
        errors="replace",
    )

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    log_file.write("\n" + "=" * 70 + "\n")
    log_file.write(f"Iniciando servicio: {service}\n")
    log_file.write(f"Comando: {command}\n")
    log_file.write(f"Directorio: {PROJECT_DIR}\n")
    log_file.write("=" * 70 + "\n")
    log_file.flush()

    process = subprocess.Popen(
        command,
        cwd=PROJECT_DIR,
        shell=True,
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=CREATE_NEW_PROCESS_GROUP,
        env=env,
    )

    processes[service] = process
    log_files[service] = log_file

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

        log_file = log_files.pop(service, None)
        if log_file:
            log_file.write(f"\nServicio detenido: {service}\n")
            log_file.close()

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