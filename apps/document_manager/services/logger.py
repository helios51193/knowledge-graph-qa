from ..models import ProcessingLog


def log_stage(document, stage, message):

    ProcessingLog.objects.create(
        document=document,
        stage=stage,
        message=message
    )