from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings

class Document(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    name = models.CharField(max_length=255)

    file = models.FileField(upload_to="documents/")

    graph_namespace = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    nodes = models.IntegerField(default=0)
    edges = models.IntegerField(default=0)
    relations = models.IntegerField(default=0)

    llm_used = models.CharField(max_length=100)

    processing_time = models.FloatField(null=True, blank=True)

    status = models.CharField(
        max_length=50,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user})"