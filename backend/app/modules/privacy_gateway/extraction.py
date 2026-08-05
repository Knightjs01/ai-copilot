from io import BytesIO

import docx
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.modules.privacy_gateway.exceptions import ExtractionFailedError, UnsupportedFileTypeError

_PDF_CONTENT_TYPE = "application/pdf"
_DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

# Legacy binary .doc (application/msword) is deliberately not supported — there's no reliable
# pure-Python extractor for it without a heavy external dependency (e.g. LibreOffice
# conversion), which isn't a reasonable addition just to support a legacy format.
SUPPORTED_CONTENT_TYPES = {_PDF_CONTENT_TYPE, _DOCX_CONTENT_TYPE}


def extract_text(*, content: bytes, content_type: str) -> str:
    if content_type == _PDF_CONTENT_TYPE:
        return _extract_pdf_text(content)
    if content_type == _DOCX_CONTENT_TYPE:
        return _extract_docx_text(content)
    raise UnsupportedFileTypeError(
        f"Cannot extract text from content type {content_type!r} — only PDF and DOCX are supported"
    )


def _extract_pdf_text(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content))
        pages_text = [page.extract_text() or "" for page in reader.pages]
    except PdfReadError as exc:
        raise ExtractionFailedError(f"Could not read PDF: {exc}") from exc

    text = "\n".join(pages_text).strip()
    if not text:
        raise ExtractionFailedError("No extractable text found in this PDF")
    return text


def _extract_docx_text(content: bytes) -> str:
    try:
        document = docx.Document(BytesIO(content))
    except Exception as exc:  # python-docx doesn't expose a narrower exception type
        raise ExtractionFailedError(f"Could not read DOCX: {exc}") from exc

    text = "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    if not text:
        raise ExtractionFailedError("No extractable text found in this DOCX")
    return text
