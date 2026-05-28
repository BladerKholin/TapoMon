"""
network/config.py
Configuración de red del cliente TapoMon.

Justificación:
    Centraliza la URL del servidor y timeouts para que sean
    fácilmente configurables. Usa variables de entorno para
    permitir apuntar a diferentes servidores (dev, staging, prod).
"""
from __future__ import annotations
import os

# URL base del servidor central
SERVER_URL = os.getenv("TAPOMON_SERVER_URL", "http://localhost:8000")

# Timeout para requests HTTP (segundos)
REQUEST_TIMEOUT = int(os.getenv("TAPOMON_REQUEST_TIMEOUT", "10"))
