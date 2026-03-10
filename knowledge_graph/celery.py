import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "knowledge_graph.settings")

app = Celery("knowledge_graph")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
print("Tasks Discovered")