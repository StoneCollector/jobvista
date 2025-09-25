from django.urls import path
from .views import *
from accounts.views import *

urlpatterns = [
    path('', job_list, name='home'),
    path('job_detail/<slug:slug>/', job_detail, name='job_detail'),
    path('company/', company_view, name='company_view'),
    path('company/add/', create_company, name='create_company'),
    path('company/update/<int:pk>/', update_company, name='update_company'),
    path('apply/', apply_job, name='apply_job'),
    path('profile_completion', profile_completion, name='profile_completion'),
]
