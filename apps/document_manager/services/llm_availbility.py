import requests
from django.conf import settings
from openai import OpenAI


def check_llm_availability(llm_used: str) -> tuple[bool, str]:
    """
    Validate whether the selected LLM option is currently reachable and usable.

    Returns a tuple of:
    - availability flag
    - human-readable error message (empty on success)
    """
    llm_used = (llm_used or "").strip()

    if llm_used == "gpt4":
        return _check_openai_model(
            model_name=getattr(settings, "OPENAI_ENTITY_MODEL", "gpt-4o-mini"),
        )

    if llm_used == "llama3":
        return _check_ollama_model(
            model_name="llama3.2",
        )

    if llm_used == "mistral":
        return _check_ollama_model(
            model_name="mistral",
        )

    return False, "Unsupported LLM selection."


def _check_openai_model(model_name: str) -> tuple[bool, str]:
    """
    Check whether the configured OpenAI model can be accessed with the current API key.
    """
    api_key = getattr(settings, "OPEN_AI_KEY", "").strip()

    if not api_key:
        return False, "OpenAI API key is not configured."

    try:
        client = OpenAI(api_key=api_key)
        client.models.retrieve(model_name)
        return True, ""
    except Exception as exc:
        return False, f"OpenAI model '{model_name}' is not accessible: {exc}"


def _check_ollama_model(model_name: str) -> tuple[bool, str]:
    """
    Check whether the requested Ollama model is available on the configured local server.
    """
    host = getattr(settings, "OLLAMA_HOST", "localhost")
    port = getattr(settings, "OLLAMA_PORT", "11434")

    try:
        response = requests.get(
            f"http://{host}:{port}/api/tags",
            timeout=5,
        )
        response.raise_for_status()

        data = response.json()
        models = data.get("models", [])

        available_names = {item.get("name", "") for item in models}

        if model_name in available_names:
            return True, ""

        # Ollama models may be tagged, for example "mistral:latest".
        if any(name.startswith(f"{model_name}:") for name in available_names):
            return True, ""

        return False, f"Ollama model '{model_name}' is not available locally."
    except Exception as exc:
        return False, f"Ollama is not accessible: {exc}"
