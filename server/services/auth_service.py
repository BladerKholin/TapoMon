"""
server/services/auth_service.py
Servicio de autenticación basado en JWT.

Justificación:
    El informe requiere autenticación en el servidor central para evitar
    suplantación de identidad. Usamos JWT porque:
    - Es stateless: el servidor no necesita guardar sesiones.
    - El token viaja en cada request (header Authorization).
    - Se firma con un secreto, garantizando integridad.
    
    El hash de password ya existe en el modelo Usuario del cliente,
    así que reutilizamos esa lógica (SHA-256).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import jwt

from server.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
from server.db.mongo import get_db
from server.config import COL_USUARIOS


def _hash_password(plain: str) -> str:
    """Mismo hash SHA-256 que usa el modelo Usuario del cliente."""
    return hashlib.sha256(plain.encode()).hexdigest()


def autenticar_usuario(username: str, password: str) -> dict | None:
    """
    Verifica credenciales contra la base de datos.
    Retorna el documento del usuario si es válido, None si no.
    """
    db = get_db()
    usuario = db[COL_USUARIOS].find_one(
        {"Username": {"$regex": f"^{username}$", "$options": "i"}}
    )

    if usuario is None:
        return None

    password_hash = _hash_password(password)
    if usuario.get("Password") != password_hash:
        return None

    return usuario


def generar_token(usuario_doc: dict) -> str:
    """
    Genera un JWT firmado con los datos del usuario.
    El token contiene: usuario_id, username, y tiempo de expiración.
    """
    payload = {
        "sub": usuario_doc["Id"],
        "username": usuario_doc["Username"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verificar_token(token: str) -> dict | None:
    """
    Decodifica y valida un JWT.
    Retorna el payload si es válido, None si expiró o es inválido.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def obtener_usuario_id_desde_token(token: str) -> str | None:
    """Extrae el usuario_id (campo 'sub') del token."""
    payload = verificar_token(token)
    if payload:
        return payload.get("sub")
    return None
