import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DocumentUploadForm
from .models import Document, ProcessingLog, QAMessage, QASession
from .services.qa.qa_engine import QAEngine
from .tasks import process_document


@login_required
def document_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Render the main document dashboard page.
    """
    return render(request, "document_manager/dashboard.jinja")


@login_required
def document_table(request: HttpRequest) -> HttpResponse:
    """
    Render the dashboard document table partial.
    """
    documents = Document.objects.filter(user=request.user).order_by("-created_at")

    return render(
        request,
        "document_manager/components/document_table.jinja",
        {"documents": documents},
    )


@login_required
def upload_document(request: HttpRequest) -> HttpResponse:
    """
    Render the upload modal or handle document upload submission.
    """
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)

        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.save()

            response = HttpResponse()
            response["HX-Trigger"] = json.dumps(
                {
                    "documentsUpdated": True,
                    "closeUploadModal": True,
                }
            )
            return response

        return render(
            request,
            "document_manager/components/upload_modal.jinja",
            {"form": form},
        )

    form = DocumentUploadForm()
    return render(
        request,
        "document_manager/components/upload_modal.jinja",
        {"form": form},
    )


@login_required
def process_document_view(request: HttpRequest, doc_id: int) -> HttpResponse:
    """
    Mark a document as processing and enqueue the background processing task.
    """
    document = Document.objects.get(id=doc_id, user=request.user)

    if document.status == Document.STATUS_PROCESSING:
        return HttpResponse(status=204)

    document.status = Document.STATUS_PROCESSING
    document.progress = 0
    document.error_message = ""
    document.save(update_fields=["status", "progress", "error_message"])

    process_document.delay(document.id)

    response = HttpResponse()
    response["HX-Trigger"] = json.dumps({"documentsUpdated": True})
    return response


@login_required
def delete_document(request: HttpRequest, doc_id: int) -> HttpResponse:
    """
    Delete a document unless it is currently being processed.
    """
    document = Document.objects.get(id=doc_id, user=request.user)

    if document.status == Document.STATUS_PROCESSING:
        return HttpResponse(status=409)

    document.delete()

    response = HttpResponse()
    response["HX-Trigger"] = json.dumps({"documentsUpdated": True})
    return response


@login_required
def ask_question(request: HttpRequest, doc_id: int, session_id: int) -> HttpResponse:
    """
    Handle a QA request, save the user/assistant turns, and return the QA result partial.
    """
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
        return render(
            request,
            "document_manager/components/qa_result.jinja",
            context=context,
        )

    session = get_object_or_404(
        QASession,
        id=session_id,
        document=document,
        user=request.user,
    )

    try:
        QAMessage.objects.create(
            session=session,
            role=QAMessage.ROLE_USER,
            content=question,
        )

        qa_engine = QAEngine()
        result = qa_engine.answer_question(document, question)

        QAMessage.objects.create(
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

        context = {
            "document": document,
            "question": result["question"],
            "answer": result["answer"],
            "cypher": result["cypher"],
            "rows": result["rows"],
            "provenance": result.get("provenance", []),
            "question_analysis": result.get("question_analysis", {}),
            "has_error": False,
        }

        response = render(
            request,
            "document_manager/components/qa_result.jinja",
            context=context,
        )

        # Trigger graph highlighting after the QA result is swapped into the thread.
        response["HX-Trigger-After-Swap"] = json.dumps(
            {
                "qaGraphHighlight": result.get(
                    "highlight",
                    {
                        "node_ids": [],
                        "edge_ids": [],
                        "focus": False,
                    },
                )
            }
        )

        return response

    except Exception as exc:
        context = {
            "document": document,
            "question": question,
            "answer": str(exc),
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

        response["HX-Trigger-After-Swap"] = json.dumps(
            {
                "qaGraphHighlight": {
                    "node_ids": [],
                    "edge_ids": [],
                    "focus": False,
                }
            }
        )

        return response


@login_required
def document_qa_page(request: HttpRequest, doc_id: int, session_id: int) -> HttpResponse:
    """
    Render the dedicated QA page for a document/session pair.
    """
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
        context=context,
    )


@login_required
def document_qa_sessions_page(request: HttpRequest, doc_id: int) -> HttpResponse:
    """
    Render the QA session picker page for a document.
    """
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
def create_qa_session(request: HttpRequest, doc_id: int) -> HttpResponse:
    """
    Create a new QA session for a document and redirect to the QA page.
    """
    document = get_object_or_404(Document, id=doc_id, user=request.user)

    session = QASession.objects.create(
        document=document,
        user=request.user,
        title=f"Conversation {document.qa_sessions.count() + 1}",
    )

    return redirect("document_manager:qa_page", doc_id=document.id, session_id=session.id)


@login_required
def graph_panel(request: HttpRequest, doc_id: int) -> HttpResponse:
    """
    Render the reloadable graph panel partial for the QA page.
    """
    document = get_object_or_404(Document, id=doc_id, user=request.user)

    return render(
        request,
        "document_manager/components/graph_panel.jinja",
        {
            "document": document,
        },
    )


@login_required
def document_logs_page(request: HttpRequest, doc_id: int) -> HttpResponse:
    """
    Render the processing log page for a document.
    """
    document = get_object_or_404(Document, id=doc_id, user=request.user)
    logs = document.processing_logs.all().order_by("created_at")

    return render(
        request,
        "document_manager/document_logs.jinja",
        {
            "document": document,
            "logs": logs,
        },
    )


@login_required
def download_document_logs(request: HttpRequest, doc_id: int) -> HttpResponse:
    """
    Download a document's processing logs as a plain-text file.
    """
    document = get_object_or_404(Document, id=doc_id, user=request.user)
    logs = document.processing_logs.all().order_by("created_at")

    lines: list[str] = []
    for log in logs:
        timestamp = log.created_at.strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"[{timestamp}] [{log.stage}] {log.message}")

    content = "\n".join(lines) if lines else "No processing logs available."

    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    safe_name = document.name.replace(" ", "_")
    response["Content-Disposition"] = (
        f'attachment; filename="{safe_name}_processing_logs.txt"'
    )
    return response
