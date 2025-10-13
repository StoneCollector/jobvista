from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Job
from accounts.models import JobAlert, Notification, UserProfile


@receiver(pre_save, sender=Job)
def fix_job_slug(sender, instance, **kwargs):
    """Automatically fix job slugs to remove problematic characters"""
    if instance.slug and ('/' in instance.slug or '\\' in instance.slug):
        # Create a safe slug
        safe_title = instance.title.replace('/', '-').replace('\\', '-').replace(' ', '-')
        safe_company = instance.company.name.replace('/', '-').replace('\\', '-').replace(' ', '-')
        new_slug = slugify(f"{safe_title}-{safe_company}")
        
        # Ensure uniqueness
        original_slug = new_slug
        counter = 1
        while Job.objects.filter(slug=new_slug).exclude(id=instance.id).exists():
            new_slug = f"{original_slug}-{counter}"
            counter += 1
        
        instance.slug = new_slug


@receiver(post_save, sender=Job)
def send_job_alerts_on_creation(sender, instance, created, **kwargs):
    """Automatically send job alerts when a new job is posted"""
    if not created or not instance.is_active:
        return
    
    try:
        # Get all active job alerts
        job_alerts = JobAlert.objects.filter(is_active=True)
        
        for alert in job_alerts:
            # Check if job matches alert criteria
            matches = False
            
            # Check keywords match
            if alert.keywords:
                keywords = [kw.strip().lower() for kw in alert.keywords.split(',') if kw.strip()]
                for keyword in keywords:
                    if (keyword in instance.title.lower() or 
                        keyword in instance.description.lower() or 
                        keyword in instance.requirements.lower()):
                        matches = True
                        break
            
            # Check location match
            if alert.location and alert.location.lower() in instance.location.lower():
                matches = True
            
            # Check salary range match
            if alert.salary_min and instance.salary_min and instance.salary_min >= alert.salary_min:
                matches = True
            if alert.salary_max and instance.salary_max and instance.salary_max <= alert.salary_max:
                matches = True
            
            if matches:
                # Create notification for the user
                Notification.objects.create(
                    user=alert.user,
                    title=f"New Job Alert: {instance.title}",
                    message=f"A new job at {instance.company.name} matches your alert criteria!",
                    link=instance.get_absolute_url()
                )
        
        # Also send alerts based on user skills (similar to management command)
        users_with_skills = User.objects.filter(
            userprofile__skills__isnull=False,
            userprofile__skills__gt=''
        ).select_related('userprofile')
        
        for user in users_with_skills:
            try:
                profile = user.userprofile
                if not profile.skills:
                    continue
                
                # Get user's skills
                user_skills = [skill.strip().lower() for skill in profile.skills.split(',') if skill.strip()]
                
                if not user_skills:
                    continue
                
                # Check if job matches user skills
                skill_match = False
                for skill in user_skills[:3]:  # Check first 3 skills
                    if (skill in instance.title.lower() or 
                        skill in instance.description.lower() or 
                        skill in instance.requirements.lower()):
                        skill_match = True
                        break
                
                if skill_match:
                    # Create notification
                    Notification.objects.create(
                        user=user,
                        title=f"New Job Matches Your Skills!",
                        message=f"Check out this new {instance.title} position at {instance.company.name}",
                        link=instance.get_absolute_url()
                    )
                    
            except Exception as e:
                # Log error but don't break the job creation
                print(f"Error sending skill-based alert to {user.username}: {str(e)}")
                
    except Exception as e:
        # Log error but don't break the job creation
        print(f"Error sending job alerts: {str(e)}")
