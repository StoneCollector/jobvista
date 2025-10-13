from django.contrib.auth.models import User
from .models import Notification


def notifications_context(request):
    """Add notifications to all template contexts"""
    if request.user.is_authenticated:
        try:
            notifications = Notification.objects.filter(
                user=request.user, 
                is_read=False
            ).order_by('-created_at')[:5]
            return {'notifications': notifications}
        except Exception:
            return {'notifications': []}
    return {'notifications': []}
