from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from functools import wraps
import os
import json

from .models import *
from bookmarks.models import *
from accounts.models import UserProfile


def company_required(view_func):
    """Decorator to ensure only company users can access the view"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'customuser') or request.user.customuser.role != 'company':
            messages.error(request, 'Access denied. This page is only for company users.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def applicant_required(view_func):
    """Decorator to ensure only applicant users can access the view"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'customuser') or request.user.customuser.role != 'applicant':
            messages.error(request, 'Access denied. This page is only for job seekers.')
            return redirect('company_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


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

    # Pagination
    paginator = Paginator(jobs, 12)
    page_number = request.GET.get('page')
    jobs = paginator.get_page(page_number)

    # Get categories for filter dropdown
    categories = JobCategory.objects.all()

    context = {
        'jobs': jobs,
        'categories': categories,
        'search_query': search_query,
        'location': location,
        'employment_type': employment_type,
        'experience_levels': experience_levels,
    }
    return render(request, 'landing.html', context)

def find_jobs(request):
    jobs = Job.objects.filter(is_active=True).select_related('company', 'category')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(company__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Filter by location
    location_query = request.GET.get('location', '')
    if location_query:
        jobs = jobs.filter(location__icontains=location_query)

    # Filter by employment type
    employment_type = request.GET.get('employment_type', '')
    if employment_type:
        jobs = jobs.filter(employment_type=employment_type)

    # Filter by experience level
    experience_level = request.GET.get('experience_level', '')
    if experience_level:
        jobs = jobs.filter(experience_level=experience_level)

    # Filter by salary range
    salary_range = request.GET.get('salary_range', '')
    if salary_range:
        if salary_range == '0-50000':
            jobs = jobs.filter(salary_max__lte=50000)
        elif salary_range == '50000-100000':
            jobs = jobs.filter(salary_min__gte=50000, salary_max__lte=100000)
        elif salary_range == '100000-150000':
            jobs = jobs.filter(salary_min__gte=100000, salary_max__lte=150000)
        elif salary_range == '150000+':
            jobs = jobs.filter(salary_min__gte=150000)

    # Filter by remote work
    remote = request.GET.get('remote', '')
    if remote == 'true':
        jobs = jobs.filter(remote_available=True)
    elif remote == 'false':
        jobs = jobs.filter(remote_available=False)

    # Filter by company size
    company_size = request.GET.get('company_size', '')
    if company_size:
        if company_size == 'startup':
            jobs = jobs.filter(company__company_size__icontains='1-50')
        elif company_size == 'small':
            jobs = jobs.filter(company__company_size__icontains='51-200')
        elif company_size == 'medium':
            jobs = jobs.filter(company__company_size__icontains='201-1000')
        elif company_size == 'large':
            jobs = jobs.filter(company__company_size__icontains='1000+')

    # Pagination
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    jobs = paginator.get_page(page_number)

    context = {
        'jobs': jobs,
        'search_query': search_query,
        'location_query': location_query,
        'employment_type': employment_type,
        'experience_level': experience_level,
        'salary_range': salary_range,
        'remote': remote,
        'company_size': company_size,
    }
    return render(request, 'jobs/find_jobs.html', context)

@login_required
@applicant_required
def my_applications(request):
    applications = ApplyForJob.objects.filter(user=request.user).select_related('job', 'job__company', 'job__category').order_by('-created_at')
    
    # Calculate stats
    total_applications = applications.count()
    pending_applications = applications.filter(status='pending').count()
    accepted_applications = applications.filter(status='accepted').count()
    rejected_applications = applications.filter(status='rejected').count()
    
    # Pagination
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    applications = paginator.get_page(page_number)
    
    context = {
        'applications': applications,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'accepted_applications': accepted_applications,
        'rejected_applications': rejected_applications,
    }
    return render(request, 'jobs/my_applications.html', context)

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

    # Enhanced AI matching with multiple algorithms
    if request.user.is_authenticated:
        try:
            from accounts.models import ResumeAnalysis
            from accounts.ml import compute_resume_keywords, score_job_match
            from accounts.ml_tf import HAS_TF, score_job_match_tf
            from accounts.ai_analyzer import calculate_skill_match_score, extract_key_phrases
            
            analysis = getattr(request.user, 'resume_analysis', None)
            skills_src = analysis.skills_extracted if (analysis and (analysis.skills_extracted or '').strip()) else getattr(request.user.userprofile, 'skills', '')
            user_skills, resume_vec = compute_resume_keywords(skills_src, '')
            
            if user_skills:
                for job in page_obj:
                    # Combine job text for analysis
                    job_text = f"{job.title} {job.description} {job.requirements} {job.responsibilities}"
                    
                    # Multiple scoring methods
                    scores = []
                    
                    # 1. Vector similarity (if available)
                    if resume_vec:
                        if HAS_TF:
                            resume_text = ' '.join(user_skills)
                            vec_score = score_job_match_tf(resume_text, job_text)
                        else:
                            vec_score = score_job_match(resume_vec, job_text)
                        scores.append(vec_score)
                    
                    # 2. Skill-based matching
                    skill_score = calculate_skill_match_score(user_skills, job_text)
                    scores.append(skill_score)
                    
                    # 3. Keyword density matching
                    job_keywords = extract_key_phrases(job_text, 20)
                    user_keywords = [skill.lower() for skill in user_skills]
                    keyword_matches = len(set(job_keywords) & set(user_keywords))
                    keyword_score = min(100, (keyword_matches / len(job_keywords)) * 100) if job_keywords else 0
                    scores.append(keyword_score)
                    
                    # 4. Experience level matching
                    experience_bonus = 0
                    if hasattr(request.user, 'userprofile') and request.user.userprofile.skills:
                        # Simple heuristic: more skills = more experience
                        skill_count = len([s for s in request.user.userprofile.skills.split(',') if s.strip()])
                        if skill_count >= 5 and 'senior' in job_text.lower():
                            experience_bonus = 15
                        elif skill_count >= 3 and 'mid' in job_text.lower():
                            experience_bonus = 10
                        elif skill_count >= 1 and 'entry' in job_text.lower():
                            experience_bonus = 20
                    
                    # Calculate weighted average
                    if scores:
                        final_score = sum(scores) / len(scores) + experience_bonus
                        final_score = min(100, max(0, final_score))
                    else:
                        final_score = 0
                    
                    setattr(job, 'match_score', int(final_score))
                    setattr(job, 'match_breakdown', {
                        'vector_score': scores[0] if len(scores) > 0 else 0,
                        'skill_score': scores[1] if len(scores) > 1 else 0,
                        'keyword_score': scores[2] if len(scores) > 2 else 0,
                        'experience_bonus': experience_bonus
                    })
        except Exception as e:
            print(f"Error in AI matching: {e}")
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
    # Handle slugs that might have been URL encoded
    try:
        job = get_object_or_404(Job, slug=slug, is_active=True)
    except:
        # Try with a cleaned slug if the original fails
        cleaned_slug = slug.replace('/', '-').replace('\\', '-')
        job = get_object_or_404(Job, slug=cleaned_slug, is_active=True)

    # Check if user has bookmarked this job
    is_bookmarked = False
    has_applied = False
    if request.user.is_authenticated:
        is_bookmarked = JobBookmark.objects.filter(user=request.user, job=job).exists()
        has_applied = ApplyForJob.objects.filter(user=request.user, job=job).exists()

    # Get related jobs
    related_jobs = Job.objects.filter(
        category=job.category,
        is_active=True
    ).exclude(id=job.id)[:5]

    context = {
        'job': job,
        'is_bookmarked': is_bookmarked,
        'has_applied': has_applied,
        'related_jobs': related_jobs,
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
@applicant_required
def apply_job(request, slug):
    job = get_object_or_404(Job, slug=slug, is_active=True)

    if request.method == 'POST':
        # prevent duplicate applications
        if ApplyForJob.objects.filter(user=request.user, job=job).exists():
            messages.info(request, 'You have already applied to this job.')
            return redirect('job_detail', slug=job.slug)

        # Calculate AI match score before creating application
        ai_match_score = 0
        try:
            from accounts.models import UserProfile
            profile = UserProfile.objects.get(user=request.user)
            ai_match_score = calculate_ai_match_score(
                type('MockApplication', (), {'job': job, 'user': request.user})(), 
                profile
            )
            print(f"Calculated AI match score for {request.user.username}: {ai_match_score}%")
        except UserProfile.DoesNotExist:
            print(f"No profile found for {request.user.username}, using default score: 0")
        except Exception as e:
            print(f"Error calculating AI score for {request.user.username}: {e}")

        # Create application with AI match score
        ApplyForJob.objects.create(user=request.user, job=job, ai_match_score=ai_match_score)
        messages.success(request, 'Application submitted successfully!')
        return redirect('job_detail', slug=job.slug)

    return render(request, 'jobs/apply_job.html', {'job': job})


@login_required
@company_required
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

        # Create a safe slug by replacing problematic characters
        safe_title = title.replace('/', '-').replace('\\', '-').replace(' ', '-')
        safe_company = custom_user.company.name.replace('/', '-').replace('\\', '-').replace(' ', '-')
        slug_base = slugify(f"{safe_title}-{safe_company}")
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
@company_required
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
@company_required
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
@company_required
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
@company_required
def company_dashboard(request):
    """Company dashboard with job management and analytics"""
    # Get company through CustomUser
    custom_user = getattr(request.user, 'customuser', None)
    company = getattr(custom_user, 'company', None) if custom_user else None
    
    if not company:
        messages.error(request, 'Company profile not found. Please complete your company profile.')
        return redirect('profile_completion')
    
    # Get company's jobs
    company_jobs = Job.objects.filter(company=company).order_by('-created_at')
    active_jobs = company_jobs.filter(is_active=True)
    
    # Get applications for company's jobs - sorted by AI match score
    applications = ApplyForJob.objects.filter(job__company=company).select_related('user', 'job')
    recent_applications = applications.order_by('-ai_match_score', '-created_at')[:10]
    
    # Calculate stats
    total_jobs = company_jobs.count()
    active_jobs_count = active_jobs.count()
    total_applications = applications.count()
    pending_applications = applications.filter(status='pending').count()
    
    # Recent activity
    recent_activity = []
    for app in recent_applications[:5]:
        recent_activity.append({
            'type': 'application',
            'message': f'New application for {app.job.title}',
            'time': app.created_at,
            'user': app.user
        })
    
    # Get categories for job posting form
    categories = JobCategory.objects.all()
    
    # Get AI-powered insights for company dashboard
    ai_insights = {}
    if company:
        try:
            from accounts.gemini_chatbot import gemini_chatbot
            
            # Create company profile for AI analysis
            company_profile = {
                'name': company.name or 'Unknown Company',
                'industry': company.industry or 'Technology',
                'location': company.location or 'Unknown',
                'company_size': company.company_size or 'Unknown',
                'total_jobs': total_jobs,
                'active_jobs': active_jobs_count,
                'total_applications': total_applications,
                'recent_job_titles': [job.title for job in recent_jobs[:3]] if recent_jobs else [],
                'skills': ', '.join([job.category.name for job in recent_jobs[:5]]) if recent_jobs else 'General',
                'first_name': 'Company',
                'resume_text': '',
                'db_context': ''
            }
            
            # Get AI company insights
            company_insights_prompt = f"""
            As an AI business analyst, analyze this company's hiring data and provide insights in JSON format ONLY:

            Company Profile:
            - Name: {company_profile['name']}
            - Industry: {company_profile['industry']}
            - Location: {company_profile['location']}
            - Company Size: {company_profile['company_size']}
            - Total Jobs Posted: {total_jobs}
            - Active Jobs: {active_jobs_count}
            - Total Applications: {total_applications}
            - Recent Job Titles: {', '.join(company_profile['recent_job_titles'])}

            IMPORTANT: Respond ONLY with valid JSON in this exact format:
            {{
                "hiring_trends": ["High demand for developers", "Remote work increasing"],
                "recommendations": ["Post more senior roles", "Improve job descriptions"],
                "market_position": "competitive",
                "growth_opportunities": ["Expand to new markets", "Hire specialized roles"],
                "efficiency_score": 85,
                "next_steps": ["Optimize job postings", "Improve candidate experience"]
            }}

            Do not include any text before or after the JSON. Only return the JSON object.
            """
            
            response = gemini_chatbot.generate_response(company_insights_prompt, company_profile)
            
            if response and response.get('response'):
                try:
                    # Clean the response - remove markdown code blocks if present
                    response_text = response['response'].strip()
                    if response_text.startswith('```json'):
                        response_text = response_text[7:]  # Remove ```json
                    if response_text.startswith('```'):
                        response_text = response_text[3:]   # Remove ```
                    if response_text.endswith('```'):
                        response_text = response_text[:-3]  # Remove trailing ```
                    response_text = response_text.strip()
                    
                    ai_insights = json.loads(response_text)
                    
                except json.JSONDecodeError as e:
                    # Fallback insights
                    ai_insights = {
                        'hiring_trends': ['Strong application volume', 'Competitive market'],
                        'recommendations': ['Optimize job descriptions', 'Improve candidate screening'],
                        'market_position': 'competitive',
                        'growth_opportunities': ['Expand team', 'New market entry'],
                        'efficiency_score': 80,
                        'next_steps': ['Review applications', 'Update job postings']
                    }
            else:
                ai_insights = {
                    'hiring_trends': ['Strong application volume', 'Competitive market'],
                    'recommendations': ['Optimize job descriptions', 'Improve candidate screening'],
                    'market_position': 'competitive',
                    'growth_opportunities': ['Expand team', 'New market entry'],
                    'efficiency_score': 80,
                    'next_steps': ['Review applications', 'Update job postings']
                }
                    
        except Exception as e:
            # Fallback insights
            ai_insights = {
                'hiring_trends': ['Strong application volume', 'Competitive market'],
                'recommendations': ['Optimize job descriptions', 'Improve candidate screening'],
                'market_position': 'competitive',
                'growth_opportunities': ['Expand team', 'New market entry'],
                'efficiency_score': 80,
                'next_steps': ['Review applications', 'Update job postings']
            }

    context = {
        'company': company,
        'total_jobs': total_jobs,
        'active_jobs_count': active_jobs_count,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'recent_jobs': active_jobs[:5],
        'recent_applications': recent_applications,
        'recent_activity': recent_activity,
        'categories': categories,
        'ai_insights': ai_insights,
    }
    
    return render(request, 'Company/dashboard.html', context)

@login_required
@company_required
def update_application_status(request, application_id):
    """Update application status (accept/reject)"""
    if request.method == 'POST':
        # Get company through CustomUser
        custom_user = getattr(request.user, 'customuser', None)
        company = getattr(custom_user, 'company', None) if custom_user else None
        
        if not company:
            messages.error(request, 'Company profile not found.')
            return redirect('company_dashboard')
            
        application = get_object_or_404(ApplyForJob, id=application_id, job__company=company)
        new_status = request.POST.get('status')
        
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            # Show success message
            messages.success(request, f'Application {new_status} successfully!')
        else:
            messages.error(request, 'Invalid status update.')
    
    return redirect('company_applicants')

@login_required
@applicant_required
def dashboard(request):
    # Check if user is a company
    if hasattr(request.user, 'company') and request.user.company:
        return company_dashboard(request)
    
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

    # Get user notifications
    notifications = []
    try:
        from accounts.models import Notification
        notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
    except Exception:
        pass

    # AI-powered job recommendations
    ai_recommendations = []
    try:
        from accounts.ai_enhanced import ai_analyzer
        user_skills = [skill.strip() for skill in (profile.skills or '').split(',') if skill.strip()]
        
        if user_skills:
            # Get all active jobs for recommendation
            all_jobs = Job.objects.filter(is_active=True).select_related('company')
            job_listings = []
            for job in all_jobs:
                job_listings.append({
                    'id': job.id,
                    'title': job.title,
                    'description': job.description,
                    'requirements': job.requirements,
                    'location': job.location,
                    'salary_min': job.salary_min,
                    'salary_max': job.salary_max,
                    'company_name': job.company.name,
                    'get_absolute_url': job.get_absolute_url()
                })
            
            # Get AI recommendations
            ai_recommendations = ai_analyzer.recommend_jobs(user_skills, job_listings)
            
    except Exception as e:
        print(f"AI job recommendations failed: {e}")

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
        'notifications': notifications,
        'ai_recommendations': ai_recommendations[:5],  # Top 5 AI recommendations
    }
    return render(request, 'accounts/dashboard.html', context)

def logout_view(request):
    # Duplicate of accounts.logout_view; remove this to avoid conflicts
    return redirect('home')


@login_required
@company_required
def company_applicants(request, job_id=None):
    custom_user = getattr(request.user, 'customuser', None)
    company = getattr(custom_user, 'company', None) if custom_user else None
    if not company:
        messages.info(request, 'Please complete your company profile first.')
        return redirect('profile_completion')

    # Base queryset: all applications to this company's jobs
    qs = ApplyForJob.objects.select_related('user', 'job').filter(job__company=company)

    # Optional filters
    # Check for job_id from URL parameter first, then from GET parameter
    if job_id:
        qs = qs.filter(job_id=job_id)
    else:
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

    # Sort by AI match score (highest first) - using stored scores
    applications = qs.order_by('-ai_match_score', '-created_at')
    
    # Add ranking data for display (using stored scores)
    ranked_applications = []
    for application in applications:
        try:
            # Get user profile for additional data
            profile = UserProfile.objects.get(user=application.user)
            
            # Add ranking data for template display
            application.ai_ranking_data = {
                'score': application.ai_match_score,
                'profile': profile,
                'skills_match': calculate_skills_match(application.job, profile),
                'experience_level': calculate_experience_level(profile),
                'resume_completeness': calculate_resume_completeness(profile)
            }
            
        except UserProfile.DoesNotExist:
            # If no profile, use basic data
            application.ai_ranking_data = {
                'score': application.ai_match_score,
                'profile': None,
                'skills_match': 0,
                'experience_level': 'Unknown',
                'resume_completeness': 0
            }
        
        ranked_applications.append(application)
    
    jobs = company.jobs.order_by('-created_at')

    context = {
        'company': company,
        'applications': ranked_applications,
        'jobs': jobs,
        'q': search,
        'selected_job_id': job_id or '',
    }
    return render(request, 'Company/applicants.html', context)


@login_required
@company_required
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

    # Use stored AI match score
    match_score = application.ai_match_score
    
    # Generate comprehensive AI analysis
    ai_analysis = generate_comprehensive_ai_analysis(application, profile)
    
    # Extract analysis components
    suggestions = ai_analysis.get('suggestions', [])
    missing_skills = ai_analysis.get('missing_skills', [])
    strengths = ai_analysis.get('strengths', [])
    concerns = ai_analysis.get('concerns', [])
    recommendation = ai_analysis.get('recommendation', '')
    interview_focus = ai_analysis.get('interview_focus', [])
    salary_expectation = ai_analysis.get('salary_expectation', {})
    hiring_timeline = ai_analysis.get('hiring_timeline', '')
    risk_factors = ai_analysis.get('risk_factors', [])

    context = {
        'application': application,
        'profile': profile,
        'skills': skills,
        'match_score': match_score,
        'missing_skills': missing_skills,
        'suggestions': suggestions,
        'strengths': strengths,
        'concerns': concerns,
        'recommendation': recommendation,
        'interview_focus': interview_focus,
        'salary_expectation': salary_expectation,
        'hiring_timeline': hiring_timeline,
        'risk_factors': risk_factors,
        'status_choices': ApplyForJob.STATUS_CHOICES,
        'company': company,
    }
    return render(request, 'Company/applicant_detail.html', context)


# AI-Powered Candidate Analysis Functions
def generate_comprehensive_ai_analysis(application, profile):
    """Generate comprehensive AI analysis for candidate detail page"""
    try:
        from accounts.gemini_chatbot import gemini_chatbot
        
        # Create context for AI analysis
        candidate_context = {
            'name': f"{profile.first_name} {profile.last_name}",
            'skills': profile.skills or '',
            'resume_text': '',  # Resume text would need to be extracted from resume file
            'job_title': application.job.title,
            'job_description': application.job.description,
            'job_requirements': application.job.requirements or '',
            'first_name': profile.first_name or 'Candidate',
            'db_context': ''
        }
        
        # Generate comprehensive AI analysis
        analysis_prompt = f"""
        As an AI recruiter, provide comprehensive analysis for this candidate in JSON format ONLY:

        Candidate Profile:
        - Name: {candidate_context['name']}
        - Skills: {candidate_context['skills']}
        - Resume: {candidate_context['resume_text'][:800]}

        Job Position:
        - Title: {application.job.title}
        - Description: {application.job.description[:400]}
        - Requirements: {application.job.requirements or 'Not specified'}

        IMPORTANT: Respond ONLY with valid JSON in this exact format:
        {{
            "strengths": ["Strong technical background", "Relevant experience", "Good communication"],
            "concerns": ["Limited cloud experience", "Could improve leadership skills"],
            "recommendation": "Strong candidate - recommend for technical interview",
            "interview_focus": ["System design", "Problem solving", "Cultural fit"],
            "salary_expectation": {{"min": 90000, "max": 110000}},
            "hiring_timeline": "2-3 weeks",
            "risk_factors": ["May have competing offers", "Salary expectations high"],
            "missing_skills": ["Kubernetes", "Docker"],
            "suggestions": ["Focus on technical skills in interview", "Discuss growth opportunities"]
        }}

        Do not include any text before or after the JSON. Only return the JSON object.
        """
        
        response = gemini_chatbot.generate_response(analysis_prompt, candidate_context)
        
        if response and response.get('response'):
            # Clean the response
            response_text = response['response'].strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            try:
                analysis = json.loads(response_text)
                return analysis
            except json.JSONDecodeError:
                pass
        
        # Fallback analysis
        return generate_fallback_analysis(application, profile)
        
    except Exception as e:
        print(f"AI analysis error: {e}")
        return generate_fallback_analysis(application, profile)

def generate_fallback_analysis(application, profile):
    """Fallback analysis when AI is unavailable"""
    job_text = f"{application.job.description} {application.job.requirements}".lower()
    user_skills = [s.strip().lower() for s in profile.skills.split(',') if s.strip()] if profile.skills else []
    
    # Calculate missing skills
    common_skills = ['python', 'javascript', 'react', 'django', 'aws', 'kubernetes', 'docker', 'sql', 'git']
    missing_skills = [skill for skill in common_skills if skill in job_text and skill not in user_skills]
    
    # Generate strengths based on skills
    strengths = []
    if profile.skills:
        strengths.append("Has relevant technical skills")
    if profile.first_name and profile.last_name:
        strengths.append("Complete profile information")
    if profile.email:
        strengths.append("Professional contact information")
    
    # Generate concerns
    concerns = []
    if missing_skills:
        concerns.append(f"Missing key skills: {', '.join(missing_skills[:3])}")
    if not profile.skills:
        concerns.append("No skills specified in profile")
    
    # Generate recommendation based on match score
    match_score = application.ai_match_score
    if match_score >= 70:
        recommendation = "Strong candidate - recommend for technical interview"
    elif match_score >= 50:
        recommendation = "Good candidate - consider for screening"
    else:
        recommendation = "May need additional evaluation"
    
    return {
        'strengths': strengths,
        'concerns': concerns,
        'recommendation': recommendation,
        'interview_focus': ['Technical skills', 'Problem solving', 'Cultural fit'],
        'salary_expectation': {'min': 80000, 'max': 120000},
        'hiring_timeline': '2-4 weeks',
        'risk_factors': ['Competitive market'],
        'missing_skills': missing_skills,
        'suggestions': [
            'Focus on technical skills in interview',
            'Discuss growth opportunities',
            'Evaluate cultural fit'
        ]
    }

# AI-Powered Candidate Ranking Helper Functions
def calculate_ai_match_score(application, profile):
    """Calculate comprehensive AI match score for a candidate"""
    try:
        from accounts.gemini_chatbot import gemini_chatbot
        
        # Create context for AI analysis
        candidate_context = {
            'name': f"{profile.first_name} {profile.last_name}",
            'skills': profile.skills or '',
            'resume_text': '',  # Resume text would need to be extracted from resume file
            'job_title': application.job.title,
            'job_description': application.job.description,
            'job_requirements': application.job.requirements or '',
            'first_name': profile.first_name or 'Candidate',
            'db_context': ''
        }
        
        # Generate AI match score
        scoring_prompt = f"""
        As an AI recruiter, analyze this candidate's match for the job position and provide ONLY a match score (0-100) in JSON format:

        Candidate Profile:
        - Name: {candidate_context['name']}
        - Skills: {candidate_context['skills']}
        - Resume: {candidate_context['resume_text'][:800]}

        Job Position:
        - Title: {application.job.title}
        - Description: {application.job.description[:400]}
        - Requirements: {application.job.requirements or 'Not specified'}

        IMPORTANT: Respond ONLY with valid JSON in this exact format:
        {{
            "match_score": 85,
            "reasoning": "Strong technical background with relevant skills"
        }}

        Do not include any text before or after the JSON. Only return the JSON object.
        """
        
        response = gemini_chatbot.generate_response(scoring_prompt, candidate_context)
        
        if response and response.get('response'):
            # Clean the response
            response_text = response['response'].strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            try:
                result = json.loads(response_text)
                return result.get('match_score', 50)
            except json.JSONDecodeError:
                pass
        
        # Fallback to rule-based scoring
        return calculate_fallback_match_score(application, profile)
        
    except Exception as e:
        print(f"AI scoring error: {e}")
        return calculate_fallback_match_score(application, profile)

def calculate_fallback_match_score(application, profile):
    """Fallback rule-based match scoring"""
    score = 0
    
    # Skills matching (40% weight)
    if profile.skills:
        job_text = f"{application.job.description} {application.job.requirements}".lower()
        user_skills = [s.strip().lower() for s in profile.skills.split(',') if s.strip()]
        skill_matches = sum(1 for skill in user_skills if skill in job_text)
        skills_score = min(40, skill_matches * 8)
        score += skills_score
    
    # Resume completeness (20% weight)
    resume_fields = [profile.first_name, profile.last_name, profile.email, profile.resume]
    completeness = sum(1 for field in resume_fields if field) / len(resume_fields)
    score += completeness * 20
    
    # Profile completeness (20% weight)
    profile_fields = [profile.first_name, profile.last_name, profile.phone, profile.email, profile.skills]
    profile_completeness = sum(1 for field in profile_fields if field) / len(profile_fields)
    score += profile_completeness * 20
    
    # Experience level bonus (20% weight)
    if profile.skills:
        skill_count = len([s for s in profile.skills.split(',') if s.strip()])
        if skill_count >= 5:
            score += 20
        elif skill_count >= 3:
            score += 15
        elif skill_count >= 1:
            score += 10
    
    return min(100, max(0, int(score)))

def calculate_skills_match(job, profile):
    """Calculate skills match percentage"""
    if not profile.skills:
        return 0
    
    job_text = f"{job.description} {job.requirements}".lower()
    user_skills = [s.strip().lower() for s in profile.skills.split(',') if s.strip()]
    
    if not user_skills:
        return 0
    
    matches = sum(1 for skill in user_skills if skill in job_text)
    return int((matches / len(user_skills)) * 100)

def calculate_experience_level(profile):
    """Determine experience level based on profile"""
    if not profile.skills:
        return 'Entry Level'
    
    skill_count = len([s for s in profile.skills.split(',') if s.strip()])
    
    if skill_count >= 8:
        return 'Senior Level'
    elif skill_count >= 5:
        return 'Mid Level'
    elif skill_count >= 2:
        return 'Junior Level'
    else:
        return 'Entry Level'

def calculate_resume_completeness(profile):
    """Calculate resume completeness percentage"""
    fields = [profile.first_name, profile.last_name, profile.email, profile.resume, profile.skills]
    completed = sum(1 for field in fields if field)
    return int((completed / len(fields)) * 100)

# AI-Powered Job Posting
@login_required
@company_required
@require_http_methods(["POST"])
def ai_generate_job_posting(request):
    """AI-powered job posting generation from natural language prompt"""
    try:
        data = json.loads(request.body)
        job_prompt = data.get('job_prompt', '')
        company_context = data.get('company_context', {})
        
        if not job_prompt:
            return JsonResponse({'success': False, 'error': 'Job prompt is required'})
        
        # Get company information
        custom_user = getattr(request.user, 'customuser', None)
        company = getattr(custom_user, 'company', None) if custom_user else None
        
        if not company:
            return JsonResponse({'success': False, 'error': 'Company profile not found'})
        
        from accounts.gemini_chatbot import gemini_chatbot
        
        # Create context for AI job generation
        ai_context = {
            'company_name': company.name or 'Our Company',
            'company_industry': 'Technology',  # Default since Company model doesn't have industry field
            'company_location': company.location or 'Remote',
            'company_size': company.company_size or 'Medium',
            'job_prompt': job_prompt,
            'first_name': 'Company',
            'skills': company_context.get('skills', ''),
            'resume_text': '',
            'db_context': ''
        }
        
        # Generate AI job posting
        job_generation_prompt = f"""
        As an AI HR specialist, create a complete job posting from this natural language description in JSON format ONLY:

        Company Context:
        - Company: {ai_context['company_name']}
        - Industry: {ai_context['company_industry']}
        - Location: {ai_context['company_location']}
        - Size: {ai_context['company_size']}

        Job Description Prompt:
        "{job_prompt}"

        IMPORTANT: Respond ONLY with valid JSON in this exact format:
        {{
            "title": "Senior Software Engineer",
            "description": "We are looking for a Senior Software Engineer to join our team...",
            "requirements": "• Bachelor's degree in Computer Science or related field\\n• 5+ years of software development experience\\n• Proficiency in Python, JavaScript, React\\n• Experience with cloud platforms (AWS, Azure)\\n• Strong problem-solving and communication skills",
            "responsibilities": "• Design and develop scalable software solutions\\n• Collaborate with cross-functional teams\\n• Mentor junior developers\\n• Participate in code reviews and technical discussions",
            "benefits": "• Competitive salary and equity\\n• Health, dental, and vision insurance\\n• Flexible work arrangements\\n• Professional development opportunities",
            "salary_range": {{"min": 120000, "max": 180000, "currency": "USD"}},
            "employment_type": "Full-time",
            "experience_level": "Senior",
            "location": "San Francisco, CA",
            "remote_work": "Hybrid",
            "skills_required": ["Python", "JavaScript", "React", "AWS", "Docker"],
            "nice_to_have": ["Kubernetes", "GraphQL", "Machine Learning"],
            "company_culture": "Fast-paced, innovative, collaborative environment",
            "growth_opportunities": "Opportunity to lead technical initiatives and mentor team members"
        }}

        Do not include any text before or after the JSON. Only return the JSON object.
        """
        
        response = gemini_chatbot.generate_response(job_generation_prompt, ai_context)
        
        if response and response.get('response'):
            # Clean the response
            response_text = response['response'].strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            try:
                job_data = json.loads(response_text)
                return JsonResponse({
                    'success': True,
                    'job_data': job_data,
                    'type': response.get('type', 'gemini')
                })
            except json.JSONDecodeError:
                pass
        
        # Fallback job data
        return JsonResponse({
            'success': True,
            'job_data': {
                'title': 'Software Engineer',
                'description': f'We are looking for a Software Engineer to join our team. {job_prompt}',
                'requirements': '• Bachelor\'s degree in Computer Science or related field\n• 2+ years of software development experience\n• Strong problem-solving skills',
                'responsibilities': '• Develop and maintain software applications\n• Collaborate with team members\n• Write clean, maintainable code',
                'benefits': '• Competitive salary\n• Health insurance\n• Flexible work arrangements',
                'salary_range': {'min': 80000, 'max': 120000, 'currency': 'USD'},
                'employment_type': 'Full-time',
                'experience_level': 'Mid-level',
                'location': company.location or 'Remote',
                'remote_work': 'Hybrid',
                'skills_required': ['Python', 'JavaScript'],
                'nice_to_have': ['React', 'AWS'],
                'company_culture': 'Innovative and collaborative environment',
                'growth_opportunities': 'Opportunity to grow and learn new technologies'
            },
            'type': 'fallback'
        })
        
    except Exception as e:
        print(f"AI job generation error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

# AI-Powered Company Features
@login_required
@company_required
@require_http_methods(["POST"])
def ai_job_suggestions(request):
    """AI-powered job description suggestions"""
    try:
        data = json.loads(request.body)
        job_title = data.get('job_title', '')
        job_description = data.get('job_description', '')
        industry = data.get('industry', '')
        location = data.get('location', '')
        
        from accounts.gemini_chatbot import gemini_chatbot
        
        # Create context for AI analysis
        job_context = {
            'title': job_title,
            'description': job_description,
            'industry': industry,
            'location': location,
            'skills': '',
            'first_name': request.user.first_name or 'Company',
            'resume_text': '',
            'db_context': ''
        }
        
        # Generate AI suggestions
        suggestions_prompt = f"""
        As an AI HR specialist, analyze this job posting and provide comprehensive suggestions in JSON format ONLY:

        Job Details:
        - Title: {job_title}
        - Description: {job_description}
        - Industry: {industry}
        - Location: {location}

        IMPORTANT: Respond ONLY with valid JSON in this exact format:
        {{
            "essential_skills": ["Python", "Django", "PostgreSQL", "AWS"],
            "nice_to_have_skills": ["React", "Docker", "Kubernetes", "GraphQL"],
            "salary_range": {{"min": 80000, "max": 120000, "currency": "USD"}},
            "inclusive_language_score": 85,
            "inclusive_suggestions": ["Use 'they' instead of 'he/she'", "Focus on skills over credentials"],
            "market_trends": ["Remote work increasing", "Cloud skills in demand"],
            "optimization_tips": ["Add specific metrics", "Include growth opportunities"]
        }}

        Do not include any text before or after the JSON. Only return the JSON object.
        """
        
        response = gemini_chatbot.generate_response(suggestions_prompt, job_context)
        
        if response and response.get('response'):
            # Clean the response
            response_text = response['response'].strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            try:
                suggestions = json.loads(response_text)
                return JsonResponse({
                    'success': True,
                    'suggestions': suggestions,
                    'type': response.get('type', 'gemini')
                })
            except json.JSONDecodeError:
                # Fallback suggestions
                return JsonResponse({
                    'success': True,
                    'suggestions': {
                        'essential_skills': ['Python', 'Django', 'PostgreSQL', 'AWS'],
                        'nice_to_have_skills': ['React', 'Docker', 'Kubernetes'],
                        'salary_range': {'min': 80000, 'max': 120000, 'currency': 'USD'},
                        'inclusive_language_score': 85,
                        'inclusive_suggestions': ['Use gender-neutral language', 'Focus on skills'],
                        'market_trends': ['Remote work increasing', 'Cloud skills in demand'],
                        'optimization_tips': ['Add specific metrics', 'Include growth opportunities']
                    },
                    'type': 'fallback'
                })
        
        return JsonResponse({'success': False, 'error': 'AI service unavailable'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@company_required
@require_http_methods(["POST"])
def ai_candidate_analysis(request):
    """AI-powered candidate analysis and ranking"""
    try:
        data = json.loads(request.body)
        application_id = data.get('application_id')
        
        if not application_id:
            return JsonResponse({'success': False, 'error': 'Application ID required'})
        
        # Get application and user profile
        application = get_object_or_404(ApplyForJob, id=application_id)
        profile = get_object_or_404(UserProfile, user=application.user)
        
        from accounts.gemini_chatbot import gemini_chatbot
        
        # Create candidate context
        candidate_context = {
            'name': f"{profile.first_name} {profile.last_name}",
            'skills': profile.skills or '',
            'experience': '3+ years',  # This could be calculated from profile
            'job_title': application.job.title,
            'job_description': application.job.description,
            'job_requirements': application.job.requirements or '',
            'resume_text': profile.resume_text or '',
            'first_name': profile.first_name or 'Candidate',
            'db_context': ''
        }
        
        # Generate AI analysis
        analysis_prompt = f"""
        As an AI recruiter, analyze this candidate for the job position and provide detailed insights in JSON format ONLY:

        Candidate Profile:
        - Name: {candidate_context['name']}
        - Skills: {candidate_context['skills']}
        - Experience: {candidate_context['experience']}
        - Resume: {candidate_context['resume_text'][:1000]}

        Job Position:
        - Title: {application.job.title}
        - Description: {application.job.description[:500]}
        - Requirements: {application.job.requirements or 'Not specified'}

        IMPORTANT: Respond ONLY with valid JSON in this exact format:
        {{
            "match_score": 85,
            "strengths": ["Strong technical background", "Relevant experience", "Good communication"],
            "concerns": ["Limited cloud experience", "Could improve leadership skills"],
            "recommendation": "Strong candidate - recommend for technical interview",
            "interview_focus": ["System design", "Problem solving", "Cultural fit"],
            "salary_expectation": {{"min": 90000, "max": 110000}},
            "hiring_timeline": "2-3 weeks",
            "risk_factors": ["May have competing offers", "Salary expectations high"]
        }}

        Do not include any text before or after the JSON. Only return the JSON object.
        """
        
        response = gemini_chatbot.generate_response(analysis_prompt, candidate_context)
        
        if response and response.get('response'):
            # Clean the response
            response_text = response['response'].strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            try:
                analysis = json.loads(response_text)
                return JsonResponse({
                    'success': True,
                    'analysis': analysis,
                    'type': response.get('type', 'gemini')
                })
            except json.JSONDecodeError:
                # Fallback analysis
                return JsonResponse({
                    'success': True,
                    'analysis': {
                        'match_score': 80,
                        'strengths': ['Strong technical background', 'Relevant experience'],
                        'concerns': ['Limited experience in some areas'],
                        'recommendation': 'Good candidate - consider for interview',
                        'interview_focus': ['Technical skills', 'Problem solving'],
                        'salary_expectation': {'min': 85000, 'max': 105000},
                        'hiring_timeline': '2-4 weeks',
                        'risk_factors': ['Competitive market']
                    },
                    'type': 'fallback'
                })
        
        return JsonResponse({'success': False, 'error': 'AI service unavailable'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@company_required
@require_http_methods(["POST"])
def ai_interview_scheduler(request):
    """AI-powered interview scheduling assistance"""
    try:
        data = json.loads(request.body)
        application_id = data.get('application_id')
        preferred_times = data.get('preferred_times', [])
        
        if not application_id:
            return JsonResponse({'success': False, 'error': 'Application ID required'})
        
        application = get_object_or_404(ApplyForJob, id=application_id)
        
        from accounts.gemini_chatbot import gemini_chatbot
        
        # Create scheduling context
        scheduling_context = {
            'candidate_name': f"{application.user.first_name} {application.user.last_name}",
            'job_title': application.job.title,
            'company_name': application.job.company.name,
            'preferred_times': ', '.join(preferred_times),
            'skills': '',
            'first_name': 'Scheduler',
            'resume_text': '',
            'db_context': ''
        }
        
        # Generate AI scheduling suggestions
        scheduling_prompt = f"""
        As an AI scheduling assistant, help coordinate an interview and provide suggestions in JSON format ONLY:

        Interview Details:
        - Candidate: {application.user.first_name} {application.user.last_name}
        - Position: {application.job.title}
        - Company: {application.job.company.name}
        - Preferred Times: {', '.join(preferred_times)}

        IMPORTANT: Respond ONLY with valid JSON in this exact format:
        {{
            "suggested_times": ["Monday 2:00 PM", "Tuesday 10:00 AM", "Wednesday 3:00 PM"],
            "interview_duration": "60 minutes",
            "interview_format": "Video call",
            "preparation_tips": ["Review candidate resume", "Prepare technical questions", "Check calendar"],
            "follow_up_actions": ["Send calendar invite", "Share interview details", "Prepare feedback form"],
            "best_time": "Tuesday 10:00 AM",
            "reasoning": "Morning slot shows professionalism, avoids lunch conflicts"
        }}

        Do not include any text before or after the JSON. Only return the JSON object.
        """
        
        response = gemini_chatbot.generate_response(scheduling_prompt, scheduling_context)
        
        if response and response.get('response'):
            # Clean the response
            response_text = response['response'].strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            try:
                scheduling = json.loads(response_text)
                return JsonResponse({
                    'success': True,
                    'scheduling': scheduling,
                    'type': response.get('type', 'gemini')
                })
            except json.JSONDecodeError:
                # Fallback scheduling
                return JsonResponse({
                    'success': True,
                    'scheduling': {
                        'suggested_times': ['Monday 2:00 PM', 'Tuesday 10:00 AM', 'Wednesday 3:00 PM'],
                        'interview_duration': '60 minutes',
                        'interview_format': 'Video call',
                        'preparation_tips': ['Review candidate resume', 'Prepare questions'],
                        'follow_up_actions': ['Send calendar invite', 'Share details'],
                        'best_time': 'Tuesday 10:00 AM',
                        'reasoning': 'Morning slot shows professionalism'
                    },
                    'type': 'fallback'
                })
        
        return JsonResponse({'success': False, 'error': 'AI service unavailable'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})