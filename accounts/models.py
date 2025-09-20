from django.db import models
from django.contrib.auth.models import User
from jobs.models import Company


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
