"""
p2pEngine/p2p_protocol.py
Definiciones del protocolo de mensajes para el combate P2P entre Tapos.
Todos los mensajes se serializan como JSON sobre TCP.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
import json


# ------------------------------------------------------------------ #
#  Tipos de mensaje
# ------------------------------------------------------------------ #

class MsgType(str, Enum):
    # Handshake / sesión
    HELLO        = "HELLO"         # el challenger envía su Tapo
    HELLO_ACK    = "HELLO_ACK"     # el host responde con su Tapo + acepta/rechaza
    READY        = "READY"         # ambos lados listos para empezar
    REJECT       = "REJECT"        # el host rechaza el combate

    # Turno
    ROLL_REQUEST = "ROLL_REQUEST"  # el atacante pide que el defensor registre su tirada de armadura
    ATTACK_ROLL  = "ATTACK_ROLL"   # resultado del ataque del turno (atacante → defensor)
    DEFENSE_ROLL = "DEFENSE_ROLL"  # tirada de armadura del defensor (defensor → atacante)
    DAMAGE       = "DAMAGE"        # daño resultante (calculado por el atacante, enviado a defensor)
    TURN_END     = "TURN_END"      # fin de turno, alternamos roles

    # Control
    SURRENDER    = "SURRENDER"     # un jugador se rinde
    GAME_OVER    = "GAME_OVER"     # la batalla terminó (HP llegó a 0)
    PING         = "PING"
    PONG         = "PONG"
    ERROR        = "ERROR"


# ------------------------------------------------------------------ #
#  Estructura genérica de mensaje
# ------------------------------------------------------------------ #

@dataclass
class Mensaje:
    tipo:    str          # MsgType.value
    payload: dict

    def encode(self) -> bytes:
        raw = json.dumps({"tipo": self.tipo, "payload": self.payload})
        return (raw + "\n").encode("utf-8")

    @staticmethod
    def decode(data: bytes) -> "Mensaje":
        obj = json.loads(data.decode("utf-8").strip())
        return Mensaje(tipo=obj["tipo"], payload=obj.get("payload", {}))


# ------------------------------------------------------------------ #
#  Helpers de construcción de mensajes
# ------------------------------------------------------------------ #

def msg_hello(tapo_dict: dict) -> Mensaje:
    return Mensaje(MsgType.HELLO, {"tapo": tapo_dict})

def msg_hello_ack(tapo_dict: dict, acepta: bool = True) -> Mensaje:
    return Mensaje(MsgType.HELLO_ACK, {"tapo": tapo_dict, "acepta": acepta})

def msg_reject(razon: str = "") -> Mensaje:
    return Mensaje(MsgType.REJECT, {"razon": razon})

def msg_ready() -> Mensaje:
    return Mensaje(MsgType.READY, {})

def msg_attack_roll(resultado: int, tiene_ventaja: bool = False, tiene_desventaja: bool = False) -> Mensaje:
    return Mensaje(MsgType.ATTACK_ROLL, {
        "resultado": resultado,
        "ventaja": tiene_ventaja,
        "desventaja": tiene_desventaja,
    })

def msg_defense_roll(armor_class: int) -> Mensaje:
    return Mensaje(MsgType.DEFENSE_ROLL, {"armor_class": armor_class})

def msg_damage(dano: int, golpeo: bool) -> Mensaje:
    return Mensaje(MsgType.DAMAGE, {"dano": dano, "golpeo": golpeo})

def msg_turn_end(hp_atacante: int, hp_defensor: int) -> Mensaje:
    return Mensaje(MsgType.TURN_END, {"hp_atacante": hp_atacante, "hp_defensor": hp_defensor})

def msg_surrender() -> Mensaje:
    return Mensaje(MsgType.SURRENDER, {})

def msg_game_over(ganador: str) -> Mensaje:
    return Mensaje(MsgType.GAME_OVER, {"ganador": ganador})

def msg_ping() -> Mensaje:
    return Mensaje(MsgType.PING, {})

def msg_pong() -> Mensaje:
    return Mensaje(MsgType.PONG, {})

def msg_error(detalle: str) -> Mensaje:
    return Mensaje(MsgType.ERROR, {"detalle": detalle})
