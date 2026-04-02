import json
from pprint import pprint

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import Document, QAMessage, QASession
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
            return render(
            request,
            "document_manager/components/upload_modal.jinja",{"form": form})
            

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

    if document.status == Document.STATUS_PROCESSING:
        return HttpResponse(status=204)

    document.status = Document.STATUS_PROCESSING
    document.progress = 0
    document.error_message = ""
    document.save(update_fields=["status", "progress", "error_message"])

    process_document.delay(document.id)

    response = HttpResponse()

    response["HX-Trigger"] = json.dumps({
        "documentsUpdated": True
    })

    return response

@login_required
def delete_document(request, doc_id):

    document = Document.objects.get(id=doc_id, user=request.user)

    if document.status == Document.STATUS_PROCESSING:
        return HttpResponse(status=409)
    
    document.delete()

    response = HttpResponse()

    response["HX-Trigger"] = json.dumps({
        "documentsUpdated": True
    })

    return response

@login_required
def ask_question(request, doc_id, session_id):

    
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


    session = get_object_or_404(QASession, id=session_id, document=document, user=request.user,)

    try:

        QAMessage.objects.create(
            session=session,
            role=QAMessage.ROLE_USER,
            content=question,
        )

        qa_engine = QAEngine()
        result = qa_engine.answer_question(document, question)

        assistant_message = QAMessage.objects.create(
            session=session,
            role=QAMessage.ROLE_ASSISTANT,
            content=result["answer"],
            cypher=result["cypher"],
            query_rows=result["rows"],
            provenance=result.get("provenance", []),
            highlight=result.get("highlight", {}),
            question_analysis=result.get("question_analysis", {}),
        )
        if not session.title:
            session.title = question[:80]
        
        session.save(update_fields=["title", "updated_at"])

        context ={
                "document": document,
                "question": result["question"],
                "answer": result["answer"],
                "cypher": result["cypher"],
                "rows": result["rows"],
                "provenance": result.get("provenance", []),
                "question_analysis": result.get("question_analysis", {}),
                "has_error": False,
            }
        
        #pprint(context)
        
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
            "question_analysis": {},
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
def document_qa_page(request, doc_id, session_id):
    document = get_object_or_404(Document, id=doc_id, user=request.user)
    session = get_object_or_404(
        QASession,
        id=session_id,
        document=document,
        user=request.user,
    )

    qa_messages = session.messages.order_by("created_at")

    context = {
            "document": document,
            "session": session,
            "qa_messages": qa_messages,
        }

    return render(
        request,
        "document_manager/qa_page.jinja",
        context=context
    )

@login_required
def document_qa_sessions_page(request, doc_id):
    document = get_object_or_404(Document, id=doc_id, user=request.user)

    sessions = document.qa_sessions.filter(user=request.user).order_by("-updated_at")

    return render(
        request,
        "document_manager/qa_sessions.jinja",
        {
            "document": document,
            "sessions": sessions,
        },
    )

@login_required
def create_qa_session(request, doc_id):
    document = get_object_or_404(Document, id=doc_id, user=request.user)

    session = QASession.objects.create(
        document=document,
        user=request.user,
        title=f"Conversation {document.qa_sessions.count() + 1}",
    )

    return redirect("document_manager:qa_page", doc_id=document.id, session_id=session.id)

@login_required
def graph_panel(request, doc_id):
    document = get_object_or_404(Document, id=doc_id, user=request.user)

    return render(
        request,
        "document_manager/components/graph_panel.jinja",
        {
            "document": document,
        },
    )