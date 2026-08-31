# app/services/business_document_service.py

from sqlalchemy.orm import Session as DBSession
from fastapi import UploadFile
import uuid

from app.models.business_document import BusinessDocument, DocumentTypeEnum, DocumentStatusEnum
from app.models.business_profile import BusinessProfile
from app.models.business_bank_details import BusinessBankDetails
from app.core.storage import upload_file_to_storage, generate_signed_download_url, delete_file_from_storage

ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def get_business_profile_for_user(db: DBSession, user_id) -> BusinessProfile:
    profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == user_id).first()
    if not profile:
        raise ValueError("You must create a business profile before uploading documents")
    return profile


def upload_business_document(
    db: DBSession,
    user_id,
    document_type: str,
    file: UploadFile,
    expiry_date=None,
) -> BusinessDocument:
    profile = get_business_profile_for_user(db, user_id)

    if document_type not in [t.value for t in DocumentTypeEnum]:
        raise ValueError(f"Invalid document_type: {document_type}")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("Only PDF, JPG, and PNG files are allowed")

    file_bytes = file.file.read()
    file_size = len(file_bytes)

    if file_size == 0:
        raise ValueError("Uploaded file is empty")
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError("File is too large — maximum size is 10MB")

    file_extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
    storage_path = f"{profile.id}/{uuid.uuid4()}.{file_extension}"

    upload_file_to_storage(storage_path, file_bytes, file.content_type)

    document = BusinessDocument(
        business_profile_id=profile.id,
        document_type=document_type,
        document_name=file.filename,
        document_url=storage_path,
        expiry_date=expiry_date,
        file_size=file_size,
        status=DocumentStatusEnum.pending.value,   # every new upload starts pending — admin reviews it later
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_my_documents(db: DBSession, user_id) -> list[BusinessDocument]:
    profile = get_business_profile_for_user(db, user_id)
    return (
        db.query(BusinessDocument)
        .filter(BusinessDocument.business_profile_id == profile.id)
        .order_by(BusinessDocument.uploaded_at.desc())
        .all()
    )


def get_document_download_url(db: DBSession, user_id, document_id: str, expires_in: int = 300) -> str:
    profile = get_business_profile_for_user(db, user_id)

    document = (
        db.query(BusinessDocument)
        .filter(BusinessDocument.id == document_id)
        .filter(BusinessDocument.business_profile_id == profile.id)
        .first()
    )
    if not document:
        raise ValueError("Document not found")

    return generate_signed_download_url(document.document_url, expires_in)


def delete_document(db: DBSession, user_id, document_id: str) -> bool:
    profile = get_business_profile_for_user(db, user_id)

    document = (
        db.query(BusinessDocument)
        .filter(BusinessDocument.id == document_id)
        .filter(BusinessDocument.business_profile_id == profile.id)
        .first()
    )
    if not document:
        raise ValueError("Document not found")

    delete_file_from_storage(document.document_url)
    db.delete(document)
    db.commit()
    return True


def get_required_documents_status(db: DBSession, business_profile_id) -> dict:
    """
    Powers the '0/5 uploaded' indicator. A document only counts as
    'completed' once it's actually been UPLOADED — status pending/
    verified/rejected doesn't affect this count, since submit_for_review
    only needs documents to EXIST, not to already be verified (that's
    admin's job during review, which happens after submission).
    """
    uploaded_file_types = {
        doc.document_type
        for doc in db.query(BusinessDocument)
        .filter(BusinessDocument.business_profile_id == business_profile_id)
        .all()
    }

    bank_details_record = (
        db.query(BusinessBankDetails)
        .filter(BusinessBankDetails.business_profile_id == business_profile_id)
        .first()
    )

    missing = []
    for doc_type in [
        DocumentTypeEnum.business_registration.value,
        DocumentTypeEnum.tax_identification.value,
        DocumentTypeEnum.owner_id.value,
    ]:
        if doc_type not in uploaded_file_types:
            missing.append(doc_type)

    if not bank_details_record:
        missing.append("bank_details")

    nin_number_exists = bank_details_record is not None and bank_details_record.nin_number is not None
    nin_photo_exists = DocumentTypeEnum.nin_document.value in uploaded_file_types

    if not (nin_number_exists and nin_photo_exists):
        missing.append("nin_document")

    total_required = 5
    completed = total_required - len(missing)

    return {"total_required": total_required, "completed": completed, "missing": missing}


def has_required_documents(db: DBSession, business_profile_id) -> bool:
    status = get_required_documents_status(db, business_profile_id)
    return status["completed"] == status["total_required"]


# ===== ADMIN — review a SPECIFIC document =====

def verify_document(db: DBSession, document_id: str) -> BusinessDocument:
    """Admin-only. Marks one document as verified."""
    document = db.query(BusinessDocument).filter(BusinessDocument.id == document_id).first()
    if not document:
        raise ValueError("Document not found")

    document.status = DocumentStatusEnum.verified.value
    document.rejection_reason = None
    db.commit()
    db.refresh(document)
    return document


def reject_document(db: DBSession, document_id: str, reason: str) -> BusinessDocument:
    """Admin-only. Rejects one document with a reason — business owner sees it and re-uploads."""
    document = db.query(BusinessDocument).filter(BusinessDocument.id == document_id).first()
    if not document:
        raise ValueError("Document not found")

    if not reason or not reason.strip():
        raise ValueError("A reason is required when rejecting a document")

    document.status = DocumentStatusEnum.rejected.value
    document.rejection_reason = reason
    db.commit()
    db.refresh(document)
    return document