from io import BytesIO

import pytest
from docx import Document
from fpdf import FPDF

from app.modules.privacy_gateway.exceptions import ExtractionFailedError, UnsupportedFileTypeError
from app.modules.privacy_gateway.extraction import extract_text


def _build_pdf_bytes(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text=text)
    return bytes(pdf.output())


def _build_docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_extracts_text_from_pdf() -> None:
    content = _build_pdf_bytes("Experienced backend engineer resume content")
    text = extract_text(content=content, content_type="application/pdf")
    assert "Experienced backend engineer resume content" in text


def test_extracts_text_from_docx() -> None:
    content = _build_docx_bytes("Experienced backend engineer resume content")
    text = extract_text(
        content=content,
        content_type=("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    )
    assert "Experienced backend engineer resume content" in text


def test_unsupported_content_type_raises() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        extract_text(content=b"not a real file", content_type="application/msword")


def test_garbage_pdf_bytes_raise_extraction_failed() -> None:
    with pytest.raises(ExtractionFailedError):
        extract_text(content=b"this is not a valid pdf", content_type="application/pdf")
