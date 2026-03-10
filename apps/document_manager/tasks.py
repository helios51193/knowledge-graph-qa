from celery import shared_task
from .models import Document
import time

@shared_task
def process_document(document_id):

    document = Document.objects.get(id=document_id)

    try:

        # simulate processing
        time.sleep(5)

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

    except Exception as e:

        document.status = Document.STATUS_ERROR
        document.error_message = str(e)

        document.save()