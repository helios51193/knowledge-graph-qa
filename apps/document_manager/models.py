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
    progress = models.IntegerField(default=0)
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

class ProcessingLog(models.Model):

    document = models.ForeignKey(
        "Document",
        on_delete=models.CASCADE,
        related_name="processing_logs"
    )

    stage = models.CharField(max_length=100)

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.document.id} - {self.stage}"
    
    class Meta:
        ordering = ["created_at"]


class QASession(models.Model):
    document = models.ForeignKey(
        "Document",
        on_delete=models.CASCADE,
        related_name="qa_sessions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="qa_sessions",
    )
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or f"Session {self.id} - {self.document.name}"
    class Meta:
        ordering = ["-updated_at"]

class QAMessage(models.Model):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
    ]

    session = models.ForeignKey(
        "QASession",
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    cypher = models.TextField(blank=True)
    query_rows = models.JSONField(default=list, blank=True)
    provenance = models.JSONField(default=list, blank=True)
    highlight = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session_id} - {self.role}"

    class Meta:
        ordering = ["created_at"]