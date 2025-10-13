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

# Handle optional imports gracefully
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    fitz = None

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    docx = None

from .forms import UserProfileForm, SignupForm
from .models import *
from .models import UserProfile
from jobs.models import Job, JobCategory, Company

# Handle AI analyzer imports gracefully
try:
    from .ai_analyzer import extract_skills, infer_skills_from_text, resume_quality, check_ats_friendliness
    HAS_AI_ANALYZER = True
except ImportError:
    HAS_AI_ANALYZER = False
    # Create dummy functions
    def extract_skills(text): return []
    def infer_skills_from_text(text): return []
    def resume_quality(text): return {"suggestions": [], "readability": {}}
    def check_ats_friendliness(text): return {"has_contact_info": False, "uses_standard_sections": False, "warnings": []}


def _extract_text_from_file(file_path):
    """Extract raw text from a PDF or DOCX file."""
    ext = file_path.rsplit(".", 1)[1].lower()
    text = ""
    try:
        if ext == "pdf" and HAS_PYMUPDF:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text("text") + "\n"
        elif ext == "docx" and HAS_DOCX:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        else:
            # Fallback: return empty string if libraries not available
            return ""
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
            return redirect('company_dashboard')
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
                return redirect("company_dashboard")
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
    # Simple static version for now
    context = {
        'has_results': False,
    }
    return render(request, 'accounts/career_advice.html', context)


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
    # Get company's jobs
    jobs = company.jobs.all().order_by('-created_at')
    
    context = {
        'company': company,
        'jobs': jobs,
        'active_jobs_count': active_jobs_count,
        'closed_jobs_count': closed_jobs_count,
        'applicants_count': applicants_count,
    }
    return render(request, 'Company/company_jobs.html', context)


@login_required
def job_alerts(request):
    """Manage job alerts"""
    alerts = JobAlert.objects.filter(user=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            keywords = request.POST.get('keywords', '').strip()
            location = request.POST.get('location', '').strip()
            salary_min = request.POST.get('salary_min', '').strip()
            salary_max = request.POST.get('salary_max', '').strip()
            frequency = request.POST.get('frequency', 'weekly')
            
            if keywords:
                alert = JobAlert.objects.create(
                    user=request.user,
                    keywords=keywords,
                    location=location,
                    salary_min=float(salary_min) if salary_min else None,
                    salary_max=float(salary_max) if salary_max else None,
                    frequency=frequency
                )
                messages.success(request, 'Job alert created successfully!')
                return redirect('job_alerts')
            else:
                messages.error(request, 'Please provide at least one keyword.')
        
        elif action == 'toggle':
            alert_id = request.POST.get('alert_id')
            try:
                alert = JobAlert.objects.get(id=alert_id, user=request.user)
                alert.is_active = not alert.is_active
                alert.save()
                messages.success(request, f'Job alert {"activated" if alert.is_active else "deactivated"}.')
            except JobAlert.DoesNotExist:
                messages.error(request, 'Job alert not found.')
        
        elif action == 'delete':
            alert_id = request.POST.get('alert_id')
            try:
                alert = JobAlert.objects.get(id=alert_id, user=request.user)
                alert.delete()
                messages.success(request, 'Job alert deleted successfully.')
            except JobAlert.DoesNotExist:
                messages.error(request, 'Job alert not found.')
    
    return render(request, 'accounts/job_alerts.html', {'alerts': alerts})