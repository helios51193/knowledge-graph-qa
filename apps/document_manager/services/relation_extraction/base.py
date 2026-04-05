from abc import ABC, abstractmethod
from typing import Any

from ..chunking.chunk import Chunk


class BaseRelationExtractor(ABC):
    """
    Base interface for relation extraction implementations.
    """

    @abstractmethod
    def extract(
        self,
        chunks: list[Chunk],
        entities: list[dict[str, Any]],
        llm: str,
    ) -> list[dict[str, Any]]:
        """
        Extract relation records from the provided chunks and entity list.
        """
        raise NotImplementedError
