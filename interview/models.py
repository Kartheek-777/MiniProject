from django.db import models
from django.contrib.auth.models import User

class MockInterviewSession(models.Model):
    MODE_CHOICES = (
        ('Full Interview', 'Full Technical & HR Interview'),
        ('HR Screening', 'Phase 1: HR Screening'),
        ('Core CS', 'Phase 2: Core CS Round'),
        ('AI/ML + GenAI', 'Phase 3: AI/ML & Generative AI'),
        ('Project Deep Dive', 'Phase 4: Project Deep Dive'),
        ('System Design', 'Phase 5: System Design'),
    )

    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interview_sessions')
    target_role = models.CharField(max_length=150, default='AI/ML Trainee | Generative AI Fresher')
    interview_mode = models.CharField(max_length=50, choices=MODE_CHOICES, default='Full Interview')
    current_phase = models.CharField(max_length=50, default='HR Screening')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    completed = models.BooleanField(default=False)
    evaluation_data = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.target_role} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"

class InterviewMessage(models.Model):
    SENDER_CHOICES = (
        ('interviewer', 'Interviewer'),
        ('candidate', 'Candidate'),
    )

    session = models.ForeignKey(MockInterviewSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    message = models.TextField()
    round_name = models.CharField(max_length=50, default='HR Screening')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.round_name}] {self.sender}: {self.message[:30]}"

