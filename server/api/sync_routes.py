"""
server/api/sync_routes.py
Endpoints del SyncService (Handover API).

Justificación:
    Estos son los dos endpoints centrales descritos en el informe:
    
    1. POST /sync/upload — sync_upload(tapo_id, tapo_state) -> Bool
       "Recibe el Snapshot del cliente y lo guarda en el Pet State Store."
    
    2. GET /sync/resume/{usuario_id} — resume_state(usuario_id) -> JSON
       "Descarga el estado actualizado de la mascota (calculado por la
        simulación IDLE) y los posibles regalos para enviarlos de vuelta."
    
    Ambos endpoints están protegidos por JWT (dependency get_current_user)
    para cumplir con el modelo de seguridad del informe.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends

from server.api.auth_routes import get_current_user
from server.models.schemas import (
    TapoStateUpload,
    SyncUploadResponse,
    ResumeStateResponse,
)
from server.services.sync_service import (
    sync_upload as do_sync_upload,
    resume_state as do_resume_state,
    verificar_propietario,
)

router = APIRouter()


@router.post("/upload", response_model=SyncUploadResponse)
async def sync_upload(
    tapo_state: TapoStateUpload,
    current_user: dict = Depends(get_current_user),
):
    """
    sync_upload(tapo_id: ObjectID, tapo_state: JSON) -> Bool
    
    El cliente envía el estado completo de su Tapo cuando se desconecta.
    El servidor lo almacena en el Pet State Store (MongoDB).
    
    Seguridad:
    - Requiere JWT válido.
    - Verifica que el Tapo pertenece al usuario autenticado.
    """
    usuario_id = current_user["sub"]
    tapo_id = tapo_state.id_mascota

    # Verificar propiedad: solo el dueño puede subir su estado
    if not verificar_propietario(usuario_id, tapo_id):
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para modificar esta mascota."
        )

    # Convertir Pydantic model a dict para MongoDB
    state_dict = tapo_state.model_dump()

    success = do_sync_upload(tapo_id, state_dict)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Error al guardar el estado en el servidor."
        )

    return SyncUploadResponse(
        success=True,
        message=f"Estado de '{tapo_state.Nombre}' sincronizado correctamente.",
        tapo_id=tapo_id,
    )


@router.get("/resume/{usuario_id}", response_model=ResumeStateResponse)
async def resume_state(
    usuario_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    resume_state(usuario_id: ObjectID) -> JSON
    
    Descarga el estado actualizado de la mascota (post-simulación IDLE)
    y los posibles regalos/mensajes del Inbox.
    
    Seguridad:
    - Requiere JWT válido.
    - Verifica que el usuario pide su propio estado (no el de otro).
    """
    # Verificar que el usuario solicita su propio estado
    if current_user["sub"] != usuario_id:
        raise HTTPException(
            status_code=403,
            detail="No puedes acceder al estado de otro usuario."
        )

    result = do_resume_state(usuario_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No se encontró el usuario o mascota en el servidor."
        )

    return ResumeStateResponse(
        success=True,
        message="Estado recuperado correctamente.",
        tapo=result["tapo"],
        inbox=result["inbox"],
    )
