from .factory import get_relation_extractor
from ..logger import log_stage

def extract_relations(chunks, entities, llm, document=None):
    if document is not None:
        log_stage(document, "RELATION_EXTRACTION", "Starting relation extraction")

    extractor = get_relation_extractor()
    relations = extractor.extract(chunks, entities, llm)

    if document is not None:
        log_stage(document, "RELATION_EXTRACTION", f"{len(relations)} relations extracted")

    return relations