from .factory import get_chunker
from ..logger import log_stage
from .chunk_metrics import build_chunk_metrics

def chunk_text(document, text):

    log_stage(document, "CHUNKING", "Starting document chunking")
    chunker = get_chunker()

    chunks = []

    chunks = chunker.chunk(text, document.id)

    log_stage(document, "CHUNKING", f"{len(chunks)} chunks created")
    metrics = build_chunk_metrics(chunks)
    log_stage(
        document,
        "CHUNKING",
        (
            f"Chunk metrics | "
            f"chunker={metrics['chunker']} | "
            f"chunks={metrics['chunk_count']} | "
            f"total_words={metrics['total_words']} | "
            f"avg_words={metrics['avg_words']} | "
            f"min_words={metrics['min_words']} | "
            f"max_words={metrics['max_words']}"
        ),
    )



    return chunks