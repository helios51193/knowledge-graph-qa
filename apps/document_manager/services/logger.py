from ..models import ProcessingLog


def log_stage(document, stage, message):

    ProcessingLog.objects.create(
        document=document,
        stage=stage,
        message=message
    )

def update_progress(document, progress):
    clamped = max(0, min(100, int(progress)))
    document.progress = clamped
    document.save(update_fields=["progress"])