from .base import BaseExtractor


class TxtExtractor(BaseExtractor):
    """
    Extract text from plain text files.
    """

    def extract(self, file_path: str) -> str:
        """
        Read and return the contents of a UTF-8 text file.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
