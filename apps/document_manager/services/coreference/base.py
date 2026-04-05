from abc import ABC, abstractmethod
from typing import Any


class BaseCoreferenceResolver(ABC):
    """
    Base interface for coreference resolution implementations.
    """

    @abstractmethod
    def resolve(self, text: str) -> dict[str, Any]:
        """
        Resolve coreferences in text and return:

        - original_text
        - resolved_text
        - clusters
        """
        raise NotImplementedError("Coreference resolver must implement resolve()")
