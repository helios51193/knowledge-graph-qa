from pdfminer.high_level import extract_text

from .base import BaseExtractor


class PdfExtractor(BaseExtractor):
    """
    Extract text content from PDF files using pdfminer.
    """

    def extract(self, file_path: str) -> str:
        """
        Extract and return text from a PDF file.
        """
        return extract_text(file_path)
