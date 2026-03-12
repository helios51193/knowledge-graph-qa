from celery import shared_task
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

        graph_data = {
            "nodes": [
                {"label": "Entity", "name": "Example"}
            ],
            "edges": []
        }

        document.graph_data = graph_data
        document.nodes = len(graph_data["nodes"])
        document.edges = len(graph_data["edges"])

        document.status = Document.STATUS_COMPLETE

        document.save()
        log_stage(document, "COMPLETE", "Processing finished successfully")

    except Exception as e:

        document.status = Document.STATUS_ERROR
        document.error_message = str(e)
        log_stage(document, "ERROR", str(e))
    finally:
        document.processing_time = (timezone.now() - start).total_seconds()
        document.save()