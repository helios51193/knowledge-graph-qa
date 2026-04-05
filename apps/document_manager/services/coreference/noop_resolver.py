from typing import Any

from .base import BaseCoreferenceResolver


class NoopCoreferenceResolver(BaseCoreferenceResolver):
    """
    A no-op resolver that returns the input text unchanged.
    """

    def resolve(self, text: str) -> dict[str, Any]:
        """
        Return the original text without applying any coreference changes.
        """
        return {
            "original_text": text,
            "resolved_text": text,
            "clusters": [],
        }
