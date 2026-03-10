from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings

class Document(models.Model):

    STATUS_PENDING = "pending"
    STATUS_PROCESSING= "processing"
    STATUS_COMPLETE = "complete"
    STATUS_ERROR = "error"

    
    
    LLM_CHOICES = [
        ("", "Select LLM"),
        ("llama3", "Llama 3"),
        ("mistral", "Mistral"),
        ("gpt4", "GPT-4"),
        
    ]

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETE,"Complete"),
        (STATUS_ERROR,"Error")
    ]


    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    name = models.CharField(max_length=255)

    file = models.FileField(upload_to="documents/")

    nodes = models.IntegerField(default=0)
    edges = models.IntegerField(default=0)
    relations = models.IntegerField(default=0)

    llm_used = models.CharField(max_length=100, choices=LLM_CHOICES, blank=False)

    processing_time = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    graph_data = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user})"