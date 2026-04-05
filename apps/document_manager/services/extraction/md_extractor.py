from .base import BaseExtractor


class MarkdownExtractor(BaseExtractor):
    """
    Extract text from Markdown files without additional rendering.
    """

    def extract(self, file_path: str) -> str:
        """
        Read and return the raw contents of a UTF-8 Markdown file.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
