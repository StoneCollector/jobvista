from django.db import models
from jobs.models import Job
from django.contrib.auth.models import User

class JobBookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')
        verbose_name = "Job Bookmark"
        verbose_name_plural = "Job Bookmarks"

    def __str__(self):
        return f"{self.user.username} bookmarked {self.job.title}"

    @staticmethod
    def is_bookmarked(user, job):
        """
        Helper method to check if a job is bookmarked by a user.
        Returns True or False.
        """
        return JobBookmark.objects.filter(user=user, job=job).exists()

    @staticmethod
    def get_bookmarked_job_ids(user):
        """
        Returns a list of job IDs bookmarked by the user.
        Useful for displaying icons in the template.
        """
        return JobBookmark.objects.filter(user=user).values_list('job_id', flat=True)
