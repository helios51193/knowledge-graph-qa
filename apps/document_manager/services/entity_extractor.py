def extract_entities(chunks, llm):

    entities = []

    for chunk in chunks:
        # placeholder
        entities.append({"label": "Concept", "name": chunk[:10]})

    return entities