import os
from django import forms
from django.core.exceptions import ValidationError
from .models import Resume

MAX_FILE_SIZE_MB = 5
ALLOWED_EXTENSIONS = ['.pdf']

class ResumeUploadForm(forms.ModelForm):
    title = forms.CharField(
        max_length=255, 
        required=False, 
        initial='Software Engineering Resume',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. SDE Resume 2026'})
    )
    file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'})
    )

    class Meta:
        model = Resume
        fields = ['title', 'file']

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise ValidationError("Only PDF files (.pdf) are allowed.")
            if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise ValidationError(f"File size exceeds maximum limit of {MAX_FILE_SIZE_MB}MB.")
        return file
