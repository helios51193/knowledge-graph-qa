import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from .models import Document
from .forms import DocumentUploadForm
from .tasks import process_document


@login_required
def document_dashboard(request):
    return render(request,"document_manager/dashboard.jinja",)

@login_required
def document_table(request):
    
    documents = Document.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "document_manager/components/document_table.jinja",
        {"documents": documents}
    )



@login_required
def upload_document(request):

    if request.method == "POST":

        form = DocumentUploadForm(request.POST, request.FILES)

        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.save()

            response = HttpResponse()
            response["HX-Trigger"] = json.dumps({
                "documentsUpdated": True,
                "closeUploadModal": True
            })

            return response

    else:
        form = DocumentUploadForm()

    return render(
        request,
        "document_manager/components/upload_modal.jinja",
        {"form": form}
    )

@login_required
def process_document_view(request, doc_id):

    document = Document.objects.get(id=doc_id, user=request.user)

    document.status = Document.STATUS_PROCESSING
    document.save()

    process_document.delay(document.id)

    response = HttpResponse()

    response["HX-Trigger"] = json.dumps({
        "documentsUpdated": True
    })

    return response

@login_required
def delete_document(request, doc_id):

    document = Document.objects.get(id=doc_id, user=request.user)

    document.delete()

    response = HttpResponse()

    response["HX-Trigger"] = json.dumps({
        "documentsUpdated": True
    })

    return response


