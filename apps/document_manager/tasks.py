from celery import shared_task
from django.utils import timezone

from .models import Document
from .services.graph_database import save_graph_to_database
from .services.logger import log_stage, update_progress
from .services.process_document_pipeline import process_document_pipeline


@shared_task
def process_document(document_id: int) -> None:
    """
    Run the full asynchronous processing workflow for a document.

    This task:
    - runs the document processing pipeline
    - stores graph summary data on the document
    - persists the graph to Memgraph
    - updates progress and final status
    - records processing logs
    """
    document = Document.objects.get(id=document_id)

    log_stage(document, "START", "Document processing started")
    update_progress(document, 5)

    start = timezone.now()

    try:
        result = process_document_pipeline(document)
        graph_data = result["graph"]

        document.graph_data = graph_data
        document.nodes = graph_data["counts"]["nodes"]
        document.edges = graph_data["counts"]["edges"]
        document.relations = graph_data["counts"]["relation_types"]

        log_stage(document, "GRAPH_BUILDING", "Graph data prepared")
        update_progress(document, 92)

        save_graph_to_database(document, graph_data)

        log_stage(document, "GRAPH_DATABASE", "Graph saved to Memgraph")
        update_progress(document, 97)

        document.status = Document.STATUS_COMPLETE
        document.error_message = ""
        document.progress = 100
        document.save()

        log_stage(document, "COMPLETE", "Processing finished successfully")

    except Exception as exc:
        document.status = Document.STATUS_ERROR
        document.error_message = str(exc)
        log_stage(document, "ERROR", str(exc))
        document.save()

    finally:
        document.processing_time = (timezone.now() - start).total_seconds()
        document.save()
