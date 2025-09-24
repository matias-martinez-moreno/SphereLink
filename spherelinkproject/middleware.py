import time
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class SessionTimeoutMiddleware(MiddlewareMixin):
    """
    Middleware to handle automatic session timeout and logout
    """
    
    def process_request(self, request):
        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return None
            
        # Skip for login/logout URLs to avoid redirect loops
        login_urls = [reverse('registration:login'), reverse('registration:logout'), '/']
        if request.path in login_urls:
            return None
            
        # Get current time
        current_time = time.time()
        
        # Check if this is the first request (no last activity recorded)
        if 'last_activity' not in request.session:
            request.session['last_activity'] = current_time
            return None
            
        # Calculate time since last activity
        last_activity = request.session.get('last_activity', current_time)
        time_since_last_activity = current_time - last_activity
        
        # Check if session has expired (30 minutes = 1800 seconds)
        if time_since_last_activity > 1800:
            # Session has expired, logout user
            logout(request)
            messages.warning(request, "Your session has expired due to inactivity. Please log in again.")
            return redirect('registration:login')
            
        # Update last activity time
        request.session['last_activity'] = current_time
        return None