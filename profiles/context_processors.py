from .models import Profile

def user_profile(request):
    """
    Context processor to make user profile available in all templates
    """
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            profile = None
    else:
        profile = None
    
    return {
        'user_profile': profile
    }

def unread_notifications(request):
    """
    Context processor to make unread notifications count available in all templates
    """
    if request.user.is_authenticated:
        from events.models import Notification
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    else:
        unread_count = 0
    
    return {
        'unread_notifications_count': unread_count
    }
