from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import Document
from .forms import DocumentUploadForm


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

            return redirect("document_dashboard")

    else:
        form = DocumentUploadForm()

    return render(
        request,
        "document_manager/components/upload_modal.jinja",
        {"form": form}
    )
