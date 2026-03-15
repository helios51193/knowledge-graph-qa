from .factory import get_entity_extractor
from ..logger import log_stage


def extract_entities(chunks, llm, document=None):
    if document is not None:
        log_stage(document, "ENTITY_EXTRACTION", "Starting entity extraction")

    extractor = get_entity_extractor()
    entities = extractor.extract(chunks, llm)

    if document is not None:
        log_stage(document, "ENTITY_EXTRACTION", f"{len(entities)} entities extracted")

    return entities