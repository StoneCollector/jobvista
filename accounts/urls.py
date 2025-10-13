from django.urls import path
from .views import *
from .api_views import get_notifications, mark_notification_read, mark_all_notifications_read

urlpatterns = [
    path('register/', signup, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile_view'),
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('career-advice/', career_advice_view, name='career_advice'),
    path('job-alerts/', job_alerts, name='job_alerts'),
    
    # API endpoints
    path('api/notifications/', get_notifications, name='api_notifications'),
    path('api/notifications/<int:notification_id>/read/', mark_notification_read, name='api_mark_notification_read'),
    path('api/notifications/read-all/', mark_all_notifications_read, name='api_mark_all_read'),
]
