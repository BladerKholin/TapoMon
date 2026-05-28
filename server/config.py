"""
server/config.py
Configuración centralizada del servidor TapoMon.

Justificación:
    Centralizar toda la configuración en un solo archivo permite:
    - Cambiar puertos, URIs y secretos sin tocar código de negocio.
    - Usar variables de entorno (.env) para cada ambiente (dev, prod).
    - Un único punto de verdad para constantes compartidas.
"""
from __future__ import annotations
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass


# ------------------------------------------------------------------ #
#  MongoDB
# ------------------------------------------------------------------ #
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB",  "Tapomon")

# ------------------------------------------------------------------ #
#  Servidor
# ------------------------------------------------------------------ #
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# ------------------------------------------------------------------ #
#  JWT
# ------------------------------------------------------------------ #
JWT_SECRET  = os.getenv("JWT_SECRET", "tapomon-dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# ------------------------------------------------------------------ #
#  Idle Simulation
# ------------------------------------------------------------------ #
IDLE_TICK_INTERVAL_SECONDS = int(os.getenv("IDLE_TICK_INTERVAL", "60"))

# Constantes de degradación (mismas que el game_engine del cliente)
TICK_HAMBRE      = -5
TICK_ENERGIA     = -3
TICK_FELICIDAD   = -4
TICK_SALUD_BASE  = -2

STAT_MIN = 0
STAT_MAX = 100

# ------------------------------------------------------------------ #
#  Colecciones MongoDB (consistente con el cliente)
# ------------------------------------------------------------------ #
COL_USUARIOS = "Usuarios"
COL_MASCOTAS = "Tapo"
COL_INBOX    = "Inbox"
