from celery import shared_task

from .services.graph_database import save_graph_to_database
from .models import Document
from django.utils import timezone
from .services.process_document_pipeline import process_document_pipeline
import time
from .services.logger import log_stage

@shared_task
def process_document(document_id):

    document = Document.objects.get(id=document_id)
    log_stage(document, "START", "Document processing started")
    start = timezone.now()
    try:

        result = process_document_pipeline(document)

        graph_data = result['graph']

        document.graph_data = graph_data
        document.nodes =  graph_data["counts"]["nodes"]
        document.edges = graph_data["counts"]["edges"]
        document.relations = graph_data["counts"]["relation_types"]

        log_stage(document, "GRAPH_BUILDING", "Graph data prepared")

        save_graph_to_database(document, graph_data)
        log_stage(document, "GRAPH_DATABASE", "Graph saved to Memgraph")

        document.status = Document.STATUS_COMPLETE
        document.error_message = ""
        document.save()
        
        log_stage(document, "COMPLETE", "Processing finished successfully")

    except Exception as e:

        document.status = Document.STATUS_ERROR
        document.error_message = str(e)
        log_stage(document, "ERROR", str(e))
    finally:
        document.processing_time = (timezone.now() - start).total_seconds()
        document.save()