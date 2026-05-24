"""
p2pEngine/__init__.py
Paquete de combate P2P para TapoMon.
"""
from p2pEngine.combat_engine import (
    calcular_attack_roll,
    calcular_armor_class,
    calcular_dano,
    resolver_turno,
    EstadoCombate,
    TABLA_TIPOS,
)
from p2pEngine.p2p_server import ServidorCombate
from p2pEngine.p2p_client import ClienteCombate
from p2pEngine.battle_cli import menu_batalla

__all__ = [
    "calcular_attack_roll",
    "calcular_armor_class",
    "calcular_dano",
    "resolver_turno",
    "EstadoCombate",
    "TABLA_TIPOS",
    "ServidorCombate",
    "ClienteCombate",
    "menu_batalla",
]
