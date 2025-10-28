from django.urls import path
from .views import *
from accounts.views import company_view

urlpatterns = [
    path('', job_list, name='home'),
    path('find-jobs/', find_jobs, name='find_jobs'),
    path('my-applications/', my_applications, name='my_applications'),
    path('job_detail/<str:slug>/', job_detail, name='job_detail'),
    path('company/', company_view, name='company_view'),
    path('company/dashboard/', company_dashboard, name='company_dashboard'),
    path('company/add/', create_company, name='create_company'),
    path('company/update/<int:pk>/', update_company, name='update_company'),
    path('company/jobs/create/', create_job, name='create_job'),
    path('company/jobs/post/', create_job, name='post_job'),
    path('company/jobs/update/<int:job_id>/', create_job, name='update_job'),
    path('company/applicants/', company_applicants, name='company_applicants'),
    path('company/applicants/job/<int:job_id>/', company_applicants, name='company_applicants_job'),
    path('company/applicants/<int:application_id>/', company_applicant_detail, name='company_applicant_detail'),
    path('company/applications/<int:application_id>/update/', update_application_status, name='update_application_status'),
    
    # AI-Powered Company Features
    path('api/company/ai/job-suggestions/', ai_job_suggestions, name='ai_job_suggestions'),
    path('api/company/ai/candidate-analysis/', ai_candidate_analysis, name='ai_candidate_analysis'),
    path('api/company/ai/interview-scheduler/', ai_interview_scheduler, name='ai_interview_scheduler'),
    path('api/company/ai/generate-job-posting/', ai_generate_job_posting, name='ai_generate_job_posting'),
    path('job/<str:slug>/apply/', apply_job, name='apply_job'),
    path('profile_completion', profile_completion, name='profile_completion'),
    path('dashboard/', dashboard, name='dashboard'),
]
