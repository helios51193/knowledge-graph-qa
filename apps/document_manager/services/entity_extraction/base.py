from abc import ABC, abstractmethod

class BaseEntityExtractor(ABC):

    @abstractmethod
    def extract(self, chunks, llm):
        pass
