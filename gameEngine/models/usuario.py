"""
models/usuario.py
Modelo de usuario según el esquema del informe.
"""
from dataclasses import dataclass, field
import hashlib


@dataclass
class Usuario:
    id:       str
    username: str
    correo:   str
    _password_hash: str = field(repr=False, default="")
    tapo_id:  str = ""

    # ------------------------------------------------------------------
    def set_password(self, plain: str) -> None:
        self._password_hash = hashlib.sha256(plain.encode()).hexdigest()

    def check_password(self, plain: str) -> bool:
        return self._password_hash == hashlib.sha256(plain.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "Id":       self.id,
            "Username": self.username,
            "Correo":   self.correo,
            "Password": self._password_hash,
            "Tapo_ID":  self.tapo_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Usuario":
        u = cls(
            id       = d["Id"],
            username = d["Username"],
            correo   = d["Correo"],
            tapo_id  = d.get("Tapo_ID", ""),
        )
        u._password_hash = d.get("Password", "")
        return u
