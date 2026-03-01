from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Document
from apps.extraction.pipeline import process_document
from .services.text_extractor import extract_text_from_file

@login_required
def upload_document(request):
    if request.method == "POST":
        file = request.FILES["file"]

        document = Document.objects.create(
            user=request.user,
            title=file.name,
            file=file,
            status="uploaded"
        )

        # Extract text via service layer
        text = extract_text_from_file(document.file.path)
        document.extracted_text = text
        document.status = "processing"
        document.save()

        # Trigger processing (sync for now)
        process_document(document)

    documents = Document.objects.filter(user=request.user).order_by("-created_at")

    return render(request, "documents/partials/document_list.html", {
        "documents": documents
    })

def document_list(request):
    pass

@login_required
def document_status(request, pk):
    document = Document.objects.get(pk=pk, user=request.user)

    return render(request, "documents/partials/document_row.html", {
        "doc": document
    })
