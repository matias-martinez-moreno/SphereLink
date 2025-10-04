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
