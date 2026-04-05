from typing import Any

from ...models import Document
from ..chunking.chunk import Chunk
from ..logger import log_stage
from .factory import get_relation_extractor


def extract_relations(
    chunks: list[Chunk],
    entities: list[dict[str, Any]],
    llm: str,
    document: Document | None = None,
) -> list[dict[str, Any]]:
    """
    Extract relations using the configured relation extractor and optionally log the stage.
    """
    if document is not None:
        log_stage(document, "RELATION_EXTRACTION", "Starting relation extraction")

    extractor = get_relation_extractor()
    relations = extractor.extract(chunks, entities, llm)

    if document is not None:
        log_stage(document, "RELATION_EXTRACTION", f"{len(relations)} relations extracted")

    return relations
