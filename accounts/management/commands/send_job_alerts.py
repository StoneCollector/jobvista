from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile, Notification
from jobs.models import Job
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Send job alerts to users based on their skills and preferences'

    def handle(self, *args, **options):
        # Get users with profiles and skills
        users_with_skills = User.objects.filter(
            userprofile__skills__isnull=False,
            userprofile__skills__gt=''
        ).select_related('userprofile')

        new_jobs_count = 0
        alerts_sent = 0

        for user in users_with_skills:
            try:
                profile = user.userprofile
                if not profile.skills:
                    continue

                # Get user's skills
                user_skills = [skill.strip().lower() for skill in profile.skills.split(',') if skill.strip()]
                
                if not user_skills:
                    continue

                # Find jobs posted in the last 24 hours that match user skills
                yesterday = timezone.now() - timedelta(days=1)
                matching_jobs = Job.objects.filter(
                    created_at__gte=yesterday,
                    is_active=True
                ).filter(
                    Q(description__icontains=user_skills[0]) |
                    Q(requirements__icontains=user_skills[0]) |
                    Q(title__icontains=user_skills[0])
                )

                # Add more skill matches
                for skill in user_skills[1:3]:  # Check first 3 skills
                    matching_jobs = matching_jobs.filter(
                        Q(description__icontains=skill) |
                        Q(requirements__icontains=skill) |
                        Q(title__icontains=skill)
                    )

                if matching_jobs.exists():
                    job_count = matching_jobs.count()
                    new_jobs_count += job_count
                    
                    # Create notification
                    Notification.objects.create(
                        user=user,
                        title=f"🎯 {job_count} New Job{'s' if job_count > 1 else ''} Match Your Skills!",
                        message=f"We found {job_count} new job{'s' if job_count > 1 else ''} that match your skills: {', '.join(user_skills[:3])}",
                        link="/"
                    )
                    alerts_sent += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing user {user.username}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully sent {alerts_sent} job alerts for {new_jobs_count} new jobs'
            )
        )
