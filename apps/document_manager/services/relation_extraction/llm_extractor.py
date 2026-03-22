import json
import re

import requests
from django.conf import settings
from openai import OpenAI

from .base import BaseRelationExtractor

class LlmRelationExtractor(BaseRelationExtractor):

    def extract(self, chunks, entities, llm):
        relations = []
        seen = set()

        for chunk in chunks:
            chunk_entities = self._get_chunk_entities(chunk, entities)

            if len(chunk_entities) < 2:
                continue

            raw_relations = self._extract_chunk_relations(
                text=chunk.text,
                entities=chunk_entities,
                llm=llm,
            )

            for item in raw_relations:
                normalized = self._normalize_relation(item, chunk, chunk_entities)

                if normalized is None:
                    continue

                relation_key = (
                    normalized["source"].lower(),
                    normalized["target"].lower(),
                    normalized["type"].upper(),
                )

                if relation_key in seen:
                    continue

                seen.add(relation_key)
                relations.append(normalized)

        return relations
    
    def _get_chunk_entities(self, chunk, entities):
        return [
            entity
            for entity in entities
            if entity.get("chunk_id") == chunk.chunk_id
            and entity.get("document_id") == chunk.document_id
        ]
    
    def _extract_chunk_relations(self, text, entities, llm):
        prompt = self._build_prompt(text, entities)

        if llm == "gpt4":
            response_text = self._extract_with_openai(prompt)
        elif llm == "llama3":
            response_text = self._extract_with_ollama(prompt)
        else:
            raise ValueError(f"Unsupported LLM for relation extraction: {llm}")

        return self._parse_json_response(response_text)

    def _build_prompt(self, text, entities):
        entity_list = [
            {
                "label": entity["label"],
                "name": entity["name"],
            }
            for entity in entities
        ]

        return f"""
                Extract relationships between the known entities in the text below.

                Return ONLY valid JSON.
                Do not include markdown.
                Do not include explanation text.

                Known entities:
                {json.dumps(entity_list, ensure_ascii=True)}

                Use this exact JSON structure:
                {{
                "relations": [
                    {{
                    "source": "entity name",
                    "target": "entity name",
                    "type": "RELATION_TYPE"
                    }}
                ]
                }}

                Rules:
                - Use only the provided entities.
                - Do not invent new entities.
                - Relation type must be uppercase with underscores.
                - Only return relationships clearly supported by the text.
                - If there are no relations, return {{"relations": []}}.

                Text:
                \"\"\"
                {text}
                \"\"\"
                """.strip()
    
    def _extract_with_openai(self, prompt):
        client = OpenAI(api_key=settings.OPEN_AI_KEY)

        response = client.chat.completions.create(
            model=getattr(settings, "OPENAI_RELATION_MODEL", "gpt-4o-mini"),
            temperature=getattr(settings, "RELATION_LLM_TEMPERATURE", 0),
            messages=[
                {
                    "role": "system",
                    "content": "You are an information extraction system that returns JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    def _extract_with_ollama(self, prompt):
        host = getattr(settings, "OLLAMA_HOST", "localhost")
        port = getattr(settings, "OLLAMA_PORT", "11434")
        model = getattr(settings, "OLLAMA_RELATION_MODEL", "llama3.2")

        response = requests.post(
            f"http://{host}:{port}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": getattr(settings, "RELATION_LLM_TEMPERATURE", 0)
                }
            },
            timeout=getattr(settings, "RELATION_LLM_TIMEOUT", 90),
        )

        if not response.ok:
            print("Ollama status:", response.status_code)
            print("Ollama body:", response.text)

        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    def _parse_json_response(self, response_text):
        
        cleaned = self._strip_code_fences(response_text)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            cleaned = self._extract_json_object(cleaned)
            parsed = json.loads(cleaned)

        relations = parsed.get("relations", [])

        if not isinstance(relations, list):
            return []

        return relations
    
    def _strip_code_fences(self, text):
        text = text.strip()

        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        return text.strip()
    
    def _extract_json_object(self, text):
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or start >= end:
            raise ValueError("LLM did not return valid JSON.")

        return text[start:end + 1]
    
    def _normalize_relation(self, item, chunk, chunk_entities):
        if not isinstance(item, dict):
            return None

        source = str(item.get("source", "")).strip()
        target = str(item.get("target", "")).strip()
        relation_type = str(item.get("type", "")).strip()

        if not source or not target or not relation_type:
            return None

        if source == target:
            return None

        entity_index = {entity["name"]: entity for entity in chunk_entities}

        if source not in entity_index or target not in entity_index:
            return None

        relation_type = relation_type.upper().replace(" ", "_")

        return {
            "source": source,
            "source_label": entity_index[source]["label"],
            "target": target,
            "target_label": entity_index[target]["label"],
            "type": relation_type,
            "document_id": chunk.document_id,
            "chunk_id": chunk.chunk_id,
            "start_index": chunk.start_index,
            "end_index": chunk.end_index,
            "source_text": chunk.text,
        }