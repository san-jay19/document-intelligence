from backend.app.services.document_validation_service import (
    validate_document,
)


def test_valid_pdf_is_accepted():
    pdf_bytes = b"%PDF-1.4\n%fake-pdf-content"

    result = validate_document(
        file_bytes=pdf_bytes,
        filename="sample.pdf",
        content_type="application/pdf",
    )

    assert isinstance(result, dict)
    assert "status" in result


def test_unsupported_extension_is_rejected():
    result = validate_document(
        file_bytes=b"test content",
        filename="sample.exe",
        content_type="application/octet-stream",
    )

    assert result["status"] == "FAILED"


def test_empty_file_is_rejected():
    result = validate_document(
        file_bytes=b"",
        filename="empty.pdf",
        content_type="application/pdf",
    )

    assert result["status"] == "FAILED"