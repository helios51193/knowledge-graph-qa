from .factory import get_extractor
from ..logger import log_stage


def extract_text(document):

    log_stage(document, "TEXT_EXTRACTION", "Starting text extraction")

    file_path = document.file.path

    extractor = get_extractor(file_path)

    text = extractor.extract(file_path)

    log_stage(document, "TEXT_EXTRACTION", "Text extraction completed")

    return text