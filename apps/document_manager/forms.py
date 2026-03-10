from django import forms
from .models import Document

class DocumentUploadForm(forms.ModelForm):

    class Meta:
        model = Document
        fields = [
            "name",
            "file",
            "llm_used"
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "Enter document name"
            }),

            "file": forms.ClearableFileInput(attrs={
                "class": "file-input"
            }),

            "llm_used": forms.Select(attrs={
                "class": "select"
            }),
        }

