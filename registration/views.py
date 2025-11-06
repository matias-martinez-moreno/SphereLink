from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from organizations.models import UserRole
from .models import ContactMessage
from .forms import ContactForm, CustomPasswordResetForm
import time

def login_view(request):
    """
    Main login view
    - Verifies user credentials
    - For superadmin: only verifies password, no organization required
    - For other users: verifies they belong to an active organization
    - Redirects according to user role (super_admin goes to organizations, others to events)
    """
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('/events/dashboard/')
    
    # Clear existing messages when loading login page (only on GET)
    if request.method == 'GET':
        try:
            storage = messages.get_messages(request)
            storage.used = True
            if hasattr(request, 'session'):
                request.session['_messages'] = []
        except:
            pass
    
    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password')
        
        # Check if input is email or username
        user = None
        if '@' in username_or_email:
            # Input is an email, try to find user by email
            try:
                user_obj = User.objects.get(email=username_or_email, is_active=True)
                # Authenticate using the username found by email
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            # Input is a username, authenticate normally
            user = authenticate(request, username=username_or_email, password=password)
        
        if user is not None:
            # SPECIAL CASE: If superadmin, allow immediate access
            if user.is_superuser:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}! Access as Super Administrator")
                return redirect('organizations:organization_list')
            
            # For NON-superadmin users: verify they belong to an active organization
            user_roles = UserRole.objects.filter(
                user=user, 
                is_active=True,
                organization__is_active=True
            ).select_related('organization')
            
            if user_roles.exists():
                # User has access to at least one organization
                login(request, user)
                
                # Determine user's highest role to customize message
                # If has multiple roles, prioritize super_admin
                role = user_roles.first()
                
                # Check if has super_admin role in any organization
                has_super_admin = user_roles.filter(role='super_admin').exists()
                
                if has_super_admin:
                    # If has super_admin, use that role for the message
                    super_admin_role = user_roles.filter(role='super_admin').first()
                    role_name = super_admin_role.get_role_display()
                    org_name = super_admin_role.organization.name
                else:
                    # If no super_admin, use first role
                    role_name = role.get_role_display()
                    org_name = role.organization.name
                
                messages.success(request, f"Welcome back, {user.username}! Access as {role_name} in {org_name}")
                
                # Redirect according to user role
                # ONLY super_admin goes to organizations, staff and member go to events
                if has_super_admin:
                    # Super admins go to organization panel
                    return redirect('organizations:organization_list')
                else:
                    # Staff and Member go to events dashboard
                    return redirect('/events/dashboard/')
            else:
                # User doesn't have access to any active organization
                # This can happen if all their organizations are deactivated
                messages.error(request, "Your account doesn't have access to any active organization. Contact the administrator.")
        else:
            # Invalid credentials
            messages.error(request, "Invalid username/email or password. Please try again.")
    
    # Render login form (GET) or with errors (POST)
    return render(request, 'registration/login.html')

def logout_view(request):
    """
    Logout view
    - Closes current user session
    - Clears all existing messages
    - Redirects to login page
    - Shows confirmation message
    """
    # Clear all existing messages before logout
    try:
        storage = messages.get_messages(request)
        storage.used = True
        if hasattr(request, 'session'):
            request.session['_messages'] = []
    except:
        pass
    
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('/')

@login_required
@csrf_exempt
def refresh_session(request):
    """
    AJAX endpoint to refresh user session and prevent automatic logout
    """
    if request.method == 'POST':
        # Update last activity time in session
        request.session['last_activity'] = time.time()
        
        # Calculate remaining time until session expires (30 minutes = 1800 seconds)
        remaining_time = 1800  # Reset to full 30 minutes
        
        return JsonResponse({
            'status': 'success',
            'remaining_time': remaining_time,
            'message': 'Session refreshed successfully'
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@login_required
def check_session_status(request):
    """
    AJAX endpoint to check current session status
    """
    current_time = time.time()
    last_activity = request.session.get('last_activity', current_time)
    time_since_last_activity = current_time - last_activity
    remaining_time = max(0, 1800 - time_since_last_activity)  # 1800 seconds = 30 minutes
    
    return JsonResponse({
        'status': 'success',
        'remaining_time': remaining_time,
        'is_expired': remaining_time <= 0
    })

def contact_admin(request):
    """
    Handle contact form submission from users who need help with login or account issues
    - Creates a ContactMessage record
    - Sends email notification to system administrators
    - Returns success message to user
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                # Save the contact message
                contact_message = form.save()
                
                # Send email notification to administrators
                admin_email = settings.ADMIN_EMAIL
                subject = f"SphereLink Contact Request: {contact_message.subject}"
                
                # Create email content
                context = {
                    'contact_message': contact_message,
                    'site_name': 'SphereLink',
                    'admin_email': admin_email
                }
                
                message_content = f"""
A new contact request has been submitted through the SphereLink login page.

Contact Details:
- Email: {contact_message.email}
- Subject: {contact_message.subject}
- Message: {contact_message.message}
- Submitted: {contact_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Please respond to this user at: {contact_message.email}

You can view and manage this contact request in the Django admin panel.

Best regards,
SphereLink System
                """
                
                # Send email to administrators
                send_mail(
                    subject=subject,
                    message=message_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin_email],
                    fail_silently=False,
                )
                
                # Return success response
                return JsonResponse({
                    'status': 'success',
                    'message': 'Your message has been sent. An administrator will contact you shortly.'
                })
                
            except Exception as e:
                # Log the error and return error response
                return JsonResponse({
                    'status': 'error',
                    'message': 'There was an error sending your message. Please try again later.'
                })
        else:
            # Return form errors
            return JsonResponse({
                'status': 'error',
                'message': 'Please correct the errors below.',
                'errors': form.errors
            })
    
    # If GET request, return the form
    form = ContactForm()
    return render(request, 'registration/contact_form.html', {'form': form})


# Custom Password Reset Views - Using Django's built-in functionality with custom templates
class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view that uses our beautiful template and verifies email exists"""
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('registration:password_reset_done')
    form_class = CustomPasswordResetForm
    from_email = settings.DEFAULT_FROM_EMAIL
    
    def form_valid(self, form):
        """Override form_valid to ensure email is sent and add logging"""
        email = form.cleaned_data['email']
        from django.contrib.auth.models import User
        
        # Get user for better logging
        try:
            user = User.objects.get(email=email, is_active=True)
            username = user.username
        except User.DoesNotExist:
            username = "Unknown"
        
        print(f"\n{'='*60}")
        print(f"🔐 Password reset requested")
        print(f"📧 Email: {email}")
        print(f"👤 Username: {username}")
        print(f"📧 Email backend: {settings.EMAIL_BACKEND}")
        print(f"📧 From email: {self.from_email}")
        
        # Check if using console backend
        is_console_backend = 'console' in settings.EMAIL_BACKEND.lower()
        if is_console_backend:
            print(f"⚠️  MODO DESARROLLO: Email se mostrará en consola")
            print(f"📧 Para enviar emails reales, configura variables de entorno:")
            print(f"   - EMAIL_HOST_USER")
            print(f"   - EMAIL_HOST_PASSWORD")
            print(f"   Ver EMAIL_SETUP.md para instrucciones")
        else:
            print(f"✅ MODO PRODUCCIÓN: Email se enviará por SMTP")
        
        print(f"{'='*60}\n")
        
        # Call parent form_valid which handles form.save() and email sending
        try:
            result = super().form_valid(form)
            
            if is_console_backend:
                print(f"\n{'='*60}")
                print(f"📧 EMAIL DE RESET DE CONTRASEÑA (mostrado en consola):")
                print(f"{'='*60}")
                # The email content will be printed by console backend
            else:
                print(f"✅ Password reset email sent successfully to: {email}")
            
            return result
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"❌ ERROR al enviar email de reset de contraseña")
            print(f"📧 Error: {str(e)}")
            print(f"{'='*60}\n")
            import traceback
            traceback.print_exc()
            # Re-raise to show error to user
            raise

class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Custom password reset done view"""
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view"""
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('registration:password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Custom password reset complete view"""
    template_name = 'registration/password_reset_complete.html'
