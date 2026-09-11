from io import BytesIO

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_PAGES = 3


def validate_document(
    file_bytes: bytes,
    filename: str,
    content_type: str | None = None,
) -> dict:
    """
    Validate uploaded PDF/JPG/PNG before OCR or AI processing.
    """

    # 1. Check empty file
    if not file_bytes:
        return {
            "status": "FAILED",
            "error_code": "EMPTY_FILE",
            "message": "The uploaded file is empty.",
        }

    # 2. Check file extension
    filename_lower = filename.lower()

    if "." not in filename_lower:
        return {
            "status": "FAILED",
            "error_code": "UNSUPPORTED_FILE_TYPE",
            "message": "Only PDF / JPG / PNG documents are supported.",
        }

    extension = "." + filename_lower.rsplit(".", 1)[1]

    if extension not in SUPPORTED_EXTENSIONS:
        return {
            "status": "FAILED",
            "error_code": "UNSUPPORTED_FILE_TYPE",
            "message": "Only PDF / JPG / PNG documents are supported.",
        }

    # 3. Validate PDF
    if extension == ".pdf":
        return _validate_pdf(file_bytes, filename)

    # 4. Validate image
    return _validate_image(file_bytes, filename, extension)


def _validate_pdf(file_bytes: bytes, filename: str) -> dict:
    try:
        reader = PdfReader(BytesIO(file_bytes))

        page_count = len(reader.pages)

        if page_count == 0:
            return {
                "status": "FAILED",
                "error_code": "INVALID_DOCUMENT",
                "message": "The PDF contains no pages.",
            }

        if page_count > MAX_PAGES:
            return {
                "status": "FAILED",
                "error_code": "PAGE_LIMIT_EXCEEDED",
                "message": "Documents must contain no more than 3 pages.",
                "page_count": page_count,
            }

        return {
            "file_type": "application/pdf",
            "is_supported": True,
            "is_readable": True,
            "page_count": page_count,
            "status": "PASS",
        }

    except Exception:
        return {
            "status": "FAILED",
            "error_code": "CORRUPTED_FILE",
            "message": "The PDF could not be read. It may be corrupted.",
        }


def _validate_image(
    file_bytes: bytes,
    filename: str,
    extension: str,
) -> dict:

    try:
        image = Image.open(BytesIO(file_bytes))

        # Force Pillow to actually read the image.
        image.verify()

        # Re-open because verify() invalidates the image object.
        image = Image.open(BytesIO(file_bytes))

        if extension in {".jpg", ".jpeg"}:
            file_type = "image/jpeg"
        else:
            file_type = "image/png"

        return {
            "file_type": file_type,
            "is_supported": True,
            "is_readable": True,
            "page_count": 1,
            "status": "PASS",
        }

    except (UnidentifiedImageError, OSError):
        return {
            "status": "FAILED",
            "error_code": "CORRUPTED_FILE",
            "message": "The image could not be read. It may be corrupted.",
        }