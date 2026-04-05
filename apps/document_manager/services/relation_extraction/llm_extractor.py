import json
import re
from typing import Any

import requests
from django.conf import settings
from openai import OpenAI
from rapidfuzz import fuzz

from ..chunking.chunk import Chunk
from .base import BaseRelationExtractor


class LlmRelationExtractor(BaseRelationExtractor):
    """
    Extract relations using an LLM and then normalize the returned relation records.
    """

    def extract(
        self,
        chunks: list[Chunk],
        entities: list[dict[str, Any]],
        llm: str,
    ) -> list[dict[str, Any]]:
        """
        Extract and normalize relations chunk by chunk, with deduplication across the run.
        """
        relations: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()

        for chunk in chunks:
            chunk_entities = self._get_chunk_entities(chunk, entities)

            if len(chunk_entities) < 2:
                continue

            analysis_text = chunk.analysis_text or chunk.text

            raw_relations = self._extract_chunk_relations(
                text=analysis_text,
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

    def _get_chunk_entities(
        self,
        chunk: Chunk,
        entities: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Return the entities that belong to the chunk or its source chunk window.
        """
        source_chunk_ids = chunk.source_chunk_ids or [chunk.chunk_id]

        return [
            entity
            for entity in entities
            if entity.get("document_id") == chunk.document_id
            and entity.get("chunk_id") in source_chunk_ids
        ]

    def _extract_chunk_relations(
        self,
        text: str,
        entities: list[dict[str, Any]],
        llm: str,
    ) -> list[dict[str, Any]]:
        """
        Ask the configured LLM to extract relations for a single chunk.
        """
        prompt = self._build_prompt(text, entities)

        if llm == "gpt4":
            response_text = self._extract_with_openai(prompt)
        elif llm == "llama3":
            response_text = self._extract_with_ollama(prompt)
        else:
            raise ValueError(f"Unsupported LLM for relation extraction: {llm}")

        return self._parse_json_response(response_text)

    def _build_prompt(self, text: str, entities: list[dict[str, Any]]) -> str:
        """
        Build the JSON-only relation extraction prompt for the LLM.
        """
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
                - Use the closest matching provided entity names exactly.
                - If the text uses a pronoun or resolved reference, map it to the corresponding provided entity name.
                - Prefer returning all clearly supported relationships, not just one.
                - If a relation spans two nearby sentences in the same chunk, you may still extract it if it is clearly supported.

                Text:
                \"\"\"
                {text}
                \"\"\"
                """.strip()

    def _extract_with_openai(self, prompt: str) -> str:
        """
        Send the relation extraction prompt to OpenAI.
        """
        client = OpenAI(api_key=settings.OPEN_AI_KEY)

        response = client.chat.completions.create(
            model=getattr(settings, "OPENAI_RELATION_MODEL", "gpt-4o-mini"),
            temperature=getattr(settings, "RELATION_LLM_TEMPERATURE", 0),
            messages=[
                {
                    "role": "system",
                    "content": "You are an information extraction system that returns JSON only.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return response.choices[0].message.content

    def _extract_with_ollama(self, prompt: str) -> str:
        """
        Send the relation extraction prompt to Ollama.
        """
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
                },
            },
            timeout=getattr(settings, "RELATION_LLM_TIMEOUT", 90),
        )

        if not response.ok:
            print("Ollama status:", response.status_code)
            print("Ollama body:", response.text)

        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    def _parse_json_response(self, response_text: str) -> list[dict[str, Any]]:
        """
        Parse the LLM response into a list of relation dictionaries.
        """
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

    def _strip_code_fences(self, text: str) -> str:
        """
        Remove markdown code fences from an LLM response if present.
        """
        text = text.strip()

        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        return text.strip()

    def _extract_json_object(self, text: str) -> str:
        """
        Extract the outermost JSON object from a noisy text response.
        """
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or start >= end:
            raise ValueError("LLM did not return valid JSON.")

        return text[start:end + 1]

    def _normalize_relation(
        self,
        item: dict[str, Any],
        chunk: Chunk,
        chunk_entities: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """
        Normalize and validate a raw relation record returned by the LLM.
        """
        if not isinstance(item, dict):
            return None

        source = str(item.get("source", "")).strip()
        target = str(item.get("target", "")).strip()
        relation_type = str(item.get("type", "")).strip()

        if not source or not target or not relation_type:
            return None

        if source == target:
            return None

        source_entity = self._resolve_entity_name(source, chunk_entities)
        target_entity = self._resolve_entity_name(target, chunk_entities)

        if source_entity is None or target_entity is None:
            return None

        # Skip relations whose endpoints collapse to the same resolved entity.
        if source_entity["name"].strip().lower() == target_entity["name"].strip().lower():
            return None

        relation_type = relation_type.upper().replace(" ", "_")

        return {
            "source": source_entity["name"],
            "source_label": source_entity["label"],
            "target": target_entity["name"],
            "target_label": target_entity["label"],
            "type": relation_type,
            "document_id": chunk.document_id,
            "chunk_id": chunk.chunk_id,
            "start_index": chunk.start_index,
            "end_index": chunk.end_index,
            "source_text": chunk.text,
        }

    def _resolve_entity_name(
        self,
        candidate_name: str,
        chunk_entities: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """
        Map an LLM-returned entity name back to one of the known chunk entities.

        This first tries exact normalized matching, then uses fuzzy matching over
        names and aliases as a repair step for near-miss surface forms.
        """
        candidate_norm = self._normalize_surface(candidate_name)

        if not candidate_norm:
            return None

        for entity in chunk_entities:
            if self._normalize_surface(entity["name"]) == candidate_norm:
                return entity

        best_entity: dict[str, Any] | None = None
        best_score = 0.0

        for entity in chunk_entities:
            entity_norm = self._normalize_surface(entity["name"])
            score = fuzz.token_sort_ratio(candidate_norm, entity_norm) / 100.0

            if score > best_score:
                best_score = score
                best_entity = entity

            for alias in entity.get("aliases", []):
                alias_norm = self._normalize_surface(alias)
                alias_score = fuzz.token_sort_ratio(candidate_norm, alias_norm) / 100.0

                if alias_score > best_score:
                    best_score = alias_score
                    best_entity = entity

        if best_score >= 0.90:
            return best_entity

        return None

    def _normalize_surface(self, text: str) -> str:
        """
        Normalize a surface form for matching and fuzzy comparison.
        """
        text = str(text or "").strip().lower()
        text = re.sub(r"[^a-z0-9\s\-']", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"^(the|a|an)\s+", "", text)
        return text
