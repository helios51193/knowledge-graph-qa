from django.conf import settings

from .noop_resolver import NoopCoreferenceResolver
from .fastcoref_resolver import FastCoreferenceResolver

def get_coreference_resolver():
    resolver_type = getattr(settings, "COREFERENCE_RESOLVER", "noop")

    if resolver_type == "noop":
        return NoopCoreferenceResolver()
    
    if resolver_type == "fastcoref":
        return FastCoreferenceResolver()

    raise ValueError(f"Invalid coreference resolver type: {resolver_type}")