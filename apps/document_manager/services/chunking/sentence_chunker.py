import re

from .base import BaseChunker
from .chunk import Chunk


class SentenceChunker(BaseChunker):
    """
    Split text into sentence-level chunks.
    """

    def chunk(self, text: str, document_id: int) -> list[Chunk]:
        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks: list[Chunk] = []
        chunk_id = 0
        current_position = 0

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            start_index = current_position
            end_index = start_index + len(sentence)

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=sentence,
                    start_index=start_index,
                    end_index=end_index,
                )
            )

            chunk_id += 1
            current_position = end_index

        return chunks
