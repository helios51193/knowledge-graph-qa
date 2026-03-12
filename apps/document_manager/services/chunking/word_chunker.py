from django.conf import settings
from .base import BaseChunker
from .chunk import Chunk


class WordChunker(BaseChunker):

    def chunk(self, text, document_id):

        words = text.split()

        chunk_size = settings.CHUNK_SIZE
        overlap = settings.CHUNK_OVERLAP
        step = chunk_size - overlap

        chunks = []
        chunk_id = 0

        for i in range(0, len(words), step):

            chunk_words = words[i:i + chunk_size]

            chunk_text = " ".join(chunk_words)

            start_index = i
            end_index = i + len(chunk_words)

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=chunk_text,
                    start_index=start_index,
                    end_index=end_index
                )
            )

            chunk_id += 1

        return chunks