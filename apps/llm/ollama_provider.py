# ollama_provider.py
import requests
from .base import BaseLLM
from django.conf import settings

class OllamaLLM(BaseLLM):
    def extract_knowledge_graph(self, text: str) -> dict:

        prompt = f"""
        Extract entities and relationships from the text.
        Return ONLY valid JSON in this format:

        {{
          "entities": [
            {{"name": "...", "type": "..."}}
          ],
          "relationships": [
            {{"source": "...", "target": "...", "relation": "..."}}
          ]
        }}

        Text:
        {text}
        """

        response = requests.post(
            f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
        )

        return response.json()