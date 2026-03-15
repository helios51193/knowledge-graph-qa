from django.conf import settings

from .heuristic_extractor import HeuristicEntityExtractor
from .llm_extractor import LlmEntityExtractor


def get_entity_extractor():
    extractor_type = getattr(settings, "ENTITY_EXTRACTOR", "heuristic")

    if extractor_type == "heuristic":
        return HeuristicEntityExtractor()

    if extractor_type == "llm":
        return LlmEntityExtractor()

    raise ValueError(f"Invalid entity extractor type: {extractor_type}")