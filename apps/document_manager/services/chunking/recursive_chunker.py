import re

from django.conf import settings

from .base import BaseChunker
from .chunk import Chunk


class RecursiveChunker(BaseChunker):

    def chunk(self, text, document_id):
        max_words = getattr(settings, "CHUNK_SIZE", 200)
        overlap_words = getattr(settings, "CHUNK_OVERLAP", 20)

        paragraphs = self._split_paragraphs(text)
        segments = []

        for paragraph in paragraphs:
            paragraph_word_count = self._word_count(paragraph)

            if paragraph_word_count <= max_words:
                segments.append(paragraph)
                continue

            sentences = self._split_sentences(paragraph)

            current_segment = []

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
                    segments.extend(
                        self._split_by_words(sentence, max_words, overlap_words)
                    )
                    current_segment = []

            if current_segment:
                segments.append(" ".join(current_segment).strip())

        chunks = []
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

    def _split_paragraphs(self, text):
        return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]

    def _split_sentences(self, text):
        return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]

    def _split_by_words(self, text, max_words, overlap_words):
        words = text.split()
        if not words:
            return []

        step = max(1, max_words - overlap_words)
        segments = []

        for i in range(0, len(words), step):
            segment_words = words[i:i + max_words]
            if not segment_words:
                continue
            segments.append(" ".join(segment_words))

            if i + max_words >= len(words):
                break

        return segments

    def _word_count(self, text):
        return len(text.split())