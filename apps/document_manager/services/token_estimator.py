def estimate_tokens_from_text(text):
    cleaned = str(text or "").strip()
    if not cleaned:
        return 0

    word_count = len(cleaned.split())

    # Simple rough estimate for English-ish text
    return int(round(word_count * 1.3))