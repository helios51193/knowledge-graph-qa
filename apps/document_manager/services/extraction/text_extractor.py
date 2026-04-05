from ...models import Document
from ..logger import log_stage
from .factory import get_extractor


def extract_text(document: Document) -> str:
    """
    Extract raw text from a document file using the appropriate extractor.
    """
    log_stage(document, "TEXT_EXTRACTION", "Starting text extraction")

    file_path = document.file.path
    extractor = get_extractor(file_path)
    text = extractor.extract(file_path)

    log_stage(document, "TEXT_EXTRACTION", "Text extraction completed")
    return text
