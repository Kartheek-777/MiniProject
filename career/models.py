from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class CareerRoadmap(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roadmaps', null=True, blank=True)
    title = models.CharField(max_length=255, default='Personalized AI Career Roadmap')
    target_role = models.CharField(max_length=150, default='Software Engineer')
    current_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    roadmap_json = models.JSONField(default=dict, blank=True)
    difficulty_level = models.CharField(max_length=50, default='Intermediate')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} - {self.target_role} ({self.difficulty_level}) Roadmap"

    @property
    def roadmap_data(self):
        """Backward compatibility helper property."""
        return self.roadmap_json


class DailyTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_tasks')
    date = models.DateField(default=timezone.now)
    task = models.TextField()
    is_completed = models.BooleanField(default=False)
    source_week = models.CharField(max_length=100, default='Week 1')
    day_number = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['date', 'day_number', 'id']

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        status = "Done" if self.is_completed else "Pending"
        return f"{user_str} - Day {self.day_number} ({self.date}) [{status}]: {self.task[:30]}"

