# app/core/storage.py
#
# Thin wrapper around the supabase-py Storage client. Kept separate from
# business_document_service.py so any future feature needing file
# storage (portfolio images, business logos) reuses this instead of
# each service reimplementing its own client setup.

from supabase import create_client, Client
from app.core.config import settings

_supabase_client: Client = None

BUCKET_NAME = "business-documents"   # private bucket — created via migration,
                                       # 10MB limit + PDF/JPG/PNG enforced at the storage layer


def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase_client


def upload_file_to_storage(path: str, file_bytes: bytes, content_type: str) -> None:
    """Uploads raw bytes to the private bucket at the given path."""
    client = get_supabase_client()
    client.storage.from_(BUCKET_NAME).upload(
        path,
        file_bytes,
        {"content-type": content_type},
    )


def generate_signed_download_url(path: str, expires_in: int = 300) -> str:
    """
    Generates a short-lived signed URL (default 5 min) so a private file
    can be viewed without the bucket ever being public.
    """
    client = get_supabase_client()
    result = client.storage.from_(BUCKET_NAME).create_signed_url(path, expires_in)
    return result["signedURL"]


def delete_file_from_storage(path: str) -> None:
    client = get_supabase_client()
    client.storage.from_(BUCKET_NAME).remove([path])