from .chunk import Chunk


class BaseChunker:
    """
    Base interface for all chunking strategies.
    """

    def chunk(self, text: str, document_id: int) -> list[Chunk]:
        """
        Return a list of Chunk objects for the given document text.
        """
        raise NotImplementedError("Chunk method must be implemented")
