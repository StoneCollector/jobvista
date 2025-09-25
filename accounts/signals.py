from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile, ResumeAnalysis, Notification
from jobs.models import ApplyForJob


@receiver(post_save, sender=UserProfile)
def analyze_resume_on_profile_save(sender, instance: UserProfile, created: bool, **kwargs):
    # Analyze on create and on updates when resume/skills present
    try:
        if instance.resume or (instance.skills or '').strip():
            ResumeAnalysis.analyze_from_profile(instance)
    except Exception:
        # Avoid blocking user save; log if you have logging configured
        pass


@receiver(post_save, sender=ApplyForJob)
def notify_status_change(sender, instance: ApplyForJob, created: bool, **kwargs):
    if created:
        return
    # Notify applicant when status changes
    try:
        Notification.objects.create(
            user=instance.user,
            title='Application Status Updated',
            message=f"Your application for '{instance.job.title}' is now '{instance.get_status_display()}'.",
            link=instance.job.get_absolute_url(),
        )
    except Exception:
        pass


