from django.conf import settings
from .openai_provider import OpenAILLM
from .ollama_provider import OllamaLLM

def get_llm():
    if settings.LLM_PROVIDER.lower() == "openai":
        return OpenAILLM()
    return OllamaLLM()