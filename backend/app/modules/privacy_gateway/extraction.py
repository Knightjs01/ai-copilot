from io import BytesIO

import docx
from docx.text.paragraph import Paragraph
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


def _is_list_paragraph(paragraph: Paragraph) -> bool:
    """A Word bullet/numbered list item has no literal bullet character in paragraph.text -- the
    glyph is drawn from list formatting, not the text run -- so plain-text extraction silently
    drops it unless detected here. Catches both a named list style (e.g. "List Bullet", applied
    via the Styles pane) and direct numbering (applied via the toolbar bullet/number button,
    which sets <w:numPr> without changing the paragraph style — the far more common real-world
    case for JDs pasted or typed straight into Word)."""

    style_name = (paragraph.style.name or "") if paragraph.style else ""
    if "List" in style_name:
        return True
    p_pr = paragraph._p.pPr
    return p_pr is not None and p_pr.numPr is not None


def _extract_docx_text(content: bytes) -> str:
    try:
        document = docx.Document(BytesIO(content))
    except Exception as exc:  # python-docx doesn't expose a narrower exception type
        raise ExtractionFailedError(f"Could not read DOCX: {exc}") from exc

    # Blank paragraphs are kept (as empty lines) rather than dropped -- they're what separates
    # one section/paragraph from the next once rendered, same as the original join-everything
    # behavior this replaces.
    lines = []
    for paragraph in document.paragraphs:
        stripped = paragraph.text.strip()
        if stripped and _is_list_paragraph(paragraph):
            lines.append(f"- {stripped}")
        else:
            lines.append(stripped)

    text = "\n".join(lines).strip()
    if not text:
        raise ExtractionFailedError("No extractable text found in this DOCX")
    return text
