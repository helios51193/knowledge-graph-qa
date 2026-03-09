from django import forms

class DocumentUploadForm(forms.Form):

    name = forms.CharField(
        label="Document Name",
        widget=forms.TextInput(attrs={
            "class": "input",
            "placeholder": "Enter document name"
        })
    )

    file = forms.FileField(
        label="Upload File",
        widget=forms.ClearableFileInput(attrs={
            "class": "file-input",
            "accept": ".pdf,.txt"
        })
    )

    llm_used = forms.ChoiceField(
        label="LLM Model",
        choices=[
            ("llama3", "Llama 3"),
            ("mistral", "Mistral"),
            ("gpt4", "GPT-4")
        ],
        widget=forms.Select(attrs={
            "class": "select"
        })
    )