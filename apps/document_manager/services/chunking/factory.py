from django.conf import settings

from .word_chunker import WordChunker
from .sentence_chunker import SentenceChunker
from .paragraph_chunker import ParagraphChunker
from .recursive_chunker import RecursiveChunker


def get_chunker():

    chunker_type = getattr(settings, "DOCUMENT_CHUNKER", "word")

    if chunker_type == "word":
        return WordChunker()

    if chunker_type == "sentence":
        return SentenceChunker()

    if chunker_type == "paragraph":
        return ParagraphChunker()

    if chunker_type == "recursive":
        return RecursiveChunker()

    raise ValueError("Invalid chunker type")