from pdfminer.high_level import extract_text
from .base import BaseExtractor


class PdfExtractor(BaseExtractor):

    def extract(self, file_path):

        text = extract_text(file_path)

        return text