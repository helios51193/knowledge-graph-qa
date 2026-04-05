def estimate_tokens_from_text(text: str) -> int:
    """
    Return a rough token estimate for a block of text.

    This uses a simple word-count-based heuristic rather than a model-specific
    tokenizer because the estimate is meant for dashboard visibility and rough
    processing/cost intuition, not exact billing or context-window accounting.
    """
    cleaned = str(text or "").strip()
    if not cleaned:
        return 0

    word_count = len(cleaned.split())

    # Rough heuristic for English-like text.
    return int(round(word_count * 1.3))