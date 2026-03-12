from .factory import get_chunker
from ..logger import log_stage

def chunk_text(document, text):

    log_stage(document, "CHUNKING", "Starting document chunking")
    chunker = get_chunker()

    chunks = []

    chunks = chunker.chunk(text, document.id)

    log_stage(document, "CHUNKING", f"{len(chunks)} chunks created")

    return chunks