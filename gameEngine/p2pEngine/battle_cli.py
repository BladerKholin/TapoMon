"""
p2pEngine/battle_cli.py
Interfaz de consola para iniciar un combate P2P entre Tapos.

Permite al usuario actuar como HOST o CHALLENGER directamente
desde el menú principal del juego o ejecutando este archivo.

Uso standalone:
    python battle_cli.py host   --tapo-id <id>
    python battle_cli.py join   --tapo-id <id> --ip <ip_del_host>
"""
from __future__ import annotations

import sys
import os
import threading

# Configurar sys.path para importar módulos del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.tapo import Tapo
from p2pEngine.p2p_server import ServidorCombate, DEFAULT_PORT
from p2pEngine.p2p_client import ClienteCombate
from p2pEngine.combat_engine import TABLA_TIPOS


# ──────────────────────────────────────────────────────────────────── #
#  Utilidades de consola
# ──────────────────────────────────────────────────────────────────── #

def _cls():
    os.system("cls" if os.name == "nt" else "clear")

def _sep(char="─", n=52):
    print(char * n)

def _titulo(texto: str):
    _sep("═")
    print(f"  ⚔️   {texto}")
    _sep("═")

def _log_combate(msg: str):
    print(msg)


# ──────────────────────────────────────────────────────────────────── #
#  Pantalla de inicio de combate
# ──────────────────────────────────────────────────────────────────── #

def mostrar_info_tapo(tapo: Tapo):
    e = tapo.estadistica
    _sep()
    print(f"  🐾 {tapo.nombre}  [{e.tipo.value}]")
    print(f"     ❤️  Vida:      {e.vida}")
    print(f"     ⚡  Fuerza:    {e.fuerza}  (mod: +{e.fuerza // 10})")
    print(f"     🛡️  Defensa:   {e.defensa}  (mod: +{e.defensa // 10})")
    print(f"     💨  Velocidad: {e.velocidad}  (mod: +{e.velocidad // 10})")
    _sep()


def mostrar_tabla_tipos():
    """Muestra la tabla de ventajas/desventajas de tipos."""
    print("\n  📊  Tabla de ventajas de tipo:\n")
    tipos = list(TABLA_TIPOS.keys())
    header = "         " + "  ".join(f"{t.value[:3]:>3}" for t in tipos)
    print(header)
    for atk in tipos:
        fila = f"  {atk.value:<9}"
        for def_ in tipos:
            rel = TABLA_TIPOS[atk][def_]
            if rel == "ventaja":
                icono = " ✅"
            elif rel == "desventaja":
                icono = " ❌"
            else:
                icono = "  —"
            fila += icono + " "
        print(fila)
    print()


# ──────────────────────────────────────────────────────────────────── #
#  Flujo HOST
# ──────────────────────────────────────────────────────────────────── #

def flujo_host(tapo: Tapo) -> None:
    """El jugador actúa como HOST: abre el servidor y espera al rival."""
    _cls()
    _titulo("MODO HOST  —  Esperando rival...")
    mostrar_info_tapo(tapo)

    import socket
    ip_local = socket.gethostbyname(socket.gethostname())
    print(f"\n  📡 Tu IP local: {ip_local}")
    print(f"  🔌 Puerto:      {DEFAULT_PORT}")
    print(f"\n  Comparte esta IP con tu rival para que se conecte.")
    print(f"  Presiona Ctrl+C para cancelar.\n")

    servidor = ServidorCombate(tapo, callback_log=_log_combate)

    try:
        servidor.iniciar()
    except KeyboardInterrupt:
        print("\n  [HOST] Combate cancelado.")

    _pausa_final()


# ──────────────────────────────────────────────────────────────────── #
#  Flujo CHALLENGER
# ──────────────────────────────────────────────────────────────────── #

def flujo_challenger(tapo: Tapo) -> None:
    """El jugador actúa como CHALLENGER: se conecta a la IP del host."""
    _cls()
    _titulo("MODO CHALLENGER  —  Conectándose al rival...")
    mostrar_info_tapo(tapo)

    ip_host = input("  🌐 IP del host: ").strip()
    if not ip_host:
        print("  IP vacía. Cancelando.")
        return

    cliente = ClienteCombate(tapo, host_ip=ip_host, callback_log=_log_combate)

    try:
        cliente.conectar()
    except KeyboardInterrupt:
        print("\n  [CLIENT] Combate cancelado.")
    except ConnectionRefusedError:
        print(f"\n  ❌ No se pudo conectar a {ip_host}:{DEFAULT_PORT}. ¿Está el host esperando?")

    _pausa_final()


# ──────────────────────────────────────────────────────────────────── #
#  Menú de batalla integrable desde main.py
# ──────────────────────────────────────────────────────────────────── #

def menu_batalla(tapo: Tapo) -> None:
    """
    Punto de entrada para el menú de combate P2P.
    Llama a esta función desde main.py pasando el Tapo activo.
    """
    _cls()
    _titulo("COMBATE P2P  —  TapoMon")
    mostrar_info_tapo(tapo)

    print("  1. Ser HOST  (esperar rival en tu red)")
    print("  2. Unirse   (conectar a un host existente)")
    print("  3. Ver tabla de tipos")
    print("  0. Volver al menú principal")
    _sep()

    opcion = input("  Opción: ").strip()

    if opcion == "1":
        flujo_host(tapo)
    elif opcion == "2":
        flujo_challenger(tapo)
    elif opcion == "3":
        mostrar_tabla_tipos()
        input("  [Enter para continuar]")
        menu_batalla(tapo)
    elif opcion == "0":
        return
    else:
        print("  ❌ Opción no válida.")
        input("  [Enter para continuar]")
        menu_batalla(tapo)


def _pausa_final():
    print()
    input("  [Enter para continuar]")


# ──────────────────────────────────────────────────────────────────── #
#  Ejecución standalone (para pruebas)
# ──────────────────────────────────────────────────────────────────── #

if __name__ == "__main__":
    from models.tapo import Tapo, Vitales, Estadistica, TipoTapo

    # Tapo de prueba
    tapo_demo = Tapo(
        id_mascota="demo-001",
        nombre="Ignis",
        vitales=Vitales(),
        estadistica=Estadistica(vida=80, fuerza=40, defensa=30, velocidad=35, tipo=TipoTapo.FUEGO),
    )

    if len(sys.argv) < 2:
        menu_batalla(tapo_demo)
    elif sys.argv[1] == "host":
        flujo_host(tapo_demo)
    elif sys.argv[1] == "join":
        flujo_challenger(tapo_demo)
    else:
        print("Uso: python battle_cli.py [host|join]")
