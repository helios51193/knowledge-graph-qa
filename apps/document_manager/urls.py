from django.urls import path
from . import views

app_name = "document_manager"

urlpatterns = [
                path("component/document-table", views.document_table, name="document_table"),
                path("component/upload-document", views.upload_document, name="upload_document"),
                path("dashboard", views.document_dashboard, name="dashboard"),]