from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Job


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
