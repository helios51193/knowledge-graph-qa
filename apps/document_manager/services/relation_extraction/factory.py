from django.conf import settings

from .base import BaseRelationExtractor
from .heuristic_extractor import HeuristicRelationExtractor
from .llm_extractor import LlmRelationExtractor


def get_relation_extractor() -> BaseRelationExtractor:
    """
    Return the configured relation extractor implementation.
    """
    extractor_type = getattr(settings, "RELATION_EXTRACTOR", "heuristic")

    if extractor_type == "heuristic":
        return HeuristicRelationExtractor()

    if extractor_type == "llm":
        return LlmRelationExtractor()

    raise ValueError(f"Invalid relation extractor type: {extractor_type}")
