from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import JobMatch, SkillGapHistory

@receiver(post_save, sender=JobMatch)
def auto_track_skill_gap_history(sender, instance, created, **kwargs):
    """
    Signal handler: Automatically creates a SkillGapHistory entry whenever a JobMatch is run.
    """
    if created:
        SkillGapHistory.objects.create(
            user=instance.user,
            job_title=instance.job_title,
            company_name=instance.company_name,
            skills_missing=instance.missing_skills if isinstance(instance.missing_skills, list) else [],
            skills_matched=instance.matched_skills if isinstance(instance.matched_skills, list) else [],
            match_score=float(instance.match_score)
        )
