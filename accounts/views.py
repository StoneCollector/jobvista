import time
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from collections import Counter

from .forms import UserProfileForm, SignupForm
from .models import *
from .models import UserProfile
from jobs.models import Job, JobCategory, Company
from .ml import extract_skills_from_text


# Create your views here.
def signup(request):
    form = SignupForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            role = form.cleaned_data['role']
            dateofbirth = form.cleaned_data['dob']
            password = form.cleaned_data['password1']

            user = User.objects.create_user(username=username, password=password, email=email)
            CustomUser.objects.create(user=user, role=role)
            UserProfile.objects.create(user=user, dateofbirth=dateofbirth)
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        if request.user.customuser.role == 'company':
            return redirect('company_view')
        else:
            return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not User.objects.filter(username=username).exists():
            messages.error(request, 'Username does not exist')
            return redirect('login')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            temp = CustomUser.objects.get(user=user) if CustomUser.objects.filter(user=user).exists() else None
            if not temp or temp.role == 'applicant':
                return redirect('dashboard')
            if temp.role == 'company':
                if not temp.company:
                    return redirect("profile_completion")
                return redirect("company_view")
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile_edit(request):
    """View to edit user profile"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=request.user)

    if request.method == 'POST':
        print(request.POST)
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_view')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile
    }
    return render(request, 'accounts/profile_edit.html', context)


@login_required
def profile_view(request):
    """View to display user profile"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.info(request, 'Please complete your profile first.')
        return redirect('profile_edit')

    # Convert skills string to list for better display
    skills_list = []
    if profile.skills:
        skills_list = [skill.strip() for skill in profile.skills.split(',') if skill.strip()]

    context = {
        'profile': profile,
        'skills_list': skills_list
    }
    return render(request, 'accounts/profile_view.html', context)


def career_advice_view(request):
    if request.method == 'POST':
        resume_file = request.FILES.get('resume')
        if not resume_file:
            messages.error(request, 'Please upload a resume file.')
            return redirect('career_advice')

        try:
            resume_text = resume_file.read().decode('utf-8', errors='ignore')
        except Exception:
            messages.error(request, 'Could not read the uploaded file.')
            return redirect('career_advice')

        extracted_skills = extract_skills_from_text(resume_text)

        # Generate dynamic advice based on extracted skills
        advice = {
            'strengths': [],
            'improvements': [
                "Add a brief professional summary at the top to highlight your career goals.",
                "Use action verbs (e.g., 'Developed,' 'Managed,' 'Implemented') to describe accomplishments.",
                "Quantify achievements with numbers where possible (e.g., 'Increased efficiency by 15%')."
            ]
        }
        if extracted_skills:
            advice['strengths'].append(f"Great job highlighting your skills in: {', '.join(extracted_skills[:5])}.")
        else:
            advice['strengths'].append(
                "Your resume was successfully read. For better results, ensure key skills are clearly listed as text.")

        if len(extracted_skills) < 5:
            advice['improvements'].append(
                "Consider listing at least 5-7 core technical skills relevant to your target roles.")

        # Find and rank company matches based on skills
        companies = []
        if extracted_skills:
            skill_query = Q()
            for skill in extracted_skills:
                skill_query |= Q(description__icontains=skill) | Q(requirements__icontains=skill)

            matching_jobs = Job.objects.filter(skill_query, is_active=True).values('company_id')

            if matching_jobs.exists():
                company_ids = [job['company_id'] for job in matching_jobs]
                company_counts = Counter(company_ids)
                top_company_ids = [cid for cid, count in company_counts.most_common(5)]

                # Fetch companies and preserve order by match count
                company_map = {c.id: c for c in Company.objects.filter(id__in=top_company_ids)}
                companies = [company_map[cid] for cid in top_company_ids if cid in company_map]

        # Fallback to popular companies if no matches are found
        if not companies:
            companies = Company.objects.filter(status="approved").annotate(num_jobs=models.Count('jobs')).order_by(
                '-num_jobs')[:5]

        context = {
            'advice': advice,
            'companies': companies,
            'has_results': True,
            'extracted_skills': extracted_skills
        }
        return render(request, 'accounts/career_advice.html', context)

    return render(request, 'accounts/career_advice.html', {})


@login_required
def company_view(request):
    custom_user = getattr(request.user, 'customuser', None)
    company = getattr(custom_user, 'company', None) if custom_user else None

    if not company:
        messages.info(request, 'Please complete your company profile first.')
        return redirect('profile_completion')

    categories = JobCategory.objects.all().order_by('name')
    # Dynamic metrics for dashboard
    active_jobs_count = company.jobs.filter(is_active=True).count()
    closed_jobs_count = company.jobs.filter(is_active=False).count()
    applicants_count = 0
    try:
        from jobs.models import ApplyForJob
        applicants_count = ApplyForJob.objects.filter(job__company=company).count()
    except Exception:
        applicants_count = 0
    context = {
        'company': company,
        'logo': company.logo,
        'categories': categories,
        'job_employment_types': Job.EMPLOYMENT_TYPES,
        'job_experience_levels': Job.EXPERIENCE_LEVELS,
        'active_jobs_count': active_jobs_count,
        'closed_jobs_count': closed_jobs_count,
        'applicants_count': applicants_count,
    }
    return render(request, 'Company/post_job.html', context)