from django.db import models
from django.contrib.auth.models import User
from resume_analyzer.models import Resume

class JobDescription(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    description_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.company}"


class JobMatch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_matches')
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='job_matches')
    job_title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    job_description = models.TextField()

    # Rule-Based Match Metrics
    match_score = models.IntegerField(default=0)
    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)

    # AI Enhancement Insights (Gemini)
    fit_level = models.CharField(max_length=50, default='Moderate Fit')
    match_summary = models.TextField(blank=True, null=True)
    recommendations = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.job_title} ({self.match_score}%)"


class SkillGapHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_gap_histories')
    job_title = models.CharField(max_length=255, default='Software Engineer')
    company_name = models.CharField(max_length=255, blank=True, null=True)
    skills_missing = models.JSONField(default=list, blank=True)
    skills_matched = models.JSONField(default=list, blank=True)
    match_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} - {self.job_title} ({self.match_score}%) at {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class JobListing(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=150, default='Remote / Hybrid')
    description = models.TextField()
    skills_required = models.JSONField(default=list, blank=True)
    apply_link = models.URLField(max_length=500, default='https://linkedin.com/jobs')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company}"


class JobApplicationMatch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_application_matches')
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='application_matches')
    match_score = models.FloatField(default=0.0)
    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-match_score']

    def __str__(self):
        return f"{self.user.username} - {self.job.title} ({self.match_score}%)"


class ApplicationAssist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='application_assists')
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='assists')
    cover_letter = models.TextField()
    suggestions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Assist for {self.user.username} -> {self.job.title}"
