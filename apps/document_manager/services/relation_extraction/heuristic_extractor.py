from .base import BaseRelationExtractor

class HeuristicRelationExtractor(BaseRelationExtractor):

    RELATION_PATTERNS = [
        ("works at", "WORKS_AT"),
        ("worked at", "WORKS_AT"),
        ("employed by", "WORKS_AT"),
        ("joined", "JOINED"),
        ("founded", "FOUNDED"),
        ("created", "CREATED"),
        ("located in", "LOCATED_IN"),
        ("based in", "LOCATED_IN"),
        ("lives in", "LIVES_IN"),
        ("born in", "BORN_IN"),
        ("part of", "PART_OF"),
    ]

    def extract(self, chunks, entities, llm):
        relations = []
        seen = set()

        for chunk in chunks:
            chunk_entities = self._get_chunk_entities(chunk, entities)
            if len(chunk_entities) < 2:
                continue

            text_lower = chunk.text.lower()

            for relation_phrase, relation_type in self.RELATION_PATTERNS:
                if relation_phrase not in text_lower:
                    continue

                for source, target in self._pair_entities(chunk_entities):
                    if source["name"] == target["name"]:
                        continue

                    relation = self._build_relation(
                        source=source,
                        target=target,
                        relation_type=relation_type,
                        chunk=chunk,
                    )

                    relation_key = (
                        relation["source"].lower(),
                        relation["target"].lower(),
                        relation["type"].upper(),
                    )

                    if relation_key in seen:
                        continue

                    seen.add(relation_key)
                    relations.append(relation)

        return relations


    def _get_chunk_entities(self, chunk, entities):
        return [
            entity
            for entity in entities
            if entity.get("chunk_id") == chunk.chunk_id
            and entity.get("document_id") == chunk.document_id
        ]
    
    def _pair_entities(self, chunk_entities):
        pairs = []

        for i in range(len(chunk_entities)):
            for j in range(len(chunk_entities)):
                if i == j:
                    continue
                pairs.append((chunk_entities[i], chunk_entities[j]))

        return pairs

    def _build_relation(self, source, target, relation_type, chunk):
        return {
            "source": source["name"],
            "source_label": source["label"],
            "target": target["name"],
            "target_label": target["label"],
            "type": relation_type,
            "document_id": chunk.document_id,
            "chunk_id": chunk.chunk_id,
            "start_index": chunk.start_index,
            "end_index": chunk.end_index,
            "source_text": chunk.text,
        }


