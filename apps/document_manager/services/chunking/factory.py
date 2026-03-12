from django.conf import settings

from .word_chunker import WordChunker
from .sentence_chunker import SentenceChunker
from .paragraph_chunker import ParagraphChunker


def get_chunker():
    print("Inside")

    chunker_type = getattr(settings, "DOCUMENT_CHUNKER", "word")

    if chunker_type == "word":
        return WordChunker()

    if chunker_type == "sentence":
        return SentenceChunker()

    if chunker_type == "paragraph":
        return ParagraphChunker()

    raise ValueError("Invalid chunker type")