import os

from .base import BaseExtractor
from .md_extractor import MarkdownExtractor
from .pdf_extractor import PdfExtractor
from .txt_extractor import TxtExtractor


def get_extractor(file_path: str) -> BaseExtractor:
    """
    Return the extractor implementation that matches the file extension.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        return TxtExtractor()

    if ext == ".md":
        return MarkdownExtractor()

    if ext == ".pdf":
        return PdfExtractor()

    raise ValueError(f"Unsupported file type: {ext}")
