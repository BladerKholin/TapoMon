"""
server/services/idle_engine.py
Motor de simulación IDLE del servidor central.

Justificación:
    Según el informe:
    "Simulación que se encarga de calcular y actualizar el estado de las
     mascotas mientras el usuario está desconectado, descontando estadísticas
     si se está mucho tiempo desconectado."

    Este componente corre como tarea programada (APScheduler) dentro del
    servidor FastAPI. Cada intervalo (configurable, default 60s):
    1. Busca TODOS los Tapos con Estado_Sistema == false (IDLE).
    2. Calcula cuántos "ticks" de degradación han pasado desde Last_Sync.
    3. Aplica la degradación (hambre, energía, felicidad, salud, vida).
    4. Actualiza Last_Sync en la base de datos.

    Replica exactamente la lógica de game_engine.aplicar_idle() del cliente,
    pero ejecutada centralizadamente para todas las mascotas IDLE.
    Esto garantiza que cuando el cliente se reconecte (resume_state),
    el estado ya está calculado.
"""
from __future__ import annotations

from datetime import datetime

from server.db.mongo import get_db
from server.config import (
    COL_MASCOTAS,
    IDLE_TICK_INTERVAL_SECONDS,
    TICK_HAMBRE,
    TICK_ENERGIA,
    TICK_FELICIDAD,
    TICK_SALUD_BASE,
    STAT_MIN,
    STAT_MAX,
)


def _clamp(value: int, lo: int = STAT_MIN, hi: int = STAT_MAX) -> int:
    """Limita un valor entre lo y hi."""
    return max(lo, min(hi, value))


def calcular_ticks_pendientes(last_sync_str: str) -> int:
    """
    Calcula cuántos ticks de degradación corresponden desde la última sync.
    Cada tick equivale a IDLE_TICK_INTERVAL_SECONDS.
    """
    try:
        last_sync = datetime.fromisoformat(last_sync_str)
    except (ValueError, TypeError):
        last_sync = datetime.now()

    delta_seconds = (datetime.now() - last_sync).total_seconds()
    return max(0, int(delta_seconds // IDLE_TICK_INTERVAL_SECONDS))


def aplicar_degradacion(tapo_doc: dict, ticks: int) -> dict:
    """
    Aplica N ticks de degradación a un documento Tapo.
    Modifica el dict in-place y lo retorna.
    
    Lógica de degradación (consistente con game_engine.py del cliente):
    - Cada tick: hambre -5, energía -3, felicidad -4
    - Si hambre o energía llegan a 0: salud -2
    - Si salud llega a 0: vida -2
    """
    vitales = tapo_doc.get("Vitales", {})
    estadistica = tapo_doc.get("Estadistica", {})

    for _ in range(ticks):
        # Verificar si la mascota aún tiene vida
        if estadistica.get("vida", 0) <= 0:
            break

        # Degradar vitales
        vitales["hambre"]    = _clamp(vitales.get("hambre", 100) + TICK_HAMBRE)
        vitales["energia"]   = _clamp(vitales.get("energia", 100) + TICK_ENERGIA)
        vitales["felicidad"] = _clamp(vitales.get("felicidad", 100) + TICK_FELICIDAD)

        # Salud cae si hambre o energía llegan a 0
        if vitales["hambre"] == 0 or vitales["energia"] == 0:
            vitales["salud"] = _clamp(vitales.get("salud", 100) + TICK_SALUD_BASE)

        # Vida cae si salud llega a 0
        if vitales.get("salud", 0) == 0:
            estadistica["vida"] = _clamp(estadistica.get("vida", 100) - 2)

    tapo_doc["Vitales"] = vitales
    tapo_doc["Estadistica"] = estadistica
    return tapo_doc


def ejecutar_idle_tick() -> int:
    """
    Tarea programada: procesa TODOS los Tapos en estado IDLE.
    
    Returns:
        Número de Tapos procesados.
    """
    db = get_db()
    
    # Buscar todos los Tapos en modo IDLE
    idle_tapos = list(db[COL_MASCOTAS].find({"Estado_Sistema": False}))
    
    procesados = 0
    for tapo_doc in idle_tapos:
        last_sync = tapo_doc.get("Last_Sync", datetime.now().isoformat())
        
        # Si Last_Sync es datetime de MongoDB, convertir a string
        if isinstance(last_sync, datetime):
            last_sync = last_sync.isoformat()

        ticks = calcular_ticks_pendientes(last_sync)
        if ticks == 0:
            continue

        # Aplicar degradación
        aplicar_degradacion(tapo_doc, ticks)

        # Actualizar en la base de datos
        db[COL_MASCOTAS].update_one(
            {"id_mascota": tapo_doc["id_mascota"]},
            {"$set": {
                "Vitales":     tapo_doc["Vitales"],
                "Estadistica": tapo_doc["Estadistica"],
                "Last_Sync":   datetime.now().isoformat(),
            }}
        )
        procesados += 1

    if procesados > 0:
        print(f"⏰  [IDLE] Procesados {procesados} Tapo(s) en modo IDLE.")

    return procesados
