import os
from django.db import models
from django.contrib.auth.models import User

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=255, default='My Resume')
    file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Phase 3 Extracted & Parsed Basic Data
    extracted_text = models.TextField(blank=True, null=True)
    extracted_email = models.CharField(max_length=255, blank=True, null=True)
    extracted_skills = models.JSONField(default=list, blank=True)
    extracted_education = models.JSONField(default=list, blank=True)
    extracted_projects = models.JSONField(default=list, blank=True)

    # Phase 4 AI Gemini Intelligence Output
    ai_analysis = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.username} - {self.filename} ({self.uploaded_at.strftime('%Y-%m-%d')})"

    @property
    def filename(self):
        return os.path.basename(self.file.name) if self.file else "No File"
