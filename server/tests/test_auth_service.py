"""
tests/test_auth_service.py
Tests unitarios del servicio de autenticación JWT.

Tests divididos en:
- TestHashPassword y TestJWT: PUROS (sin MongoDB).
- TestAutenticarUsuario: Requiere MongoDB (usa fixture mongo_test_data).
"""
from __future__ import annotations

import sys
import os
import hashlib

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from server.services.auth_service import (
    autenticar_usuario,
    generar_token,
    verificar_token,
    obtener_usuario_id_desde_token,
    _hash_password,
)
from server.tests.conftest import (
    TEST_USERNAME, TEST_PASSWORD, TEST_USER_ID, requires_mongo,
)


# ================================================================== #
#  Tests PUROS (sin MongoDB)
# ================================================================== #

class TestHashPassword:
    """Tests del hash de password — no requiere MongoDB."""

    def test_hash_es_consistente(self):
        """El mismo password siempre genera el mismo hash."""
        h1 = _hash_password("testpass")
        h2 = _hash_password("testpass")
        assert h1 == h2

    def test_hash_es_sha256(self):
        """El hash usa SHA-256 (compatible con el cliente)."""
        h = _hash_password("hello")
        expected = hashlib.sha256(b"hello").hexdigest()
        assert h == expected

    def test_passwords_distintos_dan_hash_distinto(self):
        h1 = _hash_password("pass1")
        h2 = _hash_password("pass2")
        assert h1 != h2


class TestJWT:
    """Tests de generación y verificación de JWT — no requiere MongoDB."""

    def test_generar_y_verificar_token(self):
        """Un token generado debe poder verificarse."""
        user_doc = {"Id": "u1", "Username": "player1"}
        token = generar_token(user_doc)
        payload = verificar_token(token)
        assert payload is not None
        assert payload["sub"] == "u1"
        assert payload["username"] == "player1"

    def test_token_invalido(self):
        """Un token manipulado debe ser rechazado."""
        result = verificar_token("token.invalido.aqui")
        assert result is None

    def test_obtener_usuario_id(self):
        """Extrae correctamente el usuario_id del token."""
        user_doc = {"Id": "u42", "Username": "test"}
        token = generar_token(user_doc)
        uid = obtener_usuario_id_desde_token(token)
        assert uid == "u42"

    def test_obtener_usuario_id_token_invalido(self):
        """Token inválido retorna None."""
        uid = obtener_usuario_id_desde_token("basura")
        assert uid is None


# ================================================================== #
#  Tests que REQUIEREN MongoDB
# ================================================================== #

@requires_mongo
class TestAutenticarUsuario:
    """Tests de autenticación contra MongoDB."""

    def test_login_exitoso(self, mongo_test_data):
        """Login con credenciales correctas retorna el documento."""
        result = autenticar_usuario(TEST_USERNAME, TEST_PASSWORD)
        assert result is not None
        assert result["Id"] == TEST_USER_ID
        assert result["Username"] == TEST_USERNAME

    def test_login_password_incorrecto(self, mongo_test_data):
        """Login con password incorrecto retorna None."""
        result = autenticar_usuario(TEST_USERNAME, "wrongpassword")
        assert result is None

    def test_login_usuario_inexistente(self, mongo_test_data):
        """Login con usuario que no existe retorna None."""
        result = autenticar_usuario("noexiste", TEST_PASSWORD)
        assert result is None

    def test_login_case_insensitive(self, mongo_test_data):
        """El username no es case-sensitive."""
        result = autenticar_usuario(TEST_USERNAME.upper(), TEST_PASSWORD)
        assert result is not None
