from .base import BaseChunker
from .chunk import Chunk

class ParagraphChunker(BaseChunker):

    def chunk(self, text, document_id):

        paragraphs = text.split("\n\n")

        chunks = []
        chunk_id = 0
        current_position = 0

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if not paragraph:
                continue

            start_index = current_position
            end_index = start_index + len(paragraph)

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=paragraph,
                    start_index=start_index,
                    end_index=end_index
                )
            )

            chunk_id += 1
            current_position = end_index

        return chunks

