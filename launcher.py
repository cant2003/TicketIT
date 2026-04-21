import os
import signal
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
LOG_DIR = ROOT_DIR / "logs"
VENV_PYTHON = ROOT_DIR / "venv" / "Scripts" / "python.exe"

CREATE_NEW_PROCESS_GROUP = (
    subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
)

SERVICES = {
    "webhook": {
        "name": "Webhook",
        "command": [
            str(VENV_PYTHON),
            "-m",
            "uvicorn",
            "webhook_app:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
        "log": LOG_DIR / "webhook.log",
    },
    "worker": {
        "name": "Worker",
        "command": [str(VENV_PYTHON), "run_worker.py"],
        "log": LOG_DIR / "worker.log",
    },
    "ngrok": {
        "name": "Ngrok",
        "command": ["ngrok", "http", "8000"],
        "log": LOG_DIR / "ngrok.log",
    },
}

processes = {}


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def ensure_log_dir():
    LOG_DIR.mkdir(exist_ok=True)


def validate_environment():
    if not VENV_PYTHON.exists():
        raise FileNotFoundError(
            f"No se encontró el Python del entorno virtual: {VENV_PYTHON}"
        )


def is_running(key):
    entry = processes.get(key)
    return bool(entry and entry["process"].poll() is None)


def start_service(key):
    service = SERVICES[key]

    if is_running(key):
        print(f"{service['name']} ya está ejecutándose.")
        return

    log_file = open(service["log"], "a", encoding="utf-8", errors="replace")

    process = subprocess.Popen(
        service["command"],
        cwd=ROOT_DIR,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        creationflags=CREATE_NEW_PROCESS_GROUP,
    )

    processes[key] = {
        "process": process,
        "log_file": log_file,
    }

    print(f"{service['name']} iniciado.")


def stop_service(key):
    service = SERVICES[key]
    entry = processes.get(key)

    if not entry:
        print(f"{service['name']} no está registrado como activo.")
        return

    process = entry["process"]

    if process.poll() is None:
        try:
            if os.name == "nt":
                process.send_signal(signal.CTRL_BREAK_EVENT)
                time.sleep(1)

                if process.poll() is None:
                    process.terminate()
            else:
                process.terminate()

            process.wait(timeout=5)

        except Exception:
            process.kill()

    entry["log_file"].close()
    processes.pop(key, None)

    print(f"{service['name']} detenido.")


def start_all():
    ensure_log_dir()
    validate_environment()

    for key in SERVICES:
        start_service(key)


def stop_all():
    for key in list(processes.keys()):
        stop_service(key)


def show_status():
    print("\nEstado de servicios:\n")

    for key, service in SERVICES.items():
        status = "ENCENDIDO" if is_running(key) else "APAGADO"
        print(f"- {service['name']}: {status}")


def show_logs():
    print("\nLogs disponibles:\n")

    keys = list(SERVICES.keys())

    for index, key in enumerate(keys, start=1):
        print(f"{index}. {SERVICES[key]['name']}")

    print("0. Volver")

    option = input("\nSelecciona un log: ").strip()

    if option == "0":
        return

    try:
        key = keys[int(option) - 1]
    except (ValueError, IndexError):
        print("Opción inválida.")
        time.sleep(1)
        return

    log_path = SERVICES[key]["log"]

    clear_screen()
    print(f"Ultimas lineas de {SERVICES[key]['name']} ({log_path}):\n")

    if not log_path.exists():
        print("Aun no existe archivo de log.")
    else:
        lines = log_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()

        for line in lines[-60:]:
            print(line)

    input("\nPresiona Enter para volver...")


def menu():
    ensure_log_dir()
    validate_environment()

    while True:
        clear_screen()
        print("====================================")
        print("        TicketIT Launcher")
        print("====================================")
        show_status()
        print("\nAcciones:")
        print("1. Encender todo")
        print("2. Apagar todo")
        print("3. Encender Webhook")
        print("4. Apagar Webhook")
        print("5. Encender Worker")
        print("6. Apagar Worker")
        print("7. Encender Ngrok")
        print("8. Apagar Ngrok")
        print("9. Ver logs")
        print("0. Salir")
        print("====================================")

        option = input("Selecciona una opcion: ").strip()

        clear_screen()

        if option == "1":
            start_all()
        elif option == "2":
            stop_all()
        elif option == "3":
            start_service("webhook")
        elif option == "4":
            stop_service("webhook")
        elif option == "5":
            start_service("worker")
        elif option == "6":
            stop_service("worker")
        elif option == "7":
            start_service("ngrok")
        elif option == "8":
            stop_service("ngrok")
        elif option == "9":
            show_logs()
            continue
        elif option == "0":
            stop_all()
            print("Servicios detenidos. Saliendo...")
            break
        else:
            print("Opcion invalida.")

        time.sleep(1.2)


if __name__ == "__main__":
    try:
        menu()
    finally:
        stop_all()