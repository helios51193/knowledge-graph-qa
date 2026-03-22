import json
from pprint import pprint

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
                "provenance": result.get("provenance", []),
                "has_error": False,
            }
        
        pprint(context)
        
        response = render(request, "document_manager/components/qa_result.jinja", context=context)

        response["HX-Trigger-After-Swap"] = json.dumps({
            "qaGraphHighlight": result.get("highlight", {
                "node_ids": [],
                "edge_ids": [],
                "focus": False,
            })
        })

        return response


    except Exception as e:
        
        context = {
            "document": document,
            "question": question,
            "answer": str(e),
            "cypher": "",
            "rows": [],
            "provenance": [],
            "has_error": True,
        }
        
        response = render(
            request,
            "document_manager/components/qa_result.jinja",
            context=context,
        )

        response["HX-Trigger-After-Swap"] = json.dumps({
            "qaGraphHighlight": {
                "node_ids": [],
                "edge_ids": [],
                "focus": False,
            }
        })

        return response

@login_required
def document_qa_page(request, doc_id):
    document = get_object_or_404(Document, id=doc_id, user=request.user)

    return render(
        request,
        "document_manager/qa_page.jinja",
        {
            "document": document,
        },
    )


