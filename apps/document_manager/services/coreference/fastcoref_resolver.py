import re

from .base import BaseCoreferenceResolver

class FastCoreferenceResolver(BaseCoreferenceResolver):
    _model = None

    def __init__(self):
        self._device = "cpu"

    def resolve(self, text):
        cleaned_text = str(text or "").strip()
        if not cleaned_text:
            return {
                "original_text": text,
                "resolved_text": text,
                "clusters": [],
            }

        model = self._get_model()

        preds = model.predict(
            texts=[cleaned_text],
            max_tokens_in_batch=128,
        )

        result = preds[0]
        clusters = result.get_clusters(as_strings=False)
        resolved_text = self._apply_coreference_replacements(
            cleaned_text,
            clusters,
        )

        return {
            "original_text": cleaned_text,
            "resolved_text": resolved_text,
            "clusters": clusters,
        }

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            try:
                from fastcoref import FCoref
            except ImportError as exc:
                raise ImportError(
                    "fastcoref is not installed. Run 'pip install fastcoref'."
                ) from exc

            cls._model = FCoref(device="cpu")

        return cls._model

    def _apply_coreference_replacements(self, text, clusters):
        replacements = []

        for cluster in clusters:
            if not cluster:
                continue

            canonical_span = self._choose_canonical_span(text, cluster)
            if canonical_span is None:
                continue

            canonical_text = text[canonical_span[0]:canonical_span[1]]

            for span in cluster[1:]:
                start, end = span
                mention_text = text[start:end]

                if not self._is_pronoun_like(mention_text):
                    continue

                replacement_text = self._match_pronoun_form(
                    canonical_text,
                    mention_text,
                )

                replacements.append((start, end, replacement_text))

        if not replacements:
            return text

        replacements.sort(key=lambda item: item[0], reverse=True)

        resolved_text = text
        for start, end, replacement_text in replacements:
            resolved_text = (
                resolved_text[:start]
                + replacement_text
                + resolved_text[end:]
            )

        return resolved_text

    def _choose_canonical_span(self, text, cluster):
        """
        Prefer the first non-pronoun mention as the canonical antecedent.
        """
        for span in cluster:
            start, end = span
            mention_text = text[start:end]

            if not self._is_pronoun_like(mention_text):
                return span

        return cluster[0] if cluster else None

    def _is_pronoun_like(self, text):
        cleaned = re.sub(r"[^a-zA-Z']", "", str(text or "")).lower()

        pronouns = {
            "he", "him", "his",
            "she", "her", "hers",
            "they", "them", "their", "theirs",
            "it", "its",
            "you", "your", "yours",
            "we", "us", "our", "ours",
            "i", "me", "my", "mine",
        }

        return cleaned in pronouns

    def _match_pronoun_form(self, canonical_text, mention_text):
        cleaned_mention = re.sub(r"[^a-zA-Z']", "", str(mention_text or "")).lower()

        if cleaned_mention in {"his", "her", "hers", "their", "theirs", "its", "your", "yours", "our", "ours", "my", "mine"}:
            if canonical_text.endswith("s"):
                return f"{canonical_text}'"
            return f"{canonical_text}'s"

        return canonical_text