from .base import BaseCoreferenceResolver


class NoopCoreferenceResolver(BaseCoreferenceResolver):

    def resolve(self, text):
        return {
            "original_text": text,
            "resolved_text": text,
            "clusters": [],
        }