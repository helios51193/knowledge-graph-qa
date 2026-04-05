import re

from django.conf import settings

from .base import BaseChunker
from .chunk import Chunk


class RecursiveChunker(BaseChunker):
    """
    Split text hierarchically by paragraph, then sentence, then words if needed.
    """

    def chunk(self, text: str, document_id: int) -> list[Chunk]:
        max_words = getattr(settings, "CHUNK_SIZE", 200)
        overlap_words = getattr(settings, "CHUNK_OVERLAP", 20)

        paragraphs = self._split_paragraphs(text)
        segments: list[str] = []

        for paragraph in paragraphs:
            if self._word_count(paragraph) <= max_words:
                segments.append(paragraph)
                continue

            sentences = self._split_sentences(paragraph)
            current_segment: list[str] = []

            for sentence in sentences:
                candidate = " ".join(current_segment + [sentence]).strip()

                if self._word_count(candidate) <= max_words:
                    current_segment.append(sentence)
                    continue

                if current_segment:
                    segments.append(" ".join(current_segment).strip())

                if self._word_count(sentence) <= max_words:
                    current_segment = [sentence]
                else:
                    # Fall back to overlapping word windows for very long sentences.
                    segments.extend(
                        self._split_by_words(sentence, max_words, overlap_words)
                    )
                    current_segment = []

            if current_segment:
                segments.append(" ".join(current_segment).strip())

        chunks: list[Chunk] = []
        chunk_id = 0
        search_start = 0

        for segment in segments:
            cleaned_segment = segment.strip()
            if not cleaned_segment:
                continue

            start_index = text.find(cleaned_segment, search_start)
            if start_index == -1:
                start_index = search_start

            end_index = start_index + len(cleaned_segment)
            search_start = end_index

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=cleaned_segment,
                    start_index=start_index,
                    end_index=end_index,
                )
            )
            chunk_id += 1

        return chunks

    def _split_paragraphs(self, text: str) -> list[str]:
        """
        Split text into non-empty paragraph segments.
        """
        return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into non-empty sentence segments.
        """
        return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]

    def _split_by_words(self, text: str, max_words: int, overlap_words: int) -> list[str]:
        """
        Split very long text into overlapping word windows.
        """
        words = text.split()
        if not words:
            return []

        step = max(1, max_words - overlap_words)
        segments: list[str] = []

        for i in range(0, len(words), step):
            segment_words = words[i:i + max_words]
            if not segment_words:
                continue

            segments.append(" ".join(segment_words))

            if i + max_words >= len(words):
                break

        return segments

    def _word_count(self, text: str) -> int:
        """
        Return the number of whitespace-delimited words in a text segment.
        """
        return len(text.split())
