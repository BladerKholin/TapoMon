"""
tests/conftest.py
Fixtures compartidos para todos los tests del servidor.

Provee:
- app_client: TestClient de FastAPI para tests de integración.
- Datos de prueba (usuario, tapo) para reutilizar entre tests.

NOTA: Los fixtures que requieren MongoDB (setup_test_data, auth_token)
NO son autouse — se aplican solo a los tests que los solicitan explícitamente.
Esto permite que los tests unitarios puros (JWT, clamp) corran sin MongoDB.
"""
from __future__ import annotations

import sys
import os
import hashlib
from datetime import datetime

import pytest

# Agregar el directorio padre al path para que 'server' sea importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ------------------------------------------------------------------ #
#  Datos de prueba
# ------------------------------------------------------------------ #
TEST_USER_ID   = "test-user-001"
TEST_TAPO_ID   = "test-tapo-001"
TEST_USERNAME  = "testplayer"
TEST_PASSWORD  = "testpass123"
TEST_EMAIL     = "test@tapomon.cl"

TEST_USER_DOC = {
    "Id":       TEST_USER_ID,
    "Username": TEST_USERNAME,
    "Correo":   TEST_EMAIL,
    "Password": hashlib.sha256(TEST_PASSWORD.encode()).hexdigest(),
    "Tapo_ID":  TEST_TAPO_ID,
}

TEST_TAPO_DOC = {
    "id_mascota":     TEST_TAPO_ID,
    "Nombre":         "TestTapo",
    "Vitales": {
        "hambre":        80,
        "energia":       70,
        "salud":         100,
        "felicidad":     90,
        "independencia": 50,
    },
    "Estadistica": {
        "vida":      100,
        "fuerza":    15,
        "defensa":   12,
        "velocidad": 10,
        "tipo":      "Fuego",
    },
    "Estado_Sistema": True,
    "Last_Sync":      datetime.now().isoformat(),
    "Friend_List":    [],
    "Gift_Cooldowns": [],
}


# ------------------------------------------------------------------ #
#  Helper para verificar si MongoDB está disponible
# ------------------------------------------------------------------ #
def _mongo_available() -> bool:
    """Verifica si MongoDB está corriendo y accesible."""
    try:
        from server.db.mongo import get_db
        get_db()
        return True
    except Exception:
        return False


requires_mongo = pytest.mark.skipif(
    not _mongo_available(),
    reason="MongoDB no está disponible."
)


# ------------------------------------------------------------------ #
#  Fixtures (NO autouse — solo para tests que los piden)
# ------------------------------------------------------------------ #

@pytest.fixture
def mongo_test_data():
    """
    Inserta datos de prueba en MongoDB y los limpia después.
    Solo se ejecuta en tests que lo solicitan explícitamente.
    """
    from server.db.mongo import get_db
    from server.config import COL_USUARIOS, COL_MASCOTAS, COL_INBOX

    db = get_db()

    # Limpiar datos previos de test
    db[COL_USUARIOS].delete_many({"Id": TEST_USER_ID})
    db[COL_MASCOTAS].delete_many({"id_mascota": TEST_TAPO_ID})
    db[COL_INBOX].delete_many({"Recipient_ID": TEST_TAPO_ID})

    # Insertar datos de prueba
    db[COL_USUARIOS].insert_one(TEST_USER_DOC.copy())
    db[COL_MASCOTAS].insert_one(TEST_TAPO_DOC.copy())

    yield db

    # Cleanup
    db[COL_USUARIOS].delete_many({"Id": TEST_USER_ID})
    db[COL_MASCOTAS].delete_many({"id_mascota": TEST_TAPO_ID})
    db[COL_INBOX].delete_many({"Recipient_ID": TEST_TAPO_ID})


@pytest.fixture
def app_client():
    """TestClient de FastAPI para hacer requests al servidor de prueba."""
    from fastapi.testclient import TestClient
    from server.main import app
    with TestClient(app) as client:
        yield client


@pytest.fixture
def auth_token(app_client, mongo_test_data):
    """Obtiene un JWT válido para usar en tests protegidos."""
    resp = app_client.post("/auth/login", json={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Headers con Authorization para requests protegidos."""
    return {"Authorization": f"Bearer {auth_token}"}
