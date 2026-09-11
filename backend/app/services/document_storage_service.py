import json
from datetime import datetime, timezone

from backend.app.db.database import SessionLocal
from backend.app.db.models import Document


# =========================================================
# JSON Helpers
# =========================================================

def _to_json(value):
    if value is None:
        return None

    return json.dumps(
        value,
        ensure_ascii=False,
        default=str,
    )


def _from_json(value):
    if value is None:
        return None

    try:
        return json.loads(value)

    except (TypeError, json.JSONDecodeError):
        return None


# =========================================================
# Convert Model to Dictionary
# =========================================================

def _document_to_dict(document: Document) -> dict:
    return {
        "id": document.id,
        "document_name": document.document_name,
        "document_type": document.document_type,
        "processing_status": document.processing_status,
        "file_validation": _from_json(
            document.file_validation_json
        ),
        "extracted_text": document.extracted_text,
        "extracted_data": _from_json(
            document.extracted_data_json
        ),
        "confidence": document.confidence,
        "validation": _from_json(
            document.validation_json
        ),
        "created_at": (
            document.created_at.isoformat()
            if document.created_at
            else None
        ),
        "updated_at": (
            document.updated_at.isoformat()
            if document.updated_at
            else None
        ),
    }


# =========================================================
# Store / Update Document
# =========================================================

def store_document_result(
    document_name: str,
    document_type: str,
    processing_status: str,
    file_validation: dict | None,
    extracted_text: str | None,
    extracted_data: dict | None,
    confidence: float | None,
    validation: dict | None,
) -> None:

    db = SessionLocal()

    try:
        document = (
            db.query(Document)
            .filter(
                Document.document_name
                == document_name
            )
            .first()
        )

        now = datetime.now(timezone.utc)

        if document is None:

            document = Document(
                document_name=document_name,
                document_type=document_type,
                processing_status=processing_status,
                file_validation_json=_to_json(
                    file_validation
                ),
                extracted_text=extracted_text,
                extracted_data_json=_to_json(
                    extracted_data
                ),
                confidence=confidence,
                validation_json=_to_json(
                    validation
                ),
                created_at=now,
                updated_at=now,
            )

            db.add(document)

        else:

            document.document_type = document_type

            document.processing_status = (
                processing_status
            )

            document.file_validation_json = _to_json(
                file_validation
            )

            document.extracted_text = (
                extracted_text
            )

            document.extracted_data_json = _to_json(
                extracted_data
            )

            document.confidence = confidence

            document.validation_json = _to_json(
                validation
            )

            document.updated_at = now

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# =========================================================
# Retrieve One Document
# =========================================================

def retrieve_document(
    document_name: str,
) -> dict | None:

    db = SessionLocal()

    try:
        document = (
            db.query(Document)
            .filter(
                Document.document_name
                == document_name
            )
            .first()
        )

        if document is None:
            return None

        return _document_to_dict(document)

    finally:
        db.close()


# =========================================================
# Retrieve All Documents
# =========================================================

def retrieve_all_documents() -> list[dict]:

    db = SessionLocal()

    try:
        documents = (
            db.query(Document)
            .order_by(
                Document.updated_at.desc()
            )
            .all()
        )

        return [
            _document_to_dict(document)
            for document in documents
        ]

    finally:
        db.close()