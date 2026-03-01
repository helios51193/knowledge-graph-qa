# openai_provider.py
import os
from openai import OpenAI
from .base import BaseLLM
from django.conf import settings

class OpenAILLM(BaseLLM):
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPEN_AI_KEY)

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

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        return eval(response.choices[0].message.content)