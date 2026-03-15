import json
import re

import requests
from django.conf import settings
from openai import OpenAI

from .base import BaseEntityExtractor


class LlmEntityExtractor(BaseEntityExtractor):

    def extract(self, chunks, llm):
        entities = []
        seen = set()

        for chunk in chunks:

            raw_entities = self._extract_chunk_entities(chunk.text, llm)

            for item in raw_entities:
                normalized = self._normalize_entity(item, chunk)

                if normalized is None:
                    continue
                    
                entity_key = (
                    normalized["label"].lower(),
                    normalized["name"].lower(),
                )

                if entity_key in seen:
                    continue
                    
                seen.add(entity_key)
                entities.append(normalized)
            
        return entities
    
    def _extract_chunk_entities(self, text, llm):
        prompt = self._build_prompt(text)

        if llm == "gpt4":
            response_text = self._extract_with_openai(prompt)
        elif llm == "llama3":
            response_text = self._extract_with_ollama(prompt)
        else:
            raise ValueError(f"Unsupported LLM for entity extraction: {llm}")

        return self._parse_json_response(response_text)
    
    def _build_prompt(self, text):
         return f"""
            Extract entities from the text below.

            Return ONLY valid JSON.
            Do not include markdown.
            Do not include explanation text.

            Use this exact JSON structure:
            {{
            "entities": [
                {{
                "label": "Person | Organization | Location | Concept",
                "name": "entity name"
                }}
            ]
            }}

            Rules:
            - Extract only meaningful entities.
            - Avoid duplicates.
            - Keep names concise.
            - Use "Concept" for important non-person, non-organization, non-location ideas.
            - If there are no entities, return {{"entities": []}}.

            Text:
            \"\"\"
            {text}
            \"\"\"
            """.strip()


    def _extract_with_openai(self, prompt):

        client = OpenAI(api_key=settings.OPEN_AI_KEY)

        response = client.chat.completions.create(
            model=getattr(settings, "OPENAI_ENTITY_MODEL", "gpt-4o-mini"),
            temperature=getattr(settings, "ENTITY_LLM_TEMPERATURE", 0),
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
        model = getattr(settings, "OLLAMA_ENTITY_MODEL", "llama3")

        response = requests.post(
            f"http://{host}:{port}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": getattr(settings, "ENTITY_LLM_TEMPERATURE", 0)
                }
            },
            timeout=getattr(settings, "ENTITY_LLM_TIMEOUT", 90),
        )

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

        entities = parsed.get("entities", [])

        if not isinstance(entities, list):
            return []

        return entities

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
    
    def _normalize_entity(self, item, chunk):
        if not isinstance(item, dict):
            return None

        name = str(item.get("name", "")).strip()
        label = str(item.get("label", "")).strip()

        if not name or not label:
            return None

        allowed_labels = {"Person", "Organization", "Location", "Concept"}
        if label not in allowed_labels:
            label = "Concept"

        return {
            "label": label,
            "name": name,
            "document_id": chunk.document_id,
            "chunk_id": chunk.chunk_id,
            "start_index": chunk.start_index,
            "end_index": chunk.end_index,
            "source_text": chunk.text,
        }

