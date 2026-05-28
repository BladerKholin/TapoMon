"""
server/main.py
Punto de entrada del servidor central TapoMon.

Justificación:
    FastAPI como framework por:
    - Soporte async nativo (mejor rendimiento con I/O concurrente).
    - Validación automática con Pydantic (schemas.py).
    - Documentación OpenAPI auto-generada (/docs).
    - Lifecycle events (startup/shutdown) para manejar DB y scheduler.

    APScheduler ejecuta la simulación IDLE periódicamente sin necesidad
    de infraestructura adicional (Celery/Redis). Suficiente para el MVP.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

from server.api.sync_routes import router as sync_router
from server.api.auth_routes import router as auth_router
from server.db.mongo import get_db, cerrar_conexion, crear_indices
from server.services.idle_engine import ejecutar_idle_tick
from server.config import SERVER_HOST, SERVER_PORT, IDLE_TICK_INTERVAL_SECONDS


# ------------------------------------------------------------------ #
#  Scheduler para Idle Simulation
# ------------------------------------------------------------------ #
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle de FastAPI:
    - Startup: conectar a MongoDB, crear índices, iniciar scheduler.
    - Shutdown: detener scheduler, cerrar conexión a MongoDB.
    """
    # --- Startup ---
    print("🚀  Iniciando servidor TapoMon...")
    get_db()                # Forzar conexión a MongoDB
    crear_indices()         # Crear índices necesarios

    # Programar la simulación IDLE
    scheduler.add_job(
        ejecutar_idle_tick,
        "interval",
        seconds=IDLE_TICK_INTERVAL_SECONDS,
        id="idle_simulation",
        replace_existing=True,
    )
    scheduler.start()
    print(f"⏰  Idle Simulation programada cada {IDLE_TICK_INTERVAL_SECONDS}s.")

    yield

    # --- Shutdown ---
    print("🛑  Deteniendo servidor TapoMon...")
    scheduler.shutdown(wait=False)
    cerrar_conexion()


# ------------------------------------------------------------------ #
#  Aplicación FastAPI
# ------------------------------------------------------------------ #
app = FastAPI(
    title="TapoMon Central Server",
    description=(
        "Servidor central del sistema TapoMon.\n\n"
        "Expone el **SyncService** para sincronización de estado "
        "y ejecuta la **Idle Simulation** para mascotas desconectadas."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/auth", tags=["Autenticación"])
app.include_router(sync_router, prefix="/sync", tags=["SyncService"])


@app.get("/", tags=["Health"])
async def health_check():
    """Endpoint de salud para verificar que el servidor está corriendo."""
    return {
        "status": "ok",
        "service": "TapoMon Central Server",
        "version": "1.0.0",
    }


# ------------------------------------------------------------------ #
#  Ejecución directa
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
    )
