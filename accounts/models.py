from django.db import models
from django.contrib.auth.models import User
from jobs.models import Company
from django.utils import timezone
from .ml import compute_resume_keywords


class CustomUser(models.Model):
    ROLE_CHOICES = [
        ('company', 'Company'),
        ('applicant', 'Applicant'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, default='applicant')
    company = models.ForeignKey(
        Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees"
    )

    def __str__(self):
        return self.user.username


def user_directory_path(instance, filename):
    return f'user_{instance.user.id}/{filename}'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    profile_picture = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    resume = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    skills = models.TextField(blank=True)  # Comma-separated list like "ReactJS,Python"
    created_at = models.DateTimeField(auto_now_add=True)
    dateofbirth = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    class Meta:
        get_latest_by = 'created_at'


class ResumeAnalysis(models.Model):
    """Stores extracted signals from an applicant's resume/profile for fast recommendations."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resume_analysis')
    skills_extracted = models.TextField(blank=True)  # comma separated
    summary = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    areas_to_improve = models.TextField(blank=True)
    analyzed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"ResumeAnalysis<{self.user.username}>"

    @staticmethod
    def analyze_from_profile(profile: 'UserProfile') -> 'ResumeAnalysis':
        """Very lightweight heuristic analyzer; replace with ML pipeline later."""
        user = profile.user
        # Prefer explicit skills field; fallback to simple placeholders
        raw_skills = (profile.skills or '').strip()
        resume_text = ''
        try:
            # If you want, OCR/PDF parsing could be plugged here
            resume_text = ''
        except Exception:
            resume_text = ''

        inferred, vec = compute_resume_keywords(raw_skills, resume_text)
        strengths_text = 'Experienced in: ' + ', '.join(inferred[:5]) if inferred else ''
        summary_text = f"Auto-analysis for {user.get_full_name() or user.username}." if user else ''
        improve_text = '' if inferred else 'Add more relevant skills to your profile.'

        instance, _ = ResumeAnalysis.objects.get_or_create(user=user)
        instance.skills_extracted = ', '.join(inferred)
        instance.summary = summary_text
        instance.strengths = strengths_text
        instance.areas_to_improve = improve_text
        instance.analyzed_at = timezone.now()
        instance.save()
        return instance


class Notification(models.Model):
    """Simple in-app notification for users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification<{self.user.username}: {self.title}>"
