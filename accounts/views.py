import time
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q, Count
from collections import Counter
import os
import tempfile
import fitz  # PyMuPDF
import docx

from .forms import UserProfileForm, SignupForm
from .models import *
from .models import UserProfile
from jobs.models import Job, JobCategory, Company
from .ai_analyzer import extract_skills, infer_skills_from_text, resume_quality, check_ats_friendliness


def _extract_text_from_file(file_path):
    """Extract raw text from a PDF or DOCX file."""
    ext = file_path.rsplit(".", 1)[1].lower()
    text = ""
    try:
        if ext == "pdf":
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text("text") + "\n"
        elif ext == "docx":
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return None
    return text.strip()


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

        # Save to a temporary file to read it
        fd, temp_path = tempfile.mkstemp(suffix=f"_{resume_file.name}")
        try:
            with os.fdopen(fd, 'wb') as tmp:
                for chunk in resume_file.chunks():
                    tmp.write(chunk)

            resume_text = _extract_text_from_file(temp_path)
        finally:
            os.remove(temp_path)

        if not resume_text:
            messages.error(request,
                           'Could not extract text from the uploaded file. Please ensure it is not an image-based PDF or corrupted.')
            return redirect('career_advice')

        # --- AI Analysis ---
        explicit_skills = extract_skills(resume_text)
        inferred_skills = infer_skills_from_text(resume_text)
        all_skills = sorted(list(set(explicit_skills + inferred_skills)))

        quality_report = resume_quality(resume_text)
        ats_report = check_ats_friendliness(resume_text)

        # --- Company Matching ---
        companies = []
        if all_skills:
            # This Q object is for filtering the Company model through its jobs
            company_skill_query = Q()
            for skill in all_skills:
                company_skill_query |= Q(jobs__description__icontains=skill) | Q(jobs__requirements__icontains=skill)

            # This Q object is for filtering Job models directly
            job_skill_query = Q()
            for skill in all_skills:
                job_skill_query |= Q(description__icontains=skill) | Q(requirements__icontains=skill)

            # Find companies that are approved and have active jobs matching the skills
            matching_companies = Company.objects.filter(
                company_skill_query, status="approved", jobs__is_active=True
            ).distinct()

            # Score companies based on the number of matching jobs
            company_scores = []
            for company in matching_companies:
                # Use the JOB-specific query here
                job_matches = company.jobs.filter(job_skill_query, is_active=True).count()
                if job_matches > 0:
                    company_scores.append((company, job_matches))

            # Sort by score and take top 5
            company_scores.sort(key=lambda x: x[1], reverse=True)
            companies = [company for company, score in company_scores[:5]]

        # Fallback to popular companies if no matches are found
        if not companies:
            companies = Company.objects.filter(status="approved").annotate(num_jobs=Count('jobs')).order_by(
                '-num_jobs')[:5]

        context = {
            'quality_report': quality_report,
            'ats_report': ats_report,
            'companies': companies,
            'has_results': True,
            'explicit_skills': explicit_skills,
            'inferred_skills': inferred_skills,
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