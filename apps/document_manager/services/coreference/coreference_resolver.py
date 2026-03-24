from .factory import get_coreference_resolver
from ..logger import log_stage


def resolve_coreferences(document, text):
    if document is not None:
        log_stage(document, "COREFERENCE", "Starting coreference resolution")

    resolver = get_coreference_resolver()
    result = resolver.resolve(text)

    if document is not None:
        cluster_count = len(result.get("clusters", []))
        changed = result.get("resolved_text") != result.get("original_text")
        log_stage(
            document,
            "COREFERENCE",
            f"Coreference resolution completed with {cluster_count} clusters; text_changed={changed}",
    )

    return result