from typing import Any

from ...models import Document
from ..chunking.chunk import Chunk
from ..logger import log_stage
from .factory import get_entity_extractor


def extract_entities(
    chunks: list[Chunk],
    llm: str,
    document: Document | None = None,
) -> list[dict[str, Any]]:
    """
    Extract entities using the configured extractor and optionally log the stage.
    """
    if document is not None:
        log_stage(document, "ENTITY_EXTRACTION", "Starting entity extraction")

    extractor = get_entity_extractor()
    entities = extractor.extract(chunks, llm)

    if document is not None:
        log_stage(document, "ENTITY_EXTRACTION", f"{len(entities)} entities extracted")

    return entities
