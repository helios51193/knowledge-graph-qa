from django import forms
from .models import Document
from .services.llm_availbility import check_llm_availability

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
    
    def clean_llm_used(self):
        llm_used = self.cleaned_data.get("llm_used")
        is_available, error_message = check_llm_availability(llm_used)
        if not is_available:
            raise forms.ValidationError(error_message)
        
        return llm_used


