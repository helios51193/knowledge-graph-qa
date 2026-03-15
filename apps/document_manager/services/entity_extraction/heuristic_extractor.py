import re

from .base import BaseEntityExtractor

STOPWORDS = {
    "The", "A", "An", "This", "That", "These", "Those",
    "He", "She", "It", "They", "We", "I", "You",
    "In", "On", "At", "By", "For", "From", "To", "With", "Of",
    "And", "Or", "But", "If", "Then", "So", "As", "Is", "Are",
    "Was", "Were", "Be", "Been", "Being",
    "Chapter", "Section", "Figure", "Table"
}

ORG_SUFFIXES = {
    "Inc", "Ltd", "LLC", "Company", "Corporation", "Corp", "University",
    "Institute", "Agency", "Bank", "Labs", "Lab", "Technologies", "Systems"
}


LOCATION_HINTS = {
    "City", "Town", "Village", "State", "Country", "Street", "Road",
    "River", "Mountain", "Lake", "Park"
}

class HeuristicEntityExtractor(BaseEntityExtractor):

    def extract(self, chunks, llm):
        entities = []
        seen = set()

        for chunk in chunks:
            candidates = self._extract_candidates(chunk.text)

            for candidate in candidates:
                name = self._normalize_entity_name(candidate)

                if not self._is_valid_candidate(name):
                    continue

                label = self._guess_entity_label(name)

                entity_key = (label.lower(), name.lower())
                if entity_key in seen:
                    continue

                seen.add(entity_key)

                entities.append({
                    "label": label,
                    "name": name,
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.chunk_id,
                    "start_index": chunk.start_index,
                    "end_index": chunk.end_index,
                    "source_text": chunk.text,
                })

        return entities
     
    def _extract_candidates(self, text):
        pattern = r"\b(?:[A-Z][a-zA-Z]+|[A-Z]{2,})(?:\s+(?:[A-Z][a-zA-Z]+|[A-Z]{2,}))*\b"
        return re.findall(pattern, text)

    def _normalize_entity_name(self, name):
        return re.sub(r"\s+", " ", name).strip()
    
    def _is_valid_candidate(self, name):
        if not name:
            return False

        if len(name) < 2:
            return False

        if name in STOPWORDS:
            return False

        if name.isdigit():
            return False

        return True

    def _guess_entity_label(self, name):
        words = name.split()

        if len(words) >= 2 and words[-1] in ORG_SUFFIXES:
            return "Organization"

        if any(word in LOCATION_HINTS for word in words):
            return "Location"

        if len(words) == 1 and words[0].isupper() and len(words[0]) > 1:
            return "Organization"

        if len(words) >= 2:
            return "Person"

        return "Concept"