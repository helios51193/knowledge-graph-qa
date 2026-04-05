import re
import unicodedata

from ...models import Document
from ..logger import log_stage


def normalize_text(text: str) -> str:
    """
    Normalize extracted document text for more stable chunking and extraction.

    This handles common formatting artifacts such as inconsistent whitespace,
    Windows line endings, and PDF-style broken line wraps.
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)

    # Replace single line breaks inside paragraphs while preserving paragraph gaps.
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def normalize_document_text(document: Document, text: str) -> str:
    """
    Normalize document text and emit processing-log entries for the stage.
    """
    log_stage(document, "NORMALIZATION", "Starting text normalization")

    normalized = normalize_text(text)

    log_stage(document, "NORMALIZATION", "Text normalization completed")
    return normalized
