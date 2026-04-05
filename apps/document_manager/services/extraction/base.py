class BaseExtractor:
    """
    Base interface for document text extractors.
    """

    def extract(self, file_path: str) -> str:
        """
        Extract and return raw text from a file path.
        """
        raise NotImplementedError("Extractor must implement extract()")
