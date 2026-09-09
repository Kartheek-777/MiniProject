from django import forms
from .models import MockInterviewSession

class StartInterviewForm(forms.ModelForm):
    class Meta:
        model = MockInterviewSession
        fields = ['target_role', 'interview_mode']
        widgets = {
            'target_role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. AI/ML Trainee | Generative AI Fresher'
            }),
            'interview_mode': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
