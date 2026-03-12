class BaseChunker:

    def chunk(self, text, document_id):
        raise NotImplementedError("Chunk method must be implemented")