from ..models import Document, ProcessingLog


def log_stage(document: Document, stage: str, message: str) -> None:
    """
    Create a processing log entry for a document pipeline stage.
    """
    ProcessingLog.objects.create(
        document=document,
        stage=stage,
        message=message,
    )


def update_progress(document: Document, progress: int) -> None:
    """
    Update a document's processing progress, clamping the value to 0-100.
    """
    clamped = max(0, min(100, int(progress)))
    document.progress = clamped
    document.save(update_fields=["progress"])