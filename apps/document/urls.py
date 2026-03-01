from django.urls import path
from . import views

app_name = "document"


urlpatterns = [
    path("upload/", views.upload_document, name="upload_document"),
    path("list/", views.document_list, name="document_list"),
    path("status/<int:pk>", views.document_status, name="status"),
    ]
    