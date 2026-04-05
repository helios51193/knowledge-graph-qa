from django.conf import settings

from .base import BaseChunker
from .paragraph_chunker import ParagraphChunker
from .recursive_chunker import RecursiveChunker
from .sentence_chunker import SentenceChunker
from .word_chunker import WordChunker


def get_chunker() -> BaseChunker:
    """
    Return the configured chunker implementation.
    """
    chunker_type = getattr(settings, "DOCUMENT_CHUNKER", "word")

    if chunker_type == "word":
        return WordChunker()

    if chunker_type == "sentence":
        return SentenceChunker()

    if chunker_type == "paragraph":
        return ParagraphChunker()

    if chunker_type == "recursive":
        return RecursiveChunker()

    raise ValueError(f"Invalid chunker type: {chunker_type}")
