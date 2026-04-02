from django.conf import settings

def build_chunk_metrics(chunks):
    if not chunks:
        return {
            "chunker": getattr(settings, "DOCUMENT_CHUNKER", "unknown"),
            "chunk_count": 0,
            "total_words": 0,
            "avg_words": 0.0,
            "min_words": 0,
            "max_words": 0,
        }

    word_counts = [len((chunk.text or "").split()) for chunk in chunks]
    total_words = sum(word_counts)
    chunk_count = len(chunks)

    return {
        "chunker": getattr(settings, "DOCUMENT_CHUNKER", "unknown"),
        "chunk_count": chunk_count,
        "total_words": total_words,
        "avg_words": round(total_words / chunk_count, 2),
        "min_words": min(word_counts),
        "max_words": max(word_counts),
    }