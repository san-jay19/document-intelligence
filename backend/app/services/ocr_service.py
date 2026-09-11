from io import BytesIO
import os
import shutil

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from pypdf import PdfReader


# =========================================================
# OCR Configuration
# =========================================================

# Tesseract:
# 1. Use TESSERACT_CMD if explicitly configured.
# 2. Otherwise use the Windows installation when present.
# 3. Otherwise find tesseract from PATH (Linux/hosted).
TESSERACT_CMD = os.getenv("TESSERACT_CMD")

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

elif os.name == "nt":

    windows_tesseract = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    if os.path.exists(windows_tesseract):
        pytesseract.pytesseract.tesseract_cmd = (
            windows_tesseract
        )

else:

    linux_tesseract = shutil.which("tesseract")

    if linux_tesseract:
        pytesseract.pytesseract.tesseract_cmd = (
            linux_tesseract
        )


# Poppler:
# On Windows, use the existing local installation.
# On Linux, leave this as None so pdf2image uses Poppler
# available in the system PATH.
POPPLER_PATH = os.getenv("POPPLER_PATH")

if not POPPLER_PATH and os.name == "nt":

    windows_poppler = (
        r"C:\Users\Sanjay\Downloads"
        r"\Release-26.07.0-0"
        r"\poppler-26.07.0"
        r"\Library\bin"
    )

    if os.path.exists(windows_poppler):
        POPPLER_PATH = windows_poppler


# =========================================================
# Image OCR
# =========================================================

def extract_text_from_image(
    file_bytes: bytes,
) -> str:
    """
    Extract text from a JPG or PNG image using Tesseract.
    """

    image = Image.open(
        BytesIO(file_bytes)
    )

    # Convert image to RGB to avoid issues with
    # some PNG/image modes.
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    text = pytesseract.image_to_string(
        image
    )

    return text.strip()


# =========================================================
# PDF OCR / Native Text Extraction
# =========================================================

def extract_text_from_pdf(
    file_bytes: bytes,
) -> str:
    """
    Extract text from a PDF.

    First tries native/selectable PDF text extraction.

    If no meaningful text is found, falls back to
    image-based OCR.
    """

    native_text = _extract_native_pdf_text(
        file_bytes
    )

    # If the PDF already contains meaningful text,
    # use it instead of OCR.
    if native_text.strip():
        return native_text.strip()

    # Otherwise treat it as a scanned PDF.
    return _ocr_scanned_pdf(
        file_bytes
    )


# =========================================================
# Native PDF Text Extraction
# =========================================================

def _extract_native_pdf_text(
    file_bytes: bytes,
) -> str:
    """
    Extract embedded/selectable text from a PDF.
    """

    try:

        reader = PdfReader(
            BytesIO(file_bytes)
        )

        pages_text = []

        for page in reader.pages:

            text = page.extract_text() or ""

            if text.strip():

                pages_text.append(
                    text.strip()
                )

        return "\n".join(
            pages_text
        )

    except Exception:
        return ""


# =========================================================
# Scanned PDF OCR
# =========================================================

def _ocr_scanned_pdf(
    file_bytes: bytes,
) -> str:
    """
    Convert scanned PDF pages to images and
    run Tesseract OCR.
    """

    convert_kwargs = {
        "pdf_file": file_bytes,
        "dpi": 300,
    }

    # On Windows, provide the explicit Poppler path.
    # On Linux/hosted environments, POPPLER_PATH remains
    # None and pdf2image uses Poppler from PATH.
    if POPPLER_PATH:

        convert_kwargs["poppler_path"] = (
            POPPLER_PATH
        )

    images = convert_from_bytes(
        **convert_kwargs
    )

    pages_text = []

    for page_number, image in enumerate(
        images,
        start=1,
    ):

        text = pytesseract.image_to_string(
            image
        )

        if text.strip():

            pages_text.append(
                f"--- Page {page_number} ---\n"
                f"{text.strip()}"
            )

    return "\n\n".join(
        pages_text
    )