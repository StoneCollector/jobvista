from django.shortcuts import render, get_object_or_404
from .models import *
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from bookmarks.models import *
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
import os
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import ApplyForJob, Company, Job, JobCategory
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile


# Create your views here.
def job_list(request):
    jobs = Job.objects.filter(is_active=True).select_related('company', 'category')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(company__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Filter by category
    category_slug = request.GET.get('category', '')
    if category_slug:
        jobs = jobs.filter(category__slug=category_slug)

    # Filter by employment type
    employment_type = request.GET.get('employment_type', '')
    if employment_type:
        jobs = jobs.filter(employment_type=employment_type)

    # Filter by location
    location = request.GET.get('location', '')
    if location:
        jobs = jobs.filter(location__icontains=location)

    # New: Filter by experience levels (multi-select)
    experience_levels = request.GET.getlist('experience')
    if experience_levels:
        jobs = jobs.filter(experience_level__in=experience_levels)

    # New: Salary range filters
    salary_min_param = request.GET.get('salary_min', '')
    salary_max_param = request.GET.get('salary_max', '')
    if salary_min_param:
        try:
            salary_min_val = float(salary_min_param)
            jobs = jobs.filter(
                Q(salary_min__gte=salary_min_val) | Q(salary_max__gte=salary_min_val)
            )
        except ValueError:
            pass
    if salary_max_param:
        try:
            salary_max_val = float(salary_max_param)
            jobs = jobs.filter(
                Q(salary_max__lte=salary_max_val) | Q(salary_min__lte=salary_max_val)
            )
        except ValueError:
            pass

    # New: Date posted filter (last N days)
    date_posted = request.GET.get('date_posted', '')
    if date_posted in ['1', '7', '30']:
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=int(date_posted))
        jobs = jobs.filter(created_at__gte=cutoff)

    # New: Remote only
    remote_only = request.GET.get('remote', '') == '1'
    if remote_only:
        jobs = jobs.filter(remote_available=True)

    # Sorting
    sort = request.GET.get('sort', 'relevance')
    if sort == 'date':
        jobs = jobs.order_by('-created_at')
    elif sort == 'salary_high':
        jobs = jobs.order_by('-salary_max', '-salary_min')
    elif sort == 'salary_low':
        jobs = jobs.order_by('salary_min', 'salary_max')
    # else 'relevance' keeps default ordering

    total_count = jobs.count()

    # Pagination
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Featured companies derived from visible jobs with counts
    company_counts_qs = jobs.values('company_id').annotate(open_jobs=Count('id')).order_by('-open_jobs')[:6]
    company_id_to_count = {row['company_id']: row['open_jobs'] for row in company_counts_qs}
    featured_companies = Company.objects.filter(id__in=company_id_to_count.keys())
    featured_company_rows = [
        {
            'company': company,
            'open_jobs': company_id_to_count.get(company.id, 0),
        }
        for company in featured_companies
    ]

    # Category job counts for Browse by Category
    categories_with_counts = JobCategory.objects.annotate(jobs_count=Count('jobs')).order_by('name')

    # Trending tags from top categories by job count
    trending_tags = [c.name for c in categories_with_counts.order_by('-jobs_count')[:6]]

    date_posted_options = [('1','Last 24 hours'),('7','Last 7 days'),('30','Last 30 days')]

    # Dynamic hero
    hero_title = "Find Your Dream Job Today"
    if request.user.is_authenticated:
        last_query = request.GET.get('search') or request.session.get('last_search')
        if last_query:
            hero_title = f"Welcome back, {request.user.first_name or request.user.username}. New matches for '{last_query}'."
            request.session['last_search'] = last_query

    # Match score using cosine similarity; prefer ResumeAnalysis, fallback to profile
    if request.user.is_authenticated:
        try:
            from accounts.models import ResumeAnalysis
            from accounts.ml import compute_resume_keywords, score_job_match
            from accounts.ml_tf import HAS_TF, score_job_match_tf
            analysis = getattr(request.user, 'resume_analysis', None)
            skills_src = analysis.skills_extracted if (analysis and (analysis.skills_extracted or '').strip()) else getattr(request.user.userprofile, 'skills', '')
            user_skills, resume_vec = compute_resume_keywords(skills_src, '')
            if resume_vec:
                for job in page_obj:
                    text = f"{job.title} {job.description} {job.requirements} {job.responsibilities}"
                    if HAS_TF:
                        # Compose a small resume text from skills for TF vectorization
                        resume_text = ' '.join(user_skills)
                        score = score_job_match_tf(resume_text, text)
                    else:
                        score = score_job_match(resume_vec, text)
                    setattr(job, 'match_score', score)
        except Exception:
            pass

    context = {
        'page_obj': page_obj,
        'categories': categories_with_counts,
        'employment_types': Job.EMPLOYMENT_TYPES,
        'experience_filter_options': Job.EXPERIENCE_LEVELS,
        'date_posted_options': date_posted_options,
        'search_query': search_query,
        'selected_category': category_slug,
        'selected_employment_type': employment_type,
        'selected_location': location,
        'selected_experience_levels': experience_levels,
        'salary_min_value': salary_min_param,
        'salary_max_value': salary_max_param,
        'selected_date_posted': date_posted,
        'selected_remote': '1' if remote_only else '',
        'featured_company_rows': featured_company_rows,
        'trending_tags': trending_tags,
        'selected_sort': sort,
        'total_count': total_count,
        'hero_title': hero_title,
    }
    return render(request, 'landing.html', context)


def job_detail(request, slug):
    job = get_object_or_404(Job, slug=slug, is_active=True)

    # Check if user has bookmarked this job
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = JobBookmark.objects.filter(user=request.user, job=job).exists()

    # Get related jobs
    related_jobs = Job.objects.filter(
        category=job.category,
        is_active=True
    ).exclude(id=job.id)[:5]

    context = {
        'job': job,
        'is_bookmarked': is_bookmarked,
        'related_jobs': related_jobs,
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
def apply_job(request, slug):
    job = get_object_or_404(Job, slug=slug, is_active=True)

    if request.method == 'POST':
        # prevent duplicate applications
        if ApplyForJob.objects.filter(user=request.user, job=job).exists():
            messages.info(request, 'You have already applied to this job.')
            return redirect('job_detail', slug=job.slug)

        ApplyForJob.objects.create(user=request.user, job=job)
        messages.success(request, 'Application submitted successfully!')
        return redirect('job_detail', slug=job.slug)

    return render(request, 'jobs/apply_job.html', {'job': job})


def create_job(request):
    if not request.user.is_authenticated:
        return redirect('login')
    custom_user = request.user.customuser
    if custom_user.role != "company" or not custom_user.company or custom_user.company.status != "approved":
        raise PermissionDenied("You are not approved to post jobs yet.")

    if request.method == 'POST':
        from django.utils.text import slugify
        title = request.POST.get('title', '').strip()
        location = request.POST.get('location', '').strip()
        employment_type = request.POST.get('employment_type', '').strip()
        experience_level = request.POST.get('experience_level', '').strip()
        salary_min = request.POST.get('salary_min', '').strip() or None
        salary_max = request.POST.get('salary_max', '').strip() or None
        remote_available = request.POST.get('remote_available') == 'on'
        application_deadline = request.POST.get('application_deadline', '').strip() or None
        description = request.POST.get('description', '').strip()
        requirements = request.POST.get('requirements', '').strip() or ''
        responsibilities = request.POST.get('responsibilities', '').strip() or ''
        category_id = request.POST.get('category')

        if not title or not location or not employment_type or not experience_level or not description or not category_id:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('company_view')

        try:
            category = JobCategory.objects.get(pk=category_id)
        except JobCategory.DoesNotExist:
            messages.error(request, 'Invalid category selected.')
            return redirect('company_view')

        slug_base = slugify(f"{title}-{custom_user.company.name}")
        slug = slug_base
        idx = 1
        while Job.objects.filter(slug=slug).exists():
            idx += 1
            slug = f"{slug_base}-{idx}"

        from datetime import datetime
        from django.utils import timezone
        deadline_dt = None
        if application_deadline:
            try:
                deadline_dt = timezone.make_aware(datetime.strptime(application_deadline, '%Y-%m-%d'))
            except Exception:
                messages.warning(request, 'Invalid deadline date; ignored.')

        job = Job.objects.create(
            title=title,
            slug=slug,
            company=custom_user.company,
            category=category,
            description=description,
            requirements=requirements,
            responsibilities=responsibilities,
            salary_min=salary_min or None,
            salary_max=salary_max or None,
            employment_type=employment_type,
            experience_level=experience_level,
            location=location,
            remote_available=remote_available,
            application_deadline=deadline_dt,
            is_active=True,
        )

        messages.success(request, 'Job posted successfully!')
        return redirect('company_view')

    return redirect('company_view')


@login_required
def create_company(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        website = request.POST.get("website")
        location = request.POST.get("location")
        logo = request.FILES.get("logo")

        if not name:
            messages.error(request, "Company name is required.")
        else:
            # Create company with pending status
            company = Company.objects.create(
                name=name,
                description=description,
                website=website,
                location=location,
                logo=logo,
                status="pending"
            )

            # Link company to logged-in user’s profile
            custom_user = request.user.customuser
            custom_user.company = company
            custom_user.save()

            messages.success(
                request,
                "Your company has been submitted for approval. "
                "Please wait for admin approval before posting jobs."
            )
            return redirect('company_view')  # adjust to your dashboard/homepage

    return render(request, "Company/create_company.html")

@login_required
def update_company(request, pk):
    company = get_object_or_404(Company, pk=pk)

    # make sure only users from this company can edit
    if request.user.customuser.company != company:
        messages.error(request, "You are not allowed to edit this company.")
        return redirect("company_view")

    if request.method == "POST":
        company.name = request.POST.get("name")
        company.description = request.POST.get("description")
        company.website = request.POST.get("website")
        company.location = request.POST.get("location")

        if "logo" in request.FILES:
            company.logo = request.FILES["logo"]

        company.save()
        messages.success(request, "Company details updated successfully.")
        return redirect("company_view")

    return render(request, "Company/update_company.html", {"company": company})


@login_required
def profile_completion(request):
    custom_user = request.user.customuser

    # If the user already has a company, skip profile completion
    if custom_user.company:
        return redirect("dashboard")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "new_company":
            return redirect("create_company")

        elif action == "existing_company":
            company_id = request.POST.get("company_id")
            if company_id:
                company = get_object_or_404(Company, pk=company_id, status="approved")
                custom_user.company = company
                custom_user.save()
                messages.success(request, "Company successfully linked to your profile.")
                return redirect("company_view")
            else:
                messages.error(request, "Please select a company.")

    companies = Company.objects.filter(status="approved")
    return render(request, "Company/profile_completion.html", {"companies": companies})


@login_required
def dashboard(request):
    # Dashboard: recommended jobs, saved bookmarks, quick stats
    recent_jobs = Job.objects.filter(is_active=True).order_by('-created_at')[:8].select_related('company', 'category')
    saved = []
    try:
        from bookmarks.models import JobBookmark
        saved = JobBookmark.objects.filter(user=request.user).select_related('job__company')[:12]
    except Exception:
        pass

    # Activity snapshot (placeholder counts from data we have)
    applications_sent = ApplyForJob.objects.filter(user=request.user).count() if 'ApplyForJob' in globals() else 0
    viewed_by_recruiter = 4  # placeholder; would come from analytics
    profile_views = 8        # placeholder; would come from analytics
    active_interviews = 2    # placeholder

    # Profile strength (rough heuristic)
    try:
        profile = request.user.userprofile
        fields = [profile.first_name, profile.last_name, profile.phone, profile.email, profile.profile_picture, profile.resume, profile.skills]
        completion = int(sum(1 for f in fields if f) / len(fields) * 100)
        next_hint = 'Add 3 more skills to improve your match score.' if (profile.skills or '').count(',') < 3 else 'Upload your resume to unlock quick apply.'
    except Exception:
        completion = 40
        next_hint = 'Complete your profile to get better recommendations.'

    # Skills hub suggestion (very simple heuristic)
    suggested_skill = None
    try:
        user_skills = [s.strip().lower() for s in (profile.skills or '').split(',') if s.strip()]
        corpus = ' '.join((job.description + ' ' + job.requirements) for job in recent_jobs).lower()
        for s in ['graphql', 'kubernetes', 'aws', 'react', 'django', 'spring boot']:
            if s in corpus and s not in user_skills:
                suggested_skill = s.title()
                break
    except Exception:
        pass

    # Compute simple top skills list per recent job from comma-separated requirements
    for job in recent_jobs:
        skills = []
        try:
            raw = (job.requirements or '')
            tokens = [t.strip() for t in raw.split(',') if t.strip()]
            skills = tokens[:3]
        except Exception:
            skills = []
        setattr(job, 'top_skills', skills)

    context = {
        'recent_jobs': recent_jobs,
        'saved': saved,
        'stats': {
            'applications': applications_sent,
            'viewed_by_recruiter': viewed_by_recruiter,
            'profile_views': profile_views,
            'interviews': active_interviews,
        },
        'profile_strength': completion,
        'next_hint': next_hint,
        'suggested_skill': suggested_skill,
    }
    return render(request, 'accounts/dashboard.html', context)

def logout_view(request):
    # Duplicate of accounts.logout_view; remove this to avoid conflicts
    return redirect('home')


@login_required
def company_applicants(request):
    custom_user = getattr(request.user, 'customuser', None)
    company = getattr(custom_user, 'company', None) if custom_user else None
    if not company:
        messages.info(request, 'Please complete your company profile first.')
        return redirect('profile_completion')

    # Base queryset: all applications to this company's jobs
    qs = ApplyForJob.objects.select_related('user', 'job').filter(job__company=company)

    # Optional filters
    job_id = request.GET.get('job')
    if job_id:
        qs = qs.filter(job_id=job_id)
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )

    applications = qs.order_by('-created_at')
    jobs = company.jobs.order_by('-created_at')

    context = {
        'company': company,
        'applications': applications,
        'jobs': jobs,
        'q': search,
        'selected_job_id': job_id or '',
    }
    return render(request, 'Company/applicants.html', context)


@login_required
def company_applicant_detail(request, application_id: int):
    custom_user = getattr(request.user, 'customuser', None)
    company = getattr(custom_user, 'company', None) if custom_user else None
    if not company:
        messages.info(request, 'Please complete your company profile first.')
        return redirect('profile_completion')

    application = get_object_or_404(ApplyForJob.objects.select_related('user', 'job'), pk=application_id, job__company=company)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = {key for key, _ in ApplyForJob.STATUS_CHOICES}
        if new_status in valid_statuses:
            application.status = new_status
            application.save(update_fields=['status'])
            messages.success(request, 'Applicant status updated.')
        else:
            messages.error(request, 'Invalid status value.')
        return redirect('company_applicant_detail', application_id=application.id)

    try:
        profile = application.user.userprofile
        if profile and profile.resume:
            # Check if the resume file actually exists
            resume_path = os.path.join(settings.MEDIA_ROOT, profile.resume.name)
            if not os.path.exists(resume_path):
                # If not, try to find it in other user directories
                file_name = os.path.basename(profile.resume.name)
                for dirpath, _, filenames in os.walk(settings.MEDIA_ROOT):
                    if file_name in filenames:
                        # Found the file, update the path
                        correct_path = os.path.relpath(os.path.join(dirpath, file_name), settings.MEDIA_ROOT)
                        profile.resume.name = correct_path
                        break # Stop searching once found
    except UserProfile.DoesNotExist:
        profile = None

    skills = []
    if profile and profile.skills:
        skills = [skill.strip() for skill in profile.skills.split(',') if skill.strip()]

    # Static AI-like analysis (placeholder)
    job_text = f"{application.job.description} {application.job.requirements}".lower()
    hits = sum(1 for s in [s.lower() for s in skills] if s in job_text)
    match_score = 20 + min(80, hits * 15)

    suggestions = [
        'Highlight your most relevant projects at the top of your resume.',
        'Quantify impact (metrics like performance gains, cost savings).',
        'Add 2-3 more recent technologies that match the job description.',
    ]
    missing_skills = []
    for s in ['React', 'Django', 'AWS', 'Kubernetes', 'SQL']:
        if s.lower() not in [x.lower() for x in skills] and s.lower() in job_text:
            missing_skills.append(s)

    context = {
        'application': application,
        'profile': profile,
        'skills': skills,
        'match_score': match_score,
        'missing_skills': missing_skills,
        'suggestions': suggestions,
        'status_choices': ApplyForJob.STATUS_CHOICES,
    }
    return render(request, 'Company/applicant_detail.html', context)