from django.conf import settings

from .base import BaseCoreferenceResolver
from .fastcoref_resolver import FastCoreferenceResolver
from .noop_resolver import NoopCoreferenceResolver


def get_coreference_resolver() -> BaseCoreferenceResolver:
    """
    Return the configured coreference resolver implementation.
    """
    resolver_type = getattr(settings, "COREFERENCE_RESOLVER", "noop")

    if resolver_type == "noop":
        return NoopCoreferenceResolver()

    if resolver_type == "fastcoref":
        return FastCoreferenceResolver()

    raise ValueError(f"Invalid coreference resolver type: {resolver_type}")
