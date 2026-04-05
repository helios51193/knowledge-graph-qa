from abc import ABC, abstractmethod
from typing import Any

from ..chunking.chunk import Chunk


class BaseEntityExtractor(ABC):
    """
    Base interface for entity extraction implementations.
    """

    @abstractmethod
    def extract(
        self,
        chunks: list[Chunk],
        llm: str,
    ) -> list[dict[str, Any]]:
        """
        Extract entity records from the provided chunks.
        """
        raise NotImplementedError
