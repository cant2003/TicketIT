import os

import requests

import pandas as pd



APPS_SCRIPT_REPORT_URL = os.getenv("APPS_SCRIPT_REPORT_URL")
APPS_SCRIPT_REPORT_SECRET = os.getenv("APPS_SCRIPT_REPORT_SECRET")


def generar_reporte_apps_script(
    *,
    estado: str | None = None,
    usuario: str | None = None,
    asignado: str | None = None,
    area: str | None = None,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    formato: str = "xlsx",
    nombre_archivo: str = "Reporte_Tickets",
):
    if not APPS_SCRIPT_REPORT_URL:
        raise ValueError("Falta APPS_SCRIPT_REPORT_URL en .env")

    if not APPS_SCRIPT_REPORT_SECRET:
        raise ValueError("Falta APPS_SCRIPT_REPORT_SECRET en .env")

    payload = {
        "secret": APPS_SCRIPT_REPORT_SECRET,
        "estado": estado or "",
        "usuario": usuario or "",
        "asignado": asignado or "",
        "area": area or "",
        "fechaInicio": fecha_inicio or "",
        "fechaFin": fecha_fin or "",
        "formato": formato,
        "nombreArchivo": nombre_archivo,
    }

    response = requests.post(
        APPS_SCRIPT_REPORT_URL,
        json=payload,
        timeout=90,
    )

    response.raise_for_status()
    data = response.json()

    if not data.get("ok"):
        raise RuntimeError(data.get("error", "Error desconocido generando reporte"))

    return data



def construir_dataframe(tickets):
    if tickets is None:
        return pd.DataFrame()

    if isinstance(tickets, pd.DataFrame):
        return tickets

    if isinstance(tickets, list):
        if not tickets:
            return pd.DataFrame()

        if isinstance(tickets[0], dict):
            return pd.DataFrame(tickets)

        if hasattr(tickets[0], "__dict__"):
            return pd.DataFrame([vars(t) for t in tickets])

        return pd.DataFrame(tickets)

    return pd.DataFrame([tickets])


def ordenar_dataframe(df):
    if df is None or df.empty:
        return df

    columnas_preferidas = [
        "id",
        "ticket_id",
        "folio",
        "fecha",
        "fecha_creacion",
        "usuario",
        "nombre",
        "area",
        "categoria",
        "descripcion",
        "estado",
        "asignado",
        "prioridad",
        "fecha_cierre",
    ]

    columnas_existentes = [c for c in columnas_preferidas if c in df.columns]
    columnas_restantes = [c for c in df.columns if c not in columnas_existentes]

    df = df[columnas_existentes + columnas_restantes]

    for columna in ["fecha_creacion", "fecha", "created_at"]:
        if columna in df.columns:
            try:
                df = df.sort_values(by=columna, ascending=False)
            except Exception:
                pass
            break

    return df