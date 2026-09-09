from django.db import models
from django.contrib.auth.models import User

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    college = models.CharField(max_length=255, blank=True, default='Engineering Institute')
    degree = models.CharField(max_length=100, default='B.Tech')
    branch = models.CharField(max_length=100, default='Computer Science & Engineering')
    graduation_year = models.IntegerField(default=2026)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    bio = models.TextField(blank=True)
    target_role = models.CharField(max_length=150, blank=True, default='Software Engineer')

    # Profile Picture
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    # AI Summary Cache
    ai_summary = models.TextField(blank=True, null=True)
    ai_summary_generated_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        full_name = self.user.get_full_name() or self.user.username
        return f"{full_name} - {self.branch} ({self.graduation_year})"

    @property
    def completion_percentage(self):
        """Calculate profile completeness percentage based on bio, target_role, skills, resume, projects, and bio."""
        has_resume = hasattr(self.user, 'resumes') and self.user.resumes.exists()
        latest_resume = self.user.resumes.first() if has_resume else None
        has_skills = bool(latest_resume and latest_resume.extracted_skills) if latest_resume else False
        has_projects = bool(latest_resume and latest_resume.extracted_projects) if latest_resume else False

        checks = [
            bool(self.user.first_name and self.user.last_name),
            bool(self.user.email),
            bool(self.target_role and self.target_role.strip() != ''),
            bool(self.bio and self.bio.strip() != ''),
            bool(self.phone_number and self.phone_number.strip() != ''),
            bool(self.cgpa),
            has_resume,
            has_skills,
            has_projects,
        ]
        filled = sum(1 for c in checks if c)
        return int((filled / len(checks)) * 100)

    @property
    def missing_fields(self):
        """Returns dynamic list of unfilled fields for profile completion engine."""
        missing = []
        if not (self.user.first_name and self.user.last_name):
            missing.append("Full Name")
        if not self.target_role:
            missing.append("Target Role")
        if not self.bio:
            missing.append("Professional Bio")
        if not self.phone_number:
            missing.append("Phone Number")
        if not self.cgpa:
            missing.append("CGPA")
        
        has_resume = hasattr(self.user, 'resumes') and self.user.resumes.exists()
        if not has_resume:
            missing.append("Resume Upload")
        else:
            latest = self.user.resumes.first()
            if not (latest and latest.extracted_skills):
                missing.append("Skills Extraction")
            if not (latest and latest.extracted_projects):
                missing.append("Project History")
        return missing
