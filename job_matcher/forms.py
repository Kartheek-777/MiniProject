from django import forms
from resume_analyzer.models import Resume
from .models import JobMatch

class JobMatchForm(forms.ModelForm):
    job_title = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Software Development Engineer (SDE)'})
    )
    company_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. TechCorp / Startup'})
    )
    job_description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Paste the full Job Description (JD) text here...'})
    )
    resume = forms.ModelChoiceField(
        queryset=Resume.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = JobMatch
        fields = ['job_title', 'company_name', 'job_description', 'resume']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['resume'].queryset = Resume.objects.filter(user=user)
