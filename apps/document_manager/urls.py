from django.urls import path
from . import views

app_name = "document_manager"

urlpatterns = [
                # partials
                path("component/document-table", views.document_table, name="document_table"),
                path("component/upload-document", views.upload_document, name="upload_document"),
                # api
                path("api/delete-document/<int:doc_id>", views.delete_document, name="delete_document"),
                path("api/process-document/<int:doc_id>", views.process_document_view, name="process_document"),

                # view
                path("dashboard", views.document_dashboard, name="dashboard"),]