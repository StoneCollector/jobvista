from django.contrib.auth.models import User
from django.utils import timezone

from django.db import models
from django.urls import reverse


# Create your models here.
class Company(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    SIZE_CHOICES = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1000+', '1000+ employees'),
    ]

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    location = models.CharField(max_length=200)
    company_size = models.CharField(max_length=20, choices=SIZE_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Companies"


class JobCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Job Categories"


class Job(models.Model):
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
    ]

    EXPERIENCE_LEVELS = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE, related_name='jobs')
    description = models.TextField()
    requirements = models.TextField()
    responsibilities = models.TextField()
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS)
    location = models.CharField(max_length=200)
    remote_available = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    application_deadline = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} at {self.company.name}"

    def get_absolute_url(self):
        try:
            return reverse('job_detail', kwargs={'slug': self.slug})
        except:
            # Fallback to a safe URL if slug is problematic
            safe_slug = self.slug.replace('/', '-').replace('\\', '-')
            return reverse('job_detail', kwargs={'slug': safe_slug})

    def is_expired(self):
        if self.application_deadline:
            return timezone.now() > self.application_deadline
        return False

    class Meta:
        ordering = ['-created_at']


class ApplyForJob(models.Model):
    STATUS_CHOICES = [
        ('new', 'New Applicant'),
        ('screening', 'Screening'),
        ('interviewing', 'Interviewing'),
        ('offer', 'Offer'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applied')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applied')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    ai_match_score = models.IntegerField(default=0, help_text="AI-calculated match score (0-100)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')
        verbose_name = "Job application"
        verbose_name_plural = "Job applications"

    def __str__(self):
        return f"{self.user.username} applied for {self.job.title}"

    @staticmethod
    def is_applied(user, job):
        """
        Helper method to check if a job is bookmarked by a user.
        Returns True or False.
        """
        return ApplyForJob.objects.filter(user=user, job=job).exists()

    @staticmethod
    def get_applied_job_ids(user):
        """
        Returns a list of job IDs bookmarked by the user.
        Useful for displaying icons in the template.
        """
        return ApplyForJob.objects.filter(user=user).values_list('job_id', flat=True)
