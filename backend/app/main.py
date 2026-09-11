from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from backend.app.db.database import init_db

from backend.app.services.document_validation_service import (
    validate_document,
)

from backend.app.services.ocr_service import (
    extract_text_from_image,
    extract_text_from_pdf,
)

from backend.app.services.extraction_service import (
    calculate_average_confidence,
    extract_document_data,
)

from backend.app.services.validation_router import (
    validate_document_financials,
)

from backend.app.services.document_storage_service import (
    store_document_result,
    retrieve_document,
    retrieve_all_documents,
)


# =========================================================
# FastAPI Application
# =========================================================

app = FastAPI(
    title="Document Intelligence API",
    description=(
        "AI-powered financial document extraction, "
        "validation, and processing API."
    ),
    version="1.0.0",
)


# =========================================================
# Database Startup
# =========================================================

@app.on_event("startup")
async def startup_event():
    """
    Initialize database tables when FastAPI starts.
    """

    try:
        init_db()

    except Exception as exc:
        raise RuntimeError(
            f"Database initialization failed: {exc}"
        )


# =========================================================
# Supported Document Types
# =========================================================

SUPPORTED_DOCUMENT_TYPES = {
    "invoice",
    "balance_sheet",
    "profit_and_loss",
    "cash_flow_statement",
}


# =========================================================
# Root
# =========================================================

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "document-intelligence",
        "version": "1.0.0",
    }


# =========================================================
# Health
# =========================================================

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "ok",
        "service": "document-intelligence",
    }


# =========================================================
# Process Document
# =========================================================

@app.post("/api/v1/documents/process")
async def process_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
):
    """
    Complete document intelligence pipeline.

    Upload
        ↓
    File Validation
        ↓
    OCR / Native Text Extraction
        ↓
    AI Field + Table Extraction
        ↓
    Confidence / Evidence
        ↓
    Financial Validation Router
        ↓
    Database Persistence
        ↓
    JSON Response
    """

    # =====================================================
    # 1. Basic Input Validation
    # =====================================================

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MISSING_FILENAME",
                "message": (
                    "Uploaded file must have a filename."
                ),
            },
        )

    document_type = (
        document_type
        .strip()
        .lower()
    )

    if document_type not in SUPPORTED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "UNSUPPORTED_DOCUMENT_TYPE",
                "message": (
                    "document_type must be one of: "
                    "invoice, balance_sheet, "
                    "profit_and_loss, "
                    "cash_flow_statement"
                ),
            },
        )

    # =====================================================
    # 2. Read Uploaded File
    # =====================================================

    try:
        file_bytes = await file.read()

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FILE_READ_ERROR",
                "message": (
                    f"Could not read uploaded file: {exc}"
                ),
            },
        )

    # =====================================================
    # 3. File Validation
    # =====================================================

    try:
        file_validation = validate_document(
            file_bytes=file_bytes,
            filename=file.filename,
            content_type=file.content_type,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "FILE_VALIDATION_ERROR",
                "message": (
                    "Unexpected file validation error."
                ),
                "details": str(exc),
            },
        )

    # =====================================================
    # 4. Stop When File Validation Fails
    # =====================================================

    if file_validation.get("status") == "FAILED":

        validation_result = {
            "overall_status": "NOT_APPLICABLE",
            "checks": [],
            "errors": [],
            "warnings": [],
            "summary": {
                "periods_checked": 0,
                "passed_checks": 0,
                "failed_checks": 0,
                "not_applicable_checks": 0,
            },
        }

        result = {
            "document_name": file.filename,
            "document_type": document_type,
            "processing_status": "FAILED",
            "file_validation": file_validation,
            "extracted_text": None,
            "extracted_data": None,
            "confidence": None,
            "validation": validation_result,
        }

        # -----------------------------------------------
        # Persist failed document
        # -----------------------------------------------

        try:
            store_document_result(
                document_name=file.filename,
                document_type=document_type,
                processing_status="FAILED",
                file_validation=file_validation,
                extracted_text=None,
                extracted_data=None,
                confidence=None,
                validation=validation_result,
            )

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "DATABASE_STORAGE_ERROR",
                    "message": (
                        "File validation failed and the "
                        "failure result could not be stored."
                    ),
                    "details": str(exc),
                },
            )

        return result

    # =====================================================
    # 5. OCR / Text Extraction
    # =====================================================

    filename_lower = file.filename.lower()

    try:

        if filename_lower.endswith(
            (".jpg", ".jpeg", ".png")
        ):

            extracted_text = (
                extract_text_from_image(
                    file_bytes
                )
            )

        elif filename_lower.endswith(".pdf"):

            extracted_text = (
                extract_text_from_pdf(
                    file_bytes
                )
            )

        else:

            raise HTTPException(
                status_code=400,
                detail={
                    "code": "UNSUPPORTED_FILE_TYPE",
                    "message": (
                        "Only PDF / JPG / PNG "
                        "documents are supported."
                    ),
                },
            )

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "code": "OCR_ERROR",
                "message": (
                    "Text extraction/OCR failed."
                ),
                "details": str(exc),
            },
        )

    # =====================================================
    # 6. OCR Result Validation
    # =====================================================

    if (
        not extracted_text
        or not extracted_text.strip()
    ):

        validation_result = {
            "overall_status": "NOT_APPLICABLE",
            "checks": [],
            "errors": [
                "No readable text could be extracted."
            ],
            "warnings": [],
            "summary": {
                "periods_checked": 0,
                "passed_checks": 0,
                "failed_checks": 0,
                "not_applicable_checks": 0,
            },
        }

        result = {
            "document_name": file.filename,
            "document_type": document_type,
            "processing_status": "FAILED",
            "file_validation": file_validation,
            "extracted_text": "",
            "extracted_data": None,
            "confidence": None,
            "validation": validation_result,
        }

        # -----------------------------------------------
        # Persist OCR failure
        # -----------------------------------------------

        try:
            store_document_result(
                document_name=file.filename,
                document_type=document_type,
                processing_status="FAILED",
                file_validation=file_validation,
                extracted_text="",
                extracted_data=None,
                confidence=None,
                validation=validation_result,
            )

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "DATABASE_STORAGE_ERROR",
                    "message": (
                        "OCR failed and the failure "
                        "result could not be stored."
                    ),
                    "details": str(exc),
                },
            )

        return result

    extracted_text = extracted_text.strip()

    # =====================================================
    # 7. AI Extraction
    # =====================================================

    try:

        extracted_data = extract_document_data(
            document_text=extracted_text,
            document_type=document_type,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail={
                "code": "AI_EXTRACTION_ERROR",
                "message": (
                    "AI field/table extraction failed."
                ),
                "details": str(exc),
            },
        )

    # =====================================================
    # 8. Confidence
    # =====================================================

    try:

        overall_confidence = (
            calculate_average_confidence(
                extracted_data
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "code": "CONFIDENCE_CALCULATION_ERROR",
                "message": (
                    "Could not calculate extraction confidence."
                ),
                "details": str(exc),
            },
        )

    # =====================================================
    # 9. Check Requested vs AI Document Type
    # =====================================================

    ai_document_type = (
        extracted_data.document_type
        .strip()
        .lower()
    )

    document_type_warning = None

    if ai_document_type != document_type:

        document_type_warning = (
            f"Requested document type "
            f"'{document_type}' but AI returned "
            f"'{ai_document_type}'."
        )

    # =====================================================
    # 10. Financial Validation
    # =====================================================

    try:

        validation_result = (
            validate_document_financials(
                extraction=extracted_data,
                document_type=document_type,
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "code": "FINANCIAL_VALIDATION_ERROR",
                "message": (
                    "Financial validation failed."
                ),
                "details": str(exc),
            },
        )

    # =====================================================
    # 11. Add Document Type Warning
    # =====================================================

    if document_type_warning:

        validation_result.setdefault(
            "warnings",
            [],
        )

        validation_result["warnings"].append(
            document_type_warning
        )

    # =====================================================
    # 12. Processing Status
    # =====================================================

    validation_status = (
        validation_result.get(
            "overall_status"
        )
    )

    if validation_status == "FAIL":

        processing_status = "FAILED"

    elif validation_status == "WARNING":

        processing_status = "PASS"

    elif validation_status == "NOT_APPLICABLE":

        processing_status = "PASS"

    else:

        processing_status = "PASS"

    # =====================================================
    # 13. Serialize Extracted Data
    # =====================================================

    extracted_data_json = {
        "ai_document_type": (
            extracted_data.document_type
        ),

        "fields": [
            field.model_dump()
            for field in extracted_data.fields
        ],

        "tables": [
            table.model_dump()
            for table in extracted_data.tables
        ],
    }

    # =====================================================
    # 14. Final API Response
    # =====================================================

    result = {
        "document_name": file.filename,

        "document_type": document_type,

        "processing_status": processing_status,

        "file_validation": file_validation,

        "extracted_text": extracted_text,

        "extracted_data": extracted_data_json,

        "confidence": overall_confidence,

        "validation": validation_result,
    }

    # =====================================================
    # 15. Persist Successful / Failed Processing Result
    # =====================================================

    try:

        store_document_result(
            document_name=file.filename,
            document_type=document_type,
            processing_status=processing_status,
            file_validation=file_validation,
            extracted_text=extracted_text,
            extracted_data=extracted_data_json,
            confidence=overall_confidence,
            validation=validation_result,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "code": "DATABASE_STORAGE_ERROR",
                "message": (
                    "Document processing completed, "
                    "but the result could not be stored."
                ),
                "details": str(exc),
            },
        )

    # =====================================================
    # 16. Return Final Result
    # =====================================================

    return result


# =========================================================
# Get One Document
# =========================================================

@app.get(
    "/api/v1/documents/{document_name}"
)
async def get_document_by_name(
    document_name: str,
):
    """
    Retrieve a previously processed document
    by its filename.
    """

    try:

        document = retrieve_document(
            document_name
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "code": "DATABASE_READ_ERROR",
                "message": (
                    "Could not retrieve the document."
                ),
                "details": str(exc),
            },
        )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": (
                    f"Document '{document_name}' "
                    "was not found."
                ),
            },
        )

    return document


# =========================================================
# List Documents
# =========================================================

@app.get(
    "/api/v1/documents"
)
async def get_documents():
    """
    Retrieve all processed documents.
    """

    try:

        documents = retrieve_all_documents()

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "code": "DATABASE_READ_ERROR",
                "message": (
                    "Could not retrieve documents."
                ),
                "details": str(exc),
            },
        )

    return {
        "count": len(documents),
        "documents": documents,
    }