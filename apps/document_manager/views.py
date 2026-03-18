import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import Document
from .forms import DocumentUploadForm
from .tasks import process_document
from .services.qa.qa_engine import QAEngine


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

@login_required
def ask_question(request, doc_id):

    document = get_object_or_404(Document, id=doc_id, user=request.user)

    question = request.POST.get("question", "").strip()

    if not question:
        context = {
                "document": document,
                "question": question,
                "answer": "Please enter a question.",
                "cypher": "",
                "rows": [],
                "has_error": True,
            }
        return render(request, "document_manager/components/qa_result.jinja", context=context)


    try:
        qa_engine = QAEngine()
        result = qa_engine.answer_question(document, question)

        context ={
                "document": document,
                "question": result["question"],
                "answer": result["answer"],
                "cypher": result["cypher"],
                "rows": result["rows"],
                "has_error": False,
            }
        
        return render(request, "document_manager/components/qa_result.jinja", context=context)
    except Exception as e:
        context = {
                "document": document,
                "question": question,
                "answer": str(e),
                "cypher": "",
                "rows": [],
                "has_error": True,
            }
        
        return render(request, "document_manager/components/qa_result.jinja", context=context)
        


