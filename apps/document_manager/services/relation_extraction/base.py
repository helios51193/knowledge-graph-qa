from abc import ABC, abstractmethod


class BaseRelationExtractor(ABC):

    @abstractmethod
    def extract(self, chunks, entities, llm):
        pass