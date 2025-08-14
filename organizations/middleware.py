from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser

class SuperAdminRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated and is a super admin
        if (request.user.is_authenticated and 
            not isinstance(request.user, AnonymousUser)):
            
            # Check if user is super admin
            is_super_admin = request.user.organization_roles.filter(
                role='super_admin', 
                is_active=True
            ).exists()
            
            # If super admin is trying to access event-related pages, redirect to organizations
            if is_super_admin:
                event_urls = [
                    '/events/dashboard/',
                    '/events/create_event/',
                    '/events/my_events/',
                    '/events/events/',
                ]
                
                if request.path in event_urls:
                    return redirect('organizations:organization_list')
        
        response = self.get_response(request)
        return response
