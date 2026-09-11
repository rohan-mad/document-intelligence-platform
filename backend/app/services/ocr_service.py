import os
from io import BytesIO

import fitz
import pytesseract
from PIL import Image
from pytesseract import Output


# Windows Tesseract installation


if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )
else:
    pytesseract.pytesseract.tesseract_cmd = "tesseract"


def extract_page_with_ocr(image: Image.Image) -> str:
    """
    OCR a page while preserving approximate row/column layout.

    Tesseract returns coordinates for every recognized word.
    We group words belonging to the same OCR line and preserve
    their horizontal positions.
    """

    data = pytesseract.image_to_data(
        image,
        output_type=Output.DICT,
        config="--psm 4"
    )

    lines = {}

    for i in range(len(data["text"])):

        text = data["text"][i].strip()

        if not text:
            continue

        confidence = data["conf"][i]

        try:
            confidence = float(confidence)
        except (ValueError, TypeError):
            confidence = -1

        if confidence < 20:
            continue

        key = (
            data["block_num"][i],
            data["par_num"][i],
            data["line_num"][i]
        )

        x = data["left"][i]

        lines.setdefault(key, []).append(
            (x, text)
        )

    output_lines = []

    for words in lines.values():

        # Sort words left -> right
        words.sort(key=lambda item: item[0])

        row_parts = []

        previous_x = None

        for x, text in words:

            if previous_x is None:
                row_parts.append(text)
            else:
                gap = x - previous_x

                # Preserve larger horizontal gaps.
                if gap > 80:
                    row_parts.append("    ")
                elif gap > 35:
                    row_parts.append("  ")
                else:
                    row_parts.append(" ")

                row_parts.append(text)

            previous_x = x

        output_lines.append(
            "".join(row_parts)
        )

    return "\n".join(output_lines)


def extract_text_from_image(content: bytes) -> tuple[str, bool]:
    image = Image.open(BytesIO(content)).convert("RGB")

    # Upscale small images
    width, height = image.size

    if width < 1800:
        scale = 1800 / width
        image = image.resize(
            (
                int(width * scale),
                int(height * scale)
            )
        )

    # Improve image for OCR
    from PIL import ImageOps, ImageFilter

    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)
    gray = gray.filter(ImageFilter.SHARPEN)

    # Try multiple OCR layouts
    candidates = []

    for psm in [6, 11, 4]:
        text = pytesseract.image_to_string(
            gray,
            config=f"--psm {psm}"
        ).strip()

        if text:
            candidates.append(text)

    # Select the OCR result with the most text
    text = max(candidates, key=len) if candidates else ""

    return (
        f"--- PAGE 1 ---\n{text}",
        True
    )

def extract_text_from_pdf(content: bytes) -> tuple[str, bool]:

    document = fitz.open(
        stream=content,
        filetype="pdf"
    )

    pages = []
    ocr_used = False

    for page in document:

        page_number = page.number + 1

        # Try native PDF text first
        native_text = page.get_text("text").strip()

        if native_text:
            print(
                f"Page {page_number}: "
                f"{len(native_text)} characters of native text"
            )

            pages.append(
                f"--- PAGE {page_number} ---\n"
                f"{native_text}"
            )

            continue

        # Scanned/image PDF
        ocr_used = True

        print(
            f"Page {page_number}: native text unavailable; "
            f"using coordinate-aware OCR"
        )

        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(3, 3)
        )

        image_bytes = pixmap.tobytes("png")

        image = Image.open(
            BytesIO(image_bytes)
        )

        ocr_text = extract_page_with_ocr(image)

        pages.append(
            f"--- PAGE {page_number} ---\n"
            f"{ocr_text}"
        )

    document.close()

    return "\n\n".join(pages), ocr_used