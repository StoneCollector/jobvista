from django.urls import path
from .views import *

urlpatterns = [
    path('my_bookmarks/', user_bookmarks, name='user_bookmarks'),
    path('bookmark/<int:job_id>/', toggle_bookmark, name='toggle_bookmark'),
    path('bookmark_job/<int:job_id>/', toggle_bookmark, name='bookmark_job'),
]
