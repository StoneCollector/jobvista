from django.urls import path
from .views import *
from accounts.views import *

urlpatterns = [
    path('', job_list, name='home'),
    path('job_detail/<slug:slug>/', job_detail, name='job_detail'),
    path('company/', company_view, name='company_view'),
    path('company/add/', create_company, name='create_company'),
    path('company/update/<int:pk>/', update_company, name='update_company'),
    path('company/jobs/create/', create_job, name='create_job'),
    path('company/applicants/', company_applicants, name='company_applicants'),
    path('company/applicants/<int:application_id>/', company_applicant_detail, name='company_applicant_detail'),
    path('job/<slug:slug>/apply/', apply_job, name='apply_job'),
    path('profile_completion', profile_completion, name='profile_completion'),
    path('dashboard/', dashboard, name='dashboard'),
]
