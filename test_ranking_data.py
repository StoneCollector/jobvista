#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JobSite.settings')
django.setup()

from jobs.models import ApplyForJob
from accounts.models import UserProfile, CustomUser
from jobs.views import calculate_skills_match, calculate_experience_level, calculate_resume_completeness

print('Testing AI Ranking Data Generation...')

# Get a test application
application = ApplyForJob.objects.select_related('user', 'job').first()
if application:
    print(f'Application: {application.user.username} for {application.job.title}')
    
    try:
        profile = UserProfile.objects.get(user=application.user)
        print(f'Profile: {profile.first_name} {profile.last_name}')
        
        # Test ranking data generation
        ranking_data = {
            'score': 75,
            'profile': profile,
            'skills_match': calculate_skills_match(application.job, profile),
            'experience_level': calculate_experience_level(profile),
            'resume_completeness': calculate_resume_completeness(profile)
        }
        
        print(f'Ranking Data: {ranking_data}')
        
        # Test if attributes can be set
        application.ai_match_score = 75
        application.ai_ranking_data = ranking_data
        
        print(f'AI Match Score: {application.ai_match_score}')
        print(f'AI Ranking Data: {application.ai_ranking_data}')
        
    except UserProfile.DoesNotExist:
        print('No profile found')
else:
    print('No applications found')
