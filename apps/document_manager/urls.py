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
                path("api/ask-question/<int:doc_id>/<int:session_id>", views.ask_question, name="ask_question"),
                path("api/create-qa-session/<int:doc_id>", views.create_qa_session, name="create_qa_session"),


                # view
                path("qa/<int:doc_id>", views.document_qa_sessions_page, name="qa_sessions"),
                path("qa/<int:doc_id>/<int:session_id>", views.document_qa_page, name="qa_page"),
                
                path("dashboard", views.document_dashboard, name="dashboard"),]