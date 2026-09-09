from django import forms
from resume_analyzer.models import Resume
from .models import CareerRoadmap

class RoadmapForm(forms.ModelForm):
    title = forms.CharField(
        max_length=255,
        required=True,
        initial='3-Month Placement Roadmap',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. SDE 90-Day Acceleration Roadmap'})
    )
    target_role = forms.CharField(
        max_length=150,
        required=True,
        initial='Software Development Engineer',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Software Development Engineer, Data Engineer'})
    )
    resume = forms.ModelChoiceField(
        queryset=Resume.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select your uploaded resume to auto-populate existing skills and gap analysis.'
    )
    manual_missing_skills = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Docker, AWS, System Design, Microservices'}),
        help_text='Comma-separated target skills you wish to master over the next 90 days.'
    )

    class Meta:
        model = CareerRoadmap
        fields = ['title', 'target_role']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['resume'].queryset = Resume.objects.filter(user=user)
