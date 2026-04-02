class BaseChunker:

    def chunk(self, text, document_id):
        """
        Return a list of Chunk objects for the given document text.
        """
        raise NotImplementedError("Chunk method must be implemented")