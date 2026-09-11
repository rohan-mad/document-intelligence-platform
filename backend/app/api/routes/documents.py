import json
from datetime import datetime

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Form,
    Depends
)

from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.document import Document

from backend.app.services.document_validation_service import (
    validate_document
)

from backend.app.services.ocr_service import (
    extract_text_from_pdf,
    extract_text_from_image
)

from backend.app.services.extraction_service import (
    extract_document_data
)

from backend.app.services.financial_validation_service import (
    validate_financial_document
)


router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"]
)


@router.post("/process")
def process_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db)
):

    start_time = datetime.utcnow()

    # -------------------------------------------------
    # 1. Validate document type
    # -------------------------------------------------

    allowed_document_types = {
        "invoice",
        "balance_sheet",
        "profit_and_loss",
        "cash_flow_statement"
    }

    if document_type not in allowed_document_types:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_DOCUMENT_TYPE",
                "message": (
                    "document_type must be one of: "
                    "invoice, balance_sheet, "
                    "profit_and_loss, cash_flow_statement"
                )
            }
        )

    # -------------------------------------------------
    # 2. Validate uploaded file
    # -------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FILE",
                "message": "No file was provided."
            }
        )

    content = file.file.read()

    validation = validate_document(
        filename=file.filename,
        content=content,
        content_type=file.content_type
    )

    if validation["status"] == "FAILED":
        raise HTTPException(
            status_code=400,
            detail={
                "code": validation["error_code"],
                "message": validation["message"]
            }
        )

    # -------------------------------------------------
    # 3. Extract text / OCR
    # -------------------------------------------------

    extracted_text = ""
    ocr_used = False

    try:

        if file.filename.lower().endswith(".pdf"):

            extracted_text, ocr_used = extract_text_from_pdf(
                content
            )
        elif file.filename.lower().endswith(
    (".jpg", ".jpeg", ".png")
):

            
            extracted_text, ocr_used = extract_text_from_image(
        content
    )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=422,
            detail={
                "code": "OCR_UNAVAILABLE",
                "message": str(exc)
            }
        )

    # -------------------------------------------------
    # 4. AI structured extraction
    # -------------------------------------------------

    try:

        extracted_data = extract_document_data(
            document_text=extracted_text,
            document_type=document_type
        )

    except Exception as exc:

        print(f"AI extraction error: {exc}")

        raise HTTPException(
            status_code=502,
            detail={
                "code": "AI_EXTRACTION_FAILED",
                "message": "The AI extraction service failed."
            }
        )

    extracted_data_dict = extracted_data.model_dump()

    # -------------------------------------------------
    # 5. Financial validation
    # -------------------------------------------------

    validation_result = validate_financial_document(
    data=extracted_data_dict,
    document_type=document_type
)

    # -------------------------------------------------
    # 6. Determine processing status
    # -------------------------------------------------

    processing_status = "PASS"

    if validation_result["overall_status"] == "FAIL":
        processing_status = "FAILED"

    # -------------------------------------------------
    # 7. Build final result
    # -------------------------------------------------

    processed_at = datetime.utcnow()

    processing_time_ms = int(
        (processed_at - start_time).total_seconds() * 1000
    )

    result = {
        "document_name": file.filename,
        "document_type": document_type,
        "processing_status": processing_status,

        "file_validation": {
            "file_type": file.content_type,
            "is_supported": validation["is_supported"],
            "is_readable": validation["is_readable"],
            "page_count": validation["page_count"],
            "status": validation["status"]
        },

        "extracted_data": extracted_data_dict,

        "validation": validation_result,

        "processing_metadata": {
            "ocr_used": ocr_used,
            "processed_at": processed_at.isoformat(),
            "processing_time_ms": processing_time_ms
        }
    }

    # -------------------------------------------------
    # 8. Save result to database
    # -------------------------------------------------

    existing_document = (
        db.query(Document)
        .filter(
            Document.document_name == file.filename
        )
        .first()
    )

    if existing_document:

        existing_document.document_type = document_type
        existing_document.processing_status = processing_status
        existing_document.result_json = json.dumps(
            result
        )
        existing_document.ocr_used = str(
            ocr_used
        )
        existing_document.processed_at = processed_at

    else:

        new_document = Document(
            document_name=file.filename,
            document_type=document_type,
            processing_status=processing_status,
            result_json=json.dumps(result),
            ocr_used=str(ocr_used),
            processed_at=processed_at
        )

        db.add(new_document)

    db.commit()

    return result
# -------------------------------------------------
# Get all processed documents
# -------------------------------------------------

@router.get("")
def get_documents(
    db: Session = Depends(get_db)
):
    documents = (
        db.query(Document)
        .order_by(Document.processed_at.desc())
        .all()
    )

    return [
        {
            "document_name": document.document_name,
            "document_type": document.document_type,
            "processing_status": document.processing_status,
            "processed_at": (
                document.processed_at.isoformat()
                if document.processed_at
                else None
            )
        }
        for document in documents
    ]


# -------------------------------------------------
# Get one document by name
# -------------------------------------------------

@router.get("/{document_name}")
def get_document(
    document_name: str,
    db: Session = Depends(get_db)
):
    document = (
        db.query(Document)
        .filter(
            Document.document_name == document_name
        )
        .order_by(Document.processed_at.desc())
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": (
                    f"Document '{document_name}' "
                    "was not found."
                )
            }
        )

    return json.loads(document.result_json)