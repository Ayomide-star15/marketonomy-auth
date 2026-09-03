# app/core/storage.py
# app/core/storage.py

from supabase import create_client, Client
from app.core.config import settings

_storage_client: Client = None

BUCKET_NAME = "business-documents"


def get_storage_client() -> Client:
    """
    Uses the SERVICE ROLE key, not the regular SUPABASE_KEY. Storage
    RLS would otherwise block every operation, since our backend — not
    the end user — is the one talking to Supabase directly. Ownership
    checks already happen in business_document_service.py before this
    is ever called, so bypassing RLS here is safe: the trust boundary
    is enforced in our own code, not in Supabase's policies.
    """
    global _storage_client
    if _storage_client is None:
        _storage_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return _storage_client


def upload_file_to_storage(path: str, file_bytes: bytes, content_type: str) -> None:
    client = get_storage_client()
    client.storage.from_(BUCKET_NAME).upload(
        path,
        file_bytes,
        {"content-type": content_type},
    )


def generate_signed_download_url(path: str, expires_in: int = 300) -> str:
    client = get_storage_client()
    result = client.storage.from_(BUCKET_NAME).create_signed_url(path, expires_in)
    return result["signedURL"]


def delete_file_from_storage(path: str) -> None:
    client = get_storage_client()
    client.storage.from_(BUCKET_NAME).remove([path])