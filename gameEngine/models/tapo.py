"""
models/tapo.py
Modelo de la mascota Tapo, fiel al esquema de base de datos del informe.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TipoTapo(str, Enum):
    FUEGO   = "Fuego"
    AGUA    = "Agua"
    PLANTA  = "Planta"
    ROCA    = "Luz"
    ELECTRO = "Oscuridad"
    NORMAL  = "Normal"


@dataclass
class Vitales:
    hambre:        int = 100   # 0 = muerto de hambre, 100 = lleno
    energia:       int = 100
    salud:         int = 100
    felicidad:     int = 100
    independencia: int = 50    # qué tanto tolera estar solo

    def to_dict(self) -> dict:
        return {
            "hambre":        self.hambre,
            "energia":       self.energia,
            "salud":         self.salud,
            "felicidad":     self.felicidad,
            "independencia": self.independencia,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Vitales":
        return cls(**d)


@dataclass
class Estadistica:
    vida:      int = 100
    fuerza:    int = 10
    defensa:   int = 10
    velocidad: int = 10
    tipo:      TipoTapo = TipoTapo.NORMAL

    def to_dict(self) -> dict:
        return {
            "vida":      self.vida,
            "fuerza":    self.fuerza,
            "defensa":   self.defensa,
            "velocidad": self.velocidad,
            "tipo":      self.tipo.value,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Estadistica":
        d = dict(d)
        d["tipo"] = TipoTapo(d.get("tipo", "Normal"))
        return cls(**d)


@dataclass
class Tapo:
    id_mascota:   str
    nombre:       str
    vitales:      Vitales      = field(default_factory=Vitales)
    estadistica:  Estadistica  = field(default_factory=Estadistica)
    estado_sistema: bool       = True   # True = ACTIVE, False = IDLE
    last_sync:    datetime     = field(default_factory=datetime.now)
    friend_list:  list         = field(default_factory=list)
    gift_cooldowns: list       = field(default_factory=list)

    # ------------------------------------------------------------------ #
    #  Estado derivado
    # ------------------------------------------------------------------ #
    @property
    def esta_vivo(self) -> bool:
        return self.estadistica.vida > 0

    @property
    def estado_label(self) -> str:
        return "ACTIVE" if self.estado_sistema else "IDLE"

    # ------------------------------------------------------------------ #
    #  Serialización (para Local DB / Pet State Store)
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {
            "id_mascota":     self.id_mascota,
            "Nombre":         self.nombre,
            "Vitales":        self.vitales.to_dict(),
            "Estadistica":    self.estadistica.to_dict(),
            "Estado_Sistema": self.estado_sistema,
            "Last_Sync":      self.last_sync.isoformat(),
            "Friend_List":    self.friend_list,
            "Gift_Cooldowns": self.gift_cooldowns,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Tapo":
        return cls(
            id_mascota    = d["id_mascota"],
            nombre        = d["Nombre"],
            vitales       = Vitales.from_dict(d["Vitales"]),
            estadistica   = Estadistica.from_dict(d["Estadistica"]),
            estado_sistema= d.get("Estado_Sistema", True),
            last_sync     = datetime.fromisoformat(d.get("Last_Sync", datetime.now().isoformat())),
            friend_list   = d.get("Friend_List", []),
            gift_cooldowns= d.get("Gift_Cooldowns", []),
        )
