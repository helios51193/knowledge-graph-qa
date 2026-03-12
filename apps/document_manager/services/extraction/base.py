class BaseExtractor:

    def extract(self, file_path):
        raise NotImplementedError("Extractor must implement extract()")