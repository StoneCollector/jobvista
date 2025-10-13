from django.core.management.base import BaseCommand
from django.utils.text import slugify
from jobs.models import Job


class Command(BaseCommand):
    help = 'Fix job slugs that contain invalid characters'

    def handle(self, *args, **options):
        jobs = Job.objects.all()
        fixed_count = 0
        
        for job in jobs:
            # Check if slug contains problematic characters
            if '/' in job.slug or '\\' in job.slug:
                # Create a new safe slug
                safe_title = job.title.replace('/', '-').replace('\\', '-').replace(' ', '-')
                safe_company = job.company.name.replace('/', '-').replace('\\', '-').replace(' ', '-')
                new_slug = slugify(f"{safe_title}-{safe_company}")
                
                # Ensure uniqueness
                original_slug = new_slug
                counter = 1
                while Job.objects.filter(slug=new_slug).exclude(id=job.id).exists():
                    new_slug = f"{original_slug}-{counter}"
                    counter += 1
                
                # Update the slug
                old_slug = job.slug
                job.slug = new_slug
                job.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Fixed slug: {old_slug} -> {new_slug}')
                )
                fixed_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully fixed {fixed_count} job slugs')
        )
