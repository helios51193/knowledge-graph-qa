from abc import ABC, abstractmethod


class BaseCoreferenceResolver(ABC):

    @abstractmethod
    def resolve(self, text):
        """
        Returns a dict with:
        - original_text
        - resolved_text
        - clusters
        """
        raise NotImplementedError("Coreference resolver must implement resolve()")