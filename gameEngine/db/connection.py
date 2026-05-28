"""
db/connection.py
Gestiona la conexión única a MongoDB usando pymongo.
Lee la configuración desde el archivo .env (o variables de entorno del sistema).
"""
from __future__ import annotations
import os
from pathlib import Path
 
# Intentar cargar .env si existe (requiere: pip install python-dotenv)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # Si no está instalado, usa las variables de entorno del sistema
 
try:
    from pymongo import MongoClient
    from pymongo.database import Database
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
except ImportError:
    raise ImportError(
        "pymongo no está instalado.\n"
        "Instálalo con:  pip install pymongo python-dotenv"
    )
 
 
# ------------------------------------------------------------------ #
#  Configuración
# ------------------------------------------------------------------ #
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB",  "Tapomon")
 
 
# ------------------------------------------------------------------ #
#  Singleton de conexión
# ------------------------------------------------------------------ #
_client:   MongoClient | None = None
_database: Database | None    = None
 
 
def get_db() -> Database:
    """Retorna la instancia de la base de datos (singleton)."""
    global _client, _database
 
    if _database is not None:
        return _database
 
    try:
        _client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,  # timeout de 5 s al conectar
        )
        # Verificar que la conexión funciona
        _client.admin.command("ping")
        # Evitar choque por mayusculas/minusculas en el nombre de la DB
        # (MongoDB trata nombres con distinto case como distintos, pero no
        # permite crear uno nuevo si ya existe otro con case diferente).
        db_name = MONGO_DB
        try:
            existing = _client.list_database_names()
            for name in existing:
                if name.lower() == db_name.lower():
                    db_name = name
                    break
        except Exception:
            pass

        _database = _client[db_name]
        try:
            print(f"✅  Conectado a MongoDB: {MONGO_URI} / base: {MONGO_DB}")
        except UnicodeEncodeError:
            print(f"[OK] Conectado a MongoDB: {MONGO_URI} / base: {MONGO_DB}")
        return _database
 
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        raise ConnectionError(
            f"❌  No se pudo conectar a MongoDB en '{MONGO_URI}'.\n"
            f"    Verifica que el servidor esté corriendo y que MONGO_URI sea correcto.\n"
            f"    Detalle: {e}"
        )
 
 
def cerrar_conexion() -> None:
    """Cierra la conexión con MongoDB (llamar al salir de la app)."""
    global _client, _database
    if _client:
        _client.close()
        _client   = None
        _database = None