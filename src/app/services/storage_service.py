"""Upload/remoção de anexos no Supabase Storage."""

import uuid

import httpx

from app.config import get_settings

settings = get_settings()


class StorageError(Exception):
    pass


def _object_path(user_id: uuid.UUID, task_id: uuid.UUID, file_name: str) -> str:
    return f"{user_id}/{task_id}/{uuid.uuid4()}-{file_name}"


async def upload_attachment(
    user_id: uuid.UUID, task_id: uuid.UUID, file_name: str, content: bytes, content_type: str
) -> str:
    """Envia o arquivo ao bucket configurado e retorna a URL pública/objeto."""
    path = _object_path(user_id, task_id, file_name)
    url = f"{settings.supabase_url}/storage/v1/object/{settings.supabase_storage_bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": content_type or "application/octet-stream",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, content=content, headers=headers)
    if response.status_code >= 400:
        raise StorageError(f"Falha ao enviar anexo: {response.text}")
    return f"{settings.supabase_url}/storage/v1/object/public/{settings.supabase_storage_bucket}/{path}"


async def delete_attachment(file_url: str) -> None:
    marker = f"/object/public/{settings.supabase_storage_bucket}/"
    if marker not in file_url:
        return
    path = file_url.split(marker, 1)[1]
    url = f"{settings.supabase_url}/storage/v1/object/{settings.supabase_storage_bucket}/{path}"
    headers = {"Authorization": f"Bearer {settings.supabase_service_role_key}"}
    async with httpx.AsyncClient(timeout=30) as client:
        await client.delete(url, headers=headers)
