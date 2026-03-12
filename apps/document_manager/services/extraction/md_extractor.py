from .base import BaseExtractor


class MarkdownExtractor(BaseExtractor):

    def extract(self, file_path):

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
        s