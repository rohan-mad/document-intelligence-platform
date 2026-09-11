from io import BytesIO

import fitz  # PyMuPDF
from PIL import Image


MAX_PAGES = 3
SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def validate_document(
    filename: str,
    content: bytes,
    content_type: str | None = None
) -> dict:

    if not filename:
        return {
            "is_supported": False,
            "is_readable": False,
            "page_count": None,
            "status": "FAILED",
            "error_code": "INVALID_FILE",
            "message": "No file was provided."
        }

    lower_name = filename.lower()

    extension = None
    for ext in SUPPORTED_EXTENSIONS:
        if lower_name.endswith(ext):
            extension = ext
            break

    if extension is None:
        return {
            "is_supported": False,
            "is_readable": False,
            "page_count": None,
            "status": "FAILED",
            "error_code": "UNSUPPORTED_FILE_TYPE",
            "message": "Only PDF / JPG / PNG documents are supported."
        }

    if not content:
        return {
            "is_supported": True,
            "is_readable": False,
            "page_count": None,
            "status": "FAILED",
            "error_code": "EMPTY_FILE",
            "message": "The uploaded file is empty."
        }

    # PDF validation
    if extension == ".pdf":
        try:
            document = fitz.open(stream=content, filetype="pdf")

            page_count = document.page_count

            if page_count == 0:
                document.close()
                return {
                    "is_supported": True,
                    "is_readable": False,
                    "page_count": 0,
                    "status": "FAILED",
                    "error_code": "EMPTY_PDF",
                    "message": "The PDF contains no pages."
                }

            if page_count > MAX_PAGES:
                document.close()
                return {
                    "is_supported": True,
                    "is_readable": True,
                    "page_count": page_count,
                    "status": "FAILED",
                    "error_code": "PAGE_LIMIT_EXCEEDED",
                    "message": "Documents must contain no more than 3 pages."
                }

            document.close()

            return {
                "is_supported": True,
                "is_readable": True,
                "page_count": page_count,
                "status": "PASS"
            }

        except Exception:
            return {
                "is_supported": True,
                "is_readable": False,
                "page_count": None,
                "status": "FAILED",
                "error_code": "CORRUPTED_FILE",
                "message": "The PDF could not be read."
            }

    # Image validation
    try:
        image = Image.open(BytesIO(content))
        image.verify()

        return {
            "is_supported": True,
            "is_readable": True,
            "page_count": 1,
            "status": "PASS"
        }

    except Exception:
        return {
            "is_supported": True,
            "is_readable": False,
            "page_count": None,
            "status": "FAILED",
            "error_code": "CORRUPTED_FILE",
            "message": "The image could not be read."
        }