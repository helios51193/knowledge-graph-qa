class BaseLLM:
    def extract_knowledge_graph(self, text: str) -> dict:
        raise NotImplementedError