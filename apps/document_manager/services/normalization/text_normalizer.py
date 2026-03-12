import re
import unicodedata
from ..logger import log_stage


def normalize_text(text: str) -> str:

    if not text:
        return ""

    # Normalize unicode characters
    text = unicodedata.normalize("NFKC", text)

    # Convert Windows line endings
    text = text.replace("\r\n", "\n")

    # Remove trailing spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Fix PDF broken lines (line break in middle of sentence)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Remove multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def normalize_document_text(document, text):

    log_stage(document, "NORMALIZATION", "Starting text normalization")

    normalized = normalize_text(text)

    log_stage(document, "NORMALIZATION", "Text normalization completed")

    return normalized