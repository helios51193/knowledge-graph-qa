from django.conf import settings

from .base import BaseChunker
from .chunk import Chunk


class WordChunker(BaseChunker):
    """
    Split text into fixed-size overlapping word windows.
    """

    def chunk(self, text: str, document_id: int) -> list[Chunk]:
        words = text.split()

        chunk_size = settings.CHUNK_SIZE
        overlap = settings.CHUNK_OVERLAP
        step = max(1, chunk_size - overlap)

        chunks: list[Chunk] = []
        chunk_id = 0

        for i in range(0, len(words), step):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=chunk_text,
                    start_index=i,
                    end_index=i + len(chunk_words),
                )
            )
            chunk_id += 1

        return chunks
