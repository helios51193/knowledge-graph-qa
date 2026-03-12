import os

from .txt_extractor import TxtExtractor
from .md_extractor import MarkdownExtractor
from .pdf_extractor import PdfExtractor


def get_extractor(file_path):

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        return TxtExtractor()

    if ext == ".md":
        return MarkdownExtractor()

    if ext == ".pdf":
        return PdfExtractor()

    raise ValueError(f"Unsupported file type: {ext}")